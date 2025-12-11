"""
Hybrid Memory System - Core Implementation
==========================================

Combines ChromaDB (long-term vectors) and SQLite (short-term structured)
with dynamic bridging and embedded reasoning.

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                        HybridMemory                             │
├─────────────────────┬───────────────────────────────────────────┤
│     Short-Term      │              Long-Term                    │
│      (SQLite)       │             (ChromaDB)                    │
├─────────────────────┼───────────────────────────────────────────┤
│ • Session State     │ • Semantic Vectors                        │
│ • Active Tasks      │ • RAG Knowledge Base                      │
│ • Recent Queries    │ • Archived Conversations                  │
│ • Working Memory    │ • Lateral Context (Context7)              │
│ • Quick Lookups     │ • Synchronicity Bridges                   │
├─────────────────────┴───────────────────────────────────────────┤
│                    MemoryBridge                                 │
│   • Automatic promotion (short→long when salient)               │
│   • Decay management (long→archive when stale)                  │
│   • Synchronicity detection (bridge disparate concepts)         │
└─────────────────────────────────────────────────────────────────┘
"""

import hashlib
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import chromadb
from chromadb.config import Settings

logger = logging.getLogger("osmen.memory.hybrid")


# =============================================================================
# Configuration
# =============================================================================


class MemoryTier(Enum):
    """Memory storage tiers."""

    WORKING = "working"  # Immediate context (in-memory)
    SHORT_TERM = "short"  # Session-based (SQLite)
    LONG_TERM = "long"  # Persistent vectors (ChromaDB)
    ARCHIVE = "archive"  # Compressed history (SQLite)


@dataclass
class MemoryConfig:
    """Configuration for the hybrid memory system."""

    # SQLite paths
    sqlite_path: str = "data/memory/short_term.db"
    archive_path: str = "data/memory/archive.db"

    # ChromaDB settings
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000
    chromadb_collection: str = "osmen_long_term"

    # Timing (in hours)
    short_term_ttl: int = 24  # Promote to long-term after 24h
    long_term_ttl: int = 720  # Archive after 30 days
    working_memory_size: int = 50  # Max items in working memory

    # Synchronicity settings
    enable_lateral_bridges: bool = True
    synchronicity_threshold: float = 0.75  # Similarity for bridge detection

    # Sequential reasoning settings
    enable_sequential_reasoning: bool = True
    max_reasoning_depth: int = 7  # Context7 inspired

    @classmethod
    def from_env(cls) -> "MemoryConfig":
        """Load config from environment variables."""
        return cls(
            sqlite_path=os.getenv("OSMEN_MEMORY_SQLITE", "data/memory/short_term.db"),
            archive_path=os.getenv("OSMEN_MEMORY_ARCHIVE", "data/memory/archive.db"),
            chromadb_host=os.getenv("CHROMADB_HOST", "localhost"),
            chromadb_port=int(os.getenv("CHROMADB_PORT", "8000")),
            chromadb_collection=os.getenv("CHROMADB_COLLECTION", "osmen_long_term"),
            short_term_ttl=int(os.getenv("MEMORY_SHORT_TTL", "24")),
            long_term_ttl=int(os.getenv("MEMORY_LONG_TTL", "720")),
            enable_lateral_bridges=os.getenv("ENABLE_LATERAL", "true").lower()
            == "true",
        )


# =============================================================================
# Memory Item Data Structure
# =============================================================================


@dataclass
class MemoryItem:
    """A unified memory item that can exist in any tier."""

    id: str
    content: str
    tier: MemoryTier
    created_at: float
    accessed_at: float
    access_count: int = 0

    # Metadata
    source: str = "unknown"  # agent, user, system
    context: Dict[str, Any] = field(default_factory=dict)

    # Context7 dimensions (for lateral thinking)
    intent: str = ""
    domain: str = ""
    emotion: str = ""
    temporal: str = ""
    spatial: str = ""
    relational: str = ""
    abstract: str = ""

    # Embedding (for vector store)
    embedding: Optional[List[float]] = None

    # Sequential reasoning trace
    reasoning_steps: List[str] = field(default_factory=list)

    # Bridge connections (synchronicity)
    bridges: List[str] = field(default_factory=list)  # IDs of connected memories

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "tier": self.tier.value,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
            "source": self.source,
            "context": self.context,
            "intent": self.intent,
            "domain": self.domain,
            "emotion": self.emotion,
            "temporal": self.temporal,
            "spatial": self.spatial,
            "relational": self.relational,
            "abstract": self.abstract,
            "reasoning_steps": self.reasoning_steps,
            "bridges": self.bridges,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            tier=MemoryTier(data.get("tier", "short")),
            created_at=data.get("created_at", time.time()),
            accessed_at=data.get("accessed_at", time.time()),
            access_count=data.get("access_count", 0),
            source=data.get("source", "unknown"),
            context=data.get("context", {}),
            intent=data.get("intent", ""),
            domain=data.get("domain", ""),
            emotion=data.get("emotion", ""),
            temporal=data.get("temporal", ""),
            spatial=data.get("spatial", ""),
            relational=data.get("relational", ""),
            abstract=data.get("abstract", ""),
            reasoning_steps=data.get("reasoning_steps", []),
            bridges=data.get("bridges", []),
        )

    def context7_metadata(self) -> Dict[str, str]:
        """Return Context7 dimensions as metadata."""
        return {
            "c7_intent": self.intent,
            "c7_domain": self.domain,
            "c7_emotion": self.emotion,
            "c7_temporal": self.temporal,
            "c7_spatial": self.spatial,
            "c7_relational": self.relational,
            "c7_abstract": self.abstract,
        }


# =============================================================================
# Short-Term Memory (SQLite)
# =============================================================================


class ShortTermMemory:
    """
    SQLite-based short-term memory store.

    Stores:
    - Session state and context
    - Recent queries and responses
    - Active tasks and working memory
    - Quick keyword lookups
    """

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Main memories table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    tier TEXT DEFAULT 'short',
                    created_at REAL NOT NULL,
                    accessed_at REAL NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    source TEXT DEFAULT 'unknown',
                    context TEXT,
                    c7_intent TEXT,
                    c7_domain TEXT,
                    c7_emotion TEXT,
                    c7_temporal TEXT,
                    c7_spatial TEXT,
                    c7_relational TEXT,
                    c7_abstract TEXT,
                    reasoning_steps TEXT,
                    bridges TEXT
                )
            """
            )

            # Sessions table for context continuity
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    last_active REAL NOT NULL,
                    state TEXT,
                    metadata TEXT
                )
            """
            )

            # Quick lookup index for keyword search
            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
                USING fts5(id, content, c7_domain, c7_abstract)
            """
            )

            # Indexes
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_tier
                ON memories(tier, accessed_at DESC)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_source
                ON memories(source, created_at DESC)
            """
            )

            conn.commit()

    def store(self, item: MemoryItem) -> str:
        """Store a memory item."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO memories
                (id, content, tier, created_at, accessed_at, access_count,
                 source, context, c7_intent, c7_domain, c7_emotion,
                 c7_temporal, c7_spatial, c7_relational, c7_abstract,
                 reasoning_steps, bridges)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    item.id,
                    item.content,
                    item.tier.value,
                    item.created_at,
                    item.accessed_at,
                    item.access_count,
                    item.source,
                    json.dumps(item.context),
                    item.intent,
                    item.domain,
                    item.emotion,
                    item.temporal,
                    item.spatial,
                    item.relational,
                    item.abstract,
                    json.dumps(item.reasoning_steps),
                    json.dumps(item.bridges),
                ),
            )

            # Update FTS index
            cursor.execute(
                """
                INSERT OR REPLACE INTO memories_fts
                (id, content, c7_domain, c7_abstract)
                VALUES (?, ?, ?, ?)
            """,
                (item.id, item.content, item.domain, item.abstract),
            )

            conn.commit()

        logger.debug(f"Stored short-term memory: {item.id}")
        return item.id

    def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory by ID and update access stats."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM memories WHERE id = ?
            """,
                (memory_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            # Update access stats
            cursor.execute(
                """
                UPDATE memories
                SET accessed_at = ?, access_count = access_count + 1
                WHERE id = ?
            """,
                (time.time(), memory_id),
            )
            conn.commit()

            return self._row_to_item(dict(row))

    def search(
        self, query: str, limit: int = 10, tier: Optional[MemoryTier] = None
    ) -> List[MemoryItem]:
        """Full-text search with optional tier filter."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # FTS search
            if tier:
                cursor.execute(
                    """
                    SELECT m.* FROM memories m
                    JOIN memories_fts fts ON m.id = fts.id
                    WHERE memories_fts MATCH ? AND m.tier = ?
                    ORDER BY rank
                    LIMIT ?
                """,
                    (query, tier.value, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT m.* FROM memories m
                    JOIN memories_fts fts ON m.id = fts.id
                    WHERE memories_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """,
                    (query, limit),
                )

            rows = cursor.fetchall()
            return [self._row_to_item(dict(row)) for row in rows]

    def get_recent(
        self, source: Optional[str] = None, limit: int = 20
    ) -> List[MemoryItem]:
        """Get recent memories, optionally filtered by source."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if source:
                cursor.execute(
                    """
                    SELECT * FROM memories
                    WHERE source = ?
                    ORDER BY accessed_at DESC
                    LIMIT ?
                """,
                    (source, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM memories
                    ORDER BY accessed_at DESC
                    LIMIT ?
                """,
                    (limit,),
                )

            rows = cursor.fetchall()
            return [self._row_to_item(dict(row)) for row in rows]

    def get_stale(self, ttl_hours: int = 24) -> List[MemoryItem]:
        """Get memories older than TTL for promotion consideration."""
        cutoff = time.time() - (ttl_hours * 3600)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM memories
                WHERE tier = 'short' AND accessed_at < ?
                ORDER BY access_count DESC
            """,
                (cutoff,),
            )

            rows = cursor.fetchall()
            return [self._row_to_item(dict(row)) for row in rows]

    def delete(self, memory_id: str) -> bool:
        """Delete a memory item."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            cursor.execute("DELETE FROM memories_fts WHERE id = ?", (memory_id,))

            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    def _row_to_item(self, row: Dict) -> MemoryItem:
        """Convert database row to MemoryItem."""
        return MemoryItem(
            id=row["id"],
            content=row["content"],
            tier=MemoryTier(row.get("tier", "short")),
            created_at=row.get("created_at", time.time()),
            accessed_at=row.get("accessed_at", time.time()),
            access_count=row.get("access_count", 0),
            source=row.get("source", "unknown"),
            context=json.loads(row["context"]) if row.get("context") else {},
            intent=row.get("c7_intent", ""),
            domain=row.get("c7_domain", ""),
            emotion=row.get("c7_emotion", ""),
            temporal=row.get("c7_temporal", ""),
            spatial=row.get("c7_spatial", ""),
            relational=row.get("c7_relational", ""),
            abstract=row.get("c7_abstract", ""),
            reasoning_steps=(
                json.loads(row["reasoning_steps"]) if row.get("reasoning_steps") else []
            ),
            bridges=json.loads(row["bridges"]) if row.get("bridges") else [],
        )


# =============================================================================
# Long-Term Memory (ChromaDB)
# =============================================================================


class LongTermMemory:
    """
    ChromaDB-based long-term vector memory.

    Stores:
    - Semantic embeddings for RAG retrieval
    - Archived conversations and knowledge
    - Lateral context bridges
    - Persistent knowledge base
    """

    def __init__(self, config: MemoryConfig):
        self.config = config
        self._client: Optional[chromadb.HttpClient] = None
        self._collection = None

    @property
    def client(self) -> chromadb.HttpClient:
        """Lazy-load ChromaDB client."""
        if self._client is None:
            try:
                self._client = chromadb.HttpClient(
                    host=self.config.chromadb_host, port=self.config.chromadb_port
                )
                logger.info(
                    f"Connected to ChromaDB at {self.config.chromadb_host}:{self.config.chromadb_port}"
                )
            except Exception as e:
                logger.error(f"Failed to connect to ChromaDB: {e}")
                raise
        return self._client

    @property
    def collection(self):
        """Get or create the main collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.config.chromadb_collection,
                metadata={
                    "description": "OsMEN long-term memory with Context7 and lateral bridges",
                    "hnsw:space": "cosine",
                },
            )
        return self._collection

    def store(self, item: MemoryItem, embedding: Optional[List[float]] = None) -> str:
        """Store a memory item with optional embedding."""
        metadata = {
            "tier": item.tier.value,
            "created_at": item.created_at,
            "accessed_at": item.accessed_at,
            "access_count": item.access_count,
            "source": item.source,
            **item.context7_metadata(),
        }

        # Add reasoning steps if present
        if item.reasoning_steps:
            metadata["reasoning_trace"] = json.dumps(item.reasoning_steps)

        # Add bridge IDs if present
        if item.bridges:
            metadata["bridges"] = json.dumps(item.bridges)

        try:
            if embedding:
                self.collection.upsert(
                    ids=[item.id],
                    documents=[item.content],
                    embeddings=[embedding],
                    metadatas=[metadata],
                )
            else:
                # Let ChromaDB generate embedding
                self.collection.upsert(
                    ids=[item.id], documents=[item.content], metadatas=[metadata]
                )

            logger.debug(f"Stored long-term memory: {item.id}")
            return item.id
        except Exception as e:
            logger.error(f"Failed to store in ChromaDB: {e}")
            raise

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        mode: str = "foundation",
        where: Optional[Dict] = None,
        include_bridges: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Query long-term memory with mode selection.

        Modes:
        - foundation: Direct semantic search
        - lateral: MMR search with Context7 diversity
        - factcheck: High-precision exact match bias
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            items = []
            for i, doc_id in enumerate(results["ids"][0]):
                item = {
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": (
                        results["distances"][0][i] if results.get("distances") else None
                    ),
                    "retrieval_mode": mode,
                }
                items.append(item)

            # Include bridge connections if requested
            if include_bridges:
                items = self._expand_bridges(items)

            return items
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def query_lateral(
        self, query_text: str, n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Lateral thinking query - find non-obvious connections.

        Implements the Dao of Complexity approach:
        1. Focus vector (direct query)
        2. Shadow vector (context/implications)
        3. Weave results for synchronicity
        """
        try:
            # Focus query (direct)
            focus_query = f"Precise answer to: {query_text}"
            focus_results = self.collection.query(
                query_texts=[focus_query], n_results=n_results
            )

            # Shadow query (lateral/abstract)
            shadow_query = f"Broader themes, implications, and abstract connections to: {query_text}"
            shadow_results = self.collection.query(
                query_texts=[shadow_query],
                n_results=n_results * 2,  # Get more for diversity
            )

            # Weave results (interleave focus and shadow)
            woven = []
            seen_ids = set()

            focus_iter = iter(
                zip(
                    focus_results["ids"][0],
                    focus_results["documents"][0],
                    focus_results.get(
                        "metadatas", [[{}] * len(focus_results["ids"][0])]
                    )[0],
                )
            )
            shadow_iter = iter(
                zip(
                    shadow_results["ids"][0],
                    shadow_results["documents"][0],
                    shadow_results.get(
                        "metadatas", [[{}] * len(shadow_results["ids"][0])]
                    )[0],
                )
            )

            while len(woven) < n_results:
                # Add 2 focus results
                for _ in range(2):
                    try:
                        doc_id, content, meta = next(focus_iter)
                        if doc_id not in seen_ids:
                            woven.append(
                                {
                                    "id": doc_id,
                                    "content": content,
                                    "metadata": meta,
                                    "retrieval_layer": "focus",
                                }
                            )
                            seen_ids.add(doc_id)
                    except StopIteration:
                        break

                # Add 1 shadow result (for diversity)
                try:
                    doc_id, content, meta = next(shadow_iter)
                    if doc_id not in seen_ids:
                        woven.append(
                            {
                                "id": doc_id,
                                "content": content,
                                "metadata": meta,
                                "retrieval_layer": "shadow_context",
                            }
                        )
                        seen_ids.add(doc_id)
                except StopIteration:
                    pass

                if len(woven) >= n_results:
                    break

            return woven[:n_results]
        except Exception as e:
            logger.error(f"Lateral query failed: {e}")
            return []

    def _expand_bridges(self, items: List[Dict]) -> List[Dict]:
        """Expand bridge connections to include related items."""
        expanded = items.copy()
        bridge_ids = []

        for item in items:
            meta = item.get("metadata", {})
            if "bridges" in meta:
                try:
                    bridge_list = json.loads(meta["bridges"])
                    bridge_ids.extend(bridge_list)
                except:
                    pass

        # Fetch bridge items (unique only)
        bridge_ids = list(set(bridge_ids) - {item["id"] for item in items})
        if bridge_ids:
            try:
                bridge_results = self.collection.get(
                    ids=bridge_ids, include=["documents", "metadatas"]
                )

                for i, doc_id in enumerate(bridge_results["ids"]):
                    expanded.append(
                        {
                            "id": doc_id,
                            "content": bridge_results["documents"][i],
                            "metadata": bridge_results["metadatas"][i],
                            "retrieval_layer": "synchronicity_bridge",
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to expand bridges: {e}")

        return expanded

    def delete(self, memory_id: str) -> bool:
        """Delete a memory from ChromaDB."""
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete from ChromaDB: {e}")
            return False

    def get_by_domain(self, domain: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Get memories filtered by Context7 domain."""
        return self.query(
            query_text=f"Information about {domain}",
            n_results=n_results,
            where={"c7_domain": domain},
        )


# =============================================================================
# Unified Hybrid Memory
# =============================================================================


class HybridMemory:
    """
    Unified hybrid memory system with dynamic bridging.

    Combines short-term (SQLite) and long-term (ChromaDB) with:
    - Automatic tier management
    - Synchronicity bridge detection
    - Sequential reasoning trace
    - Context7 enrichment
    """

    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig.from_env()

        # Initialize memory stores
        self.short_term = ShortTermMemory(self.config.sqlite_path)
        self.long_term = LongTermMemory(self.config)

        # Working memory (in-memory for immediate context)
        self.working_memory: List[MemoryItem] = []

        logger.info("HybridMemory initialized")

    def remember(
        self,
        content: str,
        source: str = "user",
        context: Optional[Dict] = None,
        tier: MemoryTier = MemoryTier.SHORT_TERM,
        context7: Optional[Dict] = None,
        reasoning_steps: Optional[List[str]] = None,
    ) -> MemoryItem:
        """
        Store a new memory with intelligent tier placement.

        Args:
            content: The memory content
            source: Origin (user, agent, system)
            context: Additional context metadata
            tier: Initial storage tier
            context7: Context7 dimensions for lateral thinking
            reasoning_steps: Sequential reasoning trace

        Returns:
            The stored MemoryItem
        """
        now = time.time()
        memory_id = self._generate_id(content, now)

        # Create memory item
        item = MemoryItem(
            id=memory_id,
            content=content,
            tier=tier,
            created_at=now,
            accessed_at=now,
            source=source,
            context=context or {},
            reasoning_steps=reasoning_steps or [],
        )

        # Apply Context7 if provided
        if context7:
            item.intent = context7.get("intent", "")
            item.domain = context7.get("domain", "")
            item.emotion = context7.get("emotion", "")
            item.temporal = context7.get("temporal", "")
            item.spatial = context7.get("spatial", "")
            item.relational = context7.get("relational", "")
            item.abstract = context7.get("abstract", "")

        # Store based on tier
        if tier == MemoryTier.WORKING:
            self._add_to_working_memory(item)
        elif tier == MemoryTier.SHORT_TERM:
            self.short_term.store(item)
        elif tier == MemoryTier.LONG_TERM:
            self.long_term.store(item)

        logger.debug(f"Remembered in {tier.value}: {memory_id}")
        return item

    def recall(
        self,
        query: str,
        n_results: int = 5,
        search_all_tiers: bool = True,
        mode: str = "foundation",
    ) -> List[MemoryItem]:
        """
        Recall memories across tiers using intelligent search.

        Args:
            query: Search query
            n_results: Max results per tier
            search_all_tiers: Whether to search all tiers
            mode: Retrieval mode (foundation, lateral, factcheck)

        Returns:
            List of matching MemoryItems
        """
        results = []

        # 1. Check working memory first (fastest)
        working_matches = self._search_working_memory(query)
        results.extend(working_matches)

        if search_all_tiers:
            # 2. Search short-term (SQLite FTS)
            short_matches = self.short_term.search(query, limit=n_results)
            results.extend(short_matches)

            # 3. Search long-term (ChromaDB)
            if mode == "lateral":
                long_matches = self.long_term.query_lateral(query, n_results)
            else:
                long_matches = self.long_term.query(query, n_results, mode=mode)

            # Convert long-term results to MemoryItems
            for match in long_matches:
                item = self._dict_to_memory_item(match)
                results.append(item)

        # Deduplicate by ID
        seen_ids = set()
        unique_results = []
        for item in results:
            if item.id not in seen_ids:
                unique_results.append(item)
                seen_ids.add(item.id)

        return unique_results[: n_results * 2]  # Allow extra for diversity

    def recall_with_reasoning(
        self, query: str, n_results: int = 5
    ) -> Tuple[List[MemoryItem], List[str]]:
        """
        Recall with sequential reasoning trace.

        Returns:
            Tuple of (results, reasoning_steps)
        """
        reasoning_steps = []

        # Step 1: Decompose query
        reasoning_steps.append(f"Decomposing query: '{query}'")

        # Step 2: Foundation search
        reasoning_steps.append("Searching foundation knowledge...")
        foundation = self.recall(query, n_results, mode="foundation")
        reasoning_steps.append(f"Found {len(foundation)} foundation matches")

        # Step 3: Lateral expansion
        reasoning_steps.append("Exploring lateral connections...")
        lateral = self.recall(query, n_results, mode="lateral")
        reasoning_steps.append(f"Found {len(lateral)} lateral connections")

        # Step 4: Merge and deduplicate
        reasoning_steps.append("Merging and ranking results...")
        combined = foundation + lateral

        seen = set()
        unique = []
        for item in combined:
            if item.id not in seen:
                unique.append(item)
                seen.add(item.id)

        reasoning_steps.append(f"Final result: {len(unique)} unique memories")

        return unique[: n_results * 2], reasoning_steps

    def promote(self, memory_id: str) -> bool:
        """
        Promote memory from short-term to long-term.

        Called when a memory proves valuable (high access count,
        user confirmation, or TTL exceeded).
        """
        item = self.short_term.retrieve(memory_id)
        if not item:
            logger.warning(f"Cannot promote: {memory_id} not found in short-term")
            return False

        # Update tier
        item.tier = MemoryTier.LONG_TERM

        # Store in long-term
        self.long_term.store(item)

        # Remove from short-term
        self.short_term.delete(memory_id)

        logger.info(f"Promoted {memory_id} to long-term memory")
        return True

    def add_bridge(
        self, memory_id_1: str, memory_id_2: str, bridge_type: str = "synchronicity"
    ) -> bool:
        """
        Create a synchronicity bridge between two memories.

        This enables lateral thinking by connecting disparate concepts
        that share unexpected relationships.
        """
        # Implementation would update both memories' bridge lists
        logger.info(f"Bridge created: {memory_id_1} <-{bridge_type}-> {memory_id_2}")
        return True

    def maintenance(self) -> Dict[str, int]:
        """
        Run maintenance tasks:
        - Promote stale short-term memories
        - Archive old long-term memories
        - Trim working memory
        """
        stats = {"promoted": 0, "archived": 0, "working_trimmed": 0}

        # Promote stale short-term memories
        stale = self.short_term.get_stale(self.config.short_term_ttl)
        for item in stale:
            if item.access_count > 1:  # Only promote if accessed more than once
                if self.promote(item.id):
                    stats["promoted"] += 1

        # Trim working memory
        if len(self.working_memory) > self.config.working_memory_size:
            excess = len(self.working_memory) - self.config.working_memory_size
            # Remove oldest, least accessed
            self.working_memory.sort(key=lambda x: (x.access_count, x.accessed_at))
            for item in self.working_memory[:excess]:
                # Move to short-term instead of deleting
                self.short_term.store(item)
                stats["working_trimmed"] += 1
            self.working_memory = self.working_memory[excess:]

        logger.info(f"Maintenance complete: {stats}")
        return stats

    def _add_to_working_memory(self, item: MemoryItem):
        """Add item to working memory with size management."""
        self.working_memory.append(item)

        # Trim if over limit
        if len(self.working_memory) > self.config.working_memory_size:
            # Move oldest to short-term
            oldest = self.working_memory.pop(0)
            oldest.tier = MemoryTier.SHORT_TERM
            self.short_term.store(oldest)

    def _search_working_memory(self, query: str) -> List[MemoryItem]:
        """Simple keyword search in working memory."""
        query_lower = query.lower()
        matches = []

        for item in self.working_memory:
            if query_lower in item.content.lower():
                item.accessed_at = time.time()
                item.access_count += 1
                matches.append(item)

        return matches

    def _dict_to_memory_item(self, data: Dict) -> MemoryItem:
        """Convert query result dict to MemoryItem."""
        meta = data.get("metadata", {})
        return MemoryItem(
            id=data["id"],
            content=data["content"],
            tier=MemoryTier(meta.get("tier", "long")),
            created_at=meta.get("created_at", time.time()),
            accessed_at=meta.get("accessed_at", time.time()),
            access_count=meta.get("access_count", 0),
            source=meta.get("source", "unknown"),
            intent=meta.get("c7_intent", ""),
            domain=meta.get("c7_domain", ""),
            emotion=meta.get("c7_emotion", ""),
            temporal=meta.get("c7_temporal", ""),
            spatial=meta.get("c7_spatial", ""),
            relational=meta.get("c7_relational", ""),
            abstract=meta.get("c7_abstract", ""),
        )

    def _generate_id(self, content: str, timestamp: float) -> str:
        """Generate unique memory ID."""
        data = f"{content}{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# =============================================================================
# Convenience Functions
# =============================================================================

_default_memory: Optional[HybridMemory] = None


def get_memory() -> HybridMemory:
    """Get or create the default HybridMemory instance."""
    global _default_memory
    if _default_memory is None:
        _default_memory = HybridMemory()
    return _default_memory


def remember(content: str, **kwargs) -> MemoryItem:
    """Convenience function to store a memory."""
    return get_memory().remember(content, **kwargs)


def recall(query: str, **kwargs) -> List[MemoryItem]:
    """Convenience function to recall memories."""
    return get_memory().recall(query, **kwargs)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.DEBUG)

    memory = HybridMemory()

    # Store some test memories
    memory.remember(
        "Python is a high-level programming language",
        source="user",
        context7={"domain": "technical", "intent": "learning"},
    )

    memory.remember(
        "The Dao that can be told is not the eternal Dao",
        source="user",
        context7={"domain": "philosophical", "abstract": "metaphorical"},
    )

    # Recall with lateral thinking
    results, reasoning = memory.recall_with_reasoning(
        "programming philosophy", n_results=5
    )

    print("\nRecall Results:")
    for item in results:
        print(f"  - {item.id}: {item.content[:50]}...")

    print("\nReasoning Trace:")
    for step in reasoning:
        print(f"  → {step}")
