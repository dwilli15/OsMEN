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


ViewerRole = Depends(role_required("viewer"))
OperatorRole = Depends(role_required("operator"))
AdminRole = Depends(role_required("admin"))



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
