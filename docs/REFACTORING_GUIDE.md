# OsMEN Refactoring Guide

## Architecture Overview

OsMEN has been refactored to use a **Setup Manager** + **CLI Bridge** architecture that puts Langflow and n8n at the forefront of the user experience, while providing powerful system-wide management capabilities.

## New Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   User Interface Layer                       │
├─────────────────────────────────────────────────────────────┤
│  Langflow (Primary GUI) │ n8n (Automation) │ Web Dashboard  │
│         Port 7860        │    Port 5678     │   Port 8000    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Setup Manager Layer                       │
│         Centralized initialization & configuration           │
├─────────────────────────────────────────────────────────────┤
│  • ConfigManager - Environment & agent configuration         │
│  • SetupManager - Agent lifecycle & service connections      │
│  • System-wide change management                             │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│   CLI Bridge     │  │   Agents     │  │  Services    │
│   Layer          │  │   Layer      │  │   Layer      │
├──────────────────┤  ├──────────────┤  ├──────────────┤
│ • CodexBridge    │  │ 15 Agents    │  │ • Qdrant     │
│ • CopilotBridge  │  │ initialized  │  │ • PostgreSQL │
│ • BridgeManager  │  │ via Setup    │  │ • Redis      │
│                  │  │ Manager      │  │              │
└──────────────────┘  └──────────────┘  └──────────────┘
```

## Key Components

### 1. Setup Manager (`setup_manager/`)

**Purpose**: Centralized initialization and lifecycle management for all OsMEN components.

**Files**:
- `manager.py` - Core SetupManager class
- `config.py` - ConfigManager for environment variables and settings

**Capabilities**:
- Environment validation (Docker, Python, config, directories)
- Agent initialization with dependency injection
- Service connection management (Langflow, n8n, Qdrant)
- System-wide configuration changes
- Graceful shutdown and cleanup

**Usage**:
```python
from setup_manager import SetupManager

# Initialize
manager = SetupManager()

# Validate environment
validations = manager.validate_environment()

# Initialize specific agent
agent = manager.initialize_agent('boot_hardening')

# Initialize all enabled agents
agents = manager.initialize_all_agents()

# Connect to services
services = manager.initialize_services()

# Apply system-wide change
manager.apply_system_change('config', {'LOG_LEVEL': 'DEBUG'})

# Get system status
status = manager.get_system_status()

# Shutdown
manager.shutdown()
```

### 2. CLI Bridge (`cli_bridge/`)

**Purpose**: Unified interface to Codex CLI and Copilot CLI for AI-powered assistance.

**Files**:
- `codex_bridge.py` - OpenAI Codex integration
- `copilot_bridge.py` - GitHub Copilot integration
- `bridge_manager.py` - Unified interface

**Capabilities**:

**Codex Bridge**:
- Code generation from natural language
- Code explanation and documentation
- Code review and quality checks
- Code completion

**Copilot Bridge**:
- Shell command suggestions
- Command explanations
- Git workflow assistance
- Context-aware help

**Usage**:
```python
from cli_bridge import CLIBridgeManager

# Initialize
bridge = CLIBridgeManager()

# Generate code
result = bridge.generate_code(
    "Create a function to validate email addresses",
    language='python'
)

# Suggest shell command
result = bridge.suggest_command(
    "Find all Python files modified in the last week"
)

# Explain code
result = bridge.explain_code(
    "def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2)",
    language='python'
)

# Get git help
result = bridge.get_git_help(
    "create a new branch and switch to it"
)

# Auto-route task to appropriate bridge
result = bridge.assist_with_task(
    "Create a function to sort a list",
    task_type='auto'
)
```

### 3. GUI Experience through Langflow & n8n

**Langflow** (Primary GUI):
- Visual agent workflow design
- Drag-and-drop flow builder
- Real-time testing and debugging
- Agent coordination and routing

**n8n** (Automation):
- Scheduled workflows
- Event-driven triggers
- Multi-step automations
- Service integrations

**Setup Manager Integration**:
- Agents initialized by Setup Manager
- GUI controls modify agent configuration
- System-wide changes propagate through Setup Manager
- Unified state management

## Migration Guide

### For Developers

**Before** (Direct agent instantiation):
```python
from agents.boot_hardening.boot_hardening_agent import BootHardeningAgent

agent = BootHardeningAgent()
report = agent.get_hardening_report()
```

**After** (Setup Manager):
```python
from setup_manager import SetupManager

manager = SetupManager()
agent = manager.initialize_agent('boot_hardening')
report = agent.get_hardening_report()
```

### For No-Code Users

**Before**:
- Manually run Python scripts
- Edit configuration files directly
- Restart services manually

**After**:
- Use Langflow GUI to create and run agent workflows
- Use n8n to schedule automations
- Setup Manager handles all initialization
- System-wide changes through web dashboard or Langflow

## Configuration

### Environment Variables

The Setup Manager uses these key environment variables:

**Required**:
- `N8N_BASIC_AUTH_PASSWORD` - n8n admin password
- `WEB_SECRET_KEY` - Web dashboard secret key (32+ chars)

**LLM Providers** (at least one required):
- `OPENAI_API_KEY` - OpenAI API for Codex
- `GITHUB_TOKEN` - GitHub token for Copilot CLI
- `ANTHROPIC_API_KEY` - Anthropic Claude
- `LM_STUDIO_URL` - Local LM Studio endpoint
- `OLLAMA_URL` - Local Ollama endpoint

**Services**:
- `LANGFLOW_URL` - Langflow service URL (default: http://localhost:7860)
- `N8N_URL` - n8n service URL (default: http://localhost:5678)
- `QDRANT_URL` - Qdrant service URL (default: http://localhost:6333)

**Agent Configuration**:
- `ENABLED_AGENTS` - Comma-separated list of agents to enable
- `{AGENT_NAME}_{CONFIG_KEY}` - Agent-specific configuration

### Example .env

```bash
# Security
N8N_BASIC_AUTH_PASSWORD=secure-password-here
WEB_SECRET_KEY=your-secret-key-here-min-32-characters

# LLM Providers
OPENAI_API_KEY=sk-your-openai-key
GITHUB_TOKEN=ghp_your-github-token

# Services (defaults shown)
LANGFLOW_URL=http://localhost:7860
N8N_URL=http://localhost:5678
QDRANT_URL=http://localhost:6333

# Agents
ENABLED_AGENTS=boot_hardening,daily_brief,focus_guardrails,personal_assistant

# Logging
LOG_LEVEL=INFO
```

## Testing

### Test Setup Manager

```bash
python3 -m setup_manager.manager
```

### Test CLI Bridge

```bash
# Test Codex Bridge
python3 -m cli_bridge.codex_bridge

# Test Copilot Bridge
python3 -m cli_bridge.copilot_bridge

# Test Bridge Manager
python3 -m cli_bridge.bridge_manager
```

### Run Full Test Suite

```bash
# All tests
python3 test_agents.py

# Operational check
python3 check_operational.py

# Validation
make validate
```

## Benefits of New Architecture

### For No-Code Users

1. **Unified GUI Experience**: Primary interaction through Langflow visual interface
2. **Automation Made Easy**: n8n workflows for scheduled tasks
3. **No Code Required**: All functionality accessible through GUI
4. **System-Wide Management**: Setup Manager handles complexity
5. **AI Assistance**: Codex and Copilot CLI integrated throughout

### For Developers

1. **Centralized Configuration**: Single source of truth via ConfigManager
2. **Dependency Injection**: Agents initialized with proper configuration
3. **Lifecycle Management**: Proper startup, shutdown, and cleanup
4. **Service Abstraction**: Easy service connection management
5. **Testability**: Mock services and agents easily
6. **Extensibility**: Add new agents with minimal boilerplate

### For System Administration

1. **Health Monitoring**: Built-in environment validation
2. **Service Management**: Unified service connection handling
3. **Configuration Management**: Centralized config with validation
4. **Change Control**: System-wide changes with rollback capability
5. **Logging & Debugging**: Consistent logging across all components

## Roadmap

### Phase 1: Infrastructure (Complete)
- ✅ Setup Manager implementation
- ✅ CLI Bridge implementation
- ✅ Configuration management
- ✅ Basic documentation

### Phase 2: Agent Integration (In Progress)
- [ ] Refactor agents to use Setup Manager
- [ ] Add CLI Bridge to agent workflows
- [ ] Update agent tests
- [ ] Integration testing

### Phase 3: GUI Enhancement (Planned)
- [ ] Create Langflow flows for each agent
- [ ] Create n8n workflows for automations
- [ ] Update web dashboard
- [ ] User guides and tutorials

### Phase 4: Production Readiness (Planned)
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Comprehensive testing
- [ ] Migration tooling
- [ ] Production deployment guide

## Best Practices

### 1. Always Use Setup Manager

```python
# ✅ Good
from setup_manager import SetupManager
manager = SetupManager()
agent = manager.initialize_agent('agent_name')

# ❌ Avoid
from agents.agent_name.agent_name_agent import AgentNameAgent
agent = AgentNameAgent()
```

### 2. Use CLI Bridge for AI Assistance

```python
# ✅ Good
from cli_bridge import CLIBridgeManager
bridge = CLIBridgeManager()
result = bridge.assist_with_task("your task here")

# ❌ Avoid
# Calling Codex/Copilot APIs directly
```

### 3. Configure Through Environment

```bash
# ✅ Good - .env file
AGENT_CONFIG_VALUE=something

# ❌ Avoid - Hardcoded in code
config = {'value': 'something'}
```

### 4. Use Langflow for Workflows

```
✅ Good: Create workflows visually in Langflow
❌ Avoid: Complex Python scripts for agent orchestration
```

### 5. Use n8n for Automation

```
✅ Good: Schedule tasks in n8n
❌ Avoid: Cron jobs calling Python scripts
```

## Troubleshooting

### Setup Manager Not Finding Configuration

```bash
# Check .env file exists
ls -la .env

# Copy from example if missing
cp .env.example .env

# Edit with required values
nano .env
```

### Services Not Connecting

```bash
# Check services are running
docker-compose ps

# Start services
docker-compose up -d

# Check logs
docker-compose logs langflow n8n qdrant
```

### CLI Bridge Not Working

```bash
# Check API keys are set
echo $OPENAI_API_KEY
echo $GITHUB_TOKEN

# Install Copilot CLI
gh extension install github/gh-copilot

# Test manually
gh copilot suggest "list files"
```

### Agent Initialization Fails

```bash
# Check agent name is correct
python3 -c "from setup_manager import SetupManager; m = SetupManager(); print(m.config_manager.get_enabled_agents())"

# Check agent dependencies
pip install -r requirements.txt

# Enable debug logging
export LOG_LEVEL=DEBUG
python3 -m setup_manager.manager
```

## Support

- **Documentation**: `docs/`
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Tests**: `test_agents.py`
- **Examples**: `examples/` (coming soon)

---

**Last Updated**: 2025-11-17
**Version**: 2.0 (Setup Manager + CLI Bridge Architecture)
