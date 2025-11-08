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

## 🚀 Phase 2: Advanced LLM & Tool Setup

After completing Phase 1 setup, this section provides automated configuration for:
- OAuth-based LLM providers (Gemini, ChatGPT web interface, GitHub Copilot)
- Local LLM runtimes (LM Studio, Ollama, llama.cpp)
- MCP server and tool integrations
- Team configuration and agent orchestration

### Step 1: Check Installed Programs

```bash
#!/bin/bash
# Check for installed LLM tools and prompt for installation

echo "Checking for installed LLM tools..."
echo "===================================="

# Check LM Studio
if command -v lmstudio &> /dev/null || [ -d "/Applications/LM Studio.app" ] || [ -d "$HOME/.lmstudio" ]; then
    echo "✅ LM Studio detected"
    LM_STUDIO_INSTALLED=true
else
    echo "❌ LM Studio not found"
    LM_STUDIO_INSTALLED=false
fi

# Check Ollama
if command -v ollama &> /dev/null; then
    echo "✅ Ollama detected: $(ollama --version)"
    OLLAMA_INSTALLED=true
else
    echo "❌ Ollama not found"
    OLLAMA_INSTALLED=false
fi

# Check llama.cpp
if command -v llama &> /dev/null || [ -f "$HOME/llama.cpp/main" ]; then
    echo "✅ llama.cpp detected"
    LLAMACPP_INSTALLED=true
else
    echo "❌ llama.cpp not found"
    LLAMACPP_INSTALLED=false
fi

# Check Docker (for containerized Ollama)
if docker info &> /dev/null; then
    echo "✅ Docker available (can run containerized Ollama)"
    DOCKER_AVAILABLE=true
else
    echo "⚠️  Docker not available"
    DOCKER_AVAILABLE=false
fi

echo "===================================="
```

### Step 2: Automated Installation Prompts

```python
#!/usr/bin/env python3
"""
Automated LLM Tool Installation Assistant
"""

import os
import subprocess
import platform
from pathlib import Path

def prompt_install(tool_name, description):
    """Prompt user for installation permission"""
    print(f"\n{tool_name} is not installed.")
    print(f"Description: {description}")
    response = input(f"Would you like to install {tool_name}? [y/N]: ").strip().lower()
    return response in ['y', 'yes']

def install_lm_studio():
    """Guide LM Studio installation"""
    system = platform.system()
    
    print("\n" + "="*60)
    print("LM Studio Installation Guide")
    print("="*60)
    print("\nLM Studio must be installed manually:")
    print("1. Visit: https://lmstudio.ai/")
    print("2. Download the appropriate version for your OS")
    
    if system == "Darwin":  # macOS
        print("3. Open the DMG and drag LM Studio to Applications")
    elif system == "Windows":
        print("3. Run the installer and follow the prompts")
    elif system == "Linux":
        print("3. Extract the AppImage and make it executable")
    
    print("\nAfter installation:")
    print("1. Open LM Studio")
    print("2. Download a model (recommended: Mistral 7B or Llama 2)")
    print("3. Start the local server (enable in settings)")
    print("4. Note the server URL (usually http://localhost:1234)")
    
    input("\nPress Enter after installing LM Studio...")
    
    # Verify installation
    lm_studio_dirs = [
        "/Applications/LM Studio.app",
        os.path.expanduser("~/.lmstudio"),
        "C:\\Program Files\\LM Studio"
    ]
    
    for dir_path in lm_studio_dirs:
        if os.path.exists(dir_path):
            print("✅ LM Studio installation detected!")
            return True
    
    print("⚠️  Could not verify LM Studio installation")
    return False

def install_ollama():
    """Install Ollama"""
    system = platform.system()
    
    print("\n" + "="*60)
    print("Ollama Installation")
    print("="*60)
    
    try:
        if system == "Darwin":  # macOS
            print("Installing Ollama via Homebrew...")
            subprocess.run(["brew", "install", "ollama"], check=True)
        elif system == "Linux":
            print("Installing Ollama via curl script...")
            subprocess.run(
                "curl -fsSL https://ollama.com/install.sh | sh",
                shell=True,
                check=True
            )
        elif system == "Windows":
            print("Downloading Ollama for Windows...")
            print("Visit: https://ollama.com/download/windows")
            print("Run the installer after download completes")
            input("Press Enter after installing Ollama...")
        
        # Verify installation
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Ollama installed: {result.stdout.strip()}")
            return True
        else:
            print("⚠️  Could not verify Ollama installation")
            return False
            
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def install_llamacpp():
    """Install llama.cpp"""
    print("\n" + "="*60)
    print("llama.cpp Installation")
    print("="*60)
    
    home = Path.home()
    llamacpp_dir = home / "llama.cpp"
    
    if llamacpp_dir.exists():
        print("⚠️  llama.cpp directory already exists")
        return True
    
    try:
        print("Cloning llama.cpp repository...")
        subprocess.run(
            ["git", "clone", "https://github.com/ggerganov/llama.cpp.git", str(llamacpp_dir)],
            check=True
        )
        
        print("Building llama.cpp...")
        subprocess.run(
            ["make"],
            cwd=str(llamacpp_dir),
            check=True
        )
        
        print("✅ llama.cpp installed successfully!")
        print(f"Location: {llamacpp_dir}")
        print(f"\nTo use: {llamacpp_dir}/main -m /path/to/model.gguf")
        return True
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def main():
    """Main installation flow"""
    print("="*60)
    print("OsMEN Phase 2: LLM Tool Installation Assistant")
    print("="*60)
    
    # Check and install LM Studio
    if not os.path.exists("/Applications/LM Studio.app") and \
       not os.path.exists(os.path.expanduser("~/.lmstudio")):
        if prompt_install(
            "LM Studio",
            "User-friendly local LLM runtime with model management"
        ):
            install_lm_studio()
    
    # Check and install Ollama
    if subprocess.run(["which", "ollama"], capture_output=True).returncode != 0:
        if prompt_install(
            "Ollama",
            "Simple local LLM runtime with CLI interface"
        ):
            install_ollama()
    
    # Check and install llama.cpp
    if not os.path.exists(os.path.expanduser("~/llama.cpp")):
        if prompt_install(
            "llama.cpp",
            "High-performance LLM inference engine"
        ):
            install_llamacpp()
    
    print("\n" + "="*60)
    print("Installation assistant complete!")
    print("="*60)

if __name__ == '__main__':
    main()
```

Save as `scripts/automation/install_llm_tools.py` and run:

```bash
python3 scripts/automation/install_llm_tools.py
```

### Step 3: OAuth Configuration for Cloud LLMs

#### Google Gemini OAuth Setup

```bash
#!/bin/bash
# Setup Google Gemini OAuth

echo "Google Gemini OAuth Setup"
echo "========================="
echo ""
echo "1. Go to: https://makersuite.google.com/app/apikey"
echo "2. Sign in with your Google account"
echo "3. Click 'Create API Key'"
echo "4. Copy the API key"
echo ""

read -p "Enter your Gemini API key: " GEMINI_API_KEY

# Add to .env
if ! grep -q "GEMINI_API_KEY" .env; then
    echo "" >> .env
    echo "# Google Gemini Configuration" >> .env
    echo "GEMINI_API_KEY=$GEMINI_API_KEY" >> .env
    echo "GEMINI_MODEL=gemini-pro" >> .env
    echo "✅ Gemini API key added to .env"
else
    sed -i.bak "s|GEMINI_API_KEY=.*|GEMINI_API_KEY=$GEMINI_API_KEY|" .env
    echo "✅ Gemini API key updated in .env"
fi
```

#### ChatGPT Web Interface (via ChatGPT API)

```bash
#!/bin/bash
# Setup ChatGPT Web Interface Access

echo "ChatGPT Web Interface Setup"
echo "============================"
echo ""
echo "For ChatGPT web interface integration, you need:"
echo "1. ChatGPT Plus subscription (for API access)"
echo "2. OpenAI API key"
echo ""
echo "Steps:"
echo "1. Go to: https://platform.openai.com/api-keys"
echo "2. Sign in with your OpenAI account"
echo "3. Click 'Create new secret key'"
echo "4. Name it 'OsMEN' and copy the key"
echo ""

read -p "Enter your OpenAI API key: " OPENAI_API_KEY

# Update .env
sed -i.bak "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_API_KEY|" .env
echo "✅ OpenAI API key updated in .env"

# For web interface session (advanced)
echo ""
echo "For direct web interface access (experimental):"
echo "1. Install browser automation: pip install playwright"
echo "2. Run: playwright install chromium"
echo "3. Set CHATGPT_SESSION_TOKEN in .env (requires manual extraction)"
```

#### GitHub Copilot OAuth Setup

```bash
#!/bin/bash
# Setup GitHub Copilot OAuth

echo "GitHub Copilot OAuth Setup"
echo "=========================="
echo ""
echo "GitHub Copilot requires:"
echo "1. GitHub account with Copilot subscription"
echo "2. Personal Access Token with 'copilot' scope"
echo ""
echo "Steps:"
echo "1. Go to: https://github.com/settings/tokens/new"
echo "2. Name: 'OsMEN Copilot Access'"
echo "3. Scopes: Select 'copilot'"
echo "4. Click 'Generate token'"
echo "5. Copy the token"
echo ""

read -p "Enter your GitHub token: " GITHUB_TOKEN

# Update .env
sed -i.bak "s|GITHUB_TOKEN=.*|GITHUB_TOKEN=$GITHUB_TOKEN|" .env
echo "✅ GitHub token updated in .env"

# Verify Copilot access
echo ""
echo "Verifying Copilot access..."
if command -v gh &> /dev/null; then
    gh auth login --with-token <<< "$GITHUB_TOKEN"
    if gh copilot explain "test" &> /dev/null; then
        echo "✅ GitHub Copilot access verified!"
    else
        echo "⚠️  Could not verify Copilot access. Ensure subscription is active."
    fi
else
    echo "⚠️  GitHub CLI not installed. Skipping verification."
fi
```

### Step 4: LM Studio Configuration

```bash
#!/bin/bash
# Configure LM Studio

echo "LM Studio Configuration"
echo "======================="
echo ""

# Check if LM Studio is running
if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "✅ LM Studio server is running"
    
    # List available models
    echo ""
    echo "Available models:"
    curl -s http://localhost:1234/v1/models | python3 -m json.tool
    
else
    echo "⚠️  LM Studio server is not running"
    echo ""
    echo "Please start LM Studio and enable the local server:"
    echo "1. Open LM Studio"
    echo "2. Go to 'Local Server' tab"
    echo "3. Click 'Start Server'"
    echo "4. Server will start on http://localhost:1234"
    echo ""
    read -p "Press Enter after starting LM Studio server..."
fi

# Update .env with LM Studio configuration
if ! grep -q "LM_STUDIO_URL" .env; then
    echo "" >> .env
    echo "# LM Studio Configuration" >> .env
    echo "LM_STUDIO_URL=http://localhost:1234/v1" >> .env
    echo "LM_STUDIO_MODEL=local-model" >> .env
else
    echo "✅ LM Studio already configured in .env"
fi

# Test connection
echo ""
echo "Testing LM Studio connection..."
if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "✅ Successfully connected to LM Studio!"
else
    echo "❌ Could not connect to LM Studio. Check that server is running."
fi
```

### Step 5: Ollama Setup & Model Pull

```bash
#!/bin/bash
# Setup Ollama and pull models

echo "Ollama Setup"
echo "============"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed"
    echo "Run: python3 scripts/automation/install_llm_tools.py"
    exit 1
fi

# Start Ollama service (if not running)
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    sleep 5
fi

echo "✅ Ollama is running"
echo ""

# Recommend models
echo "Recommended models:"
echo "1. llama2 (7B) - General purpose"
echo "2. mistral (7B) - Better reasoning"
echo "3. codellama (7B) - Code generation"
echo "4. llama2:13b - More capable (requires 16GB+ RAM)"
echo ""

# Prompt for model selection
read -p "Which model would you like to pull? [mistral]: " MODEL_CHOICE
MODEL_CHOICE=${MODEL_CHOICE:-mistral}

echo ""
echo "Pulling $MODEL_CHOICE (this may take 10-20 minutes)..."
ollama pull $MODEL_CHOICE

if [ $? -eq 0 ]; then
    echo "✅ Model $MODEL_CHOICE pulled successfully!"
    
    # Update .env
    sed -i.bak "s|OLLAMA_MODEL=.*|OLLAMA_MODEL=$MODEL_CHOICE|" .env
    echo "✅ Updated .env with model: $MODEL_CHOICE"
    
    # Test the model
    echo ""
    echo "Testing model..."
    ollama run $MODEL_CHOICE "Hello, this is a test. Respond with 'OK' if you can read this."
    
else
    echo "❌ Failed to pull model. Check your internet connection."
fi

# Update .env
if ! grep -q "OLLAMA_URL" .env; then
    echo "" >> .env
    echo "# Ollama Configuration" >> .env
    echo "OLLAMA_URL=http://localhost:11434" >> .env
    echo "OLLAMA_MODEL=$MODEL_CHOICE" >> .env
fi
```

### Step 6: llama.cpp Setup

```bash
#!/bin/bash
# Setup llama.cpp and download models

echo "llama.cpp Setup"
echo "==============="
echo ""

LLAMACPP_DIR="$HOME/llama.cpp"

if [ ! -d "$LLAMACPP_DIR" ]; then
    echo "❌ llama.cpp not found at $LLAMACPP_DIR"
    echo "Run: python3 scripts/automation/install_llm_tools.py"
    exit 1
fi

echo "✅ llama.cpp found at $LLAMACPP_DIR"
echo ""

# Check for models
MODELS_DIR="$HOME/llama-models"
mkdir -p "$MODELS_DIR"

echo "Recommended GGUF models:"
echo "1. Llama 2 7B GGUF"
echo "2. Mistral 7B GGUF"
echo "3. CodeLlama 7B GGUF"
echo ""
echo "Download models from: https://huggingface.co/TheBloke"
echo "Save to: $MODELS_DIR"
echo ""

# Example model download
read -p "Would you like to download Mistral 7B GGUF? [y/N]: " DOWNLOAD_MODEL

if [[ "$DOWNLOAD_MODEL" =~ ^[Yy]$ ]]; then
    echo "Downloading Mistral 7B GGUF (this may take 10-20 minutes)..."
    
    # Download using wget or curl
    MODEL_URL="https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    
    if command -v wget &> /dev/null; then
        wget -O "$MODELS_DIR/mistral-7b-instruct.gguf" "$MODEL_URL"
    elif command -v curl &> /dev/null; then
        curl -L -o "$MODELS_DIR/mistral-7b-instruct.gguf" "$MODEL_URL"
    else
        echo "❌ wget or curl required for download"
        echo "Please download manually from: $MODEL_URL"
        exit 1
    fi
    
    if [ -f "$MODELS_DIR/mistral-7b-instruct.gguf" ]; then
        echo "✅ Model downloaded successfully!"
        
        # Test the model
        echo ""
        echo "Testing model..."
        "$LLAMACPP_DIR/main" \
            -m "$MODELS_DIR/mistral-7b-instruct.gguf" \
            -p "Hello, this is a test." \
            -n 50
    fi
fi

# Add to .env
if ! grep -q "LLAMACPP_PATH" .env; then
    echo "" >> .env
    echo "# llama.cpp Configuration" >> .env
    echo "LLAMACPP_PATH=$LLAMACPP_DIR" >> .env
    echo "LLAMACPP_MODELS_PATH=$MODELS_DIR" >> .env
fi

echo ""
echo "✅ llama.cpp setup complete!"
```

### Step 7: MCP Server & Tools Setup

```bash
#!/bin/bash
# Setup MCP Server and Tool Integrations

echo "MCP Server & Tools Setup"
echo "========================"
echo ""

# Ensure MCP server is in docker-compose
if grep -q "mcp-server" docker-compose.yml; then
    echo "✅ MCP server defined in docker-compose.yml"
else
    echo "⚠️  MCP server not found in docker-compose.yml"
fi

# Check tool integrations
echo ""
echo "Checking tool integrations..."

TOOLS=("obsidian" "simplewall" "sysinternals" "ffmpeg")

for tool in "${TOOLS[@]}"; do
    if [ -d "tools/$tool" ]; then
        echo "✅ $tool integration found"
        
        # Check for integration file
        if [ -f "tools/$tool/${tool}_integration.py" ]; then
            echo "   └─ Implementation: tools/$tool/${tool}_integration.py"
        fi
    else
        echo "❌ $tool integration missing"
    fi
done

# Obsidian vault setup
echo ""
echo "Obsidian Vault Configuration"
echo "----------------------------"

read -p "Enter path to your Obsidian vault [./obsidian-vault]: " VAULT_PATH
VAULT_PATH=${VAULT_PATH:-./obsidian-vault}

if [ ! -d "$VAULT_PATH" ]; then
    echo "Creating vault directory: $VAULT_PATH"
    mkdir -p "$VAULT_PATH"
    
    # Create sample vault structure
    mkdir -p "$VAULT_PATH"/{Daily,Projects,Resources,Archive}
    
    # Create sample note
    cat > "$VAULT_PATH/Welcome.md" << 'EOF'
# Welcome to OsMEN Knowledge Base

This is your Obsidian vault integrated with OsMEN agents.

## Folders
- **Daily**: Daily notes and logs
- **Projects**: Project documentation
- **Resources**: Reference materials
- **Archive**: Completed items

## Integration
OsMEN agents can:
- Create and read notes
- Search your knowledge base
- Generate summaries
- Find connections between notes
EOF
    
    echo "✅ Sample vault created"
fi

# Update .env
sed -i.bak "s|OBSIDIAN_VAULT_PATH=.*|OBSIDIAN_VAULT_PATH=$VAULT_PATH|" .env
echo "✅ Vault path updated in .env"

# Windows-specific tool paths (if on Windows)
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo ""
    echo "Windows Tool Configuration"
    echo "--------------------------"
    
    # Simplewall
    read -p "Enter Simplewall installation path [C:\Program Files\simplewall]: " SIMPLEWALL_PATH
    SIMPLEWALL_PATH=${SIMPLEWALL_PATH:-C:\\Program Files\\simplewall}
    sed -i.bak "s|SIMPLEWALL_PATH=.*|SIMPLEWALL_PATH=$SIMPLEWALL_PATH|" .env
    
    # Sysinternals
    read -p "Enter Sysinternals installation path [C:\Tools\Sysinternals]: " SYSINTERNALS_PATH
    SYSINTERNALS_PATH=${SYSINTERNALS_PATH:-C:\\Tools\\Sysinternals}
    sed -i.bak "s|SYSINTERNALS_PATH=.*|SYSINTERNALS_PATH=$SYSINTERNALS_PATH|" .env
    
    echo "✅ Windows tool paths updated"
fi

# Start MCP server
echo ""
echo "Starting MCP server..."
docker-compose up -d mcp-server

sleep 5

# Verify MCP server
if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    echo "✅ MCP server is running!"
    echo "   API docs: http://localhost:8081/docs"
else
    echo "⚠️  MCP server not responding. Check logs:"
    echo "   docker-compose logs mcp-server"
fi
```

### Step 8: First Team Setup

```python
#!/usr/bin/env python3
"""
Setup the first agent team in OsMEN
"""

import json
import requests
from pathlib import Path

def create_first_team():
    """Create and configure the first agent team"""
    
    print("="*60)
    print("First Team Setup")
    print("="*60)
    print()
    
    # Define the first team
    team = {
        "name": "Core Operations Team",
        "description": "Primary team for system operations and daily tasks",
        "agents": [
            {
                "name": "Coordinator",
                "role": "coordinator",
                "description": "Routes tasks to specialist agents",
                "flow_file": "langflow/flows/coordinator.json"
            },
            {
                "name": "Boot Hardening Specialist",
                "role": "security",
                "description": "System security and boot integrity",
                "flow_file": "langflow/flows/boot_hardening_specialist.json"
            },
            {
                "name": "Daily Brief Specialist",
                "role": "reporting",
                "description": "Daily briefings and status reports",
                "flow_file": "langflow/flows/daily_brief_specialist.json"
            },
            {
                "name": "Focus Guardrails Specialist",
                "role": "productivity",
                "description": "Productivity and distraction management",
                "flow_file": "langflow/flows/focus_guardrails_specialist.json"
            },
            {
                "name": "Knowledge Management Specialist",
                "role": "knowledge",
                "description": "Obsidian integration and knowledge base",
                "flow_file": "langflow/flows/knowledge_specialist.json"
            }
        ],
        "workflows": [
            {
                "name": "Daily Security Check",
                "trigger": "cron: 0 0 * * *",  # Midnight daily
                "workflow_file": "n8n/workflows/boot_hardening_trigger.json"
            },
            {
                "name": "Morning Brief",
                "trigger": "cron: 0 8 * * *",  # 8 AM daily
                "workflow_file": "n8n/workflows/daily_brief_trigger.json"
            },
            {
                "name": "Focus Session Monitor",
                "trigger": "cron: */15 * * * *",  # Every 15 minutes
                "workflow_file": "n8n/workflows/focus_guardrails_monitor.json"
            }
        ]
    }
    
    # Save team configuration
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    team_file = config_dir / "teams" / "core_operations.json"
    team_file.parent.mkdir(exist_ok=True)
    
    with open(team_file, 'w') as f:
        json.dump(team, f, indent=2)
    
    print(f"✅ Team configuration saved: {team_file}")
    
    # Create Langflow flows if they don't exist
    print()
    print("Checking Langflow flows...")
    
    langflow_dir = Path("langflow/flows")
    langflow_dir.mkdir(parents=True, exist_ok=True)
    
    for agent in team["agents"]:
        flow_file = Path(agent["flow_file"])
        if not flow_file.exists():
            print(f"⚠️  Flow file missing: {flow_file}")
            print(f"   Creating placeholder for {agent['name']}...")
            
            # Create basic flow structure
            flow = {
                "name": agent["name"],
                "description": agent["description"],
                "nodes": [],
                "edges": []
            }
            
            flow_file.parent.mkdir(parents=True, exist_ok=True)
            with open(flow_file, 'w') as f:
                json.dump(flow, f, indent=2)
            
            print(f"   ✅ Created: {flow_file}")
        else:
            print(f"✅ Flow exists: {flow_file}")
    
    # Create n8n workflows if they don't exist
    print()
    print("Checking n8n workflows...")
    
    n8n_dir = Path("n8n/workflows")
    n8n_dir.mkdir(parents=True, exist_ok=True)
    
    for workflow in team["workflows"]:
        workflow_file = Path(workflow["workflow_file"])
        if not workflow_file.exists():
            print(f"⚠️  Workflow file missing: {workflow_file}")
            print(f"   Creating placeholder for {workflow['name']}...")
            
            # Create basic workflow structure
            wf = {
                "name": workflow["name"],
                "nodes": [],
                "connections": {},
                "settings": {
                    "executionOrder": "v1"
                }
            }
            
            workflow_file.parent.mkdir(parents=True, exist_ok=True)
            with open(workflow_file, 'w') as f:
                json.dump(wf, f, indent=2)
            
            print(f"   ✅ Created: {workflow_file}")
        else:
            print(f"✅ Workflow exists: {workflow_file}")
    
    # Display team summary
    print()
    print("="*60)
    print("Team Configuration Summary")
    print("="*60)
    print(f"Team: {team['name']}")
    print(f"Agents: {len(team['agents'])}")
    
    for agent in team['agents']:
        print(f"  - {agent['name']} ({agent['role']})")
    
    print(f"\nWorkflows: {len(team['workflows'])}")
    for workflow in team['workflows']:
        print(f"  - {workflow['name']} ({workflow['trigger']})")
    
    print()
    print("="*60)
    print("✅ First team setup complete!")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Configure flows in Langflow UI: http://localhost:7860")
    print("2. Configure workflows in n8n UI: http://localhost:5678")
    print("3. Test team coordination with sample tasks")
    
    return team

if __name__ == '__main__':
    create_first_team()
```

Save as `scripts/automation/setup_first_team.py` and run:

```bash
python3 scripts/automation/setup_first_team.py
```

### Step 9: Complete Phase 2 Automation Script

```bash
#!/bin/bash
# Complete Phase 2 automated setup

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           OsMEN Phase 2: Advanced Setup Automation            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check and install LLM tools
echo "Step 1: LLM Tool Installation"
echo "=============================="
python3 scripts/automation/install_llm_tools.py
echo ""

# Step 2: OAuth Configuration
echo "Step 2: OAuth Configuration"
echo "============================"
read -p "Configure Gemini OAuth? [y/N]: " SETUP_GEMINI
if [[ "$SETUP_GEMINI" =~ ^[Yy]$ ]]; then
    bash scripts/automation/setup_gemini_oauth.sh
fi

read -p "Configure ChatGPT/OpenAI? [y/N]: " SETUP_OPENAI
if [[ "$SETUP_OPENAI" =~ ^[Yy]$ ]]; then
    bash scripts/automation/setup_openai.sh
fi

read -p "Configure GitHub Copilot? [y/N]: " SETUP_COPILOT
if [[ "$SETUP_COPILOT" =~ ^[Yy]$ ]]; then
    bash scripts/automation/setup_copilot_oauth.sh
fi
echo ""

# Step 3: LM Studio Setup
echo "Step 3: LM Studio Configuration"
echo "================================"
if command -v lmstudio &> /dev/null || [ -d "/Applications/LM Studio.app" ]; then
    bash scripts/automation/configure_lm_studio.sh
else
    echo "⚠️  LM Studio not installed, skipping..."
fi
echo ""

# Step 4: Ollama Setup
echo "Step 4: Ollama Configuration"
echo "============================"
if command -v ollama &> /dev/null; then
    bash scripts/automation/setup_ollama.sh
else
    echo "⚠️  Ollama not installed, skipping..."
fi
echo ""

# Step 5: llama.cpp Setup
echo "Step 5: llama.cpp Configuration"
echo "==============================="
if [ -d "$HOME/llama.cpp" ]; then
    bash scripts/automation/setup_llamacpp.sh
else
    echo "⚠️  llama.cpp not installed, skipping..."
fi
echo ""

# Step 6: MCP & Tools Setup
echo "Step 6: MCP Server & Tools Setup"
echo "================================="
bash scripts/automation/setup_mcp_tools.sh
echo ""

# Step 7: First Team Setup
echo "Step 7: First Team Configuration"
echo "================================="
python3 scripts/automation/setup_first_team.py
echo ""

# Final validation
echo "Step 8: Phase 2 Validation"
echo "=========================="
echo "Testing configured LLM providers..."

# Test each configured provider
if [ -n "$GEMINI_API_KEY" ]; then
    echo "✅ Gemini API key configured"
fi

if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OpenAI API key configured"
fi

if [ -n "$GITHUB_TOKEN" ]; then
    echo "✅ GitHub Copilot configured"
fi

if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "✅ LM Studio running"
fi

if command -v ollama &> /dev/null; then
    echo "✅ Ollama installed"
fi

if [ -d "$HOME/llama.cpp" ]; then
    echo "✅ llama.cpp installed"
fi

if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    echo "✅ MCP Server running"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Phase 2 Setup Complete! 🎉                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "--------"
echo "LLM Providers configured and ready"
echo "Local LLM runtimes installed and configured"
echo "MCP server and tool integrations operational"
echo "First team configured with 5 agents"
echo ""
echo "Next steps:"
echo "1. Test LLM connectivity: make test-llm"
echo "2. Open Langflow: http://localhost:7860"
echo "3. Open n8n: http://localhost:5678"
echo "4. Configure agent flows and workflows"
echo ""
```

Save as `scripts/automation/phase2_setup.sh` and run:

```bash
chmod +x scripts/automation/phase2_setup.sh
./scripts/automation/phase2_setup.sh
```

### Phase 2 Quick Reference

```bash
# Complete Phase 2 in one command
./scripts/automation/phase2_setup.sh

# Or run individual components:

# Install LLM tools
python3 scripts/automation/install_llm_tools.py

# Configure OAuth providers
bash scripts/automation/setup_gemini_oauth.sh
bash scripts/automation/setup_openai.sh
bash scripts/automation/setup_copilot_oauth.sh

# Setup local LLMs
bash scripts/automation/configure_lm_studio.sh
bash scripts/automation/setup_ollama.sh
bash scripts/automation/setup_llamacpp.sh

# Setup MCP and tools
bash scripts/automation/setup_mcp_tools.sh

# Create first team
python3 scripts/automation/setup_first_team.py
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
