#!/usr/bin/env python3
"""
OsMEN Operational Status Check
Comprehensive system health check for all OsMEN components
"""

import sys
import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

# Common subprocess exceptions
SUBPROCESS_EXCEPTIONS = (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError)


class OperationalCheck:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        
    def add_check(self, name, status, message=""):
        """Add a check result"""
        self.checks.append({
            "name": name,
            "status": status,
            "message": message
        })
        if status:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_header(self):
        """Print header"""
        print("\n" + "="*60)
        print("OsMEN - Operational Status Check")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
    
    def print_results(self):
        """Print all check results"""
        for check in self.checks:
            status_icon = "✅" if check["status"] else "❌"
            print(f"{status_icon} {check['name']}")
            if check["message"]:
                print(f"   {check['message']}")
        
        print("\n" + "="*60)
        print(f"Total Checks: {len(self.checks)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print("="*60)
        
        if self.failed == 0:
            print("\n✅ OsMEN is OPERATIONAL - All checks passed!")
            print("\nSystem Status: HEALTHY ✅")
            return 0
        else:
            print(f"\n⚠️  OsMEN has {self.failed} issue(s)")
            print("\nSystem Status: DEGRADED ⚠️")
            return 1


def check_docker():
    """Check if Docker is available and running"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except SUBPROCESS_EXCEPTIONS:
        return False


def check_docker_compose():
    """Check if Docker Compose is available"""
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except SUBPROCESS_EXCEPTIONS:
        return False


def check_python():
    """Check Python version"""
    try:
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.decode().strip()
            return True, version
        return False, ""
    except SUBPROCESS_EXCEPTIONS:
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
        result = subprocess.run(
            ["python3", "test_agents.py"],
            capture_output=True,
            timeout=60,
            cwd=str(project_root)
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
            cwd=str(project_root)
        )
        if result.returncode != 0:
            return False, []
        
        output = result.stdout.decode().strip()
        if not output:
            return False, []
        
        # Parse service status
        services = []
        for line in output.split('\n'):
            if line.strip():
                try:
                    service = json.loads(line)
                    services.append(service)
                except json.JSONDecodeError:
                    pass
        
        return len(services) > 0, services
    except SUBPROCESS_EXCEPTIONS:
        return False, []


def main():
    """Run all operational checks"""
    checker = OperationalCheck()
    checker.print_header()
    
    # Use current working directory as project root
    project_root = Path(__file__).parent
    
    print("🔍 Checking system prerequisites...\n")
    
    # Check Docker
    docker_ok = check_docker()
    checker.add_check(
        "Docker Daemon",
        docker_ok,
        "Docker is running and accessible" if docker_ok else "Docker is not running"
    )
    
    # Check Docker Compose
    compose_ok = check_docker_compose()
    checker.add_check(
        "Docker Compose",
        compose_ok,
        "Docker Compose v2 is available" if compose_ok else "Docker Compose not found"
    )
    
    # Check Python
    python_ok, python_version = check_python()
    checker.add_check(
        "Python Runtime",
        python_ok,
        python_version if python_ok else "Python 3 not found"
    )
    
    print("\n🔍 Checking project structure...\n")
    
    # Check critical files
    critical_files = [
        "docker-compose.yml",
        "start.sh",
        "Makefile",
        "README.md",
        "requirements.txt",
        "test_agents.py"
    ]
    
    for file in critical_files:
        exists = check_file_exists(project_root / file)
        checker.add_check(
            f"File: {file}",
            exists,
            "Present" if exists else "Missing"
        )
    
    print("\n🔍 Checking component directories...\n")
    
    # Check critical directories
    critical_dirs = [
        "agents",
        "tools",
        "gateway",
        "langflow",
        "n8n",
        "docs"
    ]
    
    for dir_name in critical_dirs:
        exists = check_directory_exists(project_root / dir_name)
        checker.add_check(
            f"Directory: {dir_name}/",
            exists,
            "Present" if exists else "Missing"
        )
    
    print("\n🔍 Checking agent implementations...\n")
    
    # Check agent files
    agent_files = [
        "agents/boot_hardening/boot_hardening_agent.py",
        "agents/daily_brief/daily_brief_agent.py",
        "agents/focus_guardrails/focus_guardrails_agent.py",
    ]
    
    # Agent name mapping for display
    agent_names = {
        "boot_hardening": "Boot Hardening",
        "daily_brief": "Daily Brief",
        "focus_guardrails": "Focus Guardrails"
    }
    
    for agent_file in agent_files:
        exists = check_file_exists(project_root / agent_file)
        # Extract agent directory name and get display name from mapping
        agent_dir = Path(agent_file).parts[1]
        agent_name = agent_names.get(agent_dir, agent_dir.replace('_', ' ').title())
        checker.add_check(
            f"Agent: {agent_name}",
            exists,
            "Implementation found" if exists else "Not implemented"
        )
    
    print("\n🔍 Running agent test suite...\n")
    
    # Run agent tests
    tests_ok, test_output = check_agent_tests()
    checker.add_check(
        "Agent Test Suite",
        tests_ok,
        "All tests passed" if tests_ok else "Tests failed"
    )
    
    print("\n🔍 Checking Docker services...\n")
    
    # Check Docker services
    services_running, services = check_docker_services()
    if services_running:
        checker.add_check(
            "Docker Services",
            True,
            f"{len(services)} service(s) running"
        )
        
        # List running services
        for service in services:
            service_name = service.get('Service', service.get('Name', 'unknown'))
            service_status = service.get('State', 'unknown')
            is_running = service_status.lower() == 'running'
            checker.add_check(
                f"  └─ {service_name}",
                is_running,
                f"Status: {service_status}"
            )
    else:
        checker.add_check(
            "Docker Services",
            False,
            "No services are running. Use 'make start' or './start.sh' to start services"
        )
    
    print("\n")
    
    # Print final results
    return checker.print_results()


if __name__ == '__main__':
    sys.exit(main())
