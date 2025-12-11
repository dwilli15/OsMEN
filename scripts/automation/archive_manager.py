#!/usr/bin/env python3
"""
Archive Manager for OsMEN Workspace

Handles file archival operations:
1. Process pending archive prompts
2. Archive approved files
3. Restore files from archive
4. List archive contents

Usage:
    python archive_manager.py list              # List archive prompts
    python archive_manager.py approve <id>      # Approve archive prompt
    python archive_manager.py restore <path>    # Restore from archive
    python archive_manager.py browse            # Browse archive contents
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class ArchiveManager:
    """Manages file archival and restoration."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the archive manager."""
        self.base_path = base_path or Path(__file__).parent.parent.parent

        # Paths
        self.archive_path = self.base_path / "workspace" / "archive"
        self.pending_review = self.base_path / "workspace" / "pending_review"
        self.queue_file = (
            self.base_path / "infrastructure" / "queues" / "archive_prompts.json"
        )

        # Ensure directories exist
        self.archive_path.mkdir(parents=True, exist_ok=True)

    def get_pending_prompts(self) -> List[dict]:
        """Get all pending archive prompts."""
        if not self.queue_file.exists():
            return []

        with open(self.queue_file, "r") as f:
            return json.load(f)

    def get_prompt_by_id(self, prompt_id: str) -> Optional[dict]:
        """Get a specific prompt by ID."""
        prompts = self.get_pending_prompts()
        for prompt in prompts:
            if prompt.get("id") == prompt_id:
                return prompt
        return None

    def approve_prompt(self, prompt_id: str) -> dict:
        """
        Approve an archive prompt and archive the files.

        Args:
            prompt_id: ID of the prompt to approve

        Returns:
            Summary of archival
        """
        prompt = self.get_prompt_by_id(prompt_id)
        if not prompt:
            return {"success": False, "error": f"Prompt {prompt_id} not found"}

        # Archive folder name
        archive_name = datetime.now().strftime("%Y-%m")
        archived = []
        errors = []

        for file_info in prompt["files"]:
            source = self.pending_review / file_info["path"]
            dest = self.archive_path / archive_name / file_info["path"]

            if source.exists():
                try:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source), str(dest))
                    archived.append(file_info["path"])
                except Exception as e:
                    errors.append({"path": file_info["path"], "error": str(e)})
            else:
                errors.append({"path": file_info["path"], "error": "File not found"})

        # Remove prompt from queue
        self._remove_prompt(prompt_id)

        return {
            "success": True,
            "archived": archived,
            "archive_folder": archive_name,
            "errors": errors,
        }

    def reject_prompt(self, prompt_id: str) -> bool:
        """Remove a prompt without archiving."""
        return self._remove_prompt(prompt_id)

    def _remove_prompt(self, prompt_id: str) -> bool:
        """Remove a prompt from the queue."""
        prompts = self.get_pending_prompts()
        updated = [p for p in prompts if p.get("id") != prompt_id]

        if len(updated) == len(prompts):
            return False

        with open(self.queue_file, "w") as f:
            json.dump(updated, f, indent=2)

        return True

    def browse_archive(self) -> dict:
        """Browse archive contents."""
        archives = {}

        if not self.archive_path.exists():
            return archives

        for archive_folder in sorted(self.archive_path.iterdir()):
            if archive_folder.is_dir():
                files = list(archive_folder.rglob("*"))
                file_list = [
                    {
                        "path": str(f.relative_to(archive_folder)),
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            f.stat().st_mtime
                        ).isoformat(),
                    }
                    for f in files
                    if f.is_file()
                ]
                archives[archive_folder.name] = {
                    "files": file_list,
                    "total_files": len(file_list),
                    "total_size": sum(f["size"] for f in file_list),
                }

        return archives

    def restore_file(
        self, archive_path: str, destination: str = "pending_review"
    ) -> dict:
        """
        Restore a file from archive.

        Args:
            archive_path: Path within archive (e.g., "2024-01/document.pdf")
            destination: Where to restore (pending_review, staging, incoming)

        Returns:
            Result of restoration
        """
        source = self.archive_path / archive_path

        if not source.exists():
            return {"success": False, "error": f"File not found: {archive_path}"}

        # Determine destination
        dest_dirs = {
            "pending_review": self.pending_review,
            "staging": self.base_path / "workspace" / "staging",
            "incoming": self.base_path / "workspace" / "incoming",
        }

        if destination not in dest_dirs:
            return {"success": False, "error": f"Invalid destination: {destination}"}

        # Extract filename from archive path (remove archive folder prefix)
        parts = Path(archive_path).parts
        if len(parts) > 1:
            relative_path = Path(*parts[1:])
        else:
            relative_path = Path(parts[0])

        dest = dest_dirs[destination] / relative_path

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(dest))  # Copy, not move, to preserve archive

            return {"success": True, "restored_to": str(dest), "source": str(source)}
        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="OsMEN Archive Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List pending archive prompts")

    # Approve command
    approve_parser = subparsers.add_parser("approve", help="Approve archive prompt")
    approve_parser.add_argument("prompt_id", help="ID of prompt to approve")

    # Reject command
    reject_parser = subparsers.add_parser("reject", help="Reject archive prompt")
    reject_parser.add_argument("prompt_id", help="ID of prompt to reject")

    # Browse command
    browse_parser = subparsers.add_parser("browse", help="Browse archive contents")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore file from archive")
    restore_parser.add_argument("archive_path", help="Path in archive")
    restore_parser.add_argument(
        "--to",
        default="pending_review",
        choices=["pending_review", "staging", "incoming"],
        help="Destination",
    )

    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--base-path", type=str, help="Override base path")

    args = parser.parse_args()

    # Initialize
    base_path = Path(args.base_path) if args.base_path else None
    manager = ArchiveManager(base_path=base_path)

    if args.command == "list":
        prompts = manager.get_pending_prompts()

        if args.json:
            print(json.dumps(prompts, indent=2))
        else:
            if not prompts:
                print("No pending archive prompts.")
            else:
                print(f"📦 Pending Archive Prompts ({len(prompts)})\n")
                for prompt in prompts:
                    print(f"ID: {prompt['id']}")
                    print(f"Created: {prompt['created_at']}")
                    print(f"Files: {prompt['total_files']}")
                    print(f"Size: {prompt['total_size'] / 1024:.1f} KB")
                    print("-" * 40)

    elif args.command == "approve":
        result = manager.approve_prompt(args.prompt_id)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["success"]:
                print(
                    f"✅ Archived {len(result['archived'])} files to {result['archive_folder']}"
                )
                if result["errors"]:
                    print(f"⚠️ {len(result['errors'])} errors occurred")
            else:
                print(f"❌ {result['error']}")

    elif args.command == "reject":
        if manager.reject_prompt(args.prompt_id):
            print(f"✅ Prompt {args.prompt_id} rejected")
        else:
            print(f"❌ Prompt not found")

    elif args.command == "browse":
        archives = manager.browse_archive()

        if args.json:
            print(json.dumps(archives, indent=2))
        else:
            if not archives:
                print("Archive is empty.")
            else:
                print("📦 Archive Contents\n")
                for folder, info in archives.items():
                    size_mb = info["total_size"] / (1024 * 1024)
                    print(f"{folder}: {info['total_files']} files ({size_mb:.2f} MB)")

    elif args.command == "restore":
        result = manager.restore_file(args.archive_path, args.to)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["success"]:
                print(f"✅ Restored to {result['restored_to']}")
            else:
                print(f"❌ {result['error']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
