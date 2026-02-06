"""
FastAPI server for the YouTube Analysis Platform.

Provides REST API with async job processing and webhook notifications.
Enables external integrations with Zapier, n8n, and custom applications.
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import uuid
from datetime import datetime
import asyncio
import httpx
import sys
import os
from rich.console import Console

# Add parent directory to path to import agents
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import (
    SearchRequest,
    SearchResponse,
    JobStatusResponse,
    MarkVideoRequest,
    WebhookPayload,
    JobStatus,
    OutlierResult
)
from storage.database import AnalysisStore
from agents.outlier_agent import OutlierAgent
from agents.shortlist_agent import ShortlistAgent

# Initialize FastAPI app
app = FastAPI(
    title="YouTube Analysis API",
    description="Async API for YouTube outlier detection and script generation",
    version="1.0.0"
)

# Enable CORS for web integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage
store = AnalysisStore()
console = Console()


# ==================== Helper Functions ====================

async def send_webhook(url: str, data: dict, retries: int = 3) -> bool:
    """
    Send webhook with retry logic.

    Args:
        url: Webhook URL
        data: Payload data
        retries: Number of retry attempts

    Returns:
        True if successful
    """
    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            try:
                response = await client.post(
                    url,
                    json=data,
                    timeout=30.0,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                console.print(f"[green]✓ Webhook sent to {url}[/green]")
                return True
            except httpx.RequestError as e:
                console.print(f"[yellow]Webhook attempt {attempt + 1} failed: {e}[/yellow]")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except httpx.HTTPStatusError as e:
                console.print(f"[red]Webhook returned error: {e}[/red]")
                break

    console.print(f"[red]✗ Failed to send webhook to {url}[/red]")
    return False


async def run_outlier_search(job_id: str, query: str, webhook_url: Optional[str] = None):
    """
    Background task: Run outlier search agent.

    Args:
        job_id: Job identifier
        query: Search query
        webhook_url: Optional webhook URL for notification
    """
    try:
        console.print(f"[cyan]Starting outlier search: {query} (Job: {job_id})[/cyan]")

        # Run agent synchronously in thread pool
        agent = OutlierAgent(use_database=True)
        loop = asyncio.get_event_loop()
        outliers = await loop.run_in_executor(None, agent.run, query, job_id)

        # Save results to database
        store.save_outliers(job_id, outliers)
        store.update_job_status(job_id, "completed", result_count=len(outliers))

        console.print(f"[green]✓ Outlier search completed: {len(outliers)} results[/green]")

        # Send webhook notification
        if webhook_url:
            payload = WebhookPayload(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                query=query,
                result_count=len(outliers),
                results_url=f"/api/v1/jobs/{job_id}/results"
            )
            await send_webhook(webhook_url, payload.model_dump(mode='json'))

    except Exception as e:
        console.print(f"[red]✗ Outlier search failed: {e}[/red]")
        store.update_job_status(job_id, "failed", error_message=str(e))

        if webhook_url:
            payload = WebhookPayload(
                job_id=job_id,
                status=JobStatus.FAILED,
                error=str(e)
            )
            await send_webhook(webhook_url, payload.model_dump(mode='json'))


async def run_shortlist_analysis(webhook_url: Optional[str] = None):
    """
    Background task: Run shortlist analysis.

    Args:
        webhook_url: Optional webhook URL for notification
    """
    try:
        console.print("[cyan]Starting shortlist analysis...[/cyan]")

        # Run agent synchronously in thread pool
        agent = ShortlistAgent(use_database=True)
        loop = asyncio.get_event_loop()
        result_file = await loop.run_in_executor(None, agent.run)

        console.print(f"[green]✓ Shortlist analysis completed: {result_file}[/green]")

        # Send webhook notification
        if webhook_url:
            await send_webhook(webhook_url, {
                "status": "completed",
                "result_file": result_file,
                "timestamp": datetime.now().isoformat()
            })

    except Exception as e:
        console.print(f"[red]✗ Shortlist analysis failed: {e}[/red]")

        if webhook_url:
            await send_webhook(webhook_url, {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "YouTube Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "search": "POST /api/v1/search/outliers",
            "jobs": "GET /api/v1/jobs",
            "job_status": "GET /api/v1/jobs/{job_id}",
            "mark_video": "POST /api/v1/videos/mark",
            "marked_videos": "GET /api/v1/videos/marked",
            "shortlist": "POST /api/v1/shortlist/analyze"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/v1/search/outliers", response_model=SearchResponse)
async def search_outliers(
    request: SearchRequest,
    background_tasks: BackgroundTasks
):
    """
    Start async outlier search job.

    Returns job_id immediately, processes in background,
    sends webhook when complete.

    Args:
        request: Search request with query and optional webhook URL

    Returns:
        Job ID and status
    """
    job_id = str(uuid.uuid4())

    # Create job record
    from models.schemas import SearchJob
    job = SearchJob(
        job_id=job_id,
        query=request.query,
        status=JobStatus.PROCESSING,
        created_at=datetime.now(),
        webhook_url=request.webhook_url
    )
    store.save_job(job)

    # Schedule background task
    background_tasks.add_task(
        run_outlier_search,
        job_id=job_id,
        query=request.query,
        webhook_url=request.webhook_url
    )

    return SearchResponse(
        job_id=job_id,
        status=JobStatus.PROCESSING,
        message=f"Search started for: {request.query}"
    )


@app.get("/api/v1/jobs", response_model=List[JobStatusResponse])
async def list_jobs(limit: int = Query(50, ge=1, le=100)):
    """
    List recent jobs.

    Args:
        limit: Maximum number of jobs to return (1-100)

    Returns:
        List of job status responses
    """
    jobs = store.list_jobs(limit=limit)

    return [
        JobStatusResponse(
            job_id=job.job_id,
            query=job.query,
            status=job.status,
            created_at=job.created_at,
            completed_at=job.completed_at,
            result_count=job.result_count,
            error_message=job.error_message
        )
        for job in jobs
    ]


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Check job status and get results.

    Args:
        job_id: Job identifier

    Returns:
        Job status with results if completed

    Raises:
        HTTPException: If job not found
    """
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = None
    if job.status == JobStatus.COMPLETED:
        results = store.get_outliers(job_id)

    return JobStatusResponse(
        job_id=job.job_id,
        query=job.query,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        result_count=job.result_count,
        results=results,
        error_message=job.error_message
    )


@app.get("/api/v1/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    """
    Get job results only (without full job metadata).

    Args:
        job_id: Job identifier

    Returns:
        List of outlier results

    Raises:
        HTTPException: If job not found or not completed
    """
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job is {job.status.value}, results not available yet"
        )

    return store.get_outliers(job_id)


@app.post("/api/v1/videos/mark")
async def mark_video(request: MarkVideoRequest):
    """
    Mark or unmark video for analysis.

    Replaces manual markdown editing!

    Args:
        request: Video URL and mark status

    Returns:
        Success status

    Raises:
        HTTPException: If video not found
    """
    success = store.mark_video(request.url, request.marked)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Video not found in database. It must be part of a completed search."
        )

    action = "marked" if request.marked else "unmarked"
    return {
        "success": True,
        "message": f"Video {action} for analysis",
        "url": request.url
    }


@app.get("/api/v1/videos/marked")
async def get_marked_videos():
    """
    Get all videos marked for analysis.

    Replaces ShortlistAgent's markdown parsing!

    Returns:
        List of marked videos
    """
    marked = store.get_marked_videos()
    return {
        "count": len(marked),
        "videos": marked
    }


@app.post("/api/v1/shortlist/analyze")
async def analyze_shortlist(
    background_tasks: BackgroundTasks,
    webhook_url: Optional[str] = None
):
    """
    Analyze all marked videos with AI insights.

    Args:
        webhook_url: Optional webhook URL for notification

    Returns:
        Status message
    """
    marked = store.get_marked_videos()

    if not marked:
        raise HTTPException(
            status_code=400,
            detail="No videos marked for analysis"
        )

    # Schedule background task
    background_tasks.add_task(
        run_shortlist_analysis,
        webhook_url=webhook_url
    )

    return {
        "status": "processing",
        "message": f"Analyzing {len(marked)} marked videos",
        "count": len(marked)
    }


# ==================== Error Handlers ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for uncaught errors."""
    console.print(f"[red]Unhandled error: {exc}[/red]")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    console.print("[green]✓ YouTube Analysis API started[/green]")
    console.print(f"[cyan]Database: {store.db_path}[/cyan]")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    store.close()
    console.print("[yellow]YouTube Analysis API stopped[/yellow]")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
