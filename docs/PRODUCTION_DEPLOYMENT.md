# OsMEN Production Deployment Guide

## Pre-Deployment Checklist

### 1. Security Validation ✅
- [ ] Run security validation: `python scripts/automation/validate_security.py`
- [ ] All critical issues resolved
- [ ] No default credentials in use
- [ ] `.env` file properly configured (not using example values)
- [ ] Secrets not committed to git
- [ ] `.gitignore` includes all sensitive patterns

### 2. Configuration ✅
- [ ] Copy `.env.example` to `.env`
- [ ] Copy `.env.production.example` to `.env.production` for production docker-compose usage
- [ ] Generate dashboard admin hash: `python scripts/security/hash_password.py > hash.txt` → set `WEB_ADMIN_PASSWORD_HASH`
- [ ] Update n8n password (change from 'changeme')
- [ ] Follow `docs/SECRETS_MANAGEMENT.md` for storing OAuth tokens/API keys
- [ ] Review `config/access_control.json` for role assignments (admin/operator/viewer)
- [ ] Configure LLM provider(s):
  - [ ] OpenAI API key (if using)
  - [ ] GitHub Copilot token (if using)
  - [ ] Amazon Q credentials (if using)
  - [ ] Anthropic Claude API key (if using)
  - [ ] LM Studio configured (if using local)
  - [ ] Ollama setup (if using local)
- [ ] Set correct tool paths:
  - [ ] Simplewall path
  - [ ] Sysinternals path
  - [ ] FFmpeg path
- [ ] Configure Obsidian vault path (if using)

### 3. Infrastructure Setup ✅
- [ ] Docker installed and running
- [ ] Docker Compose v2 available
- [ ] Python 3.12+ installed
- [ ] Minimum 16GB RAM available
- [ ] At least 50GB free disk space
- [ ] (Optional) NVIDIA GPU for faster local inference

### 4. Directory Structure ✅
- [ ] All required directories exist:
  - [ ] `agents/`
  - [ ] `tools/`
  - [ ] `gateway/`
  - [ ] `langflow/`
  - [ ] `n8n/`
  - [ ] `docs/`
  - [ ] `config/`
  - [ ] `scripts/automation/`
  - [ ] `content/inbox/`
  - [ ] `content/output/`
  - [ ] `logs/`

### 5. Configuration Files ✅
- [ ] `config/firewall_baseline.yaml` customized for environment
- [ ] `config/boot_hardening_settings.yaml` reviewed and adjusted
- [ ] Langflow flows exported and version-controlled
- [ ] n8n workflows exported and version-controlled

### 6. Testing ✅
- [ ] Run agent tests: `python test_agents.py`
- [ ] All tests passing
- [ ] Run operational check: `python check_operational.py`
- [ ] Manual smoke test of each agent:
  - [ ] Boot Hardening Agent
  - [ ] Daily Brief Agent
  - [ ] Focus Guardrails Agent

### 7. Monitoring & Logging ✅
- [ ] Log directory writable
- [ ] Log rotation configured (if needed)
- [ ] Audit trail enabled
- [ ] n8n execution history enabled

### 8. Backup Strategy ✅
- [ ] Workflow JSON files backed up
- [ ] Configuration files backed up
- [ ] Database backup plan established
- [ ] Vector store backup plan (if using)

### Access Control & Rate Limiting
- RBAC is enforced through `config/access_control.json` and the env vars `WEB_ADMIN_USERNAME`, `WEB_ADMIN_ROLE`, and `WEB_DEFAULT_ROLE`.
- FastAPI routes require CSRF tokens; templates expose `window.OSMEN_CSRF_TOKEN` and the dashboard JS injects it into HTMX/fetch requests automatically.
- Gateway endpoints are protected by a Redis-backed rate limiter (per-IP). Customize `RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_PREFIX`, and Redis credentials in `.env(.production)` as needed.
- Prometheus metrics are exposed at `/metrics` on both the dashboard (admin-only) and the gateway. Toggle via `PROMETHEUS_METRICS_ENABLED`.
- Run `scripts/backup/run_backup.py --label nightly` to archive Postgres dumps, Qdrant snapshots, and content exports into `BACKUP_DIR`.
- `.github/workflows/infra-ci.yml` enforces infra checks (lint + security) on every push to `agent-beta-infrastructure`.
- Prometheus metrics are exposed at `/metrics` on both the dashboard (admin-only) and the gateway. Toggle via `PROMETHEUS_METRICS_ENABLED`.
- Run `scripts/backup/run_backup.py --label nightly` to archive Postgres dumps, Qdrant snapshots, and content exports into `BACKUP_DIR`.

## Deployment Steps

### Step 1: Initial Setup
```bash
# Clone repository
git clone https://github.com/dwilli15/OsMEN.git
cd OsMEN

# Create environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

### Step 2: Security Validation
```bash
# Run security validation
python scripts/automation/validate_security.py

# Fix any critical issues before proceeding
```

### Step 3: Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python check_operational.py
```

### Step 4: Launch Production Stack (docker-compose.prod.yml)
```bash
# Create hardened production env file
cp .env.production.example .env.production

# Validate configuration without starting containers
docker compose -f docker-compose.prod.yml --env-file .env.production config

# Launch the production stack
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Tail logs if needed
docker compose -f docker-compose.prod.yml logs -f

# (Optional) Configure nginx TLS proxy
sudo cp infra/nginx/osmen.conf /etc/nginx/conf.d/
sudo systemctl reload nginx
```

See `infra/nginx/README.md` for certificate issuance + proxy details.  
> Health endpoints: `curl http://localhost:8443/healthz` (gateway) and `curl http://localhost:8000/ready` (dashboard).  
> Each service also exposes `GET /healthz/<service>` for granular probes (e.g., `/healthz/postgres`).

### Step 5: Database, Vector, and Cache Setup
```bash
# Apply Postgres migrations (creates schema_migrations table automatically)
python scripts/database/run_migrations.py

# Seed Qdrant collections
python scripts/qdrant/seed_collections.py --host http://localhost:6333

# Warm Redis cache (optional)
redis-cli -h redis ping
```

> The `postgres/init/02-osmen-schema.sql` file provisions the `osmen_app` database/user automatically when the container boots. Migrations can run repeatedly; they are idempotent.

### Step 6: Start Developer Services
```bash
# Start all services
./start.sh

# Or use make
make start

# If using Ollama (optional)
docker compose --profile ollama up -d

# Verify services are running
docker compose ps
```

### Step 7: Configure LLM Providers

#### Option 1: Production Cloud Providers
See [docs/LLM_AGENTS.md](LLM_AGENTS.md) for detailed setup instructions.

#### Option 2: Local LLM (LM Studio - Recommended)
1. Download and install LM Studio from https://lmstudio.ai
2. Download a model (recommended: Mistral 7B or Llama 2 13B)
3. Start the local API server in LM Studio
4. Update `.env`: `LM_STUDIO_URL=http://host.docker.internal:1234/v1`

#### Option 3: Local LLM (Ollama)
```bash
# Pull recommended models
docker exec osmen-ollama ollama pull llama2
docker exec osmen-ollama ollama pull mistral

# Or use make command
make pull-models
```

### Step 8: Access Interfaces
- **Langflow**: http://localhost:7860
- **n8n**: http://localhost:5678 (admin / your-password)
- **Agent Gateway**: http://localhost:8080/docs
- **MCP Server**: http://localhost:8081
- **Qdrant**: http://localhost:6333/dashboard

### Step 9: Import Workflows

#### Import Langflow Flows
1. Open Langflow at http://localhost:7860
2. Navigate to "Import" section
3. Import flows from `langflow/flows/`:
   - `coordinator.json`
   - `boot_hardening_specialist.json`
   - `daily_brief_specialist.json`
   - `focus_guardrails_specialist.json`

#### Import n8n Workflows
1. Open n8n at http://localhost:5678
2. Navigate to "Workflows" → "Import"
3. Import workflows from `n8n/workflows/`:
   - `boot_hardening_trigger.json`
   - `daily_brief_trigger.json`
   - `focus_guardrails_monitor.json`

### Step 9: Configure Windows Integration (Windows Only)

#### Simplewall Setup
1. Install Simplewall from https://www.henrypp.org/product/simplewall
2. Configure CLI access
3. Update path in `.env`

#### Sysinternals Setup
1. Download Sysinternals Suite
2. Extract to a permanent location
3. Update path in `.env`

#### Task Scheduler (Boot Hardening)
1. Open Task Scheduler
2. Create new task:
   - Trigger: On system startup
   - Action: Run webhook to n8n
   ```
   curl -X POST http://localhost:5678/webhook/boot-hardening
   ```

### Step 10: Verify Operation
```bash
# Run comprehensive check
python check_operational.py

# Include service health endpoints (recommended for production)
python check_operational.py --all --gateway-url http://localhost:8443 --dashboard-url http://localhost:8000

# Test agents manually
python test_agents.py

# Create an on-demand backup
python scripts/backup/run_backup.py --label manual

# Create an on-demand backup
python scripts/backup/run_backup.py --label manual

# Check service logs
docker compose logs -f

# Or use make command
make logs
```

### Step 11: Enable Monitoring
```bash
# View service status
make status

# Monitor logs in real-time
make logs

# Check resource usage
docker stats
```

## Post-Deployment

### Daily Operations
- Monitor execution logs in n8n
- Review agent decisions in Langflow
- Check system health: `make status`
- Review security audit logs

### Weekly Maintenance
- Review override requests (Focus Guardrails)
- Update firewall baseline if needed
- Check for software updates
- Backup workflows and configurations

### Monthly Tasks
- Update Docker images: `docker compose pull`
- Review and rotate credentials
- Audit agent performance
- Clean up old logs

## Troubleshooting

### Services Won't Start
```bash
# Check Docker status
docker info

# Check logs for specific service
docker compose logs <service-name>

# Restart services
make restart
```

### Agent Tests Failing
```bash
# Check Python dependencies
pip install -r requirements.txt

# Run tests with verbose output
python test_agents.py -v

# Check individual agent
python agents/boot_hardening/boot_hardening_agent.py
```

### LLM Connection Issues
```bash
# Test OpenAI connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Test LM Studio connection
curl http://localhost:1234/v1/models

# Test Ollama connection
curl http://localhost:11434/api/tags
```

### Firewall Control Issues
- Verify Simplewall is installed
- Check admin privileges
- Review Simplewall logs
- Test CLI manually: `simplewall.exe --help`

## Rollback Procedure

### If Deployment Fails
```bash
# Stop all services
docker compose down

# Restore from backup
# 1. Restore .env file
cp .env.backup .env

# 2. Restore configurations
cp -r config.backup/* config/

# 3. Restore workflows
cp -r n8n.backup/* n8n/
cp -r langflow.backup/* langflow/

# Restart services
./start.sh
```

### If Agent Misbehaves
1. Disable agent in n8n workflow (deactivate trigger)
2. Review execution history
3. Identify issue in Langflow graph
4. Fix and test in Langflow playground
5. Re-export and re-enable

## Security Considerations

### Production Hardening
1. Change all default passwords
2. Use strong, unique passwords
3. Enable HTTPS for external access
4. Configure firewall rules
5. Enable audit logging
6. Regular security scans

### Credential Management
- Store secrets in `.env` only
- Never commit `.env` to git
- Use environment-specific `.env` files
- Rotate credentials regularly
- Document credential locations

### Network Security
- Bind services to 127.0.0.1 (localhost) only
- Use VPN for remote access
- Enable firewall rules
- Monitor network traffic
- Block unnecessary ports

## Support

### Getting Help
- 📚 Check [Documentation](../README.md)
- 🐛 [Report Issues](https://github.com/dwilli15/OsMEN/issues)
- 💬 [Discussions](https://github.com/dwilli15/OsMEN/discussions)

### Diagnostic Information
When reporting issues, include:
- Output of `python check_operational.py`
- Output of `python scripts/automation/validate_security.py`
- Relevant logs from `docker compose logs`
- System specifications
- Configuration (without secrets)

## Success Criteria

Deployment is successful when:
- ✅ All services running and healthy
- ✅ Security validation passes
- ✅ All agent tests pass
- ✅ Workflows imported and active
- ✅ At least one LLM provider configured
- ✅ Tool integrations working
- ✅ No critical security issues
- ✅ Monitoring and logging operational

---

**Remember**: This is a local-first system. All data stays on your machine unless you explicitly configure cloud integrations.
