#!/usr/bin/env python3.10
"""
Test script for ResearchAgent feedback loop functionality.
This tests the new iteration features without requiring full LLM calls.
"""

from agents.research_agent import ResearchAgent, FEEDBACK_TYPES
import config

def test_feedback_types():
    """Test that all feedback types are defined correctly."""
    print("Testing FEEDBACK_TYPES...")
    assert len(FEEDBACK_TYPES) == 10, f"Expected 10 feedback types, got {len(FEEDBACK_TYPES)}"

    expected_types = [
        "more_specific", "broader", "different_angle", "more_practical",
        "more_technical", "more_beginner", "more_advanced", "more_creative",
        "fewer_subtopics", "more_subtopics"
    ]

    for expected_type in expected_types:
        assert expected_type in FEEDBACK_TYPES, f"Missing feedback type: {expected_type}"
        assert isinstance(FEEDBACK_TYPES[expected_type], str), f"Invalid description for {expected_type}"

    print("✓ All 10 feedback types defined correctly")

def test_research_agent_initialization():
    """Test that ResearchAgent initializes with new attributes."""
    print("\nTesting ResearchAgent initialization...")
    agent = ResearchAgent()

    assert hasattr(agent, 'console'), "ResearchAgent missing 'console' attribute"
    assert hasattr(agent, 'iteration_history'), "ResearchAgent missing 'iteration_history' attribute"
    assert isinstance(agent.iteration_history, list), "iteration_history should be a list"
    assert len(agent.iteration_history) == 0, "iteration_history should start empty"

    print("✓ ResearchAgent initializes correctly with feedback loop attributes")

def test_config_updated():
    """Test that config has MAX_RESEARCH_ITERATIONS."""
    print("\nTesting config updates...")
    assert hasattr(config, 'MAX_RESEARCH_ITERATIONS'), "config missing MAX_RESEARCH_ITERATIONS"
    assert isinstance(config.MAX_RESEARCH_ITERATIONS, int), "MAX_RESEARCH_ITERATIONS should be an integer"
    assert config.MAX_RESEARCH_ITERATIONS > 0, "MAX_RESEARCH_ITERATIONS should be positive"

    print(f"✓ config.MAX_RESEARCH_ITERATIONS = {config.MAX_RESEARCH_ITERATIONS}")

def test_research_agent_methods():
    """Test that new methods exist on ResearchAgent."""
    print("\nTesting ResearchAgent new methods...")
    agent = ResearchAgent()

    # Check for new methods
    assert hasattr(agent, 'run_with_feedback_loop'), "Missing run_with_feedback_loop method"
    assert callable(agent.run_with_feedback_loop), "run_with_feedback_loop should be callable"

    assert hasattr(agent, '_regenerate_with_feedback'), "Missing _regenerate_with_feedback method"
    assert callable(agent._regenerate_with_feedback), "_regenerate_with_feedback should be callable"

    assert hasattr(agent, '_get_feedback'), "Missing _get_feedback method"
    assert callable(agent._get_feedback), "_get_feedback should be callable"

    assert hasattr(agent, '_display_subtopics'), "Missing _display_subtopics method"
    assert callable(agent._display_subtopics), "_display_subtopics should be callable"

    assert hasattr(agent, '_display_iteration_comparison'), "Missing _display_iteration_comparison method"
    assert callable(agent._display_iteration_comparison), "_display_iteration_comparison should be callable"

    # Check original method still exists
    assert hasattr(agent, 'run'), "Original run method should still exist"
    assert callable(agent.run), "Original run method should still be callable"

    print("✓ All new methods exist and are callable")

def test_display_subtopics():
    """Test that _display_subtopics works with sample data."""
    print("\nTesting _display_subtopics...")
    agent = ResearchAgent()

    sample_subtopics = [
        {
            "title": "Introduction to Python",
            "description": "Getting started with Python basics",
            "key_points": ["Variables", "Data types", "Control flow"],
            "estimated_duration": "2 minutes"
        },
        {
            "title": "Advanced Python Features",
            "description": "Deep dive into advanced concepts",
            "key_points": ["Decorators", "Generators", "Context managers"],
            "estimated_duration": "3 minutes"
        }
    ]

    try:
        agent._display_subtopics(sample_subtopics, iteration=1)
        print("✓ _display_subtopics works correctly")
    except Exception as e:
        print(f"✗ _display_subtopics failed: {e}")
        raise

def test_display_iteration_comparison():
    """Test that _display_iteration_comparison works with sample data."""
    print("\nTesting _display_iteration_comparison...")
    agent = ResearchAgent()

    previous = [
        {"title": "Old Topic 1", "description": "Previous version"},
        {"title": "Old Topic 2", "description": "Previous version"}
    ]

    current = [
        {"title": "New Topic 1", "description": "Improved version"},
        {"title": "New Topic 2", "description": "Improved version"}
    ]

    try:
        agent._display_iteration_comparison(current, previous, iteration=2)
        print("✓ _display_iteration_comparison works correctly")
    except Exception as e:
        print(f"✗ _display_iteration_comparison failed: {e}")
        raise

def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("ResearchAgent Feedback Loop Implementation Tests")
    print("=" * 60)

    try:
        test_config_updated()
        test_feedback_types()
        test_research_agent_initialization()
        test_research_agent_methods()
        test_display_subtopics()
        test_display_iteration_comparison()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe ResearchAgent feedback loop implementation is ready to use.")
        print("\nTry it out:")
        print('  python3.10 main.py create "your topic" --notes "your notes"')
        print("\nAt Step 2, you'll be able to iterate on subtopics with feedback!")

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        raise
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ UNEXPECTED ERROR: {e}")
        print("=" * 60)
        raise

if __name__ == "__main__":
    run_all_tests()
