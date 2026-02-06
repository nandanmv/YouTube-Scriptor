import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from agents.base import BaseAgent
from agents.outlier_agent import OutlierAgent
from agents.insight_agent import InsightAgent

class BrainstormAgent(BaseAgent):
    """Agent that combines outlier detection and AI insights into a single unified report."""

    def __init__(self, use_database: bool = False):
        """Initialize BrainstormAgent."""
        super().__init__(use_database=use_database)

    def run(self, query: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Run discovery and analysis for a search query.

        Args:
            query: Search query term
            top_n: Number of top results to analyze deeply

        Returns:
            List of video dictionaries with combined stats and insights
        """
        print(f"[*] Brainstorming starting for '{query}'...")
        
        # 1. Discovery Phase
        outlier_agent = OutlierAgent(use_database=self.use_database)
        outliers = outlier_agent.run(query)
        
        if not outliers:
            print(f"[!] No outliers found for '{query}'. Brainstorming stopped.")
            return []

        # 2. Analysis Phase (Top N)
        insight_agent = InsightAgent(use_database=self.use_database)
        combined_results = []
        
        target_videos = outliers[:top_n]
        print(f"[*] Analyzing top {len(target_videos)} outliers for deep insights...")
        
        for o in target_videos:
            insight = insight_agent.run(o)
            # Combine stats with insights
            combined = {**o, **insight}
            combined_results.append(combined)
            
        # 3. Save Unified Report
        self._save_brainstorm_report(query, combined_results)
        
        return combined_results

    def _sanitize_table_cell(self, text: str) -> str:
        """Sanitize text for markdown table cells by replacing newlines with <br> and escaping pipes."""
        if not text or text == "N/A":
            return text
        # Replace newlines with <br> for markdown line breaks within cells
        text = str(text).replace('\n', '<br>')
        # Escape pipe characters that could break table structure
        text = text.replace('|', '\\|')
        return text

    def _save_brainstorm_report(self, query: str, results: List[Dict[str, Any]]):
        """Save a deep-dive unified report."""
        if not os.path.exists("results"):
            os.makedirs("results")

        filename = f"results/brainstorm_{query.replace(' ', '_').lower()}.md"
        with open(filename, "w") as f:
            f.write(f"# Brainstorming Report: {query}\n\n")
            f.write(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("| Score | Video | Views | Median | Subs | Channel | Success Criteria | Subtopics Covered | Reusable Insights | Ultimate Titles | Alternate Hooks |\n")
            f.write("|-------|-------|-------|--------|------|---------|------------------|-------------------|-------------------|-----------------|-----------------|\n")

            for r in results:
                subs = f"{r['subscribers']:,}" if r.get('subscribers') else "N/A"

                # Sanitize all text fields that might contain newlines or special characters
                success = self._sanitize_table_cell(r.get('success_criteria', 'N/A'))
                subtopics = self._sanitize_table_cell(r.get('subtopics_covered', 'N/A'))
                insights = self._sanitize_table_cell(r.get('reusable_insights', 'N/A'))
                titles = self._sanitize_table_cell(r.get('ultimate_titles', 'N/A'))
                hooks = self._sanitize_table_cell(r.get('alternate_hooks', 'N/A'))

                f.write(f"| {r['ratio']:.2f}x | [{r['title']}]({r['url']}) | {r['views']:,} | {int(r['median_views']):,} | {subs} | {r['channel']} | {success} | {subtopics} | {insights} | {titles} | {hooks} |\n")

        print(f"[bold green][+] Unified Brainstorm report saved to: {filename}[/bold green]")
