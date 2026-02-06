from agents.base import BaseAgent
import re

class TeleprompterFormatter(BaseAgent):
    """Format script for Elgato teleprompter"""

    def __init__(self, use_database: bool = False):
        super().__init__(use_database=use_database)

    def run(self, script: str) -> str:
        """
        Convert script to Elgato teleprompter format.

        Args:
            script: Complete script with annotations

        Returns:
            Teleprompter-formatted script
        """
        print(f"[*] TeleprompterFormatter converting script...")

        formatted = self._format_for_teleprompter(script)

        print(f"[+] Teleprompter format complete")
        return formatted

    def _format_for_teleprompter(self, script: str) -> str:
        """
        Elgato teleprompter formatting:
        - Remove timestamps (they're for reference, not speaking)
        - Keep B-ROLL/SFX as notes (different formatting)
        - Clean up for reading
        - Large, readable text
        - Natural pauses marked clearly
        """

        lines = script.split("\n")
        formatted_lines = []

        for line in lines:
            # Skip timestamp-only lines
            if re.match(r'^\[[\d:]+\]$', line.strip()):
                continue

            # Remove timestamps from content lines
            line = re.sub(r'^\[[\d:]+\]\s*', '', line)

            # Format B-ROLL as stage direction
            if '[B-ROLL:' in line:
                line = re.sub(r'\[B-ROLL: ([^\]]+)\]', r'\n\n--- SHOW: \1 ---\n\n', line)

            # Format SFX as stage direction
            if '[SFX:' in line:
                line = re.sub(r'\[SFX: ([^\]]+)\]', r'\n\n--- SOUND: \1 ---\n\n', line)

            # Convert [PAUSE] to visual pause marker
            line = line.replace('[PAUSE]', '\n\n... [PAUSE] ...\n\n')

            # Remove speaker labels if present
            line = re.sub(r'^\[SPEAKER\]:\s*', '', line)
            line = re.sub(r'^Hook:\s*', '', line)

            if line.strip():
                formatted_lines.append(line)

        # Join with proper spacing
        formatted = "\n".join(formatted_lines)

        # Add section breaks for better readability
        formatted = formatted.replace('\n\n\n\n', '\n\n')
        formatted = formatted.replace('\n\n\n', '\n\n')

        return formatted
