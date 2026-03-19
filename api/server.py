"""
FastAPI server for the YouTube Analysis Platform.

Provides REST API with async job processing and webhook notifications.
Enables external integrations with Zapier, n8n, and custom applications.
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from fastapi.responses import RedirectResponse
from typing import Optional, List
import uuid
from datetime import datetime
import asyncio
import httpx
from functools import partial
import sys
import os
import threading
import hashlib
import hmac
import time
from urllib.parse import quote
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
    OutlierResult,
    DirectOutlierRequest,
    DiscoveryRequest,
    ThemeRequest,
    AnglesRequest,
    CreateScriptRequest,
    QuickScriptRequest
)
from storage.database import AnalysisStore
from agents.outlier_agent import OutlierAgent
from agents.discovery_agent import DiscoveryAgent
from agents.shortlist_agent import ShortlistAgent
from agents.theme_agent import ThemeAgent
from agents.angle_from_outliers_agent import AngleFromOutliersAgent
from agents.script_creator_agent import ScriptCreatorAgent
from agents.quick_script_agent import QuickScriptAgent
from api.home_ui import render_home_app
from api.outliers_ui import render_outliers_app
from api.app_ui import render_app_ui
from api.login_ui import render_login_ui
from config import (
    APP_COOKIE_NAME,
    APP_COOKIE_SECURE,
    APP_LOGIN_PASSWORD,
    APP_SESSION_SECRET,
    APP_SESSION_TTL_HOURS,
)

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
app_outlier_jobs = {}
app_outlier_jobs_lock = threading.Lock()
app_discovery_jobs = {}
app_discovery_jobs_lock = threading.Lock()
PUBLIC_PATHS = {"/health", "/favicon.ico", "/login", "/api/v1/auth/login", "/api/v1/auth/logout"}
HTML_PATHS = {"/", "/app", "/home", "/outliers", "/compare", "/docs"}


# ==================== Helper Functions ====================

def _auth_configured() -> bool:
    return bool(APP_LOGIN_PASSWORD and APP_SESSION_SECRET)


def _password_fingerprint() -> str:
    return hashlib.sha256(APP_LOGIN_PASSWORD.encode("utf-8")).hexdigest()


def _sign_value(value: str) -> str:
    return hmac.new(
        APP_SESSION_SECRET.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def _build_session_token() -> str:
    expires_at = int(time.time()) + max(APP_SESSION_TTL_HOURS, 1) * 3600
    payload = f"{expires_at}:{_password_fingerprint()}"
    signature = _sign_value(payload)
    return f"{payload}.{signature}"


def _is_authenticated(request: Request) -> bool:
    if not _auth_configured():
        return False

    token = request.cookies.get(APP_COOKIE_NAME)
    if not token or "." not in token:
        return False

    payload, signature = token.rsplit(".", 1)
    expected_signature = _sign_value(payload)
    if not hmac.compare_digest(signature, expected_signature):
        return False

    try:
        expires_at_raw, password_hash = payload.split(":", 1)
        expires_at = int(expires_at_raw)
    except ValueError:
        return False

    if expires_at < int(time.time()):
        return False

    return hmac.compare_digest(password_hash, _password_fingerprint())


def _login_redirect(path: str, query: str = "") -> RedirectResponse:
    next_path = path or "/"
    if query:
        next_path = f"{next_path}?{query}"
    encoded_next = quote(next_path, safe="/?=&-%")
    return RedirectResponse(url=f"/login?next={encoded_next}", status_code=303)


def _normalize_next_path(next_path: str) -> str:
    next_path = (next_path or "/").strip()
    if not next_path.startswith("/") or next_path.startswith("//"):
        return "/"
    return next_path


@app.middleware("http")
async def require_app_login(request: Request, call_next):
    """Protect the browser UI and API with a simple shared-password session."""
    path = request.url.path

    if request.method == "OPTIONS" or path in PUBLIC_PATHS:
        return await call_next(request)

    if _is_authenticated(request):
        return await call_next(request)

    if path == "/openapi.json" or path.startswith("/api/"):
        return JSONResponse(
            status_code=401,
            content={"detail": "Authentication required"}
        )

    if path in HTML_PATHS or request.headers.get("accept", "").startswith("text/html"):
        return _login_redirect(path, request.url.query)

    return JSONResponse(status_code=401, content={"detail": "Authentication required"})

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


def _update_app_outlier_job(job_id: str, **updates):
    with app_outlier_jobs_lock:
        if job_id in app_outlier_jobs:
            app_outlier_jobs[job_id].update(updates)
            app_outlier_jobs[job_id]["updated_at"] = datetime.now().isoformat()


def _append_app_outlier_log(job_id: str, message: str):
    with app_outlier_jobs_lock:
        job = app_outlier_jobs.get(job_id)
        if not job:
            return
        job["logs"].append(message)
        job["updated_at"] = datetime.now().isoformat()


async def run_app_outlier_job(job_id: str, request: DirectOutlierRequest):
    """Background task for browser outlier search with progress logs."""
    try:
        _append_app_outlier_log(job_id, f"[*] Starting outlier search for '{request.query}'...")
        agent = OutlierAgent(progress_callback=lambda message: _append_app_outlier_log(job_id, message))
        loop = asyncio.get_event_loop()
        runner = partial(
            agent.run,
            query=request.query,
            job_id=None,
            min_outliers=request.limit,
            generate_insights=request.include_insights,
            save_report=request.include_insights
        )
        results = await loop.run_in_executor(None, runner)
        _update_app_outlier_job(
            job_id,
            status="completed",
            result={
                "query": request.query,
                "count": min(len(results), request.limit),
                "results": results[:request.limit],
            }
        )
        _append_app_outlier_log(job_id, f"[+] Outlier search complete. Returned {min(len(results), request.limit)} results.")
    except Exception as exc:
        _update_app_outlier_job(job_id, status="failed", error=str(exc))
        _append_app_outlier_log(job_id, f"[!] Outlier search failed: {exc}")


def _update_app_discovery_job(job_id: str, **updates):
    with app_discovery_jobs_lock:
        if job_id in app_discovery_jobs:
            app_discovery_jobs[job_id].update(updates)
            app_discovery_jobs[job_id]["updated_at"] = datetime.now().isoformat()


def _append_app_discovery_log(job_id: str, message: str):
    with app_discovery_jobs_lock:
        job = app_discovery_jobs.get(job_id)
        if not job:
            return
        job["logs"].append(message)
        job["updated_at"] = datetime.now().isoformat()


async def run_app_discovery_job(job_id: str, request: DiscoveryRequest):
    """Background task for browser discovery with progress logs."""
    try:
        terms = [term.strip() for term in request.terms.split(",") if term.strip()]
        _append_app_discovery_log(job_id, f"[*] Starting discovery for {len(terms)} term(s)...")
        agent = DiscoveryAgent(progress_callback=lambda message: _append_app_discovery_log(job_id, message))
        loop = asyncio.get_event_loop()
        runner = partial(agent.run, terms)
        results, report_name = await loop.run_in_executor(None, runner)
        _update_app_discovery_job(
            job_id,
            status="completed",
            result={
                "terms": terms,
                "count": len(results),
                "report_name": report_name,
                "results": results,
            }
        )
        _append_app_discovery_log(job_id, f"[+] Discovery job complete. Returned {len(results)} results.")
    except Exception as exc:
        _update_app_discovery_job(job_id, status="failed", error=str(exc))
        _append_app_discovery_log(job_id, f"[!] Discovery failed: {exc}")


# ==================== API Endpoints ====================

@app.get("/", response_class=HTMLResponse)
async def app_home():
    """Comprehensive web app homepage."""
    return HTMLResponse(render_app_ui())


@app.get("/home", response_class=HTMLResponse)
async def home():
    """Human-friendly overview page."""
    return HTMLResponse(render_home_app())


@app.get("/app", response_class=HTMLResponse)
async def app_page():
    """Alias for the main web app."""
    return HTMLResponse(render_app_ui())


@app.get("/api")
async def root():
    """Root API endpoint with API information."""
    return {
        "name": "YouTube Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "search": "POST /api/v1/search/outliers",
            "outliers_direct": "GET /api/v1/outliers/direct?query=topic",
            "web_outlier": "POST /api/v1/app/outlier",
            "web_discovery": "POST /api/v1/app/discovery",
            "web_theme": "POST /api/v1/app/theme",
            "web_angles": "POST /api/v1/app/angles",
            "web_create": "POST /api/v1/app/create",
            "web_quick_script": "POST /api/v1/app/quick-script",
            "outliers_app": "GET /outliers",
            "jobs": "GET /api/v1/jobs",
            "job_status": "GET /api/v1/jobs/{job_id}",
            "mark_video": "POST /api/v1/videos/mark",
            "marked_videos": "GET /api/v1/videos/marked",
            "shortlist": "POST /api/v1/shortlist/analyze",
            "docs": "GET /docs",
            "web_app": "GET /"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/favicon.ico")
async def favicon():
    """Avoid noisy 404s for the browser favicon request."""
    return Response(status_code=204)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/", error: str = ""):
    """Render the shared-password login page."""
    next_path = _normalize_next_path(next)
    if _is_authenticated(request):
        return RedirectResponse(url=next_path, status_code=303)

    return HTMLResponse(
        render_login_ui(
            next_path=next_path,
            error=error,
            configured=_auth_configured()
        )
    )


@app.post("/api/v1/auth/login")
async def login_action(payload: dict):
    """Create a signed browser session cookie."""
    if not _auth_configured():
        raise HTTPException(
            status_code=503,
            detail="Login is not configured. Set APP_LOGIN_PASSWORD and APP_SESSION_SECRET."
        )

    password = str(payload.get("password", "")).strip()
    next_path = _normalize_next_path(str(payload.get("next", "/")))

    if not hmac.compare_digest(password, APP_LOGIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Incorrect password")

    response = JSONResponse({"success": True, "next": next_path})
    response.set_cookie(
        key=APP_COOKIE_NAME,
        value=_build_session_token(),
        max_age=max(APP_SESSION_TTL_HOURS, 1) * 3600,
        httponly=True,
        secure=APP_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return response


@app.post("/api/v1/auth/logout")
async def logout_action():
    """Clear the browser session cookie."""
    response = JSONResponse({"success": True})
    response.delete_cookie(key=APP_COOKIE_NAME, path="/")
    return response


@app.get("/outliers", response_class=HTMLResponse)
async def outliers_app():
    """Browser UI for regular YouTube outlier discovery."""
    return HTMLResponse(render_outliers_app())


@app.get("/compare", response_class=HTMLResponse)
async def compare_redirect_app():
    """Backwards-compatible alias for the regular outliers browser UI."""
    return HTMLResponse(render_outliers_app())


@app.get("/api/v1/outliers/direct")
async def search_outliers_direct(
    query: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(10, ge=1, le=30)
):
    """
    Search regular YouTube outliers directly for lightweight web UI flows.
    """
    agent = OutlierAgent()
    loop = asyncio.get_event_loop()
    runner = partial(
        agent.run,
        query=query,
        job_id=None,
        min_outliers=limit,
        generate_insights=False,
        save_report=False
    )
    results = await loop.run_in_executor(None, runner)

    return {
        "query": query,
        "count": min(len(results), limit),
        "results": results[:limit],
    }


@app.post("/api/v1/app/outlier")
async def app_outlier_search(request: DirectOutlierRequest):
    """Run single-topic outlier search for the web app."""
    agent = OutlierAgent()
    loop = asyncio.get_event_loop()
    runner = partial(
        agent.run,
        query=request.query,
        job_id=None,
        min_outliers=request.limit,
        generate_insights=request.include_insights,
        save_report=request.include_insights
    )
    results = await loop.run_in_executor(None, runner)
    return {
        "query": request.query,
        "count": min(len(results), request.limit),
        "results": results[:request.limit]
    }


@app.post("/api/v1/app/outlier/start")
async def app_outlier_search_start(
    request: DirectOutlierRequest,
    background_tasks: BackgroundTasks
):
    """Start async outlier search for the web app and return a job id."""
    job_id = str(uuid.uuid4())
    with app_outlier_jobs_lock:
        app_outlier_jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "query": request.query,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "logs": [],
            "result": None,
            "error": None,
        }

    background_tasks.add_task(run_app_outlier_job, job_id, request)

    return {
        "job_id": job_id,
        "status": "processing",
        "query": request.query,
    }


@app.get("/api/v1/app/outlier/jobs/{job_id}")
async def app_outlier_search_status(job_id: str):
    """Poll job status and progress logs for a running browser outlier search."""
    with app_outlier_jobs_lock:
        job = app_outlier_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Outlier job not found")
        return job


@app.post("/api/v1/app/discovery")
async def app_discovery_search(request: DiscoveryRequest):
    """Run multi-term discovery for the web app."""
    terms = [term.strip() for term in request.terms.split(",") if term.strip()]
    agent = DiscoveryAgent()
    loop = asyncio.get_event_loop()
    runner = partial(agent.run, terms)
    results, report_name = await loop.run_in_executor(None, runner)
    return {
        "terms": terms,
        "count": len(results),
        "report_name": report_name,
        "results": results
    }


@app.post("/api/v1/app/discovery/start")
async def app_discovery_search_start(
    request: DiscoveryRequest,
    background_tasks: BackgroundTasks
):
    """Start async discovery for the web app and return a job id."""
    job_id = str(uuid.uuid4())
    with app_discovery_jobs_lock:
        app_discovery_jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "terms": request.terms,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "logs": [],
            "result": None,
            "error": None,
        }

    background_tasks.add_task(run_app_discovery_job, job_id, request)

    return {
        "job_id": job_id,
        "status": "processing",
        "terms": request.terms,
    }


@app.get("/api/v1/app/discovery/jobs/{job_id}")
async def app_discovery_search_status(job_id: str):
    """Poll job status and progress logs for a running browser discovery search."""
    with app_discovery_jobs_lock:
        job = app_discovery_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Discovery job not found")
        return job


@app.post("/api/v1/app/theme")
async def app_theme_analysis(request: ThemeRequest):
    """Run theme analysis for the web app."""
    agent = ThemeAgent()
    loop = asyncio.get_event_loop()
    runner = partial(agent.run, topic=request.topic, videos=request.videos)
    return await loop.run_in_executor(None, runner)


@app.post("/api/v1/app/angles")
async def app_angles_analysis(request: AnglesRequest):
    """Generate angles for the web app."""
    agent = AngleFromOutliersAgent()
    loop = asyncio.get_event_loop()
    runner = partial(agent.run, topic=request.topic, videos=request.videos)
    return await loop.run_in_executor(None, runner)


@app.post("/api/v1/app/create")
async def app_create_script(request: CreateScriptRequest):
    """Run the full script creation workflow in non-interactive mode."""
    seed_angles = None
    seed_sources = None

    if request.selected_videos:
        angle_agent = AngleFromOutliersAgent()
        loop = asyncio.get_event_loop()
        angle_runner = partial(angle_agent.run, topic=request.topic, videos=request.selected_videos)
        angle_result = await loop.run_in_executor(None, angle_runner)
        seed_angles = angle_result.get("angles", [])
        seed_sources = [
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "channel": item.get("channel"),
                "views": item.get("views", 0),
                "ratio": item.get("ratio", 0),
            }
            for item in request.selected_videos
        ]

    agent = ScriptCreatorAgent()
    loop = asyncio.get_event_loop()
    runner = partial(
        agent.run,
        topic=request.topic,
        notes=request.notes,
        interactive=False,
        auto_select=None,
        manual_mode=False,
        duration=request.duration,
        top_n_outliers=request.top_n_outliers,
        strategy=request.strategy,
        seed_angles=seed_angles,
        seed_sources=seed_sources
    )
    return await loop.run_in_executor(None, runner)


@app.post("/api/v1/app/quick-script")
async def app_quick_script(request: QuickScriptRequest):
    """Run quick script generation in non-interactive mode."""
    agent = QuickScriptAgent()
    loop = asyncio.get_event_loop()
    runner = partial(
        agent.run,
        topic=request.topic,
        notes=request.notes,
        duration=request.duration,
        reading_level=request.reading_level,
        audience=request.audience,
        interactive=False
    )
    return await loop.run_in_executor(None, runner)


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
