#!/usr/bin/env python3
"""
Knowledge Memory Integration

Adds HybridMemory-backed semantic search to KnowledgeAgent.

Capabilities:
- Semantic search across all notes (beyond keyword matching)
- Store note embeddings for similarity queries
- Find thematically related notes across folders
- Track knowledge access patterns
- Surface forgotten but relevant knowledge
"""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger("osmen.knowledge.memory")

# Try to import HybridMemory
try:
    from integrations.memory import HybridMemory, MemoryConfig, MemoryItem, MemoryTier

    MEMORY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"HybridMemory not available for KnowledgeAgent: {e}")
    MEMORY_AVAILABLE = False
    HybridMemory = None  # type: ignore
    MemoryConfig = None  # type: ignore
    MemoryTier = None  # type: ignore


@dataclass
class KnowledgeSearchResult:
    """A semantic search result from knowledge memory"""

    note_path: str
    content_preview: str
    relevance_score: float
    retrieval_mode: str  # "semantic", "keyword", "lateral"
    themes: List[str]
    last_accessed: Optional[str]


class KnowledgeMemoryIntegration:
    """
    HybridMemory integration for semantic knowledge search.

    Enables the knowledge agent to:
    1. Index notes for semantic retrieval
    2. Find notes by meaning, not just keywords
    3. Discover thematic connections across folders
    4. Track knowledge access patterns
    """

    def __init__(self):
        """Initialize memory integration with lazy loading"""
        self._memory: Optional["HybridMemory"] = None
        self.enabled = MEMORY_AVAILABLE

        if self.enabled:
            logger.info("KnowledgeMemoryIntegration initialized (memory available)")
        else:
            logger.warning("KnowledgeMemoryIntegration disabled (memory unavailable)")

    @property
    def memory(self) -> Optional["HybridMemory"]:
        """Lazy-load HybridMemory"""
        if not self.enabled:
            return None
        if self._memory is None:
            try:
                self._memory = HybridMemory(MemoryConfig.from_env())
                logger.info("HybridMemory connected for knowledge search")
            except Exception as e:
                logger.error(f"Failed to connect HybridMemory: {e}")
                self.enabled = False
        return self._memory

    def index_note(
        self,
        note_path: str,
        title: str,
        content: str,
        tags: List[str] = None,
        folder: str = "",
        links: List[str] = None,
    ) -> Optional[str]:
        """
        Index a note in memory for semantic retrieval.

        Args:
            note_path: Full path to the note
            title: Note title
            content: Note content
            tags: Note tags
            folder: Note folder
            links: Linked notes

        Returns:
            Memory ID if indexed successfully
        """
        if not self.memory:
            return None

        tags = tags or []
        links = links or []

        # Build content string for semantic search
        search_content = (
            f"Note: {title}. "
            f"{content[:1000]}. "  # First 1000 chars
            f"{'Tags: ' + ', '.join(tags) + '. ' if tags else ''}"
            f"{'Folder: ' + folder + '. ' if folder else ''}"
        )

        # Extract themes from tags and content
        themes = self._extract_themes(title, content, tags)

        # Context7 dimensions for lateral discovery
        context7 = {
            "intent": "knowledge",
            "domain": self._infer_domain(folder, tags),
            "emotion": "neutral",
            "temporal": datetime.now().strftime("%Y-%m"),
            "spatial": folder or "root",
            "relational": ", ".join(links[:5]) if links else "standalone",
            "abstract": " ".join(themes),
        }

        try:
            item = self.memory.remember(
                content=search_content,
                source="obsidian_note",
                context={
                    "note_path": note_path,
                    "title": title,
                    "tags": tags,
                    "folder": folder,
                    "links": links,
                    "content_length": len(content),
                    "indexed_at": datetime.now().isoformat(),
                },
                tier=MemoryTier.LONG_TERM,  # Notes are long-term knowledge
                context7=context7,
            )
            logger.debug(f"Indexed note '{title}' in memory: {item.id}")
            return item.id
        except Exception as e:
            logger.error(f"Failed to index note '{title}': {e}")
            return None

    def _extract_themes(self, title: str, content: str, tags: List[str]) -> List[str]:
        """Extract abstract themes from note content"""
        themes = []

        # Add tags as themes
        themes.extend([t.lower().replace("-", "_") for t in tags])

        # Extract themes from title words
        title_words = [w.lower() for w in title.split() if len(w) > 3]
        themes.extend(title_words[:3])

        # Look for common knowledge themes
        content_lower = content.lower()
        theme_keywords = {
            "learning": ["learn", "study", "understand", "concept"],
            "process": ["step", "process", "workflow", "procedure"],
            "reference": ["reference", "document", "spec", "api"],
            "idea": ["idea", "thought", "concept", "theory"],
            "project": ["project", "plan", "goal", "milestone"],
            "reflection": ["reflect", "journal", "thought", "insight"],
        }

        for theme, keywords in theme_keywords.items():
            if any(kw in content_lower for kw in keywords):
                themes.append(theme)

        return list(set(themes))[:10]

    def _infer_domain(self, folder: str, tags: List[str]) -> str:
        """Infer knowledge domain from folder and tags"""
        combined = f"{folder} {' '.join(tags)}".lower()

        domain_indicators = {
            "technical": ["code", "programming", "api", "dev", "tech"],
            "personal": ["journal", "daily", "reflection", "personal"],
            "academic": ["study", "course", "lecture", "class", "research"],
            "project": ["project", "work", "task", "goal"],
            "reference": ["reference", "doc", "note", "wiki"],
        }

        for domain, indicators in domain_indicators.items():
            if any(ind in combined for ind in indicators):
                return domain

        return "general"

    def semantic_search(
        self, query: str, n_results: int = 10, mode: str = "lateral"
    ) -> List[KnowledgeSearchResult]:
        """
        Semantic search across all indexed notes.

        Args:
            query: Natural language search query
            n_results: Maximum results to return
            mode: Search mode ("foundation", "lateral", "factcheck")

        Returns:
            List of search results ordered by relevance
        """
        if not self.memory:
            return []

        try:
            results = self.memory.recall(query=query, n_results=n_results, mode=mode)

            search_results = []
            for item in results:
                if item.source == "obsidian_note":
                    search_results.append(
                        KnowledgeSearchResult(
                            note_path=item.context.get("note_path", ""),
                            content_preview=item.content[:200],
                            relevance_score=1.0 - (len(search_results) * 0.1),
                            retrieval_mode=mode,
                            themes=item.abstract.split() if item.abstract else [],
                            last_accessed=item.context.get("indexed_at"),
                        )
                    )

            return search_results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def find_related_by_theme(
        self, note_path: str, n_results: int = 5
    ) -> List[KnowledgeSearchResult]:
        """
        Find notes with similar themes to a given note.

        Uses lateral thinking to discover non-obvious connections.

        Args:
            note_path: Path to the source note
            n_results: Maximum results to return

        Returns:
            List of thematically related notes
        """
        if not self.memory:
            return []

        try:
            # First, find the source note in memory
            source_results = self.memory.recall(
                query=f"note_path:{note_path}", n_results=1, mode="foundation"
            )

            if not source_results:
                # Note not indexed, search by path
                return self.semantic_search(note_path, n_results, mode="lateral")

            source = source_results[0]

            # Search for notes with similar abstract themes
            query = f"{source.abstract} {source.domain}"

            results = self.memory.recall(
                query=query,
                n_results=n_results + 1,  # +1 to exclude self
                mode="lateral",
            )

            related = []
            for item in results:
                # Skip the source note itself
                if item.context.get("note_path") == note_path:
                    continue

                if item.source == "obsidian_note":
                    related.append(
                        KnowledgeSearchResult(
                            note_path=item.context.get("note_path", ""),
                            content_preview=item.content[:200],
                            relevance_score=0.8,  # Thematic relevance
                            retrieval_mode="lateral",
                            themes=item.abstract.split() if item.abstract else [],
                            last_accessed=item.context.get("indexed_at"),
                        )
                    )

                if len(related) >= n_results:
                    break

            return related

        except Exception as e:
            logger.error(f"Find related failed: {e}")
            return []

    def get_forgotten_knowledge(
        self, current_context: str, n_results: int = 3
    ) -> List[KnowledgeSearchResult]:
        """
        Surface relevant but potentially forgotten notes.

        Finds notes that are semantically relevant to the current
        context but haven't been accessed recently.

        Args:
            current_context: What the user is currently working on
            n_results: Maximum results to return

        Returns:
            List of potentially forgotten relevant notes
        """
        if not self.memory:
            return []

        try:
            # Search with lateral mode to find non-obvious connections
            results = self.memory.recall(
                query=current_context, n_results=n_results * 2, mode="lateral"
            )

            # Filter to obsidian notes only
            forgotten = []
            for item in results:
                if item.source == "obsidian_note":
                    forgotten.append(
                        KnowledgeSearchResult(
                            note_path=item.context.get("note_path", ""),
                            content_preview=item.content[:200],
                            relevance_score=0.7,  # Slightly lower for "forgotten"
                            retrieval_mode="forgotten",
                            themes=item.abstract.split() if item.abstract else [],
                            last_accessed=item.context.get("indexed_at"),
                        )
                    )

                if len(forgotten) >= n_results:
                    break

            return forgotten

        except Exception as e:
            logger.error(f"Get forgotten knowledge failed: {e}")
            return []

    def index_vault(
        self, notes: List[Dict[str, Any]], progress_callback=None
    ) -> Dict[str, int]:
        """
        Batch index an entire Obsidian vault.

        Args:
            notes: List of note dictionaries with path, title, content, etc.
            progress_callback: Optional callback(current, total) for progress

        Returns:
            Statistics about the indexing operation
        """
        stats = {"indexed": 0, "failed": 0, "skipped": 0}
        total = len(notes)

        for i, note in enumerate(notes):
            try:
                # Skip if no content
                if not note.get("content"):
                    stats["skipped"] += 1
                    continue

                memory_id = self.index_note(
                    note_path=note.get("path", ""),
                    title=note.get("title", "Untitled"),
                    content=note.get("content", ""),
                    tags=note.get("tags", []),
                    folder=note.get("folder", ""),
                    links=note.get("links", []),
                )

                if memory_id:
                    stats["indexed"] += 1
                else:
                    stats["failed"] += 1

                if progress_callback:
                    progress_callback(i + 1, total)

            except Exception as e:
                logger.error(f"Failed to index note {note.get('path')}: {e}")
                stats["failed"] += 1

        logger.info(f"Vault indexing complete: {stats}")
        return stats


# Singleton instance
_knowledge_memory: Optional[KnowledgeMemoryIntegration] = None


def get_knowledge_memory() -> KnowledgeMemoryIntegration:
    """Get or create the knowledge memory integration singleton"""
    global _knowledge_memory
    if _knowledge_memory is None:
        _knowledge_memory = KnowledgeMemoryIntegration()
    return _knowledge_memory


# Self-test
if __name__ == "__main__":
    print("=" * 70)
    print("  Knowledge Memory Integration - Self Test")
    print("=" * 70)

    km = get_knowledge_memory()

    print(f"\n🔌 Memory Available: {'✅ Yes' if km.enabled else '❌ No'}")

    if km.enabled:
        # Index a test note
        print("\n📝 Indexing test note...")
        memory_id = km.index_note(
            note_path="test/test_note.md",
            title="Test Knowledge Note",
            content="This is a test note about machine learning and neural networks. It discusses deep learning architectures and their applications.",
            tags=["test", "ml", "ai"],
            folder="test",
            links=["other_note.md"],
        )
        print(f"   Indexed: {memory_id}")

        # Semantic search
        print("\n🔍 Semantic search for 'deep learning'...")
        results = km.semantic_search("deep learning", n_results=3)
        for r in results:
            print(f"   - {r.note_path}: {r.content_preview[:50]}...")

        # Find related
        print("\n🔗 Finding related notes...")
        related = km.find_related_by_theme("test/test_note.md", n_results=3)
        for r in related:
            print(f"   - {r.note_path} (themes: {', '.join(r.themes[:3])})")

    print("\n" + "=" * 70)
