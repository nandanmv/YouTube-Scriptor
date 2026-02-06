"""
AutoResearchAgent - Automatically discover top videos and extract angles.
Supports two strategies:
1. top_performers: Analyzes highest-viewed videos (default)
2. outliers: Analyzes videos that exceeded channel baseline
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import config
from youtube_utils import YouTubeUtility
from agents.base import BaseAgent
from agents.insight_agent import InsightAgent
from agents.prompts import RESEARCH_SYSTEM, ANGLE_SYNTHESIZER_SYSTEM
import litellm
import json
from agents.outlier_agent import OutlierAgent


class AutoResearchAgent(BaseAgent):
    """
    Automatically discover YouTube videos and extract proven angles.
    Supports two strategies:
    - top_performers: Find highest-viewed recent videos (default)
    - outliers: Find videos that exceeded channel baseline
    """

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.ANGLE_MODEL

    def run(self, topic: str, top_n: Optional[int] = None, strategy: Optional[str] = None) -> dict:
        """
        Automatically find top videos and extract angles.

        Args:
            topic: Search topic (e.g., "claude code")
            top_n: Number of top videos to analyze (defaults based on strategy)
            strategy: "top_performers" or "outliers" (defaults to config.RESEARCH_STRATEGY)

        Returns:
            {
                'videos': [...],     # Top N videos with full data
                'angles': [...],     # Extracted angles from videos
                'sources': [...],    # YouTube video URLs for citation
                'strategy': str      # Strategy used
            }
        """
        # Set defaults
        if strategy is None:
            strategy = config.RESEARCH_STRATEGY

        if top_n is None:
            if strategy == "top_performers":
                top_n = config.TOP_PERFORMERS_COUNT
            else:
                top_n = config.AUTO_RESEARCH_OUTLIER_COUNT

        print(f"[*] AutoResearchAgent: Using '{strategy}' strategy for '{topic}'...")

        # Route to appropriate strategy
        if strategy == "top_performers":
            result = self._find_top_performers(topic, top_n)
        else:  # outliers
            result = self._find_outliers_strategy(topic, top_n)

        result['strategy'] = strategy
        return result

    def _find_top_performers(self, topic: str, top_n: int) -> dict:
        """
        Find top-performing videos by absolute view count.
        Filters by recency and minimum views.
        """
        recency_months = config.TOP_PERFORMERS_RECENCY_MONTHS
        min_views = config.TOP_PERFORMERS_MIN_VIEWS

        print(f"[*] Finding top {top_n} performing videos...")
        print(f"    Filters: Last {recency_months} months, >= {min_views:,} views")

        # Search with larger limit to ensure enough results after filtering
        search_limit = max(100, top_n * 3)
        results = YouTubeUtility.search(topic, limit=search_limit)

        # Filter by recency
        if recency_months > 0:
            cutoff_date = datetime.now() - timedelta(days=recency_months * 30)
            filtered_results = []
            for video in results:
                upload_date = self._parse_upload_date(video)
                if upload_date and upload_date >= cutoff_date:
                    filtered_results.append(video)
            results = filtered_results
            print(f"[*] After recency filter: {len(results)} videos")

        # Filter by minimum views
        results = [v for v in results if v.get('view_count', 0) >= min_views]
        print(f"[*] After views filter (>={min_views:,}): {len(results)} videos")

        if not results:
            print("[!] No videos found matching criteria. Using default angles.")
            return {
                'videos': [],
                'angles': self._get_default_angles(topic),
                'sources': []
            }

        # Sort by view count and take top N
        top_performers = sorted(results, key=lambda x: x.get('view_count', 0), reverse=True)[:top_n]

        print(f"[+] Found {len(top_performers)} top performers")
        if top_performers:
            print(f"    View range: {top_performers[0]['view_count']:,} - {top_performers[-1]['view_count']:,}")

        # Build video data for analysis
        videos = []
        for v in top_performers:
            videos.append({
                'title': v['title'],
                'url': f"https://www.youtube.com/watch?v={v['id']}",
                'channel': v.get('channel', 'Unknown'),
                'views': v.get('view_count', 0),
                'upload_date': self._parse_upload_date(v)
            })

        # Extract angles
        angles = self._extract_angles_from_performers(videos, topic)

        # Build sources
        sources = [
            {
                'title': v['title'],
                'url': v['url'],
                'channel': v['channel'],
                'views': v['views']
            }
            for v in videos
        ]

        return {
            'videos': videos,
            'angles': angles,
            'sources': sources
        }

    def _find_outliers_strategy(self, topic: str, top_n: int) -> dict:
        """
        Find outlier videos using baseline ratio calculation.
        Uses OutlierAgent to ensure consistent logic and reporting.
        """
        print(f"[*] Finding top {top_n} outliers using OutlierAgent...")

        # Use OutlierAgent to find and save outliers
        outlier_agent = OutlierAgent(use_database=self.use_database)
        # We pass top_n as min_outliers to ensure we get enough videos
        top_outliers = outlier_agent.run(topic, min_outliers=top_n)

        if not top_outliers:
            print("[!] No outliers found. Using default angles.")
            return {
                'videos': [],
                'angles': self._get_default_angles(topic),
                'sources': []
            }

        # Take top N outliers (already sorted by OutlierAgent)
        top_outliers = top_outliers[:top_n]
        print(f"[+] Selected top {len(top_outliers)} outliers (avg ratio: {sum(o['ratio'] for o in top_outliers) / len(top_outliers):.1f}x)")

        # Extract angles
        angles = self._extract_angles(top_outliers, topic)

        # Build sources
        sources = [
            {
                'title': o['title'],
                'url': o['url'],
                'channel': o['channel'],
                'views': o['views'],
                'ratio': o['ratio']
            }
            for o in top_outliers
        ]

        return {
            'videos': top_outliers,
            'angles': angles,
            'sources': sources
        }


    def _parse_upload_date(self, video: dict) -> Optional[datetime]:
        """Parse upload date from video metadata."""
        try:
            # yt-dlp returns upload_date as YYYYMMDD string
            upload_date_str = video.get('upload_date')
            if upload_date_str:
                return datetime.strptime(str(upload_date_str), '%Y%m%d')
        except:
            pass
        return None

    def _extract_angles_from_performers(self, videos: list, topic: str) -> list:
        """
        Extract angles from top-performing videos.
        Similar to _extract_angles but without ratio/outlier context.
        """
        # Prepare video data for analysis
        video_summaries = [
            {
                "title": v["title"],
                "views": v["views"],
                "channel": v["channel"]
            }
            for v in videos
        ]

        prompt = f"""
Analyze these high-performing YouTube videos about "{topic}" and identify the unique angles/approaches that made them successful.

Videos (sorted by view count):
{json.dumps(video_summaries, indent=2)}

For each angle you identify, provide:
- angle_name: Short descriptive name (e.g., "Tutorial Format", "Problem-Solution", "Case Study")
- description: What makes this angle unique and effective
- why_it_works: Psychological/strategic reason for success
- example_titles: 2-3 video titles that use this angle (from the list above)
- estimated_performance: Score 1-10 based on view counts and engagement potential

Return JSON: {{"angles": [...]}}

Find 5-7 distinct angles that would work well for a new video on this topic.
Focus on what's actually working on YouTube right now.
"""

        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": ANGLE_SYNTHESIZER_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=config.DEFAULT_API_TIMEOUT
            )

            result = json.loads(response.choices[0].message.content)
            angles = result.get("angles", [])
            print(f"[+] Extracted {len(angles)} proven angles from top performers")
            return angles
        except Exception as e:
            print(f"[!] Angle extraction failed: {e}")
            return self._get_default_angles(topic)

    def _extract_angles(self, outliers: list, topic: str) -> list:
        """
        Extract proven angles from outlier videos using AI.
        Same logic as AngleFromOutliersAgent._extract_angles.
        """
        # Prepare video data for analysis
        video_summaries = [
            {
                "title": o["title"],
                "views": o["views"],
                "ratio": o["ratio"],
                "channel": o["channel"],
                "success_criteria": o.get("success_criteria", "N/A"),
                "subtopics": o.get("subtopics_covered", "N/A"),
                "reusable_insights": o.get("reusable_insights", "N/A")
            }
            for o in outliers
        ]

        prompt = f"""
Analyze these high-performing YouTube videos about "{topic}" and identify the unique angles/approaches that made them successful.

Videos:
{json.dumps(video_summaries, indent=2)}

For each angle you identify, provide:
- angle_name: Short descriptive name (e.g., "Contrarian Take", "Tutorial Format", "Behind-the-Scenes")
- description: What makes this angle unique
- why_it_works: Psychological/strategic reason for success
- example_titles: 2-3 video titles that use this angle (from the list above)
- estimated_performance: Score 1-10 based on view ratios

Return JSON: {{"angles": [...]}}

Find 5-7 distinct angles that would work well for a new video on this topic.
"""

        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": ANGLE_SYNTHESIZER_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=config.DEFAULT_API_TIMEOUT
            )

            result = json.loads(response.choices[0].message.content)
            angles = result.get("angles", [])
            print(f"[+] Extracted {len(angles)} proven angles from outliers")
            return angles
        except Exception as e:
            print(f"[!] Angle extraction failed: {e}")
            return self._get_default_angles(topic)

    def _get_default_angles(self, topic: str) -> list:
        """Fallback angles if analysis fails"""
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
            }
        ]
