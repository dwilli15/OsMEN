# OsMEN - OS Management and Engagement Network

[![Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)](check_operational.py)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![Security Validated](https://img.shields.io/badge/security-validated-success.svg)](scripts/automation/validate_security.py)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

A **production-ready** local-first **no-code agent team orchestration** platform combining Langflow reasoning graphs with n8n automation fabric, powered by Codex CLI, Copilot CLI, local LLMs, and cloud providers.

## 🎯 Overview

OsMEN provides a complete **no-code agent team orchestration** platform for:
- 🤖 **Personal Assistant**: Task management, scheduling, reminders, and productivity
- 🎨 **Content Creation**: Image generation and video processing
- 📧 **Email & Contact Management**: Automated email workflows and contact sync
- 📚 **Syllabus to Calendar**: Build weekly todos and calendar items from syllabuses
- 🎤 **Live Captioning**: Real-time transcription for Zoom and meetings
- 📖 **Audiobook Creator**: Convert ebooks to audiobooks with voice cloning
- 🎙️ **Podcast Creator**: Generate podcasts from knowledge bases
- 🛡️ **Boot Hardening**: System security and boot integrity monitoring
- 📊 **Daily Briefing**: Comprehensive morning briefs with system status
- 🎯 **Focus Guardrails**: Productivity management and distraction blocking
- 💻 **OS Optimization**: System customization and performance tuning
- 🔒 **Security Operations**: White hat operations and security monitoring
- 📝 **Knowledge Management**: Obsidian, Notion, and multi-source knowledge bases

## 🏗️ Architecture

**No-Code Agent Team Orchestration:**
- **Codex CLI Integration**: OpenAI Codex as model source and agent
- **Copilot CLI Integration**: GitHub Copilot for code assistance and suggestions
- **Langflow**: Visual reasoning graph builder with coordinator + specialist agents
- **n8n**: Workflow automation with triggers and subflows
- **LLM Agents**: Production agents (OpenAI, Copilot, Amazon Q, Claude) + Local (LM Studio, Ollama)
- **Qdrant**: Vector database for agent memory
- **Tool Layer**: Codex CLI, Copilot CLI, Zoom, Audiblez, Vibevoice, Simplewall, Sysinternals, FFmpeg, Obsidian, Notion

**Agent Teams:**
1. **Personal Productivity Team**: Personal Assistant, Focus Guardrails, Daily Brief
2. **Content Creation Team**: Content Creator, Audiobook Creator, Podcast Creator
3. **Communication Team**: Email Manager, Live Caption, Contact Management
4. **Knowledge Team**: Knowledge Management, Syllabus Parser, Research Intel
5. **System Team**: OS Optimizer, Boot Hardening, Security Operations

**Flexible deployment** - Use production cloud agents or run locally for privacy.

## 🚀 Quick Start

### First-Time Setup (10 Minutes)

**🤖 AI Agents**: See **[1stsetup.md](1stsetup.md)** for automated setup guide.

**Prerequisites**:
- Docker & Docker Compose
- Python 3.12+
- 16GB+ RAM recommended
- 50GB free disk space
- Optional: NVIDIA GPU for faster inference

**Quick Installation**:

```bash
# 1. Clone the repository
git clone https://github.com/dwilli15/OsMEN.git
cd OsMEN

# 2. Configure environment (IMPORTANT: Change passwords!)
cp .env.example .env
nano .env  # or your preferred editor
# Required changes:
# - N8N_BASIC_AUTH_PASSWORD (change from 'changeme')
# - Add at least one LLM API key (OpenAI recommended)

# 3. Install dependencies
python3 -m pip install --user -r requirements.txt

# 4. Start all services
docker-compose up -d

# 5. Verify everything works
python3 check_operational.py
```

**Access Your Agent Hub**:
- **Langflow**: http://localhost:7860
- **n8n**: http://localhost:5678 (admin/[your-password])
- **Qdrant**: http://localhost:6333/dashboard

**Test Your First Agent**:
```bash
python3 agents/daily_brief/daily_brief_agent.py
```

See **[1stsetup.md](1stsetup.md)** for complete setup guide with troubleshooting.

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

### Production Readiness Validation

Before deploying to production, run complete validation:

```bash
# Run all validation checks
make validate

# Or run individually:
make security-check    # Security validation
make test              # Agent tests
make check-operational # System health check
```

See **[Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)** for complete checklist.

## 📖 Documentation

### Getting Started
- **[AI Agent Setup](1stsetup.md)** - Automated first-use setup instructions for AI agents
- **[Setup Guide](docs/SETUP.md)** - Installation and configuration
- **[Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)** - Complete production deployment checklist
- **[LLM Agents](docs/LLM_AGENTS.md)** - Configure OpenAI, Copilot, Amazon Q, Claude, LM Studio, Ollama

### Operations
- **[Usage Guide](docs/USAGE.md)** - How to use OsMEN features
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Runbooks](docs/runbooks/)** - Operational runbooks for each workflow

### Technical
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Obsidian Integration](docs/OBSIDIAN_INTEGRATION.md)** - Knowledge management with Obsidian

## 🔧 Key Features

### No-Code Agent Orchestration
- **Visual workflow builder** with Langflow for agent reasoning
- **Automated triggers** with n8n for scheduled and event-based execution
- **Agent teams** for collaborative task completion
- **Multi-model support** with Codex CLI, Copilot CLI, and cloud/local LLMs

### Model Context Protocol (MCP)
- **Standardized tool integration** for LLM agents
- **Tool discovery and execution** via REST API
- **Built-in tools**: Codex CLI, Copilot CLI, Obsidian, Simplewall, Sysinternals, FFmpeg, Zoom, Audiblez, Vibevoice
- **MCP Server**: http://localhost:8081

### Personal Assistant Capabilities
- Task management and prioritization
- Calendar integration (Google, Outlook)
- Reminder system with notifications
- Weekly schedule generation from syllabuses
- Contact and email management

### Content Creation Suite
- **Image Generation**: AI-powered image creation from text prompts
- **Video Processing**: FFmpeg integration for editing and conversion
- **Audiobook Creation**: Convert ebooks to audiobooks with Audiblez/Vibevoice
- **Voice Cloning**: Setup and manage voice profiles for narration
- **Podcast Generation**: Create podcasts from knowledge base content

### Communication & Collaboration
- **Live Captioning**: Real-time transcription for Zoom and meetings
- **Email Automation**: Smart rules and automated workflows
- **Contact Management**: Unified contact database with tagging

### Knowledge Management
- **Obsidian Integration**: Full vault access and note operations
- **Notion Integration**: Sync and manage Notion databases
- **Multi-source Knowledge Bases**: Build from syllabuses, interests, and more
- **Knowledge Graph**: Analyze connections and find insights
- **Automated workflows**: n8n webhook for note capture

### System Operations
- **OS Optimization**: Performance tuning and customization
- **Security Operations**: White hat monitoring and vulnerability assessment
- **Boot Hardening**: System security and integrity verification
- **Compliance Monitoring**: Automated security checks

## 🎯 Agent Capabilities

### Personal Assistant Agent
- Create and manage tasks with priorities
- Set reminders and notifications
- Schedule calendar events
- Generate daily summaries
- Integrate with Google/Outlook calendars

```bash
python agents/personal_assistant/personal_assistant_agent.py
```

### Content Creator Agent
- Generate images from text prompts
- Process and edit videos
- Convert media formats
- Create thumbnails
- Apply filters and effects

```bash
python agents/content_creator/content_creator_agent.py
```

### Email Manager Agent
- Manage contacts with tags
- Send automated emails
- Create email rules
- Search and filter contacts
- Batch operations

```bash
python agents/email_manager/email_manager_agent.py
```

### Live Caption Agent
- Real-time meeting transcription
- Multi-language support
- Speaker identification
- Transcript export
- Zoom integration

```bash
python agents/live_caption/live_caption_agent.py
```

### Audiobook Creator Agent
- Convert ebooks to audiobooks
- Voice cloning for narration
- Multi-format support (epub, pdf, txt)
- Chapter-based splitting
- Audiblez and Vibevoice integration

```bash
python agents/audiobook_creator/audiobook_creator_agent.py
```

### Podcast Creator Agent
- Generate podcasts from knowledge base
- Create podcast series
- Add intro/outro music
- Multi-voice narration
- Episode management

```bash
python agents/podcast_creator/podcast_creator_agent.py
```

### OS Optimizer Agent
- System performance analysis
- Apply optimizations
- Custom system configurations
- Cleanup and maintenance
- Performance monitoring

```bash
python agents/os_optimizer/os_optimizer_agent.py
```

### Security Operations Agent
- Security scanning
- Vulnerability assessment
- Event logging and monitoring
- Compliance checking
- Security posture reporting

```bash
python agents/security_ops/security_ops_agent.py
```

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

### Knowledge Management Agent
- Create and organize notes in Obsidian/Notion
- Search and retrieve knowledge
- Find connections between notes
- Generate summaries and insights
- Build knowledge bases from syllabuses

```bash
python agents/knowledge_management/knowledge_agent.py
```

## 🛠️ Tool Integrations

### Codex CLI
- Code generation from natural language
- Code completion and suggestions
- Code explanation and documentation
- Code review and quality checks

### Copilot CLI
- Command line assistance
- Shell command suggestions
- Git command help
- Code context suggestions

### Zoom
- Meeting transcription
- Live caption generation
- Recording processing
- Participant management

### Audiblez & Vibevoice
- Text-to-speech conversion
- Voice cloning
- Audiobook generation
- Multi-language support

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

### Obsidian & Notion
- Note creation and management
- Knowledge graph building
- Search and retrieval
- Automated organization

## 📊 Project Status

**Current Version**: v2.0 (No-Code Agent Team Orchestration)

**Operational Status**: ✅ [See detailed status](STATUS.md)

✅ **Completed:**
- Core infrastructure (Docker Compose)
- Langflow coordinator + specialist agents
- n8n automation workflows
- Codex CLI integration
- Copilot CLI integration
- Personal Assistant agent
- Content Creator agent
- Email Manager agent
- Live Caption agent
- Audiobook Creator agent
- Podcast Creator agent
- OS Optimizer agent
- Security Operations agent
- Boot Hardening agent
- Daily Brief agent
- Focus Guardrails agent
- Knowledge Management agent
- Ollama/LM Studio local LLM integration
- Qdrant vector memory storage
- Tool layer integrations (Codex, Copilot, Zoom, Audiblez, Vibevoice, Simplewall, Sysinternals, FFmpeg)
- Obsidian and Notion integration
- Comprehensive documentation
- Automated test suite

🚧 **In Progress:**
- Zoom API live integration
- Audiblez/Vibevoice full integration
- Enhanced voice cloning workflows
- Advanced podcast generation templates
- Web dashboard enhancements

📋 **Planned:**
- Mobile companion app
- Advanced analytics dashboard
- Multi-user collaboration
- Enterprise security features
- Plugin marketplace

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [Langflow](https://github.com/logspace-ai/langflow) - Visual LLM flow builder
- [n8n](https://github.com/n8n-io/n8n) - Workflow automation
- [OpenAI](https://openai.com/) - GPT-4, Codex CLI for code generation
- [GitHub Copilot](https://github.com/features/copilot) - Copilot CLI for development assistance
- [Amazon Q](https://aws.amazon.com/q/) - AWS AI assistant
- [Anthropic Claude](https://www.anthropic.com/) - Advanced reasoning
- [LM Studio](https://lmstudio.ai/) - Local LLM runtime (primary local option)
- [Ollama](https://github.com/ollama/ollama) - Local LLM runtime (secondary local option)
- [Qdrant](https://github.com/qdrant/qdrant) - Vector database
- [Zoom](https://zoom.us/) - Video conferencing and live transcription
- [Audiblez](https://github.com/audiblez) - Audiobook creation
- [Vibevoice Community](https://github.com/vibevoice-community) - Voice cloning
- [Obsidian](https://obsidian.md/) - Knowledge management
- [Notion](https://notion.so/) - Collaborative workspace
- [Simplewall](https://www.henrypp.org/product/simplewall) - Firewall tool
- [Sysinternals](https://docs.microsoft.com/sysinternals) - System utilities
- [FFmpeg](https://ffmpeg.org/) - Media processing

## 📞 Support

- 📚 Check the [documentation](docs/)
- 🐛 [Report issues](https://github.com/dwilli15/OsMEN/issues)
- 💬 [Discussions](https://github.com/dwilli15/OsMEN/discussions)

---

**Local-first. Privacy-focused. Agent-powered.**
