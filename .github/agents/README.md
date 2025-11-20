# GitHub Custom Agents

This directory contains GitHub Custom Agent definitions for the OsMEN project.

## Available Agents

### Day 1 Sprint Agents (6-Day Blitz to v2.0)

**Day 1 Orchestrator** (`day1-orchestrator.yml`)
- Coordinates all 5 Day 1 teams
- Manages dependencies and resolves blockers
- Tracks progress toward Day 1 deliverables
- Uses: `sprint/day1/orchestration/orchestration_agent.py`

**Team 1: Google OAuth** (`day1-team1-google-oauth.yml`)
- Implements universal OAuth handler framework
- Completes Google OAuth 2.0 integration
- Critical path: Unblocks Team 2
- TODO: `sprint/day1/team1_google_oauth/TODO.md`

**Team 2: Microsoft OAuth** (`day1-team2-microsoft-oauth.yml`)
- Implements Microsoft OAuth with Azure AD
- Builds on Team 1's OAuth base class
- Agent: `sprint/day1/team2_microsoft_oauth/team2_agent.py`
- TODO: `sprint/day1/team2_microsoft_oauth/TODO.md`

**Team 3: API Clients** (`day1-team3-api-clients.yml`)
- Auto-generates API clients for Calendar, Gmail, Contacts
- Uses openapi-generator
- Agent: `sprint/day1/team3_api_clients/team3_agent.py`
- TODO: `sprint/day1/team3_api_clients/TODO.md`

**Team 4: Testing** (`day1-team4-testing.yml`)
- Builds comprehensive test infrastructure
- Creates mock OAuth and API servers
- Targets 90%+ code coverage
- Agent: `sprint/day1/team4_testing/team4_agent.py`
- TODO: `sprint/day1/team4_testing/TODO.md`

**Team 5: Token Security** (`day1-team5-token-security.yml`)
- Implements token encryption and secure storage
- Automatic token refresh automation
- Security validation framework
- TODO: `sprint/day1/team5_token_security/TODO.md`

---

### OsMEN Coordinator (`osmen-coordinator.yml`)

The main coordinator agent that orchestrates the OsMEN multi-agent ecosystem. This agent:

- **Delegates tasks** to specialist agents (OS Sentry, Grad Navigator, Focus Steward, Content Forge, Research Scout)
- **Manages workflows** across the Langflow and n8n automation stack
- **Handles escalation** when human approval is required
- **Maintains context** using vector memory and session state
- **Ensures safety** with local-first operation and security controls

**Configuration:**
- Model: GPT-4
- Temperature: 0.3 (balanced for consistent coordination)
- Max Tokens: 4000
- Capabilities: Task delegation, workflow orchestration, decision making

### OsMEN Development Assistant (`my-agent.agent.md`)

An expert development assistant for the OsMEN project. This agent:

- **Provides development support** for code changes, architecture decisions, and testing
- **Enforces best practices** for the local-first, privacy-focused design
- **Guides implementation** of new agents, tools, and workflow automation
- **Ensures quality** through code reviews, security scans, and comprehensive testing
- **Maintains documentation** and tracks decisions using ADR format

**Configuration:**
- Model: GPT-4
- Temperature: 0.3 (balanced for consistent guidance)
- Max Tokens: 8000
- Capabilities: Code development, architecture design, testing validation, documentation, agent orchestration

## Using Custom Agents

GitHub Custom Agents defined in this directory can be invoked by GitHub Copilot and other GitHub AI features. The agent definitions follow the GitHub Custom Agent specification.

**Format Options:**
1. **YAML files** (`.yml` or `.yaml`): Pure YAML configuration
2. **Markdown files with YAML front matter** (`.md` or `.agent.md`): YAML configuration followed by markdown documentation

**Configuration Fields:**

- `name`: Human-readable agent name
- `description`: Brief overview of the agent's purpose
- `instructions`: Detailed system prompt and operational guidelines
- `model`: LLM model to use (e.g., gpt-4, gpt-3.5-turbo)
- `temperature`: Controls response randomness (0.0 = deterministic, 1.0 = creative)
- `max_tokens`: Maximum response length
- `capabilities`: List of agent capabilities
- `tools`: Available tool integrations
- `metadata`: Additional context and configuration

## Agent Architecture

The OsMEN Coordinator integrates with:

1. **Langflow** - Visual agent graph construction and LLM workflows
2. **n8n** - Event-driven automation and workflow execution
3. **Vector Database** - Long-term memory (Chroma/Qdrant)
4. **Tool Layer** - OS-native integrations (Simplewall, Sysinternals, FFmpeg, Pandoc)

## Specialist Agents

The coordinator delegates to these specialist agents:

| Agent | Mission | SLA |
|-------|---------|-----|
| OS Sentry | System hardening and monitoring | <30s boot policy |
| Grad Navigator | Academic task management | Digest by 09:05 |
| Focus Steward | Productivity and focus management | Instant app blocking |
| Content Forge | Content creation and editing | Draft in 2 minutes |
| Research Scout | Research and knowledge management | Per-document extraction |

## Security & Privacy

All agents operate with:
- **Local-first architecture** - Data stays on your machine
- **Human approval gates** - Sensitive actions require confirmation
- **Action logging** - Full audit trail with sensitive data redaction
- **Role-based access** - Prevent unauthorized operations
- **Fail-safe defaults** - Errors don't compromise security

## Development

To modify agents:

1. Edit the `.yml` or `.md` file in this directory
2. For YAML files: Validate syntax with `python3 -c "import yaml; yaml.safe_load(open('osmen-coordinator.yml'))"`
3. For Markdown files with front matter: Ensure YAML is between `---` delimiters at the start
4. Test with GitHub Copilot
5. Update version in metadata when making changes

## References

- [OsMEN Documentation](../../docs/)
- [Langflow](https://github.com/logspace-ai/langflow)
- [n8n](https://github.com/n8n-io/n8n)
- [GitHub Custom Agents Documentation](https://docs.github.com/en/copilot/customizing-copilot)
