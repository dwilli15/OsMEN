"""FastAPI Web Dashboard for OsMEN

Main application entry point providing no-code interface for system management.
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .auth import get_current_user, login_user, logout_user, check_auth
from .status import get_system_status, get_agent_health, get_service_health

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
