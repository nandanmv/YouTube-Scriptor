from agents.base import BaseAgent, parse_json_response
from agents.outlier_agent import OutlierAgent
from agents.prompts import RESEARCH_SYSTEM
import litellm
import config
import json

class AngleDiscoveryAgent(BaseAgent):
    """Research YouTube to find proven content angles for a topic"""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.ANGLE_MODEL

    def run(self, topic: str) -> list:
        """
        Find successful angles by analyzing YouTube outliers.

        Args:
            topic: Video topic (e.g., "AI agents", "Python async")

        Returns:
            List of angle dictionaries with description, examples, performance data
        """
        print(f"[*] AngleDiscoveryAgent researching angles for '{topic}'...")

        # 1. Search for outlier videos on this topic
        outlier_agent = OutlierAgent(use_database=self.use_database)
        outliers = outlier_agent.run(topic)

        if not outliers:
            print("[!] No outliers found, returning default angles")
            return self._get_default_angles(topic)

        # 2. Analyze outliers to extract successful angles
        angles = self._extract_angles(outliers, topic)

        print(f"[+] Found {len(angles)} proven angles")
        return angles

    def _extract_angles(self, outliers: list, topic: str) -> list:
        """Use LLM to identify patterns and angles from successful videos"""

        # Prepare video data for analysis
        video_summaries = []
        for o in outliers[:10]:  # Top 10 outliers
            video_summaries.append({
                "title": o["title"],
                "views": o["views"],
                "ratio": o["ratio"],
                "channel": o["channel"]
            })

        prompt = f"""
Analyze these high-performing YouTube videos about "{topic}" and identify the unique angles/approaches that made them successful.

Videos:
{json.dumps(video_summaries, indent=2)}

For each angle you identify, provide:
- angle_name: Short descriptive name (e.g., "Contrarian Take", "Tutorial Format", "Behind-the-Scenes")
- description: What makes this angle unique
- why_it_works: Psychological/strategic reason for success
- example_titles: 2-3 video titles that use this angle
- estimated_performance: Score 1-10 based on view ratios

Return JSON: {{"angles": [...]}}

Find 5-7 distinct angles.
"""

        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": RESEARCH_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = parse_json_response(response.choices[0].message.content)
            return result.get("angles", [])
        except Exception as e:
            print(f"[!] Angle extraction failed: {e}")
            return self._get_default_angles(topic)

    def _get_default_angles(self, topic: str) -> list:
        """Fallback angles if API fails"""
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
