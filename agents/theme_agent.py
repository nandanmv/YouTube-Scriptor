from agents.base import BaseAgent
from agents.prompts import THEME_ANALYZER_SYSTEM
import litellm
import config
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class ThemeAgent(BaseAgent):
    """Analyze all outlier videos to find common themes, patterns, and success criteria"""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.RESEARCH_MODEL

    def run(self, topic: str) -> dict:
        """
        Identify recurring themes by analyzing all outlier videos for a topic.

        Args:
            topic: The search term used for outliers

        Returns:
            Dict with theme analysis results
        """
        print(f"[*] ThemeAgent analyzing all outliers for '{topic}'...")

        # 1. Find and parse the latest outlier report for this topic
        all_videos = self._parse_all_outliers(topic)

        if not all_videos:
            print(f"[!] No outlier reports found for '{topic}' in results/outliers/")
            return {
                'error': f"No reports found for {topic}",
                'themes': {}
            }

        print(f"[+] Found {len(all_videos)} videos to analyze")

        # 2. Analyze all videos to extract themes
        themes = self._extract_themes(all_videos, topic)

        return themes

    def _parse_all_outliers(self, topic: str) -> List[Dict[str, Any]]:
        """
        Find the latest markdown report for a topic and parse ALL videos.
        """
        outliers_dir = "results/outliers"
        topic_slug = topic.replace(" ", "_").lower()
        
        if not os.path.exists(outliers_dir):
            return []

        # Find files for this topic, sorted by timestamp (decending)
        topic_files = [
            f for f in os.listdir(outliers_dir) 
            if f.startswith(f"outlier_{topic_slug}") and f.endswith(".md")
        ]
        
        if not topic_files:
            return []
            
        # Get the latest file
        latest_file = sorted(topic_files, reverse=True)[0]
        path = os.path.join(outliers_dir, latest_file)
        
        print(f"[*] Reading latest report: {latest_file}")
        
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
                        title = video_col.split("[")[-1].split("]")[0] if "[" in video_col else video_col
                        
                        videos.append({
                            'title': title,
                            'views': parts[4],
                            'ratio': parts[2],
                            'channel': parts[7],
                            'success_criteria': parts[8],
                            'subtopics': parts[9],
                            'reusable_insights': parts[10]
                        })
        
        return videos

    def _extract_themes(self, videos: List[Dict[str, Any]], topic: str) -> dict:
        """Use LLM to identify themes and patterns from all videos"""

        prompt = f"""
Analyze these successful outlier videos about "{topic}" and identify recurring themes.

Videos Data:
{json.dumps(videos, indent=2)}

Focus on:
1. Common Title Phrases: Recurring words or formatting styles.
2. Recurring Topics & Subtopics: What specific subjects keep coming up?
3. Universal Success Criteria: What is the shared strategic thread?
4. Audience Intent: What is the viewer looking for?

Return JSON:
{{
    "topic": "{topic}",
    "analysis_date": "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "video_count": {len(videos)},
    "themes": {{
        "common_title_phrases": ["phrase 1", "phrase 2"],
        "recurring_topics": ["topic 1", "topic 2"],
        "success_criteria_patterns": ["pattern 1", "pattern 2"],
        "audience_intent": "description of intent"
    }}
}}
"""

        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": THEME_ANALYZER_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=config.DEFAULT_API_TIMEOUT
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[!] Theme extraction failed: {e}")
            return {"error": str(e)}
