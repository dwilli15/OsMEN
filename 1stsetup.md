# OsMEN - First-Time Setup Guide for AI Agents

This guide helps AI agents (like GitHub Copilot, ChatGPT, Claude, etc.) assist users in setting up their first OsMEN agent team quickly and efficiently.

## 🎯 Goal
Get a user from zero to running their first AI agent team in **under 10 minutes**.

## 📋 Prerequisites Check

Before starting, verify the user has:
- [ ] **Docker Desktop** installed and running (Windows/Mac) OR Docker + Docker Compose (Linux)
- [ ] **16GB+ RAM** available
- [ ] **50GB+ free disk space**
- [ ] **Python 3.12+** installed (check with `python3 --version`)
- [ ] **Git** installed
- [ ] (Optional) **NVIDIA GPU** for faster local inference

## 🚀 Quick Setup (5 Steps)

### Step 1: Clone and Navigate (30 seconds)
```bash
git clone https://github.com/dwilli15/OsMEN.git
cd OsMEN
```

### Step 2: Configure Environment (2 minutes)
```bash
# Copy environment template
cp .env.example .env

# Edit .env file - CRITICAL CHANGES NEEDED:
# 1. Change N8N_BASIC_AUTH_PASSWORD from 'changeme' to something secure
# 2. Set WEB_ADMIN_PASSWORD_HASH (or use default for testing)
# 3. Configure at least ONE LLM provider:
#    Option A (Cloud - Recommended): Add your OPENAI_API_KEY
#    Option B (Local): Download LM Studio from https://lmstudio.ai
#    Option C (Local): Use Ollama (will auto-download models)
```

**Quick Edit Commands:**
```bash
# For macOS/Linux:
nano .env

# For Windows:
notepad .env

# Or use any text editor you prefer
```

**Minimum Required Changes in .env:**
```bash
# Security (REQUIRED - change these!)
N8N_BASIC_AUTH_PASSWORD=your-secure-password-here
WEB_SECRET_KEY=your-secret-key-here-min-32-chars

# LLM Provider (choose at least ONE):
# Option 1: OpenAI (easiest)
OPENAI_API_KEY=sk-your-key-here

# Option 2: Already have LM Studio running locally?
LM_STUDIO_URL=http://host.docker.internal:1234/v1

# Option 3: Use Ollama (will download models automatically)
# Just leave defaults - we'll start with --profile ollama
```

### Step 3: Install Python Dependencies (1 minute)
```bash
python3 -m pip install --user -r requirements.txt
```

### Step 4: Start Services (3 minutes)
```bash
# Standard start (with OpenAI or LM Studio):
docker-compose up -d

# OR with Ollama:
docker-compose --profile ollama up -d

# Wait for services to initialize (about 2 minutes)
# Check status with:
docker-compose ps
```

### Step 5: Verify Everything Works (1 minute)
```bash
# Run comprehensive check
python3 check_operational.py

# You should see:
# ✅ Docker Daemon
# ✅ Docker Compose  
# ✅ Python Runtime
# ✅ All files present
# ✅ Agent implementations found
# ✅ Tests passing
# ✅ Docker services running
```

## 🎉 Success! Access Your Agents

Your OsMEN system is now ready. Access the interfaces:

### Management Interfaces
- **n8n Workflow Automation**: http://localhost:5678
  - Username: `admin`
  - Password: `[what you set in .env]`
  
- **Langflow Visual Builder**: http://localhost:7860
  - No login required for local instance
  
- **Qdrant Vector Database**: http://localhost:6333/dashboard
  - No login required for local instance

### API Endpoints (if gateway built successfully)
- **Agent Gateway**: http://localhost:8080/docs
- **MCP Server**: http://localhost:8081/tools

## 🤖 Your First Agent Team

### Included Agent Specialists

OsMEN comes with three production-ready agents:

#### 1. **Boot Hardening Agent** 🛡️
Monitors system security and boot integrity
```bash
python3 agents/boot_hardening/boot_hardening_agent.py
```

**What it does:**
- Analyzes startup programs
- Checks boot integrity
- Monitors firewall configuration
- Detects security issues

#### 2. **Daily Brief Agent** 📊
Provides morning briefings with system status
```bash
python3 agents/daily_brief/daily_brief_agent.py
```

**What it does:**
- System health summary
- Pending tasks overview
- Resource usage trends
- Important notifications

#### 3. **Focus Guardrails Agent** 🎯
Manages productivity and blocks distractions
```bash
python3 agents/focus_guardrails/focus_guardrails_agent.py
```

**What it does:**
- Pomodoro timer sessions
- Website/app blocking during focus time
- Usage monitoring
- Break reminders

### Running Your First Agent

Let's test the Daily Brief Agent:

```bash
# Run the agent
python3 agents/daily_brief/daily_brief_agent.py

# You'll see output like:
# ✅ Daily Brief Agent: PASS
# Date: 2025-11-13
# Tasks: 2
# ... brief details ...
```

### Scheduling Agents with n8n

1. Open n8n: http://localhost:5678
2. Login with your credentials
3. Import the pre-configured workflows from `n8n/workflows/`
4. Activate the workflows you want

The agents will now run automatically on their schedules!

## 📚 Next Steps

### 1. Explore Documentation
- **Setup Guide**: `docs/SETUP.md` - Detailed installation
- **Usage Guide**: `docs/USAGE.md` - How to use features
- **LLM Agents**: `docs/LLM_AGENTS.md` - Configure AI providers
- **Architecture**: `docs/ARCHITECTURE.md` - System design

### 2. Customize Your Agents
- Edit agent configurations in `config/`
- Modify workflows in n8n interface
- Create custom Langflow flows

### 3. Add Integrations
- **Obsidian**: Connect your knowledge vault (`docs/OBSIDIAN_INTEGRATION.md`)
- **Calendar**: Google Calendar or Outlook integration
- **Task Managers**: Todoist, Notion integration

### 4. Advanced Setup
- **Production Deployment**: `docs/PRODUCTION_DEPLOYMENT.md`
- **Security Hardening**: `docs/SECRETS_MANAGEMENT.md`
- **Monitoring**: Set up logging and metrics

## 🛠️ Troubleshooting

### Services Not Starting

**Issue**: `docker-compose up -d` fails
```bash
# Check Docker is running
docker ps

# View detailed logs
docker-compose logs -f

# Common fix: Restart Docker
# Windows/Mac: Restart Docker Desktop
# Linux: sudo systemctl restart docker
```

### Port Already in Use

**Issue**: Error about port 5678, 7860, etc. already in use
```bash
# Find what's using the port (example for port 5678)
# Windows:
netstat -ano | findstr :5678

# Mac/Linux:
lsof -i :5678

# Kill the process or change ports in docker-compose.yml
```

### Tests Failing

**Issue**: `check_operational.py` shows failures
```bash
# Run detailed test suite
python3 test_agents.py

# Check specific agent
python3 agents/daily_brief/daily_brief_agent.py

# View logs
ls -la logs/
cat logs/osmen.log
```

### Can't Access Web Interfaces

**Issue**: http://localhost:5678 doesn't load
```bash
# Check if containers are actually running
docker-compose ps

# Look for STATUS = "Up" and "healthy"

# If not healthy, check logs:
docker-compose logs n8n
docker-compose logs langflow

# Wait longer - first start takes 2-3 minutes
```

### LLM Not Working

**Issue**: Agents can't connect to LLM
```bash
# Test LLM connectivity
python3 scripts/automation/test_llm_providers.py

# For OpenAI: Verify API key in .env
# For LM Studio: Ensure it's running on port 1234
# For Ollama: Check it started with --profile ollama
```

## 🆘 Getting Help

1. **Check Documentation**: `docs/TROUBLESHOOTING.md`
2. **View Runbooks**: `docs/runbooks/` for specific agent issues
3. **GitHub Issues**: https://github.com/dwilli15/OsMEN/issues
4. **Discussions**: https://github.com/dwilli15/OsMEN/discussions

## ✅ Production Readiness Checklist

Before deploying to production:

- [ ] Changed all default passwords in `.env`
- [ ] Generated secure `WEB_SECRET_KEY` (min 32 characters)
- [ ] Configured at least one production LLM provider
- [ ] Ran `python3 scripts/automation/validate_security.py`
- [ ] All tests passing: `python3 test_agents.py`
- [ ] Operational check green: `python3 check_operational.py`
- [ ] Reviewed `docs/PRODUCTION_DEPLOYMENT.md`
- [ ] Set up backups: `make backup` works
- [ ] Configured monitoring (optional but recommended)

## 🎓 For AI Agents Helping Users

When assisting users with OsMEN setup:

1. **Always start with prerequisites** - Check Docker, Python, disk space
2. **One step at a time** - Don't overwhelm with all options
3. **Recommend cloud LLM first** (OpenAI) - It's fastest to set up
4. **Show them the verification** - Run check_operational.py
5. **Start with one agent** - Daily Brief is the simplest
6. **Point to docs** - They have detailed guides
7. **Be patient** - First Docker pull takes time

### Quick Commands Reference

```bash
# Setup
cp .env.example .env && nano .env
pip install -r requirements.txt

# Start
docker-compose up -d

# Check
python3 check_operational.py
python3 test_agents.py

# Test agent
python3 agents/daily_brief/daily_brief_agent.py

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart
```

---

**Remember**: The goal is **10 minutes from clone to first agent running**. Keep it simple, verify each step, and celebrate the wins! 🎉
