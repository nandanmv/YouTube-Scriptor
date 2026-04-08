# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Overview

This is a multi-agent YouTube analysis platform that identifies high-performing ("outlier") videos using yt-dlp. The system uses a modular agent architecture where specialized agents can be invoked via terminal commands and can orchestrate each other.

For all Outputs, keep the messages very brief for a busy CEO. 

## Running Commands

### Installation
```bash
pip install -r requirements.txt
```

### Environment Setup
Copy `.env.template` to `.env` and configure:
- `AI_MODEL`: Model identifier (e.g., `openai/gpt-4o`, `gemini/gemini-1.5-pro`, `anthropic/Codex-3-5-sonnet-20240620`)
- Corresponding API key (`OPENAI_API_KEY`, `GEMINI_API_KEY`, or `ANTHROPIC_API_KEY`)

### Agent Commands
```bash
# Single-term search for outliers with AI insights (guarantees min 10 outliers)
python3.10 main.py outlier "Codex"

# Multi-term search (calls OutlierAgent for each term, produces collated report)
python3.10 main.py discovery "Codex, cursor ai"

# Create script using selected outliers for angle generation (full workflow)
python3.10 main.py create "your topic" --notes "your rough notes"

# Quick script generation with checklist-driven quality control (bypasses outlier/research phases)
python3.10 main.py quick-script "your topic" --notes "your detailed notes or outline"

# Quick script with custom parameters
python3.10 main.py quick-script "your topic" --notes "your notes" --duration 8 --reading-level "8th grade" --audience "students"
```

## Architecture

### Agent Hierarchy and Data Flow

1. **YouTubeUtility** (`youtube_utils.py`): Centralized wrapper around yt-dlp
   - `search()`: Performs YouTube searches
   - `get_channel_baseline()`: Fetches recent videos and calculates median views
   - `get_channel_info()`: Retrieves subscriber count
   - `get_video_details()`: Fetches full video metadata including description

2. **BaseAgent** (`agents/base.py`): Abstract base class
   - Defines `run()` interface for all agents
   - Provides `save_results()` to generate markdown tables in `results/`

3. **OutlierAgent** (`agents/outlier_agent.py`): Single-term analyzer with AI insights
   - Searches for videos using a search term
   - For each video, fetches the channel's median view count (baseline)
   - Identifies videos with `views / median_views >= OUTLIER_THRESHOLD`
   - Guarantees minimum 10 outliers by automatically expanding search if needed
   - **NEW**: Calls `InsightAgent` on top N outliers (configurable via `INSIGHT_TOP_N`)
   - **NEW**: Saves rich reports to `results/outliers/outlier_<search_term>.md`
   - Table includes: Selection, Score, Video, Views, Median, Subs, Channel, Success Criteria, Subtopics, Insights, Titles, Hooks

4. **DiscoveryAgent** (`agents/discovery_agent.py`): Multi-term orchestrator
   - Takes a comma-separated list of search terms
   - Calls `OutlierAgent.run()` for each term
   - Deduplicates results by URL and produces a single collated report

5. **InsightAgent** (`agents/insight_agent.py`): AI-powered content analyst
   - Fetches full video metadata (title, description)
   - Uses LiteLLM to call configured AI model with a structured prompt
   - Returns JSON with: success_criteria, subtopics_covered, reusable_insights, ultimate_titles, alternate_hooks
   - Called automatically by OutlierAgent for top N videos

6. **AngleFromOutliersAgent** (`agents/angle_from_outliers_agent.py`): Angle generation from selected outliers
   - Reads markdown files from `results/outliers/` to find videos marked in Selection column (| [x] |)
   - Uses AI to extract proven angles from selected outlier videos
   - Replaces angle discovery in script creation workflow
   - User must manually select outliers before running script creation

7. **ScriptCreatorAgent** (`agents/script_creator_agent.py`): Complete script creation pipeline
   - Orchestrates full workflow from angle generation to final teleprompter script
   - 7-step process: angle generation (from selected outliers) → research → web search → structure → hooks → script → quality check
   - Interactive mode with user selections at each step
   - Quality loop with regeneration based on ChecklistAgent scores
   - **NEW**: Requires manual outlier selection before running (see workflow below)

8. **QuickScriptAgent** (`agents/quick_script_agent.py`): Checklist-driven script generation from notes
   - **NEW: Checklist-driven generation** - Passes `script_checklist.json` directly to AI as quality guide
   - **NEW: Automatic scoring** - Uses ChecklistAgent to score each iteration against checklist criteria
   - **NEW: Iteration support** - User sees script + scores, can accept/reject/regenerate (up to 3 iterations)
   - **NEW: Intelligent feedback** - Combines user feedback + low-scoring categories for regeneration
   - Bypasses outlier analysis, angle generation, research, and structure phases
   - Takes topic, notes, duration, reading level, and target audience as inputs
   - Generates scripts with energy markers, pattern interrupts, curiosity gaps, and social proof
   - Ideal for users who already know what they want to say but want quality control
   - Outputs teleprompter script and raw script to `results/scripts/`

9. **ResearchAgent** (`agents/research_agent.py`): Subtopic research with accumulative selection
   - Generates subtopics based on selected angles and user notes
   - **NEW: Accumulative selection model** - Users select subtopics they like and request more
   - Simple workflow: select → request more → select → done
   - No feedback types - just keep adding subtopics until satisfied
   - Selected subtopics accumulate across iterations
   - Respects `MAX_RESEARCH_ITERATIONS` limit (default: 3)
   - Both single-pass `run()` and interactive `run_with_feedback_loop()` methods

### Configuration (`config.py`)

All behavior is controlled via `config.py`:
- `SEARCH_LIMIT`: Initial number of search results to analyze (default: 50)
- `CHANNEL_HISTORY`: Number of recent videos to fetch for baseline calculation (default: 50)
- `MIN_MEDIAN_VIEWS`: Ignore channels below this median threshold (default: 500)
- `OUTLIER_THRESHOLD`: Minimum ratio for outlier detection (default: 5.0x)
- `MAX_SUBSCRIBERS`: Only include channels below this count (default: 50000)
- `INSIGHT_TOP_N`: Number of top outliers to analyze with AI insights (default: 10)
- `AI_MODEL`: AI model identifier loaded from `.env`
- `QUALITY_THRESHOLD`: Minimum quality score for script acceptance (default: 90)
- `MAX_REGENERATIONS`: Maximum script regeneration attempts (default: 3)
- `MAX_RESEARCH_ITERATIONS`: Maximum research iteration batches (default: 3)
- `SCRIPT_GENERATION_TIMEOUT`: Timeout in seconds for script generation (default: 300)
- `DEFAULT_API_TIMEOUT`: Timeout in seconds for other API calls (default: 120)
- `QUICK_SCRIPT_READING_LEVEL`: Target reading level for quick scripts (default: "10th grade")
- `QUICK_SCRIPT_TARGET_AUDIENCE`: Target audience for quick scripts (default: "business person")
- `QUICK_SCRIPT_MAX_ITERATIONS`: Maximum quick script iterations (default: 3)

**Note**: OutlierAgent automatically expands search beyond SEARCH_LIMIT if fewer than 10 outliers are found.

### User Workflows

#### Unified Outlier Analysis Workflow
1. **Search**: Run `outlier` or `discovery` to generate rich reports with AI insights
   - Automatically analyzes top N outliers with AI (configurable via `INSIGHT_TOP_N`)
   - Saves to `results/outliers/outlier_<search_term>.md`
   - Table includes outlier stats + AI insights (Success Criteria, Subtopics, Insights, Titles, Hooks)
2. **Select for Angles**: Open `results/outliers/outlier_<search_term>.md` and mark videos with `[x]` in the **Selection** column

#### Script Creation Workflow (Full Research-Based)
**Prerequisites**: Must run outlier analysis and select videos first

1. **Prepare**: Run `python3.10 main.py outlier "your topic"` to find outliers with AI insights
2. **Select**: Open `results/outliers/outlier_<topic>.md` and mark videos with `[x]` in the **Selection** column
3. **Create**: Run `python3.10 main.py create "your topic" --notes "your notes"`
4. **Step 1**: Select angles generated from your selected outliers
5. **Step 2**: Build subtopics with accumulative selection
   - Initial batch of 8-10 subtopics generated
   - Select subtopics you like (comma-separated numbers or 'all')
   - Request more subtopics if needed
   - Selected subtopics accumulate across batches
   - Continue until satisfied (up to 3 batches)
6. **Steps 3-7**: Web search, structure, hooks, script writing, quality check, teleprompter formatting
7. **Output**: Complete script with quality score and teleprompter-ready format

#### Quick Script Workflow (Checklist-Driven Direct Generation)
**When to use**: You already know your content and don't need outlier research, but want quality control

1. **Prepare Notes**: Write your content outline, key points, or bullet points in a text file or string
2. **Generate**: Run `python3.10 main.py quick-script "your topic" --notes "your detailed notes"`
   - Optional: Add `--duration 8` (default: 11 minutes)
   - Optional: Add `--reading-level "8th grade"` (default: 10th grade)
   - Optional: Add `--audience "students"` (default: business person)
3. **Review Iteration 1**:
   - Script preview displayed (first 2000 + last 500 chars)
   - **Automatic scoring** against checklist criteria:
     - Overall score (0-100) with color coding
     - Category scores (0-10): Hook, Structure, Content, Engagement, Production, CTA
     - Status indicators: ✓ Excellent (≥9), ○ Good (≥7), ✗ Needs work (<7)
     - Improvement suggestions if score < 90
     - Strengths highlighted (categories scoring 9+)
4. **Choose Action**:
   - **Accept (y)**: Save script and exit
   - **Reject (n)**: Exit without saving
   - **Regenerate (r)**: Provide feedback or press Enter for automatic improvement based on scores
5. **Regeneration** (if selected):
   - User feedback + low-scoring categories combined for targeted improvement
   - New script generated and scored
   - Repeat up to 3 total iterations
6. **Output**: Script with checklist compliance section
   - Saved to `results/scripts/quick_teleprompter_<topic>_*.txt`
   - Raw script saved to `results/scripts/quick_script_<topic>_*.txt`

**Key Features**:
- **Checklist compliance**: AI follows `script_checklist.json` criteria for quality
- **Energy markers**: [ENERGY: HIGH/MEDIUM/LOW] for pacing
- **Pattern interrupts**: Every 60 seconds (camera switches, text overlays)
- **Curiosity gaps**: Strategic placement with clear payoffs
- **Social proof**: Credentials, experience, results where relevant
- **B-roll suggestions**: [B-ROLL: description] with URL recommendations
- **Timestamps**: [00:00], [01:30], [03:45] for structure
- **Automatic scoring**: Each iteration scored against 6 checklist categories
- **Intelligent feedback**: Low-scoring categories automatically targeted for improvement

**Note**: This workflow bypasses outlier analysis, angle generation, research, and structure phases. It's faster but doesn't include data-driven insights from high-performing videos. However, it includes automatic quality scoring and iteration support for refinement.

### Key Design Patterns

- **Agent Orchestration**: Higher-level agents (DiscoveryAgent, ScriptCreatorAgent) delegate to lower-level agents rather than duplicating logic
- **Centralized Utilities**: All yt-dlp interactions flow through `YouTubeUtility` to ensure consistent data handling
- **Text-Based Parsing**: AngleFromOutliersAgent uses pattern matching (`| [x] |`) on markdown tables rather than maintaining state in memory
- **LiteLLM Integration**: InsightAgent uses LiteLLM for multi-provider AI support (OpenAI, Gemini, Codex, etc.)
- **Unified Reports**: OutlierAgent produces comprehensive reports with both statistical analysis and AI insights in a single file

### Output Structure

- All reports are saved to `results/` directory
- **Outlier reports with AI insights**: `results/outliers/outlier_<search_term>.md`
- Collated reports: `results/collated_search_HHMMSS.md`
- Script workflows: `results/workflows/script_*.json`
- Teleprompter scripts (full workflow): `results/scripts/teleprompter_*.txt`
- Quick scripts: `results/scripts/quick_teleprompter_*.txt` and `results/scripts/quick_script_*.txt`
- Markdown tables include:
  - **Selection**: Checkbox for angle generation workflow
  - Score (ratio), Video (with link), Views, Median, Subscribers, Channel
  - **AI Insights** (top N videos): Success Criteria, Subtopics Covered, Reusable Insights, Ultimate Titles, Alternate Hooks
