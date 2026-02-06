from agents.base import BaseAgent
from agents.script_agent import ScriptAgent
from agents.script_generation_utils import ScriptGenerationUtils
from agents.teleprompter_formatter import TeleprompterFormatter
from agents.prompts import SCRIPTWRITER_SYSTEM, SCRIPTWRITER_QUALITY_GUIDE
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional
import os
from datetime import datetime
import json
import config

class QuickScriptAgent(BaseAgent):
    """
    Quick script generation directly from notes.
    Bypasses angle generation, research, and structure phases.
    Uses sensible defaults for all inputs.
    """

    def __init__(self, use_database: bool = False):
        super().__init__(use_database=use_database)
        self.console = Console()

        # Load script checklist
        with open('checklists/script_checklist.json', 'r') as f:
            self.checklist = json.load(f)

    def run(self, topic: str, notes: str = "", duration: int = 11,
            reading_level: Optional[str] = None, audience: Optional[str] = None) -> Optional[dict]:
        """
        Generate script using checklist-driven approach with iteration support.

        Args:
            topic: Video topic
            notes: User's content notes
            duration: Video duration in minutes (default: 11)
            reading_level: Target reading level (default: from config)
            audience: Target audience (default: from config)

        Returns:
            dict with script and teleprompter_script, or None if rejected
        """
        # Set defaults from config
        reading_level = reading_level or config.QUICK_SCRIPT_READING_LEVEL
        audience = audience or config.QUICK_SCRIPT_TARGET_AUDIENCE

        self.console.print(f"\n[bold cyan]⚡ Quick Script Generation for: {topic}[/bold cyan]\n")
        self.console.print(f"[yellow]Duration: {duration} min | Reading Level: {reading_level} | Audience: {audience}[/yellow]\n")

        # Iteration loop
        script = None
        regeneration_feedback = None
        previous_script = None
        previous_scores = None

        for iteration in range(1, config.QUICK_SCRIPT_MAX_ITERATIONS + 1):
            # Generate script
            script = self._generate_script_with_checklist(
                topic=topic,
                notes=notes,
                duration=duration,
                reading_level=reading_level,
                audience=audience,
                regeneration_feedback=regeneration_feedback,
                previous_script=previous_script,
                previous_scores=previous_scores
            )

            # Score script against checklist
            scores = self._score_script_with_checklist(script, topic)

            # Detect score regression
            score_regressed = False
            if previous_scores and scores['overall_score'] < previous_scores['overall_score']:
                score_regressed = True
                score_diff = previous_scores['overall_score'] - scores['overall_score']
                self.console.print(f"\n[bold red]⚠️  WARNING: Score decreased by {score_diff} points![/bold red]")
                self.console.print(f"[yellow]Previous: {previous_scores['overall_score']}/100 → Current: {scores['overall_score']}/100[/yellow]")
                self.console.print("[yellow]This iteration made things worse. Consider rejecting to keep the previous version.[/yellow]\n")

            # Show to user and get action
            action, feedback = self._show_script_and_prompt_user(
                script=script,
                scores=scores,
                iteration=iteration,
                max_iterations=config.QUICK_SCRIPT_MAX_ITERATIONS,
                score_regressed=score_regressed,
                previous_scores=previous_scores
            )

            if action == 'accept':
                break
            elif action == 'reject':
                self.console.print("[red]Script rejected. Exiting without saving.[/red]")
                return None
            elif action == 'regenerate':
                # Store current script and scores as "previous" for next iteration
                previous_script = script
                previous_scores = scores

                # Build regeneration feedback combining user input + checklist scores
                feedback_parts = []

                if feedback:
                    feedback_parts.append(f"User feedback: {feedback}")

                # Add automatic feedback from low-scoring categories
                low_categories = [cat for cat, score in scores['category_scores'].items() if score < 8]
                if low_categories:
                    feedback_parts.append(f"Low-scoring categories to improve: {', '.join(low_categories)}")

                if scores.get('improvement_suggestions'):
                    feedback_parts.append("Specific improvements needed:")
                    feedback_parts.extend([f"- {s}" for s in scores['improvement_suggestions'][:3]])

                regeneration_feedback = "\n".join(feedback_parts)
                self.console.print(f"\n[yellow]Regenerating script (attempt {iteration + 1})...[/yellow]\n")
                continue

        # Format for teleprompter
        self.console.print("\n[yellow]Formatting for Elgato teleprompter...[/yellow]")
        formatter = TeleprompterFormatter(use_database=self.use_database)
        teleprompter_script = formatter.run(script)

        # Save outputs
        result = {
            "topic": topic,
            "notes": notes,
            "duration": duration,
            "reading_level": reading_level,
            "audience": audience,
            "script": script,
            "teleprompter_script": teleprompter_script
        }

        self._save_outputs(topic, result)

        self.console.print(f"\n[bold green]✅ Quick script generation complete![/bold green]")
        topic_slug = topic.replace(' ', '_').lower()
        self.console.print(f"\n[cyan]Files saved:[/cyan]")
        self.console.print(f"  - Teleprompter: results/scripts/quick_teleprompter_{topic_slug}_*.txt")
        self.console.print(f"  - Raw script: results/scripts/quick_script_{topic_slug}_*.txt")

        return result

    def _generate_script_with_checklist(self, topic: str, notes: str,
                                        duration: int, reading_level: str,
                                        audience: str, regeneration_feedback: Optional[str] = None,
                                        previous_script: Optional[str] = None,
                                        previous_scores: Optional[dict] = None) -> str:
        """
        Generate script using checklist as quality guide.
        For regenerations, improves the previous script instead of starting from scratch.
        """
        regeneration_section = ""
        if regeneration_feedback and previous_script and previous_scores:
            improvement_suggestions = []
            if regeneration_feedback:
                improvement_suggestions.append(regeneration_feedback)

            low_categories = [cat for cat, score in previous_scores['category_scores'].items() if score < 8]
            if low_categories:
                improvement_suggestions.append(f"Improve these categories: {', '.join(low_categories)}")

            regeneration_section = ScriptGenerationUtils.build_regeneration_section(
                previous_script=previous_script,
                previous_scores=previous_scores['category_scores'],
                improvement_suggestions=improvement_suggestions,
                previous_overall_score=previous_scores['overall_score']
            )
        elif regeneration_feedback:
            regeneration_section = f"""
REGENERATION FEEDBACK: {regeneration_feedback}
Address this feedback while keeping the speaker's voice and best parts of the script.
"""

        prompt = f"""Make a YouTube script for "{topic}" with key insights and URL suggestions.

Keep the video under {duration} minutes. It should be understandable to a {audience} at a {reading_level} reading level.

THE SPEAKER'S NOTES (write in THEIR voice — use their stories, examples, credentials, and speaking style):
{notes}

{SCRIPTWRITER_QUALITY_GUIDE}
{regeneration_section}

SCRIPT FORMAT:
- Write the complete script as the speaker would actually say it, section by section with timestamps
- Use section headers like "HOOK (0:00-0:08)", "SECTION 1: TITLE (0:45-2:30)"
- After the spoken script, add these SEPARATE sections at the end:
  1. KEY URL SUGGESTIONS FOR B-ROLL
  2. PRODUCTION NOTES (B-roll cues, SFX, camera directions, pattern interrupts, energy/pacing notes)
  3. Brief CHECKLIST COMPLIANCE summary (one line per category, not an essay)

Keep production annotations OUT of the spoken script body — they go in the production notes at the end."""

        try:
            return ScriptGenerationUtils.call_litellm(prompt,
                                                       system_prompt=SCRIPTWRITER_SYSTEM)
        except Exception as e:
            print(f"[!] Script generation failed: {e}")
            raise

    def _score_script_with_checklist(self, script: str, topic: str) -> dict:
        """
        Automatically score script against checklist criteria using ChecklistAgent.

        Returns:
            dict with overall_score, category_scores, strengths, weaknesses, suggestions
        """
        print(f"[*] Scoring script against checklist criteria...")

        # Use utility to evaluate script
        quality_result = ScriptGenerationUtils.evaluate_with_checklist(script, topic, [])

        return {
            'overall_score': quality_result.get('overall_score', 0),
            'category_scores': quality_result.get('category_scores', {}),
            'improvement_suggestions': quality_result.get('improvement_suggestions', []),
            'fact_check': quality_result.get('fact_check', {}),
            'estimated_performance': quality_result.get('estimated_performance', {})
        }

    def _show_script_and_prompt_user(self, script: str, scores: dict, iteration: int, max_iterations: int,
                                     score_regressed: bool = False, previous_scores: Optional[dict] = None) -> tuple:
        """
        Display script with checklist scores and prompt for action.

        Args:
            script: Generated script text
            scores: Dict with overall_score, category_scores, improvement_suggestions, etc.
            iteration: Current iteration number
            max_iterations: Maximum iterations allowed
            score_regressed: Whether the score decreased from previous iteration
            previous_scores: Previous iteration's scores (if any)

        Returns:
            (action, feedback) where action is 'accept', 'reject', or 'regenerate'
            and feedback is user's optional feedback text
        """
        # Display script preview
        self.console.print("\n" + "="*80)
        self.console.print(f"[bold cyan]Generated Script (Iteration {iteration}/{max_iterations})[/bold cyan]")
        self.console.print("="*80 + "\n")

        # Show first 2000 chars + last 500 chars for preview
        if len(script) > 3000:
            preview = script[:2000] + "\n\n[... middle content truncated ...]\n\n" + script[-500:]
            self.console.print(preview)
            self.console.print(f"\n[yellow]Full script: {len(script)} characters, ~{len(script.split())} words[/yellow]")
        else:
            self.console.print(script)

        # Display checklist scores
        self.console.print("\n" + "="*80)
        self.console.print("[bold yellow]📊 CHECKLIST SCORES[/bold yellow]")
        self.console.print("="*80 + "\n")

        # Overall score with color coding
        overall_score = scores['overall_score']
        if overall_score >= 90:
            score_color = "green"
            score_emoji = "✅"
        elif overall_score >= 80:
            score_color = "yellow"
            score_emoji = "⚠️"
        else:
            score_color = "red"
            score_emoji = "❌"

        self.console.print(f"{score_emoji} [bold {score_color}]Overall Score: {overall_score}/100[/bold {score_color}]\n")

        # Category scores in a table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Category", style="dim")
        table.add_column("Score", justify="right")
        table.add_column("Status", justify="center")

        for category, score in scores['category_scores'].items():
            if score >= 9:
                status = "[green]✓ Excellent[/green]"
            elif score >= 7:
                status = "[yellow]○ Good[/yellow]"
            else:
                status = "[red]✗ Needs work[/red]"

            table.add_row(category, f"{score}/10", status)

        self.console.print(table)
        self.console.print()

        # Show score comparison if there was regression
        if score_regressed and previous_scores:
            self.console.print("[bold red]📉 Score Regression Detected[/bold red]\n")
            comparison_table = Table(show_header=True, header_style="bold yellow")
            comparison_table.add_column("Category", style="dim")
            comparison_table.add_column("Previous", justify="right")
            comparison_table.add_column("Current", justify="right")
            comparison_table.add_column("Change", justify="center")

            for category in scores['category_scores'].keys():
                prev = previous_scores['category_scores'].get(category, 0)
                curr = scores['category_scores'][category]
                diff = curr - prev

                if diff < 0:
                    change_str = f"[red]↓ {diff}[/red]"
                elif diff > 0:
                    change_str = f"[green]↑ +{diff}[/green]"
                else:
                    change_str = "[dim]→ 0[/dim]"

                comparison_table.add_row(category, f"{prev}/10", f"{curr}/10", change_str)

            self.console.print(comparison_table)
            self.console.print()

        # Show improvement suggestions if score < 90
        if overall_score < 90 and scores.get('improvement_suggestions'):
            self.console.print("[bold yellow]💡 Improvement Suggestions:[/bold yellow]")
            for suggestion in scores['improvement_suggestions'][:5]:  # Show top 5
                self.console.print(f"  • {suggestion}")
            self.console.print()

        # Show strengths if any category scored 9+
        strong_categories = [cat for cat, score in scores['category_scores'].items() if score >= 9]
        if strong_categories:
            self.console.print(f"[bold green]✨ Strengths:[/bold green] {', '.join(strong_categories)}")
            self.console.print()

        # Prompt user
        self.console.print("\n" + "="*80)
        self.console.print("[bold]What would you like to do?[/bold]")
        self.console.print("  [green]y[/green] - Accept this script and save")
        self.console.print("  [red]n[/red] - Reject and exit without saving")

        if iteration < max_iterations:
            self.console.print(f"  [yellow]r[/yellow] - Regenerate (with optional feedback) [{max_iterations - iteration} attempts remaining]")

        action = input("\nYour choice (y/n/r): ").lower().strip()

        if action == 'r' and iteration < max_iterations:
            self.console.print("\n[yellow]What would you like to improve?[/yellow]")
            self.console.print("[dim](Press Enter to skip for automatic improvement based on checklist)[/dim]")
            feedback = input("Feedback: ").strip()
            return ('regenerate', feedback if feedback else None)
        elif action == 'y':
            return ('accept', None)
        else:
            return ('reject', None)

    def _save_outputs(self, topic: str, result: dict):
        """Save script outputs"""
        os.makedirs("results/scripts", exist_ok=True)

        topic_slug = topic.replace(' ', '_').lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save teleprompter script
        teleprompter_file = f"results/scripts/quick_teleprompter_{topic_slug}_{timestamp}.txt"
        with open(teleprompter_file, "w") as f:
            f.write(result["teleprompter_script"])

        # Save raw script
        script_file = f"results/scripts/quick_script_{topic_slug}_{timestamp}.txt"
        with open(script_file, "w") as f:
            f.write(f"# Quick Script: {topic}\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## User Notes\n{result['notes']}\n\n")
            f.write(f"## Complete Script\n\n{result['script']}")
