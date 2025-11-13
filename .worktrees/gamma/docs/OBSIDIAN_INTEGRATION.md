# Obsidian Integration Guide

## Overview

OsMEN provides deep integration with Obsidian for knowledge management. This allows agents to capture, search, organize, and retrieve knowledge from your Obsidian vaults.

## Features

- **Note Management**: Create, read, update, and search notes
- **Graph Analysis**: Export and analyze your knowledge graph
- **Backlinks**: Find notes that reference other notes
- **Tags & Frontmatter**: Support for Obsidian metadata
- **Daily Notes**: Automatic daily note creation
- **MCP Integration**: Model Context Protocol for agent tool use

## Setup

### 1. Configure Obsidian Vault Path

Edit `.env`:
```bash
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
```

### 2. Start Services

```bash
docker-compose up -d
```

The MCP server will be available at: http://localhost:8081

### 3. Test Integration

```bash
python tools/obsidian/obsidian_integration.py
```

## Knowledge Management Agent

The Knowledge Management Specialist agent can:
- Create and organize notes
- Search your knowledge base
- Find connections between notes
- Generate knowledge summaries
- Create daily notes

### Usage via Langflow

1. Open Langflow: http://localhost:7860
2. Load flow: `knowledge_management_specialist.json`
3. Test with prompts like:
   - "Create a note about OsMEN architecture"
   - "Search for notes about agents"
   - "Show me related notes for X"

### Usage via n8n

The `knowledge_capture_trigger` workflow provides a webhook endpoint:

```bash
curl -X POST http://localhost:5678/webhook/capture-note \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Note",
    "content": "Note content here",
    "tags": ["tag1", "tag2"],
    "folder": "Notes"
  }'
```

### Usage via MCP API

Direct MCP tool calls:

```bash
# Create a note
curl -X POST http://localhost:8081/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "obsidian_create_note",
    "parameters": {
      "title": "Test Note",
      "content": "This is a test",
      "tags": ["test"]
    }
  }'

# Search notes
curl -X POST http://localhost:8081/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "obsidian_search",
    "parameters": {
      "query": "agent"
    }
  }'

# List all tools
curl http://localhost:8081/tools
```

## Python API

```python
from tools.obsidian.obsidian_integration import ObsidianIntegration

# Initialize
obsidian = ObsidianIntegration(vault_path="/path/to/vault")

# Create a note
result = obsidian.create_note(
    title="My Note",
    content="Note content",
    tags=["tag1", "tag2"],
    folder="Projects"
)

# Search notes
results = obsidian.search_notes("keyword")

# Read a note
note = obsidian.read_note("Projects/My Note.md")

# Get backlinks
backlinks = obsidian.get_backlinks("Projects/My Note.md")

# Export graph
graph = obsidian.export_graph()
```

## Available Tools (via MCP)

### Note Operations

**obsidian_create_note**
- Creates a new note in the vault
- Parameters: title, content, tags (optional), folder (optional)

**obsidian_read_note**
- Reads a note from the vault
- Parameters: note_path
- Returns: title, content, frontmatter, links, tags

**obsidian_update_note** (via Python API)
- Updates an existing note
- Parameters: note_path, content, append (optional)

### Search & Discovery

**obsidian_search**
- Searches notes by content
- Parameters: query, case_sensitive (optional)
- Returns: list of matching notes

**obsidian_list_notes**
- Lists all notes in vault or folder
- Parameters: folder (optional)
- Returns: list of notes with metadata

**get_backlinks** (via Python API)
- Finds notes that link to a given note
- Parameters: note_path
- Returns: list of backlinks

### Graph Operations

**export_graph** (via Python API)
- Exports the knowledge graph structure
- Returns: nodes (notes) and edges (links)

## Knowledge Agent Features

The Knowledge Management Agent provides high-level operations:

```python
from agents.knowledge_management.knowledge_agent import KnowledgeAgent

agent = KnowledgeAgent()

# Capture a note
agent.capture_note(
    title="Meeting Notes",
    content="Discussion points...",
    tags=["meetings", "2024"]
)

# Search knowledge
results = agent.search_knowledge("project planning")

# Find related notes
related = agent.find_related("Projects/OsMEN.md")

# Get knowledge graph
graph = agent.get_knowledge_graph()

# Create daily note
daily = agent.create_daily_note("Today's progress...")

# Analyze organization
analysis = agent.organize_notes()
```

## Integration with Other Agents

### Daily Brief Agent

The daily brief can include:
- Recent notes created
- Upcoming tasks from daily notes
- Knowledge base statistics

### Research Intelligence Agent

Can use Obsidian to:
- Store research findings
- Build knowledge graphs
- Track sources and citations

### Content Editing Agent

Can use Obsidian for:
- Draft storage
- Content versioning
- Project organization

## Best Practices

### Note Structure

Use consistent frontmatter:
```yaml
---
title: Note Title
date: 2024-01-01
tags: [tag1, tag2]
type: note-type
source: osmen
---
```

### Folder Organization

```
vault/
├── Daily Notes/
│   └── 2024-01-01.md
├── Projects/
│   └── OsMEN/
├── Research/
├── Meetings/
└── Archive/
```

### Linking Strategy

- Use wikilinks: `[[Note Title]]`
- Use aliases: `[[Note Title|Display Text]]`
- Add backlinks for context
- Tag generously for search

### Automated Workflows

1. **Daily Brief → Daily Note**: Automatically create daily note with brief
2. **Agent Conversations → Notes**: Save important conversations
3. **Research → Knowledge Base**: Auto-capture research findings
4. **System Status → Logs**: Create technical notes from system checks

## Troubleshooting

### Vault Not Found

Check `OBSIDIAN_VAULT_PATH` in `.env`:
```bash
echo $OBSIDIAN_VAULT_PATH
```

Ensure the path is absolute and accessible.

### Permission Issues

Ensure Docker has access to the vault directory:
```bash
chmod -R 755 /path/to/vault
```

### MCP Server Not Responding

Check MCP server logs:
```bash
docker-compose logs mcp-server
```

Restart if needed:
```bash
docker-compose restart mcp-server
```

## Advanced Usage

### Custom Tool Integration

Add your own tools to MCP server:

```python
# In gateway/mcp_server.py
tools['my_custom_tool'] = ToolDefinition(
    name='my_custom_tool',
    description='My custom tool description',
    parameters={...}
)
```

### Obsidian Plugins

OsMEN works with Obsidian plugins:
- **Dataview**: Query notes programmatically
- **Templater**: Use templates for notes
- **Obsidian Git**: Version control your vault
- **Local REST API**: Alternative API access

### Backup Strategy

Regular backups:
```bash
# Backup vault
tar czf obsidian-backup-$(date +%Y%m%d).tar.gz $OBSIDIAN_VAULT_PATH

# Restore vault
tar xzf obsidian-backup-20240101.tar.gz -C /path/to/restore
```

## Examples

### Example 1: Project Documentation

```python
agent = KnowledgeAgent()

# Create project note
agent.capture_note(
    title="OsMEN Project",
    content="""
## Overview
OsMEN is a local-first agent hub.

## Architecture
- Langflow for reasoning
- n8n for automation
- Obsidian for knowledge

## Status
Active development
    """,
    tags=["projects", "osmen"],
    folder="Projects"
)
```

### Example 2: Meeting Notes

```bash
curl -X POST http://localhost:5678/webhook/capture-note \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Meeting 2024-01-01",
    "content": "## Attendees\n- Alice\n- Bob\n\n## Topics\n- Project status\n- Next steps",
    "tags": ["meetings", "team"],
    "folder": "Meetings"
  }'
```

### Example 3: Research Notes

```python
integration = ObsidianIntegration()

# Create research note with citations
integration.create_note(
    title="LLM Agent Research",
    content="""
## Key Findings
- Agents benefit from tool use
- MCP provides standardization

## Sources
- [[Paper on Agent Systems]]
- [[MCP Specification]]
    """,
    tags=["research", "llm", "agents"],
    folder="Research",
    frontmatter={
        "date": "2024-01-01",
        "status": "in-progress"
    }
)
```

## Further Reading

- [Obsidian Help](https://help.obsidian.md/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [OsMEN Architecture](ARCHITECTURE.md)
- [Agent Usage Guide](USAGE.md)
