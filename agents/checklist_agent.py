from agents.base import BaseAgent
from agents.prompts import QUALITY_EVALUATOR_SYSTEM
import litellm
import config
import json
import os
from datetime import datetime

class ChecklistAgent(BaseAgent):
    """Fact-check script and predict performance"""

    # Map checklist categories to performance_factors keys
    CATEGORY_TO_WEIGHT = {
        "Hook": "hook_strength",
        "Structure": "structure",
        "Content": "content_quality",
        "Engagement": "engagement_devices",
        "Production": "production_value",
        "CTA": "content_quality"  # CTA contributes to content quality weight
    }

    def __init__(self, use_database: bool = False, ai_model: str = None, checklist_path: str = "checklists/script_checklist.json"):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.QUALITY_MODEL
        self.checklist_path = checklist_path
        self._ensure_checklist_exists()

    def _ensure_checklist_exists(self):
        """Create default checklist if none exists"""
        if not os.path.exists(self.checklist_path):
            os.makedirs(os.path.dirname(self.checklist_path), exist_ok=True)
            default_checklist = {
                "version": "1.0",
                "categories": {
                    "Hook": ["Grabs attention in 3-5 seconds", "Creates curiosity gap", "Relevant to topic"],
                    "Structure": ["Clear flow", "Curiosity gaps placed strategically", "Payoffs delivered"],
                    "Content": ["Factually accurate", "Value-dense", "No fluff"],
                    "Engagement": ["Pattern interrupts every 60 seconds", "Open loops resolved", "Maintains energy"],
                    "Production": ["B-roll suggestions clear", "SFX appropriate", "Pacing varies"],
                    "CTA": ["Clear call-to-action", "Natural placement", "Compelling reason"]
                },
                "performance_factors": {
                    "hook_strength": 30,
                    "content_quality": 25,
                    "structure": 20,
                    "engagement_devices": 15,
                    "production_value": 10
                }
            }
            with open(self.checklist_path, "w") as f:
                json.dump(default_checklist, f, indent=2)

    def _is_claude_model(self, model: str) -> bool:
        """Check if model is a Claude model (Anthropic)"""
        model_lower = model.lower()
        return 'claude' in model_lower or 'anthropic' in model_lower

    def _calculate_weighted_score(self, category_scores: dict, performance_factors: dict) -> int:
        """
        Calculate overall score using performance_factors weights.
        Maps category scores (0-10) to weighted overall score (0-100).
        """
        total_weight = sum(performance_factors.values())
        if total_weight == 0:
            return 0

        # Accumulate weighted scores by factor
        factor_scores = {}
        factor_counts = {}

        for category, score in category_scores.items():
            factor_key = self.CATEGORY_TO_WEIGHT.get(category)
            if factor_key and factor_key in performance_factors:
                if factor_key not in factor_scores:
                    factor_scores[factor_key] = 0
                    factor_counts[factor_key] = 0
                factor_scores[factor_key] += score
                factor_counts[factor_key] += 1

        # Calculate weighted average
        weighted_sum = 0
        for factor_key, weight in performance_factors.items():
            if factor_key in factor_scores and factor_counts[factor_key] > 0:
                avg_score = factor_scores[factor_key] / factor_counts[factor_key]
                weighted_sum += (avg_score / 10.0) * weight
            else:
                # If no category maps to this factor, use neutral score
                weighted_sum += 0.5 * weight

        return round((weighted_sum / total_weight) * 100)

    def run(self, script: str, topic: str, angles: list) -> dict:
        """
        Fact-check script and predict performance.

        Args:
            script: Complete script text
            topic: Video topic
            angles: List of selected angles

        Returns:
            Quality report with score, issues, improvement suggestions
        """
        print(f"[*] ChecklistAgent evaluating script...")

        # Load checklist
        with open(self.checklist_path, "r") as f:
            checklist = json.load(f)

        # Perform fact-checking and evaluation
        report = self._evaluate_script(script, topic, angles, checklist)

        # Recalculate overall_score using actual weights (don't trust AI's number)
        if 'category_scores' in report and 'performance_factors' in checklist:
            report['overall_score'] = self._calculate_weighted_score(
                report['category_scores'],
                checklist['performance_factors']
            )

        # Save report
        self._save_report(report, topic)

        print(f"[+] Quality check complete - Score: {report.get('overall_score', 0)}/100")
        return report

    def _evaluate_script(self, script: str, topic: str, angles: list, checklist: dict) -> dict:
        """Use LLM to evaluate script against checklist"""

        # Build angles text
        angles_text = "\n".join([
            f"- {a['angle_name']}"
            for a in angles
        ]) if angles else "No specific angles provided"

        prompt = f"""Evaluate this YouTube script. Be brutally honest.

FULL SCRIPT:
{script}

TOPIC: {topic}
ANGLES: {angles_text}

EVALUATION CRITERIA:
{json.dumps(checklist['categories'], indent=2)}

For each category, score 0-10 and explain WHY with specific evidence from the script.

For improvement suggestions: quote the EXACT line that needs changing and provide a CONCRETE rewrite. Don't say "strengthen the hook" — say 'Replace "What if I told you..." with a specific fact or story from the content.'

CRITICAL: Check for these red flags:
- Fabricated credentials or social proof not in the speaker's notes
- Generic examples when the notes contain specific ones
- The speaker's voice/personality being lost
- Vague claims without supporting evidence

Return JSON:
{{
    "fact_check": {{
        "errors_found": ["specific error with quote from script"],
        "questionable_claims": ["claim that needs verification"],
        "verification_needed": ["claim to verify"]
    }},
    "category_scores": {{
        "Hook": 0,
        "Structure": 0,
        "Content": 0,
        "Engagement": 0,
        "Production": 0,
        "CTA": 0
    }},
    "overall_score": 0,
    "improvement_suggestions": [
        "HOOK: Replace 'current hook text' with 'suggested better hook' because [reason]",
        "CONTENT at [timestamp]: Change 'weak line' to 'stronger alternative' because [reason]"
    ],
    "risk_assessment": {{
        "high_risk": [],
        "medium_risk": [],
        "low_risk": []
    }},
    "estimated_performance": {{
        "predicted_ctr": "range%",
        "predicted_retention": "range%",
        "confidence": "low/medium/high"
    }}
}}"""

        try:
            # Build request parameters
            messages = [
                {"role": "system", "content": QUALITY_EVALUATOR_SYSTEM},
                {"role": "user", "content": prompt}
            ]

            request_params = {
                "model": self.model,
                "messages": messages,
                "timeout": 90
            }

            # Only add response_format for non-Claude models
            if not self._is_claude_model(self.model):
                request_params["response_format"] = {"type": "json_object"}
            else:
                # For Claude, emphasize JSON format in the prompt
                messages[-1]["content"] += "\n\nReturn ONLY valid JSON. Start with { and end with }."

            response = litellm.completion(**request_params)

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

            return json.loads(content)
        except Exception as e:
            print(f"[!] Evaluation failed: {e}")
            print(f"[!] Model used: {self.model}")

            # Return fallback scores
            return {
                "fact_check": {"errors_found": [], "questionable_claims": [], "verification_needed": []},
                "category_scores": {"Hook": 5, "Structure": 5, "Content": 5, "Engagement": 5, "Production": 5, "CTA": 5},
                "overall_score": 50,
                "improvement_suggestions": [f"Manual review needed - automated evaluation failed: {str(e)[:100]}"],
                "risk_assessment": {"high_risk": [], "medium_risk": ["Evaluation system error"], "low_risk": []},
                "estimated_performance": {"predicted_ctr": "Unknown", "predicted_retention": "Unknown", "confidence": "low"}
            }

    def _save_report(self, report: dict, topic: str):
        """Save quality report"""
        if not os.path.exists("results/quality_reports"):
            os.makedirs("results/quality_reports")

        filename = f"results/quality_reports/report_{topic.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)

        print(f"[+] Quality report saved: {filename}")
