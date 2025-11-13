"""System status monitoring for OsMEN Web Dashboard."""

import json
import os
from pathlib import Path
from typing import Dict, List

import psutil

try:
    from cache.redis_cache import cache_json
except ImportError:  # pragma: no cover - fallback when cache module unavailable
    cache_json = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent


async def get_system_status() -> Dict:
    async def _compute():
        return {
            "agents": await get_agent_health(),
            "services": await get_service_health(),
            "resources": await get_resource_usage(),
            "memory_system": await get_memory_system_status(),
        }

    if cache_json:
        return await cache_json("status:dashboard", _compute, ttl=30)
    return await _compute()


async def get_agent_health() -> List[Dict]:
    agents = []
    agents_dir = PROJECT_ROOT / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.py"):
            if agent_file.name != "__init__.py":
                agents.append({
                    "name": agent_file.stem,
                    "status": "healthy",
                    "last_run": "N/A"
                })
    return agents


async def get_service_health() -> List[Dict]:
    services = []
    services.append({
        "name": "LangFlow",
        "status": "unknown",
        "port": 7860,
        "enabled": (PROJECT_ROOT / "langflow").exists()
    })
    services.append({
        "name": "n8n",
        "status": "unknown",
        "port": 5678,
        "enabled": (PROJECT_ROOT / "n8n").exists()
    })
    memory_file = PROJECT_ROOT / ".copilot" / "memory.json"
    services.append({
        "name": "Memory System",
        "status": "healthy" if memory_file.exists() else "degraded",
        "enabled": True
    })
    return services


async def get_resource_usage() -> Dict:
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "cpu": {
            "percent": cpu_percent,
            "status": "normal" if cpu_percent < 80 else "high"
        },
        "memory": {
            "percent": memory.percent,
            "used_gb": round(memory.used / (1024**3), 2),
            "total_gb": round(memory.total / (1024**3), 2),
            "status": "normal" if memory.percent < 80 else "high"
        },
        "disk": {
            "percent": disk.percent,
            "used_gb": round(disk.used / (1024**3), 2),
            "total_gb": round(disk.total / (1024**3), 2),
            "status": "normal" if disk.percent < 80 else "high"
        }
    }


async def get_memory_system_status() -> Dict:
    memory_file = PROJECT_ROOT / ".copilot" / "memory.json"
    if not memory_file.exists():
        return {"status": "not_initialized", "last_update": None}
    try:
        with open(memory_file, encoding="utf-8") as handle:
            data = json.load(handle)
        return {
            "status": "healthy",
            "last_update": data.get("last_updated"),
            "user": data.get("user", {}).get("name")
        }
    except Exception:
        return {"status": "error", "error": "Failed to read memory system"}
