from typing import List, Dict, Any
from datetime import datetime
from agents.base import BaseAgent
from agents.outlier_agent import OutlierAgent

class DiscoveryAgent(BaseAgent):
    """Higher-level agent that search for multiple terms and collates a report."""

    def __init__(self, use_database: bool = False):
        """Initialize DiscoveryAgent with optional database support."""
        super().__init__(use_database=use_database)

    def run(self, terms: List[str]):
        """Run multi-term outlier search."""
        print(f"[*] Discovery Agent starting multi-search for: {terms}")
        outlier_agent = OutlierAgent(use_database=self.use_database)
        all_results = []
        
        for term in terms:
            term = term.strip()
            if not term: continue
            results = outlier_agent.run(term)
            all_results.extend(results)
            
        # Deduplicate and sort
        unique_results = {r['url']: r for r in all_results}.values()
        sorted_results = sorted(unique_results, key=lambda x: x['ratio'], reverse=True)
        
        if sorted_results:
            report_name = f"collated_search_{datetime.now().strftime('%H%M%S')}"
            self.save_results(report_name, sorted_results)
            return sorted_results, report_name
        return [], None
