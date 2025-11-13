#!/usr/bin/env python3
"""
OsMEN Agent Gateway
Unified API gateway for production LLM agents (OpenAI, GitHub Copilot, Amazon Q, etc.)
"""

import os
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any, Tuple
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field
import httpx
import asyncpg
import redis.asyncio as redis

from logging_config import configure_logging
from rate_limiter import RateLimiter

from resilience import retryable_llm_call

configure_logging()
logger = logging.getLogger("osmen.gateway")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk  # type: ignore
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.getenv("SENTRY_ENVIRONMENT", ENVIRONMENT),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    )

def require_secret(name: str, min_length: int = 32) -> str:
    """Ensure required secrets are populated with strong values."""
    value = os.getenv(name)
    if value and len(value) >= min_length:
        return value
    if ENVIRONMENT == "production":
        raise RuntimeError(f"{name} must be set to at least {min_length} characters in production.")
    fallback = value or f"{name.lower()}-dev-secret"
    logger.warning(
        "Using fallback value for %s in %s environment. Set a secure secret via environment variable.",
        name,
        ENVIRONMENT
    )
    os.environ[name] = fallback
    return fallback


SESSION_SECRET = require_secret("SESSION_SECRET_KEY", min_length=32)


class CompletionRequest(BaseModel):
    """Request model for completions"""
    prompt: str
    agent: str = Field(default="openai", description="Agent to use: openai, copilot, amazonq, claude, lmstudio, ollama")
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False


class CompletionResponse(BaseModel):
    """Response model for completions"""
    content: str
    agent: str
    model: str
    usage: Optional[Dict[str, int]] = None


class ServiceHealthMonitor:
    """Perform health checks against core infrastructure services."""

    def __init__(self):
        self.postgres_config = {
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
            "database": os.getenv("POSTGRES_DB", "postgres"),
            "host": os.getenv("POSTGRES_HOST", "postgres"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "timeout": float(os.getenv("POSTGRES_HEALTH_TIMEOUT", "5")),
        }
        self.redis_config = {
            "host": os.getenv("REDIS_HOST", "redis"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "password": os.getenv("REDIS_PASSWORD"),
        }
        self.qdrant_url = os.getenv("QDRANT_HOST", "http://qdrant:6333")
        self.langflow_url = os.getenv(
            "LANGFLOW_INTERNAL_URL",
            os.getenv("LANGFLOW_HOST", "http://langflow:7860")
        )
        self.n8n_url = os.getenv(
            "N8N_INTERNAL_URL",
            f"http://{os.getenv('N8N_HOST', 'n8n')}:{os.getenv('N8N_PORT', '5678')}"
        )
        self.http_timeout = float(os.getenv("SERVICE_HEALTH_TIMEOUT", "5"))

    async def check_postgres(self) -> Tuple[bool, str]:
        """Verify PostgreSQL connectivity with a lightweight query."""
        conn = None
        try:
            conn = await asyncpg.connect(
                user=self.postgres_config["user"],
                password=self.postgres_config["password"],
                database=self.postgres_config["database"],
                host=self.postgres_config["host"],
                port=self.postgres_config["port"],
                timeout=self.postgres_config["timeout"]
            )
            await conn.execute("SELECT 1")
            return True, "PostgreSQL responded to SELECT 1"
        except Exception as exc:
            return False, f"PostgreSQL error: {exc}"
        finally:
            if conn:
                await conn.close()

    async def check_redis(self) -> Tuple[bool, str]:
        """Verify Redis availability using PING."""
        client = redis.Redis(
            host=self.redis_config["host"],
            port=self.redis_config["port"],
            password=self.redis_config["password"],
            encoding="utf-8",
            decode_responses=True
        )
        try:
            pong = await client.ping()
            return True, f"Redis responded with {pong}"
        except Exception as exc:
            return False, f"Redis error: {exc}"
        finally:
            await client.close()

    async def check_qdrant(self) -> Tuple[bool, str]:
        """Verify Qdrant REST API health endpoint."""
        base_url = self.qdrant_url.rstrip("/")
        for path in ("/healthz", "/health"):
            ok, detail = await self._http_check(f"{base_url}{path}")
            if ok:
                return True, "Qdrant health endpoint reachable"
        return False, f"Qdrant health check failed: {detail}"

    async def check_langflow(self) -> Tuple[bool, str]:
        """Verify Langflow UI availability (optional)."""
        if not self.langflow_url:
            return True, "Langflow disabled"
        return await self._http_check(self.langflow_url)

    async def check_n8n(self) -> Tuple[bool, str]:
        """Verify n8n workflow UI availability (optional)."""
        if not self.n8n_url:
            return True, "n8n disabled"
        return await self._http_check(self.n8n_url)

    async def _http_check(self, url: str, expected: Tuple[int, ...] = (200, 204)) -> Tuple[bool, str]:
        """Perform a simple HTTP GET and report status."""
        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                response = await client.get(url)
            ok = response.status_code in expected
            detail = f"HTTP {response.status_code}"
            try:
                payload = response.json()
                status_text = payload.get("status")
                if status_text:
                    detail = f"{detail} ({status_text})"
            except ValueError:
                pass
            return ok, detail
        except Exception as exc:
            return False, str(exc)

    async def collect(self) -> Dict[str, Dict[str, Any]]:
        """Gather health for all registered services concurrently."""
        checks = {
            "postgres": self.check_postgres(),
            "redis": self.check_redis(),
            "qdrant": self.check_qdrant(),
            "langflow": self.check_langflow(),
            "n8n": self.check_n8n(),
        }
        tasks = {name: asyncio.create_task(coro) for name, coro in checks.items()}
        results: Dict[str, Dict[str, Any]] = {}
        for name, task in tasks.items():
            try:
                ok, detail = await task
            except Exception as exc:
                ok, detail = False, f"Unexpected error: {exc}"
            results[name] = {"ok": ok, "detail": detail}
        return results

    async def summary(self) -> Dict[str, Any]:
        """Return overall health summary including per-service detail."""
        services = await self.collect()
        status = "healthy" if all(entry["ok"] for entry in services.values()) else "degraded"
        return {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": services
        }

    async def service_status(self, service: str) -> Optional[Dict[str, Any]]:
        """Return the health status for a single named service."""
        service_name = service.lower()
        check_method = getattr(self, f"check_{service_name}", None)
        if not check_method:
            return None
        ok, detail = await check_method()
        return {
            "service": service_name,
            "ok": ok,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


health_monitor = ServiceHealthMonitor()

rate_limiter = RateLimiter()
DEFAULT_RATE_LIMIT = max(30, int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")))
completion_guard = rate_limiter.guard("completion", DEFAULT_RATE_LIMIT, 60)
agents_guard = rate_limiter.guard("agents", max(30, DEFAULT_RATE_LIMIT // 4), 60)
health_guard = rate_limiter.guard("health", 90, 60)

PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_METRICS_ENABLED", "true").lower() == "true"
REQUEST_COUNTER = Counter("osmen_gateway_requests_total", "Gateway HTTP requests", ["method", "path", "status"])
COMPLETION_LATENCY = Histogram("osmen_gateway_completion_seconds", "LLM completion latency", ["agent"])

class AgentGateway:
    """Gateway for routing requests to different LLM agents"""
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.aws_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.lm_studio_url = os.getenv("LM_STUDIO_URL", "http://host.docker.internal:1234/v1")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        
        self.client = httpx.AsyncClient(timeout=120.0)
        
    async def completion(self, request: CompletionRequest) -> CompletionResponse:
        """Route completion request to appropriate agent"""
        agent = request.agent.lower()
        
        if agent == "openai":
            return await self._openai_completion(request)
        elif agent == "copilot":
            return await self._copilot_completion(request)
        elif agent == "amazonq":
            return await self._amazonq_completion(request)
        elif agent == "claude":
            return await self._claude_completion(request)
        elif agent == "lmstudio":
            return await self._lmstudio_completion(request)
        elif agent == "ollama":
            return await self._ollama_completion(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {agent}")
    
    @retryable_llm_call(max_attempts=3)
    async def _openai_completion(self, request: CompletionRequest) -> CompletionResponse:
        """OpenAI completion"""
        if not self.openai_key:
            raise HTTPException(status_code=401, detail="OpenAI API key not configured")
        
        model = request.model or os.getenv("OPENAI_MODEL", "gpt-4")
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        response = await self.client.post(
            f"{self.openai_base_url}/chat/completions",
            json=payload,
            headers=headers
        )
        
        response.raise_for_status()
        
        data = response.json()
        return CompletionResponse(
            content=data["choices"][0]["message"]["content"],
            agent="openai",
            model=model,
            usage=data.get("usage")
        )
    
    async def _copilot_completion(self, request: CompletionRequest) -> CompletionResponse:
        """GitHub Copilot completion"""
        if not self.github_token:
            raise HTTPException(status_code=401, detail="GitHub token not configured")
        
        # TODO: Implement GitHub Copilot API integration
        # GitHub Copilot is primarily used via VSCode extension (see docs/LLM_AGENTS.md)
        # API access requires special GitHub Copilot for Business subscription
        # For now, use VSCode extension or CLI: gh copilot suggest/explain
        return CompletionResponse(
            content="GitHub Copilot is best used via VSCode extension or 'gh copilot' CLI. See docs/LLM_AGENTS.md for setup.",
            agent="copilot",
            model="copilot"
        )
    
    async def _amazonq_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Amazon Q completion"""
        if not self.aws_key:
            raise HTTPException(status_code=401, detail="AWS credentials not configured")
        
        # TODO: Implement Amazon Q API integration via AWS SDK
        # Amazon Q is primarily used via AWS Console, VSCode extension, or CLI
        # API integration requires AWS SDK for Python (boto3) with Q service
        # For now, use AWS Console, VSCode AWS Toolkit, or CLI: aws q chat
        return CompletionResponse(
            content="Amazon Q is best used via AWS Console, VSCode AWS Toolkit, or 'aws q chat' CLI. See docs/LLM_AGENTS.md for setup.",
            agent="amazonq",
            model="amazonq"
        )
    
    @retryable_llm_call(max_attempts=3)
    async def _claude_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Anthropic Claude completion"""
        if not self.anthropic_key:
            raise HTTPException(status_code=401, detail="Anthropic API key not configured")
        
        model = request.model or os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        response = await self.client.post(
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers=headers
        )
        
        response.raise_for_status()
        
        data = response.json()
        return CompletionResponse(
            content=data["content"][0]["text"],
            agent="claude",
            model=model,
            usage=data.get("usage")
        )
    
    @retryable_llm_call(max_attempts=3)
    async def _lmstudio_completion(self, request: CompletionRequest) -> CompletionResponse:
        """LM Studio completion (OpenAI-compatible API)"""
        model = request.model or os.getenv("LM_STUDIO_MODEL", "local-model")
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        try:
            response = await self.client.post(
                f"{self.lm_studio_url}/chat/completions",
                json=payload
            )
            
            response.raise_for_status()
            
            data = response.json()
            return CompletionResponse(
                content=data["choices"][0]["message"]["content"],
                agent="lmstudio",
                model=model,
                usage=data.get("usage")
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="LM Studio not reachable. Please start LM Studio on host and enable API server."
            )
    
    @retryable_llm_call(max_attempts=3)
    async def _ollama_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Ollama completion"""
        model = request.model or os.getenv("OLLAMA_MODEL", "llama2")
        
        payload = {
            "model": model,
            "prompt": request.prompt,
            "stream": False
        }
        
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            )
            
            response.raise_for_status()
            
            data = response.json()
            return CompletionResponse(
                content=data["response"],
                agent="ollama",
                model=model
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Ollama not reachable. Start with: docker-compose --profile ollama up -d"
            )
    
    async def list_agents(self) -> Dict[str, Any]:
        """List available agents and their status"""
        agents = {
            "openai": {
                "available": bool(self.openai_key),
                "models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo-preview"]
            },
            "copilot": {
                "available": bool(self.github_token),
                "models": ["copilot"]
            },
            "amazonq": {
                "available": bool(self.aws_key),
                "models": ["amazonq"]
            },
            "claude": {
                "available": bool(self.anthropic_key),
                "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]
            },
            "lmstudio": {
                "available": True,
                "models": ["local-model"],
                "note": "Requires LM Studio running on host"
            },
            "ollama": {
                "available": True,
                "models": ["llama2", "mistral", "codellama"],
                "note": "Optional, start with --profile ollama"
            }
        }
        return agents


# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info("Starting OsMEN Agent Gateway")
    yield
    logger.info("Shutting down OsMEN Agent Gateway")


app = FastAPI(
    title="OsMEN Agent Gateway",
    description="Unified API gateway for production LLM agents",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.getenv("ENFORCE_HTTPS", "false").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)

if PROMETHEUS_ENABLED:
    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        REQUEST_COUNTER.labels(request.method, request.url.path, str(response.status_code)).inc()
        return response

# Initialize gateway
gateway = AgentGateway()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OsMEN Agent Gateway",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/agents")
async def list_agents(_: None = Depends(agents_guard)):
    """List available agents"""
    return await gateway.list_agents()


@app.post("/completion", response_model=CompletionResponse)
async def completion(request: CompletionRequest, _: None = Depends(completion_guard)):
    """Generate completion using specified agent"""
    start = time.perf_counter()
    response = await gateway.completion(request)
    if PROMETHEUS_ENABLED:
        COMPLETION_LATENCY.labels(request.agent).observe(time.perf_counter() - start)
    return response


async def _health_response():
    summary = await health_monitor.summary()
    status_code = 200 if summary["status"] == "healthy" else 503
    return JSONResponse(summary, status_code=status_code)


@app.get("/health")
async def health(_: None = Depends(health_guard)):
    """Aggregate health endpoint for infrastructure services."""
    return await _health_response()


@app.get("/healthz")
async def healthz(_: None = Depends(health_guard)):
    """Alias for /health to support Kubernetes-style probing."""
    return await _health_response()


@app.get("/healthz/{service_name}")
async def service_health(service_name: str, _: None = Depends(health_guard)):
    """Return health information for an individual service."""
    result = await health_monitor.service_status(service_name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service_name}'")
    status_code = 200 if result["ok"] else 503
    return JSONResponse(result, status_code=status_code)


@app.get("/metrics")
async def gateway_metrics(_: None = Depends(health_guard)):
    """Prometheus metrics for the gateway."""
    if not PROMETHEUS_ENABLED:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
