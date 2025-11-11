"""System status monitoring for OsMEN Web Dashboard

Provides real-time status information about agents, services, and resources.
"""

import os
import psutil
import json
from pathlib import Path
from typing import Dict, List


async def get_system_status() -> Dict:
    """Get comprehensive system status."""
    return {
        "agents": await get_agent_health(),
        "services": await get_service_health(),
        "resources": await get_resource_usage(),
        "memory_system": await get_memory_system_status()
    }


async def get_agent_health() -> List[Dict]:
    """Get health status of all agents."""
    agents = []
    
    # Check if agents directory exists
    agents_dir = Path("/home/runner/work/OsMEN/OsMEN/agents")
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
    """Get health status of external services."""
    services = []
    
    # Check LangFlow
    services.append({
        "name": "LangFlow",
        "status": "unknown",
        "port": 7860,
        "enabled": os.path.exists("/home/runner/work/OsMEN/OsMEN/langflow")
    })
    
    # Check n8n
    services.append({
        "name": "n8n",
        "status": "unknown",
        "port": 5678,
        "enabled": os.path.exists("/home/runner/work/OsMEN/OsMEN/n8n")
    })
    
    # Check Memory System
    memory_file = Path("/home/runner/work/OsMEN/OsMEN/.copilot/memory.json")
    services.append({
        "name": "Memory System",
        "status": "healthy" if memory_file.exists() else "degraded",
        "enabled": True
    })
    
    return services


async def get_resource_usage() -> Dict:
    """Get system resource usage."""
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
            "used_gb": memory.used / (1024**3),
            "total_gb": memory.total / (1024**3),
            "status": "normal" if memory.percent < 80 else "high"
        },
        "disk": {
            "percent": disk.percent,
            "used_gb": disk.used / (1024**3),
            "total_gb": disk.total / (1024**3),
            "status": "normal" if disk.percent < 80 else "high"
        }
    }


async def get_memory_system_status() -> Dict:
    """Get memory system status."""
    memory_file = Path("/home/runner/work/OsMEN/OsMEN/.copilot/memory.json")
    
    if not memory_file.exists():
        return {
            "status": "not_initialized",
            "last_update": None
        }
    
    try:
        with open(memory_file) as f:
            data = json.load(f)
        
        return {
            "status": "healthy",
            "last_update": data.get("last_updated"),
            "user": data.get("user", {}).get("name")
        }
    except Exception:
        return {
            "status": "error",
            "error": "Failed to read memory system"
        }
