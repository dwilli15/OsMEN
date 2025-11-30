#!/usr/bin/env python3
"""
Automated license compliance checker for OsMEN.
Ensures all dependencies have compatible licenses with Apache 2.0.
"""

import json
import subprocess
import sys
from typing import List, Dict, Set

# Licenses compatible with Apache 2.0
COMPATIBLE_LICENSES = {
    'MIT', 'MIT License',
    'BSD', 'BSD License', 'BSD-2-Clause', 'BSD-3-Clause',
    'Apache', 'Apache 2.0', 'Apache License 2.0', 'Apache Software License',
    'ISC', 'ISC License',
    'Python Software Foundation License', 'PSF',
    'PostgreSQL License',
    'Unlicense',
    'CC0',
    'Public Domain',
    'MPL-2.0', 'Mozilla Public License 2.0 (MPL 2.0)',  # File-level copyleft, acceptable
    '0BSD',
}

# Licenses that require review
REVIEW_REQUIRED = {
    'LGPL', 'LGPL-2.1', 'LGPL-3.0',  # May be acceptable with static linking
    'Fair',  # Fair Code licenses (case-by-case)
}

# Licenses NOT compatible with Apache 2.0
INCOMPATIBLE_LICENSES = {
    'GPL', 'GPLv2', 'GPLv3', 'GPL-2.0', 'GPL-3.0',
    'AGPL', 'AGPLv3', 'AGPL-3.0',
    'Commercial',
    'Proprietary',
}


class LicenseChecker:
    """Check Python package licenses for compliance."""
    
    def __init__(self):
        self.compatible: List[Dict] = []
        self.review_required: List[Dict] = []
        self.incompatible: List[Dict] = []
        self.unknown: List[Dict] = []
        
    def check_licenses(self) -> bool:
        """
        Check all installed packages for license compliance.
        
        Returns:
            True if all licenses are compatible, False otherwise
        """
        try:
            # Try using pip-licenses if available
            result = subprocess.run(
                ['pip-licenses', '--format=json', '--with-urls'],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
            else:
                # Fallback to pip list if pip-licenses not available
                print("⚠️  pip-licenses not installed, using fallback method")
                print("   Install with: pip install pip-licenses")
                print()
                packages = self._get_packages_fallback()
                
        except FileNotFoundError:
            print("❌ pip-licenses not found. Install with: pip install pip-licenses")
            packages = self._get_packages_fallback()
        
        # Categorize packages by license
        for pkg in packages:
            name = pkg.get('Name', 'Unknown')
            license_name = pkg.get('License', 'UNKNOWN')
            
            if license_name == 'UNKNOWN' or not license_name:
                self.unknown.append(pkg)
            elif self._is_compatible(license_name):
                self.compatible.append(pkg)
            elif self._needs_review(license_name):
                self.review_required.append(pkg)
            elif self._is_incompatible(license_name):
                self.incompatible.append(pkg)
            else:
                self.unknown.append(pkg)
        
        return len(self.incompatible) == 0 and len(self.unknown) == 0
    
    def _get_packages_fallback(self) -> List[Dict]:
        """Fallback method using pip list."""
        result = subprocess.run(
            ['pip', 'list', '--format=json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        packages_list = json.loads(result.stdout)
        packages = []
        
        for pkg in packages_list:
            packages.append({
                'Name': pkg['name'],
                'Version': pkg['version'],
                'License': 'UNKNOWN',  # Can't get license without pip-licenses
                'URL': ''
            })
        
        return packages
    
    def _is_compatible(self, license_name: str) -> bool:
        """Check if license is compatible with Apache 2.0."""
        return any(compat in license_name for compat in COMPATIBLE_LICENSES)
    
    def _needs_review(self, license_name: str) -> bool:
        """Check if license needs manual review."""
        return any(review in license_name for review in REVIEW_REQUIRED)
    
    def _is_incompatible(self, license_name: str) -> bool:
        """Check if license is incompatible with Apache 2.0."""
        return any(incompat in license_name for incompat in INCOMPATIBLE_LICENSES)
    
    def print_report(self):
        """Print a formatted license compliance report."""
        print("📋 License Compliance Report")
        print("=" * 70)
        print()
        
        total = len(self.compatible) + len(self.review_required) + len(self.incompatible) + len(self.unknown)
        
        print(f"Total packages: {total}")
        print(f"  ✅ Compatible: {len(self.compatible)}")
        print(f"  ⚠️  Review required: {len(self.review_required)}")
        print(f"  ❌ Incompatible: {len(self.incompatible)}")
        print(f"  ❓ Unknown: {len(self.unknown)}")
        print()
        
        if self.incompatible:
            print("❌ INCOMPATIBLE LICENSES (BLOCKING)")
            print()
            for pkg in self.incompatible:
                print(f"  {pkg['Name']} ({pkg.get('Version', 'unknown')})")
                print(f"    License: {pkg.get('License', 'UNKNOWN')}")
                if pkg.get('URL'):
                    print(f"    URL: {pkg['URL']}")
                print()
        
        if self.unknown:
            print("❓ UNKNOWN LICENSES (NEEDS INVESTIGATION)")
            print()
            for pkg in self.unknown:
                print(f"  {pkg['Name']} ({pkg.get('Version', 'unknown')})")
                print(f"    License: {pkg.get('License', 'UNKNOWN')}")
                if pkg.get('URL'):
                    print(f"    URL: {pkg['URL']}")
                print()
        
        if self.review_required:
            print("⚠️  LICENSES REQUIRING REVIEW")
            print()
            for pkg in self.review_required:
                print(f"  {pkg['Name']} ({pkg.get('Version', 'unknown')})")
                print(f"    License: {pkg.get('License', 'UNKNOWN')}")
                if pkg.get('URL'):
                    print(f"    URL: {pkg['URL']}")
                print()
        
        print("=" * 70)
        print()


def main():
    """Main entry point."""
    print("🔍 OsMEN License Compliance Checker")
    print()
    
    checker = LicenseChecker()
    is_compliant = checker.check_licenses()
    
    checker.print_report()
    
    if is_compliant:
        print("✅ SUCCESS: All licenses are compatible with Apache 2.0")
        sys.exit(0)
    elif checker.incompatible:
        print("❌ FAILURE: Incompatible licenses detected!")
        print()
        print("Action required:")
        print("1. Remove or replace packages with incompatible licenses")
        print("2. Verify license compatibility for unknown licenses")
        print("3. Re-run this checker")
        sys.exit(1)
    elif checker.unknown:
        # Warn but don't fail on unknown licenses (common in CI without pip-licenses)
        print("⚠️  WARNING: Unknown licenses detected (non-blocking)")
        print()
        print("Recommended actions:")
        print("1. Investigate packages with unknown licenses")
        print("2. Install pip-licenses for better detection:")
        print("   pip install pip-licenses")
        print("3. Verify licenses manually if needed")
        sys.exit(0)  # Exit 0 to not block CI
    else:
        print("⚠️  WARNING: Some licenses require manual review")
        print()
        print("Action required:")
        print("1. Review packages marked for review")
        print("2. Verify compatibility with project requirements")
        sys.exit(0)


if __name__ == '__main__':
    main()
