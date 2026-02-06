# YouTube Analysis Platform - Multi-Agent System with REST API

A robust, modular, agent-based platform designed to identify high-performing YouTube content. Now with **REST API** for external integrations, async job processing, and structured data storage.

## 🆕 What's New: Phase 1 - API Layer

The platform now offers **two ways to use it**:

1. **CLI** (Original) - Terminal commands for local analysis
2. **REST API** (New) - HTTP endpoints for integrations, webhooks, async processing

> [!WARNING]
> **Security Note**: The API server is designed for local use. It has no authentication by default and uses open CORS settings (`allow_origins=["*"]`). **Do not expose the API server to the public internet** without implementing proper authentication and restricting CORS.

Both methods work independently and can be used together!

---

## Table of Contents

- [Quick Start](#quick-start)
  - [CLI Usage](#cli-usage)
  - [API Usage](#api-usage)
- [Agent Architecture](#agent-architecture)
- [Configuration](#configuration)
- [CLI Commands (Original)](#cli-commands-original)
- [API Endpoints (New)](#api-endpoints-new)
- [Integration Examples](#integration-examples)
- [AI Setup](#ai-setup)
- [Advanced Features](#advanced-features)

---

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd YouTube

# Install dependencies
pip install -r requirements.txt

# Configure AI model (optional, for InsightAgent)
cp .env.template .env
# Edit .env and add your API keys
```

### CLI Usage

**Search for outlier videos:**
```bash
# Single search term
python3.10 main.py outlier "claude code"

# Multiple search terms (Discovery)
python3.10 main.py discovery "claude code, cursor ai, github copilot"

# Unified search and AI brainstorming
python3.10 main.py brainstorm "claude code"

# Analyze manually marked videos
python3.10 main.py shortlist
```

### API Usage

**Start the API server:**
```bash
# Default (port 8000)
python3.10 main.py serve

# Custom port
python3.10 main.py serve --port 8001

# Access API documentation at: http://localhost:8000/docs
```

**Create a search job via API:**
```bash
curl -X POST http://localhost:8000/api/v1/search/outliers \
  -H "Content-Type: application/json" \
  -d '{"query": "ai agents", "webhook_url": "https://webhook.site/your-id"}'

# Returns: {"job_id": "...", "status": "processing"}
```

**Check job status:**
```bash
curl http://localhost:8000/api/v1/jobs/{job_id}
```

**Mark videos programmatically:**
```bash
curl -X POST http://localhost:8000/api/v1/videos/mark \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=abc123", "marked": true}'
```

---

## Agent Architecture

This program uses a modular hierarchy of agents and utilities:

### 1. **YouTubeUtility**
- **Role**: Shared Service
- **Responsibility**: Centralizes all interactions with `yt-dlp` (Search, Metadata, Baseline calculation)
- **Location**: `youtube_utils.py`

### 2. **BaseAgent (Abstract)**
- **Role**: Foundation
- **Responsibility**: Standard interface for all agents with optional database storage
- **Location**: `agents/base.py`
- **New in Phase 1**: Supports both markdown and database storage modes

### 3. **OutlierAgent**
- **Role**: Specialist (Single Term Analysis)
- **Responsibility**:
    - Analyzes a single search term
    - Identifies videos that significantly outperform their channel's median view count
    - Saves reports to `results/` folder and/or database
- **Invocation**:
  - CLI: `python3.10 main.py outlier "search term"`
  - API: `POST /api/v1/search/outliers`

### 4. **DiscoveryAgent** (Renamed from EauClaire)
- **Role**: Strategic Manager (Multi-Term Orchestrator)
- **Responsibility**:
    - Orchestrates complex research by searching for **multiple terms** sequentially
    - Calls the `OutlierAgent` for each term
    - Collates all findings into a single, unified report
- **Invocation**:
  - CLI: `python3.10 main.py discovery "term1, term2, term3"`

### 5. **BrainstormAgent** (New)
- **Role**: Intelligence Orchestrator
- **Responsibility**:
    - Combines discovery and analysis into one step
    - Automatically analyzes the top performers from a search
    - Generates a **Super Table** (`results/brainstorm_[term].md`) with stats and AI insights
- **Invocation**:
  - CLI: `python3.10 main.py brainstorm "search term"`

### 5. **ShortlistAgent**
- **Role**: Post-Search Analyst
- **Responsibility**:
    - Scans for videos marked with `[x]` in Shortlist column (CLI mode)
    - Or queries database for marked videos (API mode)
    - Orchestrates the `InsightAgent` for each selected video
    - Generates deep analysis report in `results/shortlist_insights.md`
- **Invocation**:
  - CLI: `python3.10 main.py shortlist` (after manually marking videos in markdown)
  - API: `POST /api/v1/shortlist/analyze` (after marking via API)

### 6. **InsightAgent (AI-Powered)**
- **Role**: Content Analyst
- **Responsibility**:
    - Fetches video metadata and descriptions
    - Uses AI (via LiteLLM) to extract success criteria, insights, titles, and hooks
    - Returns structured analysis for content creators
- **Invocation**: Called automatically by ShortlistAgent
- **AI Models Supported**: OpenAI GPT-4, Gemini, Claude, Groq, and more

---

## Configuration

Customize behavior in `config.py`:

```python
SEARCH_LIMIT = 20           # Number of results to analyze per search term
CHANNEL_HISTORY = 50        # Number of recent videos for baseline calculation
MIN_MEDIAN_VIEWS = 500      # Minimum channel size threshold
OUTLIER_THRESHOLD = 5.0     # Multiplier for outlier detection (5x median)
AI_MODEL = "openai/gpt-4o"  # AI model for insights (loaded from .env)
```

---

## CLI Commands (Original)

### 1. Search for Outliers - Single Term

```bash
python3.10 main.py outlier "claude code"
```

**What it does:**
- Searches YouTube for "claude code"
- Analyzes up to 20 videos (configurable)
- Calculates each channel's median view count baseline
- Identifies videos performing 5x+ above baseline
- Saves results to `results/claude_code.md`

**Output:**
```
[*] Analyzing 20 videos for outliers matching 'claude code'...
[+] Found Outlier: How I Built an AI Agent (Ratio: 12.50)
[+] Found Outlier: Claude Code Tutorial (Ratio: 8.30)
```

---

### 2. Multi-Term Search (Discovery)

```bash
python3.10 main.py discovery "claude code, cursor ai, github copilot"
```

**What it does:**
- Runs OutlierAgent for each search term
- Deduplicates results by video URL
- Creates unified report with all outliers
- Saves to `results/collated_search_HHMMSS.md`

---

### 3. Unified Discovery & Analysis (Brainstorm)

```bash
python3.10 main.py brainstorm "claude code"
```

**What it does:**
- Automatically finds outliers for the search term.
- Selects the top results (top 5 by default).
- Immediately runs AI Insight analysis on them.
- Generates a **Super Table** with both stats and AI feedback.
- Saves to `results/brainstorm_[term].md`.

---

### 3. Analyze Shortlisted Videos

**Step 1:** Open any report in `results/` directory:
```bash
open results/claude_code.md
```

**Step 2:** Mark your favorite videos by changing:
```markdown
| [ ] | 12.50x | Amazing Video Title | ... |
```
to:
```markdown
| [x] | 12.50x | Amazing Video Title | ... |
```

**Step 3:** Run analysis:
```bash
python3.10 main.py shortlist
```

**What it does:**
- Scans all markdown files in `results/` for `[x]` marks
- Calls InsightAgent for each marked video
- Uses AI to analyze:
  - Why the video succeeded (success criteria)
  - Reusable content insights
  - Alternative high-CTR titles
  - Different hook variations
- Saves to `results/shortlist_insights.md`

---

## API Endpoints (New)

### Base URL
```
http://localhost:8000
```

### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

### 1. Health Check

```bash
GET /health
```

**Example:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

### 2. Create Outlier Search Job (Async)

```bash
POST /api/v1/search/outliers
```

**Request Body:**
```json
{
  "query": "ai agents",
  "webhook_url": "https://webhook.site/your-unique-id"  // optional
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/search/outliers \
  -H "Content-Type: application/json" \
  -d '{
    "query": "claude code",
    "webhook_url": "https://webhook.site/abc123"
  }'
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "message": "Search started for: claude code"
}
```

**What it does:**
- Creates async job (non-blocking)
- Returns immediately with job_id
- Processes search in background
- Sends webhook when complete (optional)
- Saves results to SQLite database

---

### 3. Get Job Status

```bash
GET /api/v1/jobs/{job_id}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000
```

**Response (Processing):**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "query": "claude code",
  "status": "processing",
  "created_at": "2024-01-01T12:00:00",
  "result_count": null
}
```

**Response (Completed):**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "query": "claude code",
  "status": "completed",
  "created_at": "2024-01-01T12:00:00",
  "completed_at": "2024-01-01T12:02:30",
  "result_count": 15,
  "results": [
    {
      "video": {
        "url": "https://youtube.com/watch?v=abc123",
        "title": "How to Build AI Agents",
        "views": 50000,
        "channel": "Tech Channel",
        "subscribers": 100000
      },
      "median_views": 5000.0,
      "ratio": 10.0,
      "marked_for_analysis": false
    }
  ]
}
```

---

### 4. List All Jobs

```bash
GET /api/v1/jobs?limit=50
```

**Example:**
```bash
curl http://localhost:8000/api/v1/jobs?limit=20
```

**Response:**
```json
[
  {
    "job_id": "...",
    "query": "ai agents",
    "status": "completed",
    "created_at": "2024-01-01T12:00:00",
    "result_count": 15
  }
]
```

---

### 5. Mark Video for Analysis (Programmatic Shortlisting)

```bash
POST /api/v1/videos/mark
```

**Replaces manual markdown editing!**

**Request Body:**
```json
{
  "url": "https://youtube.com/watch?v=abc123",
  "marked": true
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/videos/mark \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=abc123",
    "marked": true
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Video marked for analysis",
  "url": "https://youtube.com/watch?v=abc123"
}
```

---

### 6. Get Marked Videos

```bash
GET /api/v1/videos/marked
```

**Example:**
```bash
curl http://localhost:8000/api/v1/videos/marked
```

**Response:**
```json
{
  "count": 3,
  "videos": [
    {
      "video": {
        "url": "https://youtube.com/watch?v=abc123",
        "title": "How to Build AI Agents",
        "views": 50000,
        "channel": "Tech Channel"
      },
      "median_views": 5000.0,
      "ratio": 10.0,
      "marked_for_analysis": true
    }
  ]
}
```

---

### 7. Analyze Shortlisted Videos

```bash
POST /api/v1/shortlist/analyze
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/shortlist/analyze?webhook_url=https://webhook.site/abc123"
```

**Response:**
```json
{
  "status": "processing",
  "message": "Analyzing 3 marked videos",
  "count": 3
}
```

**What it does:**
- Finds all videos marked via API
- Runs InsightAgent on each video
- Generates AI insights asynchronously
- Saves to `results/shortlist_insights.md`
- Sends webhook when complete (optional)

---

## Integration Examples

### Zapier Workflow

**Trigger:** Webhook by Zapier
1. Create search job with Zapier webhook URL
2. Job completes → Zapier receives webhook
3. Parse results and post to Slack/Notion/Airtable

**Example Zap:**
```
1. Webhook (catch hook URL)
2. HTTP Request → POST /api/v1/search/outliers
3. Wait for webhook callback
4. Send to Slack: "Found {result_count} outlier videos!"
```

---

### Python Integration

```python
import requests
import time

# Create job
response = requests.post(
    "http://localhost:8000/api/v1/search/outliers",
    json={"query": "ai agents"}
)
job_id = response.json()["job_id"]

# Poll for completion
while True:
    status = requests.get(f"http://localhost:8000/api/v1/jobs/{job_id}").json()

    if status["status"] == "completed":
        print(f"Found {status['result_count']} outliers!")

        # Mark top 3 for analysis
        for result in status["results"][:3]:
            requests.post(
                "http://localhost:8000/api/v1/videos/mark",
                json={"url": result["video"]["url"], "marked": True}
            )

        # Trigger analysis
        requests.post("http://localhost:8000/api/v1/shortlist/analyze")
        break

    time.sleep(5)
```

---

### JavaScript/Node.js Integration

```javascript
const axios = require('axios');

async function analyzeOutliers(query) {
  // Create job
  const { data } = await axios.post(
    'http://localhost:8000/api/v1/search/outliers',
    { query }
  );

  console.log(`Job created: ${data.job_id}`);

  // Poll for completion
  while (true) {
    await new Promise(resolve => setTimeout(resolve, 5000));

    const status = await axios.get(
      `http://localhost:8000/api/v1/jobs/${data.job_id}`
    );

    if (status.data.status === 'completed') {
      console.log(`Found ${status.data.result_count} outliers`);
      return status.data.results;
    }
  }
}

// Usage
analyzeOutliers('ai agents').then(results => {
  results.forEach(r => {
    console.log(`${r.video.title} - ${r.ratio.toFixed(1)}x`);
  });
});
```

---

### n8n Workflow

**Node 1:** HTTP Request (POST)
- URL: `http://localhost:8000/api/v1/search/outliers`
- Body: `{"query": "{{$json.search_term}}"}`

**Node 2:** Wait (30 seconds)

**Node 3:** HTTP Request (GET)
- URL: `http://localhost:8000/api/v1/jobs/{{$node.0.json.job_id}}`

**Node 4:** IF (status === "completed")

**Node 5:** Send to Notion/Airtable/etc.

---

## AI Setup

The `InsightAgent` uses **[LiteLLM](https://github.com/BerriAI/litellm)** for multi-provider AI support.

### 1. Configure API Keys

Create a `.env` file:

```bash
# Option 1: OpenAI
AI_MODEL=openai/gpt-4o
OPENAI_API_KEY=sk-your-key-here

# Option 2: Google Gemini
AI_MODEL=gemini/gemini-1.5-pro
GEMINI_API_KEY=your-key-here

# Option 3: Anthropic Claude
AI_MODEL=anthropic/claude-3-5-sonnet-20240620
ANTHROPIC_API_KEY=your-key-here

# Option 4: Groq (Fast & Free)
AI_MODEL=groq/llama3-8b-8192
GROQ_API_KEY=your-key-here
```

### 2. Supported Models

- **OpenAI**: `openai/gpt-4o`, `openai/gpt-4-turbo`, `openai/gpt-3.5-turbo`
- **Google**: `gemini/gemini-1.5-pro`, `gemini/gemini-1.5-flash`
- **Anthropic**: `anthropic/claude-3-5-sonnet-20240620`, `anthropic/claude-3-opus`
- **Groq**: `groq/llama3-70b-8192`, `groq/mixtral-8x7b-32768`
- **Local**: `ollama/llama2`, `ollama/mistral`

---

## Advanced Features

### Database Access

The API uses SQLite for structured storage:

```bash
# Open database
sqlite3 youtube_analysis.db

# List all jobs
SELECT * FROM search_jobs ORDER BY created_at DESC LIMIT 10;

# Get top outliers
SELECT title, ratio, views, channel
FROM outlier_videos
ORDER BY ratio DESC
LIMIT 20;

# Find marked videos
SELECT title, url, ratio
FROM outlier_videos
WHERE marked_for_analysis = 1;
```

### Webhook Payload

When a job completes, the webhook receives:

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "query": "ai agents",
  "result_count": 15,
  "results_url": "/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000/results",
  "timestamp": "2024-01-01T12:02:30"
}
```

**Webhook features:**
- 3 automatic retries with exponential backoff
- 30-second timeout per attempt
- Non-blocking (doesn't slow down job processing)

### CORS Support

The API includes CORS middleware for web integrations:
- Accepts requests from any origin (configurable in production)
- Supports all HTTP methods
- Allows custom headers

### Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Job not found",
  "detail": "No job exists with ID: invalid-id",
  "timestamp": "2024-01-01T12:00:00"
}
```

**HTTP Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Results & Output

### CLI Output

**Terminal:**
- Rich color-coded tables
- Real-time progress indicators
- Performance metrics (ratio, views, subscribers)

**Files:**
- `results/<search_term>.md` - Individual search reports
- `results/collated_search_HHMMSS.md` - Multi-term reports
- `results/shortlist_insights.md` - AI analysis results

### API Output

**Database:**
- `youtube_analysis.db` - SQLite database
- Structured tables for jobs, videos, insights
- Query-ready for analytics

**Markdown (optional):**
- Same markdown files as CLI
- Generated for backward compatibility

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│  External Integrations (Zapier, n8n, Custom Apps)       │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/JSON
                     ↓
┌──────────────────────────────────────────────────────────┐
│  FastAPI Server (api/server.py)                          │
│  ├─ POST /api/v1/search/outliers (async job creation)   │
│  ├─ POST /api/v1/videos/mark (programmatic shortlist)   │
│  └─ GET  /api/v1/jobs/{id} (status polling)             │
└─────────────┬────────────────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────────────────┐
│  Agent Network                                           │
│  ├─ OutlierAgent: Detect high-performing videos         │
│  ├─ EauClaireAgent: Multi-term orchestration            │
│  ├─ ShortlistAgent: Parse marked videos                 │
│  └─ InsightAgent: AI-powered analysis                   │
└─────────────┬────────────────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────────────────┐
│  Storage & Utilities                                     │
│  ├─ SQLite Database (structured queries)                │
│  ├─ Markdown Files (backward compatibility)             │
│  ├─ YouTubeUtility (yt-dlp wrapper)                     │
│  └─ LiteLLM (multi-provider AI)                         │
└──────────────────────────────────────────────────────────┘
```

---

## Documentation

- **API Reference**: `API_README.md` - Complete API documentation with examples
- **Testing Guide**: `PHASE1_TESTING.md` - 13-step verification checklist
- **Project Guide**: `CLAUDE.md` - Architecture and design patterns
- **Interactive Docs**: `http://localhost:8000/docs` - Swagger UI (when server running)

---

## Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :8000

# Use different port
python3.10 main.py serve --port 8001
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database locked
```bash
# Close all connections
python3.10 -c "from storage.database import AnalysisStore; AnalysisStore().close()"
```

### Job stuck in "processing"
- Check server logs for errors
- Verify yt-dlp can access YouTube
- Ensure AI API key is valid (for InsightAgent)

---

## Roadmap

### ✅ Phase 1: API Layer + Structured State (Complete)
- REST API with FastAPI
- SQLite database storage
- Async job processing
- Webhook notifications
- Backward compatible CLI

### 🚧 Phase 2: Event-Driven Architecture (Coming Soon)
- Agent-to-agent communication via events
- Parallel processing capabilities
- Redis Streams or in-memory broker
- Dynamic agent composition

### 📋 Phase 3: Script Generation Pipeline (Planned)
- Transcript extraction from videos
- Hook optimization (5 variations)
- Full script generation with timing
- B-roll and SFX suggestions
- Template-based content creation

---

## Contributing

Contributions welcome! The modular architecture makes it easy to add new agents or features.

### Adding a New Agent

1. Create agent class inheriting from `BaseAgent`
2. Implement `run()` method
3. Add command to `main.py`
4. Add API endpoint to `api/server.py` (optional)

---

## License

[Add your license here]

---

## Support

For questions or issues:
- Check documentation: `API_README.md`, `PHASE1_TESTING.md`
- Review interactive API docs: `http://localhost:8000/docs`
- Open an issue on GitHub
