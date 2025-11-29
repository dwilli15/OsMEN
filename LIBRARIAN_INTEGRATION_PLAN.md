# OsMEN + Librarian Integration Plan

**Target Timeline**: 6 Hours to Production Ready  
**Strategy**: 5 Parallel Agent Development Paths  
**Version**: 1.0.0  
**Created**: 2025-11-29

---

## Executive Summary

This document outlines the strategy to merge [osmen-librarian](https://github.com/dwilli15/osmen-librarian) into OsMEN as a core knowledge management node. The librarian provides:

- **Semantic Memory & Lateral Thinking Engine**
- **LangGraph-based RAG System**
- **Three Retrieval Modes**: Foundation, Lateral, Factcheck
- **DeepAgents Middleware Architecture**
- **OpenAI Assistants API Compatibility**

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
│                    │   Librarian    │ ◄── NEW INTEGRATION       │
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

## 5 Agent Development Paths

### Agent 1: Core RAG Integration Agent
**Focus**: Integrate librarian RAG engine into OsMEN

**Tasks**:
- [ ] Create `agents/librarian/` directory structure
- [ ] Implement `LibrarianAgent` wrapper class
- [ ] Expose librarian API endpoints through agent gateway
- [ ] Create Langflow flow for librarian integration
- [ ] Add ChromaDB persistence to docker-compose

**Files to Create**:
```
agents/librarian/
├── __init__.py
├── librarian_agent.py      # Main agent wrapper
├── rag_integration.py      # RAG engine interface
└── config.py               # Configuration settings
```

### Agent 2: Knowledge Management Enhancement Agent
**Focus**: Enhance OsMEN's knowledge_management with librarian capabilities

**Tasks**:
- [ ] Extend `KnowledgeAgent` to use librarian retrieval
- [ ] Add lateral thinking mode to knowledge search
- [ ] Implement factcheck capability for note verification
- [ ] Create subagent integration (FactChecker, LateralResearcher)
- [ ] Bridge Obsidian integration with ChromaDB indexing

**Integration Points**:
```python
# Enhanced KnowledgeAgent with Librarian
class EnhancedKnowledgeAgent:
    def search_knowledge(self, query: str, mode: str = "lateral") -> List[Dict]:
        # Uses librarian's three-mode retrieval
        pass
    
    def verify_fact(self, statement: str) -> Dict:
        # Uses FactChecker subagent
        pass
    
    def find_connections(self, topic: str) -> Dict:
        # Uses LateralResearcher for cross-disciplinary insights
        pass
```

### Agent 3: Workflow Automation Agent
**Focus**: Create n8n workflows and triggers for librarian

**Tasks**:
- [ ] Create `n8n/workflows/librarian_trigger.json`
- [ ] Set up document ingestion workflow
- [ ] Create knowledge query webhook
- [ ] Add scheduled re-indexing workflow
- [ ] Integrate with daily brief agent

**Workflows to Create**:
```
n8n/workflows/
├── librarian_ingest_trigger.json     # Document ingestion
├── librarian_query_webhook.json      # Query API
├── librarian_reindex_schedule.json   # Scheduled maintenance
└── knowledge_daily_summary.json      # Daily knowledge report
```

### Agent 4: Production Hardening Agent
**Focus**: Ensure production readiness

**Tasks**:
- [ ] Add librarian service to docker-compose.yml
- [ ] Create health check endpoints
- [ ] Implement rate limiting for API
- [ ] Add authentication layer
- [ ] Set up monitoring and logging
- [ ] Create production configuration

**Docker Service**:
```yaml
librarian:
  build:
    context: ./agents/librarian
    dockerfile: Dockerfile
  container_name: osmen-librarian
  ports:
    - "127.0.0.1:8200:8200"
  environment:
    - LIBRARIAN_DATA_DIR=/app/data
    - LIBRARIAN_DB_PATH=/app/data/db
    - EMBEDDING_MODEL=dunzhang/stella_en_1.5B_v5
  volumes:
    - librarian-data:/app/data
  depends_on:
    - postgres
  networks:
    - osmen-network
```

### Agent 5: Automated Integration & Testing Agent
**Focus**: CI/CD and automated testing

**Tasks**:
- [ ] Create test suite for librarian integration
- [ ] Add librarian tests to `test_agents.py`
- [ ] Create GitHub Actions workflow for testing
- [ ] Set up integration tests
- [ ] Create validation scripts
- [ ] Document API contracts

**Test Structure**:
```
tests/
├── test_librarian_agent.py       # Unit tests
├── test_librarian_integration.py # Integration tests
└── test_rag_modes.py             # RAG mode validation
```

---

## Implementation Timeline (6 Hours)

### Hour 1-2: Core Infrastructure
- Agent 1: Create librarian agent directory structure
- Agent 4: Add librarian service to docker-compose.yml
- Agent 5: Set up test infrastructure

### Hour 2-3: RAG Integration
- Agent 1: Implement LibrarianAgent wrapper
- Agent 2: Extend KnowledgeAgent with librarian

### Hour 3-4: Workflow Automation
- Agent 3: Create n8n workflows
- Agent 2: Integrate with existing agents

### Hour 4-5: Production Hardening
- Agent 4: Health checks, monitoring, configuration
- Agent 5: Complete test suite

### Hour 5-6: Final Integration & Testing
- All agents: Integration testing
- Documentation updates
- Final validation

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

## Success Criteria

### Production Ready Checklist
- [ ] All 16 existing tests pass
- [ ] 5 new librarian tests pass
- [ ] Docker services start successfully
- [ ] API endpoints respond correctly
- [ ] Knowledge queries return relevant results
- [ ] Integration with existing agents works
- [ ] Documentation is complete
- [ ] Health checks all green

### Performance Targets
- Query latency < 500ms (foundation mode)
- Query latency < 1000ms (lateral mode)
- Ingestion rate > 10 docs/second
- Memory usage < 4GB (without GPU)

---

## Related Documents

- [OsMEN README](README.md)
- [Librarian Implementation Status](https://github.com/dwilli15/osmen-librarian/blob/main/implementation_status.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [Feature Status](FEATURE_STATUS.md)

---

*This plan enables parallel development by 5 agents to achieve 100% production readiness within 6 hours.*
