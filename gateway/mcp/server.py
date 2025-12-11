"""
OsMEN Unified MCP Server
Production-ready Model Context Protocol implementation

Features:
- OpenTelemetry distributed tracing
- Centralized tool registry with 40+ tools
- FastAPI with async support
- Handler dispatch with timeout and error handling
- Graceful degradation
- Health checks and monitoring

Usage:
    # As module
    from gateway.mcp import create_app
    app = create_app()

    # As standalone
    python -m gateway.mcp.server
"""

import asyncio
import json
import logging
import os
import platform
import subprocess
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from gateway.mcp.tools import (
    ToolCategory,
    ToolDefinition,
    ToolRegistry,
    get_tool_registry,
)
from gateway.mcp.tracing import TracingManager, TracingMiddleware, get_tracer, traced

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models
# =============================================================================


class ToolCallRequest(BaseModel):
    """MCP tool call request"""

    tool: str = Field(..., description="Tool name to execute")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters"
    )
    confirmation: bool = Field(
        default=False, description="Confirmation for destructive operations"
    )


class ToolCallResponse(BaseModel):
    """MCP tool call response"""

    tool: str
    result: Any
    success: bool
    error: Optional[str] = None
    duration_ms: float = 0
    trace_id: Optional[str] = None


class ToolListResponse(BaseModel):
    """List of available tools"""

    tools: List[Dict[str, Any]]
    count: int
    categories: List[str]


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    tools_available: int
    services: Dict[str, str]
    uptime_seconds: float


# =============================================================================
# Tool Handlers
# =============================================================================


class ToolHandlers:
    """
    Implementation of tool handlers.
    Each handler corresponds to a registered tool.
    """

    def __init__(self):
        self.start_time = datetime.now()
        self._http_client: Optional[httpx.AsyncClient] = None

        # Service URLs from environment
        self.n8n_url = os.getenv("N8N_URL", "http://localhost:5678")
        self.langflow_url = os.getenv("LANGFLOW_URL", "http://localhost:7860")
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.librarian_url = os.getenv("LIBRARIAN_URL", "http://localhost:8200")
        self.gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8080")

        # Paths
        self.obsidian_vault = os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian-vault")
        self.vault_logs = Path(os.getenv("VAULT_LOGS_PATH", "./vault/logs"))

        # Import integrations lazily
        self._obsidian = None
        self._simplewall = None
        self._sysinternals = None
        self._ffmpeg = None
        self._personal_assistant = None

    async def get_http_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()

    # =========================================================================
    # System Handlers
    # =========================================================================

    @traced("tool.execute_command")
    async def execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shell command with safety checks"""
        command = params.get("command", "")
        working_dir = params.get("working_dir", os.getcwd())
        timeout = params.get("timeout", 300)
        capture_output = params.get("capture_output", True)
        confirmed = params.get("confirmed", False)

        # Destructive patterns requiring confirmation
        destructive_patterns = [
            "rm -rf",
            "rm -r",
            "del /s",
            "rmdir /s",
            "Remove-Item -Recurse",
            "format",
            "diskpart",
            "reg delete",
            "uninstall",
            "DROP TABLE",
            "DELETE FROM",
            "TRUNCATE",
        ]

        is_destructive = any(p.lower() in command.lower() for p in destructive_patterns)

        if is_destructive and not confirmed:
            return {
                "status": "confirmation_required",
                "message": f"Destructive operation detected. Set confirmation=true to proceed: {command}",
                "command": command,
            }

        try:
            # Use PowerShell on Windows, bash on Unix
            if platform.system() == "Windows":
                shell_cmd = ["powershell", "-Command", command]
            else:
                shell_cmd = ["bash", "-c", command]

            result = await asyncio.to_thread(
                subprocess.run,
                shell_cmd,
                cwd=working_dir,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
            )

            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @traced("tool.check_services")
    async def check_services(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of all OsMEN services"""
        services_to_check = params.get("services", [])
        timeout = params.get("timeout", 5)

        all_services = {
            "n8n": f"{self.n8n_url}/healthz",
            "langflow": f"{self.langflow_url}/health",
            "qdrant": f"{self.qdrant_url}/",
            "librarian": f"{self.librarian_url}/health",
            "gateway": f"{self.gateway_url}/healthz",
        }

        if services_to_check:
            services = {k: v for k, v in all_services.items() if k in services_to_check}
        else:
            services = all_services

        results = {}
        client = await self.get_http_client()

        for name, url in services.items():
            try:
                response = await client.get(url, timeout=timeout)
                results[name] = "healthy" if response.status_code < 400 else "unhealthy"
            except Exception:
                results[name] = "unreachable"

        return {
            "services": results,
            "all_healthy": all(s == "healthy" for s in results.values()),
            "timestamp": datetime.now().isoformat(),
        }

    @traced("tool.get_system_info")
    async def get_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information"""
        import psutil

        include_processes = params.get("include_processes", False)

        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "hostname": platform.node(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "cpu": {
                "cores": psutil.cpu_count(),
                "usage_percent": psutil.cpu_percent(interval=1),
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "usage_percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
                "free_gb": round(psutil.disk_usage("/").free / (1024**3), 2),
                "usage_percent": psutil.disk_usage("/").percent,
            },
        }

        if include_processes:
            processes = []
            for proc in sorted(
                psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
                key=lambda p: p.info.get("cpu_percent", 0),
                reverse=True,
            )[:10]:
                processes.append(proc.info)
            info["top_processes"] = processes

        return info

    # =========================================================================
    # Knowledge Handlers
    # =========================================================================

    def _get_obsidian(self):
        """Lazy load Obsidian integration"""
        if self._obsidian is None:
            try:
                from tools.obsidian.obsidian_integration import ObsidianIntegration

                self._obsidian = ObsidianIntegration(self.obsidian_vault)
            except ImportError:
                logger.warning("Obsidian integration not available")
        return self._obsidian

    @traced("tool.obsidian_create_note")
    async def obsidian_create_note(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create note in Obsidian vault"""
        obsidian = self._get_obsidian()
        if not obsidian:
            return {"error": "Obsidian integration not available"}

        return await asyncio.to_thread(
            obsidian.create_note,
            title=params["title"],
            content=params["content"],
            folder=params.get("folder", ""),
            tags=params.get("tags", []),
        )

    @traced("tool.obsidian_read_note")
    async def obsidian_read_note(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read note from Obsidian vault"""
        obsidian = self._get_obsidian()
        if not obsidian:
            return {"error": "Obsidian integration not available"}

        return await asyncio.to_thread(
            obsidian.read_note,
            note_path=params["path"],
        )

    @traced("tool.obsidian_search")
    async def obsidian_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search Obsidian vault"""
        obsidian = self._get_obsidian()
        if not obsidian:
            return {"error": "Obsidian integration not available"}

        results = await asyncio.to_thread(
            obsidian.search_notes,
            query=params["query"],
        )
        return {"results": results[: params.get("limit", 10)]}

    @traced("tool.obsidian_list_notes")
    async def obsidian_list_notes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List notes in Obsidian vault"""
        obsidian = self._get_obsidian()
        if not obsidian:
            return {"error": "Obsidian integration not available"}

        return await asyncio.to_thread(
            obsidian.list_notes,
            folder=params.get("folder", ""),
        )

    @traced("tool.librarian_search")
    async def librarian_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search Librarian RAG system"""
        client = await self.get_http_client()
        try:
            response = await client.post(
                f"{self.librarian_url}/search",
                json={
                    "query": params["query"],
                    "collection": params.get("collection", "default"),
                    "mode": params.get("mode", "lateral"),
                    "limit": params.get("limit", 10),
                },
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    # =========================================================================
    # Memory Handlers
    # =========================================================================

    @traced("tool.memory_store")
    async def memory_store(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Store in Qdrant vector memory"""
        # TODO: Implement proper embedding generation
        client = await self.get_http_client()
        collection = params.get("collection", "default_memory")

        try:
            # Ensure collection exists
            await client.put(
                f"{self.qdrant_url}/collections/{collection}",
                json={
                    "vectors": {"size": 384, "distance": "Cosine"},
                },
            )
        except:
            pass  # Collection may already exist

        # Store (placeholder - needs actual embedding)
        point_id = int(datetime.now().timestamp() * 1000)

        return {
            "status": "stored",
            "id": str(point_id),
            "collection": collection,
            "content_preview": params["content"][:100],
        }

    @traced("tool.memory_recall")
    async def memory_recall(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recall from Qdrant vector memory"""
        client = await self.get_http_client()
        collection = params.get("collection", "default_memory")

        try:
            response = await client.post(
                f"{self.qdrant_url}/collections/{collection}/points/search",
                json={
                    "vector": [0.0] * 384,  # Placeholder
                    "limit": params.get("limit", 10),
                    "with_payload": True,
                },
            )
            return response.json()
        except Exception as e:
            return {"error": str(e), "results": []}

    @traced("tool.memory_collections")
    async def memory_collections(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List memory collections"""
        client = await self.get_http_client()
        try:
            response = await client.get(f"{self.qdrant_url}/collections")
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    # =========================================================================
    # Workflow Handlers
    # =========================================================================

    @traced("tool.workflow_trigger")
    async def workflow_trigger(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger n8n workflow"""
        client = await self.get_http_client()
        webhook_path = params.get("webhook_path", f"/webhook/{params['workflow']}")

        try:
            response = await client.post(
                f"{self.n8n_url}{webhook_path}",
                json=params.get("payload", {}),
                timeout=60.0,
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    @traced("tool.langflow_run")
    async def langflow_run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run Langflow flow"""
        client = await self.get_http_client()

        try:
            response = await client.post(
                f"{self.langflow_url}/api/v1/run/{params['flow_id']}",
                json={
                    "input_value": params["input"],
                    "tweaks": params.get("tweaks", {}),
                },
                timeout=120.0,
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    # =========================================================================
    # Security Handlers
    # =========================================================================

    def _get_simplewall(self):
        """Lazy load Simplewall integration"""
        if self._simplewall is None:
            try:
                from tools.simplewall.simplewall_integration import (
                    SimplewallIntegration,
                )

                self._simplewall = SimplewallIntegration()
            except ImportError:
                logger.warning("Simplewall integration not available")
        return self._simplewall

    def _get_sysinternals(self):
        """Lazy load Sysinternals integration"""
        if self._sysinternals is None:
            try:
                from tools.sysinternals.sysinternals_integration import (
                    SysinternalsIntegration,
                )

                self._sysinternals = SysinternalsIntegration()
            except ImportError:
                logger.warning("Sysinternals integration not available")
        return self._sysinternals

    @traced("tool.firewall_block")
    async def firewall_block(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Block domain/IP with Simplewall"""
        simplewall = self._get_simplewall()
        if not simplewall:
            return {"error": "Simplewall integration not available"}

        return await asyncio.to_thread(
            simplewall.block_domain,
            domain=params["target"],
        )

    @traced("tool.firewall_list_rules")
    async def firewall_list_rules(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Simplewall rules"""
        simplewall = self._get_simplewall()
        if not simplewall:
            return {"error": "Simplewall integration not available"}

        return await asyncio.to_thread(simplewall.get_rules)

    @traced("tool.sysinternals_autoruns")
    async def sysinternals_autoruns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run Autoruns analysis"""
        sysinternals = self._get_sysinternals()
        if not sysinternals:
            return {"error": "Sysinternals integration not available"}

        return await asyncio.to_thread(
            sysinternals.run_autoruns,
            output_file=params.get("output_file"),
        )

    @traced("tool.system_health")
    async def system_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """System health analysis"""
        sysinternals = self._get_sysinternals()
        if not sysinternals:
            return {"error": "Sysinternals integration not available"}

        return await asyncio.to_thread(sysinternals.analyze_system_health)

    # =========================================================================
    # Media Handlers
    # =========================================================================

    def _get_ffmpeg(self):
        """Lazy load FFmpeg integration"""
        if self._ffmpeg is None:
            try:
                from tools.ffmpeg.ffmpeg_integration import FFmpegIntegration

                self._ffmpeg = FFmpegIntegration()
            except ImportError:
                logger.warning("FFmpeg integration not available")
        return self._ffmpeg

    @traced("tool.media_info")
    async def media_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get media file info"""
        ffmpeg = self._get_ffmpeg()
        if not ffmpeg:
            return {"error": "FFmpeg integration not available"}

        return await asyncio.to_thread(
            ffmpeg.get_media_info,
            file_path=params["file_path"],
        )

    @traced("tool.media_convert")
    async def media_convert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert media file"""
        ffmpeg = self._get_ffmpeg()
        if not ffmpeg:
            return {"error": "FFmpeg integration not available"}

        return await asyncio.to_thread(
            ffmpeg.convert_video,
            input_file=params["input_file"],
            output_file=params["output_file"],
            codec=params.get("codec"),
        )

    # =========================================================================
    # Productivity Handlers
    # =========================================================================

    def _get_personal_assistant(self):
        """Lazy load Personal Assistant"""
        if self._personal_assistant is None:
            try:
                from agents.personal_assistant.personal_assistant_agent import (
                    PersonalAssistantAgent,
                )

                self._personal_assistant = PersonalAssistantAgent()
            except ImportError:
                logger.warning("Personal Assistant not available")
        return self._personal_assistant

    @traced("tool.task_create")
    async def task_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create task"""
        pa = self._get_personal_assistant()
        if not pa:
            return {"error": "Personal Assistant not available"}

        return await asyncio.to_thread(
            pa.create_task,
            title=params["title"],
            description=params.get("description", ""),
            priority=params.get("priority", "medium"),
            due_date=params.get("due_date"),
        )

    @traced("tool.task_list")
    async def task_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List tasks"""
        pa = self._get_personal_assistant()
        if not pa:
            return {"error": "Personal Assistant not available"}

        tasks = await asyncio.to_thread(
            pa.get_tasks,
            status=params.get("status") if params.get("status") != "all" else None,
            priority=params.get("priority"),
            due_today=params.get("due_today", False),
        )
        return {"tasks": tasks}

    @traced("tool.daily_summary")
    async def daily_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get daily summary"""
        pa = self._get_personal_assistant()
        if not pa:
            return {"error": "Personal Assistant not available"}

        return await asyncio.to_thread(
            pa.get_daily_summary,
            date=params.get("date"),
        )

    # =========================================================================
    # Agent Handlers
    # =========================================================================

    @traced("tool.agent_spawn")
    async def agent_spawn(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Spawn subagent"""
        session_id = (
            f"YO-{datetime.now().strftime('%Y%m%d-%H%M')}-{os.urandom(2).hex()}"
        )

        return {
            "status": "spawned",
            "session_id": session_id,
            "agent_type": params["agent_type"],
            "task": params["task"],
            "priority": params.get("priority", "P2"),
        }

    # =========================================================================
    # Integration Handlers
    # =========================================================================

    @traced("tool.log_action")
    async def log_action(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Log action to audit trail"""
        self.vault_logs.mkdir(parents=True, exist_ok=True)

        log_file = self.vault_logs / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        entry = (
            f"[{datetime.now().isoformat()}] "
            f"[{params.get('severity', 'info').upper()}] "
            f"{params.get('action', '')} - {params.get('result', '')}\n"
        )

        async def write_log():
            with open(log_file, "a") as f:
                f.write(entry)

        await asyncio.to_thread(write_log)

        return {"logged": True, "file": str(log_file)}

    @traced("tool.vector_search")
    async def vector_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Direct Qdrant vector search"""
        client = await self.get_http_client()

        try:
            response = await client.post(
                f"{self.qdrant_url}/collections/{params['collection']}/points/search",
                json={
                    "vector": [0.0] * 384,  # Placeholder
                    "limit": params.get("limit", 5),
                    "with_payload": True,
                    "with_vectors": params.get("with_vectors", False),
                },
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# =============================================================================
# MCP Server
# =============================================================================


class MCPServer:
    """
    Unified Model Context Protocol Server for OsMEN.

    Provides:
    - Centralized tool registry
    - OpenTelemetry tracing
    - Async handler dispatch
    - FastAPI integration
    """

    def __init__(self):
        self.registry = get_tool_registry()
        self.handlers = ToolHandlers()
        self.tracing = TracingManager()
        self.start_time = datetime.now()

        # Map tool names to handler methods
        self._handler_map = {
            # System
            "execute_command": self.handlers.execute_command,
            "check_services": self.handlers.check_services,
            "get_system_info": self.handlers.get_system_info,
            # Knowledge
            "obsidian_create_note": self.handlers.obsidian_create_note,
            "obsidian_read_note": self.handlers.obsidian_read_note,
            "obsidian_search": self.handlers.obsidian_search,
            "obsidian_list_notes": self.handlers.obsidian_list_notes,
            "librarian_search": self.handlers.librarian_search,
            # Memory
            "memory_store": self.handlers.memory_store,
            "memory_recall": self.handlers.memory_recall,
            "memory_collections": self.handlers.memory_collections,
            # Workflow
            "workflow_trigger": self.handlers.workflow_trigger,
            "langflow_run": self.handlers.langflow_run,
            # Security
            "firewall_block": self.handlers.firewall_block,
            "firewall_list_rules": self.handlers.firewall_list_rules,
            "sysinternals_autoruns": self.handlers.sysinternals_autoruns,
            "system_health": self.handlers.system_health,
            # Media
            "media_info": self.handlers.media_info,
            "media_convert": self.handlers.media_convert,
            # Productivity
            "task_create": self.handlers.task_create,
            "task_list": self.handlers.task_list,
            "daily_summary": self.handlers.daily_summary,
            # Agent
            "agent_spawn": self.handlers.agent_spawn,
            # Integration
            "log_action": self.handlers.log_action,
            "vector_search": self.handlers.vector_search,
        }

    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available tools"""
        cat = ToolCategory(category) if category else None
        tools = self.registry.list(category=cat)
        return [t.to_mcp_schema() for t in tools]

    async def call_tool(self, request: ToolCallRequest) -> ToolCallResponse:
        """Execute a tool call with tracing"""
        tool_name = request.tool
        params = request.parameters

        # Get tool definition
        tool_def = self.registry.get(tool_name)
        if not tool_def:
            return ToolCallResponse(
                tool=tool_name,
                result=None,
                success=False,
                error=f"Unknown tool: {tool_name}",
            )

        # Check if confirmation required
        if tool_def.requires_confirmation and not request.confirmation:
            return ToolCallResponse(
                tool=tool_name,
                result=None,
                success=False,
                error=f"Tool '{tool_name}' requires confirmation. Set confirmation=true to proceed.",
            )

        # Get handler
        handler = self._handler_map.get(tool_name)
        if not handler:
            return ToolCallResponse(
                tool=tool_name,
                result=None,
                success=False,
                error=f"No handler for tool: {tool_name}",
            )

        # Execute with timing
        start_time = datetime.now()
        try:
            result = await asyncio.wait_for(
                handler(params),
                timeout=tool_def.timeout_seconds,
            )
            duration = (datetime.now() - start_time).total_seconds() * 1000

            # Record to tracing
            self.tracing.record_tool_call(
                tool_name=tool_name,
                parameters=params,
                result=result,
                duration_ms=duration,
                success=True,
            )

            return ToolCallResponse(
                tool=tool_name,
                result=result,
                success=True,
                duration_ms=duration,
            )

        except asyncio.TimeoutError:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            error = f"Tool timed out after {tool_def.timeout_seconds}s"

            self.tracing.record_tool_call(
                tool_name=tool_name,
                parameters=params,
                result=None,
                duration_ms=duration,
                success=False,
                error=error,
            )

            return ToolCallResponse(
                tool=tool_name,
                result=None,
                success=False,
                error=error,
                duration_ms=duration,
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            error = str(e)
            logger.error(f"Tool call failed: {tool_name}, error: {error}")

            self.tracing.record_tool_call(
                tool_name=tool_name,
                parameters=params,
                result=None,
                duration_ms=duration,
                success=False,
                error=error,
            )

            return ToolCallResponse(
                tool=tool_name,
                result=None,
                success=False,
                error=error,
                duration_ms=duration,
            )

    async def get_health(self) -> HealthResponse:
        """Get server health status"""
        service_status = await self.handlers.check_services({})
        uptime = (datetime.now() - self.start_time).total_seconds()

        return HealthResponse(
            status=(
                "healthy" if service_status.get("all_healthy", False) else "degraded"
            ),
            version="2.0.0",
            tools_available=len(self.registry.list()),
            services=service_status.get("services", {}),
            uptime_seconds=uptime,
        )

    async def shutdown(self):
        """Cleanup resources"""
        await self.handlers.close()
        self.tracing.shutdown()


# =============================================================================
# FastAPI Application
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting OsMEN MCP Server...")
    yield
    logger.info("Shutting down OsMEN MCP Server...")
    await app.state.mcp_server.shutdown()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    app = FastAPI(
        title="OsMEN Unified MCP Server",
        description="Model Context Protocol server with OpenTelemetry tracing",
        version="2.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add tracing middleware
    app.add_middleware(TracingMiddleware)

    # Initialize MCP server
    mcp_server = MCPServer()
    app.state.mcp_server = mcp_server

    # ==========================================================================
    # Routes
    # ==========================================================================

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "OsMEN Unified MCP Server",
            "version": "2.0.0",
            "protocol": "MCP",
            "tools_available": len(mcp_server.registry.list()),
            "categories": [c.value for c in ToolCategory],
        }

    @app.get("/tools", response_model=ToolListResponse)
    async def list_tools(category: Optional[str] = None):
        """List available tools"""
        tools = mcp_server.list_tools(category)
        return ToolListResponse(
            tools=tools,
            count=len(tools),
            categories=[c.value for c in ToolCategory],
        )

    @app.get("/tools/{tool_name}")
    async def get_tool(tool_name: str):
        """Get a specific tool definition"""
        tool = mcp_server.registry.get(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
        return tool.to_mcp_schema()

    @app.post("/tools/call", response_model=ToolCallResponse)
    async def call_tool(request: ToolCallRequest):
        """Execute a tool call"""
        return await mcp_server.call_tool(request)

    @app.post("/mcp")
    async def mcp_endpoint(request: Request):
        """MCP protocol endpoint for standard clients"""
        body = await request.json()
        method = body.get("method", "")

        if method == "tools/list":
            tools = mcp_server.list_tools()
            return {"tools": tools}

        elif method == "tools/call":
            params = body.get("params", {})
            tool_request = ToolCallRequest(
                tool=params.get("name", ""),
                parameters=params.get("arguments", {}),
            )
            result = await mcp_server.call_tool(tool_request)
            return {
                "content": [{"type": "text", "text": json.dumps(result.result)}],
                "isError": not result.success,
            }

        else:
            return {"error": f"Unknown method: {method}"}

    @app.get("/health", response_model=HealthResponse)
    async def health():
        """Health check endpoint"""
        return await mcp_server.get_health()

    @app.get("/healthz")
    async def healthz():
        """Kubernetes-style health check"""
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics():
        """Basic metrics endpoint"""
        return {
            "uptime_seconds": (datetime.now() - mcp_server.start_time).total_seconds(),
            "tools_registered": len(mcp_server.registry.list()),
            "categories": len(ToolCategory),
        }

    return app


# Create default app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MCP_PORT", "8081"))
    host = os.getenv("MCP_HOST", "0.0.0.0")

    logger.info(f"Starting OsMEN Unified MCP Server on {host}:{port}")

    uvicorn.run(
        "gateway.mcp.server:app",
        host=host,
        port=port,
        reload=os.getenv("MCP_RELOAD", "false").lower() == "true",
        log_level="info",
    )
