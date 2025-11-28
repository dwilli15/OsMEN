# OsMEN Quick Start Guide

Get your first Daily Brief in 5 minutes.

## Prerequisites

- Python 3.12+
- Docker (for services)
- One of:
  - Ollama (local, recommended)
  - OpenAI API key
  - Anthropic API key

## Step 1: Clone and Setup

```bash
git clone https://github.com/your-org/osmen.git
cd osmen
make setup
```

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Choose Your LLM Provider

### Option A: Local (Ollama) - Recommended

```bash
# Install Ollama (macOS)
brew install ollama

# Or Linux
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve

# Pull a model
ollama pull llama3.2
```

### Option B: OpenAI

```bash
# Add to .env
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### Option C: Anthropic

```bash
# Add to .env
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
```

## Step 4: Run Your First Daily Brief

```bash
# With local Ollama (default)
python workflows/daily_brief.py

# With OpenAI
python workflows/daily_brief.py --provider openai

# With Anthropic
python workflows/daily_brief.py --provider anthropic
```

**Expected Output:**
```
======================================================================
DAILY BRIEF WORKFLOW RESULT
======================================================================
Status: completed
Duration: 234.5ms

# Daily Brief - Thursday, November 28, 2024

## 📅 Today's Schedule

- **09:00** - Morning Standup
- **10:00** - Project Review
- **14:00** - Deep Work: Feature Development
- **16:30** - 1:1 with Manager

## 📧 Email Summary

- **5** unread emails
- **2** requiring action
- **1** high importance

### ⚡ Priority Emails

- **Q4 Planning - Action Required** from ceo@company.com

## ✅ Tasks

- **2** due today
- **1** high priority

### 🔴 Priority Tasks

- Review Q4 budget proposal

## 💡 Recommendations

- ✨ Start with your most important task
```

## Step 5: Connect Your Calendar (Optional)

### Google Calendar

```bash
# Interactive setup
python scripts/setup_oauth.py --provider google

# Follow the prompts to:
# 1. Create OAuth credentials at console.cloud.google.com
# 2. Enter Client ID and Secret
# 3. Select Calendar scope
# 4. Authorize in browser
```

### Microsoft/Outlook

```bash
# Interactive setup
python scripts/setup_oauth.py --provider microsoft
```

## Step 6: Start the Dashboard (Optional)

```bash
# Start services
make start

# Open dashboard
open http://localhost:8080/dashboard/agent_status.html
```

## Next Steps

- [Architecture Guide](docs/ARCHITECTURE.md) - For developers
- [Workflow Templates](docs/WORKFLOWS.md) - 100+ pre-built workflows
- [LLM Configuration](docs/LLM_AGENTS.md) - Fine-tune providers
- [OAuth Setup](OAUTH_QUICKSTART.md) - Connect all services

## Troubleshooting

### Ollama not responding

```bash
# Check if running
ollama list

# Restart
ollama serve
```

### Missing dependencies

```bash
pip install -r requirements.txt
```

### OAuth errors

```bash
# Reset tokens
rm -rf .copilot/tokens/*

# Re-setup
python scripts/setup_oauth.py --provider google
```

## Getting Help

- GitHub Issues: Report bugs
- Discussions: Ask questions
- Documentation: `/docs` directory
