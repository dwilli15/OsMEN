# Librarian Vector Database Analysis

## Current OsMEN Setup

We currently use **ChromaDB** as the unified vector database (port 8000):
- Replaces Qdrant
- All vector storage: Librarian RAG, agent memory, Obsidian sync
- Persistent storage in Docker volume

### Current Librarian Config
- **Embedding Model**: Stella 1.5B (`dunzhang/stella_en_1.5B_v5`)
- **Backend**: ChromaDB via `chromadb/chroma:latest`
- **Modes**: Foundation, Lateral (MMR), Factcheck
- **Integration**: LangGraph orchestration

---

## DocumentDB Analysis

**Source**: [The New Stack - What DocumentDB Means for Open Source](https://thenewstack.io/what-documentdb-means-for-open-source/)

### What is DocumentDB?
- Open-source MongoDB-compatible document store
- Released by Microsoft under **MIT License** (August 2024)
- Based on Azure Cosmos DB for MongoDB core
- PostgreSQL extension + MongoDB API gateway

### Key Features
| Feature | Description |
|---------|-------------|
| Schema-free | No rigid schema - add fields on the fly |
| PostgreSQL integration | PG extension translates MongoDB API |
| Multi-agent support | Session history, collaboration, rollbacks |
| Semantic caching | Preserves meaning for chatbots/RAG |
| MIT License | Completely free, no vendor lock-in |

### Multi-Agent Use Cases
1. **Session History**: Store agent actions and interactions
2. **Agent Collaboration**: Multiple agents work on same document
3. **Consensus & Rollback**: Commit when agents agree
4. **Chatbot Memory**: Conversational history retention
5. **Semantic Cache**: Fast retrieval with meaning preservation

### Limitations for OsMEN
⚠️ **DocumentDB is NOT a vector database** - it's a document store.
- No native vector similarity search
- No embedding storage/indexing (HNSW, SPANN)
- Would need to be **combined** with a vector DB

---

## ChromaDB Analysis

### Why ChromaDB is Better for Librarian

| Capability | ChromaDB | DocumentDB |
|------------|----------|------------|
| Vector Search | ✅ Native HNSW/SPANN | ❌ Not supported |
| Embedding Storage | ✅ First-class | ❌ Manual JSON |
| RAG Optimized | ✅ Built for it | ⚠️ Semantic cache only |
| Full-text Search | ✅ Hybrid search | ✅ MongoDB text |
| Metadata Filtering | ✅ Native | ✅ Native |
| Multi-tenancy | ✅ Tenants/Databases | ✅ Collections |
| Local Development | ✅ In-memory mode | ⚠️ Needs Postgres |
| LangChain/LlamaIndex | ✅ Native integrations | ⚠️ Custom code |

### ChromaDB Advantages
1. **Purpose-built for AI/RAG**: Embedding-first design
2. **Automatic embedding**: Tokenization, indexing handled
3. **Hybrid search**: Dense + sparse + full-text
4. **Scalable**: Local → single-node → distributed
5. **Agent memory**: Mem0 integration, stateful agents

---

## Recommendation

### Keep ChromaDB for Librarian ✅

ChromaDB is the right choice because:
1. **Native vector search** - critical for RAG
2. **HNSW indexing** - fast similarity search
3. **Already integrated** - works in our Docker stack
4. **LangGraph compatible** - our orchestration layer

### Consider DocumentDB for Agent State 🤔

DocumentDB could **complement** ChromaDB for:
- Agent session/conversation history (JSON documents)
- Multi-agent collaboration state
- Configuration and workflow persistence
- Schema-free agent tool outputs

### Hybrid Architecture Option

```
┌─────────────────────────────────────────────────────────┐
│                     OsMEN Agents                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────────┐          │
│  │   ChromaDB   │         │   DocumentDB     │          │
│  │  (Vectors)   │         │   (Documents)    │          │
│  ├──────────────┤         ├──────────────────┤          │
│  │ - Embeddings │         │ - Session state  │          │
│  │ - RAG search │         │ - Agent history  │          │
│  │ - Similarity │         │ - Collaboration  │          │
│  │ - Librarian  │         │ - Config/Schema  │          │
│  └──────────────┘         └──────────────────┘          │
│         ↑                          ↑                     │
│         └──────────┬───────────────┘                     │
│                    │                                     │
│           ┌────────┴────────┐                            │
│           │   PostgreSQL    │                            │
│           │  (Metadata/SQL) │                            │
│           └─────────────────┘                            │
└─────────────────────────────────────────────────────────┘
```

---

## Action Items for Librarian Improvement

### Phase 1: Optimize Current ChromaDB Setup
- [ ] Upgrade to ChromaDB 0.5+ with SPANN indexing
- [ ] Tune HNSW parameters for better recall
- [ ] Add hybrid search (dense + sparse)
- [ ] Implement collection partitioning

### Phase 2: Improve Embeddings
- [ ] Test Stella 1.5B vs alternatives (BGE, E5)
- [ ] Enable GPU acceleration (CUDA)
- [ ] Add embedding caching layer
- [ ] Implement chunking strategies

### Phase 3: RAG Pipeline Enhancements
- [ ] Add re-ranking with cross-encoders
- [ ] Implement query expansion
- [ ] Add contextual compression
- [ ] Multi-modal support (images, PDFs)

### Phase 4: Optional DocumentDB Layer
- [ ] Evaluate for agent state management
- [ ] Test with multi-agent workflows
- [ ] Consider for semantic caching
- [ ] Assess PostgreSQL extension approach

---

## Summary

| Question | Answer |
|----------|--------|
| Switch to DocumentDB? | **No** - not a vector DB |
| Keep ChromaDB? | **Yes** - purpose-built for RAG |
| Use DocumentDB at all? | **Maybe** - for agent state |
| Best path forward? | Optimize ChromaDB + improve RAG |

**Bottom Line**: ChromaDB is the right choice for Librarian's vector search needs. DocumentDB is interesting for agent collaboration but addresses a different problem. Focus on optimizing ChromaDB configuration and RAG pipeline quality.
