# YouTube Analysis API - Phase 1 Documentation

## Overview

The YouTube Analysis Platform now includes a REST API for external integrations, async job processing, and structured data storage while maintaining full backward compatibility with the CLI.

## What's New in Phase 1

### 1. REST API with FastAPI
- Async job processing for long-running searches
- Webhook notifications for job completion
- Interactive API documentation at `/docs`

### 2. SQLite Storage
- Structured data storage replaces fragile markdown parsing
- Query capabilities for analytics and reporting
- Concurrent access support

### 3. Programmatic Video Marking
- Mark videos for analysis via API instead of manually editing markdown
- Database-backed shortlisting

### 4. Backward Compatibility
- All existing CLI commands work unchanged
- Markdown files still generated
- No breaking changes

---

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Start the API Server

```bash
# Default (port 8000)
python3.10 main.py serve

# Custom port
python3.10 main.py serve --port 8001

# Custom host
python3.10 main.py serve --host 127.0.0.1 --port 8000
```

**Server will be available at:**
- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

---

## API Endpoints

### Health Check

**GET** `/health`

Check if API is running.

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

### Create Outlier Search Job

**POST** `/api/v1/search/outliers`

Start an async outlier detection job.

**Request Body:**
```json
{
  "query": "ai agents",
  "webhook_url": "https://webhook.site/your-id" // optional
}
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "message": "Search started for: ai agents"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/search/outliers \
  -H "Content-Type: application/json" \
  -d '{"query": "claude code", "webhook_url": "https://webhook.site/unique-id"}'
```

---

### Get Job Status

**GET** `/api/v1/jobs/{job_id}`

Check status and results of a job.

```bash
curl http://localhost:8000/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000
```

**Response (Processing):**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "query": "ai agents",
  "status": "processing",
  "created_at": "2024-01-01T12:00:00",
  "completed_at": null,
  "result_count": null,
  "results": null
}
```

**Response (Completed):**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "query": "ai agents",
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

### List All Jobs

**GET** `/api/v1/jobs`

Get recent job history.

**Query Parameters:**
- `limit` (optional): Number of jobs to return (1-100, default: 50)

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
    "completed_at": "2024-01-01T12:02:30",
    "result_count": 15
  },
  ...
]
```

---

### Mark Video for Analysis

**POST** `/api/v1/videos/mark`

Mark or unmark a video for AI analysis.

**Request Body:**
```json
{
  "url": "https://youtube.com/watch?v=abc123",
  "title": "Video Title", // optional
  "marked": true
}
```

```bash
curl -X POST http://localhost:8000/api/v1/videos/mark \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=abc123", "marked": true}'
```

**Response:**
```json
{
  "success": true,
  "message": "Video marked for analysis",
  "url": "https://youtube.com/watch?v=abc123"
}
```

**Note:** Video must exist in database (from a completed search job).

---

### Get Marked Videos

**GET** `/api/v1/videos/marked`

Get all videos marked for analysis.

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
        "channel": "Tech Channel",
        "subscribers": 100000
      },
      "median_views": 5000.0,
      "ratio": 10.0,
      "marked_for_analysis": true
    }
  ]
}
```

---

### Analyze Shortlisted Videos

**POST** `/api/v1/shortlist/analyze`

Trigger AI analysis of all marked videos.

**Query Parameters:**
- `webhook_url` (optional): URL to notify when complete

```bash
curl -X POST "http://localhost:8000/api/v1/shortlist/analyze?webhook_url=https://webhook.site/unique-id"
```

**Response:**
```json
{
  "status": "processing",
  "message": "Analyzing 3 marked videos",
  "count": 3
}
```

---

## Webhooks

When you provide a `webhook_url` when creating a job, you'll receive a POST request when the job completes.

### Webhook Payload (Success)

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

### Webhook Payload (Failure)

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "failed",
  "error": "Error message here",
  "timestamp": "2024-01-01T12:02:30"
}
```

### Webhook Retry Logic

- 3 retry attempts with exponential backoff
- Backoff: 2s, 4s, 8s
- Timeout: 30 seconds per attempt

---

## Integration Examples

### Zapier Integration

**Trigger:** Webhook by Zapier
- URL: `https://hooks.zapier.com/hooks/catch/YOUR_WEBHOOK_ID/`

**Action 1:** Send to Slack when job completes

**Setup:**
1. Create search job with Zapier webhook URL:
```bash
curl -X POST http://localhost:8000/api/v1/search/outliers \
  -H "Content-Type: application/json" \
  -d '{"query": "ai agents", "webhook_url": "https://hooks.zapier.com/hooks/catch/YOUR_ID/"}'
```

2. Configure Zapier to parse webhook and send Slack message

---

### n8n Workflow

**Node 1:** HTTP Request (POST to create job)
```json
{
  "method": "POST",
  "url": "http://localhost:8000/api/v1/search/outliers",
  "body": {
    "query": "{{$json.search_term}}",
    "webhook_url": "{{$node.Webhook.url}}"
  }
}
```

**Node 2:** Webhook (receive completion)

**Node 3:** Process results and save to Airtable/Notion

---

### Python Client

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
    status_response = requests.get(
        f"http://localhost:8000/api/v1/jobs/{job_id}"
    )
    data = status_response.json()

    if data["status"] == "completed":
        print(f"Found {data['result_count']} outliers!")
        for result in data["results"]:
            video = result["video"]
            print(f"- {video['title']} ({result['ratio']:.1f}x)")
        break

    elif data["status"] == "failed":
        print(f"Job failed: {data.get('error_message')}")
        break

    time.sleep(5)  # Wait 5 seconds before checking again
```

---

### JavaScript (Node.js) Client

```javascript
const axios = require('axios');

async function searchOutliers(query) {
  // Create job
  const createResponse = await axios.post(
    'http://localhost:8000/api/v1/search/outliers',
    { query }
  );

  const jobId = createResponse.data.job_id;
  console.log(`Job created: ${jobId}`);

  // Poll for completion
  while (true) {
    await new Promise(resolve => setTimeout(resolve, 5000));

    const statusResponse = await axios.get(
      `http://localhost:8000/api/v1/jobs/${jobId}`
    );

    const data = statusResponse.data;

    if (data.status === 'completed') {
      console.log(`Found ${data.result_count} outliers!`);
      return data.results;
    } else if (data.status === 'failed') {
      throw new Error(data.error_message);
    }

    console.log('Still processing...');
  }
}

// Usage
searchOutliers('ai agents')
  .then(results => console.log(results))
  .catch(err => console.error(err));
```

---

## Database Schema

### search_jobs
```sql
CREATE TABLE search_jobs (
  job_id TEXT PRIMARY KEY,
  query TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  completed_at TEXT,
  webhook_url TEXT,
  error_message TEXT,
  result_count INTEGER
);
```

### outlier_videos
```sql
CREATE TABLE outlier_videos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT NOT NULL,
  views INTEGER NOT NULL,
  median_views REAL NOT NULL,
  ratio REAL NOT NULL,
  channel TEXT NOT NULL,
  subscribers INTEGER,
  marked_for_analysis BOOLEAN DEFAULT 0,
  created_at TEXT NOT NULL,
  FOREIGN KEY (job_id) REFERENCES search_jobs(job_id),
  UNIQUE(job_id, url)
);
```

### Direct Database Access

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

---

## CLI (Backward Compatible)

All existing CLI commands continue to work:

```bash
# Outlier detection (single term)
python3.10 main.py outlier "claude code"

# Multi-term search
python3.10 main.py eauclair "claude code, cursor ai"

# Analyze shortlisted videos
# (manually edit results/*.md to mark videos with [x])
python3.10 main.py shortlist
```

**Note:** CLI operates independently of the API/database unless explicitly enabled.

---

## Configuration

### Environment Variables

Create `.env` file:
```
AI_MODEL=openai/gpt-4o
OPENAI_API_KEY=sk-your-key-here

# Or use other providers:
# AI_MODEL=gemini/gemini-1.5-pro
# GEMINI_API_KEY=your-key-here

# AI_MODEL=anthropic/claude-3-5-sonnet-20240620
# ANTHROPIC_API_KEY=your-key-here
```

### config.py

Adjust thresholds:
```python
SEARCH_LIMIT = 20           # Videos per search
CHANNEL_HISTORY = 50        # Videos for baseline
MIN_MEDIAN_VIEWS = 500      # Minimum channel median
OUTLIER_THRESHOLD = 5.0     # Minimum ratio (5x)
```

---

## Error Handling

### Common HTTP Status Codes

- `200 OK` - Success
- `400 Bad Request` - Invalid input
- `404 Not Found` - Job/video not found
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## Performance

### Expected Latency

- **Job creation:** <200ms
- **Job completion:** 1-3 minutes (depends on results)
- **Database queries:** <10ms
- **Webhook delivery:** <1 second

### Optimization Tips

1. **Concurrent searches:** Run multiple jobs in parallel
2. **Webhook delivery:** Non-blocking, doesn't slow down job
3. **Database indexing:** Indexes on `url` and `marked_for_analysis`

---

## Security Considerations

### Production Deployment

1. **CORS:** Configure `allow_origins` in `api/server.py`
2. **HTTPS:** Use reverse proxy (Nginx, Caddy)
3. **Authentication:** Configure `APP_LOGIN_PASSWORD` and `APP_SESSION_SECRET` for the browser app login
4. **Secrets:** Keep API keys and login secrets in server env vars only, never in git
5. **Rate Limiting:** Prevent abuse

### Minimal Auth Setup

```bash
APP_LOGIN_PASSWORD=change-this
APP_SESSION_SECRET=use-a-long-random-secret
APP_COOKIE_SECURE=true
```

Notes:
- `/login` is the public entry point
- Browser pages and API routes require an authenticated session
- Keep the repo public-safe by committing only `.env.template`, never `.env.production` or real keys

### Example Nginx Config

```nginx
server {
  listen 80;
  server_name yourdomain.com;

  location / {
    proxy_pass http://localhost:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

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
# Ensure dependencies installed
pip install -r requirements.txt

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database locked
```bash
# Close connections
python3.10 -c "from storage.database import AnalysisStore; AnalysisStore().close()"
```

### Job stuck in "processing"
- Check server logs for errors
- Verify yt-dlp can access YouTube
- Check AI model API key is valid

---

## Next Features (Phase 2 & 3)

### Phase 2: Event-Driven Architecture
- Agent-to-agent communication via events
- Parallel processing capabilities
- Dynamic agent composition

### Phase 3: Script Generation
- Transcript extraction
- Hook optimization (5 variations)
- Full script generation with timing
- B-roll and SFX suggestions

---

## Support

**Documentation:**
- API Docs: `http://localhost:8000/docs`
- Testing Guide: `PHASE1_TESTING.md`
- Project README: `CLAUDE.md`

**Common Questions:**

**Q: Can I use CLI and API together?**
A: Yes! They work independently. CLI creates markdown, API uses database.

**Q: How do I migrate existing markdown data?**
A: Not needed. New searches via API go to database, old markdown files remain valid.

**Q: Can I query the database directly?**
A: Yes! Use `sqlite3 youtube_analysis.db` for custom queries.

**Q: Does the API require authentication?**
A: Not in Phase 1. Add authentication middleware for production.

---

**Phase 1 Complete!** Ready for external integrations, async processing, and structured data storage.
