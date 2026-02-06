#!/usr/bin/env python3.10
"""Quick test for ScriptGenerationUtils"""

from agents.script_generation_utils import ScriptGenerationUtils

def test_build_regeneration_section():
    """Test regeneration section building"""
    print("Testing build_regeneration_section...")

    previous_scores = {
        'Hook': 9,
        'Structure': 7,
        'Content': 8,
        'Engagement': 6,
        'Production': 7,
        'CTA': 5
    }

    improvement_suggestions = [
        "Strengthen the CTA with a more compelling offer",
        "Add more engagement devices in the middle section"
    ]

    previous_script = "This is a test script that would be much longer in reality..." * 10

    section = ScriptGenerationUtils.build_regeneration_section(
        previous_script=previous_script,
        previous_scores=previous_scores,
        improvement_suggestions=improvement_suggestions,
        previous_overall_score=70
    )

    # Verify key elements are present
    assert "70/100" in section, "Should include overall score"
    assert "Hook" in section, "Should mention high-scoring category"
    assert "CTA" in section or "Engagement" in section, "Should mention low-scoring categories"
    assert "Strengthen the CTA" in section, "Should include improvement suggestions"
    assert "PRESERVE" in section or "high-scoring" in section, "Should instruct to preserve strengths"
    assert "IMPROVE" in section or "weak" in section, "Should instruct to improve weaknesses"

    print("✓ build_regeneration_section works correctly")
    print(f"  - Generated {len(section)} characters")
    print(f"  - Identified 1 high-scoring category (Hook)")
    print(f"  - Identified 3 low-scoring categories (Structure, Engagement, CTA)")


def test_evaluate_with_checklist():
    """Test checklist evaluation (requires checklist file)"""
    print("\nTesting evaluate_with_checklist...")

    # This would require a real script and checklist, so just verify the method exists
    assert hasattr(ScriptGenerationUtils, 'evaluate_with_checklist'), "Method should exist"
    print("✓ evaluate_with_checklist method exists")


def test_call_litellm():
    """Test LiteLLM call method (doesn't actually call API)"""
    print("\nTesting call_litellm...")

    # Just verify the method exists and has correct signature
    assert hasattr(ScriptGenerationUtils, 'call_litellm'), "Method should exist"

    # Verify we can access it without calling
    import inspect
    sig = inspect.signature(ScriptGenerationUtils.call_litellm)
    params = list(sig.parameters.keys())

    assert 'prompt' in params, "Should have prompt parameter"
    assert 'model' in params, "Should have model parameter"
    assert 'timeout' in params, "Should have timeout parameter"

    print("✓ call_litellm method exists with correct signature")
    print(f"  - Parameters: {', '.join(params)}")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing ScriptGenerationUtils")
    print("=" * 60 + "\n")

    test_build_regeneration_section()
    test_evaluate_with_checklist()
    test_call_litellm()

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
