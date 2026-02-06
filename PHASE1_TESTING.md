# Phase 1 Implementation - Testing Guide

## Overview

Phase 1 adds REST API capabilities and structured SQLite storage while maintaining 100% backward compatibility with existing CLI commands.

## Installation

1. Install new dependencies:
```bash
pip install -r requirements.txt
```

2. Verify installation:
```bash
python3.10 -c "import fastapi, uvicorn, pydantic, httpx; print('✓ All Phase 1 dependencies installed')"
```

## Testing Plan

### Test 1: Backward Compatibility - CLI Still Works

**Goal:** Verify existing CLI commands work unchanged.

```bash
# Test outlier command (existing functionality)
python3.10 main.py outlier "claude code"

# Expected:
# - Searches for videos
# - Creates results/claude_code.md
# - Displays results table
# - NO database interaction (default behavior)
```

**Verification:**
- [ ] Command completes without errors
- [ ] Markdown file created in `results/`
- [ ] File contains table with Shortlist column
- [ ] No new database file created (backward compat mode)

---

### Test 2: Database Initialization

**Goal:** Verify SQLite database is created with correct schema.

```bash
# Initialize database
python3.10 -c "from storage.database import AnalysisStore; store = AnalysisStore(); print('✓ Database initialized')"

# Check database file exists
ls -lh youtube_analysis.db
```

**Verification:**
- [ ] `youtube_analysis.db` file created
- [ ] File size > 0 bytes
- [ ] No errors during initialization

**Inspect schema:**
```bash
sqlite3 youtube_analysis.db ".schema"
```

**Expected tables:**
- `search_jobs`
- `outlier_videos`
- `insights`
- `scripts`

---

### Test 3: Start API Server

**Goal:** Launch FastAPI server successfully.

```bash
# Start server (Terminal 1)
python3.10 main.py serve --port 8000

# Expected output:
# [green]Starting YouTube Analysis API server...[/green]
# [cyan]Server: http://0.0.0.0:8000[/cyan]
# [cyan]API Docs: http://0.0.0.0:8000/docs[/cyan]
```

**Verification:**
- [ ] Server starts without errors
- [ ] Port 8000 is listening
- [ ] Health check works:

```bash
# In Terminal 2
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"..."}
```

---

### Test 4: API Documentation (Interactive)

**Goal:** Verify FastAPI auto-generated docs are accessible.

1. Open browser: `http://localhost:8000/docs`

**Verification:**
- [ ] Swagger UI loads correctly
- [ ] All endpoints visible:
  - `GET /`
  - `GET /health`
  - `POST /api/v1/search/outliers`
  - `GET /api/v1/jobs`
  - `GET /api/v1/jobs/{job_id}`
  - `GET /api/v1/jobs/{job_id}/results`
  - `POST /api/v1/videos/mark`
  - `GET /api/v1/videos/marked`
  - `POST /api/v1/shortlist/analyze`

2. Try the "Try it out" feature for `GET /health`

---

### Test 5: Async Job Creation

**Goal:** Create async outlier search job via API.

```bash
# Create job
curl -X POST http://localhost:8000/api/v1/search/outliers \
  -H "Content-Type: application/json" \
  -d '{"query": "ai agents", "webhook_url": null}'

# Expected response:
# {
#   "job_id": "uuid-here",
#   "status": "processing",
#   "message": "Search started for: ai agents"
# }
```

**Save the job_id for next tests!**

**Verification:**
- [ ] Returns 200 status code
- [ ] Returns valid job_id (UUID format)
- [ ] Status is "processing"
- [ ] Server console shows: `[cyan]Starting outlier search: ai agents (Job: ...)[/cyan]`

---

### Test 6: Job Status Polling

**Goal:** Check job status while processing and after completion.

```bash
# Replace JOB_ID with your actual job ID
JOB_ID="paste-job-id-here"

# Check status (may be processing)
curl http://localhost:8000/api/v1/jobs/$JOB_ID

# Wait 30 seconds, then check again (should be completed)
sleep 30
curl http://localhost:8000/api/v1/jobs/$JOB_ID
```

**Verification:**
- [ ] First request: `"status": "processing"`, `"results": null`
- [ ] Second request: `"status": "completed"`, `"results": [...]`
- [ ] Result count matches number of outliers found

---

### Test 7: Database Storage Verification

**Goal:** Verify results were saved to database.

```bash
# Query database directly
sqlite3 youtube_analysis.db "SELECT * FROM search_jobs;"
sqlite3 youtube_analysis.db "SELECT COUNT(*) FROM outlier_videos;"
sqlite3 youtube_analysis.db "SELECT title, ratio FROM outlier_videos ORDER BY ratio DESC LIMIT 5;"
```

**Verification:**
- [ ] Job exists in `search_jobs` table
- [ ] Outlier videos exist in `outlier_videos` table
- [ ] Data matches API response
- [ ] Ratios are calculated correctly

---

### Test 8: Mark Video for Analysis

**Goal:** Mark video programmatically instead of editing markdown.

```bash
# Get a video URL from previous results
sqlite3 youtube_analysis.db "SELECT url FROM outlier_videos LIMIT 1;"

# Mark it
curl -X POST http://localhost:8000/api/v1/videos/mark \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=YOUR_VIDEO_ID", "marked": true}'

# Verify it's marked
curl http://localhost:8000/api/v1/videos/marked
```

**Verification:**
- [ ] Mark request returns success
- [ ] Marked videos endpoint returns the video
- [ ] Count is 1
- [ ] Database shows `marked_for_analysis = 1`

```bash
sqlite3 youtube_analysis.db "SELECT url, marked_for_analysis FROM outlier_videos WHERE marked_for_analysis = 1;"
```

---

### Test 9: List All Jobs

**Goal:** Retrieve job history.

```bash
curl http://localhost:8000/api/v1/jobs
```

**Verification:**
- [ ] Returns array of jobs
- [ ] Most recent job is first (sorted by created_at DESC)
- [ ] Each job has correct structure (job_id, query, status, etc.)

---

### Test 10: Webhook Notification (Optional)

**Goal:** Verify webhook is sent on completion.

1. Get a webhook URL from https://webhook.site/
2. Copy the unique URL

```bash
curl -X POST http://localhost:8000/api/v1/search/outliers \
  -H "Content-Type: application/json" \
  -d '{"query": "test webhook", "webhook_url": "https://webhook.site/YOUR-UNIQUE-ID"}'
```

3. Wait for job to complete (30-60 seconds)
4. Check webhook.site for incoming request

**Verification:**
- [ ] Webhook received at webhook.site
- [ ] Payload contains job_id, status, result_count
- [ ] Status is "completed"
- [ ] Results URL is provided

---

### Test 11: Error Handling

**Goal:** Verify graceful error handling.

**Invalid job ID:**
```bash
curl http://localhost:8000/api/v1/jobs/invalid-id
# Expected: 404 Not Found
```

**Mark non-existent video:**
```bash
curl -X POST http://localhost:8000/api/v1/videos/mark \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=NONEXISTENT", "marked": true}'
# Expected: 404 Not Found
```

**Verification:**
- [ ] Returns appropriate HTTP status codes
- [ ] Error messages are clear
- [ ] Server doesn't crash

---

### Test 12: Backward Compatibility - Mixed Usage

**Goal:** Verify CLI and API can be used together.

```bash
# Use CLI (old way)
python3.10 main.py outlier "cursor ide"

# Use API (new way)
curl -X POST http://localhost:8000/api/v1/search/outliers \
  -H "Content-Type: application/json" \
  -d '{"query": "cursor ide"}'

# Check that CLI still creates markdown file
ls results/cursor_ide.md
```

**Verification:**
- [ ] CLI creates markdown file as before
- [ ] API creates database records
- [ ] Both work independently
- [ ] No conflicts or errors

---

### Test 13: Database Mode via CLI (Advanced)

**Goal:** Test using database storage from CLI.

This requires modifying the CLI call in main.py to use `use_database=True` temporarily.

**Temporary modification to test:**
Edit `main.py` line 112:
```python
# Change from:
agent = OutlierAgent()
# To:
agent = OutlierAgent(use_database=True)
```

Then run:
```bash
python3.10 main.py outlier "test database mode"
```

**Verification:**
- [ ] Creates markdown file (backward compat)
- [ ] Also saves to database
- [ ] Can query results from database

**Revert changes after testing!**

---

## Phase 1 Completion Checklist

### Core Features
- [x] SQLite database with proper schema
- [x] FastAPI server with endpoints
- [x] Async job processing
- [x] Webhook notifications
- [x] Backward compatible CLI

### API Endpoints
- [x] `POST /api/v1/search/outliers` - Create search job
- [x] `GET /api/v1/jobs` - List jobs
- [x] `GET /api/v1/jobs/{id}` - Get job status
- [x] `POST /api/v1/videos/mark` - Mark video
- [x] `GET /api/v1/videos/marked` - Get marked videos
- [x] `GET /health` - Health check

### Backward Compatibility
- [x] CLI commands unchanged (`outlier`, `eauclair`, `shortlist`)
- [x] Markdown files still generated
- [x] No breaking changes to existing code
- [x] Database is optional (not required for CLI usage)

### Quality Checks
- [ ] All 13 tests pass
- [ ] API documentation accessible at `/docs`
- [ ] No Python errors or warnings
- [ ] Database schema correct
- [ ] Webhook retry logic works

---

## Common Issues & Solutions

### Issue: `uvicorn` not found
**Solution:**
```bash
pip install uvicorn[standard]
```

### Issue: Port 8000 already in use
**Solution:**
```bash
# Use different port
python3.10 main.py serve --port 8001
```

### Issue: Database locked
**Solution:**
```bash
# Close all connections
python3.10 -c "from storage.database import AnalysisStore; AnalysisStore().close()"
```

### Issue: Import errors
**Solution:**
```bash
# Ensure you're in the project directory
cd /path/to/YouTube
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## Performance Metrics

**Expected performance for Phase 1:**

- API response time: <200ms for job creation
- Job processing time: 1-3 minutes (depends on search results)
- Database queries: <10ms
- Webhook delivery: <1 second (with retries)

**Test with:**
```bash
# Time API response
time curl http://localhost:8000/health

# Should complete in < 0.1 seconds
```

---

## Next Steps

After Phase 1 testing is complete:

1. **Phase 2**: Event-Driven Architecture
   - Add event broker (Redis or in-memory)
   - Convert agents to event-driven
   - Enable agent-to-agent communication

2. **Phase 3**: Script Generation Pipeline
   - Add TranscriptAgent
   - Add HookAgent
   - Add ScriptAgent
   - Full video → script pipeline

---

## Questions?

If you encounter issues:
1. Check server logs in Terminal 1
2. Check database with `sqlite3 youtube_analysis.db`
3. Verify all dependencies installed: `pip list | grep -E "fastapi|uvicorn|pydantic|httpx"`

Phase 1 provides the foundation for all future enhancements!
