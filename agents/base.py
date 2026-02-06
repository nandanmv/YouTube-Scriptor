import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import config

class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        """
        Initialize agent with optional database support and AI model.

        Args:
            use_database: If True, save results to database in addition to markdown
            ai_model: AI model override (optional)
        """
        self.use_database = use_database
        self.ai_model = ai_model  # Store for subclasses
        if use_database:
            from storage.database import AnalysisStore
            self.store = AnalysisStore()

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    def save_results(self, search_term: str, outliers: list, job_id: Optional[str] = None):
        """
        Save results to markdown file and optionally to database.

        Args:
            search_term: Search query term
            outliers: List of outlier video dictionaries
            job_id: Optional job ID for database storage

        Returns:
            Path to markdown file
        """
        if not os.path.exists("results"):
            os.makedirs("results")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"results/{search_term.replace(' ', '_').lower()}_{timestamp}.md"
        with open(filename, "w") as f:
            f.write(f"# Results for '{search_term}'\n\n")
            f.write(f"- **Agent**: {self.__class__.__name__}\n")
            f.write(f"- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Threshold**: {config.OUTLIER_THRESHOLD}x\n\n")
            
            f.write("| Selection | Shortlist | Score | Title | Views | Median | Subscribers | Channel | URL |\n")
            f.write("|:---:|:---:|-------|-------|-------|--------|-------------|---------|-----|\n")

            for o in outliers:
                subs = f"{o['subscribers']:,}" if o.get('subscribers') else "N/A"
                f.write(f"| [ ] | [ ] | {o['ratio']:.2f}x | {o['title']} | {o['views']:,} | {int(o['median_views']):,} | {subs} | {o['channel']} | [Link]({o['url']}) |\n")

        # NEW: Also save to database if enabled
        if self.use_database and job_id:
            self.store.save_outliers(job_id, outliers)

        return filename
