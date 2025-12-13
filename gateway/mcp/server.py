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
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

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
        chroma_default = (
            "http://chromadb:8000"
            if Path("/.dockerenv").exists()
            else "http://localhost:8000"
        )
        chroma_env = os.getenv("CHROMA_URL")
        self.chroma_url = (
            chroma_env.strip() if chroma_env and chroma_env.strip() else chroma_default
        )
        self.librarian_url = os.getenv("LIBRARIAN_URL", "http://localhost:8200")
        self.gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8080")

        # ConvertX
        self.convertx_url = os.getenv("CONVERTX_URL", "http://localhost:3000")
        self._convertx = None

        # ChromaDB (vector store)
        self._chroma = None

        # Agent tracking (in-memory)
        self._spawned_agents: Dict[str, Dict[str, Any]] = {}

        # Embeddings configuration (no placeholders)
        self.embed_provider = os.getenv("EMBED_PROVIDER", "").strip().lower()
        self.ollama_url = (
            os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_HOST") or ""
        ).strip()
        self.ollama_embed_model = os.getenv(
            "OLLAMA_EMBED_MODEL",
            os.getenv("OLLAMA_MODEL", "nomic-embed-text"),
        ).strip()

        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_base_url = os.getenv(
            "OPENAI_BASE_URL",
            "https://api.openai.com/v1",
        ).strip()
        self.openai_embed_model = os.getenv(
            "OPENAI_EMBED_MODEL",
            "text-embedding-3-small",
        ).strip()

        # Paths
        self.obsidian_vault = os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian-vault")
        self.vault_logs = Path(os.getenv("VAULT_LOGS_PATH", "./vault/logs"))

        # Import integrations lazily
        self._obsidian = None
        self._simplewall = None
        self._sysinternals = None
        self._ffmpeg = None
        self._personal_assistant = None

    def _get_convertx(self):
        """Lazy load ConvertX client."""
        if self._convertx is None:
            try:
                from integrations.convertx.client import ConvertXClient

                self._convertx = ConvertXClient(base_url=self.convertx_url)
            except ImportError:
                logger.warning("ConvertX client not available")
        return self._convertx

    async def get_http_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()

    async def _embed_text(self, text: str) -> List[float]:
        """Generate an embedding vector for text using configured provider.

        Provider selection order:
        - EMBED_PROVIDER if set ("ollama" or "openai")
        - Ollama if OLLAMA_URL is set
        - OpenAI if OPENAI_API_KEY is set

        Raises:
            RuntimeError if no provider is configured or provider call fails.
        """
        provider = self.embed_provider
        if not provider:
            # Prefer OpenAI if configured; only auto-select Ollama if explicitly configured.
            if self.openai_api_key:
                provider = "openai"
            elif self.ollama_url:
                provider = "ollama"

        client = await self.get_http_client()

        if provider == "ollama":
            if not self.ollama_embed_model:
                raise RuntimeError(
                    "Ollama embedding provider selected but OLLAMA_EMBED_MODEL not configured"
                )

            base_url = self.ollama_url or "http://localhost:11434"
            url = f"{base_url.rstrip('/')}/api/embeddings"
            resp = await client.post(
                url,
                json={"model": self.ollama_embed_model, "prompt": text},
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            embedding = data.get("embedding")
            if not isinstance(embedding, list) or not embedding:
                raise RuntimeError(
                    f"Ollama embeddings response missing 'embedding': {data}"
                )
            return embedding

        if provider == "openai":
            if not self.openai_api_key:
                raise RuntimeError(
                    "OpenAI embedding provider selected but OPENAI_API_KEY not configured"
                )

            url = f"{self.openai_base_url.rstrip('/')}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            }
            resp = await client.post(
                url,
                headers=headers,
                json={"model": self.openai_embed_model, "input": text},
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            embedding = (
                (data.get("data") or [{}])[0].get("embedding")
                if isinstance(data, dict)
                else None
            )
            if not isinstance(embedding, list) or not embedding:
                raise RuntimeError(
                    f"OpenAI embeddings response missing embedding: {data}"
                )
            return embedding

        raise RuntimeError(
            "No embeddings provider configured. Set EMBED_PROVIDER (ollama/openai) and provider env vars."
        )

    def _get_chroma(self):
        """Lazy-load ChromaDB HttpClient."""
        if self._chroma is None:
            try:
                import chromadb

                parsed = urlparse(self.chroma_url)
                host = parsed.hostname or "localhost"
                port = parsed.port or 8000
                ssl = (parsed.scheme or "http").lower() == "https"

                self._chroma = chromadb.HttpClient(host=host, port=port, ssl=ssl)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize ChromaDB client: {e}")
        return self._chroma

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
            "chromadb": f"{self.chroma_url.rstrip('/')}/api/v2/heartbeat",
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

    @traced("tool.obsidian_update_note")
    async def obsidian_update_note(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing note in Obsidian vault"""
        obsidian = self._get_obsidian()
        if not obsidian:
            return {"error": "Obsidian integration not available"}

        return await asyncio.to_thread(
            obsidian.update_note,
            note_path=params["path"],
            content=params.get("content"),
            append=params.get("append", False),
        )

    @traced("tool.obsidian_delete_note")
    async def obsidian_delete_note(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a note from Obsidian vault"""
        obsidian = self._get_obsidian()
        if not obsidian:
            return {"error": "Obsidian integration not available"}

        return await asyncio.to_thread(
            obsidian.delete_note,
            note_path=params["path"],
            trash=params.get("trash", True),
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

    @traced("tool.librarian_ingest")
    async def librarian_ingest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest content into Librarian service."""
        client = await self.get_http_client()
        payload = {
            "content": params.get("content", ""),
            "source": params.get("source", ""),
            "collection": params.get("collection", "default"),
            "metadata": params.get("metadata", {}) or {},
        }
        if not payload["content"]:
            return {"error": "Missing required field: content"}
        if not payload["source"]:
            return {"error": "Missing required field: source"}

        # Librarian endpoint shapes have varied; try a small set.
        candidate_paths = ["/ingest", "/documents/ingest", "/api/ingest"]
        last_error = None
        for path in candidate_paths:
            try:
                resp = await client.post(f"{self.librarian_url}{path}", json=payload)
                if resp.status_code < 400:
                    return resp.json()
                last_error = {
                    "status_code": resp.status_code,
                    "body": resp.text[:500],
                    "path": path,
                }
            except Exception as e:
                last_error = {"error": str(e), "path": path}

        return {
            "error": "Librarian ingest failed",
            "details": last_error,
            "tried_paths": candidate_paths,
        }

    # =========================================================================
    # Memory Handlers
    # =========================================================================

    @traced("tool.memory_store")
    async def memory_store(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Store content in ChromaDB vector memory (real embeddings, real add)."""
        collection_name = params.get("collection", "default_memory")

        content = params.get("content", "")
        if not content:
            return {"error": "Missing required field: content"}

        embedding = await self._embed_text(content)
        vector_size = len(embedding)
        doc_id = os.urandom(16).hex()
        metadata = params.get("metadata", {}) or {}
        metadata = {
            **metadata,
            "importance": float(params.get("importance", 0.5)),
            "timestamp": datetime.now().isoformat(),
        }

        chroma = self._get_chroma()
        collection = await asyncio.to_thread(
            chroma.get_or_create_collection, collection_name
        )
        await asyncio.to_thread(
            collection.add,
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata],
            embeddings=[embedding],
        )

        return {
            "status": "stored",
            "id": doc_id,
            "collection": collection_name,
            "vector_size": vector_size,
            "content_preview": content[:100],
        }

    @traced("tool.memory_recall")
    async def memory_recall(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recall from ChromaDB vector memory using real embeddings."""
        collection_name = params.get("collection", "default_memory")

        query = params.get("query", "")
        if not query:
            return {
                "error": "Missing required field: query",
                "results": [],
                "collection": collection_name,
            }

        embedding = await self._embed_text(query)
        limit = int(params.get("limit", 10))
        where = params.get("filter") if isinstance(params.get("filter"), dict) else None

        try:
            chroma = self._get_chroma()
            collection = await asyncio.to_thread(
                chroma.get_or_create_collection, collection_name
            )
            q = await asyncio.to_thread(
                collection.query,
                query_embeddings=[embedding],
                n_results=limit,
                where=where,
                include=["metadatas", "documents", "distances"],
            )

            ids = (q.get("ids") or [[]])[0]
            docs = (q.get("documents") or [[]])[0]
            metas = (q.get("metadatas") or [[]])[0]
            dists = (q.get("distances") or [[]])[0]

            results = []
            for i in range(len(ids)):
                results.append(
                    {
                        "id": ids[i],
                        "distance": dists[i] if i < len(dists) else None,
                        "document": docs[i] if i < len(docs) else None,
                        "metadata": metas[i] if i < len(metas) else None,
                    }
                )
            return {"results": results, "collection": collection_name}
        except Exception as e:
            return {
                "error": str(e),
                "results": [],
                "collection": collection_name,
            }

    @traced("tool.memory_forget")
    async def memory_forget(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete specific entries from ChromaDB by IDs."""
        collection_name = params.get("collection", "default_memory")
        ids = params.get("ids")
        if not isinstance(ids, list) or not ids:
            return {"error": "Missing required field: ids", "deleted": 0}

        try:
            chroma = self._get_chroma()
            collection = await asyncio.to_thread(
                chroma.get_or_create_collection, collection_name
            )
            await asyncio.to_thread(collection.delete, ids=ids)
            return {"status": "deleted", "collection": collection_name, "ids": ids}
        except Exception as e:
            return {"error": str(e), "collection": collection_name, "ids": ids}

    @traced("tool.memory_collections")
    async def memory_collections(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List memory collections"""
        try:
            chroma = self._get_chroma()
            cols = await asyncio.to_thread(chroma.list_collections)
            return {
                "collections": [
                    getattr(c, "name", None) or c.get("name") for c in cols
                ],
                "count": len(cols),
            }
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

    @traced("tool.workflow_list")
    async def workflow_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List n8n workflows via REST API (requires API key or basic auth)."""
        client = await self.get_http_client()
        api_key = os.getenv("N8N_API_KEY", "").strip()
        user = os.getenv("N8N_BASIC_AUTH_USER", "").strip()
        password = os.getenv("N8N_BASIC_AUTH_PASSWORD", "").strip()

        headers: Dict[str, str] = {}
        auth = None
        if api_key:
            headers["X-N8N-API-KEY"] = api_key
            headers["Authorization"] = f"Bearer {api_key}"
        elif user and password:
            auth = (user, password)
        else:
            return {
                "error": "n8n auth not configured",
                "hint": "Set N8N_API_KEY or N8N_BASIC_AUTH_USER/N8N_BASIC_AUTH_PASSWORD",
            }

        try:
            resp = await client.get(
                f"{self.n8n_url}/rest/workflows",
                headers=headers,
                auth=auth,
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            workflows = data.get("data") if isinstance(data, dict) else data

            active_only = bool(params.get("active_only", True))
            tag = params.get("tag")

            if isinstance(workflows, list):
                if active_only:
                    workflows = [w for w in workflows if w.get("active")]
                if tag:
                    workflows = [w for w in workflows if tag in (w.get("tags") or [])]
            return {"workflows": workflows}
        except Exception as e:
            return {"error": str(e)}

    @traced("tool.workflow_status")
    async def workflow_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get n8n execution status via REST API."""
        execution_id = params.get("execution_id", "")
        if not execution_id:
            return {"error": "Missing required field: execution_id"}

        client = await self.get_http_client()
        api_key = os.getenv("N8N_API_KEY", "").strip()
        user = os.getenv("N8N_BASIC_AUTH_USER", "").strip()
        password = os.getenv("N8N_BASIC_AUTH_PASSWORD", "").strip()

        headers: Dict[str, str] = {}
        auth = None
        if api_key:
            headers["X-N8N-API-KEY"] = api_key
            headers["Authorization"] = f"Bearer {api_key}"
        elif user and password:
            auth = (user, password)
        else:
            return {
                "error": "n8n auth not configured",
                "hint": "Set N8N_API_KEY or N8N_BASIC_AUTH_USER/N8N_BASIC_AUTH_PASSWORD",
            }

        try:
            resp = await client.get(
                f"{self.n8n_url}/rest/executions/{execution_id}",
                headers=headers,
                auth=auth,
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()
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

    @traced("tool.langflow_list")
    async def langflow_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Langflow flows (best-effort across common endpoints)."""
        client = await self.get_http_client()
        candidate_paths = ["/api/v1/flows", "/api/v1/flows/list", "/api/v1/flow"]
        last_error = None
        for path in candidate_paths:
            try:
                resp = await client.get(f"{self.langflow_url}{path}", timeout=30.0)
                if resp.status_code < 400:
                    return (
                        resp.json()
                        if resp.headers.get("content-type", "").startswith(
                            "application/json"
                        )
                        else {"html": resp.text}
                    )
                last_error = {"status_code": resp.status_code, "path": path}
            except Exception as e:
                last_error = {"error": str(e), "path": path}
        return {"error": "Langflow list failed", "details": last_error}

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

    @traced("tool.firewall_unblock")
    async def firewall_unblock(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unblock domain/IP with Simplewall."""
        simplewall = self._get_simplewall()
        if not simplewall:
            return {"error": "Simplewall integration not available"}
        return await asyncio.to_thread(
            simplewall.unblock_domain,
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

    @traced("tool.sysinternals_procmon")
    async def sysinternals_procmon(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Capture system activity with Procmon."""
        sysinternals = self._get_sysinternals()
        if not sysinternals:
            return {"error": "Sysinternals integration not available"}
        return await asyncio.to_thread(
            sysinternals.run_process_monitor,
            duration_seconds=int(params.get("duration_seconds", 30)),
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

    @traced("tool.media_extract_audio")
    async def media_extract_audio(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract audio from a video file using FFmpeg integration."""
        ffmpeg = self._get_ffmpeg()
        if not ffmpeg:
            return {"error": "FFmpeg integration not available"}
        return await asyncio.to_thread(
            ffmpeg.extract_audio,
            video_file=params["input_file"],
            audio_file=params["output_file"],
            codec=params.get("format", "mp3"),
        )

    @traced("tool.media_thumbnail")
    async def media_thumbnail(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a thumbnail from a video using FFmpeg integration."""
        ffmpeg = self._get_ffmpeg()
        if not ffmpeg:
            return {"error": "FFmpeg integration not available"}
        return await asyncio.to_thread(
            ffmpeg.create_thumbnail,
            video_file=params["input_file"],
            thumbnail_file=params["output_file"],
            timestamp=params.get("timestamp", "00:00:01"),
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

    @traced("tool.task_update")
    async def task_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task in Personal Assistant."""
        pa = self._get_personal_assistant()
        if not pa:
            return {"error": "Personal Assistant not available"}
        return await asyncio.to_thread(
            pa.update_task,
            task_id=int(params["task_id"]),
            status=params.get("status"),
            priority=params.get("priority"),
            due_date=params.get("due_date"),
        )

    @traced("tool.reminder_set")
    async def reminder_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set a reminder in Personal Assistant."""
        pa = self._get_personal_assistant()
        if not pa:
            return {"error": "Personal Assistant not available"}
        return await asyncio.to_thread(
            pa.set_reminder,
            title=params["title"],
            time=params["time"],
            message=params.get("message", ""),
        )

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

        record = {
            "status": "spawned",
            "session_id": session_id,
            "agent_type": params["agent_type"],
            "task": params["task"],
            "priority": params.get("priority", "P2"),
            "created_at": datetime.now().isoformat(),
        }
        self._spawned_agents[session_id] = record

        return record

    @traced("tool.agent_status")
    async def agent_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a spawned agent session (in-memory)."""
        session_id = params.get("session_id", "")
        if not session_id:
            return {"error": "Missing required field: session_id"}
        record = self._spawned_agents.get(session_id)
        if not record:
            return {"error": f"Unknown session_id: {session_id}"}
        return record

    @traced("tool.agent_list")
    async def agent_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List spawned agent sessions (in-memory)."""
        include_completed = bool(params.get("include_completed", False))
        agents = list(self._spawned_agents.values())
        if not include_completed:
            agents = [
                a for a in agents if a.get("status") not in {"completed", "failed"}
            ]
        return {"agents": agents, "count": len(agents)}

    # =========================================================================
    # ConvertX Handlers
    # =========================================================================

    @traced("tool.convertx_health")
    async def convertx_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Health check ConvertX service."""
        convertx = self._get_convertx()
        if not convertx:
            return {"error": "ConvertX client not available"}
        return await asyncio.to_thread(
            lambda: {"healthy": bool(convertx.health_check()), "url": self.convertx_url}
        )

    @traced("tool.get_conversion_options")
    async def get_conversion_options(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get possible conversion targets for an input format."""
        input_format = (params.get("input_format") or "").lstrip(".").lower()
        if not input_format:
            return {"error": "Missing required field: input_format"}
        try:
            from integrations.convertx.utils import get_possible_conversions

            options = await asyncio.to_thread(get_possible_conversions, input_format)
            return {"input_format": input_format, "outputs": options}
        except Exception as e:
            return {"error": str(e)}

    @traced("tool.convert_file")
    async def convert_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single file using ConvertX service."""
        convertx = self._get_convertx()
        if not convertx:
            return {"error": "ConvertX client not available"}

        input_file = params.get("input_file")
        target_format = params.get("target_format")
        output_file = params.get("output_file")
        if not input_file or not target_format:
            return {"error": "Missing required fields: input_file, target_format"}

        result = await asyncio.to_thread(
            convertx.convert,
            input_path=input_file,
            target_format=target_format,
            output_path=output_file,
            wait=True,
        )
        return {
            "success": bool(result.success),
            "output_path": result.output_path,
            "original_format": result.original_format,
            "target_format": result.target_format,
            "job_id": result.job_id,
            "duration_seconds": result.duration_seconds,
            "error": result.error,
        }

    @traced("tool.convert_batch")
    async def convert_batch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Batch convert using ConvertX service."""
        convertx = self._get_convertx()
        if not convertx:
            return {"error": "ConvertX client not available"}
        input_files = params.get("input_files")
        target_format = params.get("target_format")
        output_dir = params.get("output_dir")
        if not isinstance(input_files, list) or not input_files:
            return {"error": "Missing required field: input_files"}
        if not target_format:
            return {"error": "Missing required field: target_format"}

        results = []
        for fpath in input_files:
            out_path = None
            if output_dir:
                p = Path(fpath)
                out_path = str(
                    Path(output_dir)
                    / p.with_suffix(f".{target_format.lstrip('.')}").name
                )
            r = await asyncio.to_thread(
                convertx.convert,
                input_path=fpath,
                target_format=target_format,
                output_path=out_path,
                wait=True,
            )
            results.append(
                {
                    "input": str(fpath),
                    "success": bool(r.success),
                    "output_path": r.output_path,
                    "error": r.error,
                }
            )
        return {"results": results, "count": len(results)}

    # =========================================================================
    # Course Handlers
    # =========================================================================

    def _courses_root(self) -> Path:
        semester_ws = os.getenv("OSMEN_SEMESTER_WORKSPACE", "").strip()
        if semester_ws:
            return Path(semester_ws).expanduser().resolve() / "vault" / "courses"
        # Fall back to Obsidian vault if configured
        return Path(self.obsidian_vault).expanduser().resolve() / "courses"

    @traced("tool.course_list")
    async def course_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root = self._courses_root()
        if not root.exists():
            return {"courses": [], "count": 0, "root": str(root)}

        courses = []
        for course_dir in sorted([p for p in root.iterdir() if p.is_dir()]):
            meta_file = course_dir / "course.json"
            meta = {}
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                except Exception:
                    meta = {}
            courses.append({"course_id": course_dir.name, **meta})
        return {"courses": courses, "count": len(courses), "root": str(root)}

    @traced("tool.course_semester_overview")
    async def course_semester_overview(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = await self.course_list({})
        courses = data.get("courses", [])
        return {
            "courses": courses,
            "count": len(courses),
            "note": "Syllabus parsing is performed during import; calendar sync requires calendar provider configuration.",
        }

    @traced("tool.course_import_syllabus")
    async def course_import_syllabus(self, params: Dict[str, Any]) -> Dict[str, Any]:
        file_path = params.get("file_path")
        if not file_path:
            return {"error": "Missing required field: file_path"}

        src = Path(file_path).expanduser().resolve()
        if not src.exists():
            return {"error": f"File not found: {src}"}

        course_id = src.stem
        root = self._courses_root()
        course_dir = root / course_id
        syllabus_dir = course_dir / "syllabus"
        syllabus_dir.mkdir(parents=True, exist_ok=True)

        # Copy raw syllabus
        raw_dest = syllabus_dir / src.name
        if raw_dest != src:
            raw_dest.write_bytes(src.read_bytes())

        # If not text/markdown, attempt ConvertX -> markdown
        converted_md = None
        if src.suffix.lower() not in {".md", ".txt"}:
            convertx = self._get_convertx()
            if convertx and convertx.health_check():
                md_out = syllabus_dir / f"{course_id}.md"
                result = await asyncio.to_thread(
                    convertx.convert,
                    input_path=str(src),
                    target_format="md",
                    output_path=str(md_out),
                    wait=True,
                )
                if result.success:
                    converted_md = str(md_out)

        meta = {
            "course_id": course_id,
            "imported_at": datetime.now().isoformat(),
            "syllabus_raw": str(raw_dest),
            "syllabus_markdown": converted_md,
            "semester": params.get("semester"),
            "year": params.get("year"),
        }
        course_dir.mkdir(parents=True, exist_ok=True)
        (course_dir / "course.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

        # Optionally create Obsidian note
        if params.get("create_obsidian_notes", True):
            await self.course_sync_obsidian({"course_id": course_id})

        # Optionally sync calendar (only if provider configured + events exist)
        if params.get("sync_calendar", True):
            await self.course_sync_calendar({"course_id": course_id})

        return {"status": "imported", **meta}

    @traced("tool.course_bulk_import")
    async def course_bulk_import(self, params: Dict[str, Any]) -> Dict[str, Any]:
        file_paths = params.get("file_paths")
        if not isinstance(file_paths, list) or not file_paths:
            return {"error": "Missing required field: file_paths"}
        results = []
        for fp in file_paths:
            r = await self.course_import_syllabus(
                {
                    "file_path": fp,
                    "semester": params.get("semester"),
                    "year": params.get("year"),
                    "sync_calendar": False,
                    "create_obsidian_notes": True,
                }
            )
            results.append(r)
        return {"results": results, "count": len(results)}

    @traced("tool.course_sync_obsidian")
    async def course_sync_obsidian(self, params: Dict[str, Any]) -> Dict[str, Any]:
        course_id = params.get("course_id", "")
        if not course_id:
            return {"error": "Missing required field: course_id"}

        obsidian = self._get_obsidian()
        if not obsidian:
            return {"error": "Obsidian integration not available"}

        root = self._courses_root()
        meta_file = root / course_id / "course.json"
        meta = {}
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                meta = {}

        content_lines = [
            f"# {course_id}",
            "",
            "## Syllabus",
            meta.get("syllabus_markdown")
            or meta.get("syllabus_raw")
            or "(not available)",
            "",
            "## Metadata",
            json.dumps(meta, indent=2),
        ]
        return await asyncio.to_thread(
            obsidian.create_note,
            title=f"{course_id} (Course)",
            content="\n".join(content_lines),
            folder=f"courses/{course_id}",
            tags=["course", course_id],
        )

    @traced("tool.course_sync_calendar")
    async def course_sync_calendar(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sync course events to calendar if a provider is configured."""
        course_id = params.get("course_id", "")
        if not course_id:
            return {"error": "Missing required field: course_id"}

        try:
            from integrations.calendars.calendar_manager import CalendarManager

            cm = CalendarManager()
            if not cm.primary_provider:
                return {
                    "status": "skipped",
                    "course_id": course_id,
                    "reason": "No calendar provider configured in CalendarManager",
                }
            # We currently only sync events if course metadata includes them.
            root = self._courses_root()
            meta_file = root / course_id / "course.json"
            meta = {}
            if meta_file.exists():
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            events = meta.get("events") or []
            if not events:
                return {
                    "status": "ok",
                    "course_id": course_id,
                    "events_synced": 0,
                    "note": "No events found in course metadata. Add 'events' to course.json to sync.",
                }
            result = cm.create_events_batch(events)
            return {"status": "ok", "course_id": course_id, "result": result}
        except Exception as e:
            return {"error": str(e), "course_id": course_id}

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
        """Direct Qdrant vector search using real embeddings."""
        client = await self.get_http_client()
        query = params.get("query", "")
        collection = params.get("collection")
        if not collection:
            return {"error": "Missing required field: collection"}
        if not query:
            return {"error": "Missing required field: query"}

        embedding = await self._embed_text(query)
        body: Dict[str, Any] = {
            "vector": embedding,
            "limit": int(params.get("limit", 5)),
            "with_payload": True,
            "with_vectors": bool(params.get("with_vectors", False)),
        }
        if params.get("filter") is not None:
            body["filter"] = params.get("filter")

        try:
            response = await client.post(
                f"{self.qdrant_url}/collections/{collection}/points/search",
                json=body,
            )
            response.raise_for_status()
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
            "obsidian_update_note": self.handlers.obsidian_update_note,
            "obsidian_delete_note": self.handlers.obsidian_delete_note,
            "librarian_search": self.handlers.librarian_search,
            "librarian_ingest": self.handlers.librarian_ingest,
            # Memory
            "memory_store": self.handlers.memory_store,
            "memory_recall": self.handlers.memory_recall,
            "memory_forget": self.handlers.memory_forget,
            "memory_collections": self.handlers.memory_collections,
            # Workflow
            "workflow_trigger": self.handlers.workflow_trigger,
            "workflow_list": self.handlers.workflow_list,
            "workflow_status": self.handlers.workflow_status,
            "langflow_run": self.handlers.langflow_run,
            "langflow_list": self.handlers.langflow_list,
            # Security
            "firewall_block": self.handlers.firewall_block,
            "firewall_unblock": self.handlers.firewall_unblock,
            "firewall_list_rules": self.handlers.firewall_list_rules,
            "sysinternals_autoruns": self.handlers.sysinternals_autoruns,
            "sysinternals_procmon": self.handlers.sysinternals_procmon,
            "system_health": self.handlers.system_health,
            # Media
            "media_info": self.handlers.media_info,
            "media_convert": self.handlers.media_convert,
            "media_extract_audio": self.handlers.media_extract_audio,
            "media_thumbnail": self.handlers.media_thumbnail,
            # Productivity
            "task_create": self.handlers.task_create,
            "task_list": self.handlers.task_list,
            "task_update": self.handlers.task_update,
            "reminder_set": self.handlers.reminder_set,
            "daily_summary": self.handlers.daily_summary,
            # Agent
            "agent_spawn": self.handlers.agent_spawn,
            "agent_status": self.handlers.agent_status,
            "agent_list": self.handlers.agent_list,
            # Integration
            "log_action": self.handlers.log_action,
            "vector_search": self.handlers.vector_search,
            # ConvertX
            "convert_file": self.handlers.convert_file,
            "convert_batch": self.handlers.convert_batch,
            "get_conversion_options": self.handlers.get_conversion_options,
            "convertx_health": self.handlers.convertx_health,
            # Courses
            "course_import_syllabus": self.handlers.course_import_syllabus,
            "course_list": self.handlers.course_list,
            "course_semester_overview": self.handlers.course_semester_overview,
            "course_bulk_import": self.handlers.course_bulk_import,
            "course_sync_calendar": self.handlers.course_sync_calendar,
            "course_sync_obsidian": self.handlers.course_sync_obsidian,
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

        # Execute with monotonic timing (avoid negative durations if wall clock shifts)
        start_time = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                handler(params),
                timeout=tool_def.timeout_seconds,
            )
            duration = (time.perf_counter() - start_time) * 1000

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
            duration = (time.perf_counter() - start_time) * 1000
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
            duration = (time.perf_counter() - start_time) * 1000
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
