from agents.base import BaseAgent, parse_json_response
from agents.prompts import ANGLE_SYNTHESIZER_SYSTEM
import litellm
import config
import json
import os
from typing import List, Dict, Any

class AngleFromOutliersAgent(BaseAgent):
    """Generate content angles from manually selected outlier videos"""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.ANGLE_MODEL

    def run(self, topic: str, videos: List[Dict[str, Any]] = None) -> dict:
        """
        Find successful angles by analyzing all outlier videos for a topic.

        Args:
            topic: The topic to find outliers for

        Returns:
            Dict with 'angles' (list) and 'sources' (list of video dicts with URLs)
        """
        print(f"[*] AngleFromOutliersAgent analyzing all outliers for '{topic}'...")

        all_outliers = videos if videos is not None else self._parse_all_outliers(topic)

        if not all_outliers:
            print(f"[!] No outlier reports found for '{topic}' in results/outliers/")
            return {
                'angles': self._get_default_angles(topic),
                'sources': []
            }

        print(f"[+] Found {len(all_outliers)} videos to analyze")

        # 2. Analyze outliers to extract successful angles
        angles = self._extract_angles(all_outliers, topic)

        # 3. Build sources list with URLs for citation
        sources = [
            {
                'title': o['title'],
                'url': o.get('url', ''),
                'channel': o.get('channel', 'Unknown'),
                'views': o.get('views', 0),
                'ratio': o.get('ratio', 0)
            }
            for o in all_outliers
        ]

        print(f"[+] Generated {len(angles)} proven angles from outliers")
        return {
            'angles': angles,
            'sources': sources
        }

    def _parse_all_outliers(self, topic: str) -> List[Dict[str, Any]]:
        """
        Find the latest markdown report for a topic and parse ALL videos.
        """
        outliers_dir = "results/outliers"
        topic_slug = topic.replace(" ", "_").lower()
        
        if not os.path.exists(outliers_dir):
            return []

        # Find files for this topic, sorted by timestamp (descending)
        topic_files = [
            f for f in os.listdir(outliers_dir) 
            if f.startswith(f"outlier_{topic_slug}") and f.endswith(".md")
        ]
        
        if not topic_files:
            return []
            
        # Get the latest file
        latest_file = sorted(topic_files, reverse=True)[0]
        path = os.path.join(outliers_dir, latest_file)
        
        print(f"[*] Reading latest report for angles: {latest_file}")
        
        videos = []
        with open(path, "r") as f:
            lines = f.readlines()
            for line in lines:
                # Look for table rows (all videos, regardless of selection)
                if line.startswith("| [ ] |") or line.startswith("| [x] |"):
                    parts = [p.strip() for p in line.split("|")]
                    # Structure: | Selection | Score | Video | Views | Median | Subs | Channel | Success Criteria | Subtopics | Insights | ...
                    if len(parts) >= 11:
                        # Video title and URL from [title](url)
                        video_col = parts[3]
                        url = video_col.split("(")[-1].strip(")") if "(" in video_col else ""
                        title = video_col.split("[")[-1].split("]")[0] if "[" in video_col else video_col
                        
                        try:
                            score_str = parts[2].replace("x", "").strip()
                            views_str = parts[4].replace(",", "").strip()
                            ratio = float(score_str)
                            views = int(views_str)
                        except (ValueError, TypeError):
                            continue

                        videos.append({
                            'title': title,
                            'url': url,
                            'views': views,
                            'ratio': ratio,
                            'channel': parts[7],
                            'success_criteria': parts[8],
                            'subtopics': parts[9],
                            'reusable_insights': parts[10]
                        })
        
        return videos

    def _extract_angles(self, outliers: list, topic: str = None) -> list:
        """Use LLM to identify patterns and angles from selected videos"""

        # Prepare video data for analysis
        video_summaries = []
        for o in outliers:
            video_summaries.append({
                "title": o["title"],
                "views": o.get("views", "N/A"),
                "ratio": o.get("ratio", "N/A"),
                "channel": o["channel"],
                "success_criteria": o.get("success_criteria", "N/A"),
                "subtopics": o.get("subtopics", "N/A"),
                "reusable_insights": o.get("reusable_insights", "N/A")
            })

        topic_context = f' about "{topic}"' if topic else ""

        prompt = f"""
Analyze these high-performing YouTube videos{topic_context} and identify the unique angles/approaches that made them successful.

Videos:
{json.dumps(video_summaries, indent=2)}

For each angle you identify, provide:
- angle_name: Short descriptive name (e.g., "Contrarian Take", "Tutorial Format", "Behind-the-Scenes")
- description: What makes this angle unique
- why_it_works: Psychological/strategic reason for success
- example_titles: 2-3 video titles that use this angle (from the list above)
- estimated_performance: Score 1-10 based on view ratios

Return JSON: {{"angles": [...]}}

Find 5-7 distinct angles.
"""

        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": ANGLE_SYNTHESIZER_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = parse_json_response(response.choices[0].message.content)
            return result.get("angles", [])
        except Exception as e:
            print(f"[!] Angle extraction failed: {e}")
            return self._get_default_angles(topic or "your topic")

    def _get_default_angles(self, topic: str) -> list:
        """Fallback angles if API fails or no selection"""
        return [
            {
                "angle_name": "Tutorial/How-To",
                "description": "Step-by-step guide teaching viewers",
                "why_it_works": "People search for solutions",
                "example_titles": [f"How to {topic}", f"{topic} Tutorial"],
                "estimated_performance": 7
            },
            {
                "angle_name": "Contrarian Take",
                "description": "Challenge common assumptions",
                "why_it_works": "Creates curiosity and debate",
                "example_titles": [f"Why {topic} is Overrated", f"The Truth About {topic}"],
                "estimated_performance": 8
            },
            {
                "angle_name": "Case Study",
                "description": "Real-world example or story",
                "why_it_works": "Concrete examples are engaging",
                "example_titles": [f"How I Used {topic} to...", f"{topic} Success Story"],
                "estimated_performance": 7
            },
            {
                "angle_name": "Comparison",
                "description": "Compare options or approaches",
                "why_it_works": "Helps decision-making",
                "example_titles": [f"{topic} vs Alternatives", f"Best {topic} Options"],
                "estimated_performance": 6
            },
            {
                "angle_name": "Behind-the-Scenes",
                "description": "Show the process or inner workings",
                "why_it_works": "Satisfies curiosity about 'how it really works'",
                "example_titles": [f"Inside {topic}", f"How {topic} Actually Works"],
                "estimated_performance": 7
            }
        ]
