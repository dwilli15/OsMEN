# Copilot Instructions for OsMEN

## Repository Overview

OsMEN (OS Management and Engagement Network) is a **production-ready** local-first no/low-code agent hub that combines Langflow reasoning graphs with n8n automation fabric, powered by local LLM via Ollama or cloud providers (OpenAI, GitHub Copilot, Amazon Q, Claude).

### Core Purpose

- Orchestrate AI agents for system management, security, productivity, and knowledge management
- Provide local-first, privacy-focused agent automation
- Enable visual flow building with Langflow and n8n workflow automation
- Integrate with tools like Simplewall, Sysinternals, FFmpeg, and Obsidian

### 🔗 Unified Orchestration Layer

**ALL components reference `integrations/orchestration.py` as the single source of truth.**

```python
from integrations.orchestration import OsMEN, Paths, Pipelines, get_pipeline

# Access any path
obsidian_root = Paths.HB411_OBSIDIAN

# Get any pipeline
briefing = get_pipeline("daily_briefing")

# Execute a pipeline
result = OsMEN.execute("daily_briefing")
```

**Key Integration Points:**

- **Paths**: All file paths defined in `Paths` class
- **Pipelines**: All workflows registered in `Pipelines` class
- **Services**: All services registered in `Services` class
- **Agents**: All agents registered in `Agents` class

### � Two-Way Connection Graph

The orchestration layer provides **bidirectional traversal** - navigate from ANY component to related resources:

```python
from integrations.orchestration import ConnectionGraph, Agents, Pipelines, Templates

# Agent → Resources
pipelines = Agents.get_pipelines("daily_brief")   # Get all pipelines for agent
workflows = Agents.get_workflows("daily_brief")   # Get all workflows for agent
templates = Agents.get_templates("daily_brief")   # Get all templates for agent

# Pipeline → Resources
agents = Pipelines.get_agents("daily_briefing")   # Get agents handling pipeline
workflows = Pipelines.get_workflows("daily_briefing")
templates = Pipelines.get_templates("daily_briefing")
trackers = Pipelines.get_trackers("adhd_tracking")

# Template → Resources
pipeline = Templates.get_pipeline("AM Check-In")  # Reverse lookup
agents = Templates.get_agents("AM Check-In")
path = Templates.get_full_path("AM Check-In")

# Full connection graph from any starting point
graph = ConnectionGraph.for_agent("daily_brief")
print(graph.pipelines)  # All pipelines
print(graph.workflows)  # All workflows
print(graph.templates)  # All templates
print(graph.trackers)   # Related trackers
print(graph.services)   # Required Docker services
```

### �📋 Daily Check-In System

Two mandatory check-ins per day:

- **AM Check-In**: Complete by 9 AM, triggers daily briefing generation
- **PM Check-In**: Complete by 10 PM, feeds next day's context

**CLI Commands:**

```bash
python cli_bridge/osmen_cli.py checkin am      # Start AM check-in
python cli_bridge/osmen_cli.py checkin pm      # Start PM check-in
python cli_bridge/osmen_cli.py briefing generate  # Generate briefing
python cli_bridge/osmen_cli.py status          # Show system status
```

**Logging:** All actions log to `logs/` via `integrations/logging_system.py`

### Technology Stack

- **Languages**: Python 3.12+, Bash, JSON/YAML
- **Infrastructure**: Docker & Docker Compose
- **Agent Frameworks**: Langflow (visual LLM flows), n8n (workflow automation)
- **LLM Providers**: OpenAI GPT-4, GitHub Copilot, Amazon Q, Claude, LM Studio, Ollama
- **Databases**: PostgreSQL (persistence), ChromaDB (long-term vector memory), SQLite (short-term), Redis (caching)
- **Memory System**: Hybrid Memory with Context7, Sequential Reasoning, and Lateral Bridges
- **APIs**: FastAPI for web services and MCP (Model Context Protocol) server
- **Testing**: pytest-style with custom test suite (`test_agents.py`)

## Project Structure

```
OsMEN/
├── agents/                    # Agent implementations (Python classes)
│   ├── boot_hardening/       # Security and boot integrity agent
│   ├── daily_brief/          # Daily briefing agent
│   ├── focus_guardrails/     # Productivity management agent
│   ├── knowledge_management/ # Obsidian integration agent
│   ├── content_editing/      # Media processing (future)
│   └── research_intel/       # Research agent (future)
├── langflow/                  # Langflow visual flows
│   ├── flows/                # Agent flow definitions (JSON)
│   └── config/               # Configuration files
├── n8n/                      # n8n automation workflows
│   └── workflows/            # Workflow definitions (JSON)
├── tools/                    # Tool integrations
│   ├── obsidian/            # Obsidian vault integration
│   ├── simplewall/          # Firewall management (Windows)
│   ├── sysinternals/        # System utilities integration
│   └── ffmpeg/              # Media processing
├── gateway/                  # API gateway and MCP server
│   ├── gateway.py           # Main API gateway (FastAPI)
│   └── mcp_server.py        # Model Context Protocol server
├── web/                      # Web dashboard (FastAPI)
├── docs/                     # Comprehensive documentation
├── scripts/automation/       # Automation scripts
├── docker-compose.yml        # Service orchestration
├── Makefile                  # Build and management commands
├── requirements.txt          # Python dependencies
└── test_agents.py           # Automated test suite
```

## Development Guidelines

### Code Style

**Python**

- Follow PEP 8 conventions
- Use type hints for function signatures
- Add docstrings to all classes and public methods
- Prefer descriptive variable names over abbreviations
- Use `pathlib.Path` for file operations, not `os.path`
- Import order: standard library → third-party → local modules

**Example:**

```python
from pathlib import Path
from typing import Dict, List, Optional

class MyAgent:
    """Brief description of the agent.

    Attributes:
        config: Configuration dictionary
        status: Current agent status
    """

    def __init__(self, config: Dict[str, str]) -> None:
        """Initialize the agent with configuration.

        Args:
            config: Configuration dictionary with required keys
        """
        self.config = config
        self.status = "initialized"

    def perform_task(self, input_data: str) -> Dict[str, any]:
        """Perform the main task of the agent.

        Args:
            input_data: Input data for processing

        Returns:
            Dictionary containing task results
        """
        # Implementation
        return {"status": "completed", "result": input_data}
```

**JSON Files**

- Use 2-space indentation for Langflow flows and n8n workflows
- Use 4-space indentation for configuration files
- Include descriptive names and descriptions in flow/workflow definitions

**Shell Scripts**

- Use `#!/bin/bash` shebang
- Add set -e for error handling when appropriate
- Comment complex logic and non-obvious commands
- Make scripts executable with `chmod +x`

### Testing Requirements

**Always Test Before Committing**

1. Run the test suite: `python3 test_agents.py`
2. Validate operational status: `python3 check_operational.py`
3. Run security checks: `make security-check` or `python3 scripts/automation/validate_security.py`

**Agent Testing**

- Each agent in `agents/` must have corresponding tests in `test_agents.py`
- Tests should validate:
  - Correct initialization
  - Required methods exist and return proper structure
  - Output format matches expected schema
  - Error handling for invalid inputs

**Tool Integration Testing**

- Tool integrations must be testable without the actual tool installed
- Use mock data or stub implementations for CI/CD
- Validate interface contracts (input/output formats)

### Build and Validation Commands

```bash
# Setup (first time only)
make setup                    # Create directories, copy .env

# Install Python dependencies
python3 -m pip install --user -r requirements.txt

# Start all services
make start                    # Start Docker Compose services
# or
./start.sh

# Testing and Validation
make test                     # Run agent tests
make check-operational        # Check system health
make security-check          # Security validation
make validate                # Run all checks (security + test + operational)

# Service Management
make status                   # Check service status
make logs                     # View all logs
make restart                 # Restart services
make stop                    # Stop all services

# Development
make pull-models             # Pull Ollama models (if using Ollama)
make backup                  # Backup configuration and data
```

### Docker Services

The application runs as a Docker Compose stack with these services:

- **langflow** (port 7860): Visual LLM flow builder
- **n8n** (port 5678): Workflow automation (credentials: admin/changeme)
- **ollama** (port 11434): Local LLM inference (optional)
- **chromadb** (port 8000): Vector database for long-term memory and RAG
- **postgres** (port 5432): Persistent storage
- **redis** (port 6379): Caching and session management
- **gateway** (port 8080): Agent Gateway API
- **mcp-server** (port 8081): Model Context Protocol server
- **convertx** (port 3000): Universal file converter (1000+ formats)

### Environment Configuration

The `.env` file (created from `.env.example`) contains:

- LLM provider API keys (OpenAI, Anthropic, etc.)
- Service credentials (n8n, PostgreSQL)
- Tool paths (Obsidian vault, Simplewall, Sysinternals)
- Feature flags and configuration

**Never commit the `.env` file or expose API keys in code.**

## Agent Development Best Practices

### Creating a New Agent

1. **Create Agent Directory and Implementation**

   ```bash
   mkdir -p agents/my_agent
   # Create my_agent.py with agent class
   ```

2. **Agent Class Structure**

   ```python
   class MyAgent:
       """Description of what this agent does."""

       def __init__(self):
           """Initialize with required configuration."""
           pass

       def perform_primary_function(self) -> Dict:
           """Main function that defines the agent's purpose.

           Returns:
               Dictionary with structured results including:
               - timestamp: ISO 8601 timestamp
               - status: Overall status string
               - results: Agent-specific results
           """
           return {
               "timestamp": datetime.now().isoformat(),
               "status": "completed",
               "results": {}
           }
   ```

3. **Create Langflow Flow**

   - Design the flow in Langflow UI (http://localhost:7860)
   - Export as JSON to `langflow/flows/my_agent_specialist.json`
   - Include coordinator integration for task routing

4. **Create n8n Workflow (if scheduled/triggered)**

   - Design workflow in n8n UI (http://localhost:5678)
   - Export as JSON to `n8n/workflows/my_agent_trigger.json`
   - Configure triggers (cron, webhook, etc.)

5. **Add Tests to test_agents.py**

   ```python
   def test_my_agent():
       """Test My Agent"""
       print("\n" + "="*50)
       print("Testing My Agent")
       print("="*50)

       try:
           from agents.my_agent.my_agent import MyAgent

           agent = MyAgent()
           result = agent.perform_primary_function()

           # Validate structure
           required_keys = ['timestamp', 'status', 'results']
           for key in required_keys:
               if key not in result:
                   raise ValueError(f"Missing required key: {key}")

           print("✅ My Agent: PASS")
           return True
       except Exception as e:
           print(f"❌ My Agent: FAIL - {e}")
           return False
   ```

6. **Update Documentation**
   - Add agent description to README.md
   - Document usage in docs/USAGE.md
   - Create runbook in docs/runbooks/ if needed

### Tool Integration Best Practices

When integrating new tools:

1. **Create Tool Directory**

   ```bash
   mkdir -p tools/my_tool
   ```

2. **Implement Integration Class**

   ```python
   class MyToolIntegration:
       """Integration with MyTool.

       Provides methods to interact with MyTool programmatically.
       """

       def __init__(self, tool_path: Optional[str] = None):
           """Initialize with optional tool path."""
           self.tool_path = tool_path or self._detect_tool_path()

       def _detect_tool_path(self) -> str:
           """Detect tool installation path."""
           # Platform-specific detection logic
           pass

       def execute_command(self, command: str) -> Dict:
           """Execute a tool command and return structured results."""
           pass
   ```

3. **Handle Platform Differences**

   - Check `platform.system()` for Windows/Linux/macOS
   - Provide fallback behavior when tool is not installed
   - Return structured error messages

4. **Register with MCP Server**
   - Add tool endpoints to `gateway/mcp_server.py`
   - Provide OpenAPI documentation
   - Follow MCP protocol standards

### ConvertX - Universal File Converter

ConvertX (port 3000) provides 1000+ format conversions via a unified API:

**Supported Converters:**

- FFmpeg: Video/audio (mp4, mkv, webm, mp3, wav, flac, etc.)
- Pandoc: Documents (pdf, docx, md, html, epub, txt, etc.)
- Vips/GraphicsMagick: Images (jpg, png, webp, heic, avif, gif, svg, etc.)
- Calibre: Ebooks (epub, mobi, azw3, fb2)
- Assimp: 3D models (obj, stl, fbx, gltf, glb)
- Inkscape: Vector graphics (svg → png/pdf)
- XeLaTeX: LaTeX → PDF

**Python Usage:**

```python
from integrations.convertx import convert_file, get_possible_conversions

# Simple conversion
result = convert_file("document.docx", "pdf")
if result.success:
    print(f"Saved to: {result.output_path}")

# Check available formats
formats = get_possible_conversions("mp4")  # ['webm', 'avi', 'mkv', 'mp3', ...]
```

**YOLO Tools Usage:**

```python
from integrations.yolo import get_tools_sync

tools = get_tools_sync()

# Convert single file
result = tools.convertx_convert("video.mp4", "webm")

# Batch convert
results = tools.convertx_batch(["file1.docx", "file2.docx"], "pdf")
```

**Environment Variables:**

- `CONVERTX_URL`: Service URL (default: http://localhost:3000)
- `CONVERTX_JWT_SECRET`: JWT secret for authenticated mode

## Security Considerations

### Required Security Practices

1. **API Keys and Secrets**

   - Store all secrets in `.env` file
   - Use environment variables in code: `os.getenv('API_KEY')`
   - Never hardcode credentials
   - Add `.env` to `.gitignore` (already configured)

2. **Input Validation**

   - Validate all user inputs and external data
   - Use type hints and runtime checks
   - Sanitize file paths to prevent traversal attacks
   - Validate JSON schemas for API inputs

3. **Docker Security**

   - Don't run containers as root when possible
   - Limit container capabilities
   - Use secrets management for sensitive data
   - Regularly update base images

4. **File Operations**

   - Validate file paths are within expected directories
   - Use `pathlib.Path.resolve()` to canonicalize paths
   - Check file permissions before operations
   - Handle file operation errors gracefully

5. **Network Operations**
   - Validate URLs before making requests
   - Set timeouts on HTTP requests
   - Handle SSL/TLS properly (don't disable verification)
   - Limit request sizes to prevent DoS

### Security Validation

Before committing code that handles:

- External inputs
- File operations
- Network requests
- Credentials or secrets

Run: `make security-check` or `python3 scripts/automation/validate_security.py`

## Common Patterns and Utilities

### Logging

Use `loguru` for logging (already in dependencies):

```python
from loguru import logger

logger.info("Agent started successfully")
logger.warning("Potential issue detected")
logger.error("Operation failed: {error}", error=str(e))
```

### Configuration Loading

```python
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment")
```

### Working with Hybrid Memory (ChromaDB + SQLite)

```python
from integrations.memory import HybridMemory, MemoryConfig
from integrations.memory.lateral_synchronicity import Context7

# Initialize hybrid memory
memory = HybridMemory(MemoryConfig.from_env())

# Store with Context7 enrichment
memory.remember(
    content="Memory content to store",
    source="agent",
    context7={
        "domain": "technical",
        "intent": "learning",
        "abstract": "metaphorical"
    }
)

# Recall with lateral thinking (searches both SQLite and ChromaDB)
results = memory.recall(
    query="search query",
    mode="lateral"  # foundation, lateral, or factcheck
)

# Recall with sequential reasoning trace
results, reasoning_steps = memory.recall_with_reasoning(
    query="complex query",
    n_results=5
)

# Run maintenance (promote stale memories, trim working memory)
memory.maintenance()
```

### Making API Requests

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def get_session_with_retries():
    """Create requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Use in code
session = get_session_with_retries()
response = session.get('http://api.example.com/endpoint', timeout=10)
response.raise_for_status()
data = response.json()
```

## Documentation Standards

### Code Comments

- Comment **why**, not **what** (the code shows what)
- Explain non-obvious algorithms or business logic
- Document assumptions and constraints
- Use TODO comments sparingly and link to issues when possible

### Docstrings

- Use Google-style docstrings
- Include Args, Returns, Raises sections
- Provide usage examples for complex functions

### README Updates

When adding major features:

1. Update main README.md with feature description
2. Add to "Key Features" or appropriate section
3. Update quick start guide if needed
4. Link to detailed documentation in docs/

### Creating Documentation

- Place detailed docs in `docs/` directory
- Use clear section headers
- Include code examples
- Add screenshots for UI features
- Keep docs updated with code changes

## Working with Langflow and n8n

### Langflow Flows

- Flows are JSON files in `langflow/flows/`
- Use descriptive names: `<agent_name>_specialist.json`
- Include nodes for: LLM, Memory, Tools, Output
- Connect to coordinator flow for routing
- Test flows in Langflow UI before exporting

### n8n Workflows

- Workflows are JSON files in `n8n/workflows/`
- Use descriptive names: `<agent_name>_trigger.json`
- Configure triggers: Cron, Webhook, Manual
- Use error handling nodes
- Test workflows in n8n UI before exporting

### Coordinator Pattern

- All specialist agents route through the Coordinator
- Coordinator determines which specialist to invoke
- Uses vector memory for context retrieval
- Maintains conversation state

## Git Workflow and Commit Messages

### Branch Naming

- `feature/<name>` - New features
- `fix/<name>` - Bug fixes
- `docs/<name>` - Documentation changes
- `refactor/<name>` - Code refactoring
- `test/<name>` - Test additions/improvements

### Commit Message Format

```
type: brief description

Longer explanation if needed. Explain what changed and why,
not how (the diff shows how).

- Additional context as bullets
- Link to issues: #123
```

**Types:**

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `style:` - Formatting, missing semicolons, etc.
- `refactor:` - Code restructuring, no behavior change
- `test:` - Adding or modifying tests
- `chore:` - Maintenance tasks, dependencies

### Before Committing

- [ ] Run `python3 test_agents.py` and ensure all tests pass
- [ ] Run `make security-check` for security-sensitive changes
- [ ] Update documentation if changing user-facing features
- [ ] Ensure `.env` and secrets are not committed
- [ ] Review `git diff` to verify only intended changes

## Troubleshooting Guide

### Common Issues

**Docker services won't start**

```bash
# Check Docker daemon
sudo systemctl status docker

# View logs
docker-compose logs <service-name>

# Restart Docker
sudo systemctl restart docker
docker-compose down && docker-compose up -d
```

**Python import errors**

```bash
# Reinstall dependencies
python3 -m pip install --user -r requirements.txt

# Verify Python version
python3 --version  # Should be 3.12+
```

**Port conflicts**

```bash
# Check what's using a port
sudo lsof -i :7860  # or other port

# Either stop the conflicting service or change ports in docker-compose.yml
```

**Agent tests failing**

```bash
# Run with verbose output
python3 test_agents.py 2>&1 | tee test_output.log

# Check agent files exist
ls -la agents/*/

# Verify Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

### Getting Help

1. Check documentation in `docs/`
2. Review existing agent implementations in `agents/`
3. Run `make help` for available commands
4. Check logs with `make logs`
5. Review test examples in `test_agents.py`

## Quick Reference Commands

```bash
# Development
make setup                    # Initial setup
make start                    # Start all services
make stop                     # Stop all services
make restart                  # Restart services
make logs                     # View logs
make status                   # Service status

# Testing & Validation
make test                     # Run tests
make check-operational        # Health check
make security-check          # Security validation
make validate                # All checks

# Maintenance
make backup                   # Backup data
make pull-models             # Pull Ollama models
make clean                   # Clean containers (careful!)

# Individual Tests
python3 test_agents.py                              # All agent tests
python3 agents/boot_hardening/boot_hardening_agent.py  # Specific agent
python3 check_operational.py                        # Operational check
```

## Production Deployment

Before deploying to production:

1. **Security Review**

   ```bash
   make security-check
   ```

2. **Change Default Credentials**

   - Update `N8N_BASIC_AUTH_PASSWORD` in `.env`
   - Update `POSTGRES_PASSWORD` in `.env`
   - Use strong, unique passwords

3. **Configure Backups**

   ```bash
   make backup  # Test backup process
   # Schedule regular backups with cron
   ```

4. **Review Firewall Rules**

   - Restrict access to internal services
   - Only expose necessary ports
   - Use HTTPS for external access

5. **Monitoring**

   - Set up logging aggregation
   - Configure alerting for failures
   - Monitor resource usage

6. **Documentation**
   - Review `docs/PRODUCTION_DEPLOYMENT.md`
   - Document environment-specific configuration
   - Create runbooks for common operations

## Additional Resources

- **Architecture**: `docs/ARCHITECTURE.md` - System design and components
- **Setup Guide**: `docs/SETUP.md` - Detailed installation instructions
- **Usage Guide**: `docs/USAGE.md` - How to use OsMEN features
- **LLM Configuration**: `docs/LLM_AGENTS.md` - Configure AI providers
- **Production Deployment**: `docs/PRODUCTION_DEPLOYMENT.md` - Production checklist
- **Troubleshooting**: `docs/TROUBLESHOOTING.md` - Common issues and solutions
- **Contributing**: `CONTRIBUTING.md` - Contribution guidelines
- **Runbooks**: `docs/runbooks/` - Operational procedures for each agent

## Contact and Support

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Check `docs/` directory for detailed guides
- **License**: Apache License 2.0 - See LICENSE file
