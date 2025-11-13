# OsMEN Quick Reference Guide

## Daily Operations

### Starting OsMEN
```bash
# Start all services
make start
# or
docker compose up -d

# Start with Ollama (local LLM)
docker compose --profile ollama up -d
```

### Checking Status
```bash
# Quick status check
make status

# Comprehensive health check
make check-operational

# View logs
make logs

# Check specific service
docker compose logs -f langflow
docker compose logs -f n8n
```

### Stopping OsMEN
```bash
# Stop all services
make stop
# or
docker compose down

# Stop and remove volumes (caution: data loss)
docker compose down -v
```

## Validation Commands

### Security
```bash
# Run security validation
make security-check
# or
python scripts/automation/validate_security.py
```

### Testing
```bash
# Test all agents
make test
# or
python test_agents.py

# Test LLM providers
make test-llm
# or
python scripts/automation/test_llm_providers.py
```

### Full Validation
```bash
# Run all checks
make validate
```

## Service URLs

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| Langflow | http://localhost:7860 | - |
| n8n | http://localhost:5678 | admin / changeme |
| Agent Gateway | http://localhost:8080/docs | - |
| MCP Server | http://localhost:8081 | - |
| Qdrant | http://localhost:6333/dashboard | - |

## Common Tasks

### Update Configuration
```bash
# Edit environment
nano .env

# Restart affected services
make restart
```

### View Agent Logs
```bash
# Boot Hardening
tail -f logs/boot_hardening.log

# Daily Brief
tail -f logs/daily_brief.log

# Focus Guardrails
tail -f logs/focus_guardrails.log
```

### Manual Agent Execution

#### Trigger via n8n Webhook
```bash
# Boot Hardening
curl -X POST http://localhost:5678/webhook/boot-hardening

# Daily Brief
curl -X POST http://localhost:5678/webhook/daily-brief

# Focus Session Start
curl -X POST http://localhost:5678/webhook/focus-start \
  -H "Content-Type: application/json" \
  -d '{"duration": 25, "type": "pomodoro"}'
```

#### Direct Python Execution
```bash
# Boot Hardening
python agents/boot_hardening/boot_hardening_agent.py

# Daily Brief
python agents/daily_brief/daily_brief_agent.py

# Focus Guardrails
python agents/focus_guardrails/focus_guardrails_agent.py
```

## LLM Provider Configuration

### Check Provider Status
```bash
make test-llm
```

### OpenAI
```bash
# Test connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

### LM Studio (Local)
1. Download from https://lmstudio.ai
2. Load a model (e.g., Mistral 7B)
3. Start Local Server (default port: 1234)
4. Test: `curl http://localhost:1234/v1/models`

### Ollama (Local)
```bash
# Pull models
make pull-models
# or
docker exec osmen-ollama ollama pull llama2
docker exec osmen-ollama ollama pull mistral

# List models
docker exec osmen-ollama ollama list

# Test connection
curl http://localhost:11434/api/tags
```

## Backup & Restore

### Create Backup
```bash
make backup
# Creates backup in backups/ directory
```

### Manual Backup
```bash
# Backup workflows
tar czf backup.tar.gz n8n/workflows langflow/flows .env

# Backup database
docker exec osmen-postgres pg_dumpall -U postgres > backup.sql
```

### Restore from Backup
```bash
# Restore workflows
tar xzf backup.tar.gz

# Restore database
cat backup.sql | docker exec -i osmen-postgres psql -U postgres
```

## Troubleshooting Quick Fixes

### Service Won't Start
```bash
# Check Docker
docker info

# Check ports
docker compose ps
netstat -ano | findstr :5678  # Windows
lsof -i :5678                 # Linux/Mac

# Restart service
docker compose restart <service-name>
```

### Agent Not Responding
```bash
# Check service logs
docker compose logs langflow
docker compose logs n8n

# Restart agent services
docker compose restart langflow n8n
```

### Out of Memory
```bash
# Check resource usage
docker stats

# Stop unused services
docker compose stop ollama  # If using LM Studio instead

# Increase Docker memory (Docker Desktop → Settings → Resources)
```

### Clear Logs
```bash
# Remove old logs
find logs/ -name "*.log" -mtime +30 -delete

# Or move to archive
mkdir -p logs/archive
mv logs/*.log logs/archive/
```

## Maintenance Tasks

### Daily
- Check service status: `make status`
- Review execution logs in n8n
- Monitor resource usage: `docker stats`

### Weekly
- Review security audit logs
- Update firewall baseline if needed
- Check for software updates
- Test backup restoration

### Monthly
- Update Docker images: `docker compose pull && docker compose up -d`
- Rotate credentials if needed
- Review and clean old logs
- Audit agent performance

## Emergency Procedures

### Complete Reset
```bash
# CAUTION: This deletes all data
docker compose down -v
rm -rf logs/*
cp .env.example .env
# Edit .env with credentials
make start
```

### Disable Specific Agent
```bash
# Edit n8n workflow
# 1. Open n8n at http://localhost:5678
# 2. Find workflow
# 3. Toggle "Active" switch off
```

### Emergency Stop
```bash
# Stop all services immediately
docker compose kill
```

## Documentation Links

- **Setup**: [docs/SETUP.md](SETUP.md)
- **Architecture**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- **Usage**: [docs/USAGE.md](USAGE.md)
- **Production Deployment**: [docs/PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Runbooks**: [docs/runbooks/](runbooks/)

## Keyboard Shortcuts & Aliases

Add these to your `.bashrc` or `.zshrc`:

```bash
# OsMEN aliases
alias osmen-start='cd ~/OsMEN && make start'
alias osmen-stop='cd ~/OsMEN && make stop'
alias osmen-status='cd ~/OsMEN && make status'
alias osmen-logs='cd ~/OsMEN && make logs'
alias osmen-test='cd ~/OsMEN && make validate'
alias osmen-check='cd ~/OsMEN && make check-operational'
```

## Getting Help

- 📚 [Full Documentation](../README.md)
- 🐛 [Report Issue](https://github.com/dwilli15/OsMEN/issues)
- 💬 [Discussions](https://github.com/dwilli15/OsMEN/discussions)
- 🔍 [Troubleshooting Guide](TROUBLESHOOTING.md)

---

**Tip**: Pin this file for quick access to common commands!
