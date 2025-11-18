#!/usr/bin/env python3
"""
Automated backup validation script for OsMEN.
Verifies backup integrity and completeness.
"""

import os
import sys
import json
import tarfile
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class BackupValidator:
    """Validates OsMEN backup files."""
    
    def __init__(self, backup_file: Path):
        self.backup_file = backup_file
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.manifest: Dict = {}
        
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate the backup file.
        
        Returns:
            Tuple of (is_valid, issues, warnings)
        """
        # Check file exists
        if not self.backup_file.exists():
            self.issues.append(f"Backup file not found: {self.backup_file}")
            return False, self.issues, self.warnings
        
        # Check file size
        file_size = self.backup_file.stat().st_size
        if file_size == 0:
            self.issues.append("Backup file is empty (0 bytes)")
            return False, self.issues, self.warnings
        
        if file_size < 1024:  # Less than 1KB
            self.warnings.append(f"Backup file is very small ({file_size} bytes)")
        
        # Check if it's a valid tar.gz file
        try:
            with tarfile.open(self.backup_file, 'r:gz') as tar:
                members = tar.getmembers()
                
                if len(members) == 0:
                    self.issues.append("Backup archive is empty")
                    return False, self.issues, self.warnings
                
                # Check for manifest
                manifest_found = False
                for member in members:
                    if member.name.endswith('manifest.json'):
                        manifest_found = True
                        try:
                            manifest_file = tar.extractfile(member)
                            if manifest_file:
                                self.manifest = json.load(manifest_file)
                        except Exception as e:
                            self.warnings.append(f"Could not read manifest: {e}")
                        break
                
                if not manifest_found:
                    self.warnings.append("No manifest.json found in backup")
                
                # Check for required components
                self._check_required_components(members)
                
        except tarfile.TarError as e:
            self.issues.append(f"Invalid tar.gz archive: {e}")
            return False, self.issues, self.warnings
        except Exception as e:
            self.issues.append(f"Error reading backup: {e}")
            return False, self.issues, self.warnings
        
        return len(self.issues) == 0, self.issues, self.warnings
    
    def _check_required_components(self, members: List):
        """Check that backup contains all required components."""
        member_names = [m.name for m in members]
        
        # Required components
        required = {
            'postgres': False,
            'config': False,
        }
        
        # Recommended components
        recommended = {
            'qdrant': False,
            'n8n': False,
            'langflow': False,
        }
        
        for name in member_names:
            if 'postgres' in name.lower() or '.sql' in name.lower():
                required['postgres'] = True
            if 'config' in name.lower() or '.env' in name.lower():
                required['config'] = True
            if 'qdrant' in name.lower():
                recommended['qdrant'] = True
            if 'n8n' in name.lower():
                recommended['n8n'] = True
            if 'langflow' in name.lower() or 'flows' in name.lower():
                recommended['langflow'] = True
        
        # Check required
        for component, found in required.items():
            if not found:
                self.issues.append(f"Required component missing: {component}")
        
        # Check recommended
        for component, found in recommended.items():
            if not found:
                self.warnings.append(f"Recommended component missing: {component}")
    
    def calculate_checksum(self) -> str:
        """Calculate SHA256 checksum of backup file."""
        sha256 = hashlib.sha256()
        with open(self.backup_file, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


def format_size(bytes_size: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def main():
    """Main entry point."""
    print("🔍 OsMEN Backup Validation")
    print("=" * 70)
    print()
    
    # Check for backup file argument
    if len(sys.argv) < 2:
        print("Usage: python3 validate_backup.py <backup_file>")
        print()
        print("Example:")
        print("  python3 validate_backup.py backups/backup_20241118.tar.gz")
        sys.exit(1)
    
    backup_path = Path(sys.argv[1])
    
    print(f"📄 Validating: {backup_path}")
    print()
    
    validator = BackupValidator(backup_path)
    is_valid, issues, warnings = validator.validate()
    
    # Print results
    if backup_path.exists():
        file_size = backup_path.stat().st_size
        print(f"Size: {format_size(file_size)}")
        print(f"Created: {datetime.fromtimestamp(backup_path.stat().st_mtime)}")
        
        # Calculate checksum
        print(f"SHA256: {validator.calculate_checksum()}")
        print()
    
    if validator.manifest:
        print("Manifest Information:")
        print(f"  Timestamp: {validator.manifest.get('timestamp', 'Unknown')}")
        print(f"  Version: {validator.manifest.get('version', 'Unknown')}")
        components = validator.manifest.get('components', [])
        if components:
            print(f"  Components: {', '.join(components)}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    if issues:
        print("❌ ISSUES DETECTED:")
        for issue in issues:
            print(f"  - {issue}")
        print()
        print("=" * 70)
        print()
        print("❌ VALIDATION FAILED")
        print()
        print("This backup file has critical issues and may not be restorable.")
        print("Action required:")
        print("1. Review the issues above")
        print("2. Create a new backup")
        print("3. Verify new backup with this tool")
        sys.exit(1)
    
    print("=" * 70)
    print()
    print("✅ VALIDATION PASSED")
    print()
    print("Backup file appears to be valid and complete.")
    
    if warnings:
        print()
        print("Note: Some warnings were detected. Review them to ensure")
        print("all expected components are backed up.")
    
    sys.exit(0)


if __name__ == '__main__':
    main()
