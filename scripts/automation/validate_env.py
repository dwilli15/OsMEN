#!/usr/bin/env python3
"""
Validation script to detect example/placeholder values in .env files.
Prevents users from accidentally using insecure example credentials in production.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict

# Patterns that indicate example/placeholder values
PLACEHOLDER_PATTERNS = [
    (r'your-.*-here', 'Generic placeholder pattern'),
    (r'changeme', 'Common placeholder password'),
    (r'example.*', 'Example value pattern'),
    (r'placeholder', 'Placeholder text'),
    (r'replace-this', 'Replacement indicator'),
    (r'TODO', 'Todo marker'),
    (r'FIXME', 'Fix me marker'),
    (r'xxx+', 'XXX placeholder'),
]

# Known insecure default values
INSECURE_DEFAULTS = {
    'admin': 'Common default password',
    'password': 'Common default password',
    'secret': 'Common default secret',
    '123456': 'Common default password',
    'postgres': 'Default PostgreSQL password',
    'redis': 'Default Redis password',
}

# Configuration keys that should NOT have placeholder values
CRITICAL_KEYS = [
    'PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'API_KEY',
    'PRIVATE_KEY', 'CREDENTIALS', 'AUTH'
]


class EnvValidator:
    """Validates .env files for placeholder and insecure values."""
    
    def __init__(self, env_file: Path):
        self.env_file = env_file
        self.issues: List[Dict] = []
        
    def validate(self) -> Tuple[bool, List[Dict]]:
        """
        Validate the .env file.
        
        Returns:
            Tuple of (is_valid, list of issues)
        """
        if not self.env_file.exists():
            return True, []  # No .env file is okay (user hasn't set up yet)
            
        with open(self.env_file, 'r') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Parse key=value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                value = value.strip('"').strip("'")
                
                self._check_value(key, value, line_num)
                
        return len(self.issues) == 0, self.issues
    
    def _check_value(self, key: str, value: str, line_num: int):
        """Check a single key-value pair for issues."""
        if not value:
            # Empty values are okay
            return
            
        # Check if this is a critical key
        is_critical = any(pattern in key.upper() for pattern in CRITICAL_KEYS)
        
        # Check for placeholder patterns
        for pattern, description in PLACEHOLDER_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                self.issues.append({
                    'line': line_num,
                    'key': key,
                    'value': value,
                    'issue': f'Placeholder value detected: {description}',
                    'severity': 'CRITICAL' if is_critical else 'WARNING'
                })
                return
        
        # Check for insecure defaults
        value_lower = value.lower()
        for insecure, description in INSECURE_DEFAULTS.items():
            if value_lower == insecure.lower():
                self.issues.append({
                    'line': line_num,
                    'key': key,
                    'value': value,
                    'issue': f'Insecure default value: {description}',
                    'severity': 'CRITICAL' if is_critical else 'WARNING'
                })
                return


def main():
    """Main entry point."""
    # Check current directory for .env
    env_path = Path('.env')
    
    print("🔍 OsMEN .env Validation")
    print("=" * 60)
    print()
    
    if not env_path.exists():
        print("ℹ️  No .env file found in current directory.")
        print("   This is expected if you haven't set up OsMEN yet.")
        print()
        print("   To get started:")
        print("   1. Copy .env.example to .env")
        print("   2. Edit .env with your actual credentials")
        print("   3. Run this validation again")
        sys.exit(0)
    
    print(f"📄 Validating: {env_path.absolute()}")
    print()
    
    validator = EnvValidator(env_path)
    is_valid, issues = validator.validate()
    
    if is_valid:
        print("✅ PASS: No placeholder or insecure values detected!")
        print()
        print("Your .env file appears to be properly configured.")
        sys.exit(0)
    
    # Report issues
    critical_issues = [i for i in issues if i['severity'] == 'CRITICAL']
    warnings = [i for i in issues if i['severity'] == 'WARNING']
    
    if critical_issues:
        print("❌ CRITICAL ISSUES DETECTED")
        print()
        for issue in critical_issues:
            print(f"  Line {issue['line']}: {issue['key']}")
            print(f"  Value: {issue['value']}")
            print(f"  Problem: {issue['issue']}")
            print()
    
    if warnings:
        print("⚠️  WARNINGS")
        print()
        for issue in warnings:
            print(f"  Line {issue['line']}: {issue['key']}")
            print(f"  Value: {issue['value']}")
            print(f"  Problem: {issue['issue']}")
            print()
    
    print("=" * 60)
    print()
    print("⚠️  SECURITY RISK: Placeholder values detected in .env!")
    print()
    print("These values MUST be changed before using OsMEN:")
    print()
    print("1. Review the issues above")
    print("2. Edit .env with real, secure values")
    print("3. Generate strong passwords:")
    print("   python3 -c \"import secrets; print(secrets.token_urlsafe(32))\"")
    print("4. Never use example values in production!")
    print()
    print("Run this script again after making changes.")
    
    sys.exit(1 if critical_issues else 0)


if __name__ == '__main__':
    main()
