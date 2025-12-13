#!/usr/bin/env python3
"""
OsMEN Web Dashboard - Main Application

FastAPI web interface for:
- Syllabus upload and parsing
- Calendar event preview and creation
- Task management dashboard
- Agent status monitoring
- Infrastructure admin hub (v1.3.0+)
"""

import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = Path("data/uploads")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    application = FastAPI(
        title="OsMEN Dashboard",
        description="Local-first agent orchestration for graduate school workflow automation",
        version="1.3.0",
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure directories exist
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Mount static files
    if STATIC_DIR.exists():
        application.mount(
            "/static", StaticFiles(directory=str(STATIC_DIR)), name="static"
        )

    return application


app = create_app()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ============================================================
# Pydantic Models
# ============================================================


class ParsedEvent(BaseModel):
    """Parsed event from syllabus"""

    id: str
    title: str
    date: Optional[str] = None
    type: str  # exam, assignment, class, deadline
    description: str = ""
    priority: str = "medium"
    course: Optional[str] = None


class CalendarEventCreate(BaseModel):
    """Event to create in calendar"""

    title: str
    date: str
    description: str = ""
    duration_minutes: int = 60
    reminder_days: int = 1


class SyllabusPreview(BaseModel):
    """Preview of parsed syllabus data"""

    session_id: str
    filename: str
    course_info: Dict[str, Any]
    events: List[ParsedEvent]
    total_events: int
    parsed_at: str


class CalendarCreateRequest(BaseModel):
    """Request to create calendar events"""

    session_id: str
    event_ids: List[str]  # IDs of events to create
    calendar_provider: str = "google"  # google, outlook


class AgentStatus(BaseModel):
    """Status of an agent"""

    name: str
    status: str  # operational, degraded, offline
    last_check: str
    capabilities: List[str]


# ============================================================
# In-Memory Session Storage
# ============================================================

# Store parsed syllabus data temporarily (session_id -> data)
syllabus_sessions: Dict[str, Dict[str, Any]] = {}


# ============================================================
# Routes - Main Pages
# ============================================================


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "OsMEN Dashboard", "version": "1.3.0"},
    )


@app.get("/syllabus", response_class=HTMLResponse)
async def syllabus_page(request: Request):
    """Syllabus upload and parsing page"""
    return templates.TemplateResponse(
        "syllabus.html", {"request": request, "title": "Syllabus Parser"}
    )


@app.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request):
    """Calendar management page"""
    return templates.TemplateResponse(
        "calendar.html", {"request": request, "title": "Calendar Manager"}
    )


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """Task management page"""
    return templates.TemplateResponse(
        "tasks.html", {"request": request, "title": "Task Manager"}
    )


@app.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    """Agent status page"""
    return templates.TemplateResponse(
        "agents.html", {"request": request, "title": "Agent Status"}
    )


# ============================================================
# Routes - API Endpoints
# ============================================================


@app.get("/api/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.3.0",
    }


@app.post("/api/syllabus/upload")
async def upload_syllabus(file: UploadFile = File(...)):
    """
    Upload and parse a syllabus file (PDF or DOCX).
    Returns parsed events and course information.
    """
    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".doc"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}",
        )

    # Save uploaded file
    session_id = str(uuid.uuid4())
    upload_path = UPLOAD_DIR / session_id
    upload_path.mkdir(parents=True, exist_ok=True)

    file_path = upload_path / file.filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Uploaded syllabus: {file.filename} -> {file_path}")

        # Parse the syllabus
        parsed_data = await parse_syllabus_file(str(file_path))

        # Store in session
        syllabus_sessions[session_id] = {
            "filename": file.filename,
            "file_path": str(file_path),
            "parsed_data": parsed_data,
            "created_at": datetime.now().isoformat(),
        }

        # Build response
        events = []
        for event in parsed_data.get("events", []) + parsed_data.get("assignments", []):
            events.append(
                ParsedEvent(
                    id=str(uuid.uuid4()),
                    title=event.get("title", "Untitled"),
                    date=event.get("date") or event.get("due_date"),
                    type=event.get("type", "event"),
                    description=event.get("description", ""),
                    priority=_calculate_priority(event),
                    course=parsed_data.get("course_info", {}).get("course_code"),
                )
            )

        # Store events with IDs for later retrieval
        syllabus_sessions[session_id]["events"] = [e.dict() for e in events]

        return SyllabusPreview(
            session_id=session_id,
            filename=file.filename,
            course_info=parsed_data.get("course_info", {}),
            events=events,
            total_events=len(events),
            parsed_at=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error processing syllabus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/syllabus/{session_id}")
async def get_syllabus_session(session_id: str):
    """Get parsed syllabus data by session ID"""
    if session_id not in syllabus_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = syllabus_sessions[session_id]
    events = [ParsedEvent(**e) for e in session.get("events", [])]

    return SyllabusPreview(
        session_id=session_id,
        filename=session["filename"],
        course_info=session["parsed_data"].get("course_info", {}),
        events=events,
        total_events=len(events),
        parsed_at=session["created_at"],
    )


@app.post("/api/calendar/create")
async def create_calendar_events(request: CalendarCreateRequest):
    """
    Create calendar events from parsed syllabus data.
    """
    if request.session_id not in syllabus_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = syllabus_sessions[request.session_id]
    events = session.get("events", [])

    # Filter to requested events
    selected_events = [e for e in events if e["id"] in request.event_ids]

    if not selected_events:
        raise HTTPException(status_code=400, detail="No valid events selected")

    # Try to create events via calendar manager
    try:
        results = await create_events_in_calendar(
            selected_events, provider=request.calendar_provider
        )

        return {
            "success": True,
            "created_count": results["created"],
            "failed_count": results["failed"],
            "events": results["details"],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Calendar creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar/status")
async def get_calendar_status():
    """Get calendar integration status"""
    google_configured = bool(os.getenv("GOOGLE_CREDENTIALS_PATH"))
    outlook_configured = bool(os.getenv("OUTLOOK_CLIENT_ID"))

    return {
        "google": {
            "available": google_configured,
            "status": "configured" if google_configured else "not_configured",
        },
        "outlook": {
            "available": outlook_configured,
            "status": "configured" if outlook_configured else "not_configured",
        },
    }


@app.get("/api/tasks")
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_today: bool = False,
):
    """Get tasks from personal assistant agent"""
    try:
        from agents.personal_assistant.personal_assistant_agent import (
            PersonalAssistantAgent,
        )

        agent = PersonalAssistantAgent()
        tasks = agent.get_tasks(status=status, priority=priority, due_today=due_today)
        return {"tasks": tasks, "total": len(tasks)}
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        return {"tasks": [], "total": 0, "error": str(e)}


@app.post("/api/tasks")
async def create_task(
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    due_date: Optional[str] = Form(None),
):
    """Create a new task"""
    try:
        from agents.personal_assistant.personal_assistant_agent import (
            PersonalAssistantAgent,
        )

        agent = PersonalAssistantAgent()
        task = agent.create_task(
            title=title, description=description, priority=priority, due_date=due_date
        )
        return {"success": True, "task": task}
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    agents = []

    # Check each agent
    agent_checks = [
        (
            "Boot Hardening",
            "agents.boot_hardening.boot_hardening_agent",
            "BootHardeningAgent",
        ),
        ("Daily Brief", "agents.daily_brief.daily_brief_agent", "DailyBriefAgent"),
        (
            "Focus Guardrails",
            "agents.focus_guardrails.focus_guardrails_agent",
            "FocusGuardrailsAgent",
        ),
        ("Librarian", "agents.librarian.librarian_agent", "LibrarianAgent"),
        (
            "Personal Assistant",
            "agents.personal_assistant.personal_assistant_agent",
            "PersonalAssistantAgent",
        ),
        ("OS Optimizer", "agents.os_optimizer.os_optimizer_agent", "OSOptimizerAgent"),
    ]

    for name, module_path, class_name in agent_checks:
        try:
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            agent = agent_class()

            # Try to get health/report
            if hasattr(agent, "get_health"):
                health = agent.get_health()
                status = health.get("status", "operational")
            elif hasattr(agent, "generate_librarian_report"):
                report = agent.generate_librarian_report()
                status = report.get("overall_status", "operational")
            else:
                status = "operational"

            capabilities = []
            if hasattr(agent, "__doc__") and agent.__doc__:
                capabilities = [agent.__doc__.split("\n")[0]]

            agents.append(
                AgentStatus(
                    name=name,
                    status=status,
                    last_check=datetime.now().isoformat(),
                    capabilities=capabilities,
                )
            )
        except Exception as e:
            logger.warning(f"Agent {name} check failed: {e}")
            agents.append(
                AgentStatus(
                    name=name,
                    status="offline",
                    last_check=datetime.now().isoformat(),
                    capabilities=[],
                )
            )

    return {"agents": [a.dict() for a in agents]}


@app.get("/api/daily-summary")
async def get_daily_summary():
    """Get daily summary from personal assistant"""
    try:
        from agents.personal_assistant.personal_assistant_agent import (
            PersonalAssistantAgent,
        )

        agent = PersonalAssistantAgent()
        summary = agent.get_daily_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting daily summary: {e}")
        return {"error": str(e)}


# ============================================================
# Routes - Admin Hub (Infrastructure Management)
# ============================================================


@app.get("/admin", response_class=HTMLResponse)
async def admin_hub_page(request: Request):
    """Admin dashboard hub - comprehensive infrastructure view"""
    return templates.TemplateResponse(
        "admin/hub.html",
        {"request": request, "title": "Admin Hub", "version": "1.3.0"},
    )


@app.get("/admin/infrastructure", response_class=HTMLResponse)
async def admin_infrastructure_page(request: Request):
    """Infrastructure visualization page"""
    return templates.TemplateResponse(
        "admin/infrastructure.html",
        {"request": request, "title": "Infrastructure", "version": "1.3.0"},
    )


@app.get("/admin/health", response_class=HTMLResponse)
async def admin_health_page(request: Request):
    """Health monitoring page"""
    return templates.TemplateResponse(
        "admin/health.html",
        {"request": request, "title": "Health Monitor", "version": "1.3.0"},
    )


@app.get("/admin/approvals", response_class=HTMLResponse)
async def admin_approvals_page(request: Request):
    """Approval queues page"""
    return templates.TemplateResponse(
        "admin/approvals.html",
        {"request": request, "title": "Approval Queues", "version": "1.3.0"},
    )


@app.get("/admin/obsidian", response_class=HTMLResponse)
async def admin_obsidian_page(request: Request):
    """Obsidian sync management page"""
    return templates.TemplateResponse(
        "admin/obsidian.html",
        {"request": request, "title": "Obsidian Sync", "version": "1.3.0"},
    )


@app.get("/admin/lifecycle", response_class=HTMLResponse)
async def admin_lifecycle_page(request: Request):
    """Lifecycle management page"""
    return templates.TemplateResponse(
        "admin/lifecycle.html",
        {"request": request, "title": "Lifecycle Management", "version": "1.3.0"},
    )


@app.get("/admin/flows", response_class=HTMLResponse)
async def admin_flows_page(request: Request):
    """Flows and workflows visualization page"""
    return templates.TemplateResponse(
        "admin/flows.html",
        {"request": request, "title": "Flows & Workflows", "version": "1.3.0"},
    )


# ============================================================
# API - Admin Hub Endpoints
# ============================================================


@app.get("/api/admin/flows")
async def get_flows_and_workflows():
    """Get all Langflow flows and n8n workflows.

    Refactored from complexity 23 to ~10 (PHOENIX Protocol compliance).
    """
    # Scan Langflow flows
    langflow_flows = await _scan_langflow_flows()

    # Scan n8n workflows
    n8n_workflows = await _scan_n8n_workflows()

    # Get pipeline registry info
    pipeline_registry = await _get_pipeline_registry(langflow_flows, n8n_workflows)

    return {
        "langflow": langflow_flows,
        "n8n": n8n_workflows,
        "registry": pipeline_registry,
    }


async def _scan_langflow_flows() -> List[Dict[str, Any]]:
    """Scan Langflow flows directory."""
    langflow_flows = []
    langflow_dir = PROJECT_DIR / "langflow" / "flows"

    if not langflow_dir.exists():
        return langflow_flows

    for flow_file in langflow_dir.glob("*.json"):
        try:
            flow_info = _parse_langflow_flow(flow_file)
            if flow_info:
                langflow_flows.append(flow_info)
        except Exception as e:
            logger.warning(f"Failed to parse flow {flow_file}: {e}")

    return langflow_flows


def _parse_langflow_flow(flow_file: Path) -> Optional[Dict[str, Any]]:
    """Parse a single Langflow flow file."""
    with open(flow_file, "r") as f:
        flow_data = json.load(f)

    name = flow_file.stem
    display_name = name.replace("_", " ").title()

    # Count nodes if structure allows
    node_count = 0
    if isinstance(flow_data, dict):
        if "nodes" in flow_data:
            node_count = len(flow_data.get("nodes", []))
        elif "data" in flow_data and "nodes" in flow_data.get("data", {}):
            node_count = len(flow_data.get("data", {}).get("nodes", []))

    # Determine type
    flow_type = "specialist"
    if "coordinator" in name:
        flow_type = "coordinator"
    elif "assistant" in name:
        flow_type = "assistant"

    return {
        "name": name,
        "display_name": display_name,
        "description": flow_data.get("description", ""),
        "node_count": node_count,
        "type": flow_type,
        "file": str(flow_file.relative_to(PROJECT_DIR)),
    }


async def _scan_n8n_workflows() -> List[Dict[str, Any]]:
    """Scan n8n workflows directory."""
    n8n_workflows = []
    n8n_dir = PROJECT_DIR / "n8n" / "workflows"

    if not n8n_dir.exists():
        return n8n_workflows

    for workflow_file in n8n_dir.glob("*.json"):
        try:
            workflow_info = _parse_n8n_workflow(workflow_file)
            if workflow_info:
                n8n_workflows.append(workflow_info)
        except Exception as e:
            logger.warning(f"Failed to parse workflow {workflow_file}: {e}")

    return n8n_workflows


def _parse_n8n_workflow(workflow_file: Path) -> Optional[Dict[str, Any]]:
    """Parse a single n8n workflow file."""
    with open(workflow_file, "r") as f:
        workflow_data = json.load(f)

    name = workflow_file.stem
    display_name = name.replace("_", " ").title()

    nodes = workflow_data.get("nodes", [])
    node_count = len(nodes)

    # Determine trigger type
    trigger_type = "manual"
    for node in nodes:
        node_type = node.get("type", "").lower()
        if "cron" in node_type or "schedule" in node_type:
            trigger_type = "scheduled"
            break
        elif "webhook" in node_type:
            trigger_type = "webhook"
            break

    return {
        "name": name,
        "display_name": display_name,
        "description": workflow_data.get("description", ""),
        "node_count": node_count,
        "trigger_type": trigger_type,
        "file": str(workflow_file.relative_to(PROJECT_DIR)),
    }


async def _get_pipeline_registry(
    langflow_flows: List[Dict[str, Any]], n8n_workflows: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Get pipeline registry info and mark registered flows/workflows."""
    pipeline_registry = {}

    try:
        from agents.infrastructure.infrastructure_agent import InfrastructureAgent

        agent = InfrastructureAgent()
        summary = agent.get_pipeline_summary()

        pipeline_registry = {
            "total": summary["total"],
            "native_count": summary["native"]["count"],
            "langflow_count": summary["langflow"]["count"],
            "n8n_count": summary["n8n"]["count"],
            "registered_langflow": summary["langflow"]["flows"],
            "registered_n8n": summary["n8n"]["workflows"],
        }

        # Mark flows/workflows as registered
        for flow in langflow_flows:
            flow["registered"] = (
                f"langflow_{flow['name']}" in summary["langflow"]["flows"]
            )

        for workflow in n8n_workflows:
            workflow["registered"] = (
                f"n8n_{workflow['name']}" in summary["n8n"]["workflows"]
            )

    except ImportError:
        logger.warning("Infrastructure agent not available for pipeline registry")
    except Exception as e:
        logger.warning(f"Error getting pipeline registry: {e}")

    return pipeline_registry


@app.get("/api/admin/infrastructure/status")
async def get_infrastructure_status():
    """Get comprehensive infrastructure status"""
    try:
        from agents.infrastructure.infrastructure_agent import InfrastructureAgent

        agent = InfrastructureAgent()
        return agent.get_status()
    except ImportError:
        return {"error": "Infrastructure agent not available"}
    except Exception as e:
        logger.error(f"Error getting infrastructure status: {e}")
        return {"error": str(e)}


@app.get("/api/admin/infrastructure/graph")
async def get_infrastructure_graph():
    """Get the full connection graph for visualization"""
    try:
        from agents.infrastructure.infrastructure_agent import InfrastructureAgent

        agent = InfrastructureAgent()
        return agent.get_full_graph()
    except ImportError:
        return {"error": "Infrastructure agent not available"}
    except Exception as e:
        logger.error(f"Error getting infrastructure graph: {e}")
        return {"error": str(e)}


@app.get("/api/admin/health/status")
async def get_health_status():
    """Get health status of all nodes"""
    try:
        from agents.health_monitor.health_monitor_agent import HealthMonitorAgent

        agent = HealthMonitorAgent()
        return agent.check_all_nodes()
    except ImportError:
        return {"error": "Health monitor agent not available"}
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return {"error": str(e)}


@app.get("/api/admin/health/history")
async def get_health_history(hours: int = 24):
    """Get health check history"""
    try:
        # Read from health logs
        log_path = PROJECT_DIR / "logs" / "health_checks.jsonl"
        history = []

        if log_path.exists():
            import time

            cutoff = time.time() - (hours * 3600)

            with open(log_path, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("timestamp", 0) > cutoff:
                            history.append(record)
                    except json.JSONDecodeError:
                        continue

        return {"history": history[-100:], "total": len(history)}
    except Exception as e:
        logger.error(f"Error getting health history: {e}")
        return {"error": str(e)}


@app.post("/api/admin/health/restart/{node_id}")
async def restart_node(node_id: str):
    """Restart a specific service/node"""
    try:
        from agents.health_monitor.health_monitor_agent import HealthMonitorAgent

        agent = HealthMonitorAgent()
        result = agent.restart_service(node_id)
        return result
    except ImportError:
        return {"error": "Health monitor agent not available"}
    except Exception as e:
        logger.error(f"Error restarting node {node_id}: {e}")
        return {"error": str(e)}


@app.get("/api/admin/context/stats")
async def get_context_injection_stats():
    """Get context injection statistics"""
    try:
        from infrastructure.context_injector import get_injector

        injector = get_injector()
        return injector.get_injection_stats()
    except ImportError:
        return {"error": "Context injector not available"}
    except Exception as e:
        logger.error(f"Error getting context stats: {e}")
        return {"error": str(e)}


@app.get("/api/admin/approvals/pending")
async def get_pending_approvals():
    """Get all pending approvals across queues"""
    queues = {"knowledge_writes": [], "destructive_fixes": [], "obsidian_exports": []}

    # Load from queue files
    queue_base = PROJECT_DIR / "infrastructure" / "queues"

    for queue_name in queues.keys():
        queue_file = queue_base / f"{queue_name}.json"
        if queue_file.exists():
            try:
                with open(queue_file, "r") as f:
                    queues[queue_name] = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load queue {queue_name}: {e}")

    return {
        "queues": queues,
        "total_pending": sum(len(q) for q in queues.values()),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/admin/approvals/approve/{queue}/{item_id}")
async def approve_item(queue: str, item_id: str):
    """Approve a pending item"""
    queue_file = PROJECT_DIR / "infrastructure" / "queues" / f"{queue}.json"

    if not queue_file.exists():
        raise HTTPException(status_code=404, detail="Queue not found")

    try:
        with open(queue_file, "r") as f:
            items = json.load(f)

        # Find and remove the item
        approved_item = None
        for i, item in enumerate(items):
            if item.get("id") == item_id:
                approved_item = items.pop(i)
                break

        if not approved_item:
            raise HTTPException(status_code=404, detail="Item not found in queue")

        # Save updated queue
        with open(queue_file, "w") as f:
            json.dump(items, f, indent=2)

        # Execute the approved action
        # (This would call the appropriate handler based on queue type)

        return {
            "success": True,
            "approved": approved_item,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error approving item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/approvals/reject/{queue}/{item_id}")
async def reject_item(queue: str, item_id: str, reason: str = Form("")):
    """Reject a pending item"""
    queue_file = PROJECT_DIR / "infrastructure" / "queues" / f"{queue}.json"

    if not queue_file.exists():
        raise HTTPException(status_code=404, detail="Queue not found")

    try:
        with open(queue_file, "r") as f:
            items = json.load(f)

        # Find and remove the item
        rejected_item = None
        for i, item in enumerate(items):
            if item.get("id") == item_id:
                rejected_item = items.pop(i)
                break

        if not rejected_item:
            raise HTTPException(status_code=404, detail="Item not found in queue")

        # Save updated queue
        with open(queue_file, "w") as f:
            json.dump(items, f, indent=2)

        # Log rejection
        rejected_item["rejected_at"] = datetime.now().isoformat()
        rejected_item["rejection_reason"] = reason

        rejected_log = PROJECT_DIR / "logs" / "rejected_approvals.jsonl"
        with open(rejected_log, "a") as f:
            f.write(json.dumps(rejected_item) + "\n")

        return {
            "success": True,
            "rejected": rejected_item,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error rejecting item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/obsidian/status")
async def get_obsidian_status():
    """Get Obsidian sync status"""
    try:
        from tools.obsidian.obsidian_sync_watcher import get_watcher

        watcher = get_watcher()
        return watcher.get_status()
    except ImportError:
        return {"error": "Obsidian watcher not available"}
    except Exception as e:
        logger.error(f"Error getting Obsidian status: {e}")
        return {"error": str(e)}


@app.get("/api/admin/obsidian/readable")
async def get_readable_notes():
    """Get list of readable Obsidian notes"""
    try:
        from tools.obsidian.obsidian_sync_watcher import get_watcher

        watcher = get_watcher()
        return {"notes": watcher.list_readable_notes()}
    except ImportError:
        return {"error": "Obsidian watcher not available"}
    except Exception as e:
        logger.error(f"Error getting readable notes: {e}")
        return {"error": str(e)}


@app.post("/api/admin/obsidian/sync")
async def trigger_obsidian_sync():
    """Manually trigger Obsidian sync"""
    try:
        from tools.obsidian.obsidian_sync_watcher import get_watcher

        watcher = get_watcher()
        changes = watcher.detect_changes()
        result = watcher.sync_to_knowledge(changes)

        return {
            "success": True,
            "changes_detected": len(changes),
            "sync_result": result,
            "timestamp": datetime.now().isoformat(),
        }
    except ImportError:
        return {"error": "Obsidian watcher not available"}
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        return {"error": str(e)}


@app.get("/api/admin/workspace/lifecycle")
async def get_workspace_lifecycle_status():
    """Get workspace file lifecycle status"""
    workspace_dirs = {
        "incoming": PROJECT_DIR / "workspace" / "incoming",
        "staging": PROJECT_DIR / "workspace" / "staging",
        "pending_review": PROJECT_DIR / "workspace" / "pending_review",
    }

    status = {}

    for name, path in workspace_dirs.items():
        if path.exists():
            files = list(path.rglob("*"))
            file_count = len([f for f in files if f.is_file()])

            # Get file ages
            old_files = []
            import time

            now = time.time()

            for f in files:
                if f.is_file():
                    age_days = (now - f.stat().st_mtime) / 86400
                    if age_days > 10:
                        old_files.append(
                            {
                                "path": str(f.relative_to(PROJECT_DIR)),
                                "age_days": round(age_days, 1),
                            }
                        )

            status[name] = {
                "file_count": file_count,
                "old_files": old_files[:10],  # Top 10 oldest
                "total_old": len(old_files),
            }
        else:
            status[name] = {"file_count": 0, "old_files": [], "total_old": 0}

    return status


# ============================================================
# Routes - Per-Agent Dashboards
# ============================================================


@app.get("/admin/agent/{agent_id}", response_class=HTMLResponse)
async def agent_dashboard_page(request: Request, agent_id: str):
    """Per-agent dashboard page"""
    return templates.TemplateResponse(
        "admin/agent_dashboard.html",
        {
            "request": request,
            "title": f"Agent: {agent_id}",
            "agent_id": agent_id,
            "version": "1.3.0",
        },
    )


@app.get("/api/admin/agent/{agent_id}/details")
async def get_agent_details(agent_id: str):
    """Get detailed information about a specific agent"""
    try:
        from agents.infrastructure.infrastructure_agent import InfrastructureAgent

        infra = InfrastructureAgent()

        # Get agent info from infrastructure
        agent_info = None
        for agent in infra.agents.values():
            if agent.agent_id == agent_id:
                agent_info = {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "uses_tools": agent.uses_tools,
                    "uses_nodes": agent.uses_nodes,
                    "provides": agent.provides,
                    "consumes": agent.consumes,
                    "context_requirements": agent.context_requirements,
                }
                break

        if not agent_info:
            return {"error": f"Agent {agent_id} not found in registry"}

        # Get recent context injections for this agent
        context_injections = []
        audit_log = PROJECT_DIR / "logs" / "context_injections.jsonl"
        if audit_log.exists():
            with open(audit_log, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("agent_id") == agent_id:
                            context_injections.append(record)
                    except json.JSONDecodeError:
                        continue
            context_injections = context_injections[-20:]  # Last 20

        # Get recent outcomes
        outcomes = []
        outcome_log = PROJECT_DIR / "logs" / "agent_outcomes.jsonl"
        if outcome_log.exists():
            with open(outcome_log, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("agent_id") == agent_id:
                            outcomes.append(record)
                    except json.JSONDecodeError:
                        continue
            outcomes = outcomes[-20:]

        return {
            "info": agent_info,
            "context_injections": context_injections,
            "outcomes": outcomes,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting agent details: {e}")
        return {"error": str(e)}


@app.get("/api/admin/agent/{agent_id}/context")
async def get_agent_context(agent_id: str, task: str = None):
    """Generate context for an agent (preview)"""
    try:
        from infrastructure.context_injector import inject_context

        context = inject_context(agent_id, task)
        return context
    except Exception as e:
        logger.error(f"Error generating context: {e}")
        return {"error": str(e)}


@app.get("/api/admin/agents/list")
async def list_all_agents():
    """List all registered agents with basic info"""
    try:
        from agents.infrastructure.infrastructure_agent import InfrastructureAgent

        infra = InfrastructureAgent()

        agents = []
        for agent in infra.agents.values():
            agents.append(
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "tools_count": len(agent.uses_tools),
                    "nodes_count": len(agent.uses_nodes),
                }
            )

        return {"agents": agents}
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return {"error": str(e)}


# ============================================================
# Helper Functions
# ============================================================


async def parse_syllabus_file(file_path: str) -> Dict[str, Any]:
    """Parse syllabus file using the appropriate parser"""
    try:
        from parsers.syllabus.syllabus_parser import SyllabusParser

        parser = SyllabusParser()
        return parser.parse(file_path)
    except ImportError:
        logger.warning("SyllabusParser not available, using fallback")
        return _fallback_parse(file_path)
    except Exception as e:
        logger.error(f"Parser error: {e}")
        return _fallback_parse(file_path)


def _fallback_parse(file_path: str) -> Dict[str, Any]:
    """Fallback parsing when main parser fails"""
    return {
        "course_info": {
            "course_code": "UNKNOWN",
            "course_name": Path(file_path).stem,
            "instructor": None,
            "semester": None,
        },
        "events": [],
        "assignments": [],
        "error": "Parser not available - please install PyPDF2 and python-docx",
    }


def _calculate_priority(event: Dict[str, Any]) -> str:
    """Calculate event priority based on type and content"""
    event_type = event.get("type", "").lower()
    title = event.get("title", "").lower()

    if "final" in title or event_type == "final":
        return "critical"
    elif "exam" in title or "midterm" in title or event_type == "exam":
        return "high"
    elif "project" in title or "paper" in title:
        return "high"
    elif "assignment" in title or "homework" in title:
        return "medium"
    else:
        return "low"


async def create_events_in_calendar(
    events: List[Dict[str, Any]], provider: str = "google"
) -> Dict[str, Any]:
    """Create events in calendar using calendar manager"""
    results = {"created": 0, "failed": 0, "details": []}

    try:
        from integrations.calendars.calendar_manager import CalendarManager

        manager = CalendarManager()

        # Check if provider is configured
        status = manager.get_status()
        if provider not in status.get("configured_providers", []):
            # Try to initialize the provider
            if provider == "google":
                manager.add_google_calendar()
            elif provider == "outlook":
                # Outlook requires token - would need OAuth flow
                pass

        for event in events:
            try:
                # Convert to calendar format
                calendar_event = {
                    "title": event.get("title", "Untitled"),
                    "date": event.get("date"),
                    "description": event.get("description", ""),
                    "reminder": {
                        "enabled": True,
                        "advance_days": 1 if event.get("priority") == "low" else 3,
                    },
                }

                result = manager.create_event(calendar_event, provider=provider)

                if result:
                    results["created"] += 1
                    results["details"].append(
                        {
                            "event_id": event.get("id"),
                            "title": event.get("title"),
                            "status": "created",
                            "calendar_id": result.get("id"),
                        }
                    )
                else:
                    results["failed"] += 1
                    results["details"].append(
                        {
                            "event_id": event.get("id"),
                            "title": event.get("title"),
                            "status": "failed",
                            "error": "Calendar API returned None",
                        }
                    )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(
                    {
                        "event_id": event.get("id"),
                        "title": event.get("title"),
                        "status": "failed",
                        "error": str(e),
                    }
                )

    except ImportError as e:
        logger.error(f"Calendar manager not available: {e}")
        results["failed"] = len(events)
        for event in events:
            results["details"].append(
                {
                    "event_id": event.get("id"),
                    "title": event.get("title"),
                    "status": "failed",
                    "error": "Calendar manager not available",
                }
            )

    return results


# ============================================================
# Routes - Lifecycle Management API
# ============================================================


@app.get("/api/admin/lifecycle/status")
async def get_lifecycle_status():
    """Get comprehensive lifecycle status"""
    try:
        import sys

        sys.path.insert(0, str(PROJECT_DIR / "scripts" / "automation"))
        from lifecycle_automation import WorkspaceLifecycleManager

        manager = WorkspaceLifecycleManager(base_path=PROJECT_DIR)
        return manager.get_status()
    except ImportError:
        return {"error": "Lifecycle manager not available"}
    except Exception as e:
        logger.error(f"Error getting lifecycle status: {e}")
        return {"error": str(e)}


@app.get("/api/admin/lifecycle/scan")
async def scan_workspace_files():
    """Scan workspace and return file details"""
    try:
        import sys

        sys.path.insert(0, str(PROJECT_DIR / "scripts" / "automation"))
        from lifecycle_automation import WorkspaceLifecycleManager

        manager = WorkspaceLifecycleManager(base_path=PROJECT_DIR)
        workspace = manager.scan_workspace()

        # Convert FileInfo objects to dicts
        result = {}
        for location, files in workspace.items():
            result[location] = [
                {
                    "path": f.relative_path,
                    "size_bytes": f.size_bytes,
                    "age_days": round(f.age_days, 1),
                    "modified_at": f.modified_at.isoformat(),
                }
                for f in files
            ]

        return result
    except ImportError:
        return {"error": "Lifecycle manager not available"}
    except Exception as e:
        logger.error(f"Error scanning workspace: {e}")
        return {"error": str(e)}


@app.get("/api/admin/lifecycle/expired")
async def get_expired_files():
    """Get files that have exceeded their age threshold"""
    try:
        import sys

        sys.path.insert(0, str(PROJECT_DIR / "scripts" / "automation"))
        from lifecycle_automation import WorkspaceLifecycleManager

        manager = WorkspaceLifecycleManager(base_path=PROJECT_DIR)
        expired = manager.get_expired_files()

        result = {}
        for location, files in expired.items():
            result[location] = [
                {
                    "path": f.relative_path,
                    "size_bytes": f.size_bytes,
                    "age_days": round(f.age_days, 1),
                    "location": f.location,
                }
                for f in files
            ]

        return result
    except ImportError:
        return {"error": "Lifecycle manager not available"}
    except Exception as e:
        logger.error(f"Error getting expired files: {e}")
        return {"error": str(e)}


@app.post("/api/admin/lifecycle/run-weekly")
async def run_weekly_review():
    """Trigger weekly review manually"""
    try:
        import sys

        sys.path.insert(0, str(PROJECT_DIR / "scripts" / "automation"))
        from lifecycle_automation import WorkspaceLifecycleManager

        manager = WorkspaceLifecycleManager(base_path=PROJECT_DIR)
        summary = manager.run_weekly_review()

        return summary
    except ImportError:
        return {"error": "Lifecycle manager not available"}
    except Exception as e:
        logger.error(f"Error running weekly review: {e}")
        return {"error": str(e)}


@app.post("/api/admin/lifecycle/run-daily")
async def run_daily_cleanup():
    """Trigger daily cleanup manually"""
    try:
        import sys

        sys.path.insert(0, str(PROJECT_DIR / "scripts" / "automation"))
        from lifecycle_automation import WorkspaceLifecycleManager

        manager = WorkspaceLifecycleManager(base_path=PROJECT_DIR)
        summary = manager.run_daily_cleanup()

        return summary
    except ImportError:
        return {"error": "Lifecycle manager not available"}
    except Exception as e:
        logger.error(f"Error running daily cleanup: {e}")
        return {"error": str(e)}


@app.get("/api/admin/archive/prompts")
async def get_archive_prompts():
    """Get pending archive prompts"""
    try:
        import sys

        sys.path.insert(0, str(PROJECT_DIR / "scripts" / "automation"))
        from archive_manager import ArchiveManager

        manager = ArchiveManager(base_path=PROJECT_DIR)
        return manager.get_pending_prompts()
    except ImportError:
        return {"error": "Archive manager not available"}
    except Exception as e:
        logger.error(f"Error getting archive prompts: {e}")
        return {"error": str(e)}


@app.post("/api/admin/archive/approve/{prompt_id}")
async def approve_archive(prompt_id: str):
    """Approve an archive prompt"""
    try:
        import sys

        sys.path.insert(0, str(PROJECT_DIR / "scripts" / "automation"))
        from archive_manager import ArchiveManager

        manager = ArchiveManager(base_path=PROJECT_DIR)
        return manager.approve_prompt(prompt_id)
    except ImportError:
        return {"error": "Archive manager not available"}
    except Exception as e:
        logger.error(f"Error approving archive: {e}")
        return {"error": str(e)}


@app.post("/api/admin/archive/reject/{prompt_id}")
async def reject_archive(prompt_id: str):
    """Reject an archive prompt"""
    try:
        import sys

        sys.path.insert(0, str(PROJECT_DIR / "scripts" / "automation"))
        from archive_manager import ArchiveManager

        manager = ArchiveManager(base_path=PROJECT_DIR)
        if manager.reject_prompt(prompt_id):
            return {"success": True}
        return {"error": "Prompt not found"}
    except ImportError:
        return {"error": "Archive manager not available"}
    except Exception as e:
        logger.error(f"Error rejecting archive: {e}")
        return {"error": str(e)}


@app.get("/api/admin/archive/browse")
async def browse_archive():
    """Browse archive contents"""
    try:
        import sys

        sys.path.insert(0, str(PROJECT_DIR / "scripts" / "automation"))
        from archive_manager import ArchiveManager

        manager = ArchiveManager(base_path=PROJECT_DIR)
        return manager.browse_archive()
    except ImportError:
        return {"error": "Archive manager not available"}
    except Exception as e:
        logger.error(f"Error browsing archive: {e}")
        return {"error": str(e)}


@app.get("/api/admin/schedules")
async def get_scheduled_tasks():
    """Get scheduled task configuration"""
    try:
        schedules_file = (
            PROJECT_DIR / "infrastructure" / "schedules" / "scheduled_tasks.json"
        )
        if schedules_file.exists():
            with open(schedules_file, "r") as f:
                return json.load(f)
        return {"scheduled_tasks": []}
    except Exception as e:
        logger.error(f"Error getting schedules: {e}")
        return {"error": str(e)}


# ============================================================
# Startup/Shutdown Events
# ============================================================


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("OsMEN Web Dashboard starting up...")

    # Ensure directories exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"Templates directory: {TEMPLATES_DIR}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("OsMEN Web Dashboard shutting down...")


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host="0.0.0.0", port=8000)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host="0.0.0.0", port=8000)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
