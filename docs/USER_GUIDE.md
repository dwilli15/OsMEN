# OsMEN v3.0 User Guide

> Complete guide to using OsMEN - your local-first AI agent hub

## Table of Contents

1. [Getting Started](#getting-started)
2. [Daily Brief Workflow](#daily-brief-workflow)
3. [Research Workflow](#research-workflow)
4. [Content Workflow](#content-workflow)
5. [Web Dashboard](#web-dashboard)
6. [LLM Providers](#llm-providers)
7. [OAuth Connections](#oauth-connections)
8. [Workflow Customization](#workflow-customization)
9. [Approval System](#approval-system)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Quick Install

```bash
# Clone repository
git clone https://github.com/your-org/OsMEN.git
cd OsMEN

# Setup environment
cp .env.example .env

# Start services
make start
# or
docker-compose up -d
```

### Verify Installation

```bash
# Check health
curl http://localhost:8080/health
```

**Expected response:**

```json
{
  "status": "healthy",
  "version": "3.0.0"
}
```

### Choose Your LLM Provider

OsMEN supports three LLM providers:

1. **Ollama** (Local, Free) - Best for privacy
2. **OpenAI** (Cloud, Paid) - Best quality
3. **Anthropic** (Cloud, Paid) - Best reasoning

Set your provider in `.env`:

```env
# For local (Ollama)
DEFAULT_LLM_PROVIDER=ollama

# For OpenAI
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# For Anthropic
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Daily Brief Workflow

The Daily Brief workflow provides a personalized summary of your day including calendar events, emails, and tasks.

### Basic Usage

```bash
# Run with default settings (Ollama)
python workflows/daily_brief.py

# Run with OpenAI
python workflows/daily_brief.py --provider openai

# Run with Anthropic
python workflows/daily_brief.py --provider anthropic
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--provider` | LLM provider | `ollama` |
| `--no-calendar` | Skip calendar | Include |
| `--no-email` | Skip email | Include |
| `--no-tasks` | Skip tasks | Include |
| `--output` | Save to file | Console |
| `--format` | Output format | `markdown` |

### Example Output

```markdown
# Daily Brief - Thursday, November 28, 2024

## 📅 Today's Schedule

| Time | Event | Location |
|------|-------|----------|
| 09:00 | Morning Standup | Teams |
| 10:00 | Project Review | Conference Room A |
| 14:00 | Deep Work Block | - |
| 16:00 | 1:1 with Manager | Zoom |

## 📧 Email Summary

- **5** unread emails
- **2** requiring action
- **1** flagged as urgent

### Key Emails
1. **Project Update** from Alice - Review budget proposal
2. **Meeting Request** from Bob - Schedule demo

## ✅ Tasks Due Today

- [ ] Review PR #123 (High Priority)
- [ ] Submit expense report (Due 5pm)
- [ ] Prepare demo slides

## 💡 Recommendations

✨ Start with the PR review - it's blocking the team
⏰ Block 30 minutes for expense report before lunch
📋 Your 2pm deep work block is perfect for demo prep
```

### Save Daily Brief to File

```bash
# Save as markdown
python workflows/daily_brief.py --output daily_brief.md

# Save as HTML
python workflows/daily_brief.py --output daily_brief.html --format html
```

---

## Research Workflow

The Research workflow performs deep research on any topic using multiple sources.

### Basic Usage

```bash
# Quick research (2-3 minutes)
python workflows/research.py "AI Agent Frameworks" --depth quick

# Standard research (5-10 minutes)
python workflows/research.py "AI Agent Frameworks" --depth standard

# Deep research (15-30 minutes)
python workflows/research.py "AI Agent Frameworks" --depth deep
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--depth` | Research depth | `standard` |
| `--sources` | Source types | `web,papers,docs` |
| `--output` | Save to file | Console |
| `--format` | Output format | `markdown` |
| `--provider` | LLM provider | `ollama` |

### Source Types

| Source | Description |
|--------|-------------|
| `web` | General web search |
| `papers` | Academic papers |
| `docs` | Official documentation |
| `news` | Recent news articles |
| `code` | Code examples |
| `forums` | Community discussions |

### Example: Multi-Source Research

```bash
python workflows/research.py "Kubernetes security best practices" \
  --depth deep \
  --sources web,docs,forums \
  --output k8s_security.md
```

### Example Output

```markdown
# Research Report: AI Agent Frameworks

## Executive Summary

AI agent frameworks have evolved rapidly in 2024...

## Key Findings

### 1. Framework Comparison

| Framework | Strengths | Weaknesses |
|-----------|-----------|------------|
| LangChain | Ecosystem, tools | Complexity |
| AutoGPT | Autonomy | Resource usage |
| CrewAI | Multi-agent | Learning curve |

### 2. Architectural Patterns

- **ReAct**: Reasoning + Acting loop
- **Plan-Execute**: Upfront planning
- **Tool-Use**: Function calling

## Sources

1. [LangChain Documentation](https://docs.langchain.com)
2. [AI Agents Survey 2024](https://arxiv.org/...)
3. [OpenAI Function Calling Guide](https://platform.openai.com/...)

## Confidence Level

High (85%) - Based on 15 sources, 12 primary
```

---

## Content Workflow

The Content workflow generates various content types for marketing, social media, and communications.

### Basic Usage

```bash
# Generate blog post
python workflows/content.py "AI Productivity Tips" --type blog

# Generate Twitter thread
python workflows/content.py "AI Productivity Tips" --type twitter

# Generate LinkedIn post
python workflows/content.py "AI Productivity Tips" --type linkedin

# Generate newsletter
python workflows/content.py "AI Productivity Tips" --type newsletter
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--type` | Content type | `blog` |
| `--tone` | Writing tone | `professional` |
| `--length` | Content length | `medium` |
| `--output` | Save to file | Console |
| `--provider` | LLM provider | `ollama` |

### Content Types

| Type | Description | Length |
|------|-------------|--------|
| `blog` | Blog post with sections | 500-1500 words |
| `twitter` | Twitter/X thread | 3-10 tweets |
| `linkedin` | LinkedIn post | 150-300 words |
| `newsletter` | Email newsletter | 300-500 words |
| `product` | Product description | 100-200 words |

### Tone Options

- `professional` - Business-appropriate
- `casual` - Conversational
- `friendly` - Warm and approachable
- `formal` - Academic/official
- `humorous` - Light and fun
- `inspiring` - Motivational

### Example: Full Campaign

```bash
# Generate content for multiple platforms
python workflows/content.py "New Product Launch" \
  --type blog \
  --tone professional \
  --output blog.md

python workflows/content.py "New Product Launch" \
  --type twitter \
  --tone casual \
  --output tweets.md

python workflows/content.py "New Product Launch" \
  --type linkedin \
  --tone professional \
  --output linkedin.md
```

---

## Web Dashboard

OsMEN includes a web dashboard for monitoring and management.

### Access Dashboard

Open in browser: **http://localhost:8080/dashboard**

### Dashboard Pages

#### 1. Runs Dashboard

Monitor workflow executions in real-time:

- **Active Runs**: Currently executing workflows
- **Run History**: Past workflow executions
- **Statistics**: Success rates, durations
- **Logs**: Detailed execution logs

#### 2. Workflow Builder

Create and edit workflows visually:

- Drag-and-drop node editor
- 23+ node types available
- Save/load workflows
- Export/import JSON

#### 3. Settings

Configure OsMEN:

- LLM provider settings
- API key management
- OAuth connections
- Notification preferences

### Real-Time Monitoring

The dashboard uses Server-Sent Events (SSE) to show:

- Live workflow progress
- Step-by-step execution
- Tool calls and results
- Error notifications

---

## LLM Providers

### Ollama (Local)

**Pros**: Free, Private, No API keys
**Cons**: Requires local resources, Slower

**Setup:**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2

# Verify
ollama list
```

**Configuration:**

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### OpenAI

**Pros**: Best quality, Fast
**Cons**: Costs money, Data sent to cloud

**Setup:**

1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

### Anthropic

**Pros**: Best reasoning, Safe
**Cons**: Costs money, Data sent to cloud

**Setup:**

1. Get API key from https://console.anthropic.com/keys
2. Add to `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Provider Comparison

| Feature | Ollama | OpenAI | Anthropic |
|---------|--------|--------|-----------|
| Privacy | ✅ Local | ❌ Cloud | ❌ Cloud |
| Cost | Free | $$ | $$ |
| Quality | Good | Best | Very Good |
| Speed | Slower | Fast | Fast |
| Tool Calling | Basic | Excellent | Excellent |

---

## OAuth Connections

Connect your calendar and email for the Daily Brief workflow.

### Google Workspace

1. **Create OAuth Credentials**
   - Go to https://console.cloud.google.com
   - Create project → Enable Calendar & Gmail APIs
   - Create OAuth 2.0 credentials
   - Add redirect URI: `http://localhost:8080/oauth/callback/google`

2. **Configure OsMEN**

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

3. **Authorize**
   - Visit http://localhost:8080/oauth/authorize/google
   - Sign in with Google
   - Grant permissions

### Microsoft 365

1. **Register Application**
   - Go to https://portal.azure.com
   - Register new application
   - Add Graph API permissions (Calendar.Read, Mail.Read)
   - Create client secret

2. **Configure OsMEN**

```env
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_TENANT_ID=...
```

3. **Authorize**
   - Visit http://localhost:8080/oauth/authorize/microsoft
   - Sign in with Microsoft
   - Grant permissions

### Check Connection Status

```bash
# Via CLI
python scripts/check_oauth_status.py

# Via API
curl http://localhost:8080/api/v1/oauth/status
```

---

## Workflow Customization

### Create Custom Workflow

```python
# workflows/custom_workflow.py
from workflows.base import BaseWorkflow
from integrations.llm_providers import get_llm_provider

class CustomWorkflow(BaseWorkflow):
    """Custom workflow example"""
    
    def __init__(self, provider: str = "ollama"):
        super().__init__(name="custom_workflow")
        self.provider = provider
    
    async def run(self, input_data: dict) -> dict:
        llm = await get_llm_provider(self.provider)
        
        # Step 1: Process input
        self.emit_step("process_input", "Processing input data")
        processed = self.process(input_data)
        
        # Step 2: Generate with LLM
        self.emit_step("generate", "Generating response")
        response = await llm.chat([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": processed}
        ])
        
        # Step 3: Format output
        self.emit_step("format", "Formatting output")
        output = self.format(response)
        
        return {"result": output}
```

### Modify Existing Workflow

```python
# Extend Daily Brief with custom sources
from workflows.daily_brief import DailyBriefWorkflow

class ExtendedDailyBrief(DailyBriefWorkflow):
    """Extended daily brief with custom data"""
    
    async def collect_data(self) -> dict:
        data = await super().collect_data()
        
        # Add custom data source
        data["custom"] = await self.collect_custom_data()
        
        return data
    
    async def collect_custom_data(self) -> dict:
        # Your custom data collection
        return {"source": "custom", "data": [...]}
```

---

## Approval System

OsMEN includes human-in-the-loop approval for sensitive operations.

### How It Works

1. Workflow requests sensitive action (e.g., send email)
2. Request enters approval queue
3. User approves/denies via dashboard or API
4. Workflow continues or stops based on decision

### Default Approval Rules

| Action | Risk Level | Timeout |
|--------|------------|---------|
| Send external email | Medium | 5 min |
| Write file | High | 3 min |
| Execute shell command | Critical | 2 min |
| Create calendar event | Low | 1 min |
| Database write | High | 3 min |

### Approve via Dashboard

1. Go to http://localhost:8080/dashboard/approvals
2. Review pending requests
3. Click Approve or Deny
4. Add optional comment

### Approve via API

```bash
# List pending
curl http://localhost:8080/api/v1/approvals/pending

# Approve
curl -X POST http://localhost:8080/api/v1/approvals/{id}/approve \
  -H "Content-Type: application/json" \
  -d '{"comment": "Approved"}'

# Deny
curl -X POST http://localhost:8080/api/v1/approvals/{id}/deny \
  -H "Content-Type: application/json" \
  -d '{"reason": "Not authorized"}'
```

### Configure Approval Rules

```python
# In workflow
from workflows.approval import ApprovalMixin, ApprovalRule, RiskLevel

class MyWorkflow(ApprovalMixin):
    def __init__(self):
        self.add_approval_rule(ApprovalRule(
            pattern="send_email_external",
            risk_level=RiskLevel.HIGH,
            timeout_seconds=120,
            requires_comment=True
        ))
```

---

## Troubleshooting

### Workflow Not Starting

**Check services are running:**

```bash
docker-compose ps
```

**Check logs:**

```bash
docker-compose logs gateway
```

### LLM Provider Errors

**Ollama not responding:**

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

**OpenAI API errors:**

```bash
# Check API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### OAuth Connection Issues

**Token expired:**

```bash
# Re-authorize
python scripts/setup_oauth.py --provider google --refresh
```

**Permissions error:**

- Verify OAuth scopes in cloud console
- Re-authorize with correct permissions

### Performance Issues

**Slow workflows:**

- Use faster LLM provider (OpenAI vs Ollama)
- Reduce research depth
- Check system resources: `docker stats`

**High memory usage:**

```bash
# Restart services
docker-compose restart

# Check memory
docker stats --no-stream
```

### Getting Help

1. **Check logs**: `docker-compose logs -f`
2. **Health check**: `curl http://localhost:8080/health/deep`
3. **GitHub Issues**: https://github.com/your-org/OsMEN/issues
4. **Discord Community**: https://discord.gg/osmen

---

## Quick Reference

### Common Commands

```bash
# Start services
make start

# Stop services
make stop

# View logs
make logs

# Run daily brief
python workflows/daily_brief.py

# Run research
python workflows/research.py "topic"

# Run content generation
python workflows/content.py "topic" --type blog

# Check health
curl http://localhost:8080/health
```

### Default URLs

| Service | URL |
|---------|-----|
| Gateway API | http://localhost:8080 |
| Dashboard | http://localhost:8080/dashboard |
| Langflow | http://localhost:7860 |
| n8n | http://localhost:5678 |

### Environment Variables

```env
# LLM Provider
DEFAULT_LLM_PROVIDER=ollama
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

---

## Next Steps

1. **Run your first Daily Brief** - Get familiar with the output
2. **Connect OAuth** - Enable calendar and email integration
3. **Try Research workflow** - Explore deep research capabilities
4. **Generate content** - Create blog posts and social media
5. **Explore the Dashboard** - Monitor and customize workflows

Happy automating! 🚀
