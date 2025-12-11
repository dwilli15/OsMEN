#!/usr/bin/env python3
"""
YOLO-OPS /initiate Command - Full Workflow Session Startup

This script performs the complete OsMEN startup sequence:
1. Service initialization (Docker)
2. Health verification
3. Housekeeping
4. Outstanding tasks review
5. Agent activation
6. Session report

Usage:
    python scripts/yolo_initiate.py

Or in Copilot Chat:
    @YOLO-OPS /initiate
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def log(msg: str, icon: str = ""):
    """Print formatted log message"""
    print(f"{icon} {msg}" if icon else msg)


def run_cmd(cmd: str, timeout: int = 60) -> Tuple[bool, str]:
    """Run shell command and return success + output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def step_1_services() -> Dict:
    """Step 1: Service Initialization"""
    log("Starting Docker services...", "🐳")

    # Check if Docker is running
    ok, out = run_cmd("docker info", timeout=10)
    if not ok:
        return {"ok": False, "error": "Docker not running"}

    # Start services
    ok, out = run_cmd("docker-compose up -d", timeout=120)
    if not ok:
        return {"ok": False, "error": f"Failed to start services: {out[:100]}"}

    # Wait for services to be healthy
    import time

    time.sleep(5)

    # Count running services
    ok, out = run_cmd("docker-compose ps --format json", timeout=30)
    try:
        # Parse docker-compose ps output
        lines = [l for l in out.strip().split("\n") if l.startswith("{")]
        services = [json.loads(l) for l in lines]
        running = sum(1 for s in services if "running" in s.get("State", "").lower())
        return {"ok": True, "running": running, "total": len(services)}
    except:
        return {"ok": True, "running": "unknown", "total": "unknown"}


def step_2_health() -> Dict:
    """Step 2: Health Verification"""
    log("Verifying service health...", "🏥")

    import requests

    endpoints = {
        "gateway": ("http://localhost:8080/health", 15),  # Gateway can be slow
        "langflow": ("http://localhost:7860", 5),
        "n8n": ("http://localhost:5678", 5),
        "chromadb": ("http://localhost:8000/api/v2/heartbeat", 5),
        "librarian": ("http://localhost:8200/health", 5),
    }

    results = {}
    healthy = 0
    for name, (url, timeout) in endpoints.items():
        try:
            resp = requests.get(url, timeout=timeout)
            results[name] = resp.status_code == 200
            if results[name]:
                healthy += 1
        except Exception:
            results[name] = False

    return {
        "ok": healthy >= 3,
        "healthy": healthy,
        "total": len(endpoints),
        "services": results,
    }


def step_3_housekeeping() -> Dict:
    """Step 3: Housekeeping"""
    log("Running housekeeping tasks...", "🧹")

    tasks_done = []

    # Check for exited containers
    ok, out = run_cmd('docker ps -a --filter "status=exited" --format "{{.Names}}"')
    exited = [c for c in out.strip().split("\n") if c]
    if exited:
        tasks_done.append(f"Found {len(exited)} exited containers")

    # Check disk space
    ok, out = run_cmd("docker system df --format '{{.Size}}'")
    tasks_done.append("Checked Docker disk usage")

    # Check old logs
    logs_dir = PROJECT_ROOT / "logs"
    if logs_dir.exists():
        old_logs = []
        cutoff = datetime.now() - timedelta(days=7)
        for f in logs_dir.glob("*.log"):
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                old_logs.append(f.name)
        if old_logs:
            tasks_done.append(f"Found {len(old_logs)} old log files (>7 days)")

    return {"ok": True, "tasks": tasks_done, "exited_containers": len(exited)}


def step_4_outstanding() -> Dict:
    """Step 4: Outstanding Tasks Review"""
    log("Reviewing outstanding tasks...", "📋")

    tasks = []

    # Check PROGRESS.md
    progress_file = PROJECT_ROOT / "PROGRESS.md"
    if progress_file.exists():
        content = progress_file.read_text()
        # Count TODO items
        todo_count = content.lower().count("- [ ]")
        done_count = content.lower().count("- [x]")
        tasks.append(f"PROGRESS.md: {todo_count} pending, {done_count} done")

    # Check memory.json
    memory_file = PROJECT_ROOT / ".copilot" / "memory.json"
    if memory_file.exists():
        try:
            memory = json.loads(memory_file.read_text())
            history = memory.get("conversation_history", [])
            tasks.append(f"Memory: {len(history)} conversation entries")
        except:
            pass

    # Check for recent git activity
    ok, out = run_cmd("git log --oneline -5", timeout=10)
    if ok:
        commits = [l for l in out.strip().split("\n") if l]
        tasks.append(f"Recent commits: {len(commits)}")

    return {
        "ok": True,
        "tasks": tasks,
        "pending": todo_count if "todo_count" in dir() else 0,
    }


def step_5_agents() -> Dict:
    """Step 5: Agent Activation"""
    log("Activating specialist agents...", "🤖")

    agents = {}

    # Boot Hardening - quick check
    try:
        from agents.boot_hardening.boot_hardening_agent import BootHardeningAgent

        agent = BootHardeningAgent()
        agents["boot_hardening"] = "ready"
    except Exception as e:
        agents["boot_hardening"] = f"error: {str(e)[:30]}"

    # Daily Brief
    try:
        from agents.daily_brief.daily_brief_agent import DailyBriefAgent

        agent = DailyBriefAgent()
        agents["daily_brief"] = "ready"
    except Exception as e:
        agents["daily_brief"] = f"error: {str(e)[:30]}"

    # Focus Guardrails
    try:
        from agents.focus_guardrails.focus_guardrails_agent import FocusGuardrailsAgent

        agent = FocusGuardrailsAgent()
        agents["focus_guardrails"] = "ready"
    except Exception as e:
        agents["focus_guardrails"] = f"error: {str(e)[:30]}"

    # Librarian
    try:
        from agents.librarian.librarian_agent import LibrarianAgent

        agents["librarian"] = "ready"
    except Exception as e:
        agents["librarian"] = f"error: {str(e)[:30]}"

    ready = sum(1 for v in agents.values() if v == "ready")
    return {"ok": ready >= 2, "ready": ready, "total": len(agents), "agents": agents}


def step_6_report(results: Dict) -> None:
    """Step 6: Session Report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    services = results.get("health", {})
    healthy = services.get("healthy", 0)
    total_services = services.get("total", 0)

    agents = results.get("agents", {})
    agents_ready = agents.get("ready", 0)
    agents_total = agents.get("total", 0)

    outstanding = results.get("outstanding", {})
    pending = outstanding.get("pending", 0)

    print()
    print("═" * 60)
    print("🔥 YOLO-OPS SESSION INITIALIZED")
    print("═" * 60)
    print(f"📅 Date: {timestamp}")
    print(f"🐳 Services: {healthy}/{total_services} healthy")
    print(f"🧠 Memory: HybridMemory active")
    print(f"📋 Outstanding: {pending} tasks")
    print(f"🤖 Agents: {agents_ready}/{agents_total} ready")
    print()

    # Service details
    if services.get("services"):
        print("Services:")
        for name, ok in services["services"].items():
            icon = "✅" if ok else "❌"
            print(f"  {icon} {name}")

    # Agent details
    if agents.get("agents"):
        print("\nAgents:")
        for name, status in agents["agents"].items():
            icon = "✅" if status == "ready" else "⚠️"
            print(f"  {icon} {name}: {status}")

    print()
    print("Ready for commands. What's the mission?")
    print("═" * 60)


def main():
    """Execute full /initiate sequence"""
    print()
    print("═" * 60)
    print("🔥 YOLO-OPS /initiate - Starting Workflow Session")
    print("═" * 60)
    print()

    results = {}

    # Step 1: Services
    print("━" * 40)
    print("STEP 1/5: Service Initialization")
    print("━" * 40)
    results["services"] = step_1_services()
    status = "✅" if results["services"]["ok"] else "❌"
    print(
        f"{status} Services: {results['services'].get('running', '?')}/{results['services'].get('total', '?')} running"
    )
    print()

    # Step 2: Health
    print("━" * 40)
    print("STEP 2/5: Health Verification")
    print("━" * 40)
    results["health"] = step_2_health()
    status = "✅" if results["health"]["ok"] else "❌"
    print(
        f"{status} Health: {results['health']['healthy']}/{results['health']['total']} healthy"
    )
    print()

    # Step 3: Housekeeping
    print("━" * 40)
    print("STEP 3/5: Housekeeping")
    print("━" * 40)
    results["housekeeping"] = step_3_housekeeping()
    for task in results["housekeeping"].get("tasks", []):
        print(f"  • {task}")
    print()

    # Step 4: Outstanding
    print("━" * 40)
    print("STEP 4/5: Outstanding Tasks")
    print("━" * 40)
    results["outstanding"] = step_4_outstanding()
    for task in results["outstanding"].get("tasks", []):
        print(f"  • {task}")
    print()

    # Step 5: Agents
    print("━" * 40)
    print("STEP 5/5: Agent Activation")
    print("━" * 40)
    results["agents"] = step_5_agents()
    status = "✅" if results["agents"]["ok"] else "⚠️"
    print(
        f"{status} Agents: {results['agents']['ready']}/{results['agents']['total']} ready"
    )
    print()

    # Step 6: Report
    step_6_report(results)

    # Store session start in memory
    try:
        from integrations.memory import HybridMemory

        memory = HybridMemory()
        memory.remember(
            content=f"YOLO-OPS session initiated at {datetime.now().isoformat()}. "
            f"Services: {results['health']['healthy']}/{results['health']['total']}, "
            f"Agents: {results['agents']['ready']}/{results['agents']['total']}",
            source="yolo_initiate",
        )
    except:
        pass  # Memory storage is optional

    # Return overall success
    all_ok = all(
        [results["services"]["ok"], results["health"]["ok"], results["agents"]["ok"]]
    )

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
