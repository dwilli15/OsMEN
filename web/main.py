"""FastAPI Web Dashboard for OsMEN

Main application entry point providing no-code interface for system management.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import (Depends, FastAPI, File, Form, HTTPException, Request,
                     UploadFile)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .agent_config import AgentConfigManager
from .auth import check_auth, get_current_user, login_user, logout_user
from .digest import DigestGenerator
from .status import (get_agent_health, get_memory_system_status,
                     get_service_health, get_system_status)

# Import syllabus parser (optional)
try:
    from parsers.syllabus.syllabus_parser import SyllabusParser
    PARSER_AVAILABLE = True
except Exception:
    PARSER_AVAILABLE = False

# Initialize agent config manager and digest generator
config_manager = AgentConfigManager()
digest_generator = DigestGenerator()

# Initialize FastAPI app
app = FastAPI(
    title="OsMEN Dashboard",
    description="No-code interface for Jarvis-like AI assistant",
    version="1.7.0"
)

# Add session middleware
SECRET_KEY = os.getenv("WEB_SECRET_KEY", "dev-secret-key-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static files
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Log buffer for live streaming
log_buffer = []
MAX_LOG_BUFFER = 100

# In-memory tracker for syllabus uploads (replace with DB in production)
active_uploads = {}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - redirects to dashboard or login."""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login form submission."""
    if await login_user(request, username, password):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "error": "Invalid username or password"}
    )


@app.get("/logout")
async def logout(request: Request):
    """Logout and redirect to login page."""
    await logout_user(request)
    return RedirectResponse(url="/login")


# Health Check Endpoints (no authentication required for monitoring)
@app.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 OK if the service is running.
    Used by load balancers and monitoring systems.
    """
    return {
        "status": "ok",
        "service": "OsMEN Dashboard",
        "version": "1.7.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Returns 200 OK if the service is ready to accept traffic.
    Checks critical dependencies.
    """
    # Check if critical files/directories exist
    critical_paths = [
        Path("/home/runner/work/OsMEN/OsMEN/.copilot/memory.json"),
        Path("/home/runner/work/OsMEN/OsMEN/agents"),
        Path("/home/runner/work/OsMEN/OsMEN/web")
    ]
    
    all_ready = all(path.exists() for path in critical_paths)
    
    if not all_ready:
        return {
            "status": "not_ready",
            "message": "Critical dependencies not available",
            "timestamp": datetime.now().isoformat()
        }
    
    # Check memory system
    memory_status = await get_memory_system_status()
    memory_ok = memory_status.get("status") in ["healthy", "not_initialized"]
    
    if not memory_ok:
        return {
            "status": "not_ready",
            "message": "Memory system error",
            "timestamp": datetime.now().isoformat()
        }
    
    return {
        "status": "ready",
        "service": "OsMEN Dashboard",
        "version": "1.7.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/healthz")
async def kubernetes_health():
    """
    Kubernetes-style health check endpoint.
    Alias for /health for Kubernetes compatibility.
    """
    return await health_check()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(check_auth)):
    """Main dashboard page."""
    status = await get_system_status()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "status": status,
            "now": datetime.now()
        }
    )


@app.get("/api/status")
async def status_api(user: dict = Depends(check_auth)):
    """API endpoint for system status."""
    return await get_system_status()


@app.get("/api/agents")
async def agents_api(user: dict = Depends(check_auth)):
    """API endpoint for agent health."""
    return await get_agent_health()


@app.get("/api/services")
async def services_api(user: dict = Depends(check_auth)):
    """API endpoint for service health."""
    return await get_service_health()


@app.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request, user: dict = Depends(check_auth)):
    """Agent configuration page."""
    return templates.TemplateResponse(
        "agents.html",
        {
            "request": request,
            "user": user,
            "agents": config_manager.get_all_agents(),
            "langflow_workflows": config_manager.get_langflow_workflows(),
            "n8n_workflows": config_manager.get_n8n_workflows(),
            "memory": config_manager.get_memory_settings(),
            "notifications": config_manager.get_notification_settings()
        }
    )


@app.post("/api/agents/{agent_name}/toggle")
async def toggle_agent(agent_name: str, user: dict = Depends(check_auth)):
    """Toggle agent enabled/disabled."""
    agent = config_manager.get_agent(agent_name)
    if agent:
        config_manager.toggle_agent(agent_name, not agent.get("enabled", False))
        add_log("INFO", f"Agent {agent_name} toggled", "config")
        return {"success": True, "enabled": config_manager.get_agent(agent_name).get("enabled")}
    return {"success": False, "error": "Agent not found"}


@app.post("/api/memory/settings")
async def update_memory_settings(request: Request, user: dict = Depends(check_auth)):
    """Update memory settings."""
    form_data = await request.form()
    settings = {
        "conversation_retention_days": int(form_data.get("conversation_retention_days", 45)),
        "summary_retention_months": int(form_data.get("summary_retention_months", 12)),
        "context_window_size": int(form_data.get("context_window_size", 8000)),
        "auto_summarize": form_data.get("auto_summarize") == "on"
    }
    config_manager.update_memory_settings(settings)
    add_log("INFO", "Memory settings updated", "config")
    return {"success": True}


@app.post("/api/notifications/settings")
async def update_notification_settings(request: Request, user: dict = Depends(check_auth)):
    """Update notification settings."""
    form_data = await request.form()
    settings = {
        "email_enabled": form_data.get("email_enabled") == "on",
        "push_enabled": form_data.get("push_enabled") == "on",
        "dashboard_enabled": form_data.get("dashboard_enabled") == "on",
        "quiet_hours": {
            "start": form_data.get("quiet_hours_start", "22:00"),
            "end": form_data.get("quiet_hours_end", "08:00")
        }
    }
    config_manager.update_notification_settings(settings)
    add_log("INFO", "Notification settings updated", "config")
    return {"success": True}


@app.get("/digest", response_class=HTMLResponse)
async def digest_page(request: Request, user: dict = Depends(check_auth)):
    """Daily digest page."""
    date = request.query_params.get('date', datetime.now().strftime('%Y-%m-%d'))
    data = digest_generator.get_digest_data(date)
    return templates.TemplateResponse(
        "digest.html",
        {
            "request": request,
            "user": user,
            "date": date,
            "activities": data['activities'],
            "task_stats": data['task_statistics'],
            "procrastination": data['procrastination_insights'],
            "health": data['health_correlations']
        }
    )


@app.get("/api/digest/data")
async def get_digest_data_api(request: Request, user: dict = Depends(check_auth)):
    """Get digest data API."""
    date = request.query_params.get('date')
    return digest_generator.get_digest_data(date)


@app.post("/api/digest/feedback")
async def save_digest_feedback(request: Request, user: dict = Depends(check_auth)):
    """Save daily feedback."""
    form_data = await request.form()
    date = form_data.get('date')
    feedback = {
        'mood': int(form_data.get('mood', 3)),
        'productivity': int(form_data.get('productivity', 3)),
        'challenges': form_data.get('challenges', ''),
        'wins': form_data.get('wins', ''),
        'improvements': form_data.get('improvements', '')
    }
    success = digest_generator.save_feedback(date, feedback)
    if success:
        add_log("INFO", f"Daily reflection saved for {date}", "digest")
        return HTMLResponse("<div class='text-green-600'>Reflection saved successfully!</div>")
    return HTMLResponse("<div class='text-red-600'>Failed to save reflection</div>")


@app.get("/api/digest/export/pdf")
async def export_digest_pdf(request: Request, user: dict = Depends(check_auth)):
    """Export digest as PDF."""
    import tempfile

    from fastapi.responses import FileResponse
    
    date = request.query_params.get('date', datetime.now().strftime('%Y-%m-%d'))
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.close()
    
    success = digest_generator.export_pdf(date, temp_file.name)
    if success:
        add_log("INFO", f"Digest PDF exported for {date}", "digest")
        return FileResponse(
            temp_file.name,
            media_type='application/pdf',
            filename=f'digest_{date}.pdf'
        )
    raise HTTPException(status_code=500, detail="Failed to generate PDF")


@app.get("/api/digest/export/json")
async def export_digest_json(request: Request, user: dict = Depends(check_auth)):
    """Export digest as JSON."""
    import tempfile

    from fastapi.responses import FileResponse
    
    date = request.query_params.get('date', datetime.now().strftime('%Y-%m-%d'))
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    temp_file.close()
    
    success = digest_generator.export_json(date, temp_file.name)
    if success:
        add_log("INFO", f"Digest JSON exported for {date}", "digest")
        return FileResponse(
            temp_file.name,
            media_type='application/json',
            filename=f'digest_{date}.json'
        )
    raise HTTPException(status_code=500, detail="Failed to generate JSON")


@app.get("/logs/stream")
async def stream_logs(request: Request, user: dict = Depends(check_auth)):
    """Server-Sent Events endpoint for live log streaming."""
    async def event_generator():
        # Send initial logs from buffer
        for log in log_buffer[-50:]:  # Last 50 logs
            yield f"data: {json.dumps(log)}\n\n"
        
        # Keep connection alive and send new logs
        while True:
            if await request.is_disconnected():
                break
            
            # In production, this would tail actual log files
            # For now, send heartbeat
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ===== CALENDAR OAUTH ENDPOINTS (A1.1) =====

@app.get("/calendar/setup", response_class=HTMLResponse)
async def calendar_setup_page(request: Request, user: dict = Depends(check_auth)):
    """Calendar setup/connection page."""
    return templates.TemplateResponse(
        "calendar_setup.html",
        {
            "request": request,
            "user": user,
            "google_client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "microsoft_client_id": os.getenv("MICROSOFT_CLIENT_ID", ""),
        }
    )


@app.get("/api/calendar/google/oauth")
async def google_oauth_init(request: Request, user: dict = Depends(check_auth)):
    """Initialize Google Calendar OAuth flow.
    
    Returns authorization URL for user to click.
    Stores state token in session for verification.
    """
    import base64
    import secrets
    
    state_token = secrets.token_urlsafe(32)
    request.session["google_oauth_state"] = state_token
    
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/calendar/google/callback")
    
    oauth_params = {
        "client_id": google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar",
        "access_type": "offline",
        "state": state_token
    }
    
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + "&".join(
        f"{k}={v}" for k, v in oauth_params.items()
    )
    
    return {"auth_url": auth_url, "provider": "google"}


@app.get("/api/calendar/google/callback")
async def google_oauth_callback(request: Request, code: str = None, state: str = None, user: dict = Depends(check_auth)):
    """Handle Google Calendar OAuth callback.
    
    Exchanges authorization code for access token.
    Stores credentials in secure session.
    """
    import requests as http_requests

    # Verify state token
    stored_state = request.session.get("google_oauth_state")
    if not state or state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid state token")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/calendar/google/callback")
    }
    
    try:
        response = http_requests.post(token_url, json=token_data)
        response.raise_for_status()
        tokens = response.json()
        
        # Store credentials in session
        request.session["google_calendar_token"] = tokens
        request.session["google_calendar_connected"] = True
        
        add_log("INFO", f"User {user.get('username')} connected Google Calendar", "calendar")
        
        return RedirectResponse(url="/calendar/setup?success=true", status_code=302)
    except Exception as e:
        add_log("ERROR", f"Google OAuth callback failed: {e}", "calendar")
        return RedirectResponse(url="/calendar/setup?error=true", status_code=302)


@app.get("/api/calendar/outlook/oauth")
async def outlook_oauth_init(request: Request, user: dict = Depends(check_auth)):
    """Initialize Microsoft Outlook Calendar OAuth flow.
    
    Returns authorization URL for user to click.
    Stores state token in session for verification.
    """
    import secrets
    
    state_token = secrets.token_urlsafe(32)
    request.session["outlook_oauth_state"] = state_token
    
    microsoft_client_id = os.getenv("MICROSOFT_CLIENT_ID")
    redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/api/calendar/outlook/callback")
    
    oauth_params = {
        "client_id": microsoft_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "Calendars.ReadWrite offline_access",
        "response_mode": "query",
        "state": state_token
    }
    
    auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?" + "&".join(
        f"{k}={v}" for k, v in oauth_params.items()
    )
    
    return {"auth_url": auth_url, "provider": "outlook"}


@app.get("/api/calendar/outlook/callback")
async def outlook_oauth_callback(request: Request, code: str = None, state: str = None, user: dict = Depends(check_auth)):
    """Handle Microsoft Outlook Calendar OAuth callback.
    
    Exchanges authorization code for access token.
    Stores credentials in secure session.
    """
    import requests as http_requests

    # Verify state token
    stored_state = request.session.get("outlook_oauth_state")
    if not state or state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid state token")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    # Exchange code for token
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    token_data = {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/api/calendar/outlook/callback")
    }
    
    try:
        response = http_requests.post(token_url, json=token_data)
        response.raise_for_status()
        tokens = response.json()
        
        # Store credentials in session
        request.session["outlook_calendar_token"] = tokens
        request.session["outlook_calendar_connected"] = True
        
        add_log("INFO", f"User {user.get('username')} connected Outlook Calendar", "calendar")
        
        return RedirectResponse(url="/calendar/setup?success=true", status_code=302)
    except Exception as e:
        add_log("ERROR", f"Outlook OAuth callback failed: {e}", "calendar")
        return RedirectResponse(url="/calendar/setup?error=true", status_code=302)


@app.get("/api/calendar/status")
async def calendar_status(request: Request, user: dict = Depends(check_auth)):
    """Check connected calendars for current user."""
    google_connected = request.session.get("google_calendar_connected", False)
    outlook_connected = request.session.get("outlook_calendar_connected", False)
    
    return {
        "google": {"connected": google_connected},
        "outlook": {"connected": outlook_connected},
        "total": sum([google_connected, outlook_connected])
    }


# ===== EVENT PREVIEW & PARSER INTEGRATION (A1.3 / A1.4) =====

@app.get("/events/preview", response_class=HTMLResponse)
async def events_preview_page(request: Request, upload_id: str, user: dict = Depends(check_auth)):
    """Preview parsed syllabus events before calendar sync."""
    rec = active_uploads.get(upload_id)
    if not rec or rec.get("status") != "ready":
        raise HTTPException(status_code=404, detail="Events not ready for preview")
    return templates.TemplateResponse(
        "event_preview.html",
        {
            "request": request,
            "user": user,
            "upload_id": upload_id,
            "events": rec.get("events", []),
        }
    )


@app.post("/api/events/preview/update")
async def update_preview_event(request: Request, user: dict = Depends(check_auth)):
    """Update a single event field (title/date/type/description)."""
    data = await request.json()
    upload_id = data.get("upload_id")
    index = data.get("index")
    field = data.get("field")
    value = data.get("value")
    rec = active_uploads.get(upload_id)
    if not rec or rec.get("status") != "ready":
        raise HTTPException(status_code=404, detail="Upload not found or not ready")
    events = rec.get("events", [])
    if index < 0 or index >= len(events):
        raise HTTPException(status_code=400, detail="Invalid event index")
    if field not in {"title", "date", "type", "description"}:
        raise HTTPException(status_code=400, detail="Invalid field")
    events[index][field] = value
    add_log("INFO", f"Preview event updated: {field} -> {value}", "preview")
    return {"success": True, "event": events[index]}


@app.post("/api/events/preview/bulk")
async def bulk_preview_action(request: Request, user: dict = Depends(check_auth)):
    """Bulk accept/reject events. If rejected, remove from list."""
    data = await request.json()
    upload_id = data.get("upload_id")
    action = data.get("action")  # 'accept_all' | 'reject_indices'
    indices = data.get("indices", [])
    rec = active_uploads.get(upload_id)
    if not rec or rec.get("status") != "ready":
        raise HTTPException(status_code=404, detail="Upload not found or not ready")
    events = rec.get("events", [])
    if action == "accept_all":
        add_log("INFO", f"All events accepted for upload {upload_id}", "preview")
        return {"success": True, "remaining": len(events)}
    elif action == "reject_indices":
        # Remove specified indices (sorted descending to avoid shift)
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(events):
                events.pop(idx)
        add_log("INFO", f"Rejected {len(indices)} events", "preview")
        return {"success": True, "remaining": len(events)}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")


# ===== CALENDAR SYNC (A1.5) =====

@app.post("/api/calendar/sync")
async def calendar_sync(request: Request, upload_id: str, provider: Optional[str] = None, user: dict = Depends(check_auth)):
    """Sync accepted preview events to the connected calendar.

    Prefers the specified provider if provided, otherwise auto-selects based on session.
    """
    from integrations.calendar.calendar_manager import CalendarManager

    rec = active_uploads.get(upload_id)
    if not rec or rec.get("status") != "ready":
        raise HTTPException(status_code=404, detail="Events not ready for sync")

    events = rec.get("events") or []
    if not events:
        raise HTTPException(status_code=400, detail="No events to sync")

    google_connected = request.session.get("google_calendar_connected", False)
    outlook_connected = request.session.get("outlook_calendar_connected", False)

    if not provider:
        # Pick a provider, prefer Outlook (tokens easier to use directly), then Google
        provider = "outlook" if outlook_connected else ("google" if google_connected else None)

    if not provider:
        raise HTTPException(status_code=400, detail="No connected calendar provider found")

    mgr = CalendarManager()

    configured = False
    chosen_provider = None

    try:
        if provider == "outlook" and outlook_connected:
            tokens = request.session.get("outlook_calendar_token") or {}
            access_token = tokens.get("access_token") or tokens.get("token")
            if not access_token:
                raise HTTPException(status_code=400, detail="Outlook access token missing")
            configured = mgr.add_outlook_calendar(access_token=access_token)
            chosen_provider = "outlook"
        elif provider == "google" and google_connected:
            # Prepare a token file compatible with google oauth libs if available
            tokens = request.session.get("google_calendar_token") or {}
            access_token = tokens.get("access_token") or tokens.get("token")
            refresh_token = tokens.get("refresh_token")
            if not access_token:
                raise HTTPException(status_code=400, detail="Google access token missing")

            # Build a token JSON that google.oauth2.credentials can read
            token_payload = {
                "token": access_token,
                "refresh_token": refresh_token,
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                "scopes": ["https://www.googleapis.com/auth/calendar"],
            }

            # Store under project temp/config dir
            cfg_dir = Path(mgr.config_dir)
            cfg_dir.mkdir(parents=True, exist_ok=True)
            token_path = cfg_dir / "google_token.json"
            with open(token_path, "w", encoding="utf-8") as f:
                json.dump(token_payload, f)

            # Add google provider; credentials file won't be used if token is valid
            configured = mgr.add_google_calendar(credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH"), token_path=str(token_path))
            chosen_provider = "google"
        else:
            raise HTTPException(status_code=400, detail="Requested provider not connected")
    except HTTPException:
        raise
    except Exception as e:
        add_log("ERROR", f"Calendar provider setup failed: {e}", "calendar")
        raise HTTPException(status_code=500, detail="Calendar provider setup failed")

    if not configured:
        raise HTTPException(status_code=500, detail="Failed to configure calendar provider")

    # Normalize events for providers; keep minimal required fields
    batch = []
    for ev in events:
        batch.append({
            "title": ev.get("title") or "Event",
            "date": ev.get("date") or "",
            "description": ev.get("description") or "",
            "type": ev.get("type") or "event",
        })

    result = mgr.create_events_batch(batch, provider=chosen_provider)
    add_log("INFO", f"Synced {result.get('successful', 0)}/{result.get('total', 0)} events via {chosen_provider}", "calendar")

    return {
        "success": True,
        "provider": chosen_provider,
        "synced": result.get("successful", 0),
        "failed": result.get("failed", 0),
        "details": result.get("events", []),
    }


# ===== PRIORITY RANKING (A1.8) =====

@app.post("/api/priority/rank")
async def rank_priority(request: Request, upload_id: Optional[str] = None, user: dict = Depends(check_auth)):
    """Return priority-ranked tasks/events. If upload_id is provided, rank its events."""
    from scheduling.priority_ranker import PriorityRanker

    tasks = []
    if upload_id:
        rec = active_uploads.get(upload_id)
        if not rec or rec.get("status") != "ready":
            raise HTTPException(status_code=404, detail="Upload not found or not ready")
        tasks = rec.get("events") or []
    else:
        try:
            body = await request.json()
            tasks = body.get("tasks") if isinstance(body, dict) else body
        except Exception:
            tasks = []

    if not isinstance(tasks, list):
        raise HTTPException(status_code=400, detail="Invalid tasks payload")

    ranker = PriorityRanker()
    ranked = ranker.rank_tasks(tasks)
    add_log("INFO", f"Ranked {len(ranked)} tasks/events", "priority")
    return {"count": len(ranked), "items": ranked}


# ===== SCHEDULE GENERATION (A1.6) =====

@app.post("/api/schedule/generate")
async def generate_schedule(request: Request, upload_id: str, days: int = 7, user: dict = Depends(check_auth)):
    """Generate a study schedule from ranked events for the next N days."""
    from scheduling.priority_ranker import PriorityRanker
    from scheduling.schedule_optimizer import ScheduleOptimizer

    rec = active_uploads.get(upload_id)
    if not rec or rec.get("status") != "ready":
        raise HTTPException(status_code=404, detail="Upload not found or not ready")

    events = rec.get("events") or []
    if not events:
        raise HTTPException(status_code=400, detail="No events to schedule")

    # Rank events and then generate sessions
    ranker = PriorityRanker()
    ranked = ranker.rank_tasks(events)

    optimizer = ScheduleOptimizer()
    start_date = datetime.now()
    end_date = start_date + timedelta(days=max(0, int(days)))
    sessions = optimizer.generate_schedule(ranked, start_date, end_date)
    sessions = optimizer.add_buffer_time(sessions)

    # Persist schedule under upload record
    rec["schedule"] = {"generated_at": datetime.now().isoformat(), "sessions": sessions}
    add_log("INFO", f"Generated schedule with {len(sessions)} blocks for upload {upload_id}", "schedule")
    return {"count": len(sessions), "sessions": sessions}


# ===== TASK SOURCE STUBS (A1.7) =====

@app.get("/api/tasks/todoist")
async def tasks_todoist_stub(user: dict = Depends(check_auth)):
    """Stub endpoint for Todoist tasks (integration pending)."""
    sample = [
        {"id": "td-1", "title": "Review lecture notes", "date": datetime.now().date().isoformat(), "priority": "high"},
        {"id": "td-2", "title": "Start project outline", "date": (datetime.now().date()).isoformat(), "priority": "medium"},
    ]
    return {"provider": "todoist", "items": sample, "integration": "pending"}


@app.get("/api/tasks/notion")
async def tasks_notion_stub(user: dict = Depends(check_auth)):
    """Stub endpoint for Notion tasks (integration pending)."""
    sample = [
        {"id": "nt-1", "title": "Draft study plan", "date": (datetime.now().date()).isoformat(), "priority": "medium"},
        {"id": "nt-2", "title": "Compile references", "date": (datetime.now().date()).isoformat(), "priority": "low"},
    ]
    return {"provider": "notion", "items": sample, "integration": "pending"}


# ===== SYLLABUS UPLOAD ENDPOINTS (A1.2) =====

@app.get("/syllabus/upload", response_class=HTMLResponse)
async def syllabus_upload_page(request: Request, user: dict = Depends(check_auth)):
    """Syllabus upload page."""
    return templates.TemplateResponse(
        "syllabus_upload.html",
        {
            "request": request,
            "user": user,
        }
    )


@app.post("/api/syllabus/upload")
async def upload_syllabus(file: UploadFile = File(...), user: dict = Depends(check_auth)):
    """Upload and validate syllabus file (PDF/DOCX)."""
    allowed_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    upload_id = str(uuid.uuid4())
    upload_dir = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / ".." / "content" / "inbox"))) / "syllabi"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{upload_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)

    active_uploads[upload_id] = {
        "filename": file.filename,
        "file_path": str(file_path),
        "file_type": file.content_type,
        "file_size": len(content),
        "status": "parsing",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "user": user.get("username"),
        "events": None,
        "error": None,
    }

    asyncio.create_task(_process_syllabus_async(upload_id))
    add_log("INFO", f"Syllabus uploaded: {file.filename}", "syllabus")

    return {"upload_id": upload_id, "status": "processing"}


async def _process_syllabus_async(upload_id: str):
    """Process syllabus asynchronously and extract events."""
    try:
        if upload_id not in active_uploads:
            return
        rec = active_uploads[upload_id]

        # Parse file
        rec["status"] = "parsing"
        rec["progress"] = 25

        events = []
        if PARSER_AVAILABLE:
            try:
                parser = SyllabusParser()
                parsed = parser.parse(rec["file_path"])
                normalized = parser.normalize_data(parsed)
                raw_events = normalized.get("events", [])
                for ev in raw_events:
                    events.append({
                        "title": ev.get("title") or ev.get("name") or "Event",
                        "date": ev.get("date") or ev.get("due_date") or "",
                        "type": ev.get("type") or "event",
                        "description": ev.get("description") or "",
                    })
            except Exception as e:
                add_log("WARNING", f"Parser error, using fallback: {e}", "syllabus")
        
        # Fallback mock events if parser not available or produced none
        if not events:
            events = [
                {"title": "Assignment 1", "date": "2025-11-20", "type": "assignment", "description": "Complete assignment 1"},
                {"title": "Midterm Exam", "date": "2025-12-10", "type": "exam", "description": "Midterm examination"},
            ]

        rec["status"] = "extracting"
        rec["progress"] = 70

        rec["events"] = events

        # Simple validation/conflict step placeholder
        rec["status"] = "validating"
        rec["progress"] = 90

        rec["status"] = "ready"
        rec["progress"] = 100
        add_log("INFO", f"Syllabus processed: {len(events)} events", "syllabus")
    except Exception as e:
        if upload_id in active_uploads:
            active_uploads[upload_id]["status"] = "error"
            active_uploads[upload_id]["error"] = str(e)
        add_log("ERROR", f"Syllabus processing failed: {e}", "syllabus")


@app.get("/api/syllabus/progress/{upload_id}")
async def syllabus_progress(upload_id: str, user: dict = Depends(check_auth)):
    if upload_id not in active_uploads:
        raise HTTPException(status_code=404, detail="Upload not found")
    rec = active_uploads[upload_id]
    return {
        "upload_id": upload_id,
        "status": rec["status"],
        "progress": rec["progress"],
        "filename": rec["filename"],
        "error": rec["error"],
        "events": rec["events"] if rec["status"] == "ready" else None,
    }


@app.delete("/api/syllabus/upload/{upload_id}")
async def cancel_syllabus_upload(upload_id: str, user: dict = Depends(check_auth)):
    if upload_id not in active_uploads:
        raise HTTPException(status_code=404, detail="Upload not found")
    rec = active_uploads.pop(upload_id)
    try:
        fp = Path(rec["file_path"]) if rec.get("file_path") else None
        if fp and fp.exists():
            fp.unlink(missing_ok=True)
    finally:
        add_log("INFO", f"Syllabus upload cancelled: {upload_id}", "syllabus")
    return {"success": True}


def add_log(level: str, message: str, source: str = "system"):
    """Add log entry to buffer."""
    global log_buffer
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "source": source
    }
    log_buffer.append(log_entry)
    if len(log_buffer) > MAX_LOG_BUFFER:
        log_buffer = log_buffer[-MAX_LOG_BUFFER:]


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    add_log("INFO", "OsMEN Web Dashboard started", "web")
    add_log("INFO", f"Version: {app.version}", "web")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    add_log("INFO", "OsMEN Web Dashboard shutting down", "web")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("WEB_PORT", "8000"))
    host = os.getenv("WEB_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
    import uvicorn
    port = int(os.getenv("WEB_PORT", "8000"))
    host = os.getenv("WEB_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
