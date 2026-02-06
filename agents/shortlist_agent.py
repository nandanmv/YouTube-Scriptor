import os
from typing import List, Dict, Any
from datetime import datetime
from rich import print
from agents.base import BaseAgent
from agents.insight_agent import InsightAgent

class ShortlistAgent(BaseAgent):
    """Agent that scans existing reports for shortlisted videos and triggers insights."""

    def __init__(self, use_database: bool = False):
        """Initialize ShortlistAgent with optional database support."""
        super().__init__(use_database=use_database)

    def run(self):
        """Run shortlist analysis on marked videos."""
        print("[*] ShortlistAgent scanning for marked videos...")
        shortlisted_videos = self._parse_shortlists()
        
        if not shortlisted_videos:
            print("[!] No shortlisted videos (marked with [x]) found in results/.")
            return []

        insight_agent = InsightAgent()
        all_insights = []
        
        for video in shortlisted_videos:
            insight = insight_agent.run(video)
            all_insights.append(insight)
            
        self._save_insight_report(all_insights)
        return all_insights

    def _parse_shortlists(self) -> List[Dict[str, Any]]:
        """
        Get marked videos from database or markdown files.

        Uses database if use_database=True, otherwise falls back to markdown parsing
        for backward compatibility.

        Returns:
            List of marked video dictionaries
        """
        # NEW: Use database if enabled (fast, structured queries)
        if self.use_database and hasattr(self, 'store'):
            print("[*] Using database to retrieve marked videos...")
            marked = self.store.get_marked_videos()
            return [
                {
                    'title': m['video']['title'],
                    'url': m['video']['url'],
                    'channel': m['video']['channel']
                }
                for m in marked
            ]

        # FALLBACK: Parse markdown files (backward compatibility)
        print("[*] Using markdown parsing (fallback mode)...")
        shortlisted = []
        if not os.path.exists("results"):
            return []

        for filename in os.listdir("results"):
            if filename.endswith(".md") and filename != "shortlist_insights.md":
                path = os.path.join("results", filename)
                with open(path, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        if "| [x] |" in line:
                            parts = [p.strip() for p in line.split("|")]
                            # Table structure: | Shortlist | Score | Title | Views | Median | Subs | Channel | URL |
                            if len(parts) >= 9:
                                video = {
                                    'title': parts[3],
                                    'url': parts[8].split("(")[-1].strip(")") if "(" in parts[8] else parts[8],
                                    'channel': parts[7]
                                }
                                shortlisted.append(video)
        return shortlisted

    def _save_insight_report(self, insights: List[Dict[str, Any]]):
        filename = "results/shortlist_insights.md"
        with open(filename, "w") as f:
            f.write("# Shortlisted Video Insights\n\n")
            f.write(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("| Video | Success Criteria | Reusable Insights | Ultimate Titles | Alternate Hooks |\n")
            f.write("|-------|------------------|-------------------|-----------------|-----------------|\n")
            
            for i in insights:
                f.write(f"| [{i['title']}]({i['url']}) | {i['success_criteria']} | {i['reusable_insights']} | {i['ultimate_titles']} | {i['alternate_hooks']} |\n")
        
        print(f"[bold green][+] Insight report saved to: {filename}[/bold green]")
