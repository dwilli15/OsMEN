#!/usr/bin/env python3
"""
OsMEN Hybrid Memory System

Combines multiple memory backends for intelligent agent memory:
- ChromaDB: Long-term semantic memory (vector embeddings, RAG)
- SQLite: Short-term structured memory (sessions, tasks, key-value cache)

Memory Tiers:
1. Ephemeral (RAM): Current conversation context
2. Short-term (SQLite): Session state, recent interactions, task queue
3. Long-term (ChromaDB): Knowledge base, learned patterns, historical data
"""

import hashlib
import json
import os
import sqlite3
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MemoryEntry:
    """A unified memory entry across all backends"""

    id: str
    content: str
    memory_type: str  # 'short_term', 'long_term', 'working'
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_score: Optional[float] = None
    source: str = "unknown"


class SQLiteShortTermMemory:
    """Short-term structured memory using SQLite"""

    def __init__(self, db_path: str = "./data/osmen_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite schema for short-term memory"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Working memory - current session context
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS working_memory (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    context_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    metadata TEXT
                )
            """
            )

            # Session memory - conversation history per session
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS session_memory (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """
            )

            # Sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    agent_name TEXT,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    context TEXT,
                    status TEXT DEFAULT 'active'
                )
            """
            )

            # Task memory - pending actions and their state
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS task_memory (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    due_at DATETIME,
                    completed_at DATETIME,
                    context TEXT,
                    result TEXT
                )
            """
            )

            # Reasoning chains - sequential/lateral thinking traces
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS reasoning_chains (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    chain_type TEXT NOT NULL,  -- 'sequential', 'lateral', 'divergent'
                    step_number INTEGER,
                    thought TEXT NOT NULL,
                    conclusion TEXT,
                    confidence REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """
            )

            # Key-value cache for quick lookups
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    ttl_seconds INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_memory_session ON session_memory(session_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_status ON task_memory(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_reasoning_session ON reasoning_chains(session_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_working_expires ON working_memory(expires_at)"
            )

            conn.commit()

    def set_working_memory(
        self,
        key: str,
        value: Any,
        context_id: str = None,
        ttl_seconds: int = None,
        metadata: Dict = None,
    ) -> bool:
        """Store in working memory (fast key-value access)"""
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO working_memory 
                (key, value, context_id, updated_at, expires_at, metadata)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
            """,
                (
                    key,
                    json.dumps(value),
                    context_id,
                    expires_at,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()
        return True

    def get_working_memory(self, key: str) -> Optional[Any]:
        """Retrieve from working memory"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT value, expires_at FROM working_memory 
                WHERE key = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """,
                (key,),
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None

    def add_session_message(
        self, session_id: str, role: str, content: str, metadata: Dict = None
    ) -> str:
        """Add a message to session memory"""
        msg_id = hashlib.md5(
            f"{session_id}{datetime.now().isoformat()}{content[:50]}".encode()
        ).hexdigest()[:16]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Ensure session exists
            cursor.execute(
                """
                INSERT OR IGNORE INTO sessions (id, started_at) VALUES (?, CURRENT_TIMESTAMP)
            """,
                (session_id,),
            )
            # Update last activity
            cursor.execute(
                "UPDATE sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,),
            )
            # Add message
            cursor.execute(
                """
                INSERT INTO session_memory (id, session_id, role, content, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    msg_id,
                    session_id,
                    role,
                    content,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()
        return msg_id

    def get_session_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Get recent session history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT role, content, timestamp, metadata 
                FROM session_memory WHERE session_id = ?
                ORDER BY timestamp DESC LIMIT ?
            """,
                (session_id, limit),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in reversed(rows)]

    def add_reasoning_step(
        self,
        session_id: str,
        chain_type: str,
        step_number: int,
        thought: str,
        conclusion: str = None,
        confidence: float = None,
        metadata: Dict = None,
    ) -> str:
        """Record a reasoning step (sequential or lateral thinking)"""
        step_id = hashlib.md5(
            f"{session_id}{chain_type}{step_number}{thought[:30]}".encode()
        ).hexdigest()[:16]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO reasoning_chains 
                (id, session_id, chain_type, step_number, thought, conclusion, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    step_id,
                    session_id,
                    chain_type,
                    step_number,
                    thought,
                    conclusion,
                    confidence,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()
        return step_id

    def get_reasoning_chain(
        self, session_id: str, chain_type: str = None
    ) -> List[Dict]:
        """Get reasoning chain for a session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if chain_type:
                cursor.execute(
                    """
                    SELECT * FROM reasoning_chains 
                    WHERE session_id = ? AND chain_type = ?
                    ORDER BY step_number
                """,
                    (session_id, chain_type),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM reasoning_chains 
                    WHERE session_id = ?
                    ORDER BY created_at
                """,
                    (session_id,),
                )
            return [dict(row) for row in cursor.fetchall()]

    def create_task(
        self,
        title: str,
        description: str = None,
        priority: int = 5,
        due_at: datetime = None,
        context: Dict = None,
    ) -> str:
        """Create a task in memory"""
        task_id = hashlib.md5(
            f"{title}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO task_memory (id, title, description, priority, due_at, context)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    task_id,
                    title,
                    description,
                    priority,
                    due_at,
                    json.dumps(context) if context else None,
                ),
            )
            conn.commit()
        return task_id

    def get_pending_tasks(self, limit: int = 10) -> List[Dict]:
        """Get pending tasks ordered by priority"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM task_memory WHERE status = 'pending'
                ORDER BY priority DESC, due_at ASC LIMIT ?
            """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def cache_set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set a cached value"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO kv_cache (key, value, ttl_seconds)
                VALUES (?, ?, ?)
            """,
                (key, json.dumps(value), ttl_seconds),
            )
            conn.commit()
        return True

    def cache_get(self, key: str) -> Optional[Any]:
        """Get a cached value (respects TTL)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT value, ttl_seconds, created_at FROM kv_cache WHERE key = ?
            """,
                (key,),
            )
            row = cursor.fetchone()
            if row:
                value, ttl, created = row
                if ttl:
                    created_dt = datetime.fromisoformat(created)
                    if datetime.now() > created_dt + timedelta(seconds=ttl):
                        cursor.execute("DELETE FROM kv_cache WHERE key = ?", (key,))
                        conn.commit()
                        return None
                return json.loads(value)
        return None

    def cleanup_expired(self):
        """Remove expired entries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM working_memory WHERE expires_at < CURRENT_TIMESTAMP"
            )
            cursor.execute(
                """
                DELETE FROM kv_cache WHERE 
                datetime(created_at, '+' || ttl_seconds || ' seconds') < CURRENT_TIMESTAMP
            """
            )
            conn.commit()


class ChromaDBLongTermMemory:
    """Long-term semantic memory using ChromaDB"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("CHROMADB_URL", "http://localhost:8000")

    def _request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Make HTTP request to ChromaDB"""
        url = f"{self.base_url}{endpoint}"
        req_data = json.dumps(data).encode() if data else None

        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json"} if data else {},
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}", "details": e.read().decode()[:200]}
        except Exception as e:
            return {"error": str(e)}

    def ensure_collection(self, name: str, metadata: Dict = None) -> Dict:
        """Create or get a collection"""
        result = self._request(
            "/api/v1/collections",
            "POST",
            {"name": name, "get_or_create": True, "metadata": metadata or {}},
        )
        return result

    def store(
        self,
        content: str,
        collection: str = "osmen_knowledge",
        metadata: Dict = None,
        doc_id: str = None,
    ) -> Dict:
        """Store content in long-term memory"""
        # Ensure collection exists
        col_result = self.ensure_collection(collection)
        collection_id = col_result.get("id", collection)

        # Generate ID if not provided
        if not doc_id:
            doc_id = hashlib.md5(
                f"{content[:100]}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]

        # Prepare metadata
        full_metadata = {
            "timestamp": datetime.now().isoformat(),
            "source": "osmen_agent",
            **(metadata or {}),
        }

        # Add to collection
        result = self._request(
            f"/api/v1/collections/{collection_id}/add",
            "POST",
            {"ids": [doc_id], "documents": [content], "metadatas": [full_metadata]},
        )

        return {
            "stored": "error" not in result,
            "id": doc_id,
            "collection": collection,
            **result,
        }

    def recall(
        self,
        query: str,
        collection: str = "osmen_knowledge",
        n_results: int = 5,
        where: Dict = None,
    ) -> List[Dict]:
        """Recall from long-term memory using semantic search"""
        # Get collection
        col_result = self._request(f"/api/v1/collections/{collection}", "GET")
        if "error" in col_result:
            return []

        collection_id = col_result.get("id", collection)

        # Query
        query_data = {
            "query_texts": [query],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_data["where"] = where

        result = self._request(
            f"/api/v1/collections/{collection_id}/query", "POST", query_data
        )

        if "error" in result:
            return []

        # Format results
        memories = []
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]

        for i, doc in enumerate(docs):
            memories.append(
                {
                    "id": ids[i] if i < len(ids) else None,
                    "content": doc,
                    "metadata": metas[i] if i < len(metas) else {},
                    "relevance": 1
                    - (
                        dists[i] if i < len(dists) else 1
                    ),  # Convert distance to relevance
                }
            )

        return memories

    def get_collections(self) -> List[str]:
        """List all collections"""
        result = self._request("/api/v1/collections", "GET")
        if isinstance(result, list):
            return [c.get("name", c.get("id")) for c in result]
        return []


class HybridMemoryManager:
    """
    Unified memory manager that coordinates between short-term and long-term memory.

    Implements intelligent memory routing:
    - Ephemeral data → Working memory (SQLite)
    - Session data → Session memory (SQLite)
    - Reasoning traces → SQLite with optional ChromaDB backup
    - Knowledge/facts → ChromaDB (long-term)
    """

    def __init__(self, sqlite_path: str = None, chromadb_url: str = None):
        self.short_term = SQLiteShortTermMemory(
            sqlite_path or os.getenv("OSMEN_MEMORY_DB", "./data/osmen_memory.db")
        )
        self.long_term = ChromaDBLongTermMemory(chromadb_url)

    def remember(
        self,
        content: str,
        memory_type: str = "auto",
        session_id: str = None,
        metadata: Dict = None,
        ttl_seconds: int = None,
    ) -> Dict:
        """
        Intelligent memory storage.

        memory_type:
            - 'working': Ephemeral key-value (use metadata['key'])
            - 'session': Conversation history
            - 'task': Task queue
            - 'reasoning': Thought chains
            - 'knowledge': Long-term facts (ChromaDB)
            - 'auto': Automatically determine based on content
        """
        result = {"stored": False, "memory_type": memory_type}

        if memory_type == "working":
            key = metadata.get("key", hashlib.md5(content.encode()).hexdigest()[:8])
            self.short_term.set_working_memory(
                key, content, session_id, ttl_seconds, metadata
            )
            result.update({"stored": True, "key": key})

        elif memory_type == "session":
            role = metadata.get("role", "assistant")
            msg_id = self.short_term.add_session_message(
                session_id or "default", role, content, metadata
            )
            result.update({"stored": True, "message_id": msg_id})

        elif memory_type == "task":
            task_id = self.short_term.create_task(
                title=metadata.get("title", content[:50]),
                description=content,
                priority=metadata.get("priority", 5),
                context=metadata,
            )
            result.update({"stored": True, "task_id": task_id})

        elif memory_type == "reasoning":
            step_id = self.short_term.add_reasoning_step(
                session_id=session_id or "default",
                chain_type=metadata.get("chain_type", "sequential"),
                step_number=metadata.get("step_number", 1),
                thought=content,
                conclusion=metadata.get("conclusion"),
                confidence=metadata.get("confidence"),
                metadata=metadata,
            )
            result.update({"stored": True, "step_id": step_id})

        elif memory_type == "knowledge":
            store_result = self.long_term.store(
                content=content,
                collection=metadata.get("collection", "osmen_knowledge"),
                metadata=metadata,
            )
            result.update(store_result)

        elif memory_type == "auto":
            # Auto-detect: Long content or factual → ChromaDB, else working memory
            if len(content) > 500 or metadata.get("persist", False):
                return self.remember(content, "knowledge", session_id, metadata)
            else:
                return self.remember(
                    content,
                    "working",
                    session_id,
                    {**metadata, "key": f"auto_{datetime.now().timestamp()}"},
                    ttl_seconds or 3600,
                )

        return result

    def recall(
        self,
        query: str,
        memory_types: List[str] = None,
        session_id: str = None,
        limit: int = 10,
    ) -> Dict[str, List]:
        """
        Multi-source memory recall.

        Returns memories from requested sources, ranked by relevance.
        """
        if memory_types is None:
            memory_types = ["working", "session", "knowledge"]

        results = {}

        if "working" in memory_types:
            # Try exact key match first
            exact = self.short_term.get_working_memory(query)
            results["working"] = (
                [{"content": exact, "match_type": "exact"}] if exact else []
            )

        if "session" in memory_types and session_id:
            history = self.short_term.get_session_history(session_id, limit)
            # Filter by query relevance (simple substring match for now)
            relevant = [
                h for h in history if query.lower() in h.get("content", "").lower()
            ]
            results["session"] = relevant[:limit]

        if "reasoning" in memory_types and session_id:
            chains = self.short_term.get_reasoning_chain(session_id)
            results["reasoning"] = chains

        if "tasks" in memory_types:
            tasks = self.short_term.get_pending_tasks(limit)
            results["tasks"] = tasks

        if "knowledge" in memory_types:
            memories = self.long_term.recall(query, n_results=limit)
            results["knowledge"] = memories

        return results

    def get_context(self, session_id: str, include_knowledge: bool = True) -> Dict:
        """
        Build comprehensive context for an agent.

        Combines:
        - Current session history
        - Active reasoning chains
        - Pending tasks
        - Relevant knowledge (if enabled)
        """
        context = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "history": self.short_term.get_session_history(session_id, 10),
            "reasoning": self.short_term.get_reasoning_chain(session_id),
            "pending_tasks": self.short_term.get_pending_tasks(5),
        }

        if include_knowledge and context["history"]:
            # Get last user message for knowledge retrieval
            last_user_msg = next(
                (
                    h["content"]
                    for h in reversed(context["history"])
                    if h.get("role") == "user"
                ),
                None,
            )
            if last_user_msg:
                context["relevant_knowledge"] = self.long_term.recall(
                    last_user_msg, n_results=3
                )

        return context


# Singleton instance for easy import
_memory_manager: Optional[HybridMemoryManager] = None


def get_memory_manager() -> HybridMemoryManager:
    """Get or create the global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = HybridMemoryManager()
    return _memory_manager
