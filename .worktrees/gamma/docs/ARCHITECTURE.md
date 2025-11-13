# OsMEN Architecture

## System Overview

OsMEN is a local-first, no/low-code agent hub that combines:
- **Langflow**: Visual reasoning graph builder for LLM agents
- **n8n**: Workflow automation and orchestration
- **Ollama**: Local LLM inference
- **Qdrant**: Vector database for memory storage
- **Tool Layer**: Integration with system utilities

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
├─────────────────────────────────────────────────────────────┤
│  Langflow UI (7860)    │    n8n UI (5678)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Coordinator Agent                         │
│              (Langflow - Task Routing)                       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│Boot Hardening│    │ Daily Brief  │    │   Focus      │
│  Specialist  │    │  Specialist  │    │ Guardrails   │
│   (Agent)    │    │   (Agent)    │    │  Specialist  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      n8n Automation                          │
│  (Triggers, Workflows, Subflows, State Management)          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Ollama     │    │   Qdrant     │    │   Tool       │
│  (Local LLM) │    │(Vector Store)│    │   Layer      │
└──────────────┘    └──────────────┘    └──────────────┘
                                                │
                              ┌─────────────────┼─────────────┐
                              ▼                 ▼             ▼
                      ┌──────────┐    ┌──────────┐  ┌──────────┐
                      │Simplewall│    │Sysinter- │  │ FFmpeg   │
                      │          │    │  nals    │  │          │
                      └──────────┘    └──────────┘  └──────────┘
```

## Component Details

### Langflow Layer

**Purpose**: Visual graph-based agent reasoning and coordination

**Components**:
- **Coordinator Agent**: Routes requests to appropriate specialists
- **Specialist Agents**: Domain-specific agents for:
  - Boot Hardening
  - Daily Brief
  - Focus Guardrails
  - Content Editing
  - Research Intelligence

**Features**:
- Visual flow builder
- LLM integration
- Tool calling
- Memory retrieval from Qdrant

### n8n Automation Layer

**Purpose**: Workflow automation, triggers, and state management

**Components**:
- **Trigger Workflows**: Schedule and event-based triggers
  - Daily boot hardening check
  - Morning daily brief
  - Periodic focus monitoring
- **Subflows**: Reusable workflow components
- **State Management**: Persistent workflow state

**Features**:
- Cron scheduling
- HTTP webhooks
- Conditional logic
- Data transformation
- Integration with Langflow agents

### Ollama (Local LLM)

**Purpose**: Local language model inference

**Features**:
- GPU acceleration support
- Multiple model support (llama2, mistral, etc.)
- API-compatible with OpenAI
- Privacy-focused (all data stays local)

**Models**:
- **llama2**: General purpose reasoning
- **mistral**: Fast inference for real-time tasks
- **codellama**: Code analysis and generation

### Qdrant (Vector Database)

**Purpose**: Memory storage and retrieval

**Collections**:
- **osmen_memory**: Global agent memory
- **boot_hardening_memory**: Boot hardening context
- **daily_brief_memory**: Historical briefs and trends
- **focus_guardrails_memory**: Focus session history

**Features**:
- Vector similarity search
- Metadata filtering
- Persistent storage
- High-performance retrieval

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
6. Specialist retrieves context from Qdrant
   ↓
7. Specialist calls Sysinternals tools
   ↓
8. Results stored in Qdrant
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
4. Specialist queries Qdrant for historical data
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
5. Usage data stored in Qdrant
   ↓
6. Status returned to n8n
```

## Scalability Considerations

### Horizontal Scaling
- Multiple Langflow instances (load balanced)
- Multiple n8n workers for parallel execution
- Qdrant cluster for distributed storage

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
- Qdrant collections
- n8n workflows
- Langflow flows
- Environment configuration

### Backup Strategy
```bash
# Backup PostgreSQL
docker exec osmen-postgres pg_dumpall -U postgres > backup.sql

# Backup Qdrant
docker exec osmen-qdrant tar czf /backup/qdrant.tar.gz /qdrant/storage

# Backup configurations
tar czf config-backup.tar.gz n8n/workflows langflow/flows .env
```

## Troubleshooting Guide

See [SETUP.md](SETUP.md#troubleshooting) for common issues and solutions.
