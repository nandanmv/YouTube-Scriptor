import subprocess
import os
import re
from rich.console import Console


class ClipAgent:
    def __init__(self):
        self.console = Console()
        self.output_dir = "results/clips"
        os.makedirs(self.output_dir, exist_ok=True)

    def _parse_timestamp(self, ts: str) -> str:
        """Accept HH:MM:SS, MM:SS, or raw seconds — return HH:MM:SS."""
        ts = ts.strip()
        if re.fullmatch(r"\d+", ts):
            secs = int(ts)
            h, rem = divmod(secs, 3600)
            m, s = divmod(rem, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"
        parts = ts.split(":")
        if len(parts) == 2:
            return f"00:{int(parts[0]):02d}:{int(parts[1]):02d}"
        if len(parts) == 3:
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(parts[2]):02d}"
        raise ValueError(f"Invalid timestamp format: '{ts}'. Use HH:MM:SS, MM:SS, or seconds.")

    def run(self, url: str, start: str, end: str, job_id: str = None, progress_callback=None) -> str | None:  # noqa: ARG002
        """Download a clip segment. Returns the output file path, or None on failure."""
        try:
            start_fmt = self._parse_timestamp(start)
            end_fmt = self._parse_timestamp(end)
        except ValueError as e:
            if progress_callback:
                progress_callback(f"[!] {e}")
            self.console.print(f"[bold red]{e}[/bold red]")
            return None

        section = f"*{start_fmt}-{end_fmt}"
        output_template = os.path.join(self.output_dir, "%(title).80s.%(ext)s")

        if progress_callback:
            progress_callback(f"[*] Downloading clip {start_fmt} → {end_fmt}...")
        self.console.print(f"[cyan]Downloading clip {start_fmt} → {end_fmt}...[/cyan]")

        cmd = [
            "yt-dlp",
            "--download-sections", section,
            "--force-keyframes-at-cuts",
            "-o", output_template,
            "--print", "after_move:filepath",
            url,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Last non-empty line printed is the final filepath
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            file_path = lines[-1] if lines else None

            if file_path and os.path.exists(file_path):
                if progress_callback:
                    progress_callback(f"[+] Clip saved: {os.path.basename(file_path)}")
                self.console.print(f"[bold green]Clip saved: {file_path}[/bold green]")
                return file_path

            if progress_callback:
                progress_callback("[!] Download completed but output file not found.")
            return None

        except subprocess.CalledProcessError as e:
            msg = f"yt-dlp failed (exit {e.returncode}). Is ffmpeg installed?"
            if progress_callback:
                progress_callback(f"[!] {msg}")
            self.console.print(f"[bold red]{msg}[/bold red]")
            if e.stderr:
                self.console.print(f"[dim]{e.stderr[:500]}[/dim]")
            return None
        except FileNotFoundError:
            msg = "yt-dlp not found. Run: pip install yt-dlp"
            if progress_callback:
                progress_callback(f"[!] {msg}")
            self.console.print(f"[bold red]{msg}[/bold red]")
            return None
