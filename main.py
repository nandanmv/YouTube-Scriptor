import sys
import os
import warnings
from rich.console import Console
from rich.table import Table
from agents.teleprompter_formatter import TeleprompterFormatter
from agents import OutlierAgent, DiscoveryAgent, ScriptCreatorAgent, QuickScriptAgent, AngleFromOutliersAgent
from agents.theme_agent import ThemeAgent
import config

# Silence Pydantic serialization warnings from LiteLLM/Pydantic v2
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

def display_outliers(console: Console, outliers: list, title: str):
    """Helper to display outliers in a rich table."""
    if not outliers:
        console.print(f"[yellow]No outliers found for {title}.[/yellow]")
        return

    table = Table(title=f"Outlier Videos for {title}")
    table.add_column("Score", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Views", justify="right")
    table.add_column("Median", justify="right")
    table.add_column("Subs", justify="right", style="green")
    table.add_column("Channel", style="green")
    table.add_column("URL")

    for o in outliers:
        subs = f"{o['subscribers']:,}" if o.get('subscribers') else "N/A"
        table.add_row(
            f"{o['ratio']:.2f}x",
            o['title'][:50] + "..." if len(o['title']) > 50 else o['title'],
            f"{o['views']:,}",
            f"{int(o['median_views']):,}",
            subs,
            o['channel'],
            o['url']
        )
    console.print(table)

def display_insights(console: Console, insights: list):
    """Helper to display AI insights in a rich table."""
    if not insights:
        return

    table = Table(title="AI Insight Breakdown")
    table.add_column("Video", style="magenta")
    table.add_column("Success Criteria", style="green")
    table.add_column("Reusable Insights", style="cyan")
    table.add_column("Ultimate Titles")
    
    for i in insights:
        # Coerce all fields to strings to prevent NotRenderableError
        title = str(i.get('title', 'N/A'))
        success = str(i.get('success_criteria', 'N/A'))
        insight = str(i.get('reusable_insights', 'N/A'))
        titles = str(i.get('ultimate_titles', 'N/A'))
        
        table.add_row(
            title[:30] + "..." if len(title) > 30 else title,
            success,
            insight,
            titles
        )
    console.print(table)

def display_brainstorm(console: Console, results: list):
    """Helper to display combined brainstorming data."""
    if not results:
        return

    table = Table(title="Brainstorming: Combined Discovery & AI Insights")
    table.add_column("Score", style="cyan")
    table.add_column("Video", style="magenta")
    table.add_column("Views", justify="right")
    table.add_column("Median", justify="right")
    table.add_column("Subs", justify="right", style="green")
    table.add_column("Channel", style="green")
    table.add_column("Success Criteria", style="green")
    table.add_column("Subtopics Covered", style="yellow")
    table.add_column("Ultimate Titles")

    for r in results:
        # Coerce all fields to strings to prevent NotRenderableError
        ratio = str(f"{r.get('ratio', 0):.2f}x")
        title = str(r.get('title', 'N/A'))
        views = f"{r.get('views', 0):,}"
        median = f"{int(r.get('median_views', 0)):,}"
        subs = f"{r.get('subscribers', 0):,}" if r.get('subscribers') else "N/A"
        channel = str(r.get('channel', 'N/A'))
        success = str(r.get('success_criteria', 'N/A'))
        subtopics = str(r.get('subtopics_covered', 'N/A'))
        titles = str(r.get('ultimate_titles', 'N/A'))

        table.add_row(
            ratio,
            title[:30] + "..." if len(title) > 30 else title,
            views,
            median,
            subs,
            channel,
            success[:50] + "..." if len(success) > 50 else success,
            subtopics[:60] + "..." if len(subtopics) > 60 else subtopics,
            titles[:50] + "..." if len(titles) > 50 else titles
        )
    console.print(table)

def display_themes(console: Console, result: dict):
    """Helper to display thematic analysis in a rich table."""
    themes = result.get('themes', {})
    if not themes:
        return

    table = Table(title=f"Market Themes: {result.get('topic', 'N/A')}")
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Patterns & Insights", style="white")

    # Add Common Title Phrases
    phrases = "\n".join([f"• {p}" for p in themes.get('common_title_phrases', [])])
    table.add_row("Title Phrases", phrases)

    # Add Recurring Topics
    topics = "\n".join([f"• {t}" for t in themes.get('recurring_topics', [])])
    table.add_row("Recurring Topics", topics)

    # Add Success Criteria
    criteria = "\n".join([f"• {c}" for c in themes.get('success_criteria_patterns', [])])
    table.add_row("Success Patterns", criteria)

    # Add Audience Intent
    table.add_row("Audience Intent", themes.get('audience_intent', 'N/A'))

    console.print(table)

def display_angles(console: Console, angles: list, topic_title: str):
    """Helper to display synthesized content angles in a rich table."""
    if not angles:
        console.print(f"[yellow]No angles synthesized for {topic_title}.[/yellow]")
        return

    table = Table(title=f"Proven Content Angles: {topic_title}")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Angle Name", style="magenta", no_wrap=False)
    table.add_column("Description", style="white")
    table.add_column("Why It Works", style="green")
    table.add_column("Example Titles", style="yellow")
    table.add_column("Score", justify="right", style="cyan")

    for i, a in enumerate(angles, 1):
        # Format example titles as a bulleted list for readability
        examples = "\n".join([f"• {t}" for t in a.get('example_titles', [])])
        
        table.add_row(
            str(i),
            str(a.get('angle_name', 'N/A')),
            str(a.get('description', 'N/A')),
            str(a.get('why_it_works', 'N/A')),
            examples,
            f"{a.get('estimated_performance', 0)}/10"
        )
    console.print(table)

def main():
    console = Console()
    args = sys.argv[1:]

    if not args:
        console.print("[bold red]Error: No command provided.[/bold red]")
        console.print("\n[bold cyan]Available Commands:[/bold cyan]\n")

        console.print("  [bold]python3.10 main.py create \"<topic>\" [options][/bold]")
        console.print("    → Automatic script creation (analyzes YouTube videos)")
        console.print("    [dim]Default: Top performers, 3 months, 5K+ views, 11 min[/dim]")
        console.print("    Options: --strategy top --duration 11 --top-n 10")

        console.print("\n  [bold]python3.10 main.py outlier \"<search term>\"[/bold]")
        console.print("    → Find outliers manually (for exploration)")

        console.print("\n  [bold]python3.10 main.py discovery \"<term 1>, <term 2>, ...\"[/bold]")
        console.print("    → Multi-term search with collated results")

        console.print("\n  [bold]python3.10 main.py quick-script \"<topic>\" --notes \"your notes\"[/bold]")
        console.print("    → Quick script from notes (bypasses research)")
        console.print("\n  [bold]python3.10 main.py angles \"<topic>\"[/bold]")
        console.print("    → Synthesize angles from outlier videos marked with [x]")

        console.print("\n  [bold]python3.10 main.py theme \"<topic>\"[/bold]")
        console.print("    → Analyze common themes across all outliers for a topic")

        console.print("\n  [bold]python3.10 main.py serve --port 8000[/bold]")
        console.print("    → Start API server")
        console.print("    [dim]Web UI: /, /outliers, /docs[/dim]")

        console.print("\n[bold cyan]Examples:[/bold cyan]")
        console.print("  [dim]python3.10 main.py create \"AI coding tools\"[/dim]")
        console.print("  [dim]python3.10 main.py create \"Python tips\" --strategy top --duration 10[/dim]")
        console.print("  [dim]python3.10 main.py create \"Web dev\" --top-n 15 --notes \"focus on React\"[/dim]")
        return

    command = args[0].lower()

    # NEW: API server command
    if command == "serve":
        port = 8000
        host = "0.0.0.0"

        # Parse optional --port argument
        if "--port" in args:
            try:
                port_idx = args.index("--port")
                if port_idx + 1 < len(args):
                    port = int(args[port_idx + 1])
            except (ValueError, IndexError):
                console.print("[bold red]Error: Invalid port number.[/bold red]")
                return

        # Parse optional --host argument
        if "--host" in args:
            try:
                host_idx = args.index("--host")
                if host_idx + 1 < len(args):
                    host = args[host_idx + 1]
            except (ValueError, IndexError):
                console.print("[bold red]Error: Invalid host.[/bold red]")
                return

        console.print(f"[green]Starting YouTube Analysis API server...[/green]")
        console.print(f"[cyan]Server: http://{host}:{port}[/cyan]")
        console.print(f"[cyan]API Docs: http://{host}:{port}/docs[/cyan]")
        console.print(f"[yellow]Press CTRL+C to stop[/yellow]\n")

        try:
            import uvicorn
            uvicorn.run("api.server:app", host=host, port=port, reload=True)
        except ImportError:
            console.print("[bold red]Error: uvicorn not installed. Run: pip install uvicorn[/bold red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped[/yellow]")
        return
    
    if command == "outlier":
        query = args[1] if len(args) > 1 else config.SEARCH_TERM
        agent = OutlierAgent()
        outliers = agent.run(query)
        display_outliers(console, outliers, f"'{query}'")
        
    elif command == "angles":
        topic = args[1] if len(args) > 1 else None
        agent = AngleFromOutliersAgent()
        result = agent.run(topic=topic)
        display_angles(console, result.get('angles', []), f"'{topic}'" if topic else "Selected Outliers")
        
    elif command == "theme":
        if len(args) < 2:
            console.print("[bold red]Error: No topic provided for theme analysis.[/bold red]")
            return
        topic = args[1]
        agent = ThemeAgent()
        result = agent.run(topic=topic)
        
        if "error" in result:
            console.print(f"[bold red]Error: {result['error']}[/bold red]")
        else:
            display_themes(console, result)
        
    elif command == "discovery":
        if len(args) < 2:
            console.print("[bold red]Error: No terms provided for discovery agent.[/bold red]")
            return
        terms_input = args[1]
        terms = [t.strip() for t in terms_input.split(",")]

        agent = DiscoveryAgent()
        outliers, report_name = agent.run(terms)
        display_outliers(console, outliers, f"Collated Report: {report_name}")

    elif command == "create":
        if len(args) < 2:
            console.print("[bold red]Error: No topic provided for script creation.[/bold red]")
            console.print("Usage: [bold]python3.10 main.py create \"<topic>\" [options][/bold]")
            console.print("\nOptions:")
            console.print("  --notes \"...\"    : Your rough notes/outline")
            console.print("  --duration 11     : Target duration in minutes (default: 11)")
            console.print("  --top-n 10        : Number of top videos to analyze (default: 10)")
            console.print("  --strategy top    : Strategy: 'top' (performers) or 'outliers' (default: top)")
            console.print("  --manual          : Use manual workflow (requires marking videos in markdown)")
            console.print("\nExamples:")
            console.print("  [dim]# Default: Top performers, 11 min, 10 videos[/dim]")
            console.print("  python3.10 main.py create \"AI coding tools\"")
            console.print("\n  [dim]# Custom settings[/dim]")
            console.print("  python3.10 main.py create \"AI tools\" --duration 10 --top-n 15 --strategy top")
            return

        topic = args[1]
        notes = ""
        duration = None  # Will use config default
        top_n_outliers = None  # Will use config default
        strategy = None  # Will use config default
        manual_mode = False

        # Parse flags
        i = 2
        while i < len(args):
            if args[i] == "--notes" and i + 1 < len(args):
                notes = args[i + 1]
                i += 2
            elif args[i] == "--duration" and i + 1 < len(args):
                try:
                    duration = int(args[i + 1])
                except ValueError:
                    console.print(f"[bold red]Error: Invalid duration '{args[i + 1]}'. Must be a number.[/bold red]")
                    return
                i += 2
            elif args[i] == "--top-n" and i + 1 < len(args):
                try:
                    top_n_outliers = int(args[i + 1])
                except ValueError:
                    console.print(f"[bold red]Error: Invalid top-n '{args[i + 1]}'. Must be a number.[/bold red]")
                    return
                i += 2
            elif args[i] == "--strategy" and i + 1 < len(args):
                strategy_input = args[i + 1].lower()
                if strategy_input in ["top", "top_performers"]:
                    strategy = "top_performers"
                elif strategy_input in ["outliers", "outlier"]:
                    strategy = "outliers"
                else:
                    console.print(f"[bold red]Error: Invalid strategy '{args[i + 1]}'. Use 'top' or 'outliers'.[/bold red]")
                    return
                i += 2
            elif args[i] == "--manual":
                manual_mode = True
                i += 1
            else:
                i += 1

        agent = ScriptCreatorAgent()
        result = agent.run(topic=topic, notes=notes, interactive=True,
                          manual_mode=manual_mode, duration=duration,
                          top_n_outliers=top_n_outliers, strategy=strategy)

        if result:
            console.print(f"\n[bold green]Script created successfully![/bold green]")
            console.print(f"Quality Score: {result.get('quality_report', {}).get('overall_score', 0)}/100")
        else:
            console.print(f"\n[yellow]Script creation cancelled or failed.[/yellow]")

    elif command == "quick-script":
        if len(args) < 2:
            console.print("[bold red]Error: No topic provided for quick script.[/bold red]")
            console.print("Usage: [bold]python3.10 main.py quick-script \"<topic>\" --notes \"your notes here\" [--duration 11] [--reading-level \"10th grade\"] [--audience \"business person\"][/bold]")
            return

        topic = args[1]
        notes = ""
        duration = 11
        reading_level = None  # Will use config default
        audience = None  # Will use config default

        # Parse flags
        i = 2
        while i < len(args):
            if args[i] == "--notes" and i + 1 < len(args):
                notes = args[i + 1]
                i += 2
            elif args[i] == "--duration" and i + 1 < len(args):
                try:
                    duration = int(args[i + 1])
                except ValueError:
                    console.print(f"[bold red]Error: Invalid duration '{args[i + 1]}'. Must be a number.[/bold red]")
                    return
                i += 2
            elif args[i] == "--reading-level" and i + 1 < len(args):
                reading_level = args[i + 1]
                i += 2
            elif args[i] == "--audience" and i + 1 < len(args):
                audience = args[i + 1]
                i += 2
            else:
                i += 1

        agent = QuickScriptAgent()
        result = agent.run(topic=topic, notes=notes, duration=duration,
                          reading_level=reading_level, audience=audience)

        if result:
            console.print(f"\n[bold green]Quick script created successfully![/bold green]")
        else:
            console.print(f"\n[yellow]Script generation cancelled.[/yellow]")

    else:
        console.print(f"[bold red]Unknown command: {command}[/bold red]")
        console.print("Available commands: [bold]outlier, discovery, create, quick-script, serve[/bold]")

if __name__ == "__main__":
    main()
