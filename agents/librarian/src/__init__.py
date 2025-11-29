"""
Librarian RAG Engine - Actual Source from osmen-librarian

This module contains the real RAG implementation ported from:
https://github.com/dwilli15/osmen-librarian

Components:
- rag_manager: Core RAG engine with ChromaDB and Stella embeddings
- lateral_thinking: Lateral thinking engine with Context7 dimensions
- retrieval: ChromaDB-based retrieval implementations
- modes: Foundation and Lateral retrieval modes
- graph: LangGraph orchestration
"""

__version__ = "1.0.0"
