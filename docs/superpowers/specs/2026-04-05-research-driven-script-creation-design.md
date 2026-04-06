# Research-Driven Script Creation Design

## Goal

Replace the old web `Create` strategy path of:

`Angles -> Subtopics -> Web research -> Structure -> Script`

with a new primary web workflow:

`Theme -> Research -> Create`

The new `Research` step becomes the main planning layer between `Theme` and `Create`.

## Why

The current web flow still leans on an older internal script-creation pipeline that derives subtopics indirectly from angles and then enriches those subtopics through generic web search. That is workable, but it is not the clearest planning model for the browser app.

The new workflow should let the user:

- use selected videos from the latest outlier/theme set
- pull transcript evidence from those videos
- gather recent discussion from Reddit and X
- add their own links and research notes
- see candidate titles and high-level topics
- choose the exact title and topics to drive the final script

This makes strategy explicit instead of inferred.

## Scope

This design applies to the FastAPI web app flow.

It covers:

- a new `Research` step and interface
- new request/response data passed through the web app
- an updated `Create` path that uses selected title/topics from `Research`

It does not remove the legacy CLI workflow in this phase.

## User Workflow

### New Web Flow

1. Run `Outlier`
2. Run `Theme` on selected videos
3. Run `Research`
4. Review and choose:
   - one title
   - one or more high-level topics
5. Run `Create`
6. Script is generated using the chosen title, chosen topics, supporting material, and research summary

### Research Inputs

The `Research` panel accepts:

- `Topic`
- selected Theme/outlier videos
- `Links / Sources I Want Included`
- `My Notes / Research Context`

### Research Outputs

The `Research` panel returns:

- `best_titles`
- `high_level_topics`
- `supporting_material`
- `research_summary`
- transcript source references
- discussion source references

### Create Requirements

The web `Create` action requires:

- at least one selected title
- at least one selected topic

If either is missing, the UI should block the request and explain what to select.

## Architecture

### 1. ResearcherAgent

`agents/researcher_agent.py` is the new synthesis layer for browser research.

Responsibilities:

- pull transcript excerpts from selected videos
- search recent Reddit and X discussion
- merge user-provided links and user-provided notes
- synthesize title candidates, topic candidates, supporting material, and a recommended story spine

Output contract:

```json
{
  "topic": "AI agents",
  "video_count": 4,
  "transcript_sources": [],
  "discussion_sources": [],
  "best_titles": [],
  "high_level_topics": [],
  "supporting_material": [],
  "research_summary": {
    "main_discussion": "",
    "strongest_evidence": [],
    "recommended_story_spine": ""
  }
}
```

### 2. Theme as Upstream Market Map

`Theme` remains the upstream strategic scan.

It identifies:

- recurring patterns
- saturated angles
- open gaps
- viewer desires
- ranked opportunities

`Research` consumes that output as context, but becomes the actual selection step before `Create`.

### 3. Create as Research-Driven Script Writer

`Create` will still reuse the existing script-writing machinery, but in web mode the strategy input changes.

Primary inputs to script generation become:

- chosen title
- chosen high-level topics
- research summary
- supporting material
- selected Theme/outlier source videos
- user notes

The old browser path built around generated subtopics and `WebSearchAgent` should no longer be the main strategy layer for the web app.

## API Changes

### Research Request

Extend the web request shape to support custom user research:

```json
{
  "topic": "AI agents",
  "videos": [],
  "theme_data": {},
  "custom_links": "https://...",
  "custom_notes": "My angle and context"
}
```

### Create Request

The create request already supports:

- `selected_title`
- `selected_topics`
- `research_packet`

These become required for the web flow.

## UI Design

### Navigation

Primary browser flow:

- Outlier
- Discovery
- Theme
- Research
- Create
- Quick Script
- Trend Discovery

### Research Panel

The new panel sits between `Theme` and `Create`.

Sections:

1. Inputs
   - topic
   - custom links textarea
   - custom notes textarea
2. Actions
   - run research
3. Outputs
   - title selection
   - topic selection
   - research summary
   - supporting material links
   - transcript/discussion evidence

### Selection Behavior

- Titles render as radio choices
- Topics render as checkbox choices
- The latest selections persist in frontend state
- `Create` consumes those selections directly

### Create Panel

The `Create` panel should show:

- selected title
- selected topic count
- whether a research packet is loaded

If selections are missing, the UI should show a friendly block message instead of sending a partial request.

## Legacy Path Replacement

### What Is Being Replaced

For the browser workflow, the old strategy chain:

- `ResearchAgent`
- `WebSearchAgent`

is replaced as the primary planning path.

### What Stays

The underlying writer, quality checker, and formatter still stay in place.

That means the existing code can still be reused for:

- structure generation
- hook generation
- script writing
- quality scoring
- final formatting

## Data Sources

### Transcript Sources

From selected Theme/outlier videos:

- best effort transcript pull
- excerpt only, not full transcript storage

### Social Discussion Sources

Recent discussion from the last 30 days:

- Reddit
- X / Twitter

### User Sources

The user can provide:

- links/sources to include
- notes/context to include

These are first-class inputs to `Research`.

## Error Handling

### Research Degradation

If transcript fetch fails:

- continue with available videos
- do not fail the entire research step

If Reddit/X search is unavailable:

- continue with transcript + user inputs
- state clearly that social discussion is limited

If the LLM synthesis fails:

- return raw supporting material and a minimal fallback summary

### Create Validation

If title selection is missing:

- block `Create`

If topic selection is missing:

- block `Create`

If research packet is missing:

- block `Create` in the web flow

## Implementation Plan Outline

1. Extend `ResearchRequest` with custom links and custom notes
2. Update `ResearcherAgent` to ingest those fields
3. Add `Research` panel to `api/app_ui.py`
4. Persist selected title/topics in frontend state
5. Make `Create` send selected title/topics/research packet
6. In web mode, bypass the old `ResearchAgent` / `WebSearchAgent` strategy path
7. Keep existing writer/quality pipeline intact

## Risks

### Input Quality

Transcript and discussion quality may vary. The agent must degrade gracefully rather than pretend certainty.

### Mixed Strategy Layers

If the old subtopic/web-search path still runs fully underneath, the app may produce conflicting strategy inputs. The implementation should avoid mixing both systems in web mode.

### Prompt Bloat

Research packet text should be curated and trimmed before script generation so the prompt stays focused.

## Success Criteria

This feature is successful when:

- the user can run `Theme`, then `Research`, then `Create`
- the user can paste custom links and custom notes into `Research`
- the user can choose one title and multiple topics
- `Create` writes toward the chosen title and chosen topics
- the browser flow no longer depends on the old subtopic/web-search planning layer
