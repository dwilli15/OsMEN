#!/usr/bin/env python3
"""
OsMEN Security Validation Script
Validates environment configuration, secrets, and security settings
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import re


class SecurityValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
        self.project_root = Path(__file__).parent.parent.parent
        
    def add_issue(self, message: str):
        """Add a security issue (critical)"""
        self.issues.append(f"❌ ISSUE: {message}")
        
    def add_warning(self, message: str):
        """Add a security warning (non-critical)"""
        self.warnings.append(f"⚠️  WARNING: {message}")
        
    def add_passed(self, message: str):
        """Add a passed check"""
        self.passed.append(f"✅ {message}")
        
    def check_env_file(self) -> bool:
        """Check if .env file exists and is properly configured"""
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if not env_file.exists():
            self.add_issue(".env file not found. Copy .env.example to .env")
            return False
            
        self.add_passed(".env file exists")
        
        # Check for default/example values
        with open(env_file) as f:
            content = f.read()
            
        # Check for unchanged default passwords
        dangerous_defaults = [
            ("changeme", "N8N_BASIC_AUTH_PASSWORD still set to default"),
            ("your_openai_api_key_here", "OpenAI API key not configured"),
            ("your_github_token_here", "GitHub token not configured"),
            ("your_aws_access_key_here", "AWS access key not configured"),
            ("your_anthropic_api_key_here", "Anthropic API key not configured"),
        ]
        
        for default, message in dangerous_defaults:
            if default in content:
                self.add_warning(message)
        
        # Check for secrets in plaintext (warn about exposure risk)
        if "API_KEY=" in content or "PASSWORD=" in content:
            self.add_warning("Secrets found in .env - ensure this file is in .gitignore")
            
        return True
        
    def check_gitignore(self) -> bool:
        """Check if sensitive files are in .gitignore"""
        gitignore = self.project_root / ".gitignore"
        
        if not gitignore.exists():
            self.add_issue(".gitignore file not found")
            return False
            
        with open(gitignore) as f:
            content = f.read()
            
        required_patterns = [
            ".env",
            "*.key",
            "*.pem",
            "credentials",
            "secrets",
        ]
        
        missing = []
        for pattern in required_patterns:
            if pattern not in content:
                missing.append(pattern)
                
        if missing:
            self.add_warning(f".gitignore missing patterns: {', '.join(missing)}")
        else:
            self.add_passed(".gitignore properly configured")
            
        return True
        
    def check_docker_compose_security(self) -> bool:
        """Check Docker Compose for security issues"""
        compose_file = self.project_root / "docker-compose.yml"
        
        if not compose_file.exists():
            self.add_issue("docker-compose.yml not found")
            return False
            
        with open(compose_file) as f:
            content = f.read()
            
        # Check for hardcoded passwords (excluding environment variable references)
        # Look for PASSWORD= followed by a literal value, not ${VAR} syntax
        password_patterns = [
            r"PASSWORD=['\"]?\w+['\"]?\s*$",  # PASSWORD=literal at end of line
        ]
        
        has_hardcoded_password = False
        for line in content.split('\n'):
            # Skip lines that use environment variable syntax
            if 'PASSWORD=' in line and '${' not in line and 'PASSWORD:-' not in line:
                # Check if it's a direct password assignment
                if re.search(r"PASSWORD=['\"]?[a-zA-Z0-9_-]+['\"]?\s*(?:#|$)", line):
                    has_hardcoded_password = True
                    break
        
        if has_hardcoded_password:
            self.add_issue("Hardcoded password found in docker-compose.yml")
                
        # Check for exposed ports without restrictions
        if "0.0.0.0:" in content:
            self.add_warning("Services exposed on 0.0.0.0 - consider restricting to 127.0.0.1")
            
        self.add_passed("docker-compose.yml security check passed")
        return True
        
    def check_file_permissions(self) -> bool:
        """Check for overly permissive file permissions"""
        sensitive_files = [
            ".env",
            "config/firewall_baseline.yaml",
        ]
        
        issues_found = False
        for file_path in sensitive_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                # On Unix-like systems, check permissions
                if hasattr(os, 'stat'):
                    mode = os.stat(full_path).st_mode
                    # Check if world-readable (others have read permission)
                    if mode & 0o004:
                        self.add_warning(f"{file_path} is world-readable")
                        issues_found = True
                        
        if not issues_found:
            self.add_passed("File permissions check passed")
            
        return True
        
    def check_default_credentials(self) -> bool:
        """Check for default credentials in configuration"""
        # Check n8n default credentials
        env_file = self.project_root / ".env"
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
                
            if "N8N_BASIC_AUTH_PASSWORD=changeme" in content:
                self.add_issue("n8n still using default password 'changeme' - CHANGE THIS")
                return False
                
        self.add_passed("No default credentials detected")
        return True
        
    def check_secret_exposure(self) -> bool:
        """Check if secrets might be committed to git"""
        # Check git status for .env file
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                cwd=self.project_root,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.decode()
                if ".env" in output:
                    self.add_issue(".env file is staged or modified - DO NOT COMMIT")
                    return False
                    
        except Exception:
            # Git not available or error - skip check
            pass
            
        self.add_passed("No secrets detected in git staging")
        return True
        
    def check_required_directories(self) -> bool:
        """Check if required directories exist with proper setup"""
        required_dirs = [
            ("logs", ".gitkeep or .gitignore entry"),
            ("config", "configuration files"),
            ("content/inbox", "content staging"),
            ("content/output", "content delivery"),
        ]
        
        for dir_path, purpose in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                self.add_warning(f"Directory {dir_path} not found (needed for {purpose})")
            else:
                self.add_passed(f"Directory {dir_path} exists")
                
        return True
        
    def check_logging_configuration(self) -> bool:
        """Check if logging is properly configured"""
        logs_dir = self.project_root / "logs"
        
        if not logs_dir.exists():
            self.add_warning("logs/ directory not found - create it for audit trails")
            return False
            
        # Check if logs directory is in .gitignore
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            with open(gitignore) as f:
                if "logs/" not in f.read():
                    self.add_warning("logs/ directory should be in .gitignore")
                    
        self.add_passed("Logging configuration check passed")
        return True
        
    def print_results(self):
        """Print all results"""
        print("\n" + "="*70)
        print("OsMEN Security Validation Report")
        print("="*70 + "\n")
        
        if self.passed:
            print("✅ Passed Checks:")
            for item in self.passed:
                print(f"  {item}")
            print()
            
        if self.warnings:
            print("⚠️  Warnings:")
            for item in self.warnings:
                print(f"  {item}")
            print()
            
        if self.issues:
            print("❌ Critical Issues:")
            for item in self.issues:
                print(f"  {item}")
            print()
            
        print("="*70)
        print(f"Summary: {len(self.passed)} passed, {len(self.warnings)} warnings, {len(self.issues)} issues")
        print("="*70)
        
        if self.issues:
            print("\n🚨 CRITICAL: Fix all issues before deploying to production!")
            return 1
        elif self.warnings:
            print("\n⚠️  WARNINGS: Review warnings for security improvements")
            return 0
        else:
            print("\n✅ PASSED: All security checks passed!")
            return 0


def main():
    """Run all security validation checks"""
    validator = SecurityValidator()
    
    print("🔒 Running OsMEN Security Validation...\n")
    
    # Run all checks
    validator.check_env_file()
    validator.check_gitignore()
    validator.check_docker_compose_security()
    validator.check_file_permissions()
    validator.check_default_credentials()
    validator.check_secret_exposure()
    validator.check_required_directories()
    validator.check_logging_configuration()
    
    # Print results
    return validator.print_results()


if __name__ == "__main__":
    sys.exit(main())
