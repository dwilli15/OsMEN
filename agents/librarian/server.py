#!/usr/bin/env python3
"""
Librarian API Server
FastAPI server for the Librarian RAG Engine

Provides REST endpoints for:
- Semantic search queries (foundation, lateral, factcheck modes)
- Document ingestion
- Health monitoring
- Fact verification
- Lateral connection discovery
"""

import os
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from librarian_agent import LibrarianAgent, LibrarianConfig


# Initialize FastAPI app
app = FastAPI(
    title="OsMEN Librarian API",
    description="Semantic Memory & Lateral Thinking RAG Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Librarian agent
config = LibrarianConfig.from_env()
agent = LibrarianAgent(config=config)


# ============================================================================
# Request/Response Models
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for RAG queries"""
    query: str = Field(..., description="The search query")
    mode: str = Field("lateral", description="Retrieval mode: foundation, lateral, or factcheck")
    top_k: int = Field(5, description="Number of results to return")


class QueryResponse(BaseModel):
    """Response model for RAG queries"""
    answer: str
    mode: str
    confidence: float
    documents: List[dict]
    query: str
    timestamp: str


class IngestRequest(BaseModel):
    """Request model for document ingestion"""
    path: str = Field(..., description="Path to document(s) to ingest")
    recursive: bool = Field(True, description="Whether to search directories recursively")


class IngestResponse(BaseModel):
    """Response model for document ingestion"""
    status: str
    documents_indexed: int
    total_indexed: int
    path: str
    timestamp: str


class VerifyRequest(BaseModel):
    """Request model for fact verification"""
    statement: str = Field(..., description="The statement to verify")


class VerifyResponse(BaseModel):
    """Response model for fact verification"""
    statement: str
    status: str
    confidence: float
    supporting_documents: int
    sources: List[str]
    timestamp: str


class ConnectionsRequest(BaseModel):
    """Request model for finding connections"""
    topic: str = Field(..., description="The topic to explore")


class ConnectionsResponse(BaseModel):
    """Response model for lateral connections"""
    topic: str
    connections_found: int
    domains_touched: List[str]
    domain_breakdown: dict
    top_connection: Optional[str]
    timestamp: str


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    embedding_model: str
    embedding_model_loaded: bool
    chroma_connected: bool
    documents_indexed: int
    default_mode: str
    api_port: int
    timestamp: str


class ReportResponse(BaseModel):
    """Response model for full status report"""
    timestamp: str
    overall_status: str
    statistics: dict
    configuration: dict
    health: dict
    capabilities: List[str]


# ============================================================================
# API Endpoints
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup with error handling."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        result = agent.initialize()
        if result.get("status") == "initialized":
            logger.info("Librarian agent initialized successfully")
        else:
            logger.warning(f"Librarian agent initialization returned unexpected status: {result}")
    except Exception as e:
        logger.error(f"Failed to initialize Librarian agent: {e}")
        # Don't crash the server - allow health check to report the issue
        # The agent will report as not_initialized in health checks


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the health status of the Librarian service including:
    - Embedding model status
    - ChromaDB connection status
    - Number of indexed documents
    """
    return agent.get_health()


@app.get("/status", response_model=ReportResponse, tags=["Health"])
async def get_status():
    """
    Get full status report.
    
    Returns comprehensive status information including:
    - Overall operational status
    - Statistics
    - Configuration
    - Health metrics
    - Available capabilities
    """
    return agent.generate_librarian_report()


@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query(request: QueryRequest):
    """
    Query the knowledge base.
    
    Performs semantic search with the specified retrieval mode:
    - **foundation**: Core concept retrieval using Top-K Cosine Similarity
    - **lateral**: Cross-disciplinary connections using MMR diversity
    - **factcheck**: High-precision citation verification
    
    Args:
        request: QueryRequest containing query, mode, and top_k
        
    Returns:
        QueryResponse with answer, confidence, and supporting documents
    """
    try:
        result = agent.query(
            query=request.query,
            mode=request.mode,
            top_k=request.top_k
        )
        return {
            "answer": result.answer,
            "mode": result.mode,
            "confidence": result.confidence,
            "documents": [
                {
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "score": doc.score,
                    "chunk_id": doc.chunk_id
                }
                for doc in result.documents
            ],
            "query": result.query,
            "timestamp": result.timestamp
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/ingest", response_model=IngestResponse, tags=["RAG"])
async def ingest_documents(request: IngestRequest):
    """
    Ingest documents into the knowledge base.
    
    Processes markdown and text files, generating embeddings and
    storing them in the vector database.
    
    Args:
        request: IngestRequest containing path and recursive flag
        
    Returns:
        IngestResponse with ingestion status and counts
    """
    try:
        result = agent.ingest_documents(
            path=request.path,
            recursive=request.recursive
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result.get("error", "Ingestion failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/verify", response_model=VerifyResponse, tags=["Analysis"])
async def verify_fact(request: VerifyRequest):
    """
    Verify a factual statement.
    
    Uses high-precision retrieval (factcheck mode) to verify the
    truthfulness of a statement against the knowledge base.
    
    Args:
        request: VerifyRequest containing the statement to verify
        
    Returns:
        VerifyResponse with verification status, confidence, and sources
    """
    try:
        result = agent.verify_fact(request.statement)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.post("/connections", response_model=ConnectionsResponse, tags=["Analysis"])
async def find_connections(request: ConnectionsRequest):
    """
    Find cross-disciplinary connections.
    
    Uses lateral thinking mode to discover unexpected connections
    between the given topic and other domains in the knowledge base.
    
    Args:
        request: ConnectionsRequest containing the topic to explore
        
    Returns:
        ConnectionsResponse with connection count, domains, and top connection
    """
    try:
        result = agent.find_connections(request.topic)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection search failed: {str(e)}")


@app.get("/modes", tags=["Info"])
async def list_modes():
    """
    List available retrieval modes.
    
    Returns information about the three retrieval modes:
    - foundation: Top-K Cosine Similarity for core concepts
    - lateral: MMR diversity for cross-disciplinary connections
    - factcheck: High-precision for citation verification
    """
    return {
        "modes": [
            {
                "name": "foundation",
                "algorithm": "Top-K Cosine Similarity",
                "purpose": "Populate new sections with core concepts",
                "best_for": "Learning fundamentals, getting started"
            },
            {
                "name": "lateral",
                "algorithm": "MMR (λ=0.5) diversity",
                "purpose": "Cross-disciplinary creative connections",
                "best_for": "Innovation, unexpected insights"
            },
            {
                "name": "factcheck",
                "algorithm": "Top-3 precision search",
                "purpose": "High-precision citation verification",
                "best_for": "Verification, accuracy-critical queries"
            }
        ],
        "default": config.default_mode
    }


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "OsMEN Librarian",
        "description": "Semantic Memory & Lateral Thinking RAG Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "/status"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=config.api_port,
        reload=True
    )
