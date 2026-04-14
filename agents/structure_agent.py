from agents.base import BaseAgent, parse_json_response
from agents.prompts import RESEARCH_SYSTEM
import litellm
import config
import json

class StructureAgent(BaseAgent):
    """Insert curiosity gaps, open loops, and payoffs throughout content"""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.RESEARCH_MODEL

    def run(self, selected_subtopics: list, notes: str) -> dict:
        """
        Add engagement structure to subtopics.

        Args:
            selected_subtopics: User-selected subtopics
            notes: User's rough notes

        Returns:
            Structured content with curiosity gaps, loops, payoffs
        """
        print(f"[*] StructureAgent adding engagement mechanics...")

        structure = self._add_engagement_structure(selected_subtopics, notes)

        print(f"[+] Structure complete with {len(structure.get('curiosity_gaps', []))} curiosity gaps")
        return structure

    def _add_engagement_structure(self, subtopics: list, notes: str) -> dict:
        """Use LLM to strategically place engagement devices"""

        prompt = f"""
Given these video subtopics, add strategic engagement mechanics:

Subtopics:
{json.dumps(subtopics, indent=2)}

User notes: {notes}

Add:
1. **Curiosity Gaps**: Questions or teasers that create anticipation (place before revealing information)
2. **Open Loops**: Promises to explain something later (creates forward momentum)
3. **Payoffs**: Satisfying delivery on promises (place strategically to maintain trust)

Return JSON with structured content including where to place each device:
{{
    "structured_subtopics": [...],
    "curiosity_gaps": [
        {{"text": "But there's a catch...", "placement": "before_subtopic_3"}}
    ],
    "open_loops": [
        {{"setup": "I'll show you the secret in a moment", "payoff_at": "subtopic_5"}}
    ],
    "payoffs": [
        {{"text": "Here's that secret I promised", "resolves": "loop_1"}}
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

            return parse_json_response(response.choices[0].message.content)
        except Exception as e:
            print(f"[!] Structure generation failed: {e}")
            return {
                "structured_subtopics": subtopics,
                "curiosity_gaps": [
                    {"text": "But first, let me show you something surprising...", "placement": "before_subtopic_2"}
                ],
                "open_loops": [
                    {"setup": "I'll reveal the most important tip at the end", "payoff_at": "conclusion"}
                ],
                "payoffs": [
                    {"text": "Here's that crucial tip I mentioned", "resolves": "loop_1"}
                ]
            }
