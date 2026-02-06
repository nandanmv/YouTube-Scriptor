from agents.base import BaseAgent
from agents.angle_from_outliers_agent import AngleFromOutliersAgent
from agents.auto_research_agent import AutoResearchAgent
from agents.research_agent import ResearchAgent
from agents.web_search_agent import WebSearchAgent
from agents.structure_agent import StructureAgent
from agents.hook_agent import HookAgent
from agents.script_agent import ScriptAgent
from agents.checklist_agent import ChecklistAgent
from agents.teleprompter_formatter import TeleprompterFormatter
from agents.theme_agent import ThemeAgent
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
import os
from datetime import datetime
import json
import config

class ScriptCreatorAgent(BaseAgent):
    """
    Complete script creation pipeline orchestrator.
    Follows BrainstormAgent pattern with user interaction.
    """

    def __init__(self, use_database: bool = False):
        super().__init__(use_database=use_database)
        self.console = Console()

    def run(self, topic: str, notes: str = "", interactive: bool = True, auto_select: dict = None,
            manual_mode: bool = False, duration: int = None, top_n_outliers: int = None,
            strategy: str = None) -> dict:
        """
        Run complete script creation pipeline.

        Args:
            topic: Video topic
            notes: User's rough notes
            interactive: If True, prompt user for selections
            auto_select: Optional dict with pre-selected options for non-interactive mode
            manual_mode: If True, use manual outlier selection workflow (requires marked videos)
            duration: Target script duration in minutes (defaults to config.DEFAULT_SCRIPT_DURATION)
            top_n_outliers: Number of top videos to analyze in automatic mode (defaults based on strategy)
            strategy: Research strategy - "top_performers" or "outliers" (defaults to config.RESEARCH_STRATEGY)

        Returns:
            Complete workflow results
        """
        # Set defaults
        if duration is None:
            duration = config.DEFAULT_SCRIPT_DURATION
        if strategy is None:
            strategy = config.RESEARCH_STRATEGY
        if top_n_outliers is None:
            if strategy == "top_performers":
                top_n_outliers = config.TOP_PERFORMERS_COUNT
            else:
                top_n_outliers = config.AUTO_RESEARCH_OUTLIER_COUNT
        self.console.print(f"\n[bold cyan]🎬 Starting Script Creation for: {topic}[/bold cyan]\n")

        # Display strategy info
        strategy_display = "Top Performers" if strategy == "top_performers" else "Outliers"
        self.console.print(f"[dim]Strategy: {strategy_display} | Duration: {duration} min | Analyzing: {top_n_outliers} videos[/dim]\n")

        # 1. Generate angles and discover sources
        youtube_sources = []  # Will hold YouTube video sources for citation

        if manual_mode:
            # Manual workflow: Use marked outliers from markdown files
            self.console.print("[yellow]Step 1/7: Generating angles from manually selected outliers...[/yellow]")
            self.console.print("[cyan]💡 Using videos marked in results/outliers/*.md files[/cyan]")
            angle_agent = AngleFromOutliersAgent(use_database=self.use_database)
            angle_result = angle_agent.run(topic)

            # Handle both old (list) and new (dict) return formats
            if isinstance(angle_result, dict):
                angles = angle_result.get('angles', [])
                youtube_sources = angle_result.get('sources', [])
            else:
                angles = angle_result
                youtube_sources = []

            if not angles:
                self.console.print("[bold red]Error: No angles generated. Please select outliers first.[/bold red]")
                self.console.print("[yellow]Run: python3.10 main.py outlier \"<search term>\"[/yellow]")
                self.console.print("[yellow]Then mark videos with [x] in Selection column of results/*.md[/yellow]")
                return {}
        else:
            # Automatic workflow: Use selected strategy
            if strategy == "top_performers":
                self.console.print(f"[yellow]Step 1/7: Analyzing top {top_n_outliers} performing videos...[/yellow]")
                self.console.print(f"[cyan]💡 Finding what's working on YouTube for '{topic}'[/cyan]")
                self.console.print(f"[dim]Filters: Last {config.TOP_PERFORMERS_RECENCY_MONTHS} months, >= {config.TOP_PERFORMERS_MIN_VIEWS:,} views[/dim]")
            else:  # outliers
                self.console.print(f"[yellow]Step 1/7: Finding top {top_n_outliers} outlier videos...[/yellow]")
                self.console.print(f"[cyan]💡 Discovering videos that exceeded channel baseline[/cyan]")

            auto_research_agent = AutoResearchAgent(use_database=self.use_database)
            auto_research_result = auto_research_agent.run(topic, top_n=top_n_outliers, strategy=strategy)

            angles = auto_research_result.get('angles', [])
            youtube_sources = auto_research_result.get('sources', [])
            videos = auto_research_result.get('videos', [])

            if not angles:
                self.console.print("[bold red]Error: No videos found. Try a different search term or adjust filters.[/bold red]")
                return {}

            self.console.print(f"[green]✓ Analyzed {len(videos)} videos, extracted {len(angles)} angles[/green]")

            # Display outliers table
            if videos:
                self._display_outliers_table(videos)

        # 1.5. Analyze overarching themes for the topic
        self.console.print(f"\n[yellow]Step 1.5/7: Analyzing overarching trends for '{topic}'...[/yellow]")
        theme_agent = ThemeAgent(use_database=self.use_database)
        theme_result = theme_agent.run(topic)
        theme_data = theme_result.get('themes', {})
        
        if theme_data:
            self.console.print(f"[green]✓ Analyzed Audience Intent and {len(theme_data.get('recurring_topics', []))} recurring topics[/green]")
        else:
            self.console.print("[yellow]! Standardizing on default themes.[/yellow]")

        if interactive and angles:
            selected_angles = self._get_multi_selection(
                angles,
                "angles",
                "angle_name",
                min_select=1,
                max_select=None  # Allow selecting all
            )
        else:
            # Auto-select: use provided angles or default to first
            if auto_select and auto_select.get("angles"):
                selected_angles = auto_select["angles"]
            else:
                selected_angles = [angles[0]] if angles else []

        # 2. Research subtopics with accumulative selection
        angle_names = ", ".join([a.get('angle_name', 'angle') for a in selected_angles])
        self.console.print(f"\n[yellow]Step 2/7: Researching subtopics for angles: {angle_names}...[/yellow]")
        research_agent = ResearchAgent(use_database=self.use_database)

        if interactive:
            # Use accumulative selection method for interactive mode
            # This returns already-selected subtopics, no need for additional selection
            selected_subtopics = research_agent.run_with_feedback_loop(
                topic=topic,
                angles=selected_angles,
                notes=notes,
                theme_data=theme_data,
                interactive=True,
                max_iterations=config.MAX_RESEARCH_ITERATIONS
            )
            # In interactive mode, subtopics list equals selected ones
            subtopics = selected_subtopics
        else:
            # Non-interactive: use original single-pass method
            subtopics = research_agent.run(topic, selected_angles, notes, theme_data=theme_data)
            # Auto-select: use provided subtopics or default to first 5
            if auto_select and auto_select.get("subtopics"):
                selected_subtopics = auto_select["subtopics"]
            else:
                selected_subtopics = subtopics[:5] if subtopics else []

        # 2.5. Web research for subtopics
        self.console.print(f"\n[yellow]Step 2.5/7: Searching web for research insights...[/yellow]")
        web_search_agent = WebSearchAgent(use_database=self.use_database)
        research_insights = web_search_agent.run(
            subtopics=selected_subtopics,
            topic=topic,
            interactive=interactive
        )

        # 3. Add structure
        self.console.print(f"\n[yellow]Step 3/7: Adding engagement structure (curiosity gaps, open loops)...[/yellow]")
        structure_agent = StructureAgent(use_database=self.use_database)
        structure = structure_agent.run(selected_subtopics, notes)

        # 4. Generate hook and intro options
        self.console.print("\n[yellow]Step 4/7: Generating specific hooks and trailers...[/yellow]")
        hook_agent = HookAgent(use_database=self.use_database)
        hook_result = hook_agent.run(topic, selected_angles, structure, notes=notes, theme_data=theme_data)

        if interactive and hook_result.get("hooks"):
            selected_hook = self._get_user_selection(hook_result["hooks"], "hook", "text")
        else:
            # Auto-select: use provided hook or default to first
            if auto_select and auto_select.get("hook"):
                selected_hook = auto_select["hook"]
            else:
                selected_hook = hook_result.get("hooks", [{}])[0]

        if interactive and hook_result.get("trailers"):
            selected_trailer = self._get_user_selection(hook_result["trailers"], "trailer", "text")
        else:
            # Auto-select: use provided trailer or default to first
            if auto_select and auto_select.get("trailer"):
                selected_trailer = auto_select["trailer"]
            else:
                selected_trailer = hook_result.get("trailers", [{}])[0]

        # 5. Write script
        self.console.print(f"\n[yellow]Step 5/7: Writing complete script ({duration} min target)...[/yellow]")
        script_agent = ScriptAgent(use_database=self.use_database)
        script = script_agent.run(
            topic=topic,
            angles=selected_angles,
            hook=selected_hook,
            trailer=selected_trailer,
            structure=structure,
            research_insights=research_insights,
            notes=notes,
            outro=auto_select.get("outro") if auto_select else None,
            duration=duration,
            youtube_sources=youtube_sources
        )

        # 6. Quality check with regeneration loop
        self.console.print(f"\n[yellow]Step 6/7: Fact-checking and predicting performance...[/yellow]")
        checklist_agent = ChecklistAgent(use_database=self.use_database)
        quality_report = checklist_agent.run(script, topic, selected_angles)

        # Quality loop
        regeneration_count = 0
        previous_script = None  # Track previous script for improvement
        while (quality_report.get('overall_score', 0) < config.QUALITY_THRESHOLD
               and regeneration_count < config.MAX_REGENERATIONS):

            score = quality_report.get('overall_score', 0)
            self.console.print(f"\n[yellow]⚠️  Quality score {score}/100 is below threshold {config.QUALITY_THRESHOLD}[/yellow]")

            # Show detailed quality report
            self._display_quality_report(quality_report)

            if not interactive:
                self.console.print("[yellow]Non-interactive mode: accepting current script[/yellow]")
                break

            # Ask user
            should_regenerate = Confirm.ask(
                f"Regenerate script? (Attempt {regeneration_count + 1}/{config.MAX_REGENERATIONS})",
                default=True
            )

            if not should_regenerate:
                self.console.print("[cyan]✓ User accepted current script[/cyan]")
                break

            # Store current script as "previous" for next iteration
            previous_script = script

            # Regenerate
            regeneration_count += 1
            self.console.print(f"\n[yellow]🔄 Regenerating script (attempt {regeneration_count})...[/yellow]")

            # Build regeneration feedback
            regeneration_feedback = {
                "previous_score": score,
                "improvement_suggestions": quality_report.get('improvement_suggestions', []),
                "category_scores": quality_report.get('category_scores', {})
            }

            # Re-run script agent with feedback AND previous script
            script = script_agent.run(
                topic=topic,
                angles=selected_angles,
                hook=selected_hook,
                trailer=selected_trailer,
                structure=structure,
                research_insights=research_insights,
                notes=notes,
                outro=auto_select.get("outro") if auto_select else None,
                regeneration_feedback=regeneration_feedback,
                previous_script=previous_script,
                duration=duration,
                youtube_sources=youtube_sources
            )

            # Re-evaluate
            new_quality_report = checklist_agent.run(script, topic, selected_angles)

            # Detect score regression
            if new_quality_report.get('overall_score', 0) < quality_report.get('overall_score', 0):
                score_diff = quality_report.get('overall_score', 0) - new_quality_report.get('overall_score', 0)
                self.console.print(f"\n[bold red]⚠️  WARNING: Score decreased by {score_diff} points![/bold red]")
                self.console.print(f"[yellow]Previous: {quality_report.get('overall_score', 0)}/100 → Current: {new_quality_report.get('overall_score', 0)}/100[/yellow]")
                self.console.print("[yellow]Regeneration made things worse.[/yellow]\n")

                # Ask if user wants to keep the worse version
                keep_worse = Confirm.ask("Keep the worse version or revert to previous?", default=False)
                if not keep_worse:
                    self.console.print("[cyan]✓ Reverted to previous script[/cyan]")
                    # Don't update script or quality_report - keep previous version
                    break

            # Update quality report for next iteration
            quality_report = new_quality_report

        # Status message
        if quality_report.get('overall_score', 0) >= config.QUALITY_THRESHOLD:
            self.console.print(f"[bold green]✅ Quality threshold met! ({quality_report['overall_score']}/100)[/bold green]")
        elif regeneration_count >= config.MAX_REGENERATIONS:
            self.console.print(f"[yellow]⚠️  Max regenerations ({config.MAX_REGENERATIONS}) reached. Proceeding with current script.[/yellow]")

        # 7. Format for teleprompter
        self.console.print(f"\n[yellow]Step 7/7: Formatting for Elgato teleprompter...[/yellow]")
        formatter = TeleprompterFormatter(use_database=self.use_database)
        teleprompter_script = formatter.run(script)

        # 8. Save all outputs
        result = {
            "topic": topic,
            "notes": notes,
            "angles": angles,
            "selected_angles": selected_angles,
            "subtopics": subtopics,
            "selected_subtopics": selected_subtopics,
            "research_insights": research_insights,
            "structure": structure,
            "hooks_and_trailers": hook_result,
            "selected_hook": selected_hook,
            "selected_trailer": selected_trailer,
            "script": script,
            "quality_report": quality_report,
            "teleprompter_script": teleprompter_script
        }

        self._save_complete_workflow(topic, result)

        self.console.print(f"\n[bold green]✅ Script creation complete![/bold green]")
        self.console.print(f"Quality Score: [bold]{quality_report.get('overall_score', 0)}/100[/bold]")
        self.console.print(f"\n[cyan]Files saved:[/cyan]")
        topic_slug = topic.replace(' ', '_').lower()
        self.console.print(f"  - Full workflow: results/workflows/script_{topic_slug}_*.json")
        self.console.print(f"  - Teleprompter: results/scripts/teleprompter_{topic_slug}_*.txt")
        self.console.print(f"  - Summary: results/scripts/summary_{topic_slug}_*.md")

        return result

    def _get_user_selection(self, options: list, option_type: str, display_field: str) -> dict:
        """Display options and get user selection"""
        if not options:
            return {}

        table = Table(title=f"Select {option_type.title()}")
        table.add_column("#", style="cyan", width=4)
        table.add_column(option_type.title(), style="magenta")

        if option_type in ["hook", "trailer", "angle"]:
            table.add_column("Score", justify="right", width=6)

        for i, option in enumerate(options, 1):
            text = str(option.get(display_field, ""))[:80]
            if option_type in ["hook", "trailer"]:
                table.add_row(str(i), text, f"{option.get('score', 0)}/10")
            elif option_type == "angle":
                table.add_row(str(i), text, f"{option.get('estimated_performance', 0)}/10")
            else:
                table.add_row(str(i), text)

        self.console.print(table)

        choice = IntPrompt.ask(
            f"Select {option_type} (1-{len(options)})",
            default=1
        )

        # Validate choice
        if 1 <= choice <= len(options):
            return options[choice - 1]
        else:
            self.console.print(f"[yellow]Invalid choice, using first option[/yellow]")
            return options[0]

    def _get_multi_selection(self, options: list, option_type: str, display_field: str, min_select: int = 1, max_select: int = None) -> list:
        """Display options and get multiple selections"""
        if not options:
            return []

        table = Table(title=f"Select {option_type.title()} (pick {min_select}-{max_select or 'all'})")
        table.add_column("#", style="cyan", width=4)
        table.add_column(option_type.title(), style="magenta")

        # Add score column for angles
        if option_type == "angles":
            table.add_column("Score", justify="right", width=6)

        for i, option in enumerate(options, 1):
            text = str(option.get(display_field, ""))[:80]
            if option_type == "angles":
                table.add_row(str(i), text, f"{option.get('estimated_performance', 0)}/10")
            else:
                table.add_row(str(i), text)

        self.console.print(table)

        selections = Prompt.ask(
            f"Select {option_type} numbers (comma-separated, e.g., 1,3,5)"
        )

        try:
            indices = [int(s.strip()) - 1 for s in selections.split(",")]
            selected = [options[i] for i in indices if 0 <= i < len(options)]

            if len(selected) < min_select:
                self.console.print(f"[yellow]Not enough selections, using first {min_select}[/yellow]")
                return options[:min_select]

            if max_select and len(selected) > max_select:
                self.console.print(f"[yellow]Too many selections, using first {max_select}[/yellow]")
                return selected[:max_select]

            return selected
        except:
            self.console.print(f"[yellow]Invalid input, using first {min_select} options[/yellow]")
            return options[:min_select]

    def _display_quality_report(self, quality_report: dict):
        """Display detailed quality report to user."""
        # Category scores table
        scores_table = Table(title="Category Scores")
        scores_table.add_column("Category", style="cyan")
        scores_table.add_column("Score", justify="right")

        for category, score in quality_report.get('category_scores', {}).items():
            color = "green" if score >= 8 else "yellow" if score >= 6 else "red"
            scores_table.add_row(category, f"[{color}]{score}/10[/{color}]")

        self.console.print(scores_table)

        # Improvement suggestions
        suggestions = quality_report.get('improvement_suggestions', [])
        if suggestions:
            suggestions_text = "\n".join([f"• {s}" for s in suggestions])
            self.console.print(Panel(
                suggestions_text,
                title="💡 Improvement Suggestions",
                border_style="yellow"
            ))

    def _display_outliers_table(self, videos: list):
        """Display outliers table with all columns matching markdown format."""
        if not videos:
            return

        self.console.print("\n[bold cyan]📊 Top Outlier Videos[/bold cyan]\n")

        # Create table
        table = Table(show_header=True, header_style="bold magenta", show_lines=True)
        table.add_column("Selection", justify="center", width=8)
        table.add_column("Score", justify="right", width=6)
        table.add_column("Video", width=30)
        table.add_column("Views", justify="right", width=8)
        table.add_column("Median", justify="right", width=8)
        table.add_column("Subs", justify="right", width=8)
        table.add_column("Channel", width=20)
        table.add_column("Success Criteria", width=25)
        table.add_column("Subtopics", width=25)
        table.add_column("Insights", width=25)
        table.add_column("Titles", width=25)
        table.add_column("Hooks", width=25)

        for video in videos:
            # Format numbers
            views_str = f"{video.get('views', 0):,}"
            median_str = f"{video.get('median_views', 0):,}"
            subs_str = f"{video.get('subscribers', 0):,}" if video.get('subscribers') else "N/A"
            ratio_str = f"{video.get('ratio', 0):.1f}x"

            # Truncate long text fields
            def truncate(text, max_len=100):
                text = str(text) if text else "N/A"
                return text[:max_len] + "..." if len(text) > max_len else text

            title = truncate(video.get('title', 'N/A'), 50)
            channel = truncate(video.get('channel', 'N/A'), 25)
            url = video.get('url', '')

            # Add URL to video title
            video_with_url = f"{title}\n[dim]{url}[/dim]"

            # Get AI insights (may not be present for all videos)
            success_criteria = truncate(video.get('success_criteria', 'N/A'))
            subtopics = truncate(video.get('subtopics_covered', 'N/A'))
            insights = truncate(video.get('reusable_insights', 'N/A'))
            titles = truncate(video.get('ultimate_titles', 'N/A'))
            hooks = truncate(video.get('alternate_hooks', 'N/A'))

            table.add_row(
                "[ ]",  # Selection checkbox
                ratio_str,
                video_with_url,
                views_str,
                median_str,
                subs_str,
                channel,
                success_criteria,
                subtopics,
                insights,
                titles,
                hooks
            )

        self.console.print(table)
        self.console.print()

    def _save_complete_workflow(self, topic: str, result: dict):
        """Save all workflow outputs"""
        # Create directories
        os.makedirs("results/workflows", exist_ok=True)
        os.makedirs("results/scripts", exist_ok=True)

        topic_slug = topic.replace(' ', '_').lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save full workflow JSON
        workflow_file = f"results/workflows/script_{topic_slug}_{timestamp}.json"
        with open(workflow_file, "w") as f:
            json.dump(result, f, indent=2)

        # Save teleprompter script
        teleprompter_file = f"results/scripts/teleprompter_{topic_slug}_{timestamp}.txt"
        with open(teleprompter_file, "w") as f:
            f.write(result["teleprompter_script"])

        # Save markdown summary
        summary_file = f"results/scripts/summary_{topic_slug}_{timestamp}.md"
        with open(summary_file, "w") as f:
            f.write(f"# Script Creation Summary: {topic}\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write(f"## Selected Angles\n")
            for angle in result['selected_angles']:
                f.write(f"**{angle.get('angle_name', 'N/A')}** (Score: {angle.get('estimated_performance', 0)}/10)\n")
                f.write(f"{angle.get('description', '')}\n\n")

            f.write(f"## Quality Score\n")
            f.write(f"**{result['quality_report'].get('overall_score', 0)}/100**\n\n")

            f.write(f"## Improvement Suggestions\n")
            for suggestion in result['quality_report'].get('improvement_suggestions', []):
                f.write(f"- {suggestion}\n")

            f.write(f"\n## Selected Hook\n")
            f.write(f"> {result['selected_hook'].get('text', 'N/A')}\n\n")

            f.write(f"## Selected Trailer\n")
            f.write(f"> {result['selected_trailer'].get('text', 'N/A')}\n\n")

            f.write(f"\n## Complete Script\n```\n{result['script']}\n```\n")
