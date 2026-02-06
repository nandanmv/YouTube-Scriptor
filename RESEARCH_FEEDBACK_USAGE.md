# ResearchAgent Feedback Loop - User Guide

## Overview

The ResearchAgent now supports iterative refinement of subtopics. When creating a script, you can review the generated subtopics at Step 2 and request improvements until you're satisfied.

## Quick Start

```bash
python3.10 main.py create "Your Video Topic" --notes "your rough notes"
```

When you reach **Step 2: Researching subtopics**, the system will:
1. Generate initial subtopics based on your selected angles
2. Display them in a formatted table
3. Ask if you're satisfied
4. Let you regenerate with specific feedback (up to 3 times)

## Step-by-Step Walkthrough

### Initial Generation

```
Step 2/7: Researching subtopics for angles: Beginner-Friendly, Technical...
[*] ResearchAgent researching subtopics...
[+] Found 10 subtopics

                                   Subtopics
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ #    ┃ Title                    ┃ Description             ┃ Duration     ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ 1    │ Understanding Basics     │ Introduction to core... │ 2 minutes    │
│ 2    │ Key Concepts Explained   │ Deep dive into...       │ 3 minutes    │
│ 3    │ Practical Applications   │ Real-world examples...  │ 2-3 minutes  │
│ ...  │ ...                      │ ...                     │ ...          │
└──────┴──────────────────────────┴─────────────────────────┴──────────────┘

Are you satisfied with these subtopics? [Y/n]:
```

### If Satisfied

Press **Y** or **Enter** to accept and continue to subtopic selection.

### If Not Satisfied

Press **n** to provide feedback:

```
Are you satisfied with these subtopics? [Y/n]: n

How should we improve?
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #    ┃ Feedback Type                            ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1    │ Make subtopics more specific and detail │
│ 2    │ Make subtopics broader and more general  │
│ 3    │ Try completely different perspectives    │
│ 4    │ Focus more on practical, actionable...   │
│ 5    │ Include more technical depth             │
│ 6    │ Make it more beginner-friendly           │
│ 7    │ Target advanced audience                 │
│ 8    │ Include more creative/unique angles      │
│ 9    │ Generate fewer, more substantial...      │
│ 10   │ Generate more granular subtopics         │
└──────┴──────────────────────────────────────────┘

Select feedback type (1-10): 4
Any additional specific guidance? (optional): Include code examples

🔄 Regenerating subtopics with feedback (iteration 2/3)...
```

### Comparison View

After regeneration, you'll see a side-by-side comparison:

```
╭─ Previous (Iteration 1) ─────╮  ╭─ Current (Iteration 2) ──────╮
│ 1. Understanding Basics      │  │ 1. Hands-On Setup Guide      │
│ 2. Key Concepts Explained    │  │ 2. Building Your First App   │
│ 3. Practical Applications    │  │ 3. Common Coding Patterns    │
│ 4. Common Challenges         │  │ 4. Debugging Real Projects   │
│ 5. Advanced Techniques       │  │ 5. Code Review Best Practice │
│ ... and 5 more               │  │ ... and 5 more               │
╰──────────────────────────────╯  ╰──────────────────────────────╯

                              Subtopics (Iteration 2)
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ #    ┃ Title                    ┃ Description             ┃ Duration     ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ 1    │ Hands-On Setup Guide     │ Step-by-step install... │ 2 minutes    │
│ 2    │ Building Your First App  │ Code walkthrough with...│ 3 minutes    │
│ ...  │ ...                      │ ...                     │ ...          │
└──────┴──────────────────────────┴─────────────────────────┴──────────────┘

Are you satisfied with these subtopics? [Y/n]:
```

## Feedback Types Explained

### 1. More Specific
Use when subtopics are too vague or generic.
- **Before**: "Understanding Python"
- **After**: "Setting Up Python Virtual Environments with venv"

### 2. Broader
Use when subtopics are too narrow or technical.
- **Before**: "Implementing Observer Pattern in React Hooks"
- **After**: "Managing State in React Applications"

### 3. Different Angle
Use when subtopics don't align with your vision. Generates completely new perspectives.

### 4. More Practical
Use when subtopics are too theoretical. Adds hands-on, actionable content.
- **Example**: Adds code examples, step-by-step guides, real-world projects

### 5. More Technical
Use when content is too basic. Increases technical depth and complexity.
- **Example**: Adds implementation details, algorithms, architecture patterns

### 6. More Beginner-Friendly
Use when content is too advanced. Simplifies language and concepts.
- **Example**: Adds "What is...", "Why...", "Getting Started" sections

### 7. More Advanced
Use when content is too basic for your audience. Targets experienced users.
- **Example**: Adds optimization, edge cases, advanced techniques

### 8. More Creative
Use when subtopics feel generic. Adds unique, creative angles.
- **Example**: Unconventional approaches, surprising connections, fresh perspectives

### 9. Fewer Subtopics
Use when there are too many sections. Consolidates into fewer, more substantial topics.
- **Before**: 10 shallow subtopics
- **After**: 5-6 comprehensive subtopics

### 10. More Subtopics
Use when topics are too high-level. Breaks into more granular sections.
- **Before**: 5 broad subtopics
- **After**: 10-12 specific subtopics

## Tips for Best Results

### 1. Use Specific Guidance
When prompted for additional guidance, be specific:

**Good:**
- "Include more code examples"
- "Focus on real-world use cases in web development"
- "Add troubleshooting tips"
- "Target complete beginners with no background"

**Not as helpful:**
- "Make it better"
- "Change it"

### 2. Combine Feedback Types
You can iterate multiple times with different feedback:
- **Iteration 1**: Use "More Practical" to add code examples
- **Iteration 2**: Use "More Specific" to target exact use cases
- **Iteration 3**: Use "Fewer Subtopics" to consolidate

### 3. Know When to Accept
Don't over-iterate. If subtopics are 80% good, accept them and refine during selection.

### 4. Review Between Iterations
The comparison view shows what changed. Use this to guide your next feedback.

## Configuration

### Adjust Maximum Iterations

Edit `.env`:
```bash
MAX_RESEARCH_ITERATIONS=5  # Allow up to 5 iterations (default: 3)
```

Or edit `config.py`:
```python
MAX_RESEARCH_ITERATIONS = int(os.getenv("MAX_RESEARCH_ITERATIONS", "3"))
```

### Use Different AI Models

You can use a different model for research:
```bash
# In .env
RESEARCH_MODEL=openai/gpt-4o-mini  # Faster, cheaper
# or
RESEARCH_MODEL=anthropic/claude-3-5-sonnet-20240620  # More thoughtful
```

## Non-Interactive Mode

For automation or API usage, the feedback loop is automatically disabled:

```python
from agents.script_creator_agent import ScriptCreatorAgent

agent = ScriptCreatorAgent()
result = agent.run(
    topic="Your Topic",
    notes="your notes",
    interactive=False  # Disables feedback loop
)
```

## Troubleshooting

### "Max iterations reached"
You've used all allowed iterations. Either:
- Accept the current subtopics
- Increase `MAX_RESEARCH_ITERATIONS` in config
- Restart and provide clearer initial notes

### "Invalid choice"
Make sure to enter a number between 1-10 when selecting feedback type.

### Subtopics seem similar to previous
Provide more specific guidance in the optional feedback field to help the AI understand what changes you want.

## Example Session

```bash
$ python3.10 main.py create "Building REST APIs with FastAPI" --notes "Focus on beginners"

Step 1/7: Discovering proven angles...
[Shows angles, user selects "Beginner-Friendly" and "Problem-Solving"]

Step 2/7: Researching subtopics for angles: Beginner-Friendly, Problem-Solving...
[+] Found 10 subtopics

[Shows subtopics table]

Are you satisfied? [Y/n]: n

Select feedback type: 4 (More Practical)
Additional guidance?: Include code examples with explanations

🔄 Regenerating (iteration 2/3)...

[Shows comparison and new table]

Are you satisfied? [Y/n]: n

Select feedback type: 6 (More Beginner-Friendly)
Additional guidance?: Add "What is" and "Why" sections

🔄 Regenerating (iteration 3/3)...

[Shows comparison and new table]

Are you satisfied? [Y/n]: y

✓ Proceeding with selected subtopics

[Shows multi-selection for final subtopics]

Select subtopics (1,2,3...): 1,2,3,4,5

[Continues to Step 3...]
```

## Benefits

✅ **Full Control**: Refine until satisfied
✅ **10 Feedback Types**: Precise direction for improvements
✅ **Visual Comparison**: See exactly what changed
✅ **Guided by Data**: Subtopics informed by your selected angles
✅ **Iterative Refinement**: Build quality gradually
✅ **Respects Limits**: Prevents infinite loops

## Next Steps

1. Try the feature: `python3.10 main.py create "test topic" --notes "test"`
2. Experiment with different feedback types
3. Find your preferred iteration workflow
4. Integrate into your video production process

Happy creating! 🎬
