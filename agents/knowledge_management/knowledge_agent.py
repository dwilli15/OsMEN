#!/usr/bin/env python3
"""
Knowledge Management Agent
Manages knowledge base using Obsidian integration
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from tools.obsidian.obsidian_integration import ObsidianIntegration

# Import knowledge memory integration for semantic search
try:
    from .knowledge_memory import KnowledgeMemoryIntegration, get_knowledge_memory

    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    KnowledgeMemoryIntegration = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeAgent:
    """Agent for knowledge management with Obsidian"""

    def __init__(self, use_semantic_memory: bool = True):
        try:
            self.obsidian = ObsidianIntegration()

            # Initialize semantic memory if available
            self.knowledge_memory: Optional[KnowledgeMemoryIntegration] = None
            if use_semantic_memory and MEMORY_AVAILABLE:
                try:
                    self.knowledge_memory = get_knowledge_memory()
                    logger.info("Semantic memory enabled for KnowledgeAgent")
                except Exception as e:
                    logger.warning(f"Could not initialize semantic memory: {e}")

            logger.info("KnowledgeAgent initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing KnowledgeAgent: {e}")
            raise

    def capture_note(
        self, title: str, content: str, tags: List[str] = None, folder: str = ""
    ) -> Dict:
        """Capture a new note to the knowledge base"""
        try:
            result = self.obsidian.create_note(
                title=title,
                content=content,
                tags=tags or [],
                folder=folder,
                frontmatter={"created": datetime.now().isoformat(), "source": "osmen"},
            )

            # Index in semantic memory for enhanced search
            if self.knowledge_memory and result.get("status") != "error":
                note_path = result.get("path", f"{folder}/{title}.md")
                self.knowledge_memory.index_note(
                    note_path=note_path,
                    title=title,
                    content=content,
                    tags=tags or [],
                    folder=folder,
                    links=[],
                )
                logger.debug(f"Indexed '{title}' in semantic memory")

            logger.info(f"Note '{title}' created successfully")
            return result
        except Exception as e:
            logger.error(f"Error capturing note '{title}': {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to create note: {title}",
            }

    def search_knowledge(self, query: str, semantic: bool = True) -> List[Dict]:
        """Search the knowledge base with optional semantic search"""
        results = []

        # Traditional keyword search from Obsidian
        try:
            keyword_results = self.obsidian.search_notes(query)
            results.extend(keyword_results)
            logger.info(
                f"Keyword search for '{query}' returned {len(keyword_results)} results"
            )
        except Exception as e:
            logger.error(f"Error in keyword search for '{query}': {e}")

        # Semantic search if available and enabled
        if semantic and self.knowledge_memory and self.knowledge_memory.enabled:
            try:
                semantic_results = self.knowledge_memory.semantic_search(
                    query=query, n_results=10, mode="lateral"
                )
                # Add semantic results that aren't duplicates
                seen_paths = {r.get("path", "") for r in results}
                for sr in semantic_results:
                    if sr.note_path not in seen_paths:
                        results.append(
                            {
                                "path": sr.note_path,
                                "content_preview": sr.content_preview,
                                "relevance_score": sr.relevance_score,
                                "source": "semantic",
                                "themes": sr.themes,
                            }
                        )
                logger.info(
                    f"Semantic search added {len(semantic_results)} additional results"
                )
            except Exception as e:
                logger.warning(f"Semantic search failed, using keyword only: {e}")

        return results

    def get_note(self, note_path: str) -> Dict:
        """Retrieve a specific note"""
        try:
            note = self.obsidian.read_note(note_path)
            logger.debug(f"Retrieved note: {note_path}")
            return note
        except Exception as e:
            logger.error(f"Error retrieving note '{note_path}': {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to retrieve note: {note_path}",
            }

    def update_knowledge(
        self, note_path: str, new_content: str, append: bool = True
    ) -> Dict:
        """Update existing knowledge"""
        try:
            result = self.obsidian.update_note(note_path, new_content, append=append)
            logger.info(f"Note '{note_path}' updated successfully")
            return result
        except Exception as e:
            logger.error(f"Error updating note '{note_path}': {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to update note: {note_path}",
            }

    def find_related(self, note_path: str, include_semantic: bool = True) -> Dict:
        """Find notes related to the given note (links + semantic similarity)"""
        try:
            # Get backlinks from Obsidian
            backlinks = self.obsidian.get_backlinks(note_path)

            # Get forward links
            note = self.obsidian.read_note(note_path)
            forward_links = note.get("links", [])

            logger.info(
                f"Found {len(backlinks)} backlinks and {len(forward_links)} forward links for '{note_path}'"
            )

            result = {
                "backlinks": backlinks,
                "forward_links": forward_links,
                "note": note_path,
            }

            # Add semantically related notes (thematic connections)
            if (
                include_semantic
                and self.knowledge_memory
                and self.knowledge_memory.enabled
            ):
                try:
                    thematic = self.knowledge_memory.find_related_by_theme(
                        note_path=note_path, n_results=5
                    )
                    result["thematic_connections"] = [
                        {
                            "path": t.note_path,
                            "themes": t.themes,
                            "relevance": t.relevance_score,
                        }
                        for t in thematic
                    ]
                    logger.info(f"Found {len(thematic)} thematic connections")
                except Exception as e:
                    logger.warning(f"Thematic search failed: {e}")
                    result["thematic_connections"] = []

            return result
        except Exception as e:
            logger.error(f"Error finding related notes for '{note_path}': {e}")
            return {
                "backlinks": [],
                "forward_links": [],
                "note": note_path,
                "error": str(e),
            }

    def get_knowledge_graph(self) -> Dict:
        """Export the complete knowledge graph"""
        try:
            graph = self.obsidian.export_graph()
            logger.info("Knowledge graph exported successfully")
            return graph
        except Exception as e:
            logger.error(f"Error exporting knowledge graph: {e}")
            return {"nodes": [], "edges": [], "error": str(e)}

    def create_daily_note(self, content: str = "") -> Dict:
        """Create a daily note for today"""
        try:
            today = datetime.now()
            title = today.strftime("%Y-%m-%d")
            folder = "Daily Notes"

            daily_content = f"""## Tasks
- [ ] Review daily brief
- [ ] Check system status

## Notes
{content}

## Links
- [[{(today.replace(day=today.day-1)).strftime('%Y-%m-%d')}|Yesterday]]
- [[{(today.replace(day=today.day+1)).strftime('%Y-%m-%d')}|Tomorrow]]
"""

            return self.obsidian.create_note(
                title=title,
                content=daily_content,
                folder=folder,
                tags=["daily-note"],
                frontmatter={"date": title, "type": "daily-note"},
            )
        except Exception as e:
            logger.error(f"Error creating daily note: {e}")
            return {"error": str(e), "status": "failed"}

    def organize_notes(self) -> Dict:
        """Analyze and suggest organization improvements"""
        notes = self.obsidian.list_notes()
        graph = self.obsidian.export_graph()

        # Find orphan notes (no links in or out)
        linked_notes = set()
        for edge in graph["edges"]:
            linked_notes.add(edge["source"])
            linked_notes.add(edge["target"])

        all_notes = {node["id"] for node in graph["nodes"]}
        orphans = all_notes - linked_notes

        return {
            "total_notes": len(notes),
            "linked_notes": len(linked_notes),
            "orphan_notes": list(orphans),
            "graph_density": len(graph["edges"]) / max(len(notes), 1),
        }

    def generate_summary(self, folder: str = "") -> Dict:
        """Generate a summary of knowledge base"""
        notes = self.obsidian.list_notes(folder)

        summary = {
            "total_notes": len(notes),
            "folder": folder or "all",
            "recent_notes": sorted(notes, key=lambda x: x["modified"], reverse=True)[
                :10
            ],
            "semantic_memory_enabled": bool(
                self.knowledge_memory and self.knowledge_memory.enabled
            ),
        }

        return summary

    def surface_forgotten(self, current_context: str, n_results: int = 5) -> List[Dict]:
        """
        Surface potentially forgotten but relevant knowledge.

        Uses semantic memory to find notes that are relevant to the
        current context but may have been forgotten.

        Args:
            current_context: What the user is currently working on
            n_results: Maximum results to return

        Returns:
            List of potentially forgotten relevant notes
        """
        if not self.knowledge_memory or not self.knowledge_memory.enabled:
            logger.info("Semantic memory not available for forgotten knowledge")
            return []

        try:
            forgotten = self.knowledge_memory.get_forgotten_knowledge(
                current_context=current_context, n_results=n_results
            )
            return [
                {
                    "path": f.note_path,
                    "preview": f.content_preview,
                    "themes": f.themes,
                    "relevance": f.relevance_score,
                }
                for f in forgotten
            ]
        except Exception as e:
            logger.error(f"Error surfacing forgotten knowledge: {e}")
            return []

    def index_vault_for_semantic_search(self, progress_callback=None) -> Dict:
        """
        Index all notes in the vault for semantic search.

        This creates embeddings for all existing notes, enabling
        semantic search and thematic discovery.

        Args:
            progress_callback: Optional callback(current, total) for progress

        Returns:
            Statistics about the indexing operation
        """
        if not self.knowledge_memory:
            return {"error": "Semantic memory not available", "indexed": 0}

        try:
            # Get all notes from vault
            all_notes = self.obsidian.list_notes()
            logger.info(f"Indexing {len(all_notes)} notes for semantic search")

            # Convert to format expected by index_vault
            notes_to_index = []
            for note_meta in all_notes:
                try:
                    note = self.obsidian.read_note(note_meta["path"])
                    notes_to_index.append(
                        {
                            "path": note_meta["path"],
                            "title": note.get(
                                "title", note_meta.get("name", "Untitled")
                            ),
                            "content": note.get("content", ""),
                            "tags": note.get("tags", []),
                            "folder": note_meta.get("folder", ""),
                            "links": note.get("links", []),
                        }
                    )
                except Exception as e:
                    logger.warning(f"Could not read note {note_meta['path']}: {e}")

            # Index all notes
            stats = self.knowledge_memory.index_vault(
                notes=notes_to_index, progress_callback=progress_callback
            )

            return stats

        except Exception as e:
            logger.error(f"Error indexing vault: {e}")
            return {"error": str(e), "indexed": 0}


def main():
    """Test the knowledge agent"""
    agent = KnowledgeAgent()

    # Example: Create a note
    result = agent.capture_note(
        title="OsMEN Knowledge Base",
        content="This is the main entry point for OsMEN knowledge management.",
        tags=["osmen", "knowledge-base"],
    )
    print("Created note:")
    print(json.dumps(result, indent=2))

    # Example: Get summary
    summary = agent.generate_summary()
    print("\nKnowledge base summary:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
    main()
    main()
