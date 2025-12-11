#!/usr/bin/env python3
"""
Obsidian Vault Watcher and Sync System

Provides bidirectional sync between OsMEN knowledge base and Obsidian vault.
Implements watcher-based detection with permission protocols and approval queues.

Key Features:
- Watcher-based file change detection (polling or watchdog)
- Read filters: Only read notes with specific tags or from specific folders
- Write-only to exports/: Agents can only write to designated export folder
- Permission protocols: Respect agent roles and approval requirements
- Bidirectional filtered sync: Vault → Knowledge base and vice versa
"""

import hashlib
import json
import logging
import os
import re
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.obsidian.obsidian_integration import ObsidianIntegration

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SyncConfig:
    """Configuration for Obsidian sync"""

    vault_path: str
    knowledge_path: str
    export_folder: str = "OsMEN-Exports"
    read_filters: Dict[str, Any] = field(
        default_factory=lambda: {
            "folders": [],  # Empty = all folders
            "tags": ["osmen", "research", "knowledge"],  # Tags to include
            "exclude_folders": [".obsidian", ".trash", "Templates"],
        }
    )
    write_policy: str = "export_only"  # 'export_only', 'with_approval', 'unrestricted'
    poll_interval_seconds: int = 30
    sync_state_file: str = ".osmen_sync_state.json"
    enabled: bool = True


@dataclass
class FileChange:
    """Represents a detected file change"""

    path: str
    change_type: str  # 'created', 'modified', 'deleted'
    timestamp: str
    content_hash: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    needs_approval: bool = False


@dataclass
class SyncRecord:
    """Record of a sync operation"""

    timestamp: str
    direction: str  # 'vault_to_knowledge', 'knowledge_to_vault'
    file_path: str
    change_type: str
    success: bool
    error: Optional[str] = None


class ObsidianSyncWatcher:
    """
    Watcher for Obsidian vault changes with permission-aware sync.

    Responsibilities:
    - Detect changes in Obsidian vault
    - Filter notes by tags and folders for reading
    - Enforce write-only to exports folder
    - Maintain sync state between restarts
    - Provide approval queue for restricted writes
    """

    def __init__(self, config: Optional[SyncConfig] = None):
        """Initialize the sync watcher."""
        self.base_path = Path(__file__).parent.parent.parent
        self.config = config or self._load_config()

        self.vault_path = Path(self.config.vault_path)
        self.knowledge_path = Path(self.config.knowledge_path)
        self.export_path = self.vault_path / self.config.export_folder

        # Ensure export folder exists
        self.export_path.mkdir(parents=True, exist_ok=True)

        # Initialize Obsidian integration
        self.obsidian = ObsidianIntegration(str(self.vault_path))

        # Sync state tracking
        self.sync_state: Dict[str, str] = {}
        self._load_sync_state()

        # Change tracking
        self.pending_changes: List[FileChange] = []
        self.approval_queue: List[FileChange] = []
        self.sync_history: List[SyncRecord] = []

        # Watcher control
        self._running = False
        self._watcher_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[FileChange], None]] = []

        logger.info(f"ObsidianSyncWatcher initialized for vault: {self.vault_path}")

    def _load_config(self) -> SyncConfig:
        """Load sync configuration from policies."""
        policies_path = self.base_path / "infrastructure" / "profiles" / "policies.json"

        default_config = SyncConfig(
            vault_path=str(self.base_path / "obsidian-vault"),
            knowledge_path=str(self.base_path / "knowledge" / "obsidian"),
        )

        if policies_path.exists():
            with open(policies_path, "r") as f:
                policies = json.load(f)

            obsidian_config = policies.get("workspace_policies", {}).get(
                "obsidian_sync", {}
            )

            return SyncConfig(
                vault_path=obsidian_config.get("vault_path", default_config.vault_path),
                knowledge_path=obsidian_config.get(
                    "knowledge_path", default_config.knowledge_path
                ),
                export_folder=obsidian_config.get("export_folder", "OsMEN-Exports"),
                read_filters=obsidian_config.get(
                    "read_filters", default_config.read_filters
                ),
                write_policy=obsidian_config.get("write_policy", "export_only"),
                poll_interval_seconds=obsidian_config.get("poll_interval", 30),
                sync_state_file=obsidian_config.get(
                    "state_file", ".osmen_sync_state.json"
                ),
                enabled=obsidian_config.get("enabled", True),
            )

        return default_config

    def _load_sync_state(self):
        """Load sync state from file."""
        state_file = self.vault_path / self.config.sync_state_file

        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    self.sync_state = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load sync state: {e}")
                self.sync_state = {}

    def _save_sync_state(self):
        """Save sync state to file."""
        state_file = self.vault_path / self.config.sync_state_file

        try:
            with open(state_file, "w") as f:
                json.dump(self.sync_state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save sync state: {e}")

    # =========================================================================
    # Read Filtering
    # =========================================================================

    def _should_read_file(self, file_path: Path) -> bool:
        """Check if a file should be read based on filters."""
        relative_path = file_path.relative_to(self.vault_path)

        # Check excluded folders
        exclude_folders = self.config.read_filters.get("exclude_folders", [])
        for folder in exclude_folders:
            if relative_path.parts[0] == folder or folder in relative_path.parts:
                return False

        # Check allowed folders (if specified)
        allowed_folders = self.config.read_filters.get("folders", [])
        if allowed_folders:
            if not any(
                relative_path.is_relative_to(folder) for folder in allowed_folders
            ):
                return False

        # Check file content for tags (if tag filter is active)
        required_tags = self.config.read_filters.get("tags", [])
        if required_tags:
            tags = self._extract_tags_from_file(file_path)
            if not any(tag in required_tags for tag in tags):
                return False

        return True

    def _extract_tags_from_file(self, file_path: Path) -> List[str]:
        """Extract tags from a markdown file."""
        if not file_path.exists():
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract frontmatter tags
            tags = []
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    tag_match = re.search(r"tags:\s*\[(.*?)\]", frontmatter)
                    if tag_match:
                        tags.extend(
                            [
                                t.strip().strip("\"'")
                                for t in tag_match.group(1).split(",")
                            ]
                        )

            # Extract inline tags
            inline_tags = re.findall(r"(?:^|\s)#([a-zA-Z][a-zA-Z0-9_/-]*)", content)
            tags.extend(inline_tags)

            return list(set(tags))
        except Exception as e:
            logger.warning(f"Failed to extract tags from {file_path}: {e}")
            return []

    # =========================================================================
    # Write Permissions
    # =========================================================================

    def can_write(self, target_path: str, agent_id: str) -> Dict[str, Any]:
        """
        Check if an agent can write to a specific path.

        Args:
            target_path: Path where agent wants to write (relative to vault)
            agent_id: ID of the requesting agent

        Returns:
            Dict with 'allowed' bool and 'reason' string
        """
        target = Path(target_path)

        # Policy: export_only
        if self.config.write_policy == "export_only":
            if target.parts[0] == self.config.export_folder:
                return {"allowed": True, "reason": "Write to export folder allowed"}
            else:
                return {
                    "allowed": False,
                    "reason": f"Policy restricts writes to {self.config.export_folder}/ only",
                }

        # Policy: with_approval
        elif self.config.write_policy == "with_approval":
            if target.parts[0] == self.config.export_folder:
                return {
                    "allowed": True,
                    "reason": "Export folder writes always allowed",
                }
            else:
                return {
                    "allowed": False,
                    "needs_approval": True,
                    "reason": "Write to non-export folder requires user approval",
                }

        # Policy: unrestricted
        else:
            return {"allowed": True, "reason": "Unrestricted write policy"}

    def write_to_vault(
        self,
        content: str,
        filename: str,
        agent_id: str,
        subfolder: Optional[str] = None,
        frontmatter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Write content to the Obsidian vault (exports folder only).

        Args:
            content: Content to write
            filename: Name of the file (without .md extension)
            agent_id: ID of the agent performing the write
            subfolder: Optional subfolder within exports
            frontmatter: Optional frontmatter dictionary

        Returns:
            Result dict with success status
        """
        # Build target path
        if subfolder:
            target_folder = self.export_path / subfolder
        else:
            target_folder = self.export_path

        target_folder.mkdir(parents=True, exist_ok=True)

        # Add .md extension if needed
        if not filename.endswith(".md"):
            filename += ".md"

        target_path = target_folder / filename
        relative_path = target_path.relative_to(self.vault_path)

        # Check permissions
        permission = self.can_write(str(relative_path), agent_id)
        if not permission.get("allowed"):
            return {
                "success": False,
                "error": permission.get("reason"),
                "needs_approval": permission.get("needs_approval", False),
            }

        # Build content with frontmatter
        full_content = []

        if frontmatter:
            full_content.append("---")
            for key, value in frontmatter.items():
                full_content.append(f"{key}: {value}")
            full_content.append(f"created_by: {agent_id}")
            full_content.append(f"created_at: {datetime.now().isoformat()}")
            full_content.append("---")
            full_content.append("")

        full_content.append(content)

        # Write file
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write("\n".join(full_content))

            # Update sync state
            self.sync_state[str(relative_path)] = str(target_path.stat().st_mtime)
            self._save_sync_state()

            # Log sync record
            self.sync_history.append(
                SyncRecord(
                    timestamp=datetime.now().isoformat(),
                    direction="knowledge_to_vault",
                    file_path=str(relative_path),
                    change_type="created",
                    success=True,
                )
            )

            logger.info(f"Agent {agent_id} wrote to vault: {relative_path}")

            return {
                "success": True,
                "path": str(relative_path),
                "full_path": str(target_path),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Change Detection
    # =========================================================================

    def detect_changes(self) -> List[FileChange]:
        """
        Detect all file changes since last sync.

        Returns:
            List of FileChange objects
        """
        changes = []
        current_files: Set[str] = set()

        # Scan vault for markdown files
        for md_file in self.vault_path.rglob("*.md"):
            relative_path = str(md_file.relative_to(self.vault_path))
            current_files.add(relative_path)

            # Check if file should be read
            if not self._should_read_file(md_file):
                continue

            # Get current modification time
            current_mtime = str(md_file.stat().st_mtime)
            previous_mtime = self.sync_state.get(relative_path)

            if previous_mtime is None:
                # New file
                changes.append(
                    FileChange(
                        path=relative_path,
                        change_type="created",
                        timestamp=datetime.now().isoformat(),
                        content_hash=self._hash_file(md_file),
                        tags=self._extract_tags_from_file(md_file),
                    )
                )
            elif current_mtime != previous_mtime:
                # Modified file
                changes.append(
                    FileChange(
                        path=relative_path,
                        change_type="modified",
                        timestamp=datetime.now().isoformat(),
                        content_hash=self._hash_file(md_file),
                        tags=self._extract_tags_from_file(md_file),
                    )
                )

        # Detect deleted files
        for prev_path in list(self.sync_state.keys()):
            if prev_path not in current_files:
                changes.append(
                    FileChange(
                        path=prev_path,
                        change_type="deleted",
                        timestamp=datetime.now().isoformat(),
                    )
                )

        return changes

    def _hash_file(self, file_path: Path) -> str:
        """Compute MD5 hash of file content."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    # =========================================================================
    # Sync Operations
    # =========================================================================

    def sync_to_knowledge(
        self, changes: Optional[List[FileChange]] = None
    ) -> Dict[str, Any]:
        """
        Sync changed files from vault to knowledge base.

        Args:
            changes: List of changes to sync (or detect automatically)

        Returns:
            Sync result summary
        """
        if changes is None:
            changes = self.detect_changes()

        results = {"synced": 0, "failed": 0, "skipped": 0, "details": []}

        for change in changes:
            if change.change_type == "deleted":
                # Handle deletion
                knowledge_path = self.knowledge_path / change.path
                if knowledge_path.exists():
                    try:
                        knowledge_path.unlink()
                        results["synced"] += 1
                        results["details"].append(
                            {"path": change.path, "action": "deleted"}
                        )
                        # Remove from sync state
                        self.sync_state.pop(change.path, None)
                    except Exception as e:
                        results["failed"] += 1
                        logger.error(f"Failed to delete {change.path}: {e}")
                continue

            # Read from vault
            vault_file = self.vault_path / change.path
            if not vault_file.exists():
                results["skipped"] += 1
                continue

            try:
                with open(vault_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Write to knowledge base
                knowledge_file = self.knowledge_path / change.path
                knowledge_file.parent.mkdir(parents=True, exist_ok=True)

                with open(knowledge_file, "w", encoding="utf-8") as f:
                    f.write(content)

                # Update sync state
                self.sync_state[change.path] = str(vault_file.stat().st_mtime)

                results["synced"] += 1
                results["details"].append(
                    {"path": change.path, "action": change.change_type}
                )

            except Exception as e:
                results["failed"] += 1
                logger.error(f"Failed to sync {change.path}: {e}")

        self._save_sync_state()
        return results

    # =========================================================================
    # Watcher Thread
    # =========================================================================

    def register_callback(self, callback: Callable[[FileChange], None]):
        """Register a callback for file changes."""
        self._callbacks.append(callback)

    def start_watching(self):
        """Start the background watcher thread."""
        if self._running:
            logger.warning("Watcher already running")
            return

        self._running = True
        self._watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._watcher_thread.start()
        logger.info("Obsidian vault watcher started")

    def stop_watching(self):
        """Stop the background watcher thread."""
        self._running = False
        if self._watcher_thread:
            self._watcher_thread.join(timeout=5.0)
        logger.info("Obsidian vault watcher stopped")

    def _watch_loop(self):
        """Main watcher loop (polling-based)."""
        while self._running:
            try:
                changes = self.detect_changes()

                for change in changes:
                    # Notify callbacks
                    for callback in self._callbacks:
                        try:
                            callback(change)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")

                    # Auto-sync to knowledge base
                    self.sync_to_knowledge([change])

                time.sleep(self.config.poll_interval_seconds)

            except Exception as e:
                logger.error(f"Watcher error: {e}")
                time.sleep(5)  # Short retry delay on error

    # =========================================================================
    # Status and Queries
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get current watcher status."""
        return {
            "running": self._running,
            "vault_path": str(self.vault_path),
            "knowledge_path": str(self.knowledge_path),
            "export_path": str(self.export_path),
            "write_policy": self.config.write_policy,
            "poll_interval": self.config.poll_interval_seconds,
            "tracked_files": len(self.sync_state),
            "pending_changes": len(self.pending_changes),
            "approval_queue": len(self.approval_queue),
            "sync_history_count": len(self.sync_history),
        }

    def list_readable_notes(self) -> List[Dict[str, Any]]:
        """List all notes that pass read filters."""
        readable = []

        for md_file in self.vault_path.rglob("*.md"):
            if self._should_read_file(md_file):
                relative_path = md_file.relative_to(self.vault_path)
                readable.append(
                    {
                        "path": str(relative_path),
                        "title": md_file.stem,
                        "tags": self._extract_tags_from_file(md_file),
                        "modified": datetime.fromtimestamp(
                            md_file.stat().st_mtime
                        ).isoformat(),
                    }
                )

        return readable

    def get_sync_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent sync history."""
        return [asdict(r) for r in self.sync_history[-limit:]]


# =============================================================================
# Global Instance
# =============================================================================

_watcher: Optional[ObsidianSyncWatcher] = None


def get_watcher() -> ObsidianSyncWatcher:
    """Get the global watcher instance."""
    global _watcher
    if _watcher is None:
        _watcher = ObsidianSyncWatcher()
    return _watcher


# =============================================================================
# CLI Entry Point
# =============================================================================


def main():
    """Test the Obsidian sync watcher."""
    watcher = ObsidianSyncWatcher()

    print("Obsidian Sync Watcher Status:")
    print(json.dumps(watcher.get_status(), indent=2))

    print("\n--- Readable Notes ---")
    notes = watcher.list_readable_notes()
    for note in notes[:10]:
        print(f"  - {note['path']} [{', '.join(note['tags'])}]")

    print(f"\nTotal readable: {len(notes)}")

    print("\n--- Detecting Changes ---")
    changes = watcher.detect_changes()
    print(f"Found {len(changes)} changes")
    for change in changes[:5]:
        print(f"  - {change.change_type}: {change.path}")

    print("\n--- Test Write to Exports ---")
    result = watcher.write_to_vault(
        content="# Test Export\n\nThis is a test note exported by OsMEN.",
        filename="test_export",
        agent_id="test_agent",
        frontmatter={"tags": "[osmen, test]"},
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
