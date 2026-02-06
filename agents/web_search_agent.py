from agents.base import BaseAgent
from agents.prompts import RESEARCH_SYSTEM
import litellm
import config
import json
import requests
import os
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

class WebSearchAgent(BaseAgent):
    """Search the web for research insights on selected subtopics."""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.RESEARCH_MODEL
        self.console = Console()
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    def run(self, subtopics: list, topic: str, interactive: bool = True) -> dict:
        """
        Search web for each subtopic and curate insights.

        Returns:
            Dict mapping subtopic_title -> list of research insights
        """
        if not self.api_key or not self.search_engine_id:
            self.console.print("[yellow]⚠️  Google Search API not configured. Skipping web research.[/yellow]")
            return {}

        all_insights = {}

        for subtopic in subtopics:
            self.console.print(f"\n[cyan]Searching web for: {subtopic['title']}[/cyan]")
            insights = self._search_subtopic(subtopic, topic)
            all_insights[subtopic['title']] = insights

        if interactive:
            return self._get_user_curation(all_insights)
        else:
            return all_insights

    def _search_subtopic(self, subtopic: dict, topic: str) -> list:
        """Perform web search and extract insights for one subtopic."""
        # Build query
        key_points = ' '.join(subtopic.get('key_points', [])[:2])
        query = f"{topic} {subtopic['title']} {key_points}"

        # Search Google
        search_results = self._google_search(query, num_results=5)

        if not search_results:
            return []

        # Extract insights using LLM
        return self._extract_insights(subtopic, search_results)

    def _google_search(self, query: str, num_results: int = 5) -> list:
        """Call Google Custom Search JSON API."""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": num_results
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet")
                })
            return results
        except Exception as e:
            self.console.print(f"[yellow]Search failed: {e}[/yellow]")
            return []

    def _extract_insights(self, subtopic: dict, search_results: list) -> list:
        """Use LLM to extract key insights from search results."""
        prompt = f"""
Analyze these web search results for "{subtopic['title']}":

{json.dumps(search_results, indent=2)}

Extract 3-5 key insights that would add depth to a YouTube video script.
Each insight should:
- Be factual and specific (include data/statistics if available)
- Cite the source
- Be immediately usable in narration

Return JSON:
{{
    "insights": [
        {{
            "text": "Specific factual insight with data",
            "source_title": "Article title",
            "source_url": "https://...",
            "relevance_score": 8
        }}
    ]
}}
"""

        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": RESEARCH_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=30
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("insights", [])
        except Exception as e:
            self.console.print(f"[yellow]Insight extraction failed: {e}[/yellow]")
            return []

    def _get_user_curation(self, all_insights: dict) -> dict:
        """Present insights to user and ask what to include."""
        curated = {}

        for subtopic_title, insights in all_insights.items():
            if not insights:
                continue

            self.console.print(f"\n[bold cyan]Research for: {subtopic_title}[/bold cyan]")

            table = Table(title=f"Found {len(insights)} insights")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Insight", style="white")
            table.add_column("Source", style="green")
            table.add_column("Score", justify="right", width=6)

            for i, insight in enumerate(insights, 1):
                table.add_row(
                    str(i),
                    insight['text'][:100] + "...",
                    insight.get('source_title', 'N/A')[:30],
                    f"{insight.get('relevance_score', 0)}/10"
                )

            self.console.print(table)

            selection = Prompt.ask(
                "Select insights (comma-separated, 'all', or 'skip')",
                default="all"
            )

            if selection.lower() == 'skip':
                continue
            elif selection.lower() == 'all':
                curated[subtopic_title] = insights
            else:
                try:
                    indices = [int(s.strip()) - 1 for s in selection.split(",")]
                    curated[subtopic_title] = [
                        insights[i] for i in indices if 0 <= i < len(insights)
                    ]
                except:
                    self.console.print("[yellow]Invalid input, including all[/yellow]")
                    curated[subtopic_title] = insights

        return curated
