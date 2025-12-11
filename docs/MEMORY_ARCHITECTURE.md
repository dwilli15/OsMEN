# OsMEN Memory Architecture

> **Unified Memory System for AI Agent Orchestration**

## Overview

OsMEN uses a consolidated memory architecture with **ChromaDB** as the single vector database, **Redis** for short-term caching, and **PostgreSQL** for structured data.

```
┌────────────────────────────────────────────────────────────────┐
│                    VS Code + GitHub Copilot                    │
├────────────────────────────────────────────────────────────────┤
│  context7     │  chroma-mcp   │  osmen-mcp   │  memory-mcp    │
│  (lib docs)   │  (your data)  │  (orchestra) │  (knowledge)   │
└───────┬───────┴───────┬───────┴───────┬──────┴───────┬────────┘
        │               │               │              │
        │  ┌────────────▼───────────────▼──────────────┘
        │  │
        │  ▼
┌───────┴──────────────────────────────────────────────┐
│                    ChromaDB (Port 8000)              │
│  ┌─────────────────┬──────────────────┬────────────┐ │
│  │ obsidian_vault  │ librarian_docs   │ agent_mem  │ │
│  │ (synced notes)  │ (research RAG)   │ (context)  │ │
│  └─────────────────┴──────────────────┴────────────┘ │
└──────────────────────────────────────────────────────┘
        ▲                                    ▲
        │                                    │
┌───────┴────────┐               ┌───────────┴──────────┐
│    Obsidian    │               │       Agents         │
│    (vault/)    │               │  (context, memory)   │
└────────────────┘               └──────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    Redis (Port 6379)                           │
│                    Short-term Cache (60s TTL)                  │
│                    API responses, rate limiting                │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    PostgreSQL (Port 5432)                      │
│                    n8n workflows, Langflow state               │
└────────────────────────────────────────────────────────────────┘
```

## Memory Components

### 1. ChromaDB - Vector Storage (Long-term Memory)

**Purpose**: Semantic search, document retrieval, conversation history

**URL**: `http://localhost:8000`

**Collections**:

| Collection | Purpose | Source | Chunking |
|------------|---------|--------|----------|
| `obsidian_vault` | Synced notes from Obsidian | `obsidian_sync.py` | 1000 chars, 200 overlap |
| `librarian_docs` | Research documents | Librarian agent | Semantic splitting |
| `agent_memory` | Conversation context | All agents | Per-turn storage |
| `session_context` | Working memory | Active sessions | Dynamic |

**When to Use**:
- ✅ Semantic search ("find notes about X")
- ✅ Long-term memory retrieval
- ✅ RAG for document Q&A
- ✅ Cross-session context
- ❌ NOT for transient data (use Redis)

### 2. Redis - Short-term Cache

**Purpose**: API response caching, rate limiting, session state

**URL**: `redis://localhost:6379`

**TTL Settings**:
```python
# From cache/redis_cache.py
DEFAULT_TTL = 60  # 60 seconds
```

**When to Use**:
- ✅ Cache expensive API calls
- ✅ Rate limit tracking
- ✅ Session tokens
- ✅ Deduplication within a session
- ❌ NOT for persistent storage

### 3. PostgreSQL - Structured Data

**Purpose**: n8n workflow state, Langflow persistence

**URL**: `postgresql://localhost:5432/osmen`

**When to Use**:
- ✅ n8n credential storage
- ✅ Workflow execution history
- ✅ Langflow flow definitions
- ✅ Structured relational data
- ❌ NOT for vector/semantic search

### 4. Context7 - External Library Docs

**Purpose**: Up-to-date documentation for libraries/frameworks

**Source**: `context7.com` API

**When to Use**:
- ✅ Looking up latest library APIs
- ✅ Framework documentation
- ✅ Code examples from official docs
- ❌ NOT for your own documents
- ❌ REQUIRES internet connection

**API Key** (optional but recommended):
```env
# In .env
CONTEXT7_API_KEY=your_api_key_here
```

## Agent Memory Guidelines

### When Agents Should Use ChromaDB

```python
# Search for relevant context before responding
from chromadb import HttpClient

client = HttpClient(host="localhost", port=8000)
collection = client.get_collection("agent_memory")

# Query for relevant memories
results = collection.query(
    query_texts=["user's question or context"],
    n_results=5,
    where={"agent": "daily_brief"}  # Filter by agent type
)

# Include relevant context in prompt
context = "\n".join([doc for doc in results['documents'][0]])
```

### When Agents Should Store Memories

```python
# After completing a significant task or conversation
collection.add(
    documents=["Summary of what happened"],
    metadatas=[{
        "agent": "daily_brief",
        "timestamp": datetime.now().isoformat(),
        "type": "task_completion",
        "tags": ["research", "summary"]
    }],
    ids=[str(uuid.uuid4())]
)
```

### Memory Decision Matrix

| Scenario | Store Where | Retrieve From |
|----------|-------------|---------------|
| User asks a question | - | ChromaDB (context) |
| Agent completes task | ChromaDB | - |
| API response arrives | Redis (cache) | - |
| Same API call within 60s | - | Redis |
| User references old topic | - | ChromaDB |
| Looking up library docs | - | Context7 |
| Syncing Obsidian notes | ChromaDB | Obsidian vault |

## Obsidian Integration

### Automatic Sync

```bash
# First-time full sync
python agents/knowledge_management/obsidian_sync.py --vault D:\OsMEN\obsidian-vault --force

# Incremental sync (only changed files)
python agents/knowledge_management/obsidian_sync.py --vault D:\OsMEN\obsidian-vault

# Search synced notes
python agents/knowledge_management/obsidian_sync.py --search "focus management"
```

### Sync Configuration

```python
# In obsidian_sync.py
SyncConfig(
    vault_path="D:/OsMEN/obsidian-vault",
    chroma_host="localhost",
    chroma_port=8000,
    collection_name="obsidian_vault",
    chunk_size=1000,
    chunk_overlap=200
)
```

### What Gets Indexed

- ✅ All `.md` files in vault
- ✅ YAML frontmatter (as metadata)
- ✅ Tags (both `#tag` and frontmatter)
- ✅ Links (as metadata)
- ❌ Images (not embedded, paths stored)
- ❌ `.obsidian/` folder

## Librarian Agent RAG

The Librarian agent uses ChromaDB with specialized RAG modes:

### RAG Modes

| Mode | Purpose | Use When |
|------|---------|----------|
| `foundation` | Core knowledge retrieval | General questions |
| `lateral` | Cross-domain connections | Finding relationships |
| `factcheck` | Verification queries | Checking accuracy |

### Configuration

```python
# Librarian uses Stella 1.5B embeddings
EMBEDDING_MODEL = "dunzhang/stella_en_1.5B_v5"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
```

## MCP Server Integration

### OsMEN MCP Tools for Memory

```python
# From gateway/mcp/tool_registry.py

# Store in vector memory
@register_tool
def memory_store(content: str, category: str, tags: list) -> dict:
    """Store content in ChromaDB with metadata"""
    
# Recall from vector memory
@register_tool
def memory_recall(query: str, limit: int = 5) -> list:
    """Search ChromaDB for relevant memories"""
```

### VS Code Integration

Your `mcp.json` is configured to use:

1. **chroma-mcp**: Direct ChromaDB access
   - Collections: list, create, query
   - Documents: add, delete, update

2. **memory-mcp**: Knowledge graph for entities
   - Create entities with relationships
   - Search by name or relationship

## Workflow Example

### Research Task Flow

```
User Request: "Research attention management techniques"
                │
                ▼
┌───────────────────────────────────┐
│  1. Check ChromaDB for existing   │
│     notes (obsidian_vault)        │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  2. Check Librarian docs          │
│     (librarian_docs collection)   │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  3. Use Context7 for library      │
│     documentation if needed       │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  4. Synthesize response           │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  5. Store result in ChromaDB      │
│     (agent_memory collection)     │
└───────────────────────────────────┘
```

## Configuration Reference

### Environment Variables

```env
# ChromaDB
CHROMADB_HOST=http://chromadb:8000
CHROMADB_PERSIST_DIR=./data/chromadb

# Redis
REDIS_URL=redis://localhost:6379
REDIS_CACHE_TTL=60

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=osmen

# Context7 (optional)
CONTEXT7_API_KEY=your_api_key_here

# Obsidian
OBSIDIAN_VAULT_PATH=D:/OsMEN/obsidian-vault
```

### Docker Services

```yaml
# In docker-compose.yml
services:
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma-data:/chroma/chroma
      
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
      
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
```

## Quick Reference

### Starting Services

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View ChromaDB logs
docker compose logs chromadb
```

### Testing Memory

```bash
# Test ChromaDB connection
curl http://localhost:8000/api/v2/heartbeat

# Test Redis
redis-cli ping

# Run Obsidian sync
python agents/knowledge_management/obsidian_sync.py --vault D:\OsMEN\obsidian-vault --stats
```

### Common Operations

```python
# Python quick access
import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)

# List collections
print(client.list_collections())

# Create collection
collection = client.get_or_create_collection("test")

# Add document
collection.add(
    documents=["Test document"],
    metadatas=[{"source": "test"}],
    ids=["test-1"]
)

# Query
results = collection.query(
    query_texts=["test"],
    n_results=5
)
```

## Maintenance

### Backup

```bash
# Backup ChromaDB data
docker compose exec chromadb tar -czf /backup/chroma-backup.tar.gz /chroma/chroma

# Backup PostgreSQL
docker compose exec postgres pg_dump -U osmen osmen > backup.sql
```

### Cleanup

```bash
# Remove old agent memories (keep last 30 days)
# Run via Python script or scheduled n8n workflow
```

---

**Last Updated**: 2025-01-19
**Version**: 2.0 (Post-consolidation)
