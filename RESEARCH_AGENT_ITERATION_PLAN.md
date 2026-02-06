# ResearchAgent Iteration Plan

## Overview

Enable ResearchAgent to iteratively refine subtopics based on user feedback, allowing users to request more/better topics until satisfied.

## Current Behavior

Currently, ResearchAgent (`agents/research_agent.py:13-115`):
1. Takes topic, angles, and notes as input
2. Calls LLM once to generate 8-10 subtopics
3. Returns subtopics immediately
4. No option to regenerate or refine

Integration point: ScriptCreatorAgent (`agents/script_creator_agent.py:67-68`) calls ResearchAgent once and presents results.

## Proposed Architecture

### 1. ResearchAgent Enhancements

#### New Methods

**`run_with_feedback_loop()`** - New primary method for interactive usage
```python
def run_with_feedback_loop(
    self,
    topic: str,
    angles: list,
    notes: str,
    interactive: bool = True,
    max_iterations: int = 3
) -> list:
    """
    Generate subtopics with iterative refinement based on user feedback.

    Args:
        topic: Main video topic
        angles: Selected angle dictionaries
        notes: User's rough notes
        interactive: If True, prompt for feedback after each iteration
        max_iterations: Maximum research iterations allowed

    Returns:
        Final list of subtopics
    """
```

**`regenerate_with_feedback()`** - Internal refinement method
```python
def _regenerate_with_feedback(
    self,
    topic: str,
    angles: list,
    notes: str,
    previous_subtopics: list,
    feedback: dict,
    iteration: int
) -> list:
    """
    Regenerate subtopics incorporating user feedback.

    Args:
        topic: Main video topic
        angles: Selected angles
        notes: User notes
        previous_subtopics: Previously generated subtopics
        feedback: Structured feedback dict with type and details
        iteration: Current iteration number

    Returns:
        New list of subtopics
    """
```

#### Feedback Types

Support the following feedback categories:

```python
FEEDBACK_TYPES = {
    "more_specific": "Make subtopics more specific and detailed",
    "broader": "Make subtopics broader and more general",
    "different_angle": "Try completely different perspectives",
    "more_practical": "Focus more on practical, actionable content",
    "more_technical": "Include more technical depth",
    "more_beginner": "Make it more beginner-friendly",
    "more_advanced": "Target advanced audience",
    "more_creative": "Include more creative/unique angles",
    "fewer_subtopics": "Generate fewer, more substantial subtopics",
    "more_subtopics": "Generate more granular subtopics"
}
```

#### Enhanced LLM Prompt

Update `_research_subtopics()` to accept optional feedback:

```python
def _research_subtopics(
    self,
    topic: str,
    angles: list,
    notes: str,
    feedback: dict = None,
    previous_subtopics: list = None,
    iteration: int = 1
) -> list:
    """Generate subtopics, optionally with feedback from previous iteration"""
```

Enhanced prompt structure:
```
Create YouTube video subtopics for "{topic}" blending these angles:
{angles_text}

User notes: {notes}

[IF FEEDBACK EXISTS:]
Previous Iteration Feedback:
- Iteration: {iteration}
- User feedback type: {feedback['type']}
- Specific notes: {feedback['details']}

Previous subtopics (for reference, DO NOT repeat these exactly):
{previous_subtopics_formatted}

Requirements:
- Address the user's feedback
- Generate NEW subtopics that incorporate the feedback
- Avoid repeating previous subtopics unless specifically requested
[END IF]

Generate 8-10 subtopics that naturally incorporate elements from multiple angles.
...
```

#### State Tracking

Add instance variables to track iteration state:
```python
def __init__(self, use_database: bool = False, ai_model: str = None):
    super().__init__(use_database=use_database, ai_model=ai_model)
    self.model = ai_model or config.RESEARCH_MODEL
    self.iteration_history = []  # Track all attempts
```

#### Display Helper

Add method to show comparison:
```python
def _display_iteration_comparison(
    self,
    current_subtopics: list,
    previous_subtopics: list,
    iteration: int
):
    """Display side-by-side comparison of iterations using Rich tables"""
```

### 2. ScriptCreatorAgent Integration

Update Step 2 in `run()` method (`script_creator_agent.py:64-77`):

**Before:**
```python
# 2. Research subtopics
self.console.print(f"\n[yellow]Step 2/7: Researching subtopics...[/yellow]")
research_agent = ResearchAgent(use_database=self.use_database)
subtopics = research_agent.run(topic, selected_angles, notes)

if interactive and subtopics:
    selected_subtopics = self._get_multi_selection(...)
```

**After:**
```python
# 2. Research subtopics with feedback loop
self.console.print(f"\n[yellow]Step 2/7: Researching subtopics...[/yellow]")
research_agent = ResearchAgent(use_database=self.use_database)

if interactive:
    # Use new feedback loop method
    subtopics = research_agent.run_with_feedback_loop(
        topic=topic,
        angles=selected_angles,
        notes=notes,
        interactive=True,
        max_iterations=config.MAX_RESEARCH_ITERATIONS
    )
else:
    # Non-interactive: use original single-pass method
    subtopics = research_agent.run(topic, selected_angles, notes)

if interactive and subtopics:
    selected_subtopics = self._get_multi_selection(...)
```

#### Add Feedback Collection Method

New helper in ScriptCreatorAgent:
```python
def _get_research_feedback(self, subtopics: list) -> dict:
    """
    Collect user feedback on research results.

    Returns:
        dict with 'satisfied', 'feedback_type', and 'details'
    """
    from agents.research_agent import FEEDBACK_TYPES

    # Display satisfaction prompt
    satisfied = Confirm.ask(
        "\nAre you satisfied with these subtopics?",
        default=True
    )

    if satisfied:
        return {"satisfied": True}

    # Display feedback type options
    table = Table(title="How should we improve?")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Feedback Type", style="magenta")

    feedback_items = list(FEEDBACK_TYPES.items())
    for i, (key, description) in enumerate(feedback_items, 1):
        table.add_row(str(i), description)

    self.console.print(table)

    choice = IntPrompt.ask(
        f"Select feedback type (1-{len(feedback_items)})",
        default=1
    )

    # Get optional detailed feedback
    details = Prompt.ask(
        "Any additional specific guidance? (optional)",
        default=""
    )

    feedback_type = feedback_items[choice - 1][0]

    return {
        "satisfied": False,
        "type": feedback_type,
        "description": FEEDBACK_TYPES[feedback_type],
        "details": details
    }
```

### 3. Configuration Updates

Add to `config.py`:

```python
# ResearchAgent iteration settings
MAX_RESEARCH_ITERATIONS = 3  # Maximum times user can request regeneration
RESEARCH_MODEL = AI_MODEL  # Can use same or different model for research
```

### 4. User Experience Flow

**Interactive Mode:**

```
Step 2/7: Researching subtopics for angles: Beginner-Friendly, Technical Deep-Dive...
[*] ResearchAgent researching subtopics for angles...
[+] Found 10 subtopics

┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #  ┃ Subtopic                               ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1  │ Understanding the Basics              │
│ 2  │ Getting Started with Installation     │
│ 3  │ Core Concepts Explained               │
│ ...│ ...                                    │
└────┴────────────────────────────────────────┘

Are you satisfied with these subtopics? [Y/n]: n

How should we improve?
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #  ┃ Feedback Type                          ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1  │ Make subtopics more specific          │
│ 2  │ Make subtopics broader                 │
│ 3  │ Try completely different perspectives  │
│ 4  │ Focus more on practical content        │
│ ...│ ...                                    │
└────┴────────────────────────────────────────┘

Select feedback type (1-10): 4
Any additional specific guidance? (optional): Include more code examples

[*] Regenerating subtopics with feedback (iteration 2/3)...
[+] Found 10 new subtopics

[Shows new subtopics in table...]

Are you satisfied with these subtopics? [Y/n]: y

✓ Proceeding with selected subtopics
```

### 5. Implementation Steps

1. **Phase 1: Core ResearchAgent Updates**
   - Add `run_with_feedback_loop()` method
   - Add `_regenerate_with_feedback()` method
   - Update `_research_subtopics()` to accept feedback parameters
   - Add `FEEDBACK_TYPES` constant
   - Add iteration state tracking
   - Add `_display_iteration_comparison()` helper

2. **Phase 2: ScriptCreatorAgent Integration**
   - Add `_get_research_feedback()` method
   - Update Step 2 to use feedback loop when interactive
   - Test interactive and non-interactive modes

3. **Phase 3: Configuration & Testing**
   - Add config parameters
   - Test full workflow end-to-end
   - Test max iterations limit
   - Test all feedback types

4. **Phase 4: Documentation**
   - Update CLAUDE.md with new workflow
   - Add examples to main.py help text
   - Document feedback types in code comments

### 6. Backward Compatibility

**Keep existing `run()` method unchanged** for:
- Non-interactive mode
- API/programmatic usage
- Existing agent orchestration patterns

The original `run()` method signature remains:
```python
def run(self, topic: str, angles: list, notes: str) -> list:
    """Original single-pass research (unchanged)"""
```

### 7. Benefits

1. **User Control**: Users can iteratively refine until satisfied
2. **Better Quality**: Feedback loop improves subtopic relevance
3. **Flexibility**: Different feedback types for different needs
4. **Maintained Workflow**: Keeps single-pass option for automation
5. **Iteration History**: Track attempts for debugging/learning

### 8. Future Enhancements

Potential additions (out of scope for initial implementation):
- Save iteration history to workflow JSON
- Auto-detect feedback from user's natural language input
- ML-based feedback classification
- Combine multiple feedback types
- A/B comparison mode showing old vs new side-by-side
- Partial regeneration (keep some subtopics, regenerate others)

## File Changes Summary

**New Files:**
- None (all changes in existing files)

**Modified Files:**
1. `agents/research_agent.py` - Add feedback loop methods and state tracking
2. `agents/script_creator_agent.py` - Integrate feedback collection in Step 2
3. `config.py` - Add MAX_RESEARCH_ITERATIONS constant

**No Changes Required:**
- `main.py` - Command interface unchanged
- `agents/base.py` - Base class unchanged
- Other agents - Unchanged

## Testing Strategy

1. **Unit Tests**:
   - Test `_regenerate_with_feedback()` with various feedback types
   - Test max iterations limit
   - Test state tracking

2. **Integration Tests**:
   - Full workflow in interactive mode
   - Full workflow in non-interactive mode
   - Mixed interactive/non-interactive steps

3. **Manual Testing**:
   - Run `python3.10 main.py create "test topic" --notes "test"` and test iteration at Step 2
   - Test all 10 feedback types
   - Test hitting max iterations limit
   - Test early satisfaction (accept first results)

## Success Criteria

- [ ] User can regenerate subtopics with feedback
- [ ] All 10 feedback types work correctly
- [ ] Iteration limit is respected
- [ ] Previous subtopics are not repeated
- [ ] Rich tables display properly
- [ ] Non-interactive mode still works (uses single-pass)
- [ ] Backward compatible with existing `run()` method
- [ ] No breaking changes to other agents
