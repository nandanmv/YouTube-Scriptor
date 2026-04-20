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
from fastapi.responses import FileResponse
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
    TrendRequest,
    ThemeRequest,
    ResearchRequest,
    AnglesRequest,
    HooksTalkingPointsRequest,
    CreateScriptRequest,
    QuickScriptRequest,
    ClipRequest,
    SearchJob,
    Insight,
)
from storage.database import AnalysisStore
from agents.outlier_agent import OutlierAgent
from agents.discovery_agent import DiscoveryAgent
from agents.trend_agent import TrendAgent
from agents.shortlist_agent import ShortlistAgent
from agents.theme_agent import ThemeAgent
from agents.angle_from_outliers_agent import AngleFromOutliersAgent
from agents.researcher_agent import ResearcherAgent
from agents.hooks_talking_points_agent import HooksTalkingPointsAgent
from agents.script_creator_agent import ScriptCreatorAgent
from agents.quick_script_agent import QuickScriptAgent
from agents.clip_agent import ClipAgent as ClipAgentWorker
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
app_trend_jobs = {}
app_trend_jobs_lock = threading.Lock()
app_create_jobs = {}
app_create_jobs_lock = threading.Lock()
app_research_jobs = {}
app_research_jobs_lock = threading.Lock()
app_clip_jobs = {}
app_clip_jobs_lock = threading.Lock()
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
        return True  # No auth configured — allow all requests

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


def _persist_outlier_results_to_db(job_id: str, query: str, results: list, job_type: str = "outlier") -> None:
    """Save web app outlier/discovery results to DB so they appear in 'Load Past Run' dropdown."""
    try:
        job = SearchJob(
            job_id=job_id,
            query=query,
            status=JobStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            result_count=len(results),
            job_type=job_type,
        )
        store.save_job(job)
        store.update_job_status(job_id, "completed", result_count=len(results))
        store.save_outliers(job_id, results)

        # Save AI insights (including subtopics_covered) for future reuse
        for r in results:
            sc = r.get("success_criteria", "")
            if not sc or sc in ("Analysis failed", "N/A"):
                continue
            try:
                def _to_list(v):
                    return [v] if isinstance(v, str) else (v or [])
                insight = Insight(
                    video_url=r.get("url", ""),
                    video_title=r.get("title", ""),
                    success_criteria=_to_list(r.get("success_criteria", "")),
                    subtopics_covered=r.get("subtopics_covered", "") or "",
                    reusable_insights=_to_list(r.get("reusable_insights", "")),
                    ultimate_titles=_to_list(r.get("ultimate_titles", "")),
                    alternate_hooks=_to_list(r.get("alternate_hooks", "")),
                    generated_at=datetime.now()
                )
                store.save_insight(insight)
            except Exception:
                pass
    except Exception as e:
        console.print(f"[yellow]Warning: Could not persist outlier results to DB: {e}[/yellow]")


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
            save_report=request.include_insights,
            max_subscribers=request.max_subscribers
        )
        results = await loop.run_in_executor(None, runner)

        # Persist to DB so this run appears in the "Load Past Run" dropdown
        await asyncio.get_event_loop().run_in_executor(
            None, _persist_outlier_results_to_db, job_id, request.query, results
        )

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


def _update_app_trend_job(job_id: str, **updates):
    with app_trend_jobs_lock:
        if job_id in app_trend_jobs:
            app_trend_jobs[job_id].update(updates)
            app_trend_jobs[job_id]["updated_at"] = datetime.now().isoformat()


def _append_app_trend_log(job_id: str, message: str):
    with app_trend_jobs_lock:
        job = app_trend_jobs.get(job_id)
        if not job:
            return
        job["logs"].append(message)
        job["updated_at"] = datetime.now().isoformat()


def _update_app_create_job(job_id: str, **updates):
    with app_create_jobs_lock:
        if job_id in app_create_jobs:
            app_create_jobs[job_id].update(updates)
            app_create_jobs[job_id]["updated_at"] = datetime.now().isoformat()


def _append_app_create_log(job_id: str, message: str):
    with app_create_jobs_lock:
        job = app_create_jobs.get(job_id)
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

        # Persist to DB as a discovery job
        query_label = ", ".join(terms)
        await asyncio.get_event_loop().run_in_executor(
            None, _persist_outlier_results_to_db, job_id, query_label, results, "discovery"
        )

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


async def run_app_trend_job(job_id: str, request: TrendRequest):
    """Background task for browser trend discovery with progress logs."""
    try:
        seeds = [seed.strip() for seed in (request.seeds or "").split(",") if seed.strip()]
        _append_app_trend_log(job_id, f"[*] Starting trend discovery across {len(seeds) or 'default'} seed set(s)...")
        agent = TrendAgent(progress_callback=lambda message: _append_app_trend_log(job_id, message))
        loop = asyncio.get_event_loop()
        runner = partial(
            agent.run,
            seeds=seeds or None,
            lookback_days=request.lookback_days,
            max_videos_per_seed=request.max_videos_per_seed,
            ai_only=request.ai_only,
            max_terms=request.max_terms,
        )
        result = await loop.run_in_executor(None, runner)
        _update_app_trend_job(job_id, status="completed", result=result)
        _append_app_trend_log(job_id, f"[+] Trend discovery complete. Ranked {len(result.get('terms', []))} term(s).")
    except Exception as exc:
        _update_app_trend_job(job_id, status="failed", error=str(exc))
        _append_app_trend_log(job_id, f"[!] Trend discovery failed: {exc}")


async def run_app_create_job(job_id: str, request: CreateScriptRequest):
    """Background task — runs ScriptCreatorAgent with progress_callback logging."""
    try:
        _append_app_create_log(job_id, "[*] Starting script creation...")
        
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

        agent = ScriptCreatorAgent(
            progress_callback=lambda message: _append_app_create_log(job_id, message)
        )
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
            seed_sources=seed_sources,
            selected_title=request.selected_title,
            selected_topics=request.selected_topics,
            research_packet=request.research_packet,
            selected_hook_script=request.selected_hook_script,
            talking_points=request.talking_points,
            outro=request.outro,
            shorts_segments=request.shorts_segments,
            selected_thumbnail=request.selected_thumbnail,
        )
        result = await loop.run_in_executor(None, runner)
        _update_app_create_job(job_id, status="completed", result=result)
        _append_app_create_log(job_id, "[+] Script creation complete.")
    except Exception as exc:
        _update_app_create_job(job_id, status="failed", error=str(exc))
        _append_app_create_log(job_id, f"[!] Script creation failed: {exc}")


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
            "web_trends": "POST /api/v1/app/trends",
            "web_theme": "POST /api/v1/app/theme",
            "web_research": "POST /api/v1/app/research",
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
        save_report=request.include_insights,
        max_subscribers=request.max_subscribers
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


@app.post("/api/v1/app/trends")
async def app_trend_search(request: TrendRequest):
    """Run trend discovery for the web app."""
    seeds = [seed.strip() for seed in (request.seeds or "").split(",") if seed.strip()]
    agent = TrendAgent()
    loop = asyncio.get_event_loop()
    runner = partial(
        agent.run,
        seeds=seeds or None,
        lookback_days=request.lookback_days,
        max_videos_per_seed=request.max_videos_per_seed,
        ai_only=request.ai_only,
        max_terms=request.max_terms,
    )
    return await loop.run_in_executor(None, runner)


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


@app.post("/api/v1/app/trends/start")
async def app_trend_search_start(
    request: TrendRequest,
    background_tasks: BackgroundTasks
):
    """Start async trend discovery for the web app and return a job id."""
    job_id = str(uuid.uuid4())
    with app_trend_jobs_lock:
        app_trend_jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "seeds": request.seeds,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "logs": [],
            "result": None,
            "error": None,
        }

    background_tasks.add_task(run_app_trend_job, job_id, request)

    return {
        "job_id": job_id,
        "status": "processing",
        "seeds": request.seeds,
    }


@app.get("/api/v1/app/discovery/jobs/{job_id}")
async def app_discovery_search_status(job_id: str):
    """Poll job status and progress logs for a running browser discovery search."""
    with app_discovery_jobs_lock:
        job = app_discovery_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Discovery job not found")
        return job


@app.get("/api/v1/app/trends/jobs/{job_id}")
async def app_trend_search_status(job_id: str):
    """Poll job status and progress logs for a running browser trend discovery."""
    with app_trend_jobs_lock:
        job = app_trend_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Trend job not found")
        return job


@app.post("/api/v1/app/theme")
async def app_theme_analysis(request: ThemeRequest):
    """Run theme analysis for the web app."""
    agent = ThemeAgent()
    loop = asyncio.get_event_loop()
    runner = partial(agent.run, topic=request.topic, videos=request.videos)
    result = await loop.run_in_executor(None, runner)
    if result and "themes" in result and "error" not in result:
        try:
            store.save_theme(request.topic, result.get("themes", {}))
        except Exception:
            pass
    return result


async def run_app_research_job(job_id: str, request: ResearchRequest):
    """Background task for research analysis."""
    def _update(**kw):
        with app_research_jobs_lock:
            if job_id in app_research_jobs:
                app_research_jobs[job_id].update(kw)
                app_research_jobs[job_id]["updated_at"] = datetime.now().isoformat()

    def _log(msg: str):
        with app_research_jobs_lock:
            job = app_research_jobs.get(job_id)
            if job:
                job.setdefault("logs", []).append(msg)
                job["updated_at"] = datetime.now().isoformat()

    try:
        loop = asyncio.get_event_loop()
        _log(f"[*] Starting research for '{request.topic}'...")

        theme_data = request.theme_data
        if not theme_data and request.videos:
            try:
                _log("[*] Running theme analysis...")
                theme_agent = ThemeAgent()
                theme_result = await loop.run_in_executor(
                    None,
                    partial(theme_agent.run, topic=request.topic, videos=request.videos),
                )
                if theme_result and "themes" in theme_result and "error" not in theme_result:
                    theme_data = theme_result.get("themes", {})
                    try:
                        store.save_theme(request.topic, theme_data)
                    except Exception:
                        pass
            except Exception:
                pass

        _log("[*] Fetching transcripts and synthesizing research...")
        agent = ResearcherAgent()
        runner = partial(
            agent.run,
            topic=request.topic,
            videos=request.videos,
            theme_data=theme_data,
            custom_links=request.custom_links,
            custom_notes=request.custom_notes,
        )
        result = await loop.run_in_executor(None, runner)
        result["theme_data"] = theme_data or {}

        if result.get("best_titles") or result.get("high_level_topics"):
            try:
                store.save_research(request.topic, result)
            except Exception:
                pass

        _log("[+] Research complete.")
        _update(status="completed", result=result)
    except Exception as exc:
        _update(status="failed", error=str(exc))
        _log(f"[!] Research failed: {exc}")


@app.post("/api/v1/app/research/start")
async def app_research_start(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start async research analysis and return a job id."""
    job_id = str(uuid.uuid4())
    with app_research_jobs_lock:
        app_research_jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "topic": request.topic,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "logs": [],
            "result": None,
            "error": None,
        }
    background_tasks.add_task(run_app_research_job, job_id, request)
    return {"job_id": job_id, "status": "processing", "topic": request.topic}


@app.get("/api/v1/app/research/jobs/{job_id}")
async def app_research_job_status(job_id: str):
    """Poll research job status."""
    with app_research_jobs_lock:
        job = app_research_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Research job not found")
        return job


@app.post("/api/v1/app/research")
async def app_research_analysis(request: ResearchRequest):
    """Legacy sync endpoint — kept for compatibility."""
    loop = asyncio.get_event_loop()
    theme_data = request.theme_data
    if not theme_data and request.videos:
        try:
            theme_agent = ThemeAgent()
            theme_result = await loop.run_in_executor(
                None,
                partial(theme_agent.run, topic=request.topic, videos=request.videos),
            )
            if theme_result and "themes" in theme_result and "error" not in theme_result:
                theme_data = theme_result.get("themes", {})
                try:
                    store.save_theme(request.topic, theme_data)
                except Exception:
                    pass
        except Exception:
            pass
    agent = ResearcherAgent()
    runner = partial(
        agent.run,
        topic=request.topic,
        videos=request.videos,
        theme_data=theme_data,
        custom_links=request.custom_links,
        custom_notes=request.custom_notes,
    )
    result = await loop.run_in_executor(None, runner)
    result["theme_data"] = theme_data or {}
    if result.get("best_titles") or result.get("high_level_topics"):
        try:
            store.save_research(request.topic, result)
        except Exception:
            pass
    return result


@app.post("/api/v1/app/hooks-talking-points")
async def app_hooks_talking_points(request: HooksTalkingPointsRequest):
    """Generate hooks, talking points outline, outro, and shorts segments."""
    agent = HooksTalkingPointsAgent()
    loop = asyncio.get_event_loop()
    runner = partial(
        agent.run,
        topic=request.topic,
        title=request.title,
        topics=request.topics,
        custom_notes=request.custom_notes,
    )
    result = await loop.run_in_executor(None, runner)
    if result.get("hooks") and not result.get("error"):
        try:
            store.save_hooks_tp(request.topic, request.title, result)
        except Exception:
            pass
    return result


@app.get("/api/v1/past-hooks-tp")
async def list_past_hooks_tp():
    """List saved hooks & talking points runs."""
    return {"results": store.list_hooks_tp(limit=100)}


@app.get("/api/v1/past-hooks-tp/{htp_id}")
async def get_past_hooks_tp(htp_id: int):
    """Get a saved hooks & talking points result by ID."""
    result = store.get_hooks_tp(htp_id)
    if not result:
        raise HTTPException(status_code=404, detail="Hooks & talking points result not found")
    return result


@app.post("/api/v1/app/angles")
async def app_angles_analysis(request: AnglesRequest):
    """Generate angles for the web app."""
    agent = AngleFromOutliersAgent()
    loop = asyncio.get_event_loop()
    runner = partial(agent.run, topic=request.topic, videos=request.videos)
    return await loop.run_in_executor(None, runner)


@app.get("/api/v1/past-outliers")
async def list_past_outlier_jobs():
    """List completed outlier runs from the database."""
    jobs = store.list_outlier_jobs(limit=100)
    return {"jobs": jobs}


@app.get("/api/v1/past-outliers/{job_id}")
async def get_past_outlier_videos(job_id: str):
    """Get outlier videos (with insights) from a past run."""
    videos = store.get_outlier_videos_with_insights(job_id)
    if not videos:
        raise HTTPException(status_code=404, detail="No outliers found for this job")
    return {"job_id": job_id, "videos": videos}


@app.get("/api/v1/past-discovery")
async def list_past_discovery_jobs():
    """List completed discovery runs from the database."""
    jobs = store.list_discovery_jobs(limit=100)
    return {"jobs": jobs}


@app.get("/api/v1/past-discovery/{job_id}")
async def get_past_discovery_videos(job_id: str):
    """Get videos from a past discovery run."""
    videos = store.get_outlier_videos_with_insights(job_id)
    if not videos:
        raise HTTPException(status_code=404, detail="No videos found for this discovery job")
    return {"job_id": job_id, "videos": videos}


@app.get("/api/v1/past-themes")
async def list_past_themes():
    """List saved theme analyses."""
    themes = store.list_themes(limit=100)
    return {"themes": themes}


@app.get("/api/v1/past-themes/{theme_id}")
async def get_past_theme(theme_id: int):
    """Get a saved theme by ID."""
    theme = store.get_theme(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme


@app.get("/api/v1/past-research")
async def list_past_research():
    """List saved research results (titles & topics runs)."""
    results = store.list_research(limit=100)
    return {"results": results}


@app.get("/api/v1/past-research/{research_id}")
async def get_past_research(research_id: int):
    """Get a saved research result by ID."""
    result = store.get_research(research_id)
    if not result:
        raise HTTPException(status_code=404, detail="Research result not found")
    return result


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
        seed_sources=seed_sources,
        selected_title=request.selected_title,
        selected_topics=request.selected_topics,
        research_packet=request.research_packet,
        selected_hook_script=request.selected_hook_script,
        talking_points=request.talking_points,
        outro=request.outro,
        shorts_segments=request.shorts_segments,
        selected_thumbnail=request.selected_thumbnail,
    )
    return await loop.run_in_executor(None, runner)


@app.post("/api/v1/app/create/start")
async def app_create_script_start(
    request: CreateScriptRequest,
    background_tasks: BackgroundTasks
):
    """Start async script creation for the web app and return a job id."""
    job_id = str(uuid.uuid4())
    with app_create_jobs_lock:
        app_create_jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "topic": request.topic,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "logs": [],
            "result": None,
            "error": None,
        }

    background_tasks.add_task(run_app_create_job, job_id, request)

    return {
        "job_id": job_id,
        "status": "processing",
        "topic": request.topic,
    }


@app.get("/api/v1/app/create/jobs/{job_id}")
async def app_create_script_status(job_id: str):
    """Poll job status and progress logs for a running browser script creation."""
    with app_create_jobs_lock:
        job = app_create_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Create job not found")
        return job


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


# ==================== Clip Endpoints ====================

async def run_app_clip_job(job_id: str, request: ClipRequest):
    """Background task: download a YouTube clip segment."""
    def _update(**kw):
        with app_clip_jobs_lock:
            if job_id in app_clip_jobs:
                app_clip_jobs[job_id].update(kw)
                app_clip_jobs[job_id]["updated_at"] = datetime.now().isoformat()

    def _log(msg: str):
        with app_clip_jobs_lock:
            job = app_clip_jobs.get(job_id)
            if job:
                job.setdefault("logs", []).append(msg)
                job["updated_at"] = datetime.now().isoformat()

    try:
        agent = ClipAgentWorker()
        loop = asyncio.get_event_loop()
        runner = partial(agent.run, url=request.url, start=request.start, end=request.end,
                         job_id=job_id, progress_callback=_log)
        file_path = await loop.run_in_executor(None, runner)
        if file_path:
            _update(status="completed", file_path=file_path, filename=os.path.basename(file_path))
            _log(f"[+] Done: {os.path.basename(file_path)}")
        else:
            _update(status="failed", error="Download failed or file not found.")
            _log("[!] Download failed.")
    except Exception as exc:
        _update(status="failed", error=str(exc))
        _log(f"[!] Error: {exc}")


@app.post("/api/v1/app/clip/start")
async def app_clip_start(request: ClipRequest, background_tasks: BackgroundTasks):
    """Start a clip download job."""
    job_id = str(uuid.uuid4())
    with app_clip_jobs_lock:
        app_clip_jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "url": request.url,
            "start": request.start,
            "end": request.end,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "logs": [],
            "file_path": None,
            "filename": None,
            "error": None,
        }
    background_tasks.add_task(run_app_clip_job, job_id, request)
    return {"job_id": job_id, "status": "processing"}


@app.get("/api/v1/app/clip/jobs/{job_id}")
async def app_clip_status(job_id: str):
    """Poll clip job status."""
    with app_clip_jobs_lock:
        job = app_clip_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Clip job not found")
    return job


@app.get("/api/v1/app/clip/download/{job_id}")
async def app_clip_download(job_id: str, background_tasks: BackgroundTasks):
    """Stream the clipped file to the browser then delete it from the server."""
    with app_clip_jobs_lock:
        job = app_clip_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Clip job not found")
    if job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Clip not ready yet")
    file_path = job.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Clip file not found on disk")

    def _cleanup():
        try:
            os.remove(file_path)
            console.print(f"[dim]Deleted clip after download: {os.path.basename(file_path)}[/dim]")
        except Exception:
            pass

    background_tasks.add_task(_cleanup)
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="video/mp4",
    )


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
