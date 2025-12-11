#!/usr/bin/env python3
"""
Enhanced Obsidian Integration for OsMEN

Features:
- Real-time file watching with automatic ChromaDB sync
- Multi-embedding model support (all-MiniLM, BGE, Stella, E5)
- Unified search combining text + semantic
- Librarian integration for RAG
- Daily notes automation
- Template system
- Graph visualization export
"""

import asyncio
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from watchdog.events import (
        FileCreatedEvent,
        FileDeletedEvent,
        FileModifiedEvent,
        FileSystemEventHandler,
    )
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog not available. Install with: pip install watchdog")

try:
    import chromadb
    from chromadb.config import Settings

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class ObsidianConfig:
    """Enhanced configuration for Obsidian integration"""

    vault_path: Path
    chroma_url: str = "http://localhost:8000"
    librarian_url: str = "http://localhost:8200"

    # Collections
    main_collection: str = "obsidian_vault"
    daily_collection: str = "obsidian_daily"
    research_collection: str = "obsidian_research"

    # Embedding settings
    embedding_model: str = (
        "all-MiniLM-L6-v2"  # default, can be stella, bge-m3, e5-mistral
    )

    # Sync settings
    auto_sync: bool = True
    sync_interval: int = 300  # 5 minutes
    watch_changes: bool = True

    # Content settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    include_frontmatter: bool = True

    # Exclude patterns
    exclude_patterns: List[str] = field(
        default_factory=lambda: [
            ".obsidian/*",
            ".trash/*",
            "*.excalidraw.md",
        ]
    )

    # Template folders (content is templates, not notes)
    template_folders: List[str] = field(
        default_factory=lambda: ["Templates", "templates"]
    )

    @classmethod
    def from_env(cls) -> "ObsidianConfig":
        """Load configuration from environment"""
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian-vault")
        return cls(
            vault_path=Path(vault_path),
            chroma_url=os.getenv("CHROMADB_HOST", "http://localhost:8000"),
            librarian_url=os.getenv("LIBRARIAN_URL", "http://localhost:8200"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            auto_sync=os.getenv("OBSIDIAN_AUTO_SYNC", "true").lower() == "true",
            watch_changes=os.getenv("OBSIDIAN_WATCH", "true").lower() == "true",
        )


@dataclass
class ObsidianNote:
    """Enhanced note representation"""

    path: Path
    title: str
    content: str
    raw_content: str  # Original with frontmatter
    frontmatter: Dict[str, Any]
    tags: List[str]
    links: List[str]
    backlinks: List[str]  # Will be populated later
    modified: datetime
    created: Optional[datetime]
    content_hash: str
    word_count: int
    folder: str
    is_daily: bool
    is_template: bool

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get metadata for embedding storage"""
        return {
            "path": str(self.path),
            "title": self.title,
            "folder": self.folder,
            "tags": ",".join(self.tags),
            "links": ",".join(self.links[:20]),
            "modified": self.modified.isoformat(),
            "created": self.created.isoformat() if self.created else "",
            "word_count": self.word_count,
            "is_daily": self.is_daily,
            "is_template": self.is_template,
            "hash": self.content_hash,
        }


class EnhancedObsidianIntegration:
    """
    Enhanced Obsidian integration with ChromaDB sync and Librarian RAG.

    Features:
    - Real-time file watching
    - Semantic search via ChromaDB
    - Librarian RAG integration
    - Daily notes automation
    - Template management
    - Graph export
    """

    def __init__(self, config: Optional[ObsidianConfig] = None):
        self.config = config or ObsidianConfig.from_env()
        self._chroma_client = None
        self._collections: Dict[str, Any] = {}
        self._watcher = None
        self._note_cache: Dict[str, ObsidianNote] = {}
        self._backlinks_cache: Dict[str, List[str]] = {}

    @property
    def vault_exists(self) -> bool:
        return self.config.vault_path.exists()

    @property
    def chroma_client(self):
        """Lazy-load ChromaDB client"""
        if self._chroma_client is None and CHROMA_AVAILABLE:
            try:
                from urllib.parse import urlparse

                parsed = urlparse(self.config.chroma_url)
                host = parsed.hostname or "localhost"
                port = parsed.port or 8000
                self._chroma_client = chromadb.HttpClient(host=host, port=port)
                logger.info(f"Connected to ChromaDB at {host}:{port}")
            except Exception as e:
                logger.error(f"Failed to connect to ChromaDB: {e}")
        return self._chroma_client

    def get_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        if name not in self._collections and self.chroma_client:
            self._collections[name] = self.chroma_client.get_or_create_collection(
                name=name, metadata={"description": f"Obsidian {name} collection"}
            )
        return self._collections.get(name)

    # ==================== NOTE OPERATIONS ====================

    def list_notes(
        self, folder: str = "", include_templates: bool = False
    ) -> List[Dict]:
        """List all notes in the vault"""
        if not self.vault_exists:
            return []

        search_path = (
            self.config.vault_path / folder if folder else self.config.vault_path
        )
        notes = []

        for md_file in search_path.rglob("*.md"):
            if self._should_exclude(md_file):
                continue

            # Check if template
            rel_path = str(md_file.relative_to(self.config.vault_path))
            is_template = any(
                rel_path.startswith(tf) for tf in self.config.template_folders
            )

            if not include_templates and is_template:
                continue

            notes.append(
                {
                    "title": md_file.stem,
                    "path": rel_path,
                    "folder": str(md_file.parent.relative_to(self.config.vault_path)),
                    "modified": datetime.fromtimestamp(
                        md_file.stat().st_mtime
                    ).isoformat(),
                    "is_template": is_template,
                }
            )

        return notes

    def read_note(self, note_path: str) -> Optional[ObsidianNote]:
        """Read and parse a note"""
        if not self.vault_exists:
            return None

        full_path = self.config.vault_path / note_path
        if not full_path.exists():
            return None

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {note_path}: {e}")
            return None

        # Parse frontmatter
        frontmatter = {}
        content = raw_content
        if raw_content.startswith("---"):
            parts = raw_content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = self._parse_frontmatter(parts[1])
                content = parts[2].strip()

        # Extract metadata
        tags = self._extract_tags(raw_content, frontmatter)
        links = self._extract_links(content)

        # Check note type
        rel_path = str(full_path.relative_to(self.config.vault_path))
        is_template = any(
            rel_path.startswith(tf) for tf in self.config.template_folders
        )
        is_daily = self._is_daily_note(full_path.stem)

        # Get created date from frontmatter or file
        created = None
        if "created" in frontmatter:
            try:
                created = datetime.fromisoformat(frontmatter["created"])
            except:
                pass

        stat = full_path.stat()

        return ObsidianNote(
            path=full_path.relative_to(self.config.vault_path),
            title=full_path.stem,
            content=content,
            raw_content=raw_content,
            frontmatter=frontmatter,
            tags=tags,
            links=links,
            backlinks=self._backlinks_cache.get(full_path.stem, []),
            modified=datetime.fromtimestamp(stat.st_mtime),
            created=created or datetime.fromtimestamp(stat.st_ctime),
            content_hash=hashlib.md5(content.encode()).hexdigest()[:12],
            word_count=len(content.split()),
            folder=str(full_path.parent.relative_to(self.config.vault_path)),
            is_daily=is_daily,
            is_template=is_template,
        )

    def create_note(
        self,
        title: str,
        content: str,
        folder: str = "",
        tags: List[str] = None,
        frontmatter: Dict = None,
        template: str = None,
    ) -> Dict[str, Any]:
        """Create a new note"""
        if not self.vault_exists:
            return {"error": "Vault not found"}

        # Apply template if specified
        if template:
            template_content = self._get_template(template)
            if template_content:
                content = self._apply_template(
                    template_content,
                    {
                        "title": title,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "content": content,
                        **(frontmatter or {}),
                    },
                )

        # Build note
        filename = self._sanitize_filename(title) + ".md"
        note_folder = (
            self.config.vault_path / folder if folder else self.config.vault_path
        )
        note_folder.mkdir(parents=True, exist_ok=True)
        full_path = note_folder / filename

        # Build content
        note_content = []

        # Frontmatter
        fm = frontmatter or {}
        fm["created"] = datetime.now().isoformat()
        if tags:
            fm["tags"] = tags

        note_content.append("---")
        for key, value in fm.items():
            if isinstance(value, list):
                note_content.append(f"{key}: [{', '.join(value)}]")
            else:
                note_content.append(f"{key}: {value}")
        note_content.append("---")
        note_content.append("")

        # Title and content
        note_content.append(f"# {title}")
        note_content.append("")
        note_content.append(content)

        # Write file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(note_content))

        # Trigger sync
        if self.config.auto_sync:
            asyncio.create_task(
                self._sync_note(str(full_path.relative_to(self.config.vault_path)))
            )

        return {
            "success": True,
            "path": str(full_path.relative_to(self.config.vault_path)),
            "created": datetime.now().isoformat(),
        }

    def update_note(
        self,
        note_path: str,
        content: str = None,
        append: bool = False,
        frontmatter_updates: Dict = None,
    ) -> Dict[str, Any]:
        """Update an existing note"""
        note = self.read_note(note_path)
        if not note:
            return {"error": f"Note not found: {note_path}"}

        full_path = self.config.vault_path / note_path

        if append and content:
            # Append to existing
            with open(full_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n{content}")
        elif content is not None:
            # Replace content (preserve frontmatter)
            new_fm = {**note.frontmatter, **(frontmatter_updates or {})}
            new_fm["modified"] = datetime.now().isoformat()

            note_content = ["---"]
            for key, value in new_fm.items():
                if isinstance(value, list):
                    note_content.append(f"{key}: [{', '.join(value)}]")
                else:
                    note_content.append(f"{key}: {value}")
            note_content.append("---")
            note_content.append("")
            note_content.append(content)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write("\n".join(note_content))

        # Trigger sync
        if self.config.auto_sync:
            asyncio.create_task(self._sync_note(note_path))

        return {
            "success": True,
            "path": note_path,
            "updated": datetime.now().isoformat(),
        }

    def delete_note(self, note_path: str) -> Dict[str, Any]:
        """Delete a note (move to .trash)"""
        full_path = self.config.vault_path / note_path
        if not full_path.exists():
            return {"error": f"Note not found: {note_path}"}

        # Move to trash
        trash_dir = self.config.vault_path / ".trash"
        trash_dir.mkdir(exist_ok=True)
        trash_path = trash_dir / full_path.name

        full_path.rename(trash_path)

        # Remove from ChromaDB
        if self.chroma_client:
            collection = self.get_collection(self.config.main_collection)
            if collection:
                try:
                    collection.delete(where={"path": note_path})
                except:
                    pass

        return {
            "success": True,
            "deleted": note_path,
            "moved_to": str(trash_path.relative_to(self.config.vault_path)),
        }

    # ==================== SEARCH ====================

    def search_text(self, query: str, case_sensitive: bool = False) -> List[Dict]:
        """Text search across notes"""
        if not self.vault_exists:
            return []

        results = []
        flags = 0 if case_sensitive else re.IGNORECASE

        for md_file in self.config.vault_path.rglob("*.md"):
            if self._should_exclude(md_file):
                continue

            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                matches = list(re.finditer(query, content, flags))
                if matches:
                    results.append(
                        {
                            "title": md_file.stem,
                            "path": str(md_file.relative_to(self.config.vault_path)),
                            "match_count": len(matches),
                            "preview": self._get_match_preview(content, matches[0]),
                        }
                    )
            except Exception:
                continue

        return sorted(results, key=lambda x: x["match_count"], reverse=True)

    def search_semantic(
        self,
        query: str,
        limit: int = 10,
        tags: List[str] = None,
        folder: str = None,
    ) -> List[Dict]:
        """Semantic search using ChromaDB embeddings"""
        if not CHROMA_AVAILABLE or not self.chroma_client:
            return []

        collection = self.get_collection(self.config.main_collection)
        if not collection:
            return []

        # Build filters
        where = {}
        if tags:
            # ChromaDB filter for tags
            where["tags"] = {"$contains": tags[0]}
        if folder:
            where["folder"] = {"$eq": folder}

        try:
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                where=where if where else None,
            )

            formatted = []
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                formatted.append(
                    {
                        "content": doc,
                        "title": meta.get("title", "Unknown"),
                        "path": meta.get("path", ""),
                        "score": 1
                        - (results["distances"][0][i] if results["distances"] else 0),
                        "tags": meta.get("tags", "").split(","),
                    }
                )

            return formatted
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def search_unified(
        self,
        query: str,
        limit: int = 10,
        semantic_weight: float = 0.7,
    ) -> List[Dict]:
        """Unified search combining text and semantic"""
        text_results = self.search_text(query)
        semantic_results = self.search_semantic(query, limit=limit)

        # Combine and rank
        combined = {}

        # Add text results
        for i, r in enumerate(text_results[:limit]):
            path = r["path"]
            combined[path] = {
                **r,
                "text_rank": i + 1,
                "semantic_rank": None,
                "combined_score": (1 - semantic_weight) * (1 / (i + 1)),
            }

        # Add semantic results
        for i, r in enumerate(semantic_results):
            path = r["path"]
            if path in combined:
                combined[path]["semantic_rank"] = i + 1
                combined[path]["combined_score"] += semantic_weight * r["score"]
            else:
                combined[path] = {
                    **r,
                    "text_rank": None,
                    "semantic_rank": i + 1,
                    "combined_score": semantic_weight * r["score"],
                }

        # Sort by combined score
        results = sorted(
            combined.values(), key=lambda x: x["combined_score"], reverse=True
        )
        return results[:limit]

    # ==================== LIBRARIAN INTEGRATION ====================

    async def search_with_librarian(
        self,
        query: str,
        limit: int = 10,
        include_vault: bool = True,
    ) -> Dict[str, Any]:
        """Search using Librarian RAG (combines vault + external docs)"""
        if not HTTPX_AVAILABLE:
            return {"error": "httpx not available"}

        results = {"vault": [], "librarian": [], "combined": []}

        # Get vault results
        if include_vault:
            results["vault"] = self.search_semantic(query, limit=limit)

        # Query Librarian
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.librarian_url}/search",
                    json={"query": query, "limit": limit},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    results["librarian"] = response.json().get("results", [])
        except Exception as e:
            logger.warning(f"Librarian search failed: {e}")

        # Combine results (interleave)
        combined = []
        vault_iter = iter(results["vault"])
        lib_iter = iter(results["librarian"])

        for _ in range(limit):
            try:
                combined.append({**next(vault_iter), "source": "vault"})
            except StopIteration:
                pass
            try:
                combined.append({**next(lib_iter), "source": "librarian"})
            except StopIteration:
                pass

        results["combined"] = combined[:limit]
        return results

    async def ingest_to_librarian(self, note_path: str) -> Dict[str, Any]:
        """Ingest a note to Librarian for RAG"""
        note = self.read_note(note_path)
        if not note:
            return {"error": f"Note not found: {note_path}"}

        if not HTTPX_AVAILABLE:
            return {"error": "httpx not available"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.librarian_url}/ingest",
                    json={
                        "content": note.content,
                        "metadata": {
                            "source": "obsidian",
                            "path": str(note.path),
                            "title": note.title,
                            "tags": note.tags,
                        },
                    },
                    timeout=30.0,
                )
                return response.json()
        except Exception as e:
            return {"error": str(e)}

    # ==================== GRAPH & BACKLINKS ====================

    def build_backlinks(self) -> Dict[str, List[str]]:
        """Build complete backlinks index"""
        backlinks = {}

        for md_file in self.config.vault_path.rglob("*.md"):
            if self._should_exclude(md_file):
                continue

            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                source = md_file.stem
                links = self._extract_links(content)

                for link in links:
                    if link not in backlinks:
                        backlinks[link] = []
                    backlinks[link].append(source)
            except Exception:
                continue

        self._backlinks_cache = backlinks
        return backlinks

    def get_backlinks(self, note_path: str) -> List[Dict]:
        """Get all notes linking to this note"""
        if not self._backlinks_cache:
            self.build_backlinks()

        note_title = Path(note_path).stem
        linking_notes = self._backlinks_cache.get(note_title, [])

        return [{"title": title, "path": f"{title}.md"} for title in linking_notes]

    def export_graph(self) -> Dict[str, Any]:
        """Export knowledge graph for visualization"""
        if not self._backlinks_cache:
            self.build_backlinks()

        nodes = []
        edges = []

        for md_file in self.config.vault_path.rglob("*.md"):
            if self._should_exclude(md_file):
                continue

            note_id = md_file.stem
            rel_path = str(md_file.relative_to(self.config.vault_path))

            nodes.append(
                {
                    "id": note_id,
                    "label": note_id,
                    "path": rel_path,
                    "backlinks": len(self._backlinks_cache.get(note_id, [])),
                }
            )

            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                links = self._extract_links(content)
                for link in links:
                    edges.append({"source": note_id, "target": link})
            except:
                continue

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "avg_connections": len(edges) / max(len(nodes), 1),
            },
        }

    # ==================== DAILY NOTES ====================

    def get_daily_note(self, date: datetime = None) -> Optional[ObsidianNote]:
        """Get daily note for a specific date"""
        date = date or datetime.now()
        filename = date.strftime("%Y-%m-%d") + ".md"

        # Check common daily note locations
        for folder in ["Daily Notes", "Journal", "Daily", ""]:
            path = f"{folder}/{filename}" if folder else filename
            note = self.read_note(path)
            if note:
                return note

        return None

    def create_daily_note(
        self, date: datetime = None, content: str = ""
    ) -> Dict[str, Any]:
        """Create daily note from template"""
        date = date or datetime.now()
        title = date.strftime("%Y-%m-%d")

        # Get yesterday/tomorrow for navigation
        yesterday = (date - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (date + timedelta(days=1)).strftime("%Y-%m-%d")

        daily_content = f"""## 📅 Daily Overview

### Navigation
- [[{yesterday}|← Yesterday]]
- [[{tomorrow}|Tomorrow →]]

## ✅ Tasks
- [ ] Review daily brief
- [ ] Check system status
- [ ] Process inbox

## 📝 Notes
{content}

## 🔗 Today's Links


## 📊 Metrics


---
*Generated by OsMEN at {datetime.now().strftime('%H:%M')}*
"""

        return self.create_note(
            title=title,
            content=daily_content,
            folder="Daily Notes",
            tags=["daily-note", date.strftime("%Y-%m")],
            frontmatter={
                "type": "daily-note",
                "date": title,
            },
        )

    # ==================== SYNC ====================

    async def sync_to_chroma(self, force: bool = False) -> Dict[str, Any]:
        """Sync entire vault to ChromaDB"""
        if not CHROMA_AVAILABLE or not self.chroma_client:
            return {"error": "ChromaDB not available"}

        collection = self.get_collection(self.config.main_collection)
        if not collection:
            return {"error": "Failed to get collection"}

        stats = {
            "total": 0,
            "synced": 0,
            "skipped": 0,
            "failed": 0,
            "chunks": 0,
        }

        # Load sync state
        state_file = self.config.vault_path / ".osmen_sync_state.json"
        sync_state = {}
        if not force and state_file.exists():
            try:
                with open(state_file) as f:
                    sync_state = json.load(f)
            except:
                pass

        new_state = {}

        for md_file in self.config.vault_path.rglob("*.md"):
            if self._should_exclude(md_file):
                continue

            stats["total"] += 1
            rel_path = str(md_file.relative_to(self.config.vault_path))
            mtime = str(md_file.stat().st_mtime)

            # Skip unchanged
            if not force and sync_state.get(rel_path) == mtime:
                stats["skipped"] += 1
                new_state[rel_path] = mtime
                continue

            # Read and chunk note
            note = self.read_note(rel_path)
            if not note:
                stats["failed"] += 1
                continue

            try:
                chunks = self._chunk_content(note)

                # Delete old chunks
                try:
                    collection.delete(where={"path": rel_path})
                except:
                    pass

                # Add new chunks
                if chunks:
                    collection.add(
                        ids=[c["id"] for c in chunks],
                        documents=[c["text"] for c in chunks],
                        metadatas=[c["metadata"] for c in chunks],
                    )
                    stats["chunks"] += len(chunks)

                stats["synced"] += 1
                new_state[rel_path] = mtime
            except Exception as e:
                logger.error(f"Failed to sync {rel_path}: {e}")
                stats["failed"] += 1

        # Save state
        with open(state_file, "w") as f:
            json.dump(new_state, f, indent=2)

        stats["status"] = "success"
        stats["timestamp"] = datetime.now().isoformat()
        return stats

    async def _sync_note(self, note_path: str) -> None:
        """Sync a single note to ChromaDB"""
        note = self.read_note(note_path)
        if not note or not self.chroma_client:
            return

        collection = self.get_collection(self.config.main_collection)
        if not collection:
            return

        try:
            # Delete old
            collection.delete(where={"path": note_path})

            # Add new
            chunks = self._chunk_content(note)
            if chunks:
                collection.add(
                    ids=[c["id"] for c in chunks],
                    documents=[c["text"] for c in chunks],
                    metadatas=[c["metadata"] for c in chunks],
                )

            logger.debug(f"Synced: {note_path}")
        except Exception as e:
            logger.error(f"Failed to sync {note_path}: {e}")

    # ==================== FILE WATCHER ====================

    def start_watcher(self) -> bool:
        """Start file system watcher for real-time sync"""
        if not WATCHDOG_AVAILABLE:
            return False

        if self._watcher:
            return True

        class VaultEventHandler(FileSystemEventHandler):
            def __init__(self, integration):
                self.integration = integration

            def on_modified(self, event):
                if event.is_directory or not event.src_path.endswith(".md"):
                    return
                rel_path = Path(event.src_path).relative_to(
                    self.integration.config.vault_path
                )
                if self.integration.config.auto_sync:
                    asyncio.create_task(self.integration._sync_note(str(rel_path)))

            def on_created(self, event):
                if not event.is_directory and event.src_path.endswith(".md"):
                    self.on_modified(event)

            def on_deleted(self, event):
                if event.is_directory or not event.src_path.endswith(".md"):
                    return
                # Remove from ChromaDB
                rel_path = str(
                    Path(event.src_path).relative_to(self.integration.config.vault_path)
                )
                collection = self.integration.get_collection(
                    self.integration.config.main_collection
                )
                if collection:
                    try:
                        collection.delete(where={"path": rel_path})
                    except:
                        pass

        handler = VaultEventHandler(self)
        self._watcher = Observer()
        self._watcher.schedule(handler, str(self.config.vault_path), recursive=True)
        self._watcher.start()
        logger.info(f"Started watching: {self.config.vault_path}")
        return True

    def stop_watcher(self) -> None:
        """Stop file system watcher"""
        if self._watcher:
            self._watcher.stop()
            self._watcher.join()
            self._watcher = None
            logger.info("Stopped watching vault")

    # ==================== HELPERS ====================

    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded"""
        try:
            rel_path = str(path.relative_to(self.config.vault_path))
        except ValueError:
            return True

        for pattern in self.config.exclude_patterns:
            if pattern.endswith("/*"):
                if rel_path.startswith(pattern[:-2]):
                    return True
            elif "*" in pattern:
                import fnmatch

                if fnmatch.fnmatch(rel_path, pattern):
                    return True
            elif rel_path == pattern:
                return True
        return False

    def _is_daily_note(self, title: str) -> bool:
        """Check if note is a daily note by title format"""
        try:
            datetime.strptime(title, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    @staticmethod
    def _parse_frontmatter(fm_text: str) -> Dict[str, Any]:
        """Parse YAML-style frontmatter"""
        fm = {}
        for line in fm_text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Parse arrays
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip().strip("\"'") for v in value[1:-1].split(",")]

                fm[key] = value
        return fm

    @staticmethod
    def _extract_tags(content: str, frontmatter: Dict) -> List[str]:
        """Extract tags from content and frontmatter"""
        tags = []

        # Frontmatter tags
        if "tags" in frontmatter:
            fm_tags = frontmatter["tags"]
            if isinstance(fm_tags, list):
                tags.extend(fm_tags)
            elif isinstance(fm_tags, str):
                tags.extend([t.strip() for t in fm_tags.split(",")])

        # Inline tags
        inline = re.findall(r"(?:^|\s)#([a-zA-Z][a-zA-Z0-9_/-]*)", content)
        tags.extend(inline)

        return list(set(tags))

    @staticmethod
    def _extract_links(content: str) -> List[str]:
        """Extract wikilinks"""
        return re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Make filename safe"""
        return re.sub(r'[<>:"/\\|?*]', "", name).strip()

    def _get_match_preview(
        self, content: str, match: re.Match, context: int = 50
    ) -> str:
        """Get preview around a match"""
        start = max(0, match.start() - context)
        end = min(len(content), match.end() + context)
        preview = content[start:end]
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."
        return preview

    def _chunk_content(self, note: ObsidianNote) -> List[Dict]:
        """Chunk note content for embedding"""
        chunks = []
        text = note.content
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        if len(text) <= chunk_size:
            chunks.append(
                {
                    "id": f"{note.content_hash}_0",
                    "text": text,
                    "metadata": {**note.metadata, "chunk": 0},
                }
            )
            return chunks

        start = 0
        chunk_idx = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Try to break at paragraph/sentence
            if end < len(text):
                for sep in ["\n\n", ". ", "! ", "? "]:
                    pos = text.rfind(sep, start, end)
                    if pos > start + chunk_size // 2:
                        end = pos + len(sep)
                        break

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    {
                        "id": f"{note.content_hash}_{chunk_idx}",
                        "text": chunk_text,
                        "metadata": {**note.metadata, "chunk": chunk_idx},
                    }
                )
                chunk_idx += 1

            start = end - overlap if end < len(text) else len(text)

        return chunks

    def _get_template(self, template_name: str) -> Optional[str]:
        """Get template content by name"""
        for folder in self.config.template_folders:
            template_path = self.config.vault_path / folder / f"{template_name}.md"
            if template_path.exists():
                with open(template_path, "r", encoding="utf-8") as f:
                    return f.read()
        return None

    def _apply_template(self, template: str, variables: Dict) -> str:
        """Apply variables to template"""
        content = template
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        return content


# ==================== CLI ====================


async def main():
    """CLI for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Obsidian Integration")
    parser.add_argument("--vault", help="Vault path")
    parser.add_argument("--sync", action="store_true", help="Sync to ChromaDB")
    parser.add_argument("--search", help="Search query")
    parser.add_argument("--watch", action="store_true", help="Start file watcher")
    parser.add_argument("--graph", action="store_true", help="Export graph")
    parser.add_argument("--stats", action="store_true", help="Show stats")

    args = parser.parse_args()

    config = ObsidianConfig.from_env()
    if args.vault:
        config.vault_path = Path(args.vault)

    integration = EnhancedObsidianIntegration(config)

    if args.sync:
        result = await integration.sync_to_chroma()
        print(json.dumps(result, indent=2))

    elif args.search:
        results = integration.search_unified(args.search)
        for r in results:
            print(f"\n{r['title']} (score: {r.get('combined_score', 0):.3f})")
            print(f"  Path: {r['path']}")

    elif args.graph:
        graph = integration.export_graph()
        print(json.dumps(graph, indent=2))

    elif args.watch:
        if integration.start_watcher():
            print("Watching for changes... Press Ctrl+C to stop")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                integration.stop_watcher()
        else:
            print("Watchdog not available")

    else:
        # Default: show stats
        notes = integration.list_notes()
        print(f"📁 Vault: {config.vault_path}")
        print(f"📝 Notes: {len(notes)}")
        print(f"🔗 ChromaDB: {config.chroma_url}")
        print(f"📚 Librarian: {config.librarian_url}")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(main())
    asyncio.run(main())
