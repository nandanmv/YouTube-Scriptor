from agents.base import BaseAgent
from agents.prompts import RESEARCH_SYSTEM
import litellm
import config
import json
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.panel import Panel

class ResearchAgent(BaseAgent):
    """Perform web research to find relevant subtopics"""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.RESEARCH_MODEL
        self.console = Console()
        self.iteration_history = []  # Track all attempts

    def run(self, topic: str, angles: list, notes: str, theme_data: dict = None, outlier_sources: list = None) -> list:
        """
        Generate subtopics covering all selected angles, prioritized by theme data.

        Args:
            topic: Main video topic
            angles: List of selected angle dictionaries
            notes: User's rough notes
            theme_data: Data from ThemeAgent (Audience Intent, Success Patterns, etc.)
            outlier_sources: List of outlier video data (title, subtopics, insights, success_criteria)

        Returns:
            List of subtopic dictionaries with title, description, key_points
        """
        angle_names = ", ".join([a.get('angle_name', 'angle') for a in angles])
        print(f"[*] ResearchAgent researching subtopics for angles: {angle_names}...")

        # Use LLM to generate subtopics
        subtopics = self._research_subtopics(topic, angles, notes, theme_data=theme_data, outlier_sources=outlier_sources)

        print(f"[+] Found {len(subtopics)} subtopics")
        return subtopics

    def _research_subtopics(self, topic: str, angles: list, notes: str, 
                           theme_data: dict = None, iteration: int = 1,
                           outlier_sources: list = None) -> list:
        """
        Generate subtopics based on research and market themes.

        Args:
            topic: Main video topic
            angles: Selected angle dictionaries
            notes: User's rough notes
            theme_data: Metadata from ThemeAgent
            iteration: Current iteration number
            outlier_sources: List of outlier video data (title, subtopics, insights, success_criteria)

        Returns:
            List of subtopic dictionaries
        """
        # Build angles text
        angles_text = "\n".join([
            f"- **{a['angle_name']}**: {a['description']}"
            for a in angles
        ])

        theme_text = ""
        if theme_data:
            theme_text = f"""
MARKET THEMES (PRIORITIZE THESE):
- **Audience Intent**: {theme_data.get('audience_intent', 'N/A')}
- **Recurring Topics**: {", ".join(theme_data.get('recurring_topics', []))}
- **Universal Success Patterns**: {", ".join(theme_data.get('universal_success_criteria', []))}
"""

        sources_text = ""
        if outlier_sources:
            sources_text = "\nOUTLIER VIDEOS (What these successful videos actually discussed):\n"
            for s in outlier_sources[:10]:
                title = s.get('title', '')
                subtopics = s.get('subtopics', '') or s.get('subtopics_covered', '')
                insights = s.get('reusable_insights', '')
                success = s.get('success_criteria', '')
                if title:
                    sources_text += f"- \"{title}\"\n"
                    if subtopics:
                        sources_text += f"  Topics covered: {subtopics}\n"
                    if insights:
                        sources_text += f"  Key insights: {insights}\n"
                    if success:
                        sources_text += f"  Success criteria: {success}\n"

        saturated_text = ""
        if theme_data:
            saturated = theme_data.get('saturated_angles', [])
            if saturated:
                saturated_text = f"\nSATURATED ANGLES (common in the market — include them as subtopics if the outlier videos covered them; do NOT auto-exclude):\n"
                saturated_text += "\n".join(f"- {a}" for a in saturated)
                saturated_text += "\n"

        prompt = f"""
Create YouTube video subtopics for "{topic}".

{sources_text}
{theme_text}
{saturated_text}
SELECTED ANGLES (USE AS PERSPECTIVE/FLAVOR):
{angles_text}

User notes: {notes}

Generate 15-20 subtopics grounded in what the outlier videos actually discuss.
Base subtopics on real topics covered in the videos above — not generic assumptions.
The Selected Angles determine the STYLE and PERSPECTIVE of presentation.
Include both open-gap and saturated topics if they appear in the successful videos.
Each subtopic should:
- Be drawn from what the outlier videos actually cover
- Support the chosen angle
- Be interesting and valuable
- Flow logically
- Include specific points to cover

Return JSON: {{
    "subtopics": [
        {{
            "title": "Subtopic title",
            "description": "What this section covers",
            "key_points": ["Point 1", "Point 2", ...],
            "estimated_duration": "2-3 minutes"
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
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("subtopics", [])
        except Exception as e:
            print(f"[!] Subtopic research failed: {e}")
            return self._get_default_subtopics(topic, angles)

    def run_with_feedback_loop(self, topic: str, angles: list, notes: str,
                               theme_data: dict = None, interactive: bool = True, 
                               max_iterations: int = None, outlier_sources: list = None) -> list:
        """
        Generate subtopics with accumulative selection model and theme awareness.

        Args:
            topic: Main video topic
            angles: List of selected angle dictionaries
            notes: User's rough notes
            theme_data: Metadata from ThemeAgent
            interactive: If True, allow user to select and request more subtopics
            max_iterations: Maximum research iterations allowed (defaults to config)
        """
        if max_iterations is None:
            max_iterations = config.MAX_RESEARCH_ITERATIONS

        angle_names = ", ".join([a.get('angle_name', 'angle') for a in angles])
        print(f"[*] ResearchAgent researching subtopics for angles: {angle_names}...")

        # Initial generation
        all_subtopics = self._research_subtopics(topic, angles, notes, theme_data=theme_data, iteration=1, outlier_sources=outlier_sources)
        self.iteration_history.append({
            "iteration": 1,
            "subtopics": all_subtopics
        })

        print(f"[+] Generated {len(all_subtopics)} initial subtopics")

        if not interactive:
            return all_subtopics

        # Accumulative selection loop
        selected_subtopics = []
        iteration = 1
        remaining_subtopics = all_subtopics.copy()

        while iteration <= max_iterations:
            # Display current batch of subtopics
            self._display_subtopics_for_selection(remaining_subtopics, selected_subtopics, iteration)

            # Ask user to select from current batch
            if remaining_subtopics:
                selections = Prompt.ask(
                    "\nSelect subtopics to keep (comma-separated numbers, or 'all' for all, or 'skip' to skip)",
                    default="all"
                )

                if selections.lower() == 'all':
                    selected_subtopics.extend(remaining_subtopics)
                    remaining_subtopics = []
                elif selections.lower() != 'skip':
                    try:
                        indices = [int(s.strip()) - 1 for s in selections.split(",")]
                        for idx in indices:
                            if 0 <= idx < len(remaining_subtopics):
                                selected_subtopics.append(remaining_subtopics[idx])
                        # Remove selected items from remaining
                        remaining_subtopics = [s for i, s in enumerate(remaining_subtopics) if i not in indices]
                    except:
                        self.console.print("[yellow]Invalid input, skipping selection[/yellow]")

            # Show current selection count
            self.console.print(f"\n[cyan]Selected {len(selected_subtopics)} subtopics so far[/cyan]")

            # Ask if user wants more
            if iteration >= max_iterations:
                self.console.print(f"[yellow]⚠️  Max iterations ({max_iterations}) reached.[/yellow]")
                break

            want_more = Confirm.ask(
                "\nGenerate more subtopics?",
                default=False
            )

            if not want_more:
                self.console.print("[cyan]✓ Proceeding with selected subtopics[/cyan]")
                break

            # Generate more subtopics
            iteration += 1
            self.console.print(f"\n[yellow]🔄 Generating more subtopics (batch {iteration}/{max_iterations})...[/yellow]")

            # Generate new batch, excluding already selected topics
            new_subtopics = self._generate_additional_subtopics(
                topic, angles, notes, selected_subtopics, iteration, theme_data=theme_data, outlier_sources=outlier_sources
            )

            self.iteration_history.append({
                "iteration": iteration,
                "subtopics": new_subtopics
            })

            print(f"[+] Generated {len(new_subtopics)} additional subtopics")

            # Add to remaining pool
            remaining_subtopics = new_subtopics

        # Final summary
        if selected_subtopics:
            self._display_final_selection(selected_subtopics)
        else:
            self.console.print("[yellow]No subtopics selected, using all from last batch[/yellow]")
            selected_subtopics = all_subtopics

        return selected_subtopics

    def _generate_additional_subtopics(self, topic: str, angles: list, notes: str,
                                       selected_subtopics: list, iteration: int,
                                       theme_data: dict = None, outlier_sources: list = None) -> list:
        """
        Generate new subtopics with theme awareness.
        """
        # Build list of already covered topics
        covered_topics = "\n".join([
            f"- {s.get('title', 'N/A')}"
            for s in selected_subtopics
        ])

        # Build angles text
        angles_text = "\n".join([
            f"- **{a['angle_name']}**: {a['description']}"
            for a in angles
        ])

        theme_text = ""
        if theme_data:
            theme_text = f"""
MARKET THEMES (PRIORITIZE THESE):
- **Audience Intent**: {theme_data.get('audience_intent', 'N/A')}
- **Recurring Topics**: {", ".join(theme_data.get('recurring_topics', []))}
- **Universal Success Patterns**: {", ".join(theme_data.get('universal_success_criteria', []))}
"""

        sources_text = ""
        if outlier_sources:
            sources_text = "\nOUTLIER VIDEOS (What these successful videos actually discussed):\n"
            for s in outlier_sources[:10]:
                title = s.get('title', '')
                subtopics = s.get('subtopics', '') or s.get('subtopics_covered', '')
                insights = s.get('reusable_insights', '')
                success = s.get('success_criteria', '')
                if title:
                    sources_text += f"- \"{title}\"\n"
                    if subtopics:
                        sources_text += f"  Topics covered: {subtopics}\n"
                    if insights:
                        sources_text += f"  Key insights: {insights}\n"
                    if success:
                        sources_text += f"  Success criteria: {success}\n"

        saturated_text = ""
        if theme_data:
            saturated = theme_data.get('saturated_angles', [])
            if saturated:
                saturated_text = f"\nSATURATED ANGLES (common in the market — include them as subtopics if the outlier videos covered them; do NOT auto-exclude):\n"
                saturated_text += "\n".join(f"- {a}" for a in saturated)
                saturated_text += "\n"

        prompt = f"""
Create NEW YouTube video subtopics for "{topic}".

{sources_text}
{theme_text}
{saturated_text}
SELECTED ANGLES (USE AS PERSPECTIVE/FLAVOR):
{angles_text}

User notes: {notes}

IMPORTANT: The following subtopics have already been selected. Generate DIFFERENT subtopics that complement these:
{covered_topics}

Generate 15-20 NEW subtopics that:
- Do NOT repeat the already selected topics above
- Complement and expand on the selected topics
- Support the chosen angles
- Are interesting and valuable
- Flow logically
- Include specific points to cover

Return JSON: {{
    "subtopics": [
        {{
            "title": "Subtopic title",
            "description": "What this section covers",
            "key_points": ["Point 1", "Point 2", ...],
            "estimated_duration": "2-3 minutes"
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
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("subtopics", [])
        except Exception as e:
            print(f"[!] Additional subtopic generation failed: {e}")
            return []

    def _display_subtopics_for_selection(self, current_batch: list,
                                          selected_so_far: list, iteration: int):
        """Display current batch of subtopics for user selection."""
        if not current_batch:
            self.console.print("[yellow]No new subtopics in current batch[/yellow]")
            return

        # Show selected count
        if selected_so_far:
            self.console.print(Panel(
                f"Already selected: {len(selected_so_far)} subtopics",
                border_style="green"
            ))

        # Show current batch
        title = f"New Subtopics (Batch {iteration})" if iteration > 1 else "Subtopics (Batch 1)"
        table = Table(title=title)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Title", style="magenta")
        table.add_column("Description", style="white")
        table.add_column("Duration", style="green", width=12)

        for i, subtopic in enumerate(current_batch, 1):
            title_text = subtopic.get('title', 'N/A')
            desc_text = subtopic.get('description', 'N/A')[:60]
            if len(subtopic.get('description', '')) > 60:
                desc_text += "..."
            duration = subtopic.get('estimated_duration', 'N/A')

            table.add_row(str(i), title_text, desc_text, duration)

        self.console.print(table)

    def _display_final_selection(self, selected_subtopics: list):
        """Display final selected subtopics."""
        if not selected_subtopics:
            return

        table = Table(title=f"Final Selection ({len(selected_subtopics)} subtopics)")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Title", style="magenta")
        table.add_column("Description", style="white")

        for i, subtopic in enumerate(selected_subtopics, 1):
            title_text = subtopic.get('title', 'N/A')
            desc_text = subtopic.get('description', 'N/A')[:80]
            if len(subtopic.get('description', '')) > 80:
                desc_text += "..."

            table.add_row(str(i), title_text, desc_text)

        self.console.print("\n")
        self.console.print(table)
        self.console.print(f"\n[bold green]✓ {len(selected_subtopics)} subtopics ready for script[/bold green]\n")

    def _get_default_subtopics(self, topic: str, angles: list) -> list:
        """Fallback subtopics if API fails"""
        return [
            {
                "title": f"Introduction to {topic}",
                "description": "Overview and context",
                "key_points": ["What it is", "Why it matters", "Who should care"],
                "estimated_duration": "2 minutes"
            },
            {
                "title": "Key Concepts",
                "description": "Core ideas and terminology",
                "key_points": ["Main concepts", "Important terms", "Common misconceptions"],
                "estimated_duration": "3 minutes"
            },
            {
                "title": "Practical Applications",
                "description": "Real-world uses",
                "key_points": ["Use cases", "Examples", "Benefits"],
                "estimated_duration": "3 minutes"
            },
            {
                "title": "Common Challenges",
                "description": "Obstacles and solutions",
                "key_points": ["Typical problems", "Solutions", "Best practices"],
                "estimated_duration": "2 minutes"
            },
            {
                "title": "Getting Started",
                "description": "First steps",
                "key_points": ["What you need", "Where to begin", "Resources"],
                "estimated_duration": "2 minutes"
            }
        ]
