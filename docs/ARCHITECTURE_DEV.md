# OsMEN Developer Architecture Guide

Technical documentation for developers extending OsMEN v3.0.

## Core Components Added in v3.0

### 1. LLM Provider Adapters

**Location**: `integrations/llm_providers.py`

Unified interface for all LLM providers with identical tool-call semantics:

```python
from integrations.llm_providers import get_llm_provider, LLMConfig

# Auto-select available provider (local-first)
llm = await get_llm_provider()

# Or specify provider
llm = await get_llm_provider("openai")

# Common interface for all providers
response = await llm.chat([
    {"role": "user", "content": "Hello"}
])

# Tool calling (works on all providers)
response = await llm.tool_call(
    messages=[...],
    tools=[ToolDefinition(
        name="search",
        description="Search the web",
        parameters={"query": {"type": "string"}}
    )]
)

# Streaming (SSE-ready)
async for chunk in llm.stream([{"role": "user", "content": "Hello"}]):
    print(chunk, end="")
```

**Provider Priority**:
1. **Ollama** (local) - Default, no API key needed
2. **OpenAI** - Cloud fallback with tool support
3. **Anthropic** - Cloud fallback with tool support

**Configuration**:
```python
LLMConfig(
    provider=ProviderType.OLLAMA,
    model="llama3.2",
    temperature=0.7,
    max_tokens=4096,
    json_mode=False,
    rate_limit_rpm=60,
    rate_limit_tpm=100000,
    retry_attempts=3,
    retry_delay=1.0,
    timeout=120.0
)
```

### 2. Workflows System

**Location**: `workflows/`

Production-ready workflow implementations:

```python
from workflows import DailyBriefWorkflow, DailyBriefConfig

config = DailyBriefConfig(
    llm_provider="ollama",
    include_google_calendar=True,
    include_gmail=True
)

workflow = DailyBriefWorkflow(config)
result = await workflow.run()

print(result.brief)  # Markdown summary
print(result.data)   # Raw data
print(result.status) # WorkflowStatus.COMPLETED
```

### 3. Multi-Agent Orchestration

**Location**: `integrations/langchain_ecosystem.py`

LangGraph-inspired orchestration patterns:

```python
from integrations.langchain_ecosystem import (
    get_langchain_ecosystem,
    OrchestrationPattern,
    AgentNode,
    AgentRole
)

ecosystem = get_langchain_ecosystem()

# Create orchestrator
orchestrator = ecosystem.create_orchestrator(
    "research",
    OrchestrationPattern.HIERARCHICAL
)

# Add agents
orchestrator.add_agent(AgentNode(
    id="coordinator",
    role=AgentRole.COORDINATOR,
    capabilities=["planning", "delegation"]
))

# Execute
result = await orchestrator.execute({"query": "AI trends"})
```

**Patterns**:
- `SEQUENTIAL`: Agents run in sequence
- `PARALLEL`: Agents run concurrently
- `HIERARCHICAL`: Coordinator delegates to specialists
- `SUPERVISOR`: Supervisor validates and iterates

## Directory Structure (v3.0 additions)

```
osmen/
├── integrations/
│   ├── llm_providers.py       # NEW: LLM adapter layer
│   ├── langchain_ecosystem.py # NEW: LangGraph integration
│   ├── langflow_enhanced.py   # NEW: Enhanced Langflow
│   ├── awesome_generative_ai.py # NEW: AI resource catalog
│   ├── v3_integration_layer.py
│   └── token_manager.py
├── workflows/                 # NEW: Production workflows
│   ├── daily_brief.py
│   └── __init__.py
├── gateway/
│   ├── health.py              # NEW: K8s health probes
│   └── middleware/
│       └── rate_limit.py      # NEW: Rate limiting
├── infra/
│   ├── monitoring/
│   │   ├── prometheus.yml     # NEW: Metrics config
│   │   └── grafana_dashboards.json # NEW: Dashboards
│   ├── ssl/
│   │   └── certbot_auto.sh    # NEW: SSL automation
│   └── terraform/
│       └── main.tf            # NEW: AWS IaC
└── docs/
    ├── QUICKSTART_USER.md     # NEW: End-user guide
    └── ARCHITECTURE_DEV.md    # NEW: Developer guide
```

## Adding a New LLM Provider

1. Create adapter class in `integrations/llm_providers.py`:

```python
class MyProvider(LLMProvider):
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        # Implementation
        pass
    
    async def chat(self, messages, **kwargs) -> LLMResponse:
        # Implementation
        pass
    
    async def tool_call(self, messages, tools, **kwargs) -> LLMResponse:
        # Implementation
        pass
    
    async def stream(self, messages, **kwargs) -> AsyncGenerator:
        # Implementation
        pass
```

2. Register in `ProviderRouter.initialize()`:

```python
if my_provider_available:
    self._providers[ProviderType.MY_PROVIDER] = MyProvider(config)
```

## Adding a New Workflow

1. Create workflow file:

```python
# workflows/my_workflow.py

@dataclass
class MyWorkflowConfig:
    llm_provider: str = "ollama"
    # ... config options

class MyWorkflow:
    def __init__(self, config: MyWorkflowConfig = None):
        self.config = config or MyWorkflowConfig()
    
    async def run(self) -> WorkflowResult:
        # 1. Collect data
        # 2. Process with LLM
        # 3. Return result
        pass
```

2. Export in `workflows/__init__.py`:

```python
from workflows.my_workflow import MyWorkflow, MyWorkflowConfig
```

## Testing

```bash
# Unit tests
python -m pytest tests/

# Agent tests
python test_agents.py

# Integration tests
python -m pytest tests/integration/

# Workflow E2E test
python workflows/daily_brief.py --provider ollama
```

## Performance Benchmarks

| Operation | Ollama (local) | OpenAI | Anthropic |
|-----------|---------------|--------|-----------|
| Simple chat | ~500ms | ~200ms | ~300ms |
| Tool call | ~800ms | ~400ms | ~500ms |
| Streaming | ~50ms/chunk | ~20ms/chunk | ~30ms/chunk |

## Security

- Tokens encrypted with Fernet (AES-128)
- File permissions: 600 (tokens), 700 (directories)
- No secrets in code or git
- Rate limiting on all endpoints
- HTTPS enforced in production
