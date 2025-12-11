# OsMEN Infrastructure Layer

This directory contains the workspace infrastructure management system - a comprehensive
framework for node registry, tool inventory, connection graphs, and dynamic context injection.

## Directory Structure

```
infrastructure/
├── nodes/           # Service registry with endpoints, schemas, health states
├── tools/           # Tool inventory with capability manifests
├── graph/           # Connection maps (agents↔tools↔nodes↔pipelines)
└── profiles/        # Workspace policies, permission rules, agent roles
```

## Core Components

### 1. Health Monitor Agent (`agents/health_monitor/`)

- Continuous MCP server and service monitoring
- Non-destructive auto-fixes (restart, cache clear, port rebind)
- Destructive fix protocols with checkpoint prompts

### 2. Infrastructure Agent (`agents/infrastructure/`)

- Node registry management
- Tool inventory with expectations verification
- Connection graph maintenance
- Dynamic context injection

### 3. Dynamic Context Injector

- Pre-hook: Queries graph + memory indices before agent execution
- Post-hook: Logs injections and captures outcomes
- Per-task tailoring to keep prompts lean

## Key Files

- `nodes/registry.json` - Service definitions and endpoints
- `tools/inventory.json` - Tool capabilities and health states
- `graph/connections.json` - Agent↔Tool↔Node relationships
- `profiles/policies.json` - Permission rules and workspace policies

## Related Directories

- `knowledge/` - Embeddings, memories, RAG (Obsidian-linked)
- `workspace/` - In-process items (incoming, staging, pending_review)
- `dashboards/` - Admin hub and per-agent dashboards
- `logs/` - Health reports and action logs
- `checkpoints/` - Rollback points for destructive fixes
