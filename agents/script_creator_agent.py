from agents.base import BaseAgent
from agents.script_agent import ScriptAgent
from agents.checklist_agent import ChecklistAgent
from agents.teleprompter_formatter import TeleprompterFormatter
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
import os
from datetime import datetime
import json
import config


class ScriptCreatorAgent(BaseAgent):
    """
    Script creation pipeline using HTP (Hooks & Talking Points) data.
    Requires: selected_title, selected_topics, selected_hook_script,
              talking_points, outro from the Hooks & Talking Points step.
    Optionally uses outlier video transcript excerpts from research_packet.
    """

    def __init__(self, use_database: bool = False, progress_callback: callable = None):
        super().__init__(use_database=use_database)
        self.console = Console()
        self.progress_callback = progress_callback

    def _log(self, msg: str):
        self.console.print(msg)
        if self.progress_callback:
            self.progress_callback(msg)

    def run(self, topic: str, notes: str = "", interactive: bool = True, auto_select: dict = None,
            manual_mode: bool = False, duration: int = None, top_n_outliers: int = None,
            strategy: str = None, seed_angles: list = None, seed_sources: list = None,
            selected_title: str = None, selected_topics: list = None,
            research_packet: dict = None,
            selected_hook_script: str = None, talking_points: dict = None,
            outro: str = None, shorts_segments: list = None,
            selected_thumbnail: dict = None) -> dict:
        """
        Generate a complete script from Hooks & Talking Points data.

        Required inputs (from the HTP step):
            selected_title: Chosen video title
            selected_topics: List of chosen topic strings
            selected_hook_script: Word-for-word 30-second hook opening
            talking_points: Dict with sections → subsections → bullets
            outro: Word-for-word outro script
            shorts_segments: List of short-form segment specs from HTP

        Optional:
            research_packet: Raw ResearcherAgent output — transcript_sources
                             are extracted and used to ground the script.
            notes: Creator's rough notes / personal voice details
            duration: Target minutes (defaults to config.DEFAULT_SCRIPT_DURATION)
        """
        if duration is None:
            duration = config.DEFAULT_SCRIPT_DURATION

        self._log(f"\n[bold cyan]🎬 Script Creation: {topic}[/bold cyan]\n")

        # Validate required HTP inputs
        missing = []
        if not selected_title:
            missing.append("selected_title")
        if not selected_topics:
            missing.append("selected_topics")
        if not selected_hook_script:
            missing.append("selected_hook_script")
        if not talking_points:
            missing.append("talking_points")
        if missing:
            self._log(f"[bold red]Error: Missing required HTP data: {', '.join(missing)}[/bold red]")
            self._log("[yellow]Complete the 'Hooks & Talking Points' step first.[/yellow]")
            return {}

        # Extract transcript sources from research_packet for grounding
        youtube_sources = []
        if research_packet and isinstance(research_packet, dict):
            transcript_sources = research_packet.get("transcript_sources", [])
            for src in transcript_sources:
                if src.get("title") or src.get("url"):
                    youtube_sources.append(src)

        self._log(f"[dim]Title: {selected_title}[/dim]")
        self._log(f"[dim]Topics: {len(selected_topics)} selected | "
                  f"Transcript sources: {len(youtube_sources)} videos | "
                  f"Shorts: {len(shorts_segments or [])} planned[/dim]\n")

        # Step 1: Write script
        self._log(f"[yellow]Step 1/3: Writing complete script ({duration} min target)...[/yellow]")
        script_agent = ScriptAgent(use_database=self.use_database)
        script = script_agent.run(
            topic=topic,
            angles=[],
            hook={},
            trailer={},
            structure={},
            research_insights={},
            notes=notes,
            outro=outro,
            duration=duration,
            youtube_sources=youtube_sources,
            selected_title=selected_title,
            selected_topics=selected_topics,
            research_packet=research_packet,
            selected_hook_script=selected_hook_script,
            talking_points=talking_points,
            shorts_segments=shorts_segments,
            selected_thumbnail=selected_thumbnail,
        )

        # Step 2: Quality check with regeneration loop
        self._log(f"\n[yellow]Step 2/3: Quality check...[/yellow]")
        checklist_agent = ChecklistAgent(use_database=self.use_database)
        quality_report = checklist_agent.run(script, topic, [])

        regeneration_count = 0
        previous_script = None
        while (quality_report.get("overall_score", 0) < config.QUALITY_THRESHOLD
               and regeneration_count < config.MAX_REGENERATIONS):

            score = quality_report.get("overall_score", 0)
            self._log(f"\n[yellow]⚠️  Quality score {score}/100 below threshold {config.QUALITY_THRESHOLD}[/yellow]")
            self._display_quality_report(quality_report)

            if not interactive:
                self._log("[yellow]Non-interactive mode: accepting current script[/yellow]")
                break

            should_regenerate = Confirm.ask(
                f"Regenerate script? (Attempt {regeneration_count + 1}/{config.MAX_REGENERATIONS})",
                default=True,
            )
            if not should_regenerate:
                self._log("[cyan]✓ User accepted current script[/cyan]")
                break

            previous_script = script
            regeneration_count += 1
            self._log(f"\n[yellow]🔄 Regenerating (attempt {regeneration_count})...[/yellow]")

            regeneration_feedback = {
                "previous_score": score,
                "improvement_suggestions": quality_report.get("improvement_suggestions", []),
                "category_scores": quality_report.get("category_scores", {}),
            }

            script = script_agent.run(
                topic=topic,
                angles=[],
                hook={},
                trailer={},
                structure={},
                research_insights={},
                notes=notes,
                outro=outro,
                regeneration_feedback=regeneration_feedback,
                previous_script=previous_script,
                duration=duration,
                youtube_sources=youtube_sources,
                selected_title=selected_title,
                selected_topics=selected_topics,
                research_packet=research_packet,
                selected_hook_script=selected_hook_script,
                talking_points=talking_points,
                shorts_segments=shorts_segments,
                selected_thumbnail=selected_thumbnail,
            )

            new_report = checklist_agent.run(script, topic, [])

            if new_report.get("overall_score", 0) < quality_report.get("overall_score", 0):
                diff = quality_report.get("overall_score", 0) - new_report.get("overall_score", 0)
                self._log(f"\n[bold red]⚠️  Score dropped by {diff} points![/bold red]")
                if interactive:
                    keep = Confirm.ask("Keep worse version or revert?", default=False)
                    if not keep:
                        self._log("[cyan]✓ Reverted to previous script[/cyan]")
                        break

            quality_report = new_report

        if quality_report.get("overall_score", 0) >= config.QUALITY_THRESHOLD:
            self._log(f"[bold green]✅ Quality threshold met! ({quality_report['overall_score']}/100)[/bold green]")
        elif regeneration_count >= config.MAX_REGENERATIONS:
            self._log(f"[yellow]⚠️  Max regenerations reached. Using current script.[/yellow]")

        # Step 3: Teleprompter format
        self._log(f"\n[yellow]Step 3/3: Formatting for teleprompter...[/yellow]")
        formatter = TeleprompterFormatter(use_database=self.use_database)
        teleprompter_script = formatter.run(script)

        result = {
            "topic": topic,
            "notes": notes,
            "selected_title": selected_title,
            "selected_topics": selected_topics or [],
            "talking_points": talking_points,
            "shorts_segments": shorts_segments or [],
            "research_packet": research_packet,
            "youtube_sources": youtube_sources,
            "script": script,
            "quality_report": quality_report,
            "teleprompter_script": teleprompter_script,
        }

        self._save_complete_workflow(topic, result)

        self._log(f"\n[bold green]✅ Script creation complete![/bold green]")
        self._log(f"Quality Score: [bold]{quality_report.get('overall_score', 0)}/100[/bold]")
        topic_slug = topic.replace(" ", "_").lower()
        self._log(f"[cyan]Saved:[/cyan] results/scripts/teleprompter_{topic_slug}_*.txt")

        return result

    def _display_quality_report(self, quality_report: dict):
        scores_table = Table(title="Category Scores")
        scores_table.add_column("Category", style="cyan")
        scores_table.add_column("Score", justify="right")
        for category, score in quality_report.get("category_scores", {}).items():
            color = "green" if score >= 8 else "yellow" if score >= 6 else "red"
            scores_table.add_row(category, f"[{color}]{score}/10[/{color}]")
        self.console.print(scores_table)

        suggestions = quality_report.get("improvement_suggestions", [])
        if suggestions:
            self.console.print(Panel(
                "\n".join(f"• {s}" for s in suggestions),
                title="💡 Improvement Suggestions",
                border_style="yellow",
            ))

    def _save_complete_workflow(self, topic: str, result: dict):
        """Save workflow JSON and teleprompter text to results/."""
        os.makedirs("results/workflows", exist_ok=True)
        os.makedirs("results/scripts", exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        topic_slug = topic.replace(" ", "_").lower()

        workflow_path = f"results/workflows/script_{topic_slug}_{timestamp}.json"
        with open(workflow_path, "w") as f:
            json.dump(result, f, indent=2, default=str)

        tp_path = f"results/scripts/teleprompter_{topic_slug}_{timestamp}.txt"
        with open(tp_path, "w") as f:
            f.write(result.get("teleprompter_script", result.get("script", "")))

        self._log(f"[dim]Workflow: {workflow_path}[/dim]")
        self._log(f"[dim]Teleprompter: {tp_path}[/dim]")
