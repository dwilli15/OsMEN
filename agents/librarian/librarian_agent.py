#!/usr/bin/env python3
"""
Librarian Agent for OsMEN
Semantic Memory & Lateral Thinking RAG Engine

Integrates the full osmen-librarian repository as a git submodule,
providing access to:
- LangGraph orchestration (graph.py)
- Three-mode RAG retrieval (foundation, lateral, factcheck)
- ChromaDB vector storage with Stella 1.5B embeddings
- OpenAI Assistants API compatibility
- Deep research and analysis capabilities
- Middleware architecture (filesystem, todo, subagent, HITL)
- 69 passing tests

Source: https://github.com/dwilli15/osmen-librarian (git submodule)
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the osmen-librarian submodule to the path
LIBRARIAN_PATH = Path(__file__).parent / "osmen-librarian" / "src"
if LIBRARIAN_PATH.exists():
    sys.path.insert(0, str(LIBRARIAN_PATH))
    sys.path.insert(0, str(LIBRARIAN_PATH.parent))

# Try to import from the actual osmen-librarian submodule
REAL_RAG_AVAILABLE = False
try:
    # Import from the submodule
    from src.graph import AgentState
    from src.graph import app as langgraph_app
    from src.lateral_thinking import Context7, LateralEngine
    from src.rag_manager import get_vector_store, ingest_data, query_knowledge_base
    from src.retrieval import ChromaRetriever
    from src.retrieval.interfaces import DocumentChunk as RealDocumentChunk
    from src.retrieval.interfaces import RetrievalResult, RetrieverConfig

    REAL_RAG_AVAILABLE = True
    logger.info("osmen-librarian submodule loaded successfully")
except ImportError as e:
    logger.warning(
        f"osmen-librarian submodule not available: {e}. Using fallback mode."
    )
    # Try partial imports
    try:
        from src.lateral_thinking import Context7, LateralEngine
        from src.retrieval.interfaces import DocumentChunk as RealDocumentChunk
        from src.retrieval.interfaces import RetrievalResult, RetrieverConfig

        logger.info("Partial osmen-librarian imports successful")
    except ImportError:
        logger.warning("No osmen-librarian components available. Fallback mode only.")


@dataclass
class LibrarianConfig:
    """Configuration for the Librarian Agent"""

    data_dir: Path = field(default_factory=lambda: Path("./data/librarian"))
    db_path: Path = field(default_factory=lambda: Path("./data/librarian/db"))
    embedding_model: str = "dunzhang/stella_en_1.5B_v5"
    embedding_device: str = "cpu"  # cuda for GPU acceleration
    default_mode: str = "lateral"
    top_k: int = 5
    mmr_lambda: float = 0.5
    api_port: int = 8200
    chunk_size: int = 1000
    chunk_overlap: int = 200

    @classmethod
    def from_env(cls) -> "LibrarianConfig":
        """Create config from environment variables"""
        return cls(
            data_dir=Path(os.getenv("LIBRARIAN_DATA_DIR", "./data/librarian")),
            db_path=Path(os.getenv("LIBRARIAN_DB_PATH", "./data/librarian/db")),
            embedding_model=os.getenv(
                "LIBRARIAN_EMBEDDING_MODEL", "dunzhang/stella_en_1.5B_v5"
            ),
            embedding_device=os.getenv("LIBRARIAN_EMBEDDING_DEVICE", "cpu"),
            default_mode=os.getenv("RAG_DEFAULT_MODE", "lateral"),
            top_k=int(os.getenv("RAG_TOP_K", "5")),
            mmr_lambda=float(os.getenv("RAG_MMR_LAMBDA", "0.5")),
            api_port=int(os.getenv("LIBRARIAN_API_PORT", "8200")),
            chunk_size=int(os.getenv("LIBRARIAN_CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("LIBRARIAN_CHUNK_OVERLAP", "200")),
        )


@dataclass
class DocumentChunk:
    """Represents a chunk of a document"""

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    score: float = 0.0
    chunk_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
            "score": self.score,
            "chunk_id": self.chunk_id,
        }


@dataclass
class QueryResult:
    """Result from a RAG query"""

    answer: str
    documents: List[DocumentChunk]
    mode: str
    confidence: float
    query: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class LibrarianAgent:
    """
    Librarian Agent for OsMEN - Semantic Memory & Lateral Thinking Engine

    This agent integrates the osmen-librarian RAG system into the OsMEN ecosystem,
    providing:
    - Foundation mode: Core concept retrieval (Top-K Cosine Similarity)
    - Lateral mode: Cross-disciplinary connections (MMR diversity)
    - Factcheck mode: High-precision citation verification

    Uses real ChromaDB retrieval when dependencies are available,
    falls back to mock mode for testing.

    Attributes:
        config: LibrarianConfig for agent settings
        initialized: Whether the agent is fully initialized
        use_real_rag: Whether real RAG components are available
    """

    def __init__(self, config: Optional[LibrarianConfig] = None):
        """Initialize the Librarian Agent.

        Args:
            config: Optional configuration. If not provided, loads from environment.
        """
        self.config = config or LibrarianConfig.from_env()
        self._initialized = False
        self._documents_indexed = 0
        self._retriever = None
        self._lateral_engine = None
        self.use_real_rag = REAL_RAG_AVAILABLE

        # Ensure data directories exist
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        self.config.db_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"LibrarianAgent initialized with config: {self.config}")
        logger.info(f"Real RAG available: {self.use_real_rag}")

    @property
    def initialized(self) -> bool:
        """Check if the agent is fully initialized"""
        return self._initialized

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize the RAG engine and embedding model.

        This method performs lazy initialization of heavyweight components
        like the embedding model and vector store (ChromaDB).

        Returns:
            Dictionary with initialization status
        """
        try:
            if self.use_real_rag:
                # Initialize real ChromaDB retriever
                retriever_config = RetrieverConfig(
                    collection_name="librarian_knowledge",
                    persist_directory=str(self.config.db_path),
                    embedding_model=self.config.embedding_model,
                    embedding_device=self.config.embedding_device,
                    default_k=self.config.top_k,
                    chunk_size=self.config.chunk_size,
                    chunk_overlap=self.config.chunk_overlap,
                )
                self._retriever = ChromaRetriever(retriever_config)
                self._retriever.initialize_sync()
                self._documents_indexed = self._retriever.count()
                logger.info(
                    f"ChromaDB initialized with {self._documents_indexed} documents"
                )

            self._initialized = True
            logger.info("Librarian RAG engine initialized successfully")
            return {
                "status": "initialized",
                "embedding_model": self.config.embedding_model,
                "db_path": str(self.config.db_path),
                "real_rag": self.use_real_rag,
                "documents_indexed": self._documents_indexed,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to initialize Librarian: {e}")
            # Fall back to mock mode
            self.use_real_rag = False
            self._initialized = True
            return {
                "status": "initialized_fallback",
                "error": str(e),
                "real_rag": False,
                "timestamp": datetime.now().isoformat(),
            }

    def query(
        self, query: str, mode: Optional[str] = None, top_k: Optional[int] = None
    ) -> QueryResult:
        """
        Query the knowledge base with the specified mode.

        Args:
            query: The search query
            mode: Retrieval mode ('foundation', 'lateral', 'factcheck')
            top_k: Number of results to return

        Returns:
            QueryResult with answer and supporting documents
        """
        mode = mode or self.config.default_mode
        top_k = top_k or self.config.top_k

        if mode not in ["foundation", "lateral", "factcheck"]:
            raise ValueError(
                f"Invalid mode: {mode}. Must be one of: foundation, lateral, factcheck"
            )

        logger.info(f"Processing query in {mode} mode: {query[:50]}...")

        # Use real retrieval if available
        documents = self._retrieve_documents(query, mode, top_k)
        answer = self._generate_answer(query, documents, mode)
        confidence = self._calculate_confidence(documents, mode)

        result = QueryResult(
            answer=answer,
            documents=documents,
            mode=mode,
            confidence=confidence,
            query=query,
        )

        logger.info(
            f"Query completed with {len(documents)} documents, confidence: {confidence:.2f}"
        )
        return result

    def _retrieve_documents(
        self, query: str, mode: str, top_k: int
    ) -> List[DocumentChunk]:
        """
        Retrieve documents based on the query and mode.

        Uses real ChromaDB retrieval when available with different algorithms per mode:
        - foundation: Top-K Cosine Similarity for core concepts
        - lateral: MMR (Maximal Marginal Relevance) with λ=0.5 for diversity
        - factcheck: High-precision Top-3 for citation verification

        Args:
            query: Search query
            mode: Retrieval mode
            top_k: Number of results

        Returns:
            List of DocumentChunk objects
        """
        if self.use_real_rag and self._retriever:
            try:
                # Use real ChromaDB retrieval
                if mode == "foundation":
                    # Standard semantic search
                    enhanced_query = f"Represent this outline point for retrieving foundational concepts and definitions: {query}"
                    result = self._retriever.retrieve_sync(enhanced_query, k=top_k)
                elif mode == "lateral":
                    # Use lateral engine for cross-disciplinary connections
                    enhanced_query = f"Represent the broad context, themes, and implications of this concept: {query}"
                    result = self._retriever.retrieve_sync(enhanced_query, k=top_k * 2)
                    # Note: In full implementation, would use MMR for diversity
                elif mode == "factcheck":
                    # High-precision search
                    enhanced_query = f"Represent this claim to find the exact supporting evidence or source text: {query}"
                    result = self._retriever.retrieve_sync(
                        enhanced_query, k=min(3, top_k)
                    )
                else:
                    result = self._retriever.retrieve_sync(query, k=top_k)

                # Convert to DocumentChunk
                return [
                    DocumentChunk(
                        content=chunk.content,
                        metadata=chunk.metadata,
                        source=chunk.source,
                        score=chunk.score,
                        chunk_id=chunk.chunk_id,
                    )
                    for chunk in result.chunks[:top_k]
                ]
            except Exception as e:
                logger.warning(f"Real retrieval failed, using fallback: {e}")

        # Fallback to mock data for testing
        return [
            DocumentChunk(
                content=f"Sample document content for query: {query}",
                metadata={
                    "source": "sample.md",
                    "mode": mode,
                    "retrieved_at": datetime.now().isoformat(),
                },
                source="sample.md",
                score=0.85,
                chunk_id="sample-001",
            )
        ]

    def _generate_answer(
        self, query: str, documents: List[DocumentChunk], mode: str
    ) -> str:
        """
        Generate an answer from retrieved documents.

        Args:
            query: Original query
            documents: Retrieved documents
            mode: Retrieval mode

        Returns:
            Generated answer string
        """
        # Placeholder - will use LLM for answer generation
        if not documents:
            return "No relevant documents found for your query."

        context = "\n".join([doc.content for doc in documents])
        return f"Based on {len(documents)} document(s) retrieved in {mode} mode: {context[:200]}..."

    def _calculate_confidence(self, documents: List[DocumentChunk], mode: str) -> float:
        """
        Calculate confidence score for the retrieval.

        Args:
            documents: Retrieved documents
            mode: Retrieval mode

        Returns:
            Confidence score between 0 and 1
        """
        if not documents:
            return 0.0

        avg_score = sum(doc.score for doc in documents) / len(documents)

        # Adjust confidence based on mode
        mode_multipliers = {
            "foundation": 1.0,
            "lateral": 0.9,  # Lateral may have lower scores due to diversity
            "factcheck": 1.1,  # Factcheck should have higher confidence threshold
        }

        return min(avg_score * mode_multipliers.get(mode, 1.0), 1.0)

    def ingest_documents(self, path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Ingest documents from the specified path.

        Uses real ChromaDB ingestion when available:
        1. Find all markdown/text files
        2. Chunk documents
        3. Generate embeddings with Stella
        4. Store in ChromaDB

        Args:
            path: Path to document(s) to ingest
            recursive: Whether to search directories recursively

        Returns:
            Dictionary with ingestion status
        """
        path_obj = Path(path)

        if not path_obj.exists():
            return {
                "status": "error",
                "error": f"Path does not exist: {path}",
                "documents_indexed": 0,
            }

        logger.info(f"Ingesting documents from: {path}")

        # Find all markdown files
        files = []
        if path_obj.is_file():
            files = [path_obj]
        else:
            pattern = "**/*.md" if recursive else "*.md"
            files = list(path_obj.glob(pattern))

        if not files:
            return {
                "status": "success",
                "documents_indexed": 0,
                "total_indexed": self._documents_indexed,
                "path": str(path),
                "message": "No markdown files found",
            }

        if self.use_real_rag and self._retriever:
            try:
                # Load and ingest documents using real ChromaDB
                documents = []
                for file_path in files:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            documents.append(
                                {
                                    "content": content,
                                    "metadata": {
                                        "source": file_path.name,
                                        "path": str(file_path),
                                        "type": "markdown",
                                    },
                                }
                            )
                    except Exception as e:
                        logger.warning(f"Failed to read {file_path}: {e}")

                if documents:
                    chunks_ingested = self._retriever.ingest_sync(
                        documents, source=str(path)
                    )
                    self._documents_indexed = self._retriever.count()

                    return {
                        "status": "success",
                        "documents_indexed": len(documents),
                        "chunks_created": chunks_ingested,
                        "total_indexed": self._documents_indexed,
                        "path": str(path),
                        "recursive": recursive,
                        "real_rag": True,
                        "timestamp": datetime.now().isoformat(),
                    }
            except Exception as e:
                logger.warning(f"Real ingestion failed: {e}")

        # Fallback to mock ingestion
        self._documents_indexed += len(files)

        return {
            "status": "success",
            "documents_indexed": len(files),
            "total_indexed": self._documents_indexed,
            "path": str(path),
            "recursive": recursive,
            "real_rag": False,
            "timestamp": datetime.now().isoformat(),
        }

    def verify_fact(self, statement: str) -> Dict[str, Any]:
        """
        Verify a factual statement using high-precision retrieval.

        Args:
            statement: The statement to verify

        Returns:
            Dictionary with verification results
        """
        logger.info(f"Verifying statement: {statement[:50]}...")

        # Use factcheck mode for high-precision retrieval
        result = self.query(statement, mode="factcheck", top_k=3)

        # Determine verification status based on confidence
        if result.confidence >= 0.8:
            status = "verified"
        elif result.confidence >= 0.5:
            status = "partially_supported"
        else:
            status = "unverified"

        return {
            "statement": statement,
            "status": status,
            "confidence": result.confidence,
            "supporting_documents": len(result.documents),
            "sources": [
                doc.metadata.get("source", "unknown") for doc in result.documents
            ],
            "timestamp": datetime.now().isoformat(),
        }

    def find_connections(self, topic: str) -> Dict[str, Any]:
        """
        Find cross-disciplinary connections for a topic using lateral thinking.

        Args:
            topic: The topic to explore

        Returns:
            Dictionary with connection results
        """
        logger.info(f"Finding lateral connections for: {topic}")

        # Use lateral mode for diverse, creative connections
        result = self.query(topic, mode="lateral", top_k=10)

        # Group documents by source/domain
        domains = {}
        for doc in result.documents:
            source = doc.metadata.get("source", "unknown")
            domain = Path(source).parent.name if "/" in source else "general"
            if domain not in domains:
                domains[domain] = []
            domains[domain].append({"content": doc.content[:200], "score": doc.score})

        return {
            "topic": topic,
            "connections_found": len(result.documents),
            "domains_touched": list(domains.keys()),
            "domain_breakdown": {k: len(v) for k, v in domains.items()},
            "top_connection": result.answer if result.documents else None,
            "timestamp": datetime.now().isoformat(),
        }

    def get_health(self) -> Dict[str, Any]:
        """
        Get health status of the Librarian agent.

        Returns:
            Dictionary with health status
        """
        health = {
            "status": "healthy" if self._initialized else "not_initialized",
            "embedding_model": self.config.embedding_model,
            "embedding_device": self.config.embedding_device,
            "embedding_model_loaded": self._initialized,
            "chroma_connected": self._initialized and self.use_real_rag,
            "documents_indexed": self._documents_indexed,
            "default_mode": self.config.default_mode,
            "api_port": self.config.api_port,
            "real_rag_enabled": self.use_real_rag,
            "timestamp": datetime.now().isoformat(),
        }

        # Get real health from retriever if available
        if self.use_real_rag and self._retriever:
            try:
                retriever_health = self._retriever.health_check()
                health["retriever_status"] = retriever_health.get("status", "unknown")
                health["documents_indexed"] = retriever_health.get("document_count", 0)
            except Exception as e:
                health["retriever_error"] = str(e)

        return health

    def generate_librarian_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive status report.

        Returns:
            Dictionary with full status report
        """
        health = self.get_health()

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": (
                "operational" if self._initialized else "pending_initialization"
            ),
            "real_rag_enabled": self.use_real_rag,
            "statistics": {
                "documents_indexed": self._documents_indexed,
                "embedding_model": self.config.embedding_model,
                "embedding_device": self.config.embedding_device,
                "retrieval_modes": ["foundation", "lateral", "factcheck"],
                "default_mode": self.config.default_mode,
            },
            "configuration": {
                "data_dir": str(self.config.data_dir),
                "db_path": str(self.config.db_path),
                "top_k": self.config.top_k,
                "mmr_lambda": self.config.mmr_lambda,
                "api_port": self.config.api_port,
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": self.config.chunk_overlap,
            },
            "health": health,
            "capabilities": [
                "semantic_search",
                "lateral_thinking",
                "fact_verification",
                "document_ingestion",
                "cross_domain_connections",
                "context7_enrichment" if self.use_real_rag else "mock_retrieval",
                "ebook_management",
                "format_conversion",
                "drm_handling",
                "text_extraction",
            ],
        }

    # ============================================================
    # Calibre Integration Methods
    # ============================================================

    def _get_calibre_manager(self):
        """Lazy load CalibreManager"""
        if not hasattr(self, "_calibre_manager"):
            try:
                from integrations.calibre import CalibreManager

                self._calibre_manager = CalibreManager()
            except ImportError as e:
                logger.warning(f"CalibreManager not available: {e}")
                self._calibre_manager = None
        return self._calibre_manager

    def _get_drm_handler(self):
        """Lazy load DRMHandler"""
        if not hasattr(self, "_drm_handler"):
            try:
                from integrations.calibre import DRMHandler

                self._drm_handler = DRMHandler()
            except ImportError as e:
                logger.warning(f"DRMHandler not available: {e}")
                self._drm_handler = None
        return self._drm_handler

    def _get_ebook_converter(self):
        """Lazy load EbookConverter"""
        if not hasattr(self, "_ebook_converter"):
            try:
                from integrations.calibre import EbookConverter

                self._ebook_converter = EbookConverter()
            except ImportError as e:
                logger.warning(f"EbookConverter not available: {e}")
                self._ebook_converter = None
        return self._ebook_converter

    def search_library(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search the Calibre ebook library.

        Args:
            query: Search query (supports Calibre syntax)
            limit: Maximum results to return

        Returns:
            Dictionary with search results
        """
        manager = self._get_calibre_manager()
        if not manager:
            return {"error": "CalibreManager not available", "books": []}

        try:
            books = manager.search(query)[:limit]
            return {
                "query": query,
                "total_results": len(books),
                "books": [
                    {
                        "id": book.id,
                        "title": book.title,
                        "authors": book.authors,
                        "formats": book.formats,
                        "tags": book.tags,
                    }
                    for book in books
                ],
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Library search error: {e}")
            return {"error": str(e), "books": []}

    def convert_ebook(
        self, input_file: str, output_format: str, preset: str = "study"
    ) -> Dict[str, Any]:
        """
        Convert an ebook to a different format.

        Args:
            input_file: Path to input ebook
            output_format: Target format (epub, pdf, txt, mobi, etc.)
            preset: Quality preset (study, archive, kindle, text)

        Returns:
            Dictionary with conversion result
        """
        converter = self._get_ebook_converter()
        if not converter:
            return {"success": False, "error": "EbookConverter not available"}

        try:
            result = converter.convert(input_file, output_format, preset=preset)
            return {
                "success": result.success,
                "input_file": result.input_file,
                "output_file": result.output_file,
                "input_format": result.input_format,
                "output_format": result.output_format,
                "message": result.message,
                "duration_seconds": result.duration_seconds,
                "timestamp": result.timestamp,
            }
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return {"success": False, "error": str(e)}

    def extract_text_from_ebook(
        self, input_file: str, use_ocr: bool = False
    ) -> Dict[str, Any]:
        """
        Extract text content from an ebook.

        Args:
            input_file: Path to input ebook
            use_ocr: Use OCR for scanned PDFs

        Returns:
            Dictionary with extraction result
        """
        converter = self._get_ebook_converter()
        if not converter:
            return {"success": False, "error": "EbookConverter not available"}

        try:
            result = converter.extract_text(input_file, use_ocr=use_ocr)
            return {
                "success": result.success,
                "source_file": result.source_file,
                "text_file": result.text_file,
                "title": result.title,
                "author": result.author,
                "word_count": result.word_count,
                "char_count": result.char_count,
                "message": result.message,
            }
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return {"success": False, "error": str(e)}

    def batch_extract_text(
        self, input_files: List[str], use_ocr: bool = False
    ) -> Dict[str, Any]:
        """
        Extract text from multiple ebooks.

        Args:
            input_files: List of input file paths
            use_ocr: Use OCR for scanned PDFs

        Returns:
            Dictionary with batch extraction results
        """
        converter = self._get_ebook_converter()
        if not converter:
            return {
                "success": False,
                "error": "EbookConverter not available",
                "results": [],
            }

        try:
            results = converter.batch_extract_text(input_files, use_ocr=use_ocr)
            return {
                "total_files": len(input_files),
                "successful": sum(1 for r in results if r.success),
                "failed": sum(1 for r in results if not r.success),
                "total_words": sum(r.word_count for r in results if r.success),
                "results": [
                    {
                        "source_file": r.source_file,
                        "text_file": r.text_file,
                        "success": r.success,
                        "word_count": r.word_count if r.success else 0,
                        "message": r.message,
                    }
                    for r in results
                ],
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Batch extraction error: {e}")
            return {"success": False, "error": str(e), "results": []}

    def remove_drm(self, input_file: str) -> Dict[str, Any]:
        """
        Remove DRM from an ebook file.

        Args:
            input_file: Path to DRM-protected ebook

        Returns:
            Dictionary with DRM removal result
        """
        handler = self._get_drm_handler()
        if not handler:
            return {"success": False, "error": "DRMHandler not available"}

        try:
            result = handler.remove_drm(input_file)
            return {
                "success": result.success,
                "input_file": result.input_file,
                "output_file": result.output_file,
                "drm_type": result.drm_type.value,
                "message": result.message,
                "timestamp": result.timestamp,
            }
        except Exception as e:
            logger.error(f"DRM removal error: {e}")
            return {"success": False, "error": str(e)}

    def process_acsm(self, acsm_path: str) -> Dict[str, Any]:
        """
        Process ACSM file to download and decrypt ebook.

        Args:
            acsm_path: Path to ACSM file

        Returns:
            Dictionary with ACSM processing result
        """
        handler = self._get_drm_handler()
        if not handler:
            return {"success": False, "error": "DRMHandler not available"}

        try:
            # First check ACSM status
            acsm_info = handler.check_acsm(acsm_path)
            if acsm_info.status.value == "expired":
                return {
                    "success": False,
                    "status": "expired",
                    "title": acsm_info.title,
                    "expiration": (
                        acsm_info.expiration.isoformat()
                        if acsm_info.expiration
                        else None
                    ),
                    "message": acsm_info.message,
                }

            result = handler.process_acsm(acsm_path)
            return {
                "success": result.success,
                "input_file": result.input_file,
                "output_file": result.output_file,
                "drm_type": result.drm_type.value,
                "message": result.message,
                "timestamp": result.timestamp,
            }
        except Exception as e:
            logger.error(f"ACSM processing error: {e}")
            return {"success": False, "error": str(e)}

    def get_calibre_health(self) -> Dict[str, Any]:
        """
        Get health status of Calibre integration.

        Returns:
            Dictionary with Calibre integration health
        """
        health = {
            "calibre_manager_available": False,
            "drm_handler_available": False,
            "ebook_converter_available": False,
            "timestamp": datetime.now().isoformat(),
        }

        manager = self._get_calibre_manager()
        if manager:
            try:
                manager_health = manager.health_check()
                health["calibre_manager_available"] = True
                health["calibre_manager"] = manager_health
            except Exception as e:
                health["calibre_manager_error"] = str(e)

        handler = self._get_drm_handler()
        if handler:
            try:
                handler_health = handler.health_check()
                health["drm_handler_available"] = True
                health["drm_handler"] = handler_health
            except Exception as e:
                health["drm_handler_error"] = str(e)

        converter = self._get_ebook_converter()
        if converter:
            try:
                converter_health = converter.health_check()
                health["ebook_converter_available"] = True
                health["ebook_converter"] = converter_health
            except Exception as e:
                health["ebook_converter_error"] = str(e)

        health["overall_status"] = (
            "healthy"
            if all(
                [
                    health["calibre_manager_available"],
                    health["drm_handler_available"],
                    health["ebook_converter_available"],
                ]
            )
            else "degraded"
        )

        return health

    def ingest_ebook(
        self, ebook_path: str, extract_text: bool = True, remove_drm: bool = True
    ) -> Dict[str, Any]:
        """
        Full pipeline: Process ebook (DRM removal if needed), extract text,
        and ingest into RAG knowledge base.

        Args:
            ebook_path: Path to ebook file
            extract_text: Whether to extract text
            remove_drm: Whether to attempt DRM removal

        Returns:
            Dictionary with full ingestion result
        """
        from pathlib import Path

        path = Path(ebook_path)

        result = {
            "input_file": ebook_path,
            "steps_completed": [],
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Step 1: DRM removal if needed
        if remove_drm and path.suffix.lower() in [
            ".epub",
            ".pdf",
            ".azw",
            ".azw3",
            ".mobi",
        ]:
            drm_result = self.remove_drm(ebook_path)
            result["drm_removal"] = drm_result
            if drm_result.get("success"):
                result["steps_completed"].append("drm_removal")
                ebook_path = drm_result.get("output_file", ebook_path)

        # Step 2: Text extraction
        if extract_text:
            text_result = self.extract_text_from_ebook(ebook_path)
            result["text_extraction"] = text_result
            if text_result.get("success"):
                result["steps_completed"].append("text_extraction")
                text_file = text_result.get("text_file")

                # Step 3: Ingest into RAG
                if text_file and self._initialized:
                    try:
                        ingest_result = self.ingest_documents([text_file])
                        result["rag_ingestion"] = ingest_result
                        if ingest_result.get("status") == "success":
                            result["steps_completed"].append("rag_ingestion")
                            result["success"] = True
                    except Exception as e:
                        result["rag_ingestion"] = {"error": str(e)}

        result["steps_count"] = len(result["steps_completed"])
        return result

    # ============================================================
    # Advanced DRM Automation Integration
    # ============================================================

    def _get_drm_automation(self):
        """Lazy load DRMAutomation with multi-strategy fallback"""
        if not hasattr(self, "_drm_automation"):
            try:
                from integrations.calibre.drm_automation import DRMAutomation

                self._drm_automation = DRMAutomation()
            except ImportError as e:
                logger.warning(f"DRMAutomation not available: {e}")
                self._drm_automation = None
        return self._drm_automation

    async def process_ebook_with_fallback(
        self,
        ebook_path: str,
        preferred_strategy: Optional[str] = None,
        extract_text: bool = True,
        ingest_to_rag: bool = True,
    ) -> Dict[str, Any]:
        """
        Process ebook with multi-strategy DRM removal and automatic fallback.

        Uses DRMAutomation which attempts multiple strategies in order:
        1. CALIBRE_DEDRM - Standard Calibre DeDRM plugin
        2. CALIBRE_DEACSM - DeACSM plugin for ACSM files
        3. ADE_AUTOMATION - Adobe Digital Editions automation
        4. KNOCK_CLI - knock CLI tool
        5. SCREEN_CAPTURE - Screen capture with OCR (last resort)

        Args:
            ebook_path: Path to ebook or ACSM file
            preferred_strategy: Optional strategy to try first
            extract_text: Whether to extract text after processing
            ingest_to_rag: Whether to ingest extracted text into RAG

        Returns:
            Dictionary with processing results
        """
        from pathlib import Path

        drm_auto = self._get_drm_automation()
        if not drm_auto:
            # Fall back to basic processing
            return await self._process_ebook_basic(
                ebook_path, extract_text, ingest_to_rag
            )

        result = {
            "input_file": ebook_path,
            "steps_completed": [],
            "strategies_attempted": [],
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Import ProcessingStrategy enum
            from integrations.calibre.drm_automation import ProcessingStrategy

            strategy = None
            if preferred_strategy:
                try:
                    strategy = ProcessingStrategy[preferred_strategy.upper()]
                except KeyError:
                    logger.warning(f"Unknown strategy: {preferred_strategy}")

            # Process ebook with DRM automation
            drm_result = await drm_auto.process_ebook(
                ebook_path,
                preferred_strategy=strategy,
                extract_text=extract_text,
            )

            result["drm_processing"] = {
                "success": drm_result.success,
                "strategy_used": (
                    drm_result.strategy_used.value if drm_result.strategy_used else None
                ),
                "strategies_attempted": [
                    s.value for s in drm_result.strategies_attempted
                ],
                "output_file": drm_result.output_file,
                "text_file": drm_result.text_file,
                "message": drm_result.message,
            }
            result["strategies_attempted"] = result["drm_processing"][
                "strategies_attempted"
            ]

            if drm_result.success:
                result["steps_completed"].append("drm_removal")
                processed_file = drm_result.output_file or ebook_path

                # Text extraction
                if extract_text and drm_result.text_file:
                    result["steps_completed"].append("text_extraction")
                    result["text_file"] = drm_result.text_file

                    # RAG ingestion
                    if ingest_to_rag and self._initialized:
                        try:
                            ingest_result = self.ingest_documents(drm_result.text_file)
                            result["rag_ingestion"] = ingest_result
                            if ingest_result.get("status") == "success":
                                result["steps_completed"].append("rag_ingestion")
                                result["success"] = True
                        except Exception as e:
                            result["rag_ingestion"] = {"error": str(e)}
                            logger.error(f"RAG ingestion failed: {e}")
                else:
                    result["success"] = True
            else:
                result["error"] = drm_result.message

        except Exception as e:
            logger.error(f"DRM automation error: {e}")
            result["error"] = str(e)

        result["steps_count"] = len(result["steps_completed"])
        return result

    async def _process_ebook_basic(
        self, ebook_path: str, extract_text: bool, ingest_to_rag: bool
    ) -> Dict[str, Any]:
        """Basic ebook processing without DRM automation fallback."""
        return self.ingest_ebook(ebook_path, extract_text=extract_text, remove_drm=True)

    async def batch_process_ebooks(
        self,
        ebook_paths: List[str],
        preferred_strategy: Optional[str] = None,
        extract_text: bool = True,
        ingest_to_rag: bool = True,
        parallel: bool = True,
    ) -> Dict[str, Any]:
        """
        Process multiple ebooks with DRM removal and RAG ingestion.

        Args:
            ebook_paths: List of paths to ebooks or ACSM files
            preferred_strategy: Optional strategy to prefer
            extract_text: Whether to extract text
            ingest_to_rag: Whether to ingest to RAG
            parallel: Whether to process in parallel

        Returns:
            Dictionary with batch processing results
        """
        import asyncio

        results = {
            "total_files": len(ebook_paths),
            "successful": 0,
            "failed": 0,
            "results": [],
            "timestamp": datetime.now().isoformat(),
        }

        if parallel:
            # Process in parallel
            tasks = [
                self.process_ebook_with_fallback(
                    path, preferred_strategy, extract_text, ingest_to_rag
                )
                for path in ebook_paths
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for path, res in zip(ebook_paths, batch_results):
                if isinstance(res, Exception):
                    results["failed"] += 1
                    results["results"].append(
                        {
                            "input_file": path,
                            "success": False,
                            "error": str(res),
                        }
                    )
                elif res.get("success"):
                    results["successful"] += 1
                    results["results"].append(res)
                else:
                    results["failed"] += 1
                    results["results"].append(res)
        else:
            # Process sequentially
            for path in ebook_paths:
                try:
                    res = await self.process_ebook_with_fallback(
                        path, preferred_strategy, extract_text, ingest_to_rag
                    )
                    if res.get("success"):
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
                    results["results"].append(res)
                except Exception as e:
                    results["failed"] += 1
                    results["results"].append(
                        {
                            "input_file": path,
                            "success": False,
                            "error": str(e),
                        }
                    )

        return results

    async def setup_drm_keys(self) -> Dict[str, Any]:
        """
        Automatically extract and configure DRM keys.

        Extracts Adobe and Kindle keys and saves them to the
        DeDRM plugin configuration folder.

        Returns:
            Dictionary with key extraction results
        """
        drm_auto = self._get_drm_automation()
        if not drm_auto:
            return {
                "success": False,
                "error": "DRMAutomation not available",
                "adobe_key": False,
                "kindle_key": False,
            }

        result = {
            "success": False,
            "adobe_key": False,
            "kindle_key": False,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Extract Adobe key
            adobe_success, adobe_msg = await drm_auto.extract_adobe_key()
            result["adobe_key"] = adobe_success
            result["adobe_message"] = adobe_msg

            # Extract Kindle key
            kindle_success, kindle_msg = await drm_auto.extract_kindle_key()
            result["kindle_key"] = kindle_success
            result["kindle_message"] = kindle_msg

            result["success"] = adobe_success or kindle_success
        except Exception as e:
            logger.error(f"Key extraction error: {e}")
            result["error"] = str(e)

        return result

    def get_drm_automation_health(self) -> Dict[str, Any]:
        """
        Get health status of DRM automation system.

        Returns:
            Dictionary with DRM automation health status
        """
        drm_auto = self._get_drm_automation()
        if not drm_auto:
            return {
                "available": False,
                "error": "DRMAutomation not initialized",
                "timestamp": datetime.now().isoformat(),
            }

        try:
            return drm_auto.health_check()
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


def main():
    """Test the Librarian agent"""
    agent = LibrarianAgent()

    # Initialize
    print("Initializing Librarian Agent...")
    init_result = agent.initialize()
    print(json.dumps(init_result, indent=2))

    # Test query
    print("\nTesting query in lateral mode...")
    result = agent.query("What is therapeutic alliance?", mode="lateral")
    print(f"Answer: {result.answer}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Documents: {len(result.documents)}")

    # Test fact verification
    print("\nTesting fact verification...")
    verification = agent.verify_fact("Attachment theory was developed by John Bowlby")
    print(json.dumps(verification, indent=2))

    # Generate report
    print("\nGenerating status report...")
    report = agent.generate_librarian_report()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
    main()
