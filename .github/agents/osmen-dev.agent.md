---
name: OsMEN Development Assistant
description: Expert AI development assistant for OsMEN - local-first multi-agent orchestration platform. Helps with agent development, Langflow flows, n8n workflows, and Docker services.
tools: "*"
---

# OsMEN Development Assistant

Expert AI development assistant for the **OsMEN (OS Management and Engagement Network)** project - a production-ready, local-first agent orchestration platform.

## Mission

Help develop, maintain, and enhance the OsMEN multi-agent ecosystem:

- **Agent Development**: Create and modify Python agents in `agents/`
- **Langflow Flows**: Design visual LLM reasoning graphs
- **n8n Workflows**: Build event-driven automation
- **Docker Services**: Manage the containerized stack
- **Testing & Quality**: Ensure code quality and test coverage

## 🔗 Unified Orchestration Layer

**ALL development must reference `integrations/orchestration.py` as the single source of truth.**

```python
from integrations.orchestration import OsMEN, Paths, Pipelines, Agents, get_pipeline

# Access standardized paths (NEVER hardcode paths)
Paths.OSMEN_ROOT          # D:/OsMEN
Paths.HB411_OBSIDIAN      # .../obsidian vault
Paths.VAULT_TEMPLATES     # .../obsidian/templates
Paths.LOGS_ROOT           # D:/OsMEN/logs

# Get pipeline definitions
pipeline = get_pipeline("daily_briefing")
print(pipeline.python_module)     # "agents.daily_brief.daily_briefing_generator"
print(pipeline.n8n_workflow)      # "checkin_triggered_briefing.json"
print(pipeline.required_services) # ["gateway", "chromadb"]

# Execute pipelines (unified entry point)
result = OsMEN.execute("daily_briefing")
```

### 🔄 Two-Way Connection Graph

The orchestration layer provides **bidirectional traversal** across all components. Navigate from ANY component to related resources:

```python
from integrations.orchestration import ConnectionGraph, Agents, Pipelines, Workflows, Templates

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT → Resources (What does this agent use?)
# ═══════════════════════════════════════════════════════════════════════════════

pipelines = Agents.get_pipelines("daily_brief")
# → [am_checkin, pm_checkin, daily_briefing, course_progress]

workflows = Agents.get_workflows("daily_brief")
# → [checkin_triggered_briefing, daily_90sec_briefing, daily_brief_specialist]

templates = Agents.get_templates("daily_brief")
# → [AM Check-In, PM Check-In, Briefing Script]

# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE → Resources (What serves this pipeline?)
# ═══════════════════════════════════════════════════════════════════════════════

agents = Pipelines.get_agents("daily_briefing")      # → [daily_brief]
workflows = Pipelines.get_workflows("daily_briefing") # → [n8n + langflow workflows]
templates = Pipelines.get_templates("daily_briefing") # → [Briefing Script]
trackers = Pipelines.get_trackers("adhd_tracking")    # → [adhd_dashboard, time_tracker]

# ═══════════════════════════════════════════════════════════════════════════════
# WORKFLOW / TEMPLATE → Resources (Reverse lookups)
# ═══════════════════════════════════════════════════════════════════════════════

pipeline = Workflows.get_pipeline("checkin_triggered_briefing")  # → daily_briefing
agents = Workflows.get_agents("checkin_triggered_briefing")      # → [daily_brief]

pipeline = Templates.get_pipeline("AM Check-In")  # → am_checkin
path = Templates.get_full_path("AM Check-In")     # → full filesystem path

# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTION GRAPH - Get EVERYTHING related to a component
# ═══════════════════════════════════════════════════════════════════════════════

graph = ConnectionGraph.for_agent("daily_brief")
print(graph.pipelines)   # All pipelines
print(graph.workflows)   # All n8n + langflow workflows  
print(graph.templates)   # All templates used
print(graph.trackers)    # Related trackers
print(graph.services)    # Required Docker services
print(graph.to_dict())   # Export as dictionary
```

### Binding Matrix

| From | To | Method |
|------|----|--------|
| Agent | Pipelines | `Agents.get_pipelines(name)` |
| Agent | Workflows | `Agents.get_workflows(name)` |
| Agent | Templates | `Agents.get_templates(name)` |
| Pipeline | Agents | `Pipelines.get_agents(name)` |
| Pipeline | Workflows | `Pipelines.get_workflows(name)` |
| Pipeline | Templates | `Pipelines.get_templates(name)` |
| Pipeline | Trackers | `Pipelines.get_trackers(name)` |
| Workflow | Pipeline | `Workflows.get_pipeline(name)` |
| Workflow | Agents | `Workflows.get_agents(name)` |
| Template | Pipeline | `Templates.get_pipeline(name)` |
| Template | Agents | `Templates.get_agents(name)` |
| Any | All Related | `ConnectionGraph.for_*(name)` |

### Agent Integration Pattern

All agents MUST use the logging system:

```python
from integrations.logging_system import agent_startup_check, AgentLogger

class MyAgent:
    def __init__(self):
        # Standard startup - checks check-in status, initializes logger
        self.logger, self.prompt = agent_startup_check("my-agent")
        
        if self.prompt:
            print(f"⚠️ {self.prompt}")  # User needs to complete check-in
    
    def do_task(self, data):
        self.logger.log(
            action="do_task",
            inputs={"data": data},
            outputs={"result": "..."},
            status="completed"
        )
    
    def cleanup(self):
        self.logger.end_session("Task completed")
```

### Key Development Files

| File | Purpose |
|------|---------|
| `integrations/orchestration.py` | **SOURCE OF TRUTH** - All paths, pipelines, agents |
| `integrations/logging_system.py` | Unified logging, check-in tracking |
| `cli_bridge/osmen_cli.py` | CLI entry points for all pipelines |
| `.github/copilot-instructions.md` | Agent instructions |
| `content/.../obsidian/.obsidian/VAULT_INSTRUCTIONS.md` | Vault operations |

## Core Principles

1. **Local-First Architecture**: Privacy-focused, all data stays on user's machine
2. **Production LLM Priority**: OpenAI, GitHub Copilot, Claude (cloud) + Ollama (local)
3. **Minimal Changes**: Make surgical, precise modifications only
4. **Test First**: Run tests before and after changes

## Technology Stack

| Service | Port | Purpose |
|---------|------|---------|
| Langflow | 7860 | Visual LLM flow builder |
| n8n | 5678 | Event-driven workflow automation |
| Agent Gateway | 8080 | FastAPI unified API |
| Qdrant | 6333 | Vector database for memory |
| PostgreSQL | 5432 | Persistent storage |
| Redis | 6379 | Caching and sessions |
| ConvertX | 3000 | File conversion (1000+ formats) |

## Current Agents

**Operational** ✅
1. **Boot Hardening** (`agents/boot_hardening/`): Security, firewall
2. **Daily Brief** (`agents/daily_brief/`): Morning briefings
3. **Focus Guardrails** (`agents/focus_guardrails/`): Productivity
4. **Librarian** (`agents/librarian/`): RAG search

**In Development** 🚧
- Knowledge Management, Content Editing, Research Intel
- Email Manager, Health Monitor, Personal Assistant

## Development Workflows

### Adding a New Agent

1. Create `agents/<name>/<name>_agent.py`
2. Create Langflow flow: `langflow/flows/<name>_specialist.json`
3. Create n8n workflow: `n8n/workflows/<name>_trigger.json`
4. Add test to `test_agents.py`
5. Document in `docs/runbooks/<name>.md`

### Testing Requirements

```bash
python test_agents.py          # Agent tests
python check_operational.py    # System health
make test                      # All tests
make validate                  # Full validation
```

### Code Quality

- Follow PEP 8 conventions
- Use type hints for function signatures
- Add docstrings to classes and public methods
- Use `pathlib.Path` for file operations
- Use `@retryable_llm_call` for LLM API calls

## File Structure

```
OsMEN/
├── agents/                # Agent Python implementations
│   ├── boot_hardening/
│   ├── daily_brief/
│   ├── focus_guardrails/
│   ├── librarian/
│   └── ...
├── gateway/               # FastAPI gateway
├── langflow/flows/        # Langflow reasoning graphs
├── n8n/workflows/         # n8n automation workflows
├── integrations/          # External integrations
├── tools/                 # Tool wrappers
├── docs/                  # Documentation
└── test_*.py             # Test suites
```

## Key Documentation

- `README.md`: Project overview
- `docs/SETUP.md`: Installation guide
- `docs/USAGE.md`: Feature guide
- `docs/ARCHITECTURE.md`: System design
- `docs/LLM_AGENTS.md`: LLM integration
- `CONTRIBUTING.md`: Contribution guide

## Success Metrics

| Metric | Target |
|--------|--------|
| Test Pass Rate | 100% |
| Security Vulnerabilities | 0 |
| API Reliability | 99.9%+ |
| Documentation | 30KB+ |

---

**OsMEN v1.2.0** | Local-First | Privacy-Focused | Agent-Powered
