# Agent Orchestration Guide

## Overview

OsMEN v2.0 introduces **no-code agent team orchestration**, enabling you to build and deploy sophisticated AI agent teams without writing code. This guide explains how to orchestrate agents for maximum productivity.

## Architecture

### No-Code Orchestration Components

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  Langflow (Visual Flows) │ n8n (Workflows) │ Web Dashboard  │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Model Source Layer                        │
│   Codex CLI │ Copilot CLI │ GPT-4 │ Claude │ LM Studio      │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Agent Coordination Layer                    │
│              (Langflow Coordinator Agent)                    │
└─────────────────────────────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Personal         │  │ Content          │  │ Communication    │
│ Productivity     │  │ Creation         │  │ Team             │
│ Team             │  │ Team             │  │                  │
│                  │  │                  │  │                  │
│ • Personal       │  │ • Content        │  │ • Email Manager  │
│   Assistant      │  │   Creator        │  │ • Live Caption   │
│ • Focus          │  │ • Audiobook      │  │ • Contact Mgmt   │
│   Guardrails     │  │   Creator        │  │                  │
│ • Daily Brief    │  │ • Podcast        │  │                  │
│                  │  │   Creator        │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘

         ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Knowledge        │  │ System           │  │ Security         │
│ Team             │  │ Team             │  │ Team             │
│                  │  │                  │  │                  │
│ • Knowledge      │  │ • OS Optimizer   │  │ • Security Ops   │
│   Management     │  │ • Boot Hardening │  │ • Compliance     │
│ • Syllabus       │  │ • Performance    │  │ • Monitoring     │
│   Parser         │  │   Monitoring     │  │                  │
│ • Research       │  │                  │  │                  │
│   Intel          │  │                  │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

## Agent Teams

### 1. Personal Productivity Team

**Purpose**: Manage daily tasks, schedules, and productivity

**Agents**:
- **Personal Assistant**: Task management, reminders, calendar integration
- **Focus Guardrails**: Distraction blocking, Pomodoro sessions
- **Daily Brief**: Morning briefings, system status

**Example Workflow**:
```
Morning Routine:
1. Daily Brief generates morning summary
2. Personal Assistant reviews today's tasks
3. Focus Guardrails sets up first work session
4. Calendar events synced from Google/Outlook
```

**n8n Trigger**: Daily at 8:00 AM

### 2. Content Creation Team

**Purpose**: Generate and process multimedia content

**Agents**:
- **Content Creator**: Image generation, video processing
- **Audiobook Creator**: Convert ebooks with voice cloning
- **Podcast Creator**: Generate podcasts from knowledge base

**Example Workflow**:
```
Podcast Production:
1. User uploads notes to knowledge base
2. Podcast Creator generates episode script
3. Audiobook Creator narrates with cloned voice
4. Content Creator adds intro/outro music
5. Final podcast exported and published
```

**n8n Trigger**: Manual or scheduled weekly

### 3. Communication Team

**Purpose**: Handle email, contacts, and meeting transcription

**Agents**:
- **Email Manager**: Automated email workflows
- **Live Caption**: Real-time meeting transcription
- **Contact Management**: Unified contact database

**Example Workflow**:
```
Meeting Workflow:
1. Live Caption starts transcription when Zoom starts
2. Email Manager sends meeting notes to attendees
3. Contact Manager updates participant information
4. Transcript saved to knowledge base
```

**n8n Trigger**: Zoom webhook on meeting start

### 4. Knowledge Team

**Purpose**: Build and maintain knowledge bases

**Agents**:
- **Knowledge Management**: Obsidian/Notion integration
- **Syllabus Parser**: Extract events from syllabuses
- **Research Intel**: Information gathering

**Example Workflow**:
```
Semester Setup:
1. User uploads syllabus PDF
2. Syllabus Parser extracts assignments and exams
3. Knowledge Management creates course notes structure
4. Personal Assistant adds all to calendar
5. Research Intel gathers course materials
```

**n8n Trigger**: Manual syllabus upload

### 5. System Team

**Purpose**: Optimize and monitor system performance

**Agents**:
- **OS Optimizer**: Performance tuning, cleanup
- **Boot Hardening**: Security and integrity checks
- **Performance Monitor**: Resource tracking

**Example Workflow**:
```
Weekly Maintenance:
1. OS Optimizer analyzes system performance
2. Boot Hardening runs security checks
3. Cleanup tasks remove temporary files
4. Performance report generated
```

**n8n Trigger**: Weekly on Sunday at 2:00 AM

### 6. Security Team

**Purpose**: Monitor and maintain security posture

**Agents**:
- **Security Operations**: Vulnerability scanning
- **Compliance Monitor**: Policy enforcement
- **Threat Detection**: Anomaly detection

**Example Workflow**:
```
Security Audit:
1. Security Ops runs vulnerability scan
2. Compliance Monitor checks policies
3. Threat Detection analyzes logs
4. Security report with recommendations
```

**n8n Trigger**: Daily at midnight

## Using Codex CLI and Copilot CLI as Model Sources

### Codex CLI Integration

**Purpose**: Code generation and technical assistance

**Capabilities**:
- Generate code from natural language
- Complete partial code
- Explain complex code
- Review code for issues

**Example Usage in Agents**:
```python
from tools.codex_cli.codex_integration import CodexCLIIntegration

codex = CodexCLIIntegration()

# Generate code
code = codex.generate_code(
    "Create a function to parse CSV files",
    language="python"
)

# Review code
review = codex.review_code(my_code, "python")
```

**Use Cases**:
- OS Optimizer generating system scripts
- Security Ops creating security automation
- Content Creator building media processing pipelines

### Copilot CLI Integration

**Purpose**: Command-line and development assistance

**Capabilities**:
- Suggest shell commands
- Explain commands
- Git assistance
- Context-aware code suggestions

**Example Usage in Agents**:
```python
from tools.copilot_cli.copilot_integration import CopilotCLIIntegration

copilot = CopilotCLIIntegration()

# Get command suggestion
cmd = copilot.suggest_command(
    "find all large files over 100MB"
)

# Git help
git_cmd = copilot.suggest_git_command(
    "squash last 3 commits"
)
```

**Use Cases**:
- OS Optimizer suggesting optimization commands
- Boot Hardening creating security scripts
- System automation workflows

## Building Workflows in Langflow

### Step 1: Create a Flow

1. Open Langflow at http://localhost:7860
2. Click "New Flow"
3. Add nodes:
   - **Input Node**: Receives user request
   - **LLM Node**: Codex/Copilot/GPT-4
   - **Tool Nodes**: Agent capabilities
   - **Memory Node**: Qdrant for context
   - **Output Node**: Returns result

### Step 2: Configure Model Source

**For Codex CLI**:
```json
{
  "model_type": "codex_cli",
  "api_key": "${OPENAI_API_KEY}",
  "temperature": 0.7
}
```

**For Copilot CLI**:
```json
{
  "model_type": "copilot_cli",
  "github_token": "${GITHUB_TOKEN}",
  "context_aware": true
}
```

**For Cloud LLMs**:
```json
{
  "model_type": "openai",
  "model": "gpt-4",
  "api_key": "${OPENAI_API_KEY}"
}
```

### Step 3: Connect Agents

Link specialist agents to the coordinator:
- Coordinator receives request
- Routes to appropriate specialist
- Specialist executes using configured model
- Results aggregated and returned

## Building Workflows in n8n

### Step 1: Create Trigger

1. Open n8n at http://localhost:5678
2. Add trigger node:
   - **Cron**: Scheduled execution
   - **Webhook**: HTTP trigger
   - **File Watcher**: On file change

### Step 2: Add Agent Nodes

Add HTTP Request nodes to call agents:

```json
{
  "url": "http://localhost:8080/api/agents/personal_assistant/create_task",
  "method": "POST",
  "body": {
    "title": "{{ $json.task_title }}",
    "priority": "high"
  }
}
```

### Step 3: Configure Logic

- **IF nodes**: Conditional routing
- **Switch nodes**: Multi-way branching
- **Set nodes**: Data transformation
- **Function nodes**: Custom JavaScript

### Example: Syllabus to Calendar Workflow

```
┌─────────────┐
│   Trigger   │ (File uploaded)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Parser    │ (Syllabus Parser Agent)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Switch    │ (Route by event type)
└──────┬──────┘
       │
   ┌───┴───┬───────┬────────┐
   ▼       ▼       ▼        ▼
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│Exam │ │Assign│ │Lecture│ │Other│
└──┬──┘ └──┬──┘ └──┬───┘ └──┬──┘
   │       │       │        │
   └───────┴───────┴────────┘
                │
                ▼
      ┌─────────────────┐
      │ Personal        │
      │ Assistant       │ (Add to calendar)
      └─────────────────┘
                │
                ▼
      ┌─────────────────┐
      │ Knowledge       │
      │ Management      │ (Create notes)
      └─────────────────┘
```

## Best Practices

### 1. Agent Selection

- Use **Personal Assistant** for task/schedule management
- Use **Content Creator** for multimedia generation
- Use **Knowledge Management** for note organization
- Use **Security Ops** for security monitoring
- Use **OS Optimizer** for system maintenance

### 2. Model Source Selection

**Use Codex CLI when**:
- Generating code or scripts
- Need code review/explanation
- Building technical documentation

**Use Copilot CLI when**:
- Need command-line assistance
- Working with git operations
- Want context-aware suggestions

**Use Cloud LLMs when**:
- Need advanced reasoning
- Processing complex language tasks
- Require high-quality generation

**Use Local LLMs when**:
- Privacy is critical
- Offline operation needed
- Cost optimization important

### 3. Workflow Design

- Keep flows simple and focused
- Use error handling nodes
- Add logging for debugging
- Test with sample data first
- Monitor performance metrics

### 4. Security

- Never hardcode API keys in flows
- Use environment variables
- Limit agent permissions
- Audit agent actions
- Encrypt sensitive data

## Examples

### Example 1: Daily Productivity Flow

**Goal**: Start each day with tasks, calendar, and focus session

**Agents**: Daily Brief, Personal Assistant, Focus Guardrails

**Trigger**: Daily at 8:00 AM

**Workflow**:
1. Daily Brief generates morning summary
2. Personal Assistant fetches today's tasks
3. Focus Guardrails starts first 25-min session
4. Email sent with summary

### Example 2: Content Creation Pipeline

**Goal**: Create weekly podcast from notes

**Agents**: Knowledge Management, Podcast Creator, Audiobook Creator

**Trigger**: Weekly on Friday

**Workflow**:
1. Knowledge Management finds notes tagged "podcast"
2. Podcast Creator generates episode script
3. Audiobook Creator narrates with voice profile
4. Content Creator adds intro/outro
5. Upload to podcast hosting

### Example 3: Security Monitoring

**Goal**: Continuous security monitoring

**Agents**: Security Ops, Boot Hardening, Email Manager

**Trigger**: Hourly

**Workflow**:
1. Security Ops scans for vulnerabilities
2. Boot Hardening checks integrity
3. If critical issue found:
   - Email Manager sends alert
   - OS Optimizer applies fixes
   - Security log updated

## Troubleshooting

### Issue: Agent Not Responding

**Solution**:
1. Check agent logs: `docker logs osmen-[service]`
2. Verify API keys in `.env`
3. Test agent directly: `python agents/[agent]/[agent]_agent.py`
4. Check network connectivity

### Issue: Model Source Error

**Solution**:
1. Verify API credentials
2. Check rate limits
3. Test CLI integrations:
   ```bash
   python tools/codex_cli/codex_integration.py
   python tools/copilot_cli/copilot_integration.py
   ```

### Issue: Workflow Not Triggering

**Solution**:
1. Check n8n workflow status
2. Verify trigger configuration
3. Test webhook manually
4. Review n8n logs

## Next Steps

1. **Explore Agents**: Try each agent individually
2. **Build Simple Flow**: Create a basic Langflow flow
3. **Create Workflow**: Build an n8n automation
4. **Combine Agents**: Create multi-agent workflows
5. **Monitor Performance**: Track metrics and optimize

## Resources

- [Langflow Documentation](docs/LANGFLOW_GUIDE.md)
- [n8n Documentation](docs/N8N_GUIDE.md)
- [Agent API Reference](docs/API_REFERENCE.md)
- [Example Workflows](n8n/workflows/)
- [Example Flows](langflow/flows/)
