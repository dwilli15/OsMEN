# OsMEN Quick Start - Get Running in 10 Minutes

## Step 1: Clone (30 seconds)
```bash
git clone https://github.com/dwilli15/OsMEN.git
cd OsMEN
```

## Step 2: Configure (2 minutes)
```bash
cp .env.example .env
```

Edit `.env` and change these **REQUIRED** values:
```bash
# Security - CHANGE THESE!
N8N_BASIC_AUTH_PASSWORD=your-secure-password-here  # NOT 'changeme'
WEB_SECRET_KEY=your-random-32-char-secret-key-here

# LLM Provider - ADD AT LEAST ONE:
OPENAI_API_KEY=sk-your-key-here  # Easiest option
# OR use LM Studio or Ollama (see below)
```

## Step 3: Install Dependencies (1 minute)
```bash
python3 -m pip install --user -r requirements.txt
```

## Step 4: Start Services (3 minutes)
```bash
# Start core services (n8n, Langflow, databases)
docker compose up -d

# Start the web dashboard (Agent Hub)
python3 start_web.py

# OR include web in Docker (slower first time):
# docker compose up -d web

# Wait 2-3 minutes for first-time setup
```

## Step 5: Verify (1 minute)
```bash
# In another terminal
python3 check_operational.py
```

## Access Your System

- **Agent Hub** (Main Interface): http://localhost:8000 ⭐
- **Langflow** (Visual AI Builder): http://localhost:7860
- **n8n** (Automation): http://localhost:5678 (admin/[your password])
- **Qdrant** (Vector DB): http://localhost:6333/dashboard

## Test Your First Agent

```bash
# Run the Daily Brief agent
python3 agents/daily_brief/daily_brief_agent.py

# You should see: ✅ Daily Brief Agent: PASS
```

## 🎉 Success!

Your OsMEN system is running. Next steps:

1. **Open Agent Hub**: http://localhost:8000
2. **Create Agent Team**: Click "Create New Team" and describe what you need
3. **Explore**: Check out agents, workflows, and embedded tools
4. **Learn**: Check [1stsetup.md](1stsetup.md) for complete guide

## Troubleshooting

### Services Not Starting
```bash
# Check Docker is running
docker ps

# View logs
docker-compose logs -f

# Restart
docker-compose restart
```

### Port Already in Use
```bash
# Find what's using the port
lsof -i :5678  # Mac/Linux
netstat -ano | findstr :5678  # Windows

# Either kill that process or edit docker-compose.yml to use different ports
```

### Tests Failing
```bash
# Run detailed tests
python3 test_agents.py

# Check specific agent
python3 agents/boot_hardening/boot_hardening_agent.py
```

## Production Deployment

For production deployment, see:
- [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)
- Run `python3 scripts/automation/validate_security.py` first
- Change ALL default passwords
- Use HTTPS (see infra/nginx/)

## Need Help?

- Full setup guide: [1stsetup.md](1stsetup.md)
- Detailed docs: [docs/](docs/)
- Issues: https://github.com/dwilli15/OsMEN/issues
- Discussions: https://github.com/dwilli15/OsMEN/discussions
