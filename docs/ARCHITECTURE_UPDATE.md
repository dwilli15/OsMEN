# Architecture Update - Setup Manager + CLI Bridge

## New Architecture Components

### Setup Manager Layer

The Setup Manager provides centralized initialization and lifecycle management:

```
User/GUI → Setup Manager → Agents + Services
```

**Key Features**:
- Centralized configuration management
- Environment validation
- Agent initialization with dependency injection
- Service connection management (Langflow, n8n, Qdrant)
- System-wide change propagation
- Graceful shutdown

**Usage**:
```python
from setup_manager import SetupManager

manager = SetupManager()
manager.validate_environment()
agent = manager.initialize_agent('daily_brief')
```

### CLI Bridge Layer

The CLI Bridge provides unified AI assistance from Codex and Copilot:

```
User Task → CLI Bridge → Codex/Copilot → AI Assistance
```

**Key Features**:
- Code generation (Codex)
- Command suggestions (Copilot)
- Code explanation
- Git workflow help
- Auto-routing to appropriate AI

**Usage**:
```python
from cli_bridge import CLIBridgeManager

bridge = CLIBridgeManager()
result = bridge.generate_code("Create a validation function")
```

## Integration with Existing Architecture

The new Setup Manager and CLI Bridge integrate seamlessly:

1. **Langflow** (Primary GUI) → Uses agents initialized by Setup Manager
2. **n8n** (Automation) → Triggers agents through Setup Manager
3. **Web Dashboard** → Leverages Setup Manager for status and control
4. **Agents** → Initialized and managed by Setup Manager
5. **CLI Tools** → Accessed through unified CLI Bridge

## Migration Path

**Before** (Direct Usage):
```python
from agents.daily_brief.daily_brief_agent import DailyBriefAgent
agent = DailyBriefAgent()
```

**After** (Setup Manager):
```python
from setup_manager import SetupManager
manager = SetupManager()
agent = manager.initialize_agent('daily_brief')
```

## Benefits

### For Users
- Simplified initialization
- Consistent configuration
- Better error handling
- Unified AI assistance

### For Developers
- Centralized dependency management
- Easier testing and mocking
- Clear separation of concerns
- Extensible architecture

## See Also

- [Refactoring Guide](docs/REFACTORING_GUIDE.md) - Complete architecture details
- [Examples](examples/) - Working code examples
- [Architecture](docs/ARCHITECTURE.md) - Full system design
