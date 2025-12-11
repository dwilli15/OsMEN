# OsMEN Architecture

## System Overview

OsMEN is a **no-code agent team orchestration** platform that combines:

- **Codex CLI**: OpenAI Codex for code generation and technical tasks
- **Copilot CLI**: GitHub Copilot for development assistance
- **Langflow**: Visual reasoning graph builder for LLM agents
- **n8n**: Workflow automation and orchestration
- **Cloud LLMs**: OpenAI GPT-4, Copilot, Amazon Q, Claude
- **Local LLMs**: LM Studio, Ollama for privacy-focused inference
- **ChromaDB**: Vector database for long-term memory (RAG, semantic search)
- **SQLite**: Short-term structured memory (sessions, tasks, conversations)
- **Hybrid Memory**: Dynamic bridges between short/long term with lateral thinking
- **Tool Layer**: Integration with Zoom, Audiblez, Vibevoice, Obsidian, Notion, and system utilities

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface Layer                    │
├─────────────────────────────────────────────────────────────┤
│  Langflow (7860)  │   n8n (5678)   │  Web Dashboard (8000)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Model Source Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Codex CLI  │ Copilot CLI │ GPT-4 │ Claude │ LM Studio     │
│             │             │       │        │ Ollama        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Coordinator Agent                          │
│                (Langflow - Task Routing)                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Personal     │    │  Content     │    │Communication │
│ Productivity │    │  Creation    │    │    Team      │
│   Team       │    │    Team      │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Knowledge   │    │   System     │    │  Security    │
│    Team      │    │    Team      │    │    Team      │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    n8n Automation Layer                      │
│         (Triggers, Workflows, State Management)              │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  ChromaDB    │    │  PostgreSQL  │    │    Redis     │
│ (Long-Term)  │    │ (Database)   │    │   (Cache)    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                                       │
        └───────────────┬───────────────────────┘
                        ▼
              ┌──────────────────┐
              │  Hybrid Memory   │
              │ (SQLite Bridge)  │
              └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Tool Layer                             │
├─────────────────────────────────────────────────────────────┤
│ Codex  │ Copilot │ Zoom │ Audiblez │ Vibevoice │ Obsidian  │
│  CLI   │   CLI   │      │          │           │  Notion   │
├─────────────────────────────────────────────────────────────┤
│ Simplewall │ Sysinternals │ FFmpeg │ System Tools           │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### Model Source Layer

**Purpose**: Provide AI model capabilities for agents

**Components**:

1. **Codex CLI Integration**
   - Code generation from natural language
   - Code completion and review
   - Code explanation and documentation
   - Technical task automation

2. **Copilot CLI Integration**
   - Command-line assistance
   - Shell command suggestions
   - Git workflow help
   - Context-aware code suggestions

3. **Cloud LLM Providers**
   - **OpenAI GPT-4**: Advanced reasoning and generation
   - **GitHub Copilot**: Development assistance
   - **Amazon Q**: AWS integration and enterprise features
   - **Claude**: Long-context understanding

4. **Local LLM Options**
   - **LM Studio**: Primary local option, user-friendly
   - **Ollama**: Secondary option, CLI-focused

**Model Selection Logic**:

- Codex CLI for code generation tasks
- Copilot CLI for development workflows
- GPT-4 for complex reasoning
- Claude for long documents
- Local LLMs for privacy-sensitive data

### Agent Teams

**Purpose**: Organize specialized agents into functional teams

**Teams**:

#### 1. Personal Productivity Team

- **Personal Assistant Agent**: Task and calendar management
- **Focus Guardrails Agent**: Distraction blocking
- **Daily Brief Agent**: Morning summaries

**Primary Model**: GPT-4 for reasoning, Copilot CLI for scheduling

#### 2. Content Creation Team

- **Content Creator Agent**: Image/video generation
- **Audiobook Creator Agent**: ebook to audiobook conversion
- **Podcast Creator Agent**: Podcast generation from notes

**Primary Model**: GPT-4 for content, Codex CLI for processing scripts

#### 3. Communication Team

- **Email Manager Agent**: Email automation
- **Live Caption Agent**: Meeting transcription
- **Contact Management**: Contact database

**Primary Model**: GPT-4 for email composition, Claude for transcription

#### 4. Knowledge Team

- **Knowledge Management Agent**: Obsidian/Notion integration
- **Syllabus Parser Agent**: Extract events from syllabuses
- **Research Intel Agent**: Information gathering

**Primary Model**: Claude for long documents, GPT-4 for organization

#### 5. System Team

- **OS Optimizer Agent**: Performance tuning
- **Boot Hardening Agent**: Security verification
- **Performance Monitor**: Resource tracking

**Primary Model**: Codex CLI for scripts, Copilot CLI for commands

#### 6. Security Team

- **Security Operations Agent**: Vulnerability scanning
- **Compliance Monitor**: Policy enforcement
- **Threat Detection**: Anomaly detection

**Primary Model**: Codex CLI for security scripts, GPT-4 for analysis

### Langflow Layer

**Purpose**: Visual graph-based agent reasoning and coordination

**Components**:

- **Coordinator Agent**: Routes requests to appropriate specialist teams
- **Specialist Agents**: Domain-specific agents organized in teams
  - Personal Productivity (3 agents)
  - Content Creation (3 agents)
  - Communication (3 agents)
  - Knowledge (3 agents)
  - System (3 agents)
  - Security (3 agents)

**Features**:

- Visual flow builder with drag-and-drop
- Multi-model LLM integration
- Tool calling and orchestration
- Memory retrieval from Hybrid Memory (ChromaDB + SQLite)
- Conversation state management
- Error handling and retry logic

**Flow Types**:

- **Coordinator Flow**: Main entry point, routes to specialists
- **Specialist Flows**: Domain-specific reasoning graphs
- **Tool Flows**: Integration with external tools
- **Memory Flows**: Context retrieval and storage

### n8n Automation Layer

**Purpose**: Workflow automation, triggers, and state management

**Components**:

- **Trigger Workflows**: Schedule and event-based triggers
  - Daily boot hardening check (6 AM)
  - Morning daily brief (8 AM)
  - Periodic focus monitoring (hourly)
  - Weekly system optimization (Sunday 2 AM)
  - Security scans (hourly)
  
- **Agent Workflows**: Orchestrate multi-agent tasks
  - Syllabus to calendar pipeline
  - Podcast creation workflow
  - Meeting transcription workflow
  - Weekly knowledge digest
  
- **Subflows**: Reusable workflow components
  - Email sending
  - Calendar event creation
  - Note creation in Obsidian
  - Notification dispatch

- **State Management**: Persistent workflow state
  - Task queues
  - Processing status
  - Error states
  - Retry counters

**Features**:

- Cron scheduling with timezone support
- HTTP webhooks for external triggers
- Conditional logic and branching
- Data transformation and mapping
- Integration with Langflow agents
- Error handling and notifications

**Features**:

- GPU acceleration support
- Multiple model support (llama2, mistral, etc.)
- API-compatible with OpenAI
- Privacy-focused (all data stays local)

**Models**:

- **llama2**: General purpose reasoning
- **mistral**: Fast inference for real-time tasks
- **codellama**: Code analysis and generation

### ChromaDB (Vector Database - Long-Term Memory)

**Purpose**: Persistent semantic memory and RAG retrieval

**Port**: 8000

**Collections**:

- **osmen_long_term**: Global agent memory with Context7 enrichment
- **boot_hardening_memory**: Boot hardening context
- **daily_brief_memory**: Historical briefs and trends
- **librarian_knowledge**: RAG knowledge base with Stella embeddings

**Features**:

- Semantic similarity search (cosine distance)
- Context7 metadata for 7-dimensional context
- Lateral thinking retrieval (focus + shadow vectors)
- Bridge storage for synchronicity connections

### SQLite (Short-Term Memory)

**Purpose**: Session state, quick lookups, working memory

**Location**: `data/memory/short_term.db`

**Tables**:

- **memories**: Active memories with Context7 metadata
- **sessions**: Agent session state
- **memories_fts**: Full-text search index

**Features**:

- Fast keyword search (FTS5)
- Session state persistence
- Recent conversation history
- Task and working memory

### Hybrid Memory System (`integrations/memory/`)

**Purpose**: Dynamic bridging between short and long-term memory

**Components**:

1. **HybridMemory** (`hybrid_memory.py`)
   - Unified interface for all memory operations
   - Automatic tier management (working → short → long)
   - Context7 enrichment on store

2. **MemoryBridge** (`bridge.py`)
   - Promotion: short-term → long-term based on access patterns
   - Decay: archive stale memories
   - Synchronicity detection between disparate concepts

3. **SequentialReasoner** (`sequential_reasoning.py`)
   - Query decomposition before search
   - Progressive context building
   - Hypothesis generation and verification

4. **LateralBridge** (`lateral_synchronicity.py`)
   - Multi-dimensional query expansion (Context7)
   - Glimmer detection for unexpected connections
   - Focus + Shadow result weaving

**Data Flow**:

```
┌─────────────────────────────────────────────────────────────┐
│                      User/Agent Query                        │
└─────────────────────────────────────────────────────────────┘
                              │
                    SequentialReasoner
                     (decompose query)
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       LateralExpander                   Working Memory
    (focus + shadow queries)              (in-memory)
              │                               │
              ▼                               ▼
┌─────────────────────┐           ┌─────────────────────┐
│     ChromaDB        │           │       SQLite        │
│   (Long-Term RAG)   │           │   (Short-Term FTS)  │
└─────────────────────┘           └─────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
                       MemoryBridge
                 (weave + detect glimmers)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           Woven Results with Synchronicity Bridges          │
└─────────────────────────────────────────────────────────────┘
```

### Tool Layer

**Purpose**: Integration with system utilities

**Tools**:

1. **Simplewall Integration**
   - Firewall rule management
   - Application blocking
   - Domain blocking
   - Network monitoring

2. **Sysinternals Integration**
   - Autoruns (startup analysis)
   - Process Monitor
   - Process Explorer
   - TCPView
   - RootkitRevealer

3. **FFmpeg Integration**
   - Video processing
   - Audio extraction
   - Thumbnail generation
   - Media conversion

### PostgreSQL

**Purpose**: Persistent storage for Langflow and n8n

**Databases**:

- **langflow**: Langflow flows and configurations
- **n8n**: n8n workflows and execution history

### Redis

**Purpose**: Caching and session management

**Features**:

- Session storage
- Temporary data caching
- Rate limiting

## Data Flow

### MVP Use Case: Boot Hardening

```
1. n8n Schedule Trigger (Daily, 00:00)
   ↓
2. n8n checks if BOOT_HARDENING_ENABLED
   ↓
3. n8n calls Langflow Coordinator
   ↓
4. Coordinator routes to Boot Hardening Specialist
   ↓
5. Specialist uses Ollama for reasoning
   ↓
6. Specialist retrieves context from Hybrid Memory (ChromaDB + SQLite)
   ↓
7. Specialist calls Sysinternals tools
   ↓
8. Results stored in Hybrid Memory with Context7 enrichment
   ↓
9. Response returned to n8n
   ↓
10. n8n logs and stores result
```

### MVP Use Case: Daily Brief

```
1. n8n Schedule Trigger (Daily, 08:00)
   ↓
2. n8n calls Daily Brief Specialist
   ↓
3. Specialist gathers system status
   ↓
4. Specialist queries ChromaDB for historical data
   ↓
5. Specialist uses Ollama to generate brief
   ↓
6. Brief formatted and returned
   ↓
7. n8n presents brief to user
```

### MVP Use Case: Focus Guardrails

```
1. n8n Schedule Trigger (Every 15 minutes)
   ↓
2. n8n calls Focus Guardrails Specialist
   ↓
3. Specialist checks active focus session
   ↓
4. Specialist enforces rules via Simplewall
   ↓
5. Usage data stored in Hybrid Memory (ChromaDB + SQLite)
   ↓
6. Status returned to n8n
```

## Scalability Considerations

### Horizontal Scaling

- Multiple Langflow instances (load balanced)
- Multiple n8n workers for parallel execution
- ChromaDB with distributed storage

### Performance Optimization

- Ollama model caching
- Redis for frequently accessed data
- PostgreSQL connection pooling

### Resource Management

- GPU memory allocation for Ollama
- Docker resource limits
- Database query optimization

## Security Considerations

### Network Security

- All services in isolated Docker network
- Simplewall for application-level firewall
- No external network access required

### Data Privacy

- All LLM inference local (no cloud API calls)
- Vector storage encrypted at rest
- Passwords managed via environment variables

### Access Control

- n8n basic authentication
- PostgreSQL user isolation
- API authentication tokens

## Future Enhancements

### Planned Components

1. **Content Editing Pipeline**
   - FFmpeg integration
   - Media processing workflows
   - Content organization

2. **Research Intelligence**
   - Web scraping (local)
   - Document analysis
   - Knowledge graph

3. **Dashboard**
   - Real-time monitoring
   - Agent performance metrics
   - System health visualization

4. **Additional Agents**
   - Grad planning assistant
   - Project management
   - Personal knowledge management

## Development Workflow

1. Design agent flow in Langflow
2. Test agent reasoning with Ollama
3. Create n8n automation workflow
4. Test integration end-to-end
5. Monitor via logs and dashboards
6. Iterate and improve

## Monitoring and Logging

- **Docker logs**: `docker-compose logs -f`
- **Individual service**: `docker-compose logs -f <service>`
- **Application logs**: `./logs/osmen.log`
- **n8n execution logs**: n8n UI → Executions
- **Langflow logs**: Langflow UI → Logs

## Backup and Recovery

### Data to Backup

- PostgreSQL databases
- ChromaDB collections (via docker volume)
- SQLite short-term memory (`data/memory/`)
- n8n workflows
- Langflow flows
- Environment configuration

### Backup Strategy

```bash
# Backup PostgreSQL
docker exec osmen-postgres pg_dumpall -U postgres > backup.sql

# Backup ChromaDB
tar czf chromadb-backup.tar.gz ./chromadb/data

# Backup SQLite memories
cp data/memory/*.db backup/

# Backup configurations
tar czf config-backup.tar.gz n8n/workflows langflow/flows .env
```

## Troubleshooting Guide

See [SETUP.md](SETUP.md#troubleshooting) for common issues and solutions.
