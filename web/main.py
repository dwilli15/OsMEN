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
from .status import get_system_status, get_agent_health, get_service_health, get_memory_system_status
from .agent_config import AgentConfigManager
from .digest import DigestGenerator

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


# ============================================================================
# Calendar Integration Endpoints (Agent Alpha - Task A1.1)
# ============================================================================

@app.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request, user: dict = Depends(check_auth)):
    """Calendar management page."""
    # Import calendar manager
    import sys
    sys.path.insert(0, str(BASE_DIR.parent / "integrations" / "calendar"))
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
    sys.path.insert(0, str(BASE_DIR.parent / "integrations" / "calendar"))
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
    sys.path.insert(0, str(BASE_DIR.parent / "integrations" / "calendar"))
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
    sys.path.insert(0, str(BASE_DIR.parent / "integrations" / "calendar"))
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
    sys.path.insert(0, str(BASE_DIR.parent / "integrations" / "calendar"))
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
    sys.path.insert(0, str(BASE_DIR.parent / "integrations" / "calendar"))
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
    sys.path.insert(0, str(BASE_DIR.parent / "integrations" / "calendar"))
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
    
    sys.path.insert(0, str(BASE_DIR.parent / "parsers" / "syllabus"))
    from syllabus_parser import SyllabusParser
    
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
        
        add_log("INFO", f"Syllabus uploaded and parsed: {file.filename}", "syllabus")
        
        return {
            "success": True,
            "preview_id": preview_id,
            "course": normalized_data.get('course', {}),
            "event_count": normalized_data.get('metadata', {}).get('total_events', 0)
        }
    
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


# ============================================================================
# Scheduling Engine Integration (Agent Alpha - Task A1.6)
# ============================================================================

@app.get("/api/schedule/generate")
async def generate_schedule(request: Request, user: dict = Depends(check_auth)):
    """Generate optimal schedule from calendar events."""
    import sys
    sys.path.insert(0, str(BASE_DIR.parent / "scheduling"))
    from schedule_optimizer import ScheduleOptimizer
    from priority_ranker import PriorityRanker
    
    try:
        # Get calendar events
        sys.path.insert(0, str(BASE_DIR.parent / "integrations" / "calendar"))
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
    import sys
    sys.path.insert(0, str(BASE_DIR.parent / "reminders"))
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
    import sys
    sys.path.insert(0, str(BASE_DIR.parent / "reminders"))
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
    import sys
    sys.path.insert(0, str(BASE_DIR.parent / "reminders"))
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
    import sys
    sys.path.insert(0, str(BASE_DIR.parent / "health_integration"))
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
    import sys
    sys.path.insert(0, str(BASE_DIR.parent / "health_integration"))
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


@app.logs/stream")
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
