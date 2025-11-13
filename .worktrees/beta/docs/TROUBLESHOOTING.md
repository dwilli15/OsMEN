# OsMEN Troubleshooting Guide

## Quick Diagnostics

### Run System Health Check
```bash
# Comprehensive operational check
python check_operational.py

# Security validation
python scripts/automation/validate_security.py

# Agent tests
python test_agents.py
```

## Common Issues

### 1. Docker Services Won't Start

#### Symptom
```
ERROR: Cannot connect to the Docker daemon
```

#### Solutions
```bash
# Check if Docker is running
docker info

# Start Docker service (Linux)
sudo systemctl start docker

# Start Docker Desktop (Windows/Mac)
# Launch Docker Desktop application

# Check Docker Compose version
docker compose version
```

#### Symptom
```
ERROR: Port already in use
```

#### Solutions
```bash
# Find what's using the port
netstat -ano | findstr :5678  # Windows
lsof -i :5678                 # Linux/Mac

# Stop conflicting service or change port in docker-compose.yml
```

### 2. Agent Tests Failing

#### Symptom
```
ImportError: No module named 'X'
```

#### Solutions
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify Python version
python --version  # Should be 3.12+

# Check virtual environment
which python  # Should point to venv if using one
```

#### Symptom
```
Agent test failed: Connection refused
```

#### Solutions
```bash
# Verify services are running
docker compose ps

# Check service logs
docker compose logs langflow
docker compose logs n8n

# Restart services
docker compose restart
```

### 3. LLM Connection Issues

#### OpenAI API Errors

**Symptom**: `Invalid API key` or `Unauthorized`
```bash
# Verify API key in .env
grep OPENAI_API_KEY .env

# Test API key manually
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**Symptom**: `Rate limit exceeded`
- Wait for rate limit to reset
- Upgrade OpenAI plan
- Switch to local LLM temporarily

#### LM Studio Connection Issues

**Symptom**: `Connection refused to localhost:1234`
```bash
# Verify LM Studio is running
curl http://localhost:1234/v1/models

# Check LM Studio settings:
# 1. Open LM Studio
# 2. Go to "Local Server" tab
# 3. Ensure server is started
# 4. Verify port is 1234
```

**Symptom**: `Model not loaded`
- Open LM Studio
- Go to "Local Server" tab
- Select and load a model
- Wait for model to finish loading

#### Ollama Connection Issues

**Symptom**: `Cannot connect to Ollama`
```bash
# Check if Ollama container is running
docker compose --profile ollama ps

# Start Ollama if not running
docker compose --profile ollama up -d

# Check Ollama logs
docker compose logs ollama

# Test Ollama API
curl http://localhost:11434/api/tags
```

**Symptom**: `Model not found`
```bash
# List available models
docker exec osmen-ollama ollama list

# Pull required model
docker exec osmen-ollama ollama pull llama2
docker exec osmen-ollama ollama pull mistral

# Or use make command
make pull-models
```

### 4. n8n Workflow Issues

#### Cannot Access n8n UI

**Symptom**: `Unable to connect to localhost:5678`
```bash
# Check if n8n is running
docker compose ps n8n

# Check n8n logs for errors
docker compose logs n8n

# Restart n8n
docker compose restart n8n
```

#### Login Issues

**Symptom**: `Invalid credentials`
```bash
# Check credentials in .env
grep N8N_BASIC_AUTH .env

# Default credentials (change these!):
# Username: admin
# Password: changeme

# Reset password by updating .env and restarting
docker compose restart n8n
```

#### Workflow Execution Fails

**Symptom**: Workflow shows error in execution history
1. Open n8n UI at http://localhost:5678
2. Go to "Executions" tab
3. Click on failed execution
4. Review error message and stack trace
5. Check "Input" and "Output" tabs for each node
6. Fix issue and re-execute

#### Webhook Not Triggering

**Symptom**: Manual trigger works, but webhook doesn't
```bash
# Test webhook manually
curl -X POST http://localhost:5678/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Check webhook URL in workflow
# Verify webhook is active (not in test mode)
# Check n8n logs for incoming requests
docker compose logs n8n | grep webhook
```

### 5. Langflow Issues

#### Cannot Access Langflow UI

**Symptom**: `Connection refused to localhost:7860`
```bash
# Check if Langflow is running
docker compose ps langflow

# Check Langflow logs
docker compose logs langflow

# Restart Langflow
docker compose restart langflow
```

#### Flow Import Fails

**Symptom**: Error when importing flow JSON
- Verify JSON file is valid: `cat flow.json | jq .`
- Check Langflow version compatibility
- Try importing a simple flow first
- Check Langflow logs for detailed error

#### Agent Not Responding

**Symptom**: Flow runs but produces no output
1. Open Langflow Playground
2. Test flow with sample input
3. Check each node's output
4. Verify LLM connection in flow
5. Check API keys/credentials in flow nodes

### 6. Firewall/Simplewall Issues

#### Cannot Control Firewall

**Symptom**: `Simplewall CLI not found`
```bash
# Verify Simplewall is installed
# Download from: https://www.henrypp.org/product/simplewall

# Check path in .env
grep SIMPLEWALL_PATH .env

# Test Simplewall CLI manually
"C:\Program Files\simplewall\simplewall.exe" --help
```

**Symptom**: `Access denied` or `Permission error`
- Run command prompt as Administrator
- Verify user has admin privileges
- Check Windows UAC settings
- Add exception in antivirus software

#### Rules Not Applying

**Symptom**: Firewall rules don't seem to work
1. Open Simplewall GUI
2. Verify rules are present
3. Check if Simplewall filtering is enabled
4. Review Simplewall logs
5. Restart Simplewall service

### 7. Database Issues

#### PostgreSQL Connection Errors

**Symptom**: `Could not connect to PostgreSQL`
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres

# Verify database credentials in .env
grep POSTGRES .env
```

#### Database Initialization Fails

**Symptom**: Services fail to start, database errors in logs
```bash
# Stop all services
docker compose down

# Remove database volumes (WARNING: This deletes all data)
docker volume rm osmen_postgres-data

# Restart services
docker compose up -d

# Check initialization
docker compose logs postgres
```

### 8. Vector Store (Qdrant) Issues

#### Cannot Connect to Qdrant

**Symptom**: `Connection refused to localhost:6333`
```bash
# Check if Qdrant is running
docker compose ps qdrant

# Check Qdrant logs
docker compose logs qdrant

# Restart Qdrant
docker compose restart qdrant

# Test Qdrant API
curl http://localhost:6333/dashboard
```

#### Collection Not Found

**Symptom**: Agent fails with "collection does not exist"
```bash
# Access Qdrant dashboard
open http://localhost:6333/dashboard

# Verify collection exists
# Create collection if needed through API or dashboard
```

### 9. Memory/Resource Issues

#### Out of Memory Errors

**Symptom**: Services crashing with OOM errors
```bash
# Check Docker memory allocation
docker stats

# Increase Docker memory limit:
# Docker Desktop → Settings → Resources → Memory
# Recommended: 16GB for full stack

# Stop unused services
docker compose stop ollama  # If using LM Studio instead
```

#### Disk Space Issues

**Symptom**: `No space left on device`
```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes

# Remove old logs
find logs/ -name "*.log" -mtime +30 -delete

# Check large files
du -sh * | sort -hr | head -10
```

### 10. Agent-Specific Issues

#### Boot Hardening Agent

**Issue**: Agent not triggering on boot
- Verify Task Scheduler is configured (Windows)
- Check webhook URL is correct
- Test manual trigger first
- Review n8n logs for incoming requests

**Issue**: Firewall rules not applying
- Verify Simplewall path in .env
- Check admin privileges
- Test Simplewall CLI manually
- Review boot_hardening logs

#### Daily Brief Agent

**Issue**: Brief not delivered
- Check cron schedule in n8n workflow
- Verify time zone settings
- Check email/notification credentials
- Review workflow execution history

**Issue**: Missing calendar events
- Verify calendar API credentials
- Check API rate limits
- Test calendar connection manually
- Review data collection logs

#### Focus Guardrails Agent

**Issue**: Window monitoring not working
- Verify PowerShell execution policy (Windows)
- Check AutoHotkey script is running
- Test window detection manually
- Review monitoring logs

**Issue**: Blocks not applying
- Verify Simplewall integration
- Check firewall profiles
- Test manual blocking
- Review decision logs

## Debugging Tools

### Enable Debug Logging
```bash
# In .env file
LOG_LEVEL=DEBUG

# Restart services
docker compose restart
```

### View Logs in Real-Time
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f langflow
docker compose logs -f n8n

# Agent logs
tail -f logs/boot_hardening.log
tail -f logs/daily_brief.log
tail -f logs/focus_guardrails.log
```

### Check Service Health
```bash
# Service status
docker compose ps

# Resource usage
docker stats

# Detailed inspect
docker inspect osmen-langflow
docker inspect osmen-n8n
```

### Network Debugging
```bash
# Check container network
docker network inspect osmen-network

# Test connectivity between containers
docker exec osmen-n8n ping qdrant
docker exec osmen-langflow ping postgres

# Check port bindings
docker compose ps --format json | jq '.[].Ports'
```

## Getting Help

### Before Asking for Help

Collect diagnostic information:
```bash
# Run all checks
python check_operational.py > diagnostics.txt
python scripts/automation/validate_security.py >> diagnostics.txt
python test_agents.py >> diagnostics.txt

# Collect logs
docker compose logs > docker_logs.txt

# System information
docker info > system_info.txt
docker compose config >> system_info.txt
```

### Where to Get Help
- 📚 [Documentation](../README.md)
- 🐛 [Report Issues](https://github.com/dwilli15/OsMEN/issues)
- 💬 [Discussions](https://github.com/dwilli15/OsMEN/discussions)

### When Reporting Issues

Include:
1. Output of `python check_operational.py`
2. Relevant error messages
3. Steps to reproduce
4. System specifications
5. Docker and Docker Compose versions
6. What you've already tried

### Emergency Recovery

If everything is broken:
```bash
# Nuclear option: Complete reset
docker compose down -v  # WARNING: Deletes all data
rm -rf logs/*
cp .env.example .env
# Edit .env with your settings
./start.sh

# Verify
python check_operational.py
```

## Performance Optimization

### Slow Startup
- Use SSD for Docker volumes
- Increase Docker memory allocation
- Pre-pull Docker images
- Use local LLM instead of API calls

### High Resource Usage
- Disable unused services
- Reduce logging verbosity
- Use smaller LLM models
- Limit concurrent workflows

### Network Latency
- Use local LLM providers
- Cache API responses
- Reduce polling frequency
- Optimize workflow design

---

**Still having issues?** Open an issue on GitHub with detailed information.
