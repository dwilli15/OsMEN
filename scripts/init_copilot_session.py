#!/usr/bin/env python3
"""
OsMEN Copilot Session Initializer

This script initializes the OsMEN context for a Copilot chat session.
It loads memory, checks services, and prepares the orchestration layer.

Usage:
    python scripts/init_copilot_session.py

Or in Copilot Chat (if MCP is enabled):
    @osmen initialize session
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_mcp_config():
    """Verify MCP configuration in VS Code settings"""
    settings_path = PROJECT_ROOT / ".vscode" / "settings.json"
    if not settings_path.exists():
        return {"ok": False, "error": "No .vscode/settings.json found"}

    try:
        import json5  # Try json5 for jsonc support

        with open(settings_path) as f:
            settings = json5.load(f)
    except ImportError:
        # Fallback: strip comments manually
        with open(settings_path) as f:
            content = f.read()
            # Remove // comments
            import re

            content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
            settings = json.loads(content)

    mcp_enabled = settings.get("github.copilot.chat.experimental.mcp.enabled", False)
    mcp_servers = settings.get("github.copilot.chat.experimental.mcp.servers", {})

    return {
        "ok": mcp_enabled and "osmen" in mcp_servers,
        "mcp_enabled": mcp_enabled,
        "servers": list(mcp_servers.keys()),
        "osmen_config": mcp_servers.get("osmen", {}),
    }


def check_services():
    """Check OsMEN service health"""
    import requests

    services = {
        "gateway": "http://localhost:8080/health",
        "langflow": "http://localhost:7860",
        "n8n": "http://localhost:5678",
        "chromadb": "http://localhost:8000/api/v2/heartbeat",
    }

    results = {}
    for name, url in services.items():
        try:
            # Gateway can be slow, use longer timeout
            timeout = 10 if name == "gateway" else 3
            resp = requests.get(url, timeout=timeout)
            results[name] = {"ok": resp.status_code == 200, "status": resp.status_code}
        except Exception as e:
            results[name] = {"ok": False, "error": str(e)[:50]}

    return results


def load_context():
    """Load current context from memory.json"""
    memory_path = PROJECT_ROOT / ".copilot" / "memory.json"
    if memory_path.exists():
        with open(memory_path) as f:
            memory = json.load(f)
        return {
            "current_phase": memory.get("system_state", {}).get(
                "current_phase", "unknown"
            ),
            "recent_actions": len(memory.get("conversation_history", [])),
            "learned_preferences": len(memory.get("learned_preferences", {})),
        }
    return {"ok": False, "error": "No memory.json found"}


def init_hybrid_memory():
    """Initialize HybridMemory system"""
    try:
        from integrations.memory import HybridMemory

        memory = HybridMemory()

        # Store session start (use 'remember' method)
        memory.remember(
            content=f"Copilot session initialized at {datetime.now().isoformat()}",
            source="session_init",
        )

        return {"ok": True, "memory_type": "HybridMemory"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


def main():
    """Initialize OsMEN Copilot session"""
    print("=" * 60)
    print("🤖 OsMEN Copilot Session Initializer")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # 1. Check MCP Configuration
    print("📋 MCP Configuration:")
    mcp = check_mcp_config()
    if mcp["ok"]:
        print(f"   ✅ MCP enabled with servers: {mcp['servers']}")
    else:
        print(f"   ❌ MCP not configured: {mcp.get('error', 'Check settings.json')}")
    print()

    # 2. Check Services
    print("🔌 Service Health:")
    services = check_services()
    for name, status in services.items():
        icon = "✅" if status.get("ok") else "❌"
        detail = (
            f"HTTP {status.get('status')}"
            if status.get("ok")
            else status.get("error", "down")
        )
        print(f"   {icon} {name}: {detail}")
    print()

    # 3. Load Context
    print("📚 Context:")
    ctx = load_context()
    if ctx.get("ok", True):
        print(f"   Phase: {ctx.get('current_phase', 'unknown')}")
        print(f"   Recent actions: {ctx.get('recent_actions', 0)}")
        print(f"   Learned preferences: {ctx.get('learned_preferences', 0)}")
    else:
        print(f"   ⚠️  {ctx.get('error')}")
    print()

    # 4. Initialize Memory
    print("🧠 HybridMemory:")
    mem = init_hybrid_memory()
    if mem["ok"]:
        print(f"   ✅ {mem['memory_type']} initialized")
    else:
        print(f"   ❌ {mem.get('error')}")
    print()

    # 5. Summary
    all_ok = mcp["ok"] and all(s.get("ok") for s in services.values()) and mem["ok"]
    print("=" * 60)
    if all_ok:
        print("✅ Session ready! Use @YOLO-OPS in Copilot Chat")
    else:
        print("⚠️  Some components need attention")
    print("=" * 60)

    # Return status for programmatic use
    return {
        "timestamp": datetime.now().isoformat(),
        "mcp": mcp,
        "services": services,
        "context": ctx,
        "memory": mem,
        "ready": all_ok,
    }


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result["ready"] else 1)
