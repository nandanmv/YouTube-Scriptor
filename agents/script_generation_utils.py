"""Shared utilities for script generation agents"""

import litellm
import config
from typing import Optional, Dict, List


class ScriptGenerationUtils:
    """Common script generation utilities used by QuickScriptAgent and ScriptAgent"""

    @staticmethod
    def call_litellm(prompt: str, model: Optional[str] = None, timeout: Optional[int] = None,
                     system_prompt: Optional[str] = None) -> str:
        """
        Shared LiteLLM completion call for script generation.

        Args:
            prompt: Complete prompt text
            model: AI model to use (defaults to config.SCRIPT_MODEL)
            timeout: Optional timeout in seconds (defaults to config.SCRIPT_GENERATION_TIMEOUT)
            system_prompt: Optional system prompt to set AI persona and behavior

        Returns:
            Generated script text

        Raises:
            Exception: If script generation fails
        """
        model = model or config.SCRIPT_MODEL
        timeout = timeout or config.SCRIPT_GENERATION_TIMEOUT

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            print(f"[*] Generating script with {model} (timeout: {timeout}s)...")
            response = litellm.completion(
                model=model,
                messages=messages,
                timeout=timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[!] Script generation failed: {e}")
            raise

    @staticmethod
    def build_regeneration_section(
        previous_script: str,
        previous_scores: Dict[str, int],
        improvement_suggestions: List[str],
        previous_overall_score: Optional[int] = None,
        threshold: int = 8
    ) -> str:
        """
        Build regeneration section for prompt to improve previous script.

        Args:
            previous_script: Script from previous iteration
            previous_scores: Category scores dict (e.g., {'Hook': 8, 'Structure': 7, ...})
            improvement_suggestions: List of improvement suggestions from evaluation
            previous_overall_score: Optional overall score (will be calculated from category scores if not provided)
            threshold: Score threshold for high/low categories (default: 8)

        Returns:
            Formatted regeneration section for prompt
        """
        # Calculate overall score if not provided
        if previous_overall_score is None:
            if previous_scores:
                previous_overall_score = sum(previous_scores.values()) * 100 // (len(previous_scores) * 10)
            else:
                previous_overall_score = 0

        # Categorize high vs low scoring categories
        high_scoring = [cat for cat, score in previous_scores.items() if score >= threshold]
        low_scoring = [cat for cat, score in previous_scores.items() if score < threshold]

        # Format improvement suggestions
        suggestions_text = "\n".join([f"- {s}" for s in improvement_suggestions]) if improvement_suggestions else "- No specific suggestions"

        # Include full previous script (or truncate only for very long scripts)
        max_script_chars = 12000
        script_preview = previous_script[:max_script_chars]
        truncation_note = f"\n... (truncated from {len(previous_script)} chars)" if len(previous_script) > max_script_chars else ""

        return f"""

**REGENERATION - IMPROVE THE PREVIOUS SCRIPT:**

Previous Overall Score: {previous_overall_score}/100

**WHAT TO KEEP** (scored {threshold}+ out of 10): {', '.join(high_scoring) if high_scoring else 'All areas need work'}
**WHAT TO FIX** (scored below {threshold}): {', '.join(low_scoring) if low_scoring else 'Minor polish needed'}

**SPECIFIC CHANGES REQUIRED:**
{suggestions_text}

**PREVIOUS SCRIPT:**
{script_preview}{truncation_note}

Rewrite the script, keeping what works and fixing the weak areas. Maintain the speaker's voice and specific examples.
"""

    @staticmethod
    def evaluate_with_checklist(script: str, topic: str, angles: Optional[List[dict]] = None) -> dict:
        """
        Evaluate script using ChecklistAgent.

        Args:
            script: Script text to evaluate
            topic: Video topic
            angles: Optional list of angle dicts (empty list if none)

        Returns:
            Evaluation dict with overall_score, category_scores, improvement_suggestions, etc.
        """
        from agents.checklist_agent import ChecklistAgent

        angles = angles or []
        checklist_agent = ChecklistAgent()
        return checklist_agent.run(script, topic, angles)
