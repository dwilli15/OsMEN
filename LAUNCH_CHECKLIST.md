# OsMEN Launch Checklist

Use this checklist to verify your OsMEN installation is production-ready.

## ✅ Pre-Launch Validation

### System Requirements
- [ ] Docker & Docker Compose installed and running
- [ ] Python 3.12+ installed
- [ ] 16GB+ RAM available
- [ ] 50GB+ disk space free
- [ ] Internet connection for initial setup

### Environment Configuration
- [ ] `.env` file created from `.env.example`
- [ ] `N8N_BASIC_AUTH_PASSWORD` changed from default
- [ ] `WEB_SECRET_KEY` changed to secure value (32+ characters)
- [ ] At least one LLM provider configured:
  - [ ] `OPENAI_API_KEY` set (recommended)
  - [ ] OR LM Studio running and configured
  - [ ] OR Ollama configured to start with `--profile ollama`
- [ ] Tool paths configured (if using):
  - [ ] `OBSIDIAN_VAULT_PATH` if using Obsidian
  - [ ] `SIMPLEWALL_PATH` if on Windows
  - [ ] `SYSINTERNALS_PATH` if on Windows

### Dependencies Installed
```bash
python3 -m pip install --user -r requirements.txt
```
- [ ] All Python dependencies installed successfully
- [ ] No import errors when running `python3 check_operational.py`

### Services Running
```bash
docker-compose up -d
```
- [ ] PostgreSQL started (port 5432)
- [ ] Redis started (port 6379)
- [ ] Qdrant started (ports 6333-6334)
- [ ] n8n started (port 5678)
- [ ] Langflow started (port 7860)
- [ ] All services show "healthy" status in `docker-compose ps`

### Validation Passed
```bash
# Run comprehensive validation
make validate-production
# OR
python3 scripts/automation/validate_production_ready.py
```
- [ ] Production readiness validation passed
- [ ] All critical checks green
- [ ] Warnings reviewed and addressed

### Agent Tests Passing
```bash
python3 test_agents.py
```
- [ ] Boot Hardening Agent test: PASS
- [ ] Daily Brief Agent test: PASS
- [ ] Focus Guardrails Agent test: PASS
- [ ] All tool integrations: PASS
- [ ] Schedule optimizer: PASS
- [ ] Syllabus parser: PASS

### Security Validation
```bash
python3 scripts/automation/validate_security.py
```
- [ ] No critical security issues
- [ ] No default passwords in use
- [ ] No secrets in git history
- [ ] `.env` file in `.gitignore`
- [ ] File permissions secure

## 🚀 First Agent Launch

### Test Individual Agents
Run each agent manually to verify:

```bash
# Daily Brief Agent
python3 agents/daily_brief/daily_brief_agent.py
```
- [ ] Returns valid JSON output
- [ ] No errors in execution
- [ ] Output contains expected fields

```bash
# Boot Hardening Agent  
python3 agents/boot_hardening/boot_hardening_agent.py
```
- [ ] Security checks complete
- [ ] Issues identified (if any)
- [ ] Recommendations provided

```bash
# Focus Guardrails Agent
python3 agents/focus_guardrails/focus_guardrails_agent.py
```
- [ ] Session management works
- [ ] Site blocking functional
- [ ] Timer operates correctly

### Access Web Interfaces

#### n8n Workflow Automation
- [ ] Access http://localhost:5678
- [ ] Login successful with your credentials
- [ ] Dashboard loads correctly
- [ ] Can view/edit workflows

#### Langflow Visual Builder
- [ ] Access http://localhost:7860
- [ ] Interface loads
- [ ] Can create/edit flows
- [ ] Agent flows visible

#### Qdrant Vector Database
- [ ] Access http://localhost:6333/dashboard
- [ ] Dashboard loads
- [ ] Collections visible (if any exist)

### Configure First Workflow

In n8n (http://localhost:5678):
1. [ ] Import a workflow from `n8n/workflows/`
2. [ ] Configure credentials if needed
3. [ ] Test workflow execution
4. [ ] Activate workflow
5. [ ] Verify scheduled execution (wait for next trigger)

## 📊 Post-Launch Monitoring

### First 24 Hours

#### Check Logs
```bash
# View all logs
docker-compose logs -f

# Or individual services:
docker-compose logs langflow
docker-compose logs n8n
docker-compose logs postgres
```
- [ ] No critical errors in logs
- [ ] Services staying healthy
- [ ] No restart loops

#### Verify Workflows
- [ ] Daily Brief triggered as scheduled
- [ ] Security checks running
- [ ] No workflow execution failures in n8n

#### Resource Usage
```bash
docker stats
```
- [ ] Memory usage within expected range (<8GB for all services)
- [ ] CPU usage reasonable (<50% average)
- [ ] Disk space not rapidly depleting

### First Week

#### Backup Verification
```bash
make backup
```
- [ ] Backup script runs successfully
- [ ] Database backup created
- [ ] Configuration backed up
- [ ] Backup size reasonable

#### Performance Check
- [ ] Agent response times acceptable (<5s)
- [ ] Workflow execution times normal
- [ ] No database connection issues
- [ ] Vector search performing well

#### Integration Testing
- [ ] Calendar integration working (if configured)
- [ ] Obsidian integration functional (if configured)
- [ ] LLM provider responding correctly
- [ ] Tool integrations operational

## 🎯 Production Readiness Sign-Off

Before considering fully production-ready:

### Technical Sign-Off
- [ ] All validation checks passing
- [ ] All agents tested and working
- [ ] No critical errors in 24-hour run
- [ ] Backup and restore tested
- [ ] Resource usage sustainable

### Security Sign-Off  
- [ ] All default credentials changed
- [ ] Production secrets properly secured
- [ ] Security validation clean
- [ ] HTTPS configured (if exposing externally)
- [ ] Rate limiting in place (if exposing externally)

### Documentation Sign-Off
- [ ] Team members can follow setup guide
- [ ] Troubleshooting guide covers common issues
- [ ] Runbooks available for each agent
- [ ] Architecture documented
- [ ] Configuration documented

### Operational Sign-Off
- [ ] Monitoring in place
- [ ] Alert thresholds configured
- [ ] Backup schedule set
- [ ] Recovery procedures tested
- [ ] Escalation path defined

## 📝 Launch Notes

Date: _______________

Deployed by: _______________

### Configuration Summary
- LLM Provider: _______________
- Agents Enabled: _______________
- Integrations Active: _______________

### Known Issues
1. _______________
2. _______________
3. _______________

### Next Steps
1. _______________
2. _______________
3. _______________

## 🆘 Rollback Plan

If critical issues occur:

```bash
# Stop all services
docker-compose down

# Restore from backup (if needed)
# ... restore commands ...

# Start with known-good configuration
docker-compose up -d

# Verify services
python3 check_operational.py
```

## ✅ Final Approval

- [ ] **Technical Lead**: System meets technical requirements
- [ ] **Security Review**: Security validation passed
- [ ] **Operations**: Monitoring and backups configured
- [ ] **Product Owner**: System ready for users

---

**Status**: [ ] Ready to Launch  [ ] Needs Work  [ ] Blocked

**Launch Date**: _______________

**Signed**: _______________
