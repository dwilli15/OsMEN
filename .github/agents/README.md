# OsMEN GitHub Copilot Agents

This directory contains GitHub Copilot custom agent definitions for the OsMEN workspace.

## Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM-WIDE (VS Code)                     │
│  C:\Users\<user>\.vscode\agents\                            │
│  ├── yolo-ops.agent.md      # Generic YOLO for any project  │
│  └── blackhat-yolo.agent.md # Aggressive automation mode    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 WORKSPACE-WIDE (OsMEN)                       │
│  D:\OsMEN\.github\agents\                                   │
│  ├── yolo-ops.agent.md      # OsMEN-specific YOLO           │
│  ├── osmen-dev.agent.md     # Development assistant         │
│  ├── osmen-coordinator.yml  # Runtime task routing          │
│  └── manager.agent.md       # Project management            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BUILT-IN (Copilot)                        │
│  (Read-only, provided by VS Code extensions)                │
│  ├── Plan.agent.md          # Research & planning           │
│  └── AIAgentExpert.agent.md # AI/ML development             │
└─────────────────────────────────────────────────────────────┘
```

## Available Agents

### YOLO-OPS (OsMEN Workspace)
**File:** `yolo-ops.agent.md`

The master coordinator for OsMEN. Full access to all services:
- Langflow flows
- n8n workflows
- Docker services
- YOLO tools SDK
- All specialist agents

**Usage:** `@YOLO-OPS <task>`

### OsMEN Development Assistant
**File:** `osmen-dev.agent.md`

Development assistant for code changes:
- Agent development patterns
- Testing and quality
- Documentation
- Architecture guidance

**Usage:** `@OsMEN Development Assistant <question>`

### OsMEN Coordinator
**File:** `osmen-coordinator.yml`

Runtime task router for specialist agents:
- Boot Hardening
- Daily Brief
- Focus Guardrails
- Librarian

**Usage:** `@OsMEN Coordinator <request>`

### Manager
**File:** `manager.agent.md`

Project management and automation:
- Task coordination
- Progress tracking
- PR management
- Automation-first approach

**Usage:** `@manager <task>`

## System-Wide Agents

Located in `C:\Users\<user>\.vscode\agents\`:

### YOLO-OPS (System)
Generic autonomous agent for any project. Not OsMEN-specific.

### Blackhat-YOLO
Aggressive automation mode. Maximum autonomy, creative problem solving.

## Configuration

Agents are defined using:
- **Markdown files** (`.agent.md`): YAML front matter + markdown docs
- **YAML files** (`.yml`): Pure YAML configuration

### Required Fields

```yaml
---
name: Agent Name
description: Brief description
tools: "*"  # or list of specific tools
---
```

## Adding New Agents

1. Create file in `D:\OsMEN\.github\agents\`
2. Use `.agent.md` or `.yml` extension
3. Include required front matter
4. Test with `@<agent-name>` in Copilot Chat

## References

- [OsMEN Documentation](../../docs/)
- [GitHub Custom Agents](https://docs.github.com/en/copilot/customizing-copilot)
- [Langflow](https://github.com/logspace-ai/langflow)
- [n8n](https://github.com/n8n-io/n8n)
