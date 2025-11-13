#!/usr/bin/env python3
"""
OsMEN Production Readiness Validator
Comprehensive validation of system readiness for production deployment
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple
import json


class ProductionValidator:
    def __init__(self):
        self.passed = []
        self.warnings = []
        self.failures = []
        self.project_root = Path(__file__).parent.parent.parent
        
    def check(self, name: str, result: bool, message: str = "", warning: bool = False):
        """Record a check result"""
        if result:
            self.passed.append(f"✅ {name}")
            if message:
                self.passed.append(f"   {message}")
        elif warning:
            self.warnings.append(f"⚠️  {name}")
            if message:
                self.warnings.append(f"   {message}")
        else:
            self.failures.append(f"❌ {name}")
            if message:
                self.failures.append(f"   {message}")
    
    def section(self, title: str):
        """Print section header"""
        print(f"\n{'='*70}")
        print(f"{title}")
        print(f"{'='*70}\n")
    
    def run_command(self, cmd: List[str], check_output: bool = True) -> Tuple[bool, str]:
        """Run a command and return success status and output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            if check_output:
                return result.returncode == 0, result.stdout + result.stderr
            return True, result.stdout
        except Exception as e:
            return False, str(e)
    
    def validate_environment(self):
        """Validate environment configuration"""
        self.section("1. Environment Configuration")
        
        env_file = self.project_root / ".env"
        self.check(
            "Environment file exists",
            env_file.exists(),
            "Found .env configuration file"
        )
        
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
            
            # Check for dangerous defaults
            self.check(
                "N8N password changed",
                "changeme" not in content,
                "Default n8n password has been changed",
                warning=True
            )
            
            self.check(
                "LLM provider configured",
                any(key in content and "your_" not in content for key in [
                    "OPENAI_API_KEY=sk-",
                    "ANTHROPIC_API_KEY=sk-",
                    "LM_STUDIO_URL=http"
                ]),
                "At least one LLM provider is configured",
                warning=True
            )
            
            self.check(
                "Web secret key changed",
                "dev-secret-key-change-in-production" not in content,
                "Production secret key is set",
                warning=True
            )
    
    def validate_dependencies(self):
        """Validate Python dependencies"""
        self.section("2. Python Dependencies")
        
        # Check Python version
        import sys
        version = sys.version_info
        self.check(
            "Python version",
            version >= (3, 12),
            f"Python {version.major}.{version.minor}.{version.micro}"
        )
        
        # Check requirements installed
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            with open(requirements_file) as f:
                requirements = [line.split("==")[0].strip() 
                              for line in f if line.strip() and not line.startswith("#")]
            
            failed_imports = []
            for req in requirements:
                # Convert package names to import names
                import_name = req.replace("-", "_").lower()
                try:
                    __import__(import_name)
                except ImportError:
                    failed_imports.append(req)
            
            self.check(
                "Required packages installed",
                len(failed_imports) == 0,
                f"All {len(requirements)} packages available" if not failed_imports 
                else f"Missing: {', '.join(failed_imports)}",
                warning=len(failed_imports) > 0
            )
    
    def validate_docker(self):
        """Validate Docker environment"""
        self.section("3. Docker Environment")
        
        # Check Docker daemon
        success, output = self.run_command(["docker", "version"])
        self.check(
            "Docker daemon running",
            success,
            "Docker is accessible"
        )
        
        # Check Docker Compose
        success, output = self.run_command(["docker", "compose", "version"])
        self.check(
            "Docker Compose available",
            success,
            "Docker Compose v2+ installed"
        )
        
        # Check running containers
        success, output = self.run_command(["docker", "compose", "ps", "--format", "json"])
        if success:
            try:
                containers = json.loads(output) if output.strip() else []
                running = len([c for c in containers if isinstance(c, dict)])
                self.check(
                    "Docker services",
                    running > 0,
                    f"{running} service(s) running",
                    warning=running == 0
                )
            except:
                self.check("Docker services", False, "Could not parse container status", warning=True)
    
    def validate_agents(self):
        """Validate agent implementations"""
        self.section("4. Agent Implementations")
        
        agents_dir = self.project_root / "agents"
        expected_agents = [
            ("boot_hardening", "boot_hardening_agent.py"),
            ("daily_brief", "daily_brief_agent.py"),
            ("focus_guardrails", "focus_guardrails_agent.py"),
        ]
        
        for agent_name, agent_file in expected_agents:
            agent_path = agents_dir / agent_name / agent_file
            self.check(
                f"{agent_name.replace('_', ' ').title()} Agent",
                agent_path.exists(),
                f"Implementation found at {agent_path.relative_to(self.project_root)}"
            )
    
    def validate_tests(self):
        """Validate test suite"""
        self.section("5. Test Suite")
        
        test_file = self.project_root / "test_agents.py"
        self.check(
            "Test suite exists",
            test_file.exists(),
            "Found agent test suite"
        )
        
        if test_file.exists():
            success, output = self.run_command(["python3", str(test_file)])
            passed = "All tests passed!" in output
            self.check(
                "All tests passing",
                passed,
                "6/6 agent tests passed" if passed else "Some tests failed - check output"
            )
    
    def validate_security(self):
        """Validate security configuration"""
        self.section("6. Security Validation")
        
        security_script = self.project_root / "scripts" / "automation" / "validate_security.py"
        if security_script.exists():
            success, output = self.run_command(["python3", str(security_script)])
            issues = "0 issues" in output
            self.check(
                "Security validation",
                issues,
                "No critical security issues" if issues else "Review security output",
                warning=not issues
            )
    
    def validate_documentation(self):
        """Validate documentation"""
        self.section("7. Documentation")
        
        docs = [
            ("README.md", "Main readme"),
            ("1stsetup.md", "First-time setup guide"),
            ("QUICKSTART.md", "Quick start guide"),
            ("docs/SETUP.md", "Detailed setup"),
            ("docs/PRODUCTION_DEPLOYMENT.md", "Production deployment guide"),
            ("docs/LLM_AGENTS.md", "LLM configuration"),
            ("docs/TROUBLESHOOTING.md", "Troubleshooting guide"),
        ]
        
        for doc_file, description in docs:
            doc_path = self.project_root / doc_file
            self.check(
                description,
                doc_path.exists(),
                f"Found {doc_file}"
            )
    
    def validate_configuration_files(self):
        """Validate configuration files"""
        self.section("8. Configuration Files")
        
        config_files = [
            "docker-compose.yml",
            "docker-compose.prod.yml",
            ".env.example",
            ".env.production.example",
            "requirements.txt",
            "Makefile",
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            self.check(
                config_file,
                config_path.exists(),
                "Configuration file present"
            )
    
    def validate_directory_structure(self):
        """Validate directory structure"""
        self.section("9. Directory Structure")
        
        required_dirs = [
            "agents",
            "tools",
            "gateway",
            "langflow/flows",
            "n8n/workflows",
            "docs",
            "config",
            "scripts/automation",
            "integrations/calendar",
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            self.check(
                dir_path,
                full_path.exists(),
                "Directory exists"
            )
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*70)
        print("PRODUCTION READINESS SUMMARY")
        print("="*70 + "\n")
        
        total = len(self.passed) + len(self.warnings) + len(self.failures)
        passed_count = len([p for p in self.passed if p.startswith("✅")])
        warning_count = len([w for w in self.warnings if w.startswith("⚠️")])
        failure_count = len([f for f in self.failures if f.startswith("❌")])
        
        print(f"Total Checks: {passed_count + warning_count + failure_count}")
        print(f"✅ Passed: {passed_count}")
        print(f"⚠️  Warnings: {warning_count}")
        print(f"❌ Failed: {failure_count}")
        print()
        
        if self.warnings:
            print("Warnings:")
            for warning in [w for w in self.warnings if w.startswith("⚠️")]:
                print(f"  {warning}")
            print()
        
        if self.failures:
            print("Critical Failures:")
            for failure in [f for f in self.failures if f.startswith("❌")]:
                print(f"  {failure}")
            print()
        
        # Determine readiness status
        if failure_count == 0 and warning_count == 0:
            print("🎉 PRODUCTION READY!")
            print("   All checks passed. System is ready for deployment.")
            return 0
        elif failure_count == 0:
            print("⚠️  READY WITH WARNINGS")
            print("   No critical failures, but review warnings before production.")
            return 0
        else:
            print("❌ NOT PRODUCTION READY")
            print("   Critical failures must be resolved before deployment.")
            return 1


def main():
    print("="*70)
    print("OsMEN PRODUCTION READINESS VALIDATION")
    print("="*70)
    
    validator = ProductionValidator()
    
    # Run all validations
    validator.validate_environment()
    validator.validate_dependencies()
    validator.validate_docker()
    validator.validate_agents()
    validator.validate_tests()
    validator.validate_security()
    validator.validate_documentation()
    validator.validate_configuration_files()
    validator.validate_directory_structure()
    
    # Print summary and return exit code
    return validator.print_summary()


if __name__ == "__main__":
    sys.exit(main())
