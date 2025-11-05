# OsMEN - OS Management and Engagement Network

[![Operational Status](https://img.shields.io/badge/status-operational-brightgreen.svg)](check_operational.py)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

A local-first no/low-code agent hub combining Langflow reasoning graphs with n8n automation fabric, powered by local LLM via Ollama.

## 🎯 Overview

OsMEN provides a complete agent orchestration platform for:
- 🛡️ **Boot Hardening**: System security and boot integrity monitoring
- 📊 **Daily Briefing**: Comprehensive morning briefs with system status
- 🎯 **Focus Guardrails**: Productivity management and distraction blocking
- 📝 **Content Editing**: Media processing and content management (coming soon)
- 🔍 **Research Intelligence**: Information gathering and analysis (coming soon)

## 🏗️ Architecture

**Core Components:**
- **Langflow**: Visual reasoning graph builder with coordinator + specialist agents
- **n8n**: Workflow automation with triggers and subflows
- **LLM Agents**: Production agents (OpenAI, Copilot, Amazon Q, Claude) + Local (LM Studio, Ollama)
- **Qdrant**: Vector database for agent memory
- **Tool Layer**: Simplewall, Sysinternals, FFmpeg integrations

**Flexible deployment** - Use production cloud agents or run locally for privacy.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 16GB+ RAM recommended
- 50GB free disk space
- Optional: NVIDIA GPU for faster inference

### Installation

```bash
# Clone the repository
git clone https://github.com/dwilli15/OsMEN.git
cd OsMEN

# Configure environment
cp .env.example .env
# Edit .env with your preferences

# Start all services
docker-compose up -d

# Configure LLM agents (see docs/LLM_AGENTS.md)
# Option 1: Use production agents (OpenAI, Copilot, etc.)
# Option 2: Use LM Studio (download from lmstudio.ai)
# Option 3: Use Ollama (docker-compose --profile ollama up -d)

# Access the interfaces
# Langflow: http://localhost:7860
# n8n: http://localhost:5678 (admin/changeme)
# Agent Gateway: http://localhost:8080/docs
# Qdrant: http://localhost:6333/dashboard

# Check if everything is operational
python3 check_operational.py
# or
make check-operational
```

See [docs/SETUP.md](docs/SETUP.md) for detailed setup instructions.

### Verify Operational Status

To check if OsMEN is fully operational:

```bash
# Run comprehensive operational check
python3 check_operational.py

# Or use make command
make check-operational
```

This will verify:
- ✅ Docker daemon availability
- ✅ Docker Compose installation
- ✅ Python runtime
- ✅ All required files and directories
- ✅ Agent implementations
- ✅ Agent test suite
- ✅ Running Docker services

## 📖 Documentation

- **[Setup Guide](docs/SETUP.md)** - Installation and configuration
- **[LLM Agents](docs/LLM_AGENTS.md)** - Configure OpenAI, Copilot, Amazon Q, Claude, LM Studio, Ollama
- **[Obsidian Integration](docs/OBSIDIAN_INTEGRATION.md)** - Knowledge management with Obsidian
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Usage Guide](docs/USAGE.md)** - How to use OsMEN features

## 🔧 Key Features

### Model Context Protocol (MCP)
- **Standardized tool integration** for LLM agents
- **Tool discovery and execution** via REST API
- **Built-in tools**: Obsidian, Simplewall, Sysinternals, FFmpeg
- **MCP Server**: http://localhost:8081

### Obsidian Integration
- **Knowledge management** with full Obsidian vault access
- **Note operations**: Create, read, search, update
- **Graph analysis**: Export knowledge graph and find backlinks
- **Agent integration**: Knowledge Management Specialist
- **Automated workflows**: n8n webhook for note capture

## 🎯 MVP Features

### Knowledge Management Agent
- Create and organize notes in Obsidian
- Search and retrieve knowledge
- Find connections between notes
- Generate summaries and insights

### Boot Hardening Agent
- Automated daily security checks
- Boot integrity verification
- Startup program analysis
- Firewall configuration via Simplewall
- Integration with Sysinternals tools

```bash
python agents/boot_hardening/boot_hardening_agent.py
```

### Daily Brief Agent
- Morning briefings at 8 AM
- System health status
- Scheduled tasks overview
- Pending updates summary
- Resource usage trends

```bash
python agents/daily_brief/daily_brief_agent.py
```

### Focus Guardrails Agent
- Timed focus sessions (Pomodoro)
- Automatic distraction blocking
- Application usage monitoring
- Focus reminders and alerts

```bash
python agents/focus_guardrails/focus_guardrails_agent.py
```

## 🛠️ Tool Integrations

### Simplewall
- Firewall rule management
- Application/domain blocking
- Network traffic control

### Sysinternals Suite
- Autoruns - Startup analysis
- Process Monitor - Activity tracking
- TCPView - Network monitoring
- RootkitRevealer - Threat detection

### FFmpeg
- Video/audio processing
- Media format conversion
- Thumbnail generation
- Content optimization

## 📊 Project Status

**Current Version**: MVP (Minimum Viable Product)

**Operational Status**: ✅ [See detailed status](STATUS.md)

✅ **Completed:**
- Core infrastructure (Docker Compose)
- Langflow coordinator + specialist agents
- n8n automation workflows
- Ollama local LLM integration
- Qdrant vector memory storage
- Boot hardening agent
- Daily brief agent
- Focus guardrails agent
- Tool layer integrations
- Comprehensive documentation

🚧 **In Progress:**
- Content editing pipeline
- Research intelligence agent
- Web dashboard
- Additional specialist agents

📋 **Planned:**
- Grad planning assistant
- Project management agent
- Personal knowledge management
- Advanced analytics dashboard

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [Langflow](https://github.com/logspace-ai/langflow) - Visual LLM flow builder
- [n8n](https://github.com/n8n-io/n8n) - Workflow automation
- [OpenAI](https://openai.com/) - Production LLM (GPT-4, Codex)
- [GitHub Copilot](https://github.com/features/copilot) - AI pair programmer
- [Amazon Q](https://aws.amazon.com/q/) - AWS AI assistant
- [Anthropic Claude](https://www.anthropic.com/) - Advanced reasoning
- [LM Studio](https://lmstudio.ai/) - Local LLM runtime (primary local option)
- [Ollama](https://github.com/ollama/ollama) - Local LLM runtime (secondary local option)
- [Qdrant](https://github.com/qdrant/qdrant) - Vector database
- [Simplewall](https://www.henrypp.org/product/simplewall) - Firewall tool
- [Sysinternals](https://docs.microsoft.com/sysinternals) - System utilities
- [FFmpeg](https://ffmpeg.org/) - Media processing

## 📞 Support

- 📚 Check the [documentation](docs/)
- 🐛 [Report issues](https://github.com/dwilli15/OsMEN/issues)
- 💬 [Discussions](https://github.com/dwilli15/OsMEN/discussions)

---

**Local-first. Privacy-focused. Agent-powered.**
