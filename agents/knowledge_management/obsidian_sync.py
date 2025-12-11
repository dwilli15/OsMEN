#!/usr/bin/env python3
"""
Obsidian Vault → ChromaDB Sync

Automatically ingests Obsidian notes into ChromaDB for semantic search.
Supports incremental sync based on file modification times.

Collections:
- obsidian_vault: Full vault content with embeddings
- obsidian_daily: Daily notes for temporal context
- obsidian_tags: Tag-based organization
"""

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available. Install with: pip install chromadb")


@dataclass
class SyncConfig:
    """Configuration for Obsidian sync"""

    vault_path: Path
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    collection_name: str = "obsidian_vault"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    exclude_patterns: List[str] = field(
        default_factory=lambda: [
            ".obsidian/*",
            ".trash/*",
            "templates/*",
            "*.excalidraw.md",
        ]
    )
    include_frontmatter: bool = True
    sync_state_file: str = ".osmen_sync_state.json"

    @classmethod
    def from_env(cls) -> "SyncConfig":
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian-vault")
        chroma_host = os.getenv("CHROMADB_HOST", "http://localhost:8000")

        # Parse host and port from URL
        if chroma_host.startswith("http"):
            from urllib.parse import urlparse

            parsed = urlparse(chroma_host)
            host = parsed.hostname or "localhost"
            port = parsed.port or 8000
        else:
            host = chroma_host
            port = 8000

        return cls(
            vault_path=Path(vault_path),
            chroma_host=host,
            chroma_port=port,
        )


@dataclass
class Note:
    """Represents an Obsidian note"""

    path: Path
    title: str
    content: str
    frontmatter: Dict[str, Any]
    tags: List[str]
    links: List[str]
    modified: datetime
    content_hash: str

    def to_chunks(
        self, chunk_size: int = 1000, overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """Split note into overlapping chunks for embedding"""
        chunks = []
        text = self.content

        # If note is small, return as single chunk
        if len(text) <= chunk_size:
            chunks.append(
                {
                    "id": f"{self.content_hash}_0",
                    "text": text,
                    "metadata": self._get_metadata(0, len(text)),
                }
            )
            return chunks

        # Split into overlapping chunks
        start = 0
        chunk_idx = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Try to break at sentence or paragraph
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + chunk_size // 2:
                    end = para_break
                else:
                    # Look for sentence break
                    sent_break = max(
                        text.rfind(". ", start, end),
                        text.rfind("! ", start, end),
                        text.rfind("? ", start, end),
                    )
                    if sent_break > start + chunk_size // 2:
                        end = sent_break + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    {
                        "id": f"{self.content_hash}_{chunk_idx}",
                        "text": chunk_text,
                        "metadata": self._get_metadata(start, end),
                    }
                )
                chunk_idx += 1

            start = end - overlap if end < len(text) else len(text)

        return chunks

    def _get_metadata(self, start: int, end: int) -> Dict[str, Any]:
        """Get metadata for a chunk"""
        return {
            "source": str(self.path),
            "title": self.title,
            "tags": ",".join(self.tags),
            "links": ",".join(self.links[:10]),  # Limit links
            "modified": self.modified.isoformat(),
            "chunk_start": start,
            "chunk_end": end,
            "frontmatter": json.dumps(self.frontmatter) if self.frontmatter else "{}",
        }


class ObsidianSync:
    """
    Syncs Obsidian vault to ChromaDB for semantic search.

    Features:
    - Incremental sync (only changed files)
    - Intelligent chunking with overlap
    - Frontmatter extraction
    - Tag and link extraction
    - Multiple collections for different use cases
    """

    def __init__(self, config: Optional[SyncConfig] = None):
        self.config = config or SyncConfig.from_env()
        self._client = None
        self._collection = None
        self._sync_state = {}

        if not self.config.vault_path.exists():
            logger.warning(f"Vault path does not exist: {self.config.vault_path}")

    @property
    def client(self):
        """Lazy-load ChromaDB client"""
        if self._client is None and CHROMA_AVAILABLE:
            try:
                self._client = chromadb.HttpClient(
                    host=self.config.chroma_host, port=self.config.chroma_port
                )
                logger.info(
                    f"Connected to ChromaDB at {self.config.chroma_host}:{self.config.chroma_port}"
                )
            except Exception as e:
                logger.error(f"Failed to connect to ChromaDB: {e}")
                raise
        return self._client

    @property
    def collection(self):
        """Get or create the collection"""
        if self._collection is None and self.client:
            self._collection = self.client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"description": "Obsidian vault notes with embeddings"},
            )
            logger.info(f"Using collection: {self.config.collection_name}")
        return self._collection

    def _load_sync_state(self) -> Dict[str, str]:
        """Load sync state from file"""
        state_file = self.config.vault_path / self.config.sync_state_file
        if state_file.exists():
            with open(state_file, "r") as f:
                return json.load(f)
        return {}

    def _save_sync_state(self, state: Dict[str, str]) -> None:
        """Save sync state to file"""
        state_file = self.config.vault_path / self.config.sync_state_file
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded"""
        rel_path = str(path.relative_to(self.config.vault_path))
        for pattern in self.config.exclude_patterns:
            if pattern.endswith("/*"):
                folder = pattern[:-2]
                if rel_path.startswith(folder):
                    return True
            elif "*" in pattern:
                import fnmatch

                if fnmatch.fnmatch(rel_path, pattern):
                    return True
            elif rel_path == pattern:
                return True
        return False

    def _parse_note(self, path: Path) -> Optional[Note]:
        """Parse a markdown note file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Failed to read {path}: {e}")
            return None

        # Extract frontmatter
        frontmatter = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = self._parse_frontmatter(parts[1])
                content = parts[2].strip()

        # Extract tags (both frontmatter and inline)
        tags = []
        if "tags" in frontmatter:
            fm_tags = frontmatter["tags"]
            if isinstance(fm_tags, list):
                tags.extend(fm_tags)
            elif isinstance(fm_tags, str):
                tags.extend([t.strip() for t in fm_tags.split(",")])

        # Extract inline tags
        inline_tags = re.findall(r"(?:^|\s)#([a-zA-Z][a-zA-Z0-9_/-]*)", content)
        tags.extend(inline_tags)
        tags = list(set(tags))  # Dedupe

        # Extract wikilinks
        links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)

        # Calculate content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]

        return Note(
            path=path.relative_to(self.config.vault_path),
            title=path.stem,
            content=content,
            frontmatter=frontmatter,
            tags=tags,
            links=links,
            modified=datetime.fromtimestamp(path.stat().st_mtime),
            content_hash=content_hash,
        )

    @staticmethod
    def _parse_frontmatter(fm_text: str) -> Dict[str, Any]:
        """Parse YAML-style frontmatter"""
        frontmatter = {}
        for line in fm_text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Handle arrays
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip().strip("\"'") for v in value[1:-1].split(",")]

                frontmatter[key] = value
        return frontmatter

    def discover_notes(self) -> List[Path]:
        """Discover all markdown files in vault"""
        if not self.config.vault_path.exists():
            return []

        notes = []
        for path in self.config.vault_path.rglob("*.md"):
            if not self._should_exclude(path):
                notes.append(path)

        return notes

    def sync(self, force: bool = False) -> Dict[str, Any]:
        """
        Sync Obsidian vault to ChromaDB.

        Args:
            force: If True, re-sync all files regardless of state

        Returns:
            Sync statistics
        """
        if not CHROMA_AVAILABLE:
            return {"error": "ChromaDB not available", "status": "failed"}

        if not self.config.vault_path.exists():
            return {
                "error": f"Vault not found: {self.config.vault_path}",
                "status": "failed",
            }

        logger.info(f"Starting sync from {self.config.vault_path}")

        # Load previous sync state
        sync_state = {} if force else self._load_sync_state()
        new_state = {}

        stats = {
            "total_files": 0,
            "synced": 0,
            "skipped": 0,
            "failed": 0,
            "chunks_created": 0,
            "deleted": 0,
        }

        # Discover notes
        note_paths = self.discover_notes()
        stats["total_files"] = len(note_paths)
        current_paths = set()

        for path in note_paths:
            rel_path = str(path.relative_to(self.config.vault_path))
            current_paths.add(rel_path)

            # Check if file changed
            mtime = str(path.stat().st_mtime)
            if rel_path in sync_state and sync_state[rel_path] == mtime:
                stats["skipped"] += 1
                new_state[rel_path] = mtime
                continue

            # Parse and sync note
            note = self._parse_note(path)
            if not note:
                stats["failed"] += 1
                continue

            try:
                chunks = note.to_chunks(
                    self.config.chunk_size, self.config.chunk_overlap
                )

                # Delete old chunks for this note
                try:
                    self.collection.delete(where={"source": str(note.path)})
                except Exception:
                    pass  # Collection might be empty

                # Add new chunks
                if chunks:
                    self.collection.add(
                        ids=[c["id"] for c in chunks],
                        documents=[c["text"] for c in chunks],
                        metadatas=[c["metadata"] for c in chunks],
                    )
                    stats["chunks_created"] += len(chunks)

                stats["synced"] += 1
                new_state[rel_path] = mtime
                logger.debug(f"Synced: {rel_path} ({len(chunks)} chunks)")

            except Exception as e:
                logger.error(f"Failed to sync {rel_path}: {e}")
                stats["failed"] += 1

        # Clean up deleted notes
        for old_path in sync_state:
            if old_path not in current_paths:
                try:
                    self.collection.delete(where={"source": old_path})
                    stats["deleted"] += 1
                    logger.debug(f"Deleted: {old_path}")
                except Exception:
                    pass

        # Save new sync state
        self._save_sync_state(new_state)

        stats["status"] = "success"
        stats["collection"] = self.config.collection_name
        stats["timestamp"] = datetime.now().isoformat()

        logger.info(f"Sync complete: {stats}")
        return stats

    def search(
        self, query: str, limit: int = 10, tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across synced notes.

        Args:
            query: Search query
            limit: Max results
            tags: Filter by tags

        Returns:
            List of matching chunks with metadata
        """
        if not CHROMA_AVAILABLE or not self.collection:
            return []

        where = None
        if tags:
            # ChromaDB doesn't support array contains, so we use string matching
            where = {"tags": {"$contains": tags[0]}}

        try:
            results = self.collection.query(
                query_texts=[query], n_results=limit, where=where
            )

            # Format results
            formatted = []
            for i, doc in enumerate(results["documents"][0]):
                formatted.append(
                    {
                        "content": doc,
                        "metadata": (
                            results["metadatas"][0][i] if results["metadatas"] else {}
                        ),
                        "distance": (
                            results["distances"][0][i] if results["distances"] else 0
                        ),
                        "id": results["ids"][0][i] if results["ids"] else None,
                    }
                )

            return formatted

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if not CHROMA_AVAILABLE or not self.collection:
            return {"error": "ChromaDB not available"}

        try:
            count = self.collection.count()
            return {
                "collection": self.config.collection_name,
                "chunk_count": count,
                "vault_path": str(self.config.vault_path),
                "chroma_host": f"{self.config.chroma_host}:{self.config.chroma_port}",
                "status": "connected",
            }
        except Exception as e:
            return {"error": str(e), "status": "disconnected"}


def main():
    """CLI for Obsidian sync"""
    import argparse

    parser = argparse.ArgumentParser(description="Sync Obsidian vault to ChromaDB")
    parser.add_argument("--vault", help="Path to Obsidian vault")
    parser.add_argument("--force", action="store_true", help="Force full resync")
    parser.add_argument("--search", help="Search query")
    parser.add_argument("--stats", action="store_true", help="Show statistics")

    args = parser.parse_args()

    config = SyncConfig.from_env()
    if args.vault:
        config.vault_path = Path(args.vault)

    sync = ObsidianSync(config)

    if args.stats:
        stats = sync.get_stats()
        print(json.dumps(stats, indent=2))
    elif args.search:
        results = sync.search(args.search)
        for r in results:
            print(f"\n--- {r['metadata'].get('title', 'Unknown')} ---")
            print(r["content"][:200])
    else:
        result = sync.sync(force=args.force)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
