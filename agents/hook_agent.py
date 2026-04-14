from agents.base import BaseAgent, parse_json_response
from agents.prompts import HOOK_GENERATOR_SYSTEM
import litellm
import config
import json

class HookAgent(BaseAgent):
    """Generate hook and intro/trailer options"""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.SCRIPT_MODEL

    def run(self, topic: str, angles: list, structure: dict, notes: str = "", theme_data: dict = None) -> dict:
        """
        Generate hook options prioritized by common viral title patterns.

        Args:
            topic: Video topic
            angles: List of selected angles
            structure: Content structure from StructureAgent
            notes: User's notes for content-specific hooks
            theme_data: Metadata from ThemeAgent (Common Title Phrases, etc.)

        Returns:
            Dictionary with hooks and trailers lists
        """
        print(f"[*] HookAgent generating hooks and trailers...")

        hooks_and_trailers = self._generate_options(topic, angles, structure, notes, theme_data=theme_data)

        print(f"[+] Generated {len(hooks_and_trailers.get('hooks', []))} hooks, {len(hooks_and_trailers.get('trailers', []))} trailers")
        return hooks_and_trailers

    def _generate_options(self, topic: str, angles: list, structure: dict, notes: str, theme_data: dict = None) -> dict:
        """Generate multiple hook and trailer options with viral phrasing"""

        # Build readable subtopic list
        subtopics = structure.get('structured_subtopics', [])[:5]
        subtopic_text = ""
        for i, sub in enumerate(subtopics, 1):
            if isinstance(sub, dict):
                subtopic_text += f"{i}. {sub.get('title', '')}\n"
            else:
                subtopic_text += f"{i}. {sub}\n"

        # Build angles text
        angles_text = "\n".join([
            f"- {a['angle_name']}: {a['description']}"
            for a in angles
        ])

        theme_text = ""
        if theme_data:
            theme_text = f"""
MARKET THEMES & VIRAL PHRASING:
- **Common Title Phrases**: {", ".join(theme_data.get('common_title_phrases', []))}
- **Audience Intent**: {theme_data.get('audience_intent', 'N/A')}
- **Success Patterns**: {", ".join(theme_data.get('universal_success_criteria', []))}
"""

        prompt = f"""Create 5 hooks and 3 trailers/intros for a YouTube video on "{topic}".

{theme_text}

ANGLES:
{angles_text}

KEY CONTENT COVERED:
{subtopic_text}

SPEAKER'S NOTES (use specific details from these for hooks):
{notes[:2000] if notes else "No specific notes provided"}

HOOK REQUIREMENTS:
- **Viral Phrasing**: Use the "Common Title Phrases" identified above to inform the wording of your hooks.
- Each hook must use a SPECIFIC fact, story, or detail from the notes or content — not a generic template
- Avoid these overused patterns: "What if I told you...", "Stop scrolling", "Everything you know about X is wrong"
- The best hooks open with something concrete: a number, a name, a specific result, or an unexpected comparison

Generate:
5 Hook Options (first 3-5 seconds each):
1. Specific Fact/Result - Lead with a concrete detail, phrased like a viral title
2. Contrarian Statement - Challenge a specific assumption using niche-tested phrasing
3. Story Opening - Start mid-action using viral phrasing principles
4. Problem Statement - Name a specific pain the viewer has
5. Curiosity Gap - Tease a specific reveal using niche-tested wording

3 Trailer/Intro Options (after hook, 15-20 seconds max):
- Each should preview value and set expectations
- Include a retention hook (e.g., "stick around for minute X where I show you...")

Return JSON:
{{
    "hooks": [
        {{
            "text": "Exact words to say",
            "type": "specific_fact",
            "score": 8,
            "reasoning": "Why this works"
        }}
    ],
    "trailers": [
        {{
            "text": "Exact intro/trailer text",
            "style": "preview",
            "score": 7,
            "reasoning": "Why this works"
        }}
    ]
}}"""

        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": HOOK_GENERATOR_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=config.DEFAULT_API_TIMEOUT
            )

            content = response.choices[0].message.content
            # Strip markdown code fences if present
            if content.strip().startswith("```"):
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            return parse_json_response(content)
        except Exception as e:
            print(f"[!] Hook generation failed: {e}")
            return self._get_default_hooks_and_trailers(topic, angles)

    def _get_default_hooks_and_trailers(self, topic: str, angles: list) -> dict:
        """Fallback hooks if API fails"""
        return {
            "hooks": [
                {
                    "text": f"In 2025, you won't need separate apps for presentations, reports, or automation — just one AI that does it all. Let me show you.",
                    "type": "specific_fact",
                    "score": 7,
                    "reasoning": "Opens with a concrete, specific vision"
                },
                {
                    "text": f"I've been testing {topic} for months. Here's the one thing that changes everything.",
                    "type": "story",
                    "score": 6,
                    "reasoning": "Personal experience with specificity"
                },
                {
                    "text": f"Most people are using {topic} completely wrong. Here's what the top performers do differently.",
                    "type": "contrarian",
                    "score": 6,
                    "reasoning": "Challenges assumption with promise of insider knowledge"
                }
            ],
            "trailers": [
                {
                    "text": f"Today I'll break down exactly what {topic} is, why it matters to your business, and how to get started — even if you've never touched code.",
                    "style": "preview",
                    "score": 7,
                    "reasoning": "Clear roadmap of value"
                },
                {
                    "text": f"By the end of this video, you'll have a step-by-step plan to use {topic}. And stay until minute 8 — I'll show you how to do this completely free.",
                    "style": "promise_with_retention",
                    "score": 8,
                    "reasoning": "Outcome promise plus retention hook"
                }
            ]
        }
