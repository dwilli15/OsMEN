# GitHub Custom Agents

This directory contains GitHub Custom Agent definitions for the OsMEN project.

## Available Agents

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

## Using Custom Agents

GitHub Custom Agents defined in this directory can be invoked by GitHub Copilot and other GitHub AI features. The agent definitions follow the GitHub Custom Agent specification with:

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

1. Edit the `.yml` file in this directory
2. Validate YAML syntax: `python3 -c "import yaml; yaml.safe_load(open('osmen-coordinator.yml'))"`
3. Test with GitHub Copilot
4. Update version in metadata when making changes

## References

- [OsMEN Documentation](../../docs/)
- [Langflow](https://github.com/logspace-ai/langflow)
- [n8n](https://github.com/n8n-io/n8n)
- [GitHub Custom Agents Documentation](https://docs.github.com/en/copilot/customizing-copilot)
