#!/usr/bin/env python3
"""
OsMEN Web Dashboard
Real-time monitoring and control interface for the OsMEN system
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OsMEN Dashboard",
    description="Real-time monitoring and control for OsMEN agent orchestration platform",
    version="1.4.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Setup static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Import monitoring modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from tools.productivity.productivity_monitor import ProductivityMonitor
from agents.innovation_agent.innovation_agent import InnovationAgent


class DashboardService:
    """Service for dashboard data aggregation"""
    
    def __init__(self):
        self.productivity = ProductivityMonitor()
        self.innovation = InnovationAgent()
        self.repo_path = Path(__file__).parent.parent
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "status": "operational",
            "version": "1.4.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": {
                "boot_hardening": {"status": "active", "last_run": None},
                "daily_brief": {"status": "active", "last_run": None},
                "focus_guardrails": {"status": "active", "last_run": None},
                "innovation_agent": {"status": "active", "last_run": None},
            },
            "services": {
                "mcp_server": {"status": "unknown", "tools": 16},
                "agent_gateway": {"status": "unknown"},
                "productivity_monitor": {"status": "active"},
            }
        }
    
    def get_productivity_metrics(self) -> Dict[str, Any]:
        """Get productivity metrics"""
        try:
            daily = self.productivity.get_daily_summary()
            weekly = self.productivity.get_weekly_trends()
            
            return {
                "daily": daily,
                "weekly": weekly,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error getting productivity metrics: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_innovation_backlog(self) -> Dict[str, Any]:
        """Get innovation backlog"""
        try:
            backlog_path = self.repo_path / "docs" / "INNOVATION_BACKLOG.md"
            if backlog_path.exists():
                with open(backlog_path) as f:
                    content = f.read()
                
                # Parse markdown to extract innovations (simple parsing)
                innovations = []
                lines = content.split('\n')
                current_innovation = None
                
                for line in lines:
                    if line.startswith('### '):
                        if current_innovation:
                            innovations.append(current_innovation)
                        current_innovation = {
                            "name": line.replace('### ', '').strip(),
                            "details": []
                        }
                    elif current_innovation and line.strip():
                        current_innovation["details"].append(line)
                
                if current_innovation:
                    innovations.append(current_innovation)
                
                return {
                    "status": "success",
                    "innovations": innovations[:10],  # Top 10
                    "total": len(innovations)
                }
            else:
                return {"status": "success", "innovations": [], "total": 0}
        except Exception as e:
            logger.error(f"Error getting innovation backlog: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_agent_logs(self, agent_name: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent agent logs"""
        # Placeholder - would read from actual log files
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": "innovation_agent",
                "level": "INFO",
                "message": "Weekly scan completed"
            }
        ]


# Initialize dashboard service
dashboard = DashboardService()


# WebSocket for real-time updates
active_connections: List[WebSocket] = []


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            data = {
                "type": "status_update",
                "data": dashboard.get_system_status(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await websocket.send_json(data)
            
            # Wait for any client messages
            message = await websocket.receive_text()
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)


# API Routes

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Dashboard home page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "OsMEN Dashboard"
    })


@app.get("/api/status")
async def get_status():
    """Get system status"""
    return dashboard.get_system_status()


@app.get("/api/productivity")
async def get_productivity():
    """Get productivity metrics"""
    return dashboard.get_productivity_metrics()


@app.get("/api/productivity/daily")
async def get_daily_productivity(date: Optional[str] = None):
    """Get daily productivity summary"""
    try:
        summary = dashboard.productivity.get_daily_summary(date)
        return {"status": "success", "data": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/productivity/weekly")
async def get_weekly_productivity():
    """Get weekly productivity trends"""
    try:
        trends = dashboard.productivity.get_weekly_trends()
        return {"status": "success", "data": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/innovations")
async def get_innovations():
    """Get innovation backlog"""
    return dashboard.get_innovation_backlog()


@app.get("/api/agents")
async def get_agents():
    """Get agent status"""
    status = dashboard.get_system_status()
    return {"status": "success", "agents": status["agents"]}


@app.get("/api/agents/{agent_name}/logs")
async def get_agent_logs(agent_name: str, limit: int = 50):
    """Get logs for specific agent"""
    logs = dashboard.get_agent_logs(agent_name, limit)
    return {"status": "success", "logs": logs}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.4.0"
    }


@app.post("/api/productivity/session/start")
async def start_session(session_type: str = "pomodoro", duration: int = 25):
    """Start a focus session"""
    try:
        result = dashboard.productivity.start_focus_session(session_type, duration)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/productivity/session/{session_id}/end")
async def end_session(
    session_id: int,
    productivity_score: int = 7,
    distractions: int = 0,
    notes: str = ""
):
    """End a focus session"""
    try:
        result = dashboard.productivity.end_focus_session(
            session_id, productivity_score, distractions, notes
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
async def get_config():
    """Get system configuration"""
    config_path = Path(__file__).parent.parent / ".copilot" / "memory.json"
    try:
        with open(config_path) as f:
            config = json.load(f)
        return {"status": "success", "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the dashboard
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8082,
        log_level="info"
    )
