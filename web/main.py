"""FastAPI Web Dashboard for OsMEN

Main application entry point providing no-code interface for system management.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware

from logging_config import configure_logging
from .auth import (
    check_auth,
    ensure_csrf_token,
    get_current_user,
    login_user,
    logout_user,
    role_required,
    validate_csrf,
)
from .status import (
    get_agent_health,
    get_memory_system_status,
    get_service_health,
    get_system_status,
)
from .agent_config import AgentConfigManager
from .digest import DigestGenerator
from calendar_manager import CalendarManager

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
except ImportError:  # pragma: no cover - sentry optional in dev
    sentry_sdk = None
    FastApiIntegration = None

configure_logging()
logger = logging.getLogger(__name__)

APP_VERSION = "1.7.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
SESSION_COOKIE_MAX_AGE = int(os.getenv("SESSION_COOKIE_MAX_AGE", "3600"))
ENFORCE_HTTPS = os.getenv("ENFORCE_HTTPS", "false").lower() == "true"
METRICS_ENABLED = os.getenv("PROMETHEUS_METRICS_ENABLED", "true").lower() == "true"

SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", ENVIRONMENT)
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.2"))
SENTRY_RELEASE = os.getenv("SENTRY_RELEASE", f"osmen-web@{APP_VERSION}")

# Initialize agent config manager and digest generator
config_manager = AgentConfigManager()
digest_generator = DigestGenerator()

# Initialize FastAPI app
app = FastAPI(
    title="OsMEN Dashboard",
    description="No-code interface for Jarvis-like AI assistant",
    version=APP_VERSION
)

if sentry_sdk and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        release=SENTRY_RELEASE,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        integrations=[FastApiIntegration()] if FastApiIntegration else None,
    )

# Add session middleware
SECRET_KEY = os.getenv("WEB_SECRET_KEY", "dev-secret-key-change-in-production")
SESSION_COOKIE_SAMESITE = "none" if SESSION_COOKIE_SECURE else "lax"
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=SESSION_COOKIE_SECURE,
    max_age=SESSION_COOKIE_MAX_AGE,
    same_site=SESSION_COOKIE_SAMESITE,
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply common security headers to every response."""

    def __init__(self, app):
        super().__init__(app)
        self.csp = os.getenv("WEB_CONTENT_SECURITY_POLICY", "default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; connect-src 'self'; font-src 'self';")

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if ENFORCE_HTTPS:
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Content-Security-Policy", self.csp)
        return response

PROMETHEUS_ENABLED = METRICS_ENABLED
REQUEST_COUNT = Counter("osmen_web_requests_total", "Total dashboard HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("osmen_web_request_duration_seconds", "Dashboard HTTP request duration", ["path"])

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

if ENFORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)

if PROMETHEUS_ENABLED:
    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        REQUEST_COUNT.labels(request.method, request.url.path, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(request.url.path).observe(duration)
        return response

# Setup templates and static files
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Add project directories to Python path for proper imports
import sys
for module_dir in ['integrations', 'scheduling', 'parsers', 'reminders', 'health_integration']:
    module_path = str(PROJECT_ROOT / module_dir)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Log buffer for live streaming
log_buffer = []
MAX_LOG_BUFFER = 100

def template_context(request: Request, extra: Optional[dict] = None) -> dict:
    ctx = {"request": request, "csrf_token": ensure_csrf_token(request)}
    if extra:
        ctx.update(extra)
    return ctx


ViewerRole = role_required("viewer")
OperatorRole = role_required("operator")
AdminRole = role_required("admin")

# In-memory tracker for parsed syllabus previews
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
    return templates.TemplateResponse("login.html", template_context(request))


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...)
):
    """Handle login form submission."""
    validate_csrf(request, csrf_token)
    if await login_user(request, username, password):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        template_context(request, {"error": "Invalid username or password"})
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
        "version": APP_VERSION,
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
        PROJECT_ROOT / ".copilot" / "memory.json",
        PROJECT_ROOT / "agents",
        PROJECT_ROOT / "web",
    ]

    if not all(path.exists() for path in critical_paths):
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
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/healthz")
async def kubernetes_health():
    """
    Kubernetes-style health check endpoint.
    Alias for /health for Kubernetes compatibility.
    """
    return await health_check()


@app.get("/metrics")
async def metrics_endpoint():
    """Expose Prometheus metrics when enabled."""
    if not PROMETHEUS_ENABLED:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(check_auth)):
    """Main dashboard page."""
    status = await get_system_status()
    return templates.TemplateResponse(
        "dashboard.html",
        template_context(request, {
            "user": user,
            "status": status,
            "now": datetime.now(),
        })
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
async def agents_page(request: Request, user: dict = Depends(OperatorRole)):
    """Agent configuration page."""
    return templates.TemplateResponse(
        "agents.html",
        template_context(request, {
            "user": user,
            "agents": config_manager.get_all_agents(),
            "langflow_workflows": config_manager.get_langflow_workflows(),
            "n8n_workflows": config_manager.get_n8n_workflows(),
            "memory": config_manager.get_memory_settings(),
            "notifications": config_manager.get_notification_settings(),
        })
    )


@app.post("/api/agents/{agent_name}/toggle")
async def toggle_agent(agent_name: str, request: Request, user: dict = Depends(OperatorRole)):
    """Toggle agent enabled/disabled."""
    validate_csrf(request, request.headers.get("X-CSRF-Token"))
    agent = config_manager.get_agent(agent_name)
    if agent:
        config_manager.toggle_agent(agent_name, not agent.get("enabled", False))
        add_log("INFO", f"Agent {agent_name} toggled", "config")
        return {"success": True, "enabled": config_manager.get_agent(agent_name).get("enabled")}
    return {"success": False, "error": "Agent not found"}


@app.post("/api/memory/settings")
async def update_memory_settings(request: Request, user: dict = Depends(OperatorRole)):
    """Update memory settings."""
    form_data = await request.form()
    validate_csrf(request, form_data.get('csrf_token'))
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
async def update_notification_settings(request: Request, user: dict = Depends(OperatorRole)):
    """Update notification settings."""
    form_data = await request.form()
    validate_csrf(request, form_data.get('csrf_token'))
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
async def digest_page(request: Request, user: dict = Depends(ViewerRole)):
    """Daily digest page."""
    date = request.query_params.get('date', datetime.now().strftime('%Y-%m-%d'))
    data = digest_generator.get_digest_data(date)
    return templates.TemplateResponse(
        "digest.html",
        template_context(request, {
            "user": user,
            "date": date,
            "activities": data['activities'],
            "task_stats": data['task_statistics'],
            "procrastination": data['procrastination_insights'],
            "health": data['health_correlations'],
        })
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
    validate_csrf(request, form_data.get('csrf_token'))
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


# ============================================================================
# Calendar Integration Endpoints (Agent Alpha - Task A1.1)
# ============================================================================

@app.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request, user: dict = Depends(check_auth)):
    """Calendar management page."""
    # Import calendar manager
    from calendar_manager import CalendarManager
    
    manager = CalendarManager()
    status = manager.get_status()
    
    return templates.TemplateResponse(
        "calendar_setup.html",
        {
            "request": request,
            "user": user,
            "status": status,
            "connected_calendars": status.get('configured_providers', []),
            "primary_provider": status.get('primary_provider')
        }
    )


@app.get("/api/calendar/google/oauth")
async def google_calendar_oauth(request: Request, user: dict = Depends(check_auth)):
    """Initiate Google Calendar OAuth flow."""
    # Import Google Calendar integration
    import sys
    from google_calendar import GoogleCalendarIntegration
    
    try:
        google_cal = GoogleCalendarIntegration()
        auth_url = google_cal.get_authorization_url()
        
        if auth_url:
            add_log("INFO", "Google Calendar OAuth initiated", "calendar")
            return {"auth_url": auth_url, "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate OAuth URL")
    
    except Exception as e:
        add_log("ERROR", f"Google Calendar OAuth error: {e}", "calendar")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar/google/callback")
async def google_calendar_callback(request: Request, code: str = None, user: dict = Depends(check_auth)):
    """Handle Google Calendar OAuth callback."""
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code required")
    
    import sys
    from calendar_manager import CalendarManager
    
    try:
        manager = CalendarManager()
        
        # Exchange code for credentials
        credentials_path = BASE_DIR.parent / ".copilot" / "calendar" / "google_credentials.json"
        token_path = BASE_DIR.parent / ".copilot" / "calendar" / "google_token.json"
        
        success = manager.add_google_calendar(
            credentials_path=str(credentials_path),
            token_path=str(token_path)
        )
        
        if success:
            add_log("INFO", "Google Calendar connected successfully", "calendar")
            return RedirectResponse(url="/calendar?status=success")
        else:
            raise HTTPException(status_code=500, detail="Failed to connect Google Calendar")
    
    except Exception as e:
        add_log("ERROR", f"Google Calendar callback error: {e}", "calendar")
        return RedirectResponse(url="/calendar?status=error")


@app.get("/api/calendar/outlook/oauth")
async def outlook_calendar_oauth(request: Request, user: dict = Depends(check_auth)):
    """Initiate Outlook Calendar OAuth flow."""
    # Import Outlook Calendar integration
    import sys
    from outlook_calendar import OutlookCalendarIntegration
    
    try:
        outlook_cal = OutlookCalendarIntegration()
        auth_url = outlook_cal.get_authorization_url()
        
        if auth_url:
            add_log("INFO", "Outlook Calendar OAuth initiated", "calendar")
            return {"auth_url": auth_url, "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate OAuth URL")
    
    except Exception as e:
        add_log("ERROR", f"Outlook Calendar OAuth error: {e}", "calendar")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar/outlook/callback")
async def outlook_calendar_callback(request: Request, code: str = None, user: dict = Depends(check_auth)):
    """Handle Outlook Calendar OAuth callback."""
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code required")
    
    import sys
    from calendar_manager import CalendarManager
    from outlook_calendar import OutlookCalendarIntegration
    
    try:
        # Exchange code for access token
        outlook_cal = OutlookCalendarIntegration()
        access_token = outlook_cal.exchange_code_for_token(code)
        
        if not access_token:
            raise HTTPException(status_code=500, detail="Failed to exchange code for token")
        
        # Add to calendar manager
        manager = CalendarManager()
        success = manager.add_outlook_calendar(access_token)
        
        if success:
            add_log("INFO", "Outlook Calendar connected successfully", "calendar")
            return RedirectResponse(url="/calendar?status=success")
        else:
            raise HTTPException(status_code=500, detail="Failed to connect Outlook Calendar")
    
    except Exception as e:
        add_log("ERROR", f"Outlook Calendar callback error: {e}", "calendar")
        return RedirectResponse(url="/calendar?status=error")


@app.get("/api/calendar/events")
async def list_calendar_events(request: Request, user: dict = Depends(check_auth)):
    """List calendar events."""
    import sys
    from calendar_manager import CalendarManager
    
    try:
        manager = CalendarManager()
        max_results = int(request.query_params.get('max_results', 50))
        events = manager.list_events(max_results=max_results)
        
        return {"events": events, "count": len(events)}
    
    except Exception as e:
        add_log("ERROR", f"Error listing events: {e}", "calendar")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/calendar/sync")
async def sync_calendar_events(request: Request, user: dict = Depends(check_auth)):
    """Sync events to calendar (batch creation)."""
    import sys
    from calendar_manager import CalendarManager
    
    try:
        data = await request.json()
        events = data.get('events', [])
        
        if not events:
            raise HTTPException(status_code=400, detail="No events provided")
        
        manager = CalendarManager()
        result = manager.create_events_batch(events)
        
        add_log("INFO", f"Calendar sync: {result['successful']}/{result['total']} events created", "calendar")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        add_log("ERROR", f"Calendar sync error: {e}", "calendar")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Syllabus Upload and Processing (Agent Alpha - Task A1.2, A1.3)
# ============================================================================

@app.post("/api/syllabus/upload")
async def upload_syllabus(request: Request, user: dict = Depends(check_auth)):
    """Upload and process syllabus file."""
    from fastapi import UploadFile, File
    import tempfile
    import sys
    
    from syllabus.syllabus_parser import SyllabusParser
    
    try:
        form = await request.form()
        file: UploadFile = form.get('file')
        
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.doc']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024
        file_content = await file.read()
        
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Parse syllabus
        parser = SyllabusParser()
        parsed_data = parser.parse(temp_file_path)
        normalized_data = parser.normalize_data(parsed_data)
        
        # Clean up temp file
        Path(temp_file_path).unlink()
        
        # Store parsed data for preview
        preview_id = f"syllabus_{datetime.now().timestamp()}"
        preview_path = BASE_DIR.parent / "content" / "inbox" / f"{preview_id}.json"
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(preview_path, 'w') as f:
            json.dump(normalized_data, f, indent=2)

        active_uploads[preview_id] = {
            "status": "ready",
            "events": normalized_data.get("events", []).copy()
        }
        
        add_log("INFO", f"Syllabus uploaded and parsed: {file.filename}", "syllabus")
        
        return {
            "success": True,
            "preview_id": preview_id,
            "course": normalized_data.get('course', {}),
            "event_count": normalized_data.get('metadata', {}).get('total_events', 0)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        add_log("ERROR", f"Syllabus upload error: {e}", "syllabus")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/syllabus/preview/{preview_id}")
async def get_syllabus_preview(preview_id: str, user: dict = Depends(check_auth)):
    """Get parsed syllabus data for preview."""
    try:
        preview_path = BASE_DIR.parent / "content" / "inbox" / f"{preview_id}.json"
        
        if not preview_path.exists():
            raise HTTPException(status_code=404, detail="Preview not found")
        
        with open(preview_path, 'r') as f:
            data = json.load(f)
        
        return data
    
    except Exception as e:
        add_log("ERROR", f"Preview retrieval error: {e}", "syllabus")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/preview/{preview_id}", response_class=HTMLResponse)
async def event_preview_page(request: Request, preview_id: str, user: dict = Depends(check_auth)):
    """Event preview and editing page."""
    return templates.TemplateResponse(
        "event_preview.html",
        {
            "request": request,
            "user": user,
            "preview_id": preview_id
        }
    )


@app.post("/api/events/preview/update")
async def update_preview_event(request: Request, user: dict = Depends(check_auth)):
    """Update a single staged event field before calendar sync."""
    data = await request.json()
    upload_id = data.get("upload_id")
    index = data.get("index")
    field = data.get("field")
    value = data.get("value")

    record = active_uploads.get(upload_id)
    if not record or record.get("status") != "ready":
        raise HTTPException(status_code=404, detail="Upload not found or not ready")

    events = record.get("events", [])
    if index is None or index < 0 or index >= len(events):
        raise HTTPException(status_code=400, detail="Invalid event index")

    allowed_fields = {"title", "date", "type", "description"}
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail="Invalid field")

    events[index][field] = value
    add_log("INFO", f"Preview event updated ({field})", "preview")
    return {"success": True, "event": events[index]}


@app.post("/api/events/preview/bulk")
async def bulk_preview_action(request: Request, user: dict = Depends(check_auth)):
    """Bulk accept/reject staged preview events."""
    data = await request.json()
    upload_id = data.get("upload_id")
    action = data.get("action")
    indices = data.get("indices", [])

    record = active_uploads.get(upload_id)
    if not record or record.get("status") != "ready":
        raise HTTPException(status_code=404, detail="Upload not found or not ready")

    events = record.get("events", [])

    if action == "accept_all":
        add_log("INFO", f"All events accepted for {upload_id}", "preview")
        return {"success": True, "remaining": len(events)}

    if action == "reject_indices":
        removed = 0
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(events):
                events.pop(idx)
                removed += 1
        add_log("INFO", f"Rejected {removed} events for {upload_id}", "preview")
        return {"success": True, "remaining": len(events)}

    raise HTTPException(status_code=400, detail="Invalid action")


# ============================================================================
# Scheduling Engine Integration (Agent Alpha - Task A1.6)
# ============================================================================

@app.get("/api/schedule/generate")
async def generate_schedule(request: Request, user: dict = Depends(check_auth)):
    """Generate optimal schedule from calendar events."""
    from scheduling.schedule_optimizer import ScheduleOptimizer
    from scheduling.priority_ranker import PriorityRanker
    
    try:
        # Get calendar events
        from calendar_manager import CalendarManager
        
        manager = CalendarManager()
        events = manager.list_events(max_results=100)
        
        if not events:
            return {"schedule": [], "message": "No events to schedule"}
        
        # Calculate priorities
        ranker = PriorityRanker()
        for event in events:
            event['calculated_priority'] = ranker.calculate_priority(event)
        
        # Generate optimized schedule
        optimizer = ScheduleOptimizer()
        schedule = optimizer.optimize(events)
        
        add_log("INFO", f"Schedule generated with {len(schedule)} items", "scheduling")
        
        return {
            "schedule": schedule,
            "event_count": len(events),
            "optimized_count": len(schedule)
        }
    
    except Exception as e:
        add_log("ERROR", f"Schedule generation error: {e}", "scheduling")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request, user: dict = Depends(check_auth)):
    """Tasks and scheduling page."""
    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "user": user
        }
    )


# ============================================================================
# Reminder Integration (Agent Alpha - Task A2.1)
# ============================================================================

@app.post("/api/reminders/create")
async def create_reminder(request: Request, user: dict = Depends(check_auth)):
    """Create reminder for a task."""
    from adaptive_reminders import AdaptiveReminderSystem
    
    try:
        data = await request.json()
        task = data.get('task')
        
        if not task:
            raise HTTPException(status_code=400, detail="Task data required")
        
        reminder_system = AdaptiveReminderSystem()
        reminder = reminder_system.create_reminder(task)
        
        add_log("INFO", f"Reminder created for task: {task.get('title')}", "reminders")
        
        return reminder
    
    except Exception as e:
        add_log("ERROR", f"Reminder creation error: {e}", "reminders")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reminders/due")
async def get_due_reminders(request: Request, user: dict = Depends(check_auth)):
    """Get reminders that are due now."""
    from adaptive_reminders import AdaptiveReminderSystem
    
    try:
        reminder_system = AdaptiveReminderSystem()
        due_reminders = reminder_system.get_due_reminders()
        
        return {"reminders": due_reminders, "count": len(due_reminders)}
    
    except Exception as e:
        add_log("ERROR", f"Error getting due reminders: {e}", "reminders")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reminders/{reminder_id}/snooze")
async def snooze_reminder(reminder_id: str, request: Request, user: dict = Depends(check_auth)):
    """Snooze a reminder."""
    from adaptive_reminders import AdaptiveReminderSystem
    
    try:
        data = await request.json()
        duration_hours = data.get('duration_hours')
        
        reminder_system = AdaptiveReminderSystem()
        success = reminder_system.snooze_reminder(reminder_id, duration_hours)
        
        if success:
            add_log("INFO", f"Reminder snoozed: {reminder_id}", "reminders")
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="Reminder not found")
    
    except Exception as e:
        add_log("ERROR", f"Snooze error: {e}", "reminders")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Integration (Agent Alpha - Task A2.4, A2.5)
# ============================================================================

@app.get("/health", response_class=HTMLResponse)
async def health_page(request: Request, user: dict = Depends(check_auth)):
    """Health data and integration page."""
    return templates.TemplateResponse(
        "health.html",
        {
            "request": request,
            "user": user
        }
    )


@app.get("/api/health/status")
async def get_health_status(request: Request, user: dict = Depends(check_auth)):
    """Get health status summary."""
    from schedule_adjuster import HealthBasedScheduleAdjuster
    
    try:
        adjuster = HealthBasedScheduleAdjuster()
        status = adjuster.get_health_status_summary()
        
        return status
    
    except Exception as e:
        add_log("ERROR", f"Health status error: {e}", "health")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/health/adjust_schedule")
async def adjust_schedule_for_health(request: Request, user: dict = Depends(check_auth)):
    """Adjust schedule based on health data."""
    from schedule_adjuster import HealthBasedScheduleAdjuster
    
    try:
        data = await request.json()
        schedule = data.get('schedule', [])
        
        adjuster = HealthBasedScheduleAdjuster()
        adjusted_schedule = adjuster.adjust_schedule_for_health(schedule)
        
        add_log("INFO", f"Schedule adjusted for health ({len(adjusted_schedule)} items)", "health")
        
        return {"schedule": adjusted_schedule}
    
    except Exception as e:
        add_log("ERROR", f"Schedule adjustment error: {e}", "health")
        raise HTTPException(status_code=500, detail=str(e))


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


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "osmen-web"}


# ============================================================================
# AGENT HUB - Comprehensive Agent Management Interface
# ============================================================================

@app.get("/", response_class=HTMLResponse)
@app.get("/hub", response_class=HTMLResponse)
async def agent_hub():
    """Serve the main agent hub interface"""
    ui_file = Path(__file__).parent / "agent_hub.html"
    with open(ui_file, 'r') as f:
        return HTMLResponse(content=f.read())


@app.get("/api/agents")
async def list_agents():
    """List all agents (from Langflow flows)"""
    try:
        flows_dir = Path(__file__).parent.parent / "langflow" / "flows"
        agents = []
        
        if flows_dir.exists():
            for flow_file in flows_dir.glob("*.json"):
                try:
                    with open(flow_file, 'r') as f:
                        flow = json.load(f)
                        
                        # Skip non-agent flows
                        if flow_file.stem in ['knowledge_specialist']:
                            continue
                            
                        agents.append({
                            'id': flow_file.stem,
                            'name': flow.get('name', flow_file.stem.replace('_', ' ').title()),
                            'purpose': flow.get('description', 'No description'),
                            'status': 'active',
                            'capabilities': _extract_capabilities(flow),
                            'icon': _get_agent_icon(flow_file.stem)
                        })
                except Exception as e:
                    logger.error(f"Error loading flow {flow_file}: {e}")
        
        return agents
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return []


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    try:
        flows_dir = Path(__file__).parent.parent / "langflow" / "flows"
        workflows_dir = Path(__file__).parent.parent / "n8n" / "workflows"
        
        # Delete Langflow flow
        flow_file = flows_dir / f"{agent_id}.json"
        if flow_file.exists():
            flow_file.unlink()
        
        # Delete n8n workflow
        workflow_file = workflows_dir / f"{agent_id}_trigger.json"
        if workflow_file.exists():
            workflow_file.unlink()
        
        return {"status": "deleted", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows")
async def list_workflows():
    """List all n8n workflows"""
    try:
        workflows_dir = Path(__file__).parent.parent / "n8n" / "workflows"
        workflows = []
        
        if workflows_dir.exists():
            for workflow_file in workflows_dir.glob("*.json"):
                try:
                    with open(workflow_file, 'r') as f:
                        workflow = json.load(f)
                        workflows.append({
                            'id': workflow.get('id', workflow_file.stem),
                            'name': workflow.get('name', workflow_file.stem.replace('_', ' ').title()),
                            'description': _extract_workflow_description(workflow),
                            'trigger': _extract_trigger_type(workflow),
                            'active': workflow.get('active', False)
                        })
                except Exception as e:
                    logger.error(f"Error loading workflow {workflow_file}: {e}")
        
        return workflows
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        return []


def _extract_capabilities(flow: dict) -> list:
    """Extract capabilities from Langflow flow"""
    capabilities = []
    
    # Look for system message that might contain capabilities
    for node in flow.get('nodes', []):
        if node.get('type') == 'ChatOllama':
            system_msg = node.get('data', {}).get('system_message', '')
            if 'capabilities include:' in system_msg.lower():
                caps_text = system_msg.split('capabilities include:')[1]
                capabilities = [c.strip() for c in caps_text.replace('.', '').split(',')]
    
    # Default capabilities if none found
    if not capabilities:
        capabilities = ['task_execution', 'llm_reasoning', 'memory_access']
    
    return capabilities[:5]  # Limit to 5


def _get_agent_icon(agent_id: str) -> str:
    """Get icon for agent type"""
    icons = {
        'boot_hardening': '🛡️',
        'daily_brief': '📊',
        'focus_guardrails': '🎯',
        'security': '🔒',
        'productivity': '⚡',
        'research': '🔍',
        'content': '🎨'
    }
    
    for key, icon in icons.items():
        if key in agent_id.lower():
            return icon
    
    return '🤖'


def _extract_workflow_description(workflow: dict) -> str:
    """Extract description from n8n workflow"""
    # Get first few nodes and create description
    nodes = workflow.get('nodes', [])
    if nodes:
        triggers = [n for n in nodes if 'trigger' in n.get('type', '').lower()]
        if triggers:
            return f"Triggered workflow with {len(nodes)} steps"
    return "Automated workflow"


def _extract_trigger_type(workflow: dict) -> str:
    """Extract trigger type from n8n workflow"""
    nodes = workflow.get('nodes', [])
    for node in nodes:
        node_type = node.get('type', '').lower()
        if 'schedule' in node_type:
            params = node.get('parameters', {})
            rule = params.get('rule', {})
            interval = rule.get('interval', [{}])[0] if rule.get('interval') else {}
            cron = interval.get('expression', 'Schedule')
            return f"Cron: {cron}"
        elif 'webhook' in node_type:
            return "Webhook"
        elif 'manual' in node_type:
            return "Manual"
    return "Unknown"


# ============================================================================
# INTAKE AGENT - Natural Language Agent Team Creation
# ============================================================================

@app.get("/intake-agent", response_class=HTMLResponse)
async def intake_agent_ui():
    """Serve the standalone intake agent UI (legacy)"""
    ui_file = Path(__file__).parent / "intake_agent_ui.html"
    with open(ui_file, 'r') as f:
        return HTMLResponse(content=f.read())


@app.post("/api/intake-agent/chat")
async def intake_agent_chat(request: Request):
    """
    Handle intake agent conversation.
    Processes natural language input and creates custom agent teams.
    """
    try:
        # Import the intake agent
        import sys
        from pathlib import Path
        
        # Add agents directory to path
        agents_dir = Path(__file__).parent.parent / "agents"
        sys.path.insert(0, str(agents_dir))
        
        from intake_agent.intake_agent import IntakeAgent
        
        # Parse request
        data = await request.json()
        message = data.get('message', '')
        context = data.get('context', {'stage': 'initial'})
        history = data.get('history', [])
        
        # Process with intake agent
        agent = IntakeAgent()
        result = agent.process_message(message, context, history)
        
        return result
        
    except Exception as e:
        logger.error(f"Intake agent error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'response': f'I encountered an error: {str(e)}. Please try again.',
            'context': context,
            'isHtml': False
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("WEB_PORT", "8000"))
    host = os.getenv("WEB_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
