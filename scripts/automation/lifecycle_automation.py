#!/usr/bin/env python3
"""
Workspace Lifecycle Automation

Implements automated file lifecycle management:
- Weekly review of workspace files
- 90-day archive prompts for old files
- Automatic file aging rules
- Cleanup automations

This script can be run manually or scheduled via cron/Task Scheduler.
"""

import json
import logging
import os
import shutil
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class LifecycleConfig:
    """Configuration for lifecycle management"""

    # Workspace directories
    incoming_path: str = "workspace/incoming"
    staging_path: str = "workspace/staging"
    pending_review_path: str = "workspace/pending_review"
    archive_path: str = "workspace/archive"

    # Age thresholds (in days)
    incoming_max_age: int = 30
    staging_max_age: int = 14
    surface_inactive_days: int = 10
    archive_prompt_days: int = 90

    # Actions
    auto_move_expired: bool = True
    create_archive_prompts: bool = True
    log_actions: bool = True


@dataclass
class FileInfo:
    """Information about a file for lifecycle management"""

    path: str
    relative_path: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    accessed_at: datetime
    age_days: float
    location: str  # incoming, staging, pending_review


@dataclass
class LifecycleAction:
    """Record of a lifecycle action"""

    timestamp: str
    action: str  # moved, archived, deleted, prompted
    file_path: str
    from_location: str
    to_location: Optional[str]
    reason: str
    success: bool


class WorkspaceLifecycleManager:
    """
    Manages workspace file lifecycle automation.

    Responsibilities:
    - Track file ages across workspace directories
    - Move files based on age thresholds
    - Generate archive prompts for old files
    - Maintain audit log of all actions
    """

    def __init__(
        self, base_path: Optional[Path] = None, config: Optional[LifecycleConfig] = None
    ):
        """Initialize the lifecycle manager."""
        self.base_path = base_path or Path(__file__).parent.parent.parent
        self.config = config or self._load_config()

        # Resolve paths
        self.incoming = self.base_path / self.config.incoming_path
        self.staging = self.base_path / self.config.staging_path
        self.pending_review = self.base_path / self.config.pending_review_path
        self.archive = self.base_path / self.config.archive_path

        # Ensure directories exist
        for path in [self.incoming, self.staging, self.pending_review, self.archive]:
            path.mkdir(parents=True, exist_ok=True)

        # Action history
        self.actions: List[LifecycleAction] = []

        logger.info(f"WorkspaceLifecycleManager initialized at {self.base_path}")

    def _load_config(self) -> LifecycleConfig:
        """Load configuration from policies file."""
        policies_path = self.base_path / "infrastructure" / "profiles" / "policies.json"

        if policies_path.exists():
            with open(policies_path, "r") as f:
                policies = json.load(f)

            lifecycle = policies.get("workspace_policies", {}).get(
                "workspace_lifecycle", {}
            )

            return LifecycleConfig(
                incoming_max_age=lifecycle.get("incoming", {}).get("max_age_days", 30),
                staging_max_age=lifecycle.get("staging", {}).get("max_age_days", 14),
                surface_inactive_days=lifecycle.get("pending_review", {}).get(
                    "surface_inactive_days", 10
                ),
                archive_prompt_days=lifecycle.get("pending_review", {}).get(
                    "archive_prompt_days", 90
                ),
            )

        return LifecycleConfig()

    # =========================================================================
    # File Scanning
    # =========================================================================

    def scan_workspace(self) -> Dict[str, List[FileInfo]]:
        """
        Scan all workspace directories and return file information.

        Returns:
            Dictionary mapping location to list of FileInfo objects
        """
        results = {"incoming": [], "staging": [], "pending_review": []}

        directories = {
            "incoming": self.incoming,
            "staging": self.staging,
            "pending_review": self.pending_review,
        }

        now = time.time()

        for location, dir_path in directories.items():
            if not dir_path.exists():
                continue

            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    stat = file_path.stat()

                    file_info = FileInfo(
                        path=str(file_path),
                        relative_path=str(file_path.relative_to(dir_path)),
                        size_bytes=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        modified_at=datetime.fromtimestamp(stat.st_mtime),
                        accessed_at=datetime.fromtimestamp(stat.st_atime),
                        age_days=(now - stat.st_mtime) / 86400,
                        location=location,
                    )

                    results[location].append(file_info)

        return results

    def get_expired_files(self) -> Dict[str, List[FileInfo]]:
        """
        Get files that have exceeded their age threshold.

        Returns:
            Dictionary mapping location to list of expired FileInfo objects
        """
        workspace = self.scan_workspace()
        expired = {"incoming": [], "staging": [], "pending_review": []}

        # Check incoming
        for file in workspace["incoming"]:
            if file.age_days > self.config.incoming_max_age:
                expired["incoming"].append(file)

        # Check staging
        for file in workspace["staging"]:
            if file.age_days > self.config.staging_max_age:
                expired["staging"].append(file)

        # Check pending_review for archive candidates
        for file in workspace["pending_review"]:
            if file.age_days > self.config.archive_prompt_days:
                expired["pending_review"].append(file)

        return expired

    def get_inactive_files(self) -> List[FileInfo]:
        """
        Get files that need surfacing for review (inactive).

        Returns:
            List of FileInfo objects that need attention
        """
        workspace = self.scan_workspace()
        inactive = []

        for location in ["incoming", "staging", "pending_review"]:
            for file in workspace[location]:
                if file.age_days > self.config.surface_inactive_days:
                    inactive.append(file)

        return inactive

    # =========================================================================
    # Lifecycle Actions
    # =========================================================================

    def move_to_pending_review(self, file_info: FileInfo) -> bool:
        """
        Move a file to pending_review.

        Args:
            file_info: FileInfo object for the file to move

        Returns:
            True if successful
        """
        source = Path(file_info.path)
        dest = self.pending_review / file_info.relative_path

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))

            self._log_action(
                LifecycleAction(
                    timestamp=datetime.now().isoformat(),
                    action="moved",
                    file_path=file_info.path,
                    from_location=file_info.location,
                    to_location="pending_review",
                    reason=f"Exceeded {file_info.location} max age ({file_info.age_days:.1f} days)",
                    success=True,
                )
            )

            logger.info(f"Moved {file_info.relative_path} to pending_review")
            return True

        except Exception as e:
            logger.error(f"Failed to move {file_info.path}: {e}")
            self._log_action(
                LifecycleAction(
                    timestamp=datetime.now().isoformat(),
                    action="moved",
                    file_path=file_info.path,
                    from_location=file_info.location,
                    to_location="pending_review",
                    reason=str(e),
                    success=False,
                )
            )
            return False

    def archive_file(
        self, file_info: FileInfo, archive_name: Optional[str] = None
    ) -> bool:
        """
        Archive a file.

        Args:
            file_info: FileInfo object for the file to archive
            archive_name: Optional custom archive folder name

        Returns:
            True if successful
        """
        source = Path(file_info.path)

        # Create dated archive folder
        if archive_name is None:
            archive_name = datetime.now().strftime("%Y-%m")

        dest = self.archive / archive_name / file_info.relative_path

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))

            self._log_action(
                LifecycleAction(
                    timestamp=datetime.now().isoformat(),
                    action="archived",
                    file_path=file_info.path,
                    from_location=file_info.location,
                    to_location=f"archive/{archive_name}",
                    reason=f"Archived after {file_info.age_days:.1f} days",
                    success=True,
                )
            )

            logger.info(f"Archived {file_info.relative_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to archive {file_info.path}: {e}")
            return False

    def create_archive_prompt(self, files: List[FileInfo]) -> Dict[str, Any]:
        """
        Create an archive prompt for user review.

        Args:
            files: List of FileInfo objects to include in prompt

        Returns:
            Prompt data dictionary
        """
        prompt = {
            "id": f"archive_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "files": [
                {
                    "path": f.relative_path,
                    "location": f.location,
                    "age_days": round(f.age_days, 1),
                    "size_bytes": f.size_bytes,
                    "modified_at": f.modified_at.isoformat(),
                }
                for f in files
            ],
            "total_files": len(files),
            "total_size": sum(f.size_bytes for f in files),
            "message": f"{len(files)} files are ready for archival (90+ days old)",
        }

        # Save to approval queue
        queue_file = (
            self.base_path / "infrastructure" / "queues" / "archive_prompts.json"
        )

        try:
            existing = []
            if queue_file.exists():
                with open(queue_file, "r") as f:
                    existing = json.load(f)

            existing.append(prompt)

            with open(queue_file, "w") as f:
                json.dump(existing, f, indent=2)

            logger.info(f"Created archive prompt for {len(files)} files")

        except Exception as e:
            logger.error(f"Failed to save archive prompt: {e}")

        return prompt

    # =========================================================================
    # Automation Runs
    # =========================================================================

    def run_weekly_review(self) -> Dict[str, Any]:
        """
        Run weekly review automation.

        Returns:
            Summary of actions taken
        """
        logger.info("Starting weekly review...")

        summary = {
            "timestamp": datetime.now().isoformat(),
            "type": "weekly_review",
            "files_scanned": 0,
            "files_moved": 0,
            "prompts_created": 0,
            "errors": 0,
        }

        workspace = self.scan_workspace()

        for files in workspace.values():
            summary["files_scanned"] += len(files)

        # Move expired files
        expired = self.get_expired_files()

        for file in expired["incoming"]:
            if self.move_to_pending_review(file):
                summary["files_moved"] += 1
            else:
                summary["errors"] += 1

        for file in expired["staging"]:
            if self.move_to_pending_review(file):
                summary["files_moved"] += 1
            else:
                summary["errors"] += 1

        # Create archive prompts for old pending_review files
        if expired["pending_review"] and self.config.create_archive_prompts:
            self.create_archive_prompt(expired["pending_review"])
            summary["prompts_created"] += 1

        # Log summary
        self._log_summary(summary)

        logger.info(
            f"Weekly review complete: {summary['files_moved']} moved, {summary['prompts_created']} prompts"
        )
        return summary

    def run_daily_cleanup(self) -> Dict[str, Any]:
        """
        Run daily cleanup automation.

        Returns:
            Summary of actions taken
        """
        logger.info("Starting daily cleanup...")

        summary = {
            "timestamp": datetime.now().isoformat(),
            "type": "daily_cleanup",
            "empty_dirs_removed": 0,
            "temp_files_removed": 0,
        }

        # Remove empty directories
        for base_dir in [self.incoming, self.staging, self.pending_review]:
            for dir_path in sorted(base_dir.rglob("*"), reverse=True):
                if dir_path.is_dir():
                    try:
                        dir_path.rmdir()  # Only removes if empty
                        summary["empty_dirs_removed"] += 1
                        logger.info(f"Removed empty directory: {dir_path}")
                    except OSError:
                        pass  # Directory not empty

        # Remove temp files (*.tmp, *.bak, ~*)
        temp_patterns = ["*.tmp", "*.bak", "~*", "*.swp"]
        for pattern in temp_patterns:
            for base_dir in [self.incoming, self.staging]:
                for temp_file in base_dir.rglob(pattern):
                    if temp_file.is_file():
                        try:
                            temp_file.unlink()
                            summary["temp_files_removed"] += 1
                            logger.info(f"Removed temp file: {temp_file}")
                        except Exception as e:
                            logger.warning(f"Failed to remove temp file: {e}")

        self._log_summary(summary)
        logger.info(
            f"Daily cleanup complete: {summary['empty_dirs_removed']} dirs, {summary['temp_files_removed']} temp files"
        )
        return summary

    # =========================================================================
    # Logging and Status
    # =========================================================================

    def _log_action(self, action: LifecycleAction):
        """Log a lifecycle action."""
        self.actions.append(action)

        if self.config.log_actions:
            log_file = self.base_path / "logs" / "lifecycle_actions.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)

            with open(log_file, "a") as f:
                f.write(json.dumps(asdict(action)) + "\n")

    def _log_summary(self, summary: Dict[str, Any]):
        """Log a run summary."""
        log_file = self.base_path / "logs" / "lifecycle_summaries.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "a") as f:
            f.write(json.dumps(summary) + "\n")

    def get_status(self) -> Dict[str, Any]:
        """Get current lifecycle status."""
        workspace = self.scan_workspace()
        expired = self.get_expired_files()

        return {
            "timestamp": datetime.now().isoformat(),
            "workspace_files": {
                location: len(files) for location, files in workspace.items()
            },
            "expired_files": {
                location: len(files) for location, files in expired.items()
            },
            "config": asdict(self.config),
            "recent_actions": len(self.actions),
        }


# =============================================================================
# CLI Entry Point
# =============================================================================


def main():
    """Run lifecycle automation from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Workspace Lifecycle Automation")
    parser.add_argument(
        "--action",
        choices=["status", "weekly", "daily", "scan"],
        default="status",
        help="Action to perform",
    )
    parser.add_argument("--base-path", type=str, help="Base path for workspace")

    args = parser.parse_args()

    base_path = Path(args.base_path) if args.base_path else None
    manager = WorkspaceLifecycleManager(base_path=base_path)

    if args.action == "status":
        status = manager.get_status()
        print(json.dumps(status, indent=2))

    elif args.action == "weekly":
        summary = manager.run_weekly_review()
        print(json.dumps(summary, indent=2))

    elif args.action == "daily":
        summary = manager.run_daily_cleanup()
        print(json.dumps(summary, indent=2))

    elif args.action == "scan":
        workspace = manager.scan_workspace()
        for location, files in workspace.items():
            print(f"\n{location.upper()} ({len(files)} files):")
            for f in files[:10]:
                print(f"  - {f.relative_path} ({f.age_days:.1f} days)")
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more")


if __name__ == "__main__":
    main()
