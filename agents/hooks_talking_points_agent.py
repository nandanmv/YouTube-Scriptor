from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import litellm

import config
from agents.base import BaseAgent


def _extract_json(text: str) -> Any:
    """Parse JSON from raw model output, stripping markdown code fences if present."""
    if not text:
        raise ValueError("Empty response from model")
    # Strip ```json ... ``` or ``` ... ``` wrappers
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    return json.loads(cleaned)

CHECKLIST = {
    "Hook": ["Grabs attention in 3-5 seconds", "Creates curiosity gap", "Relevant to topic"],
    "Structure": ["Clear flow", "Smooth section transitions", "Curiosity gaps placed strategically", "Payoffs delivered", "Strong conclusion"],
    "Content": ["Factually accurate", "Easy to understand", "Value-dense", "No fluff", "No repetitions"],
    "Engagement": ["Pattern interrupts every 60 seconds", "Open loops resolved", "Maintains energy", "Optimized for retention", "Social proof elements"],
    "Production": ["B-roll suggestions clear", "SFX appropriate", "Pacing varies"],
    "CTA": ["Clear call-to-action", "Natural placement", "Compelling reason"],
}


class HooksTalkingPointsAgent(BaseAgent):
    """Generate hooks, structured talking points, outro, and shorts segments from title + topics."""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.SCRIPT_MODEL

    def run(
        self,
        topic: str,
        title: str,
        topics: List[str],
        custom_notes: str = "",
    ) -> Dict[str, Any]:
        topics_text = "\n".join(f"  - {t}" for t in topics)
        checklist_text = json.dumps(CHECKLIST, indent=2)

        prompt = f"""You are a senior YouTube scriptwriter. Given a title and chosen topics, produce:
1. Five distinct hooks (opening lines + first 30 seconds of script)
2. A structured talking points outline (sections → subsections → bullets)
3. An outro script (~30 seconds)
4. Two or three self-contained "shorts segments" that can be cut from the long-form video

VIDEO TITLE: {title or topic}
TOPIC: {topic}

CHOSEN TOPICS TO COVER:
{topics_text}

CUSTOM NOTES FROM CREATOR:
{custom_notes or "None"}

QUALITY CHECKLIST (every hook and talking point must satisfy these):
{checklist_text}

CONSTRAINTS:
- Full video: under 11 minutes (~1,650 words of spoken content)
- Audience: business professionals
- Reading level: 10th grade — short sentences, concrete examples, zero jargon
- Shorts: 60 seconds max each, completely self-contained (no "as I mentioned earlier")
- Each section of talking points must include specific subtopic bullets from the chosen topics above

Return this exact JSON (no markdown, no extra keys):
{{
  "hooks": [
    {{
      "hook_line": "One punchy opening line (≤15 words)",
      "thirty_sec_script": "Full word-for-word 30-second opening script the creator reads on camera. Include [ENERGY: HIGH] marker. ~75 words."
    }},
    ... 4 more hooks ...
  ],
  "talking_points": {{
    "sections": [
      {{
        "title": "Section title",
        "subsections": [
          {{
            "title": "Subsection title",
            "bullets": [
              "Specific talking point with enough detail to speak from",
              "Another specific point",
              "Third point"
            ]
          }}
        ]
      }}
    ]
  }},
  "outro": "Full word-for-word outro script (~75 words). Include CTA: subscribe, comment, what's next.",
  "shorts_segments": [
    {{
      "title": "Short title (≤8 words)",
      "source_section": "Which section this comes from",
      "hook_line": "Short's opening hook line",
      "script": "Complete 60-second self-contained script for this short. No references to the main video."
    }},
    ... 1-2 more shorts ...
  ]
}}"""

        try:
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=config.SCRIPT_GENERATION_TIMEOUT,
            )
            raw = (response.choices[0].message.content or "").strip()
            return _extract_json(raw)
        except Exception as e:
            raw_preview = ""
            try:
                raw_preview = (response.choices[0].message.content or "")[:200]
            except Exception:
                pass
            return {
                "hooks": [],
                "talking_points": {"sections": []},
                "outro": "",
                "shorts_segments": [],
                "error": f"{e}" + (f" | raw: {raw_preview}" if raw_preview else ""),
            }
