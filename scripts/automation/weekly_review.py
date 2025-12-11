#!/usr/bin/env python3
"""
Weekly Review Script for OsMEN Workspace

Runs the full weekly review automation:
1. Scans all workspace directories
2. Moves expired files to pending_review
3. Creates archive prompts for old files
4. Generates summary report

Usage:
    python weekly_review.py              # Run review
    python weekly_review.py --dry-run    # Preview without changes
    python weekly_review.py --report     # Generate report only

Schedule with Task Scheduler (Windows) or cron (Linux):
    # Run every Sunday at 2 AM
    0 2 * * 0 cd /path/to/OsMEN && python scripts/automation/weekly_review.py
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.automation.lifecycle_automation import WorkspaceLifecycleManager


def generate_report(manager: WorkspaceLifecycleManager) -> str:
    """Generate a human-readable report."""
    workspace = manager.scan_workspace()
    expired = manager.get_expired_files()
    inactive = manager.get_inactive_files()

    report = []
    report.append("=" * 60)
    report.append("OsMEN Weekly Workspace Review")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)
    report.append("")

    # Summary
    total_files = sum(len(files) for files in workspace.values())
    total_expired = sum(len(files) for files in expired.values())

    report.append("📊 Summary")
    report.append("-" * 40)
    report.append(f"Total files in workspace: {total_files}")
    report.append(f"Files needing attention: {total_expired}")
    report.append(f"Inactive files: {len(inactive)}")
    report.append("")

    # By location
    report.append("📁 Files by Location")
    report.append("-" * 40)
    for location, files in workspace.items():
        if files:
            total_size = sum(f.size_bytes for f in files)
            size_mb = total_size / (1024 * 1024)
            report.append(f"  {location}: {len(files)} files ({size_mb:.2f} MB)")
    report.append("")

    # Expired files
    if any(expired.values()):
        report.append("⚠️ Expired Files (Will be moved to pending_review)")
        report.append("-" * 40)
        for location, files in expired.items():
            if files:
                report.append(
                    f"\n  {location.upper()} (>{manager.config.incoming_max_age if location == 'incoming' else manager.config.staging_max_age} days):"
                )
                for f in files[:10]:
                    report.append(f"    • {f.relative_path} ({f.age_days:.1f} days)")
                if len(files) > 10:
                    report.append(f"    ... and {len(files) - 10} more")
        report.append("")

    # Archive candidates
    archive_candidates = expired.get("pending_review", [])
    if archive_candidates:
        report.append("📦 Archive Candidates (90+ days)")
        report.append("-" * 40)
        for f in archive_candidates[:10]:
            report.append(f"  • {f.relative_path} ({f.age_days:.1f} days)")
        if len(archive_candidates) > 10:
            report.append(f"  ... and {len(archive_candidates) - 10} more")
        report.append("")

    # Recommendations
    report.append("💡 Recommendations")
    report.append("-" * 40)
    if total_expired > 0:
        report.append("  • Run full review to move expired files")
    if archive_candidates:
        report.append("  • Review archive candidates and approve archival")
    if not total_expired and not archive_candidates:
        report.append("  • ✅ Workspace is well-maintained!")
    report.append("")

    report.append("=" * 60)
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="OsMEN Weekly Workspace Review")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying"
    )
    parser.add_argument("--report", action="store_true", help="Generate report only")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--base-path", type=str, help="Override base path")

    args = parser.parse_args()

    # Initialize manager
    base_path = Path(args.base_path) if args.base_path else None
    manager = WorkspaceLifecycleManager(base_path=base_path)

    if args.report:
        # Report only
        report = generate_report(manager)
        print(report)
        return

    if args.dry_run:
        # Dry run - show what would happen
        print("🔍 DRY RUN - No changes will be made\n")
        report = generate_report(manager)
        print(report)

        expired = manager.get_expired_files()
        if any(expired.values()):
            print("\nActions that WOULD be taken:")
            for location, files in expired.items():
                for f in files:
                    print(f"  MOVE: {f.relative_path} → pending_review")
        return

    # Full run
    print("🚀 Running weekly review...\n")

    summary = manager.run_weekly_review()

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"✅ Weekly review complete!")
        print(f"   Files scanned: {summary['files_scanned']}")
        print(f"   Files moved: {summary['files_moved']}")
        print(f"   Prompts created: {summary['prompts_created']}")
        print(f"   Errors: {summary['errors']}")

        if summary["errors"] > 0:
            print(f"\n⚠️ Check logs/lifecycle_actions.jsonl for error details")


if __name__ == "__main__":
    main()
