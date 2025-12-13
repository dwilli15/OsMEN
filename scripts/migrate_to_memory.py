#!/usr/bin/env python3
"""
OsMEN Data Migration Script

Migrates existing data into HybridMemory for unified semantic search.

Data Sources:
- Check-in logs from logs/
- Focus session history from data/
- Obsidian notes from obsidian-vault/
- Research findings from agents/

Usage:
    python scripts/migrate_to_memory.py
    python scripts/migrate_to_memory.py --dry-run
    python scripts/migrate_to_memory.py --source checkins
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("osmen.migration")

# Try to import HybridMemory
try:
    from integrations.memory import HybridMemory, MemoryConfig, MemoryTier

    MEMORY_AVAILABLE = True
except ImportError as e:
    logger.error(f"HybridMemory not available: {e}")
    MEMORY_AVAILABLE = False


class DataMigrator:
    """Migrates existing OsMEN data into HybridMemory"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.stats = {
            "checkins": {"found": 0, "migrated": 0, "failed": 0},
            "focus_sessions": {"found": 0, "migrated": 0, "failed": 0},
            "notes": {"found": 0, "migrated": 0, "failed": 0},
            "research": {"found": 0, "migrated": 0, "failed": 0},
        }

        self._memory: Optional[HybridMemory] = None

    @property
    def memory(self) -> Optional[HybridMemory]:
        """Lazy-load HybridMemory"""
        if not MEMORY_AVAILABLE:
            return None
        if self._memory is None and not self.dry_run:
            try:
                self._memory = HybridMemory(MemoryConfig.from_env())
                logger.info("HybridMemory connected for migration")
            except Exception as e:
                logger.error(f"Failed to connect HybridMemory: {e}")
        return self._memory

    def migrate_checkins(self) -> Dict[str, int]:
        """Migrate check-in logs to memory"""
        logger.info("=== Migrating Check-In Logs ===")

        logs_dir = Path("logs")
        if not logs_dir.exists():
            logger.warning("logs/ directory not found")
            return self.stats["checkins"]

        # Find check-in log files
        checkin_files = list(logs_dir.glob("*checkin*.json")) + list(
            logs_dir.glob("*check_in*.json")
        )

        for log_file in checkin_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Handle both single object and array formats
                checkins = data if isinstance(data, list) else [data]

                for checkin in checkins:
                    self.stats["checkins"]["found"] += 1

                    if self.dry_run:
                        logger.info(
                            f"  [DRY-RUN] Would migrate checkin from {log_file.name}"
                        )
                        continue

                    if self.memory:
                        try:
                            content = self._format_checkin_content(checkin)
                            self.memory.remember(
                                content=content,
                                source="checkin_migration",
                                context={
                                    "type": checkin.get("type", "unknown"),
                                    "timestamp": checkin.get(
                                        "timestamp", datetime.now().isoformat()
                                    ),
                                    "migrated_from": str(log_file),
                                    "migrated_at": datetime.now().isoformat(),
                                },
                                tier=MemoryTier.WORKING,
                                context7={
                                    "intent": "reflection",
                                    "domain": "productivity",
                                    "emotion": checkin.get("mood", "neutral"),
                                    "temporal": checkin.get("timestamp", "")[:10],
                                    "spatial": "personal",
                                    "relational": "self",
                                    "abstract": "checkin routine",
                                },
                            )
                            self.stats["checkins"]["migrated"] += 1
                        except Exception as e:
                            logger.error(f"Failed to migrate checkin: {e}")
                            self.stats["checkins"]["failed"] += 1

            except Exception as e:
                logger.error(f"Error processing {log_file}: {e}")

        return self.stats["checkins"]

    def _format_checkin_content(self, checkin: Dict) -> str:
        """Format checkin data as searchable content"""
        parts = [f"Check-in: {checkin.get('type', 'daily')}"]

        if "mood" in checkin:
            parts.append(f"Mood: {checkin['mood']}")
        if "energy" in checkin:
            parts.append(f"Energy: {checkin['energy']}")
        if "focus_areas" in checkin:
            parts.append(f"Focus areas: {', '.join(checkin['focus_areas'])}")
        if "accomplishments" in checkin:
            parts.append(f"Accomplishments: {', '.join(checkin['accomplishments'])}")
        if "blockers" in checkin:
            parts.append(f"Blockers: {', '.join(checkin['blockers'])}")
        if "notes" in checkin:
            parts.append(f"Notes: {checkin['notes']}")

        return ". ".join(parts)

    def migrate_focus_sessions(self) -> Dict[str, int]:
        """Migrate focus session history to memory"""
        logger.info("=== Migrating Focus Sessions ===")

        data_dir = Path("data")
        focus_files = list(data_dir.glob("*focus*.json")) + list(
            data_dir.glob("*session*.json")
        )

        for data_file in focus_files:
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                sessions = data if isinstance(data, list) else [data]

                for session in sessions:
                    self.stats["focus_sessions"]["found"] += 1

                    if self.dry_run:
                        logger.info(
                            f"  [DRY-RUN] Would migrate session from {data_file.name}"
                        )
                        continue

                    if self.memory:
                        try:
                            content = self._format_session_content(session)
                            self.memory.remember(
                                content=content,
                                source="focus_migration",
                                context={
                                    "duration": session.get("duration", 0),
                                    "task": session.get("task", ""),
                                    "completed": session.get("completed", False),
                                    "migrated_from": str(data_file),
                                },
                                tier=MemoryTier.WORKING,
                                context7={
                                    "intent": "focus",
                                    "domain": "productivity",
                                    "emotion": "determined",
                                    "temporal": session.get("start_time", "")[:10],
                                    "spatial": "workspace",
                                    "relational": "work",
                                    "abstract": "deep work session",
                                },
                            )
                            self.stats["focus_sessions"]["migrated"] += 1
                        except Exception as e:
                            logger.error(f"Failed to migrate session: {e}")
                            self.stats["focus_sessions"]["failed"] += 1

            except Exception as e:
                logger.warning(f"Could not process {data_file}: {e}")

        return self.stats["focus_sessions"]

    def _format_session_content(self, session: Dict) -> str:
        """Format session data as searchable content"""
        parts = [f"Focus session on: {session.get('task', 'unknown task')}"]

        if "duration" in session:
            parts.append(f"Duration: {session['duration']} minutes")
        if "completed" in session:
            parts.append(f"Completed: {'yes' if session['completed'] else 'no'}")
        if "distractions" in session:
            parts.append(f"Distractions: {session['distractions']}")
        if "rating" in session:
            parts.append(f"Rating: {session['rating']}")

        return ". ".join(parts)

    def migrate_obsidian_notes(self) -> Dict[str, int]:
        """Migrate Obsidian notes to memory"""
        logger.info("=== Migrating Obsidian Notes ===")

        vault_dirs = [Path("obsidian-vault"), Path("vault")]
        vault_path = None

        for vd in vault_dirs:
            if vd.exists():
                vault_path = vd
                break

        if not vault_path:
            logger.warning("No Obsidian vault found")
            return self.stats["notes"]

        # Find all markdown files
        md_files = list(vault_path.glob("**/*.md"))
        logger.info(f"Found {len(md_files)} markdown files")

        for md_file in md_files[:100]:  # Limit to 100 for first migration
            try:
                content = md_file.read_text(encoding="utf-8")
                self.stats["notes"]["found"] += 1

                if self.dry_run:
                    logger.info(
                        f"  [DRY-RUN] Would migrate note: {md_file.relative_to(vault_path)}"
                    )
                    continue

                if self.memory and len(content) > 50:  # Skip tiny files
                    try:
                        # Extract title from filename or first heading
                        title = md_file.stem
                        if content.startswith("# "):
                            title = content.split("\n")[0].strip("# ")

                        self.memory.remember(
                            content=f"Note: {title}. {content[:1000]}",
                            source="obsidian_note",
                            context={
                                "title": title,
                                "path": str(md_file.relative_to(vault_path)),
                                "folder": str(md_file.parent.relative_to(vault_path)),
                                "content_length": len(content),
                                "migrated_at": datetime.now().isoformat(),
                            },
                            tier=MemoryTier.LONG_TERM,
                            context7={
                                "intent": "knowledge",
                                "domain": self._infer_domain(str(md_file)),
                                "emotion": "neutral",
                                "temporal": datetime.now().strftime("%Y-%m"),
                                "spatial": str(md_file.parent.name),
                                "relational": "knowledge",
                                "abstract": title.lower().replace("-", " "),
                            },
                        )
                        self.stats["notes"]["migrated"] += 1
                    except Exception as e:
                        logger.error(f"Failed to migrate note {md_file}: {e}")
                        self.stats["notes"]["failed"] += 1

            except Exception as e:
                logger.warning(f"Could not read {md_file}: {e}")

        return self.stats["notes"]

    def _infer_domain(self, filepath: str) -> str:
        """Infer domain from file path"""
        path_lower = filepath.lower()

        if "daily" in path_lower:
            return "personal"
        elif "project" in path_lower:
            return "project"
        elif "research" in path_lower:
            return "research"
        elif "course" in path_lower or "study" in path_lower:
            return "academic"
        elif "code" in path_lower or "dev" in path_lower:
            return "technical"

        return "general"

    def run_all(self) -> Dict[str, Dict[str, int]]:
        """Run all migrations"""
        logger.info("=" * 60)
        logger.info("  OsMEN Data Migration")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("  [DRY-RUN MODE - No data will be written]")

        logger.info("")

        self.migrate_checkins()
        self.migrate_focus_sessions()
        self.migrate_obsidian_notes()

        # Print summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("  Migration Summary")
        logger.info("=" * 60)

        total_found = 0
        total_migrated = 0
        total_failed = 0

        for source, stats in self.stats.items():
            logger.info(f"  {source}:")
            logger.info(f"    Found: {stats['found']}")
            logger.info(f"    Migrated: {stats['migrated']}")
            logger.info(f"    Failed: {stats['failed']}")

            total_found += stats["found"]
            total_migrated += stats["migrated"]
            total_failed += stats["failed"]

        logger.info("")
        logger.info(
            f"  Total: {total_found} found, {total_migrated} migrated, {total_failed} failed"
        )
        logger.info("=" * 60)

        return self.stats


def main():
    parser = argparse.ArgumentParser(description="Migrate OsMEN data to HybridMemory")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview migration without writing data"
    )
    parser.add_argument(
        "--source",
        choices=["checkins", "focus", "notes", "all"],
        default="all",
        help="Which data source to migrate",
    )

    args = parser.parse_args()

    if not MEMORY_AVAILABLE and not args.dry_run:
        logger.error("HybridMemory not available. Run with --dry-run to preview.")
        sys.exit(1)

    migrator = DataMigrator(dry_run=args.dry_run)

    if args.source == "all":
        migrator.run_all()
    elif args.source == "checkins":
        migrator.migrate_checkins()
    elif args.source == "focus":
        migrator.migrate_focus_sessions()
    elif args.source == "notes":
        migrator.migrate_obsidian_notes()

    return 0


if __name__ == "__main__":
    sys.exit(main())
