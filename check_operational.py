#!/usr/bin/env python3
"""
OsMEN Operational Status Check
Comprehensive system health check for all OsMEN components
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

# Force UTF-8 output on Windows to avoid charmap codec errors with checkmarks/crosses
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Common subprocess exceptions
SUBPROCESS_EXCEPTIONS = (
    subprocess.TimeoutExpired,
    subprocess.CalledProcessError,
    FileNotFoundError,
    OSError,
)


class OperationalCheck:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0

    def add_check(self, name, status, message=""):
        """Add a check result"""
        self.checks.append({"name": name, "status": status, "message": message})
        if status:
            self.passed += 1
        else:
            self.failed += 1

    def print_header(self):
        """Print header"""
        print("\n" + "=" * 60)
        print("OsMEN - Operational Status Check")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")

    def print_results(self):
        """Print all check results"""
        for check in self.checks:
            status_icon = "[PASS]" if check["status"] else "[FAIL]"
            print(f"{status_icon} {check['name']}")
            if check["message"]:
                print(f"   {check['message']}")

        print("\n" + "=" * 60)
        print(f"Total Checks: {len(self.checks)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print("=" * 60)

        if self.failed == 0:
            print("\n[OK] OsMEN is OPERATIONAL - All checks passed!")
            print("\nSystem Status: HEALTHY")
            return 0
        else:
            print(f"\n[WARN] OsMEN has {self.failed} issue(s)")
            print("\nSystem Status: DEGRADED")
            return 1


def parse_args():
    """CLI arguments for operational checks."""
    parser = argparse.ArgumentParser(description="Run OsMEN operational health checks.")
    parser.add_argument(
        "--all", action="store_true", help="Run the full check suite (default)."
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Run Docker prerequisite and service checks.",
    )
    parser.add_argument(
        "--structure", action="store_true", help="Validate repository structure."
    )
    parser.add_argument(
        "--tests", action="store_true", help="Execute agent test suites."
    )
    parser.add_argument(
        "--services", action="store_true", help="Call HTTP health/readiness endpoints."
    )
    parser.add_argument(
        "--gateway-url",
        default=os.getenv("GATEWAY_HEALTH_URL", "http://localhost:8080"),
        help="Base URL for the Agent Gateway service.",
    )
    parser.add_argument(
        "--dashboard-url",
        default=os.getenv("DASHBOARD_URL", "http://localhost:8000"),
        help="Base URL for the OsMEN dashboard.",
    )
    return parser.parse_args()


def check_docker():
    """Check if Docker is available and running"""
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return result.returncode == 0
    except SUBPROCESS_EXCEPTIONS:
        return False


def check_docker_compose():
    """Check if Docker Compose is available"""
    try:
        result = subprocess.run(
            ["docker", "compose", "version"], capture_output=True, timeout=5
        )
        return result.returncode == 0
    except SUBPROCESS_EXCEPTIONS:
        return False


def check_python():
    """Check Python version - handles Windows using 'python' and Unix using 'python3'"""
    # Windows typically uses 'python' while Unix uses 'python3'
    python_cmds = (
        ["python3", "python"] if sys.platform != "win32" else ["python", "python3"]
    )

    for cmd in python_cmds:
        try:
            result = subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.decode().strip()
                # Verify it's Python 3.x
                if "Python 3" in version:
                    return True, version
        except SUBPROCESS_EXCEPTIONS:
            continue
    return False, ""


def check_file_exists(filepath):
    """Check if a file exists"""
    return Path(filepath).exists()


def check_directory_exists(dirpath):
    """Check if a directory exists"""
    return Path(dirpath).exists() and Path(dirpath).is_dir()


def check_agent_tests():
    """Run agent test suite"""
    try:
        # Use current working directory
        project_root = Path(__file__).parent

        # Determine correct Python command based on platform
        python_cmd = "python" if sys.platform == "win32" else "python3"

        result = subprocess.run(
            [python_cmd, "test_agents.py"],
            capture_output=True,
            timeout=300,  # 5 minute timeout for full test suite
            cwd=str(project_root),
        )
        return result.returncode == 0, result.stdout.decode()
    except SUBPROCESS_EXCEPTIONS as e:
        return False, str(e)


def check_docker_services():
    """Check if Docker services are running"""
    try:
        # Use current working directory
        project_root = Path(__file__).parent
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            capture_output=True,
            timeout=10,
            cwd=str(project_root),
        )
        if result.returncode != 0:
            return False, []

        output = result.stdout.decode().strip()
        if not output:
            return False, []

        # Parse service status
        services = []
        for line in output.split("\n"):
            if line.strip():
                try:
                    service = json.loads(line)
                    services.append(service)
                except json.JSONDecodeError:
                    pass

        return len(services) > 0, services
    except SUBPROCESS_EXCEPTIONS:
        return False, []


def http_health_check(url, timeout=5):
    """Perform a HTTP GET for health checking."""
    try:
        response = requests.get(url, timeout=timeout)
        detail = f"HTTP {response.status_code}"
        payload = None
        try:
            payload = response.json()
        except ValueError:
            payload = None
        ok = 200 <= response.status_code < 300
        return ok, detail, payload
    except requests.RequestException as exc:
        return False, str(exc), None


def main():
    """Run all operational checks"""
    args = parse_args()
    run_all = args.all or not any(
        [args.docker, args.structure, args.tests, args.services]
    )
    checker = OperationalCheck()
    checker.print_header()

    # Use current working directory as project root
    project_root = Path(__file__).parent

    if run_all or args.docker:
        print("Checking system prerequisites...\n")

        docker_ok = check_docker()
        checker.add_check(
            "Docker Daemon",
            docker_ok,
            (
                "Docker is running and accessible"
                if docker_ok
                else "Docker is not running"
            ),
        )

        compose_ok = check_docker_compose()
        checker.add_check(
            "Docker Compose",
            compose_ok,
            (
                "Docker Compose v2 is available"
                if compose_ok
                else "Docker Compose not found"
            ),
        )

        python_ok, python_version = check_python()
        checker.add_check(
            "Python Runtime",
            python_ok,
            python_version if python_ok else "Python 3 not found",
        )

    if run_all or args.structure:
        print("\nChecking project structure...\n")

        critical_files = [
            "docker-compose.yml",
            "start.sh",
            "Makefile",
            "README.md",
            "requirements.txt",
            "test_agents.py",
        ]

        for file in critical_files:
            exists = check_file_exists(project_root / file)
            checker.add_check(
                f"File: {file}", exists, "Present" if exists else "Missing"
            )

        print("\nChecking component directories...\n")
        critical_dirs = ["agents", "tools", "gateway", "langflow", "n8n", "docs"]

        for dir_name in critical_dirs:
            exists = check_directory_exists(project_root / dir_name)
            checker.add_check(
                f"Directory: {dir_name}/", exists, "Present" if exists else "Missing"
            )

        print("\nChecking agent implementations...\n")
        agent_files = [
            "agents/boot_hardening/boot_hardening_agent.py",
            "agents/daily_brief/daily_brief_agent.py",
            "agents/focus_guardrails/focus_guardrails_agent.py",
        ]
        agent_names = {
            "boot_hardening": "Boot Hardening",
            "daily_brief": "Daily Brief",
            "focus_guardrails": "Focus Guardrails",
        }

        for agent_file in agent_files:
            exists = check_file_exists(project_root / agent_file)
            agent_dir = Path(agent_file).parts[1]
            agent_name = agent_names.get(agent_dir, agent_dir.replace("_", " ").title())
            checker.add_check(
                f"Agent: {agent_name}",
                exists,
                "Implementation found" if exists else "Not implemented",
            )

    if run_all or args.tests:
        print("\nRunning agent test suite...\n")
        tests_ok, _ = check_agent_tests()
        checker.add_check(
            "Agent Test Suite",
            tests_ok,
            "All tests passed" if tests_ok else "Tests failed",
        )

    if run_all or args.docker:
        print("\nChecking Docker services...\n")
        services_running, services = check_docker_services()
        if services_running:
            checker.add_check(
                "Docker Services", True, f"{len(services)} service(s) running"
            )
            for service in services:
                service_name = service.get("Service", service.get("Name", "unknown"))
                service_status = service.get("State", "unknown")
                is_running = service_status.lower() == "running"
                checker.add_check(
                    f"  └─ {service_name}", is_running, f"Status: {service_status}"
                )
        else:
            checker.add_check(
                "Docker Services",
                False,
                "No services are running. Use 'make start' or './start.sh' to start services",
            )

    if run_all or args.services:
        print("\nChecking service health endpoints...\n")
        gateway_base = args.gateway_url.rstrip("/")

        gateway_ok, gateway_detail, gateway_payload = http_health_check(
            f"{gateway_base}/healthz"
        )
        checker.add_check("Gateway /healthz", gateway_ok, gateway_detail)
        if gateway_payload and isinstance(gateway_payload, dict):
            for service_name, data in gateway_payload.get("services", {}).items():
                checker.add_check(
                    f"  └─ {service_name}",
                    data.get("ok", False),
                    data.get("detail", ""),
                )

        # Check individual service health endpoints
        for dependent in ("postgres", "redis", "chromadb"):
            dep_ok, dep_detail, _ = http_health_check(
                f"{gateway_base}/healthz/{dependent}"
            )
            checker.add_check(f"Gateway /healthz/{dependent}", dep_ok, dep_detail)

        # Note: Dashboard is optional and not always deployed
        # If you need dashboard checks, uncomment and configure DASHBOARD_URL
        # dash_ready_ok, dash_ready_detail, _ = http_health_check(f"{dashboard_base}/ready")
        # checker.add_check("Dashboard /ready", dash_ready_ok, dash_ready_detail)

    print("\n")
    return checker.print_results()


if __name__ == "__main__":
    sys.exit(main())
