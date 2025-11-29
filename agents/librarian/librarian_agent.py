#!/usr/bin/env python3
"""
Librarian Agent for OsMEN
Semantic Memory & Lateral Thinking RAG Engine

This agent provides:
- Three-mode RAG retrieval (foundation, lateral, factcheck)
- LangGraph-based orchestration
- Subagent delegation (FactChecker, LateralResearcher)
- OpenAI Assistants API compatibility
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LibrarianConfig:
    """Configuration for the Librarian Agent"""
    data_dir: Path = field(default_factory=lambda: Path("./data/librarian"))
    db_path: Path = field(default_factory=lambda: Path("./data/librarian/db"))
    embedding_model: str = "dunzhang/stella_en_1.5B_v5"
    default_mode: str = "lateral"
    top_k: int = 5
    mmr_lambda: float = 0.5
    api_port: int = 8200
    
    @classmethod
    def from_env(cls) -> "LibrarianConfig":
        """Create config from environment variables"""
        return cls(
            data_dir=Path(os.getenv("LIBRARIAN_DATA_DIR", "./data/librarian")),
            db_path=Path(os.getenv("LIBRARIAN_DB_PATH", "./data/librarian/db")),
            embedding_model=os.getenv("LIBRARIAN_EMBEDDING_MODEL", "dunzhang/stella_en_1.5B_v5"),
            default_mode=os.getenv("RAG_DEFAULT_MODE", "lateral"),
            top_k=int(os.getenv("RAG_TOP_K", "5")),
            mmr_lambda=float(os.getenv("RAG_MMR_LAMBDA", "0.5")),
            api_port=int(os.getenv("LIBRARIAN_API_PORT", "8200")),
        )


@dataclass
class DocumentChunk:
    """Represents a chunk of a document"""
    content: str
    metadata: Dict[str, Any]
    score: float = 0.0
    chunk_id: str = ""


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
    
    Attributes:
        config: LibrarianConfig for agent settings
        initialized: Whether the agent is fully initialized
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
        
        # Ensure data directories exist
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        self.config.db_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"LibrarianAgent initialized with config: {self.config}")
    
    @property
    def initialized(self) -> bool:
        """Check if the agent is fully initialized"""
        return self._initialized
    
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize the RAG engine and embedding model.
        
        This method performs lazy initialization of heavyweight components
        like the embedding model and vector store.
        
        Returns:
            Dictionary with initialization status
        """
        try:
            # For now, we simulate initialization
            # In production, this would load the embedding model and connect to ChromaDB
            self._initialized = True
            logger.info("Librarian RAG engine initialized successfully")
            return {
                "status": "initialized",
                "embedding_model": self.config.embedding_model,
                "db_path": str(self.config.db_path),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to initialize Librarian: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def query(
        self,
        query: str,
        mode: Optional[str] = None,
        top_k: Optional[int] = None
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
            raise ValueError(f"Invalid mode: {mode}. Must be one of: foundation, lateral, factcheck")
        
        logger.info(f"Processing query in {mode} mode: {query[:50]}...")
        
        # TODO: Replace placeholder with actual ChromaDB retrieval from osmen-librarian
        # See: https://github.com/dwilli15/osmen-librarian/blob/main/src/retrieval/chroma.py
        documents = self._retrieve_documents(query, mode, top_k)
        answer = self._generate_answer(query, documents, mode)
        confidence = self._calculate_confidence(documents, mode)
        
        result = QueryResult(
            answer=answer,
            documents=documents,
            mode=mode,
            confidence=confidence,
            query=query
        )
        
        logger.info(f"Query completed with {len(documents)} documents, confidence: {confidence:.2f}")
        return result
    
    def _retrieve_documents(
        self,
        query: str,
        mode: str,
        top_k: int
    ) -> List[DocumentChunk]:
        """
        Retrieve documents based on the query and mode.
        
        Args:
            query: Search query
            mode: Retrieval mode
            top_k: Number of results
            
        Returns:
            List of DocumentChunk objects
        """
        # TODO: Replace with actual ChromaDB retrieval from osmen-librarian
        # The actual implementation will use different algorithms per mode:
        # - foundation: Top-K Cosine Similarity
        # - lateral: MMR (Maximal Marginal Relevance) with λ=0.5
        # - factcheck: High-precision Top-3
        # See: https://github.com/dwilli15/osmen-librarian/blob/main/src/retrieval/chroma.py
        
        return [
            DocumentChunk(
                content=f"Sample document content for query: {query}",
                metadata={
                    "source": "sample.md",
                    "mode": mode,
                    "retrieved_at": datetime.now().isoformat()
                },
                score=0.85,
                chunk_id="sample-001"
            )
        ]
    
    def _generate_answer(
        self,
        query: str,
        documents: List[DocumentChunk],
        mode: str
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
    
    def _calculate_confidence(
        self,
        documents: List[DocumentChunk],
        mode: str
    ) -> float:
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
            "factcheck": 1.1  # Factcheck should have higher confidence threshold
        }
        
        return min(avg_score * mode_multipliers.get(mode, 1.0), 1.0)
    
    def ingest_documents(
        self,
        path: str,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest documents from the specified path.
        
        Args:
            path: Path to document(s) to ingest
            recursive: Whether to search directories recursively
            
        Returns:
            Dictionary with ingestion status
        """
        path = Path(path)
        
        if not path.exists():
            return {
                "status": "error",
                "error": f"Path does not exist: {path}",
                "documents_indexed": 0
            }
        
        logger.info(f"Ingesting documents from: {path}")
        
        # Placeholder - will be replaced with actual document ingestion
        # The actual implementation will:
        # 1. Find all markdown/text files
        # 2. Chunk documents
        # 3. Generate embeddings
        # 4. Store in ChromaDB
        
        files_found = 0
        if path.is_file():
            files_found = 1
        else:
            pattern = "**/*.md" if recursive else "*.md"
            files_found = len(list(path.glob(pattern)))
        
        self._documents_indexed += files_found
        
        return {
            "status": "success",
            "documents_indexed": files_found,
            "total_indexed": self._documents_indexed,
            "path": str(path),
            "recursive": recursive,
            "timestamp": datetime.now().isoformat()
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
            "sources": [doc.metadata.get("source", "unknown") for doc in result.documents],
            "timestamp": datetime.now().isoformat()
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
            domains[domain].append({
                "content": doc.content[:200],
                "score": doc.score
            })
        
        return {
            "topic": topic,
            "connections_found": len(result.documents),
            "domains_touched": list(domains.keys()),
            "domain_breakdown": {k: len(v) for k, v in domains.items()},
            "top_connection": result.answer if result.documents else None,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_health(self) -> Dict[str, Any]:
        """
        Get health status of the Librarian agent.
        
        Returns:
            Dictionary with health status
        """
        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "embedding_model": self.config.embedding_model,
            "embedding_model_loaded": self._initialized,
            "chroma_connected": self._initialized,
            "documents_indexed": self._documents_indexed,
            "default_mode": self.config.default_mode,
            "api_port": self.config.api_port,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_librarian_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive status report.
        
        Returns:
            Dictionary with full status report
        """
        health = self.get_health()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "operational" if self._initialized else "pending_initialization",
            "statistics": {
                "documents_indexed": self._documents_indexed,
                "embedding_model": self.config.embedding_model,
                "retrieval_modes": ["foundation", "lateral", "factcheck"],
                "default_mode": self.config.default_mode,
            },
            "configuration": {
                "data_dir": str(self.config.data_dir),
                "db_path": str(self.config.db_path),
                "top_k": self.config.top_k,
                "mmr_lambda": self.config.mmr_lambda,
                "api_port": self.config.api_port
            },
            "health": health,
            "capabilities": [
                "semantic_search",
                "lateral_thinking",
                "fact_verification",
                "document_ingestion",
                "cross_domain_connections"
            ]
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
