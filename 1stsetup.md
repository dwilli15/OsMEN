# OsMEN - First Use Setup Instructions for AI Agents

**Version:** 1.0  
**Last Updated:** 2025-11-08  
**Purpose:** Automated first-time setup and configuration of OsMEN repository

---

## 🎯 Overview

This document provides comprehensive instructions for an AI agent to:
1. **Scan** all files and directories in the repository
2. **Establish** to-dos based on repository state
3. **Setup** the repository automatically on the user's behalf
4. **Validate** successful installation and readiness

## 📋 Pre-Flight Checks

Before beginning setup, verify these prerequisites:

### System Requirements
```bash
# Check Docker installation
docker --version
# Expected: Docker version 20.10+ or higher

# Check Docker Compose
docker compose version
# Expected: Docker Compose version 2.0+ or higher

# Check Python installation
python3 --version
# Expected: Python 3.12+ or higher

# Check available disk space (minimum 50GB required)
df -h .
# Expected: At least 50GB available

# Check available RAM (minimum 16GB recommended)
free -h
# Expected: 16GB+ total memory
```

### Network Requirements
```bash
# Verify internet connectivity for pulling Docker images
ping -c 3 google.com
# Expected: Successful ping responses

# Check Docker daemon status
docker info
# Expected: Docker daemon running without errors
```

## 🔍 Repository Scan Procedure

### Step 1: Scan Repository Structure

Execute a comprehensive scan to understand the repository layout:

```bash
# From repository root
cd /path/to/OsMEN

# List all directories
find . -type d -not -path '*/\.git/*' | sort

# List all Python files
find . -name "*.py" -not -path '*/\.git/*' | sort

# List all configuration files
find . -name "*.yml" -o -name "*.yaml" -o -name "*.json" -o -name "*.env*" | sort

# List all documentation
find . -name "*.md" | sort

# List all shell scripts
find . -name "*.sh" | sort
```

### Step 2: Inventory Key Components

Scan and document the following components:

#### Core Infrastructure Files
- [ ] `docker-compose.yml` - Service orchestration
- [ ] `.env.example` - Environment configuration template
- [ ] `Makefile` - Build and management commands
- [ ] `start.sh` - Automated startup script
- [ ] `requirements.txt` - Python dependencies

#### Agent Implementations
```bash
# List all agent directories
ls -la agents/

# Expected agents:
# - boot_hardening/
# - daily_brief/
# - focus_guardrails/
# - knowledge_management/
# - content_editing/
# - research_intel/
```

#### Tool Integrations
```bash
# List all tool directories
ls -la tools/

# Expected tools:
# - simplewall/
# - sysinternals/
# - ffmpeg/
# - obsidian/
```

#### Documentation Files
```bash
# List all documentation
ls -la docs/

# Expected docs:
# - SETUP.md
# - ARCHITECTURE.md
# - USAGE.md
# - LLM_AGENTS.md
# - PRODUCTION_DEPLOYMENT.md
# - TROUBLESHOOTING.md
# - OBSIDIAN_INTEGRATION.md
# - QUICK_REFERENCE.md
```

#### Gateway and Services
```bash
# List gateway components
ls -la gateway/

# Expected:
# - gateway.py (Agent Gateway API)
# - mcp_server.py (Model Context Protocol server)
# - Dockerfile, Dockerfile.mcp
# - requirements.txt
```

### Step 3: Analyze Current State

Determine what needs to be done:

```bash
# Check if .env file exists
if [ ! -f .env ]; then
    echo "TODO: Create .env file from .env.example"
fi

# Check if required directories exist
for dir in langflow/flows langflow/config n8n/workflows postgres/init content/inbox content/output logs gateway/config; do
    if [ ! -d "$dir" ]; then
        echo "TODO: Create directory $dir"
    fi
done

# Check if Docker services are running
docker compose ps
# If no services running, add to TODO list

# Check if Python dependencies are installed
python3 -c "import dotenv, qdrant_client, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "TODO: Install Python dependencies"
fi
```

## ✅ Automated Setup Procedure

Execute these steps in order to set up the repository:

### Step 1: Environment Configuration

```bash
# Create .env file from template
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  IMPORTANT: Edit .env with your credentials before starting services"
else
    echo "✅ .env file already exists"
fi
```

### Step 2: Directory Structure Creation

```bash
# Run the setup target from Makefile
echo "Creating directory structure..."
make setup

# Or manually create directories if make is not available:
mkdir -p langflow/flows langflow/config
mkdir -p n8n/workflows
mkdir -p postgres/init
mkdir -p agents/boot_hardening agents/daily_brief agents/focus_guardrails
mkdir -p agents/content_editing agents/research_intel agents/knowledge_management
mkdir -p tools/simplewall tools/sysinternals tools/ffmpeg tools/obsidian
mkdir -p docs/runbooks
mkdir -p config
mkdir -p scripts/automation
mkdir -p content/inbox content/output
mkdir -p logs
mkdir -p gateway/config

# Create placeholder files for git tracking
touch content/inbox/.gitkeep
touch content/output/.gitkeep

echo "✅ Directory structure created"
```

### Step 3: Python Dependencies Installation

```bash
# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m pip install --user -r requirements.txt

# Verify installation
python3 -c "import dotenv, qdrant_client, requests, pandas, psutil, loguru" && \
    echo "✅ Python dependencies installed successfully" || \
    echo "❌ Error installing Python dependencies"
```

### Step 4: Pre-commit Hooks Installation (Optional)

```bash
# Install pre-commit hooks for code quality
if command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit hooks..."
    make pre-commit-install
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️  pre-commit not available, skipping hooks installation"
fi
```

### Step 5: Docker Services Initialization

```bash
# Pull required Docker images
echo "Pulling Docker images (this may take several minutes)..."
docker compose pull

# Start services
echo "Starting OsMEN services..."
docker compose up -d

# Wait for services to be ready
echo "Waiting for services to initialize..."
sleep 15

# Check service status
docker compose ps
echo "✅ Docker services started"
```

### Step 6: LLM Configuration

Choose one of the following LLM options:

#### Option A: Production Cloud LLM Agents (Recommended for best results)

Edit `.env` and configure ONE OR MORE of these:

```bash
# OpenAI (GPT-4, Codex)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# GitHub Copilot
GITHUB_TOKEN=your_github_token_here

# Amazon Q
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-opus-20240229
```

#### Option B: LM Studio (Primary Local Option)

```bash
# 1. Download LM Studio from https://lmstudio.ai/
# 2. Install and open LM Studio
# 3. Download a model (e.g., Mistral, Llama 2)
# 4. Start the local server (port 1234)
# 5. Verify in .env:
LM_STUDIO_URL=http://host.docker.internal:1234/v1
LM_STUDIO_MODEL=local-model
```

#### Option C: Ollama (Secondary Local Option)

```bash
# Start Ollama with Docker Compose
docker compose --profile ollama up -d

# Wait for Ollama to start
sleep 10

# Pull recommended models
echo "Pulling Ollama models (this will take time)..."
docker exec osmen-ollama ollama pull llama2
docker exec osmen-ollama ollama pull mistral

echo "✅ Ollama models ready"
```

### Step 7: Obsidian Integration (Optional)

```bash
# If using Obsidian knowledge management:
# 1. Create or specify your Obsidian vault location
# 2. Update .env:
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

# 3. Restart MCP server
docker compose restart mcp-server
```

## 🔬 Post-Setup Validation

### Step 1: Run Operational Check

```bash
# Execute comprehensive operational check
echo "Running operational status check..."
python3 check_operational.py

# Expected output:
# ✅ OsMEN is OPERATIONAL - All checks passed!
# System Status: HEALTHY ✅
```

### Step 2: Run Agent Tests

```bash
# Execute agent test suite
echo "Running agent tests..."
python3 test_agents.py

# Expected output:
# Boot Hardening            ✅ PASS
# Daily Brief               ✅ PASS
# Focus Guardrails          ✅ PASS
# Tool Integrations         ✅ PASS
# Total: 4/4 tests passed
# 🎉 All tests passed!
```

### Step 3: Security Validation

```bash
# Run security checks
echo "Running security validation..."
python3 scripts/automation/validate_security.py

# Expected: All security checks pass
```

### Step 4: LLM Provider Test (If configured)

```bash
# Test LLM connectivity
echo "Testing LLM provider connectivity..."
python3 scripts/automation/test_llm_providers.py

# Expected: Successful connection to configured LLM(s)
```

### Step 5: Service Accessibility Check

```bash
# Verify all web interfaces are accessible
echo "Checking service endpoints..."

# Langflow UI
curl -f http://localhost:7860 > /dev/null 2>&1 && \
    echo "✅ Langflow accessible at http://localhost:7860" || \
    echo "❌ Langflow not accessible"

# n8n UI
curl -f http://localhost:5678 > /dev/null 2>&1 && \
    echo "✅ n8n accessible at http://localhost:5678" || \
    echo "❌ n8n not accessible"

# Qdrant UI
curl -f http://localhost:6333/dashboard > /dev/null 2>&1 && \
    echo "✅ Qdrant accessible at http://localhost:6333/dashboard" || \
    echo "❌ Qdrant not accessible"

# Agent Gateway API
curl -f http://localhost:8080/docs > /dev/null 2>&1 && \
    echo "✅ Agent Gateway accessible at http://localhost:8080/docs" || \
    echo "❌ Agent Gateway not accessible"

# MCP Server
curl -f http://localhost:8081 > /dev/null 2>&1 && \
    echo "✅ MCP Server accessible at http://localhost:8081" || \
    echo "❌ MCP Server not accessible"
```

## 📝 Automated To-Do Generation

Based on repository scan, generate a to-do list:

```python
#!/usr/bin/env python3
"""
Automated To-Do Generator for OsMEN Setup
"""

import os
import json
from pathlib import Path

def generate_setup_todos():
    """Generate setup to-dos based on repository state"""
    
    todos = []
    project_root = Path.cwd()
    
    # Check .env file
    if not (project_root / '.env').exists():
        todos.append({
            'priority': 'HIGH',
            'task': 'Create .env file from .env.example',
            'command': 'cp .env.example .env',
            'notes': 'Edit with your LLM API keys and configuration'
        })
    
    # Check required directories
    required_dirs = [
        'langflow/flows', 'langflow/config',
        'n8n/workflows',
        'content/inbox', 'content/output',
        'logs', 'gateway/config'
    ]
    
    for dir_path in required_dirs:
        if not (project_root / dir_path).exists():
            todos.append({
                'priority': 'HIGH',
                'task': f'Create directory: {dir_path}',
                'command': f'mkdir -p {dir_path}',
                'notes': 'Required for proper operation'
            })
    
    # Check Python dependencies
    try:
        import dotenv
        import qdrant_client
        import requests
        import pandas
        import psutil
        import loguru
    except ImportError as e:
        todos.append({
            'priority': 'HIGH',
            'task': 'Install Python dependencies',
            'command': 'python3 -m pip install --user -r requirements.txt',
            'notes': f'Missing: {e.name}'
        })
    
    # Check Docker services
    import subprocess
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--format', 'json'],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            output = result.stdout.decode().strip()
            if not output:
                todos.append({
                    'priority': 'MEDIUM',
                    'task': 'Start Docker services',
                    'command': 'docker compose up -d',
                    'notes': 'Required to run OsMEN'
                })
    except:
        todos.append({
            'priority': 'HIGH',
            'task': 'Install and start Docker',
            'command': 'N/A - Manual installation required',
            'notes': 'Visit https://docs.docker.com/get-docker/'
        })
    
    # Check LLM configuration
    env_file = project_root / '.env'
    if env_file.exists():
        with open(env_file) as f:
            env_content = f.read()
            
        has_llm = False
        llm_options = [
            'OPENAI_API_KEY', 'GITHUB_TOKEN', 'AWS_ACCESS_KEY_ID',
            'ANTHROPIC_API_KEY', 'LM_STUDIO_URL', 'OLLAMA_URL'
        ]
        
        for option in llm_options:
            if option in env_content and 'your_' not in env_content:
                has_llm = True
                break
        
        if not has_llm:
            todos.append({
                'priority': 'HIGH',
                'task': 'Configure LLM provider',
                'command': 'Edit .env file',
                'notes': 'Set up OpenAI, Copilot, Claude, LM Studio, or Ollama'
            })
    
    # Generate report
    print("\n" + "="*60)
    print("OsMEN Setup To-Do List")
    print("="*60 + "\n")
    
    if not todos:
        print("✅ No setup tasks required - repository is ready!")
        return 0
    
    # Sort by priority
    priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    todos.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    for i, todo in enumerate(todos, 1):
        print(f"{i}. [{todo['priority']}] {todo['task']}")
        print(f"   Command: {todo['command']}")
        print(f"   Notes: {todo['notes']}\n")
    
    print("="*60)
    print(f"Total Tasks: {len(todos)}")
    print("="*60)
    
    return len(todos)

if __name__ == '__main__':
    import sys
    sys.exit(generate_setup_todos())
```

Save this as `generate_todos.py` and run:

```bash
python3 generate_todos.py
```

## 🚀 Quick Setup Commands

For AI agents, use these commands in sequence:

```bash
# 1. Navigate to repository
cd /path/to/OsMEN

# 2. Run automated setup
make setup

# 3. Edit .env with LLM credentials
# (AI agent should prompt user for credentials)
nano .env

# 4. Install Python dependencies
python3 -m pip install --user -r requirements.txt

# 5. Start all services
make start
# or
./start.sh

# 6. Pull Ollama models (if using Ollama)
make pull-models

# 7. Validate installation
make validate
# This runs: security-check + test + check-operational

# 8. Access the interfaces
echo "Langflow: http://localhost:7860"
echo "n8n: http://localhost:5678 (admin/changeme)"
echo "Qdrant: http://localhost:6333/dashboard"
echo "Agent Gateway: http://localhost:8080/docs"
```

## 🎯 Success Criteria

The setup is successful when:

- [x] `.env` file exists with valid configuration
- [x] All required directories are created
- [x] Python dependencies are installed
- [x] Docker services are running (7+ containers)
- [x] `check_operational.py` reports all systems operational
- [x] `test_agents.py` shows all tests passing
- [x] Security validation passes
- [x] All web interfaces are accessible
- [x] At least one LLM provider is configured

## 🔧 Troubleshooting Common Issues

### Issue: Docker services won't start

```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs
docker compose logs

# Restart Docker
sudo systemctl restart docker
docker compose down
docker compose up -d
```

### Issue: Port conflicts

```bash
# Check if ports are in use
sudo lsof -i :7860  # Langflow
sudo lsof -i :5678  # n8n
sudo lsof -i :6333  # Qdrant

# Stop conflicting services or change ports in docker-compose.yml
```

### Issue: Python dependencies fail to install

```bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Install with verbose output
python3 -m pip install -v -r requirements.txt
```

### Issue: Ollama models fail to download

```bash
# Check Ollama logs
docker logs osmen-ollama

# Manually pull model
docker exec -it osmen-ollama ollama pull llama2

# Check available space
df -h
```

### Issue: Agent tests fail

```bash
# Check detailed error output
python3 test_agents.py 2>&1 | tee test_output.log

# Verify Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Check agent files exist
ls -la agents/*/
```

## 📚 Next Steps After Setup

1. **Read Documentation**
   - Review `docs/SETUP.md` for detailed configuration
   - Read `docs/USAGE.md` for usage examples
   - Check `docs/LLM_AGENTS.md` for LLM provider setup

2. **Configure Agents**
   - Customize agent behavior in Langflow UI (http://localhost:7860)
   - Set up automated workflows in n8n (http://localhost:5678)
   - Configure tool integrations for your system

3. **Test Functionality**
   - Run individual agents: `python3 agents/boot_hardening/boot_hardening_agent.py`
   - Test LLM connectivity: `make test-llm`
   - Create test workflows in n8n

4. **Production Deployment**
   - Review `docs/PRODUCTION_DEPLOYMENT.md`
   - Set up backups: `make backup`
   - Configure monitoring and alerting

## 📞 Support and Resources

- **Documentation**: `docs/` directory
- **Examples**: `test_agents.py`, `test_live_use_cases.py`
- **Help Commands**: `make help`
- **Logs**: `make logs` or `docker compose logs -f`
- **Status Check**: `make status`

## 🔐 Security Considerations

Before production use:

```bash
# 1. Change default credentials in .env
N8N_BASIC_AUTH_PASSWORD=<strong-password>
POSTGRES_PASSWORD=<strong-password>

# 2. Run security validation
make security-check

# 3. Review security script
cat scripts/automation/validate_security.py

# 4. Set up firewall rules if exposing services
# Use Simplewall integration for Windows hosts
```

## ✨ AI Agent Automation Summary

For full automation, an AI agent should execute:

```bash
#!/bin/bash
set -e

echo "Starting OsMEN automated setup..."

# 1. Pre-flight checks
./check_operational.py || echo "Initial check may fail before setup"

# 2. Run setup
make setup

# 3. Prompt user for LLM configuration
echo "Please configure your LLM provider in .env file"
read -p "Press Enter after configuring .env..."

# 4. Install dependencies
python3 -m pip install --user -r requirements.txt

# 5. Start services
make start

# 6. Wait for services
sleep 20

# 7. Validate
make validate

# 8. Display endpoints
echo ""
echo "Setup complete! Access points:"
echo "  Langflow: http://localhost:7860"
echo "  n8n: http://localhost:5678"
echo "  Qdrant: http://localhost:6333/dashboard"
echo ""
```

---

**End of Setup Instructions**

For questions or issues, review the troubleshooting section or check the comprehensive documentation in the `docs/` directory.
