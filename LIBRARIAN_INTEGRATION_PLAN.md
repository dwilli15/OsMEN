# OsMEN + Librarian Integration Plan

**Target Timeline**: 6 Hours to Production Ready  
**Strategy**: Unified Single-Agent Implementation  
**Version**: 3.0.0 (Real RAG Implementation)  
**Created**: 2025-11-29  
**Status**: ✅ COMPLETE - Full Source Code Ported

---

## Executive Summary

This document outlines the completed integration of [osmen-librarian](https://github.com/dwilli15/osmen-librarian) into OsMEN as a core knowledge management node. The actual source code from osmen-librarian has been ported, including:

- **Semantic Memory & Lateral Thinking Engine** (Context7 dimensions)
- **ChromaDB Vector Store** with Stella 1.5B embeddings
- **Three Retrieval Modes**: Foundation, Lateral, Factcheck
- **Real Document Ingestion** with chunking and embedding generation
- **Graceful Fallback** to mock mode when dependencies unavailable

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         OsMEN Ecosystem                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  Langflow   │    │     n8n     │    │   Agent Gateway     │ │
│  │ (Reasoning) │    │ (Automation)│    │   (API Gateway)     │ │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘ │
│         │                  │                       │            │
│         └──────────────────┼───────────────────────┘            │
│                            │                                    │
│                    ┌───────▼───────┐                           │
│                    │   Librarian    │ ◄── REAL RAG ENGINE       │
│                    │   RAG Node     │                           │
│                    │  (Port 8200)   │                           │
│                    └───────┬───────┘                           │
│                            │                                    │
│  ┌─────────────────────────┼─────────────────────────────────┐ │
│  │                   Storage Layer                            │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────────┐ │ │
│  │  │ Qdrant  │  │ Postgres│  │  Redis  │  │  ChromaDB    │ │ │
│  │  │ (OsMEN) │  │ (Shared)│  │ (Cache) │  │ (Librarian)  │ │ │
│  │  └─────────┘  └─────────┘  └─────────┘  └──────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Checklist (COMPLETED)

### Core RAG Integration ✅
- [x] Create `agents/librarian/` directory structure
- [x] Implement `LibrarianAgent` wrapper class with real ChromaDB integration
- [x] Port ChromaRetriever from osmen-librarian src/retrieval/chroma.py
- [x] Port retrieval interfaces from osmen-librarian src/retrieval/interfaces.py
- [x] Port LateralEngine with Context7 dimensions
- [x] Expose librarian API endpoints through FastAPI server
- [x] Add ChromaDB persistence to docker-compose

**Files Created**:
```
agents/librarian/
├── __init__.py
├── librarian_agent.py      # Main agent wrapper with real ChromaDB retrieval
├── server.py               # FastAPI server
├── Dockerfile              # Container definition
├── requirements.txt        # Dependencies (chromadb, langchain-huggingface, etc.)
└── src/                    # Ported source from osmen-librarian
    ├── __init__.py
    ├── lateral_thinking.py # Context7 dimensions, LateralEngine
    └── retrieval/
        ├── __init__.py
        ├── interfaces.py   # RetrieverBase, DocumentChunk, RetrievalResult
        └── chroma.py       # ChromaRetriever with Stella embeddings
```

### Knowledge Management Enhancement ✅
- [x] LibrarianAgent supports lateral thinking mode with Context7
- [x] Real ChromaDB retrieval with Stella 1.5B embeddings
- [x] Fact verification capability via `verify_fact()` method
- [x] Cross-disciplinary connections via `find_connections()` method
- [x] Graceful fallback to mock mode when dependencies unavailable

**LibrarianAgent Capabilities**:
```python
class LibrarianAgent:
    def initialize(self) -> Dict:
        # Initializes ChromaDB, loads Stella embeddings (or fallback)
        pass
    
    def query(self, query: str, mode: str = "lateral") -> QueryResult:
        # Three-mode retrieval with real ChromaDB:
        # - foundation: Top-K Cosine Similarity
        # - lateral: MMR diversity with Context7 enrichment
        # - factcheck: High-precision citation verification
        pass
    
    def ingest_documents(self, path: str) -> Dict:
        # Real document ingestion with chunking and embedding
        pass
    
    def verify_fact(self, statement: str) -> Dict:
        # High-precision fact verification
        pass
    
    def find_connections(self, topic: str) -> Dict:
        # Cross-disciplinary lateral thinking
        pass
```

### Workflow Automation ✅
- [x] Create `n8n/workflows/librarian_query_webhook.json`
- [x] Create `n8n/workflows/librarian_ingest_trigger.json`

### Production Hardening ✅
- [x] Add librarian service to docker-compose.yml (optional profile)
- [x] Create health check endpoints
- [x] Configure logging and error handling
- [x] Set up environment configuration

### Testing ✅
- [x] Add librarian tests to `test_agents.py`
- [x] All 17/17 tests passing
- [x] CodeQL security scan: 0 alerts

---

## API Contracts

### Librarian Query API
```
POST /api/librarian/query
{
    "query": "string",
    "mode": "foundation" | "lateral" | "factcheck",
    "top_k": 5
}

Response:
{
    "answer": "string",
    "documents": [...],
    "mode": "string",
    "confidence": 0.0-1.0
}
```

### Document Ingestion API
```
POST /api/librarian/ingest
{
    "path": "string",
    "recursive": true
}

Response:
{
    "status": "success",
    "documents_indexed": 42,
    "errors": []
}
```

### Health Check API
```
GET /api/librarian/health

Response:
{
    "status": "healthy",
    "chroma_connected": true,
    "embedding_model_loaded": true,
    "documents_indexed": 1000
}
```

---

## Configuration

### Environment Variables
```bash
# Librarian Configuration
LIBRARIAN_DATA_DIR=./data/librarian
LIBRARIAN_DB_PATH=./data/librarian/db
LIBRARIAN_EMBEDDING_MODEL=dunzhang/stella_en_1.5B_v5
LIBRARIAN_API_PORT=8200

# RAG Settings
RAG_DEFAULT_MODE=lateral
RAG_TOP_K=5
RAG_MMR_LAMBDA=0.5

# Integration Settings
OSMEN_KNOWLEDGE_USE_LIBRARIAN=true
LIBRARIAN_URL=http://librarian:8200
```

---

## Consistency Guidelines

### Direction of Adaptation
Based on analysis, **librarian patterns should flow into OsMEN**:

1. **LangGraph Patterns**: Adopt librarian's StateGraph orchestration
2. **Middleware Architecture**: Apply DeepAgents middleware to other agents
3. **Three-Mode Retrieval**: Standardize across knowledge operations
4. **Assistants API**: Use as template for other agent APIs

### Code Style Alignment
- Both use Python 3.10+
- Both use FastAPI for APIs
- Both follow similar docstring conventions
- Align on logging patterns (use loguru)

### Shared Dependencies
```
# Core (already in OsMEN)
fastapi>=0.115.0
uvicorn>=0.32.0

# New from Librarian
langgraph>=0.2.0
langchain>=0.3.0
chromadb>=0.5.0
sentence-transformers>=2.0.0
```

---

## Success Criteria ✅

### Production Ready Checklist
- [x] All 17 tests pass (16 existing + 1 new librarian)
- [x] Docker services configuration complete
- [x] API endpoints defined and working
- [x] Integration with existing agents tested
- [x] Documentation complete
- [x] Health checks implemented

### Performance Targets
- Query latency < 500ms (foundation mode)
- Query latency < 1000ms (lateral mode)
- Ingestion rate > 10 docs/second
- Memory usage < 4GB (without GPU)

---

## Usage

### Start with Librarian
```bash
docker-compose --profile librarian up -d
```

### Query the Knowledge Base
```bash
curl -X POST http://localhost:8200/query \
  -H "Content-Type: application/json" \
  -d '{"query": "therapeutic alliance", "mode": "lateral"}'
```

### Ingest Documents
```bash
curl -X POST http://localhost:8200/ingest \
  -H "Content-Type: application/json" \
  -d '{"path": "/app/data/sources", "recursive": true}'
```

---

## Related Documents

- [OsMEN README](README.md)
- [Librarian Implementation Status](https://github.com/dwilli15/osmen-librarian/blob/main/implementation_status.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [Feature Status](FEATURE_STATUS.md)

---

*Integration completed with unified single-agent implementation approach.*
