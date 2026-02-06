#!/usr/bin/env python3.10
"""Test script creation in non-interactive mode"""

from agents import ScriptCreatorAgent

# Test with predefined selections
agent = ScriptCreatorAgent()

# Create auto_select dict with first option of everything
auto_select = {
    "angle": None,  # Will use first angle
    "subtopics": None,  # Will use first 5 subtopics
    "hook": None,  # Will use first hook
    "trailer": None,  # Will use first trailer
    "outro": "Thanks for watching! Don't forget to like and subscribe for more Python tips."
}

result = agent.run(
    topic="Python Programming Tips",
    notes="Cover best practices, common mistakes, and productivity tools for Python developers",
    interactive=False,
    auto_select=auto_select
)

print("\n" + "="*80)
print("SCRIPT CREATION TEST RESULTS")
print("="*80)
print(f"\nTopic: {result['topic']}")
print(f"Selected Angle: {result['selected_angle'].get('angle_name', 'N/A')}")
print(f"Quality Score: {result['quality_report'].get('overall_score', 0)}/100")
print(f"\nImprovement Suggestions:")
for suggestion in result['quality_report'].get('improvement_suggestions', [])[:3]:
    print(f"  - {suggestion}")

print(f"\n✅ Script creation pipeline completed successfully!")
print(f"\nOutput files:")
print(f"  - Workflow JSON in results/workflows/")
print(f"  - Teleprompter script in results/scripts/")
print(f"  - Summary markdown in results/scripts/")
print(f"  - Quality report in results/quality_reports/")
