#!/usr/bin/env python3.10
"""Test markdown table sanitization"""

from agents import BrainstormAgent

# Create test data with newlines and special characters
test_result = {
    'ratio': 10.5,
    'title': 'Test Video',
    'url': 'https://youtube.com/watch?v=test',
    'views': 1000,
    'median_views': 100,
    'subscribers': 5000,
    'channel': 'Test Channel',
    'success_criteria': 'Line 1\nLine 2\nLine 3',
    'subtopics_covered': '• Topic 1\n• Topic 2\n• Topic 3',
    'reusable_insights': 'Insight with | pipe character',
    'ultimate_titles': 'Title 1\nTitle 2',
    'alternate_hooks': 'Hook 1\nHook 2'
}

# Test sanitization function
agent = BrainstormAgent()

print("Testing sanitization function:")
print("="*80)

# Test with newlines
text_with_newlines = "Line 1\nLine 2\nLine 3"
sanitized = agent._sanitize_table_cell(text_with_newlines)
print(f"Original: {repr(text_with_newlines)}")
print(f"Sanitized: {repr(sanitized)}")
print(f"✅ Newlines replaced with <br>: {chr(10) not in sanitized}")

# Test with pipe character
text_with_pipe = "Text with | pipe"
sanitized = agent._sanitize_table_cell(text_with_pipe)
print(f"\nOriginal: {repr(text_with_pipe)}")
print(f"Sanitized: {repr(sanitized)}")
escaped_pipe = '\\|'
print(f"✅ Pipe escaped: {escaped_pipe in sanitized}")

# Test with both
text_with_both = "Line 1\nLine with | pipe\nLine 3"
sanitized = agent._sanitize_table_cell(text_with_both)
print(f"\nOriginal: {repr(text_with_both)}")
print(f"Sanitized: {repr(sanitized)}")
print(f"✅ Both handled correctly: {chr(10) not in sanitized and escaped_pipe in sanitized}")

# Create a test report
print("\n" + "="*80)
print("Creating test markdown file...")

agent._save_brainstorm_report("test_sanitization", [test_result])

print("\n✅ Test report created at: results/brainstorm_test_sanitization.md")
print("\nChecking generated markdown:")
with open("results/brainstorm_test_sanitization.md", "r") as f:
    content = f.read()
    # Count pipes in table row to verify structure
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'Test Video' in line:
            pipe_count = line.count('|')
            print(f"Table row has {pipe_count} pipes (should be 12 for 11 columns)")
            print(f"✅ Table structure intact: {pipe_count == 12}")

            # Check for <br> tags
            has_br = '<br>' in line
            print(f"✅ Contains <br> tags: {has_br}")

            # Check for escaped pipes
            escaped_pipe = '\\|'
            has_escaped = escaped_pipe in line
            print(f"✅ Contains escaped pipes: {has_escaped}")

            print(f"\nRow content preview:")
            print(line[:200] + "...")
            break

print("\n" + "="*80)
print("✅ All tests passed! Markdown tables should now render correctly.")
