from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import config
from youtube_utils import YouTubeUtility
from agents.base import BaseAgent
from agents.insight_agent import InsightAgent

class OutlierAgent(BaseAgent):
    """Agent that identifies high-performing videos for a single search term."""

    def __init__(self, use_database: bool = False, progress_callback=None):
        """Initialize OutlierAgent with optional database support."""
        super().__init__(use_database=use_database)
        self.progress_callback = progress_callback

    def _log(self, message: str):
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)

    def run(
        self,
        query: str,
        job_id: Optional[str] = None,
        min_outliers: int = 10,
        generate_insights: bool = True,
        save_report: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run outlier detection for a search query.

        Args:
            query: Search query term
            job_id: Optional job ID for database storage
            min_outliers: Minimum number of outliers to find (default: 10)

        Returns:
            List of outlier video dictionaries
        """
        search_limit = config.SEARCH_LIMIT
        outliers = []

        # Try with initial search limit
        self._log(f"[*] Analyzing {search_limit} videos for outliers matching '{query}'...")
        results = YouTubeUtility.search(query, search_limit, logger=self._log)

        for video in results:
            outlier_data = self._analyze_video(video)
            if outlier_data:
                self._log(f"[+] Found Outlier: {outlier_data['title']} (Ratio: {outlier_data['ratio']:.2f})")
                outliers.append(outlier_data)

        # If we found fewer than min_outliers, suggest increasing search limit
        if len(outliers) < min_outliers and search_limit < 100:
            needed_limit = min(search_limit + 20, 100)
            self._log(f"[!] Found only {len(outliers)} outliers (target: {min_outliers})")
            self._log(f"[*] Expanding search to {needed_limit} results to find more outliers...")

            # Search additional videos
            additional_results = YouTubeUtility.search(query, needed_limit, logger=self._log)

            # Process only new videos (those beyond original search_limit)
            for video in additional_results[search_limit:]:
                outlier_data = self._analyze_video(video)
                if outlier_data:
                    self._log(f"[+] Found Outlier: {outlier_data['title']} (Ratio: {outlier_data['ratio']:.2f})")
                    outliers.append(outlier_data)

                # Stop if we reached the minimum
                if len(outliers) >= min_outliers:
                    break

        # Display final count
        if len(outliers) < min_outliers:
            self._log(f"[!] Warning: Found {len(outliers)} outliers (target was {min_outliers})")
            self._log("[*] Consider adjusting OUTLIER_THRESHOLD or MIN_MEDIAN_VIEWS in config.py")
        else:
            self._log(f"[+] Successfully found {len(outliers)} outliers (target: {min_outliers})")

        sorted_outliers = sorted(outliers, key=lambda x: x['ratio'], reverse=True)

        # Add AI insights to top N videos
        if sorted_outliers and generate_insights:
            self._log(f"[*] Generating AI insights for top {min(len(sorted_outliers), config.INSIGHT_TOP_N)} outliers...")
            insight_agent = InsightAgent(use_database=self.use_database, progress_callback=self.progress_callback)

            for i, outlier in enumerate(sorted_outliers[:config.INSIGHT_TOP_N]):
                self._log(f"[*] Analyzing {i+1}/{min(len(sorted_outliers), config.INSIGHT_TOP_N)}: {outlier['title']}")
                insight = insight_agent.run(outlier)
                # Merge insights into outlier dict
                outlier.update(insight)

        if sorted_outliers and save_report:
            if generate_insights:
                self._save_rich_results(query, sorted_outliers, job_id=job_id)
            else:
                self.save_results(query, sorted_outliers, job_id=job_id)

        return sorted_outliers

    def _analyze_video(self, video: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        channel_url = video.get('channel_url')
        if not channel_url:
            channel_id = video.get('channel_id')
            if channel_id:
                channel_url = f"https://www.youtube.com/channel/{channel_id}"
            else:
                return None

        video_views = video.get('view_count') or 0
        median_views = YouTubeUtility.get_channel_baseline(channel_url, config.CHANNEL_HISTORY)
        
        ratio = video_views / median_views if median_views > 0 else 0
        
        # Super Outlier Bypass: If ratio is >= 10x, allow even if median is low
        is_super_outlier = ratio >= 10.0
        
        if not is_super_outlier and (median_views is None or median_views < config.MIN_MEDIAN_VIEWS):
            return None
        
        if ratio >= config.OUTLIER_THRESHOLD:
            channel_info = YouTubeUtility.get_channel_info(channel_url)
            subscribers = channel_info.get('channel_follower_count') or channel_info.get('subscriber_count')

            # Filter: Only include channels with fewer than MAX_SUBSCRIBERS
            if subscribers and subscribers >= config.MAX_SUBSCRIBERS:
                return None

            return {
                'title': video.get('title'),
                'url': f"https://www.youtube.com/watch?v={video.get('id')}",
                'views': video_views,
                'median_views': median_views,
                'ratio': ratio,
                'channel': video.get('channel'),
                'subscribers': subscribers
            }
        return None

    def _sanitize_table_cell(self, text: str) -> str:
        """Sanitize text for markdown table cells by replacing newlines with <br> and escaping pipes."""
        if not text or text == "N/A":
            return text
        # Replace newlines with <br> for markdown line breaks within cells
        text = str(text).replace('\n', '<br>')
        # Escape pipe characters that could break table structure
        text = text.replace('|', '\\|')
        return text

    def _save_rich_results(self, query: str, outliers: list, job_id: Optional[str] = None):
        """Save results with AI insights to markdown file in organized folder structure."""
        # Create outliers subfolder
        output_dir = "results/outliers"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/outlier_{query.replace(' ', '_').lower()}_{timestamp}.md"

        with open(filename, "w") as f:
            f.write(f"# Outlier Analysis: {query}\n\n")
            f.write(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Threshold**: {config.OUTLIER_THRESHOLD}x\n")
            f.write(f"- **Total Outliers**: {len(outliers)}\n")
            f.write(f"- **AI Insights**: Top {min(len(outliers), config.INSIGHT_TOP_N)} videos\n\n")

            # Table header with Selection column and all insight columns
            f.write("| Selection | Score | Video | Views | Median | Subs | Channel | Success Criteria | Subtopics Covered | Reusable Insights | Ultimate Titles | Alternate Hooks |\n")
            f.write("|:---:|-------|-------|-------|--------|------|---------|------------------|-------------------|-------------------|-----------------|-----------------|\n")

            for r in outliers:
                subs = f"{r['subscribers']:,}" if r.get('subscribers') else "N/A"

                # Sanitize AI insight fields (only present for top N videos)
                success = self._sanitize_table_cell(r.get('success_criteria', 'N/A'))
                subtopics = self._sanitize_table_cell(r.get('subtopics_covered', 'N/A'))
                insights = self._sanitize_table_cell(r.get('reusable_insights', 'N/A'))
                titles = self._sanitize_table_cell(r.get('ultimate_titles', 'N/A'))
                hooks = self._sanitize_table_cell(r.get('alternate_hooks', 'N/A'))

                f.write(f"| [ ] | {r['ratio']:.2f}x | [{r['title']}]({r['url']}) | {r['views']:,} | {int(r['median_views']):,} | {subs} | {r['channel']} | {success} | {subtopics} | {insights} | {titles} | {hooks} |\n")

        self._log(f"[+] Outlier analysis saved to: {filename}")

        # Save to database if enabled
        if self.use_database and job_id:
            self.store.save_outliers(job_id, outliers)
