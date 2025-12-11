# OsMEN - OS Management and Engagement Network

[![Version](https://img.shields.io/badge/version-3.0%20(Implementation)-blue.svg)](docs/v3.0_IMPLEMENTATION_GUIDE.md)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![Tests Passing](https://img.shields.io/badge/tests-16%2F16%20passing-brightgreen.svg)](test_agents.py)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![6-Day Blitz](https://img.shields.io/badge/6--Day%20Blitz-Complete-success.svg)](sprint/6_DAY_BLITZ_COMPLETION_REPORT.md)

A **production-ready agent orchestration platform** combining Langflow reasoning graphs with n8n automation fabric, powered by local LLMs and cloud providers. **v3.0 implements all frameworks from v1/v2, making documented features actually work.**

> 🚀 **v3.0 Status**: Active implementation of v1/v2 frameworks. New unified integration layer connects OAuth, APIs, and agents. No-code OAuth setup CLI added. Google and Microsoft integrations now fully functional. See [v3.0 Implementation Guide](docs/v3.0_IMPLEMENTATION_GUIDE.md) for details.

## 🎯 Overview

OsMEN provides an **agent orchestration platform** with comprehensive frameworks and working implementations.

## 🚀 What's New in v3.0

### ✅ Implementation of v1/v2 Frameworks

- 🔗 **Unified Integration Layer**: Connects all framework components automatically
- 🎨 **No-Code OAuth Setup**: Interactive CLI for Google and Microsoft OAuth configuration
- 📅 **Working Calendar Integration**: Fully functional Google and Microsoft calendar APIs
- 📧 **Working Email Integration**: Gmail and Outlook Mail with send/receive capabilities
- 👥 **Contact Management**: Syncing and managing contacts across providers
- 🔐 **Token Management**: Automatic token refresh and secure storage
- 📊 **Health Monitoring**: Built-in diagnostics for all integrations
- 📚 **Comprehensive Documentation**: Complete v3.0 implementation guide

### ✅ New Features in v3.0

- **v3 Integration Layer** (`integrations/v3_integration_layer.py`): Unified interface for all external services
- **OAuth Setup CLI** (`scripts/setup_oauth.py`): No-code interactive configuration
- **OAuth Completion Tool** (`scripts/complete_oauth.py`): Streamlined authorization flow
- **Working Examples**: Real calendar event creation, email sending, contact management
- **Status Monitoring**: Check integration health with `--status` flag

See [v3.0 Implementation Guide](docs/v3.0_IMPLEMENTATION_GUIDE.md) for complete details.

## 🚀 What Was in v2.0

### ✅ Production Infrastructure Ready

- 🔐 **OAuth Automation Framework**: Universal OAuth handlers for Google, Microsoft (extensible to Zoom, Notion, Todoist)
- 🔧 **API Utilities**: Retry with exponential backoff, token bucket rate limiting, response normalization
- 🧪 **Testing Infrastructure**: Comprehensive unit/integration/end-to-end test framework (16 passing, capacity for 300+)
- ⚙️ **CI/CD Pipeline**: Automated testing on every push/PR with security validation
- 🛡️ **Production Hardening**: SSL automation, secrets management, monitoring (Prometheus/Grafana)
- 🌐 **Web Dashboard Framework**: React/Vue foundation with real-time updates
- 📚 **Comprehensive Documentation**: 6-day blitz completion report with detailed deliverables

### ✅ API Integration Frameworks

- 📅 **Google APIs**: Calendar, Gmail, Contacts (CRUD operations, multi-calendar support)
- 📧 **Microsoft APIs**: Outlook Calendar, Mail, Contacts (Azure AD integration)
- 📝 **Notion & Todoist**: API integration frameworks ready
- 🔄 **Multi-Provider Support**: Unified interface for all calendar/email/contact providers

### ✅ TTS & Audio Pipeline Frameworks

- 🎙️ **TTS Service**: Multi-provider framework (Coqui, ElevenLabs, Azure)
- 📖 **Audiobook Pipeline**: Ebook parsing, chapter detection, parallel TTS generation
- 🎧 **Podcast Pipeline**: Script generation, multi-voice support, RSS feeds
- 📹 **Zoom Integration**: OAuth framework, Whisper transcription ready

### ✅ Fully Working Now (v1.0 Core)

- 🛡️ **Boot Hardening**: System security and boot integrity monitoring (Windows)
- 📊 **Daily Briefing**: System status reports and task summaries
- 🎯 **Focus Guardrails**: Productivity timers and distraction blocking (Windows)
- 🤖 **Personal Assistant**: Task management and reminders
- 📝 **Knowledge Management**: Full Obsidian vault integration
- 🎨 **Content Processing**: Video/audio processing via FFmpeg
- 🔧 **Workflow Automation**: Visual builder (Langflow) and automation (n8n)
- 🔒 **Security Operations**: System scanning and monitoring

### 🏗️ Framework Ready (Needs Configuration)

- 📧 **Email & Calendar**: OAuth automation complete, needs provider credentials
- 📚 **Syllabus Parser**: Working, calendar sync ready with OAuth
- 📧 **Contact Management**: Full framework with sync capabilities
- 🎤 **Live Captioning**: Zoom OAuth ready, transcription framework complete
- 📖 **Audiobook Creator**: Complete pipeline, needs TTS service configuration
- 🎙️ **Podcast Creator**: Full workflow, needs TTS provider setup
- 💻 **OS Optimization**: Analysis working, cross-platform tuning framework ready

See [CHANGELOG_V2.md](CHANGELOG_V2.md) and [6-Day Blitz Report](sprint/6_DAY_BLITZ_COMPLETION_REPORT.md) for complete v2.0 details.

## 🧠 Librarian Integration

OsMEN now integrates with [osmen-librarian](https://github.com/dwilli15/osmen-librarian), providing:

- **Three-Mode RAG Retrieval**: Foundation (core concepts), Lateral (cross-disciplinary), Factcheck (verification)
- **LangGraph Orchestration**: StateGraph pattern with 15-field AgentState
- **Specialized Subagents**: FactChecker, LateralResearcher, Summarizer, Executor
- **OpenAI Assistants API**: Compatible interface for threads and runs

```bash
# Start OsMEN with Librarian
docker-compose --profile librarian up -d

# Query the knowledge base
curl -X POST http://localhost:8200/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is lateral thinking?", "mode": "lateral"}'
```

See [LIBRARIAN_INTEGRATION_PLAN.md](LIBRARIAN_INTEGRATION_PLAN.md) for details.

## 🏗️ Architecture

**Agent Orchestration Platform:**

- **Langflow**: Visual reasoning graph builder with coordinator + specialist agents
- **n8n**: Workflow automation with triggers and subflows
- **LLM Agents**: OpenAI GPT-4, Claude, LM Studio (local), Ollama (local)
- **Qdrant**: Vector database for agent memory
- **Librarian**: Semantic Memory & RAG engine with ChromaDB
- **PostgreSQL**: Persistent data storage
- **Redis**: Caching layer
- **Tool Layer**: Obsidian, FFmpeg, Simplewall, Sysinternals

**Planned Integrations** (frameworks in place):

- Codex CLI, Copilot CLI, Zoom API, Google Calendar/Gmail, Outlook, Notion, Audiblez, Vibeboice

**Agent Teams:**

1. **Personal Productivity**: Personal Assistant, Focus Guardrails, Daily Brief
2. **Content Processing**: Content Creator (basic), Audiobook Creator (planned), Podcast Creator (planned)
3. **Knowledge Management**: Obsidian integration, Syllabus Parser, Note organization, **Librarian RAG**
4. **System Operations**: OS Optimizer, Boot Hardening, Security Operations
5. **DRM Liberation** (BLACKHAT): ACSM fulfillment, Adobe ADEPT decryption, format conversion

**Flexible deployment** - Use cloud LLMs or run locally for privacy.

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

- **Langflow**: <http://localhost:7860>
- **n8n**: <http://localhost:5678> (admin/[your-password])
- **Qdrant**: <http://localhost:6333/dashboard>

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

### Understanding OsMEN

- **[Feature Status](FEATURE_STATUS.md)** - Complete feature capability matrix (✅ Working, ⚠️ Framework, ❌ Planned)
- **[Final Product Assessment](FINAL_PRODUCT_ASSESSMENT.md)** - Honest evaluation of current state
- **[Realistic Roadmap](REALISTIC_ROADMAP.md)** - 8-month plan to v2.0 completion

### Getting Started

- **[AI Agent Setup](1stsetup.md)** - Automated first-use setup instructions for AI agents
- **[Setup Guide](docs/SETUP.md)** - Installation and configuration
- **[LLM Agents](docs/LLM_AGENTS.md)** - Configure OpenAI, Claude, LM Studio, Ollama

### Operations

- **[Usage Guide](docs/USAGE.md)** - How to use OsMEN features
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Runbooks](docs/runbooks/)** - Operational runbooks for each workflow

### Technical

- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[OAuth Workflow](docs/OAUTH_WORKFLOW.md)** - Complete OAuth integration guide
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
- **MCP Server**: <http://localhost:8081>

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
- **Course Manager**: Import syllabi, sync to calendar, create course notes
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

### Course Manager

- Import course syllabi (PDF/DOCX) with automatic parsing
- Extract assignments, exams, deadlines, and schedules
- Sync events to Google/Outlook calendar
- Create structured notes in Obsidian vault
- Detect scheduling conflicts between courses
- Semester overview with upcoming events

```bash
python agents/knowledge_management/course_manager.py
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

**Current Version**: v1.0 (Foundation Complete)

**Realistic Status**: See [FEATURE_STATUS.md](FEATURE_STATUS.md) for complete details

### ✅ Production-Ready Core (100%)

- Core infrastructure (Docker Compose)
- PostgreSQL, Redis, Qdrant databases
- Langflow visual agent builder
- n8n workflow automation
- FastAPI gateway
- Agent testing framework (15/15 tests passing)
- Comprehensive documentation

### ✅ Fully Working Agents (8 agents)

- Boot Hardening Agent (Windows)
- Daily Brief Agent
- Focus Guardrails Agent (Windows)
- Personal Assistant Agent (basic features)
- Content Creator Agent (FFmpeg-based)
- Email Manager Agent (contact storage)
- OS Optimizer Agent (analysis)
- Security Operations Agent (scanning)

### ✅ Working Tool Integrations

- Obsidian (full vault access)
- FFmpeg (video/audio processing)
- Simplewall (Windows firewall)
- Sysinternals (Windows utilities)
- LLM providers (OpenAI, Claude, LM Studio, Ollama)

### ⚠️ Frameworks in Place (Needs Configuration/Development)

- Google Calendar/Gmail (OAuth needed)
- Microsoft Outlook/Calendar (OAuth needed)
- Notion API (completion needed)
- Todoist (completion needed)

### 🚧 In Active Development

- Live Caption Agent (Zoom API integration)
- Audiobook Creator Agent (TTS service needed)
- Podcast Creator Agent (TTS service needed)
- Codex CLI integration (CLI + API needed)
- Copilot CLI integration (CLI + token needed)
- Cross-platform support (Linux/macOS)
- Web dashboard enhancements
- Production hardening (SSL, monitoring, backups)

### 📋 Planned for v2.0 (6-8 months)

- Complete OAuth flows for Google/Microsoft
- TTS integration (Coqui, ElevenLabs, or Azure)
- Zoom API full integration
- Enhanced web dashboard
- Multi-user collaboration
- Advanced analytics
- Plugin marketplace
- Mobile companion app

**See [REALISTIC_ROADMAP.md](REALISTIC_ROADMAP.md) for detailed development timeline.**

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
