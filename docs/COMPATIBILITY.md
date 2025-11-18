# Compatibility Matrix

This document outlines the tested platforms, versions, and known compatibility issues for OsMEN.

## Supported Operating Systems

### ✅ Tested and Supported

| Operating System | Version | Status | Notes |
|-----------------|---------|--------|-------|
| **Ubuntu** | 20.04 LTS | ✅ Fully Supported | Recommended for production |
| **Ubuntu** | 22.04 LTS | ✅ Fully Supported | Recommended for production |
| **Ubuntu** | 24.04 LTS | ✅ Fully Supported | Latest LTS |
| **Debian** | 11 (Bullseye) | ✅ Supported | |
| **Debian** | 12 (Bookworm) | ✅ Supported | |
| **macOS** | 12 (Monterey) | ✅ Supported | Docker Desktop required |
| **macOS** | 13 (Ventura) | ✅ Supported | Docker Desktop required |
| **macOS** | 14 (Sonoma) | ✅ Supported | Docker Desktop required |
| **Windows** | 10 (21H2+) | ✅ Supported | WSL2 + Docker Desktop |
| **Windows** | 11 | ✅ Supported | WSL2 + Docker Desktop |

### ⚠️ Limited Support

| Operating System | Version | Status | Notes |
|-----------------|---------|--------|-------|
| **CentOS** | 8 Stream | ⚠️ Limited | EOL, migrate to Rocky/Alma |
| **Rocky Linux** | 8.x, 9.x | ⚠️ Limited | Should work, not officially tested |
| **Fedora** | 38+ | ⚠️ Limited | Should work, not officially tested |

### ❌ Not Supported

- Windows without WSL2
- macOS < 12
- 32-bit systems
- ARM systems (experimental, not tested)

## Required Software Versions

### Docker

| Component | Minimum Version | Recommended | Notes |
|-----------|----------------|-------------|-------|
| **Docker Engine** | 20.10.0 | 24.0.0+ | Older versions may have compatibility issues |
| **Docker Compose** | 1.29.0 | 2.20.0+ | V2 recommended for better performance |

**Installation:**
- Linux: Use official Docker repository
- macOS: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- Windows: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) with WSL2 backend

### Python

| Version | Status | Notes |
|---------|--------|-------|
| **3.12.x** | ✅ Recommended | Fully tested |
| **3.11.x** | ✅ Supported | Compatible |
| **3.10.x** | ⚠️ Minimum | May have minor issues |
| **3.9.x** | ❌ Not Supported | Missing required features |

### Git

| Version | Status |
|---------|--------|
| **2.30+** | ✅ Recommended |
| **2.20+** | ⚠️ Minimum |

## System Requirements

### Minimum Requirements

| Resource | Minimum | Notes |
|----------|---------|-------|
| **CPU** | 4 cores | Intel/AMD x86_64 |
| **RAM** | 16 GB | 8 GB for Docker, 8 GB for OS/other |
| **Disk Space** | 50 GB free | 20 GB for Docker images, 30 GB for data |
| **Network** | Stable internet | Required for LLM APIs and updates |

### Recommended Requirements

| Resource | Recommended | Notes |
|----------|------------|-------|
| **CPU** | 8+ cores | Better performance for parallel agents |
| **RAM** | 32 GB | 16 GB for Docker, 16 GB for OS/other |
| **Disk Space** | 100 GB free | SSD recommended for better I/O |
| **GPU** | NVIDIA GPU | Optional, for local LLM acceleration |

### Production Requirements

| Resource | Production | Notes |
|----------|-----------|-------|
| **CPU** | 16+ cores | For high-concurrency workloads |
| **RAM** | 64 GB | Handle multiple concurrent users |
| **Disk Space** | 500 GB+ | SSD/NVMe required |
| **Network** | 1 Gbps+ | Low latency connection |
| **Redundancy** | Multi-node | Consider Kubernetes/Docker Swarm |

## Known Compatibility Issues

### Docker Desktop on macOS

**Issue:** File system performance with bind mounts  
**Impact:** Slower I/O operations  
**Workaround:** Use named volumes instead of bind mounts when possible  
**Status:** Known Docker Desktop limitation

### WSL2 on Windows

**Issue:** Memory usage grows over time  
**Impact:** System slowdown  
**Workaround:** Configure WSL2 memory limits in `.wslconfig`:
```ini
[wsl2]
memory=16GB
processors=8
swap=8GB
```
**Status:** Known WSL2 issue, Microsoft working on fix

### Ollama on ARM (Apple Silicon)

**Issue:** Some models not optimized for ARM  
**Impact:** Slower inference  
**Workaround:** Use Rosetta 2 or wait for ARM-optimized models  
**Status:** Experimental support

### N8N Webhook Timeouts

**Issue:** Webhooks timing out with slow LLM responses  
**Impact:** Failed workflow executions  
**Workaround:** Increase timeout in n8n settings or use async workflows  
**Status:** Configuration issue

## Platform-Specific Installation

### Ubuntu/Debian

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose V2
sudo apt-get install docker-compose-plugin

# Install Python 3.12
sudo apt-get install python3.12 python3.12-venv python3-pip

# Clone and setup OsMEN
git clone https://github.com/dwilli15/OsMEN.git
cd OsMEN
./1stsetup.md
```

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
# Download from https://docs.docker.com/desktop/install/mac-install/
# Or use: brew install --cask docker

# Install Python 3.12
brew install python@3.12

# Clone and setup OsMEN
git clone https://github.com/dwilli15/OsMEN.git
cd OsMEN
./1stsetup.md
```

### Windows (WSL2)

```powershell
# Install WSL2 (PowerShell as Administrator)
wsl --install

# Install Ubuntu in WSL2
wsl --install -d Ubuntu-22.04

# Restart computer, then open Ubuntu terminal
```

Then inside WSL2 Ubuntu terminal:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Python 3.12
sudo apt-get update
sudo apt-get install python3.12 python3.12-venv python3-pip

# Clone and setup OsMEN
git clone https://github.com/dwilli15/OsMEN.git
cd OsMEN
./1stsetup.md
```

## Network Requirements

### Required Ports

| Port | Service | Required | Notes |
|------|---------|----------|-------|
| 5678 | n8n | Internal | Workflow automation |
| 7860 | Langflow | Internal | Visual flow builder |
| 6333 | Qdrant | Internal | Vector database |
| 5432 | PostgreSQL | Internal | Database |
| 6379 | Redis | Internal | Cache |
| 8080 | Gateway API | Optional | External if needed |
| 11434 | Ollama | Optional | If using local LLM |

### Firewall Configuration

For production deployments, restrict access:
- Allow only trusted IPs to management interfaces
- Use VPN for remote access
- Enable HTTPS with valid certificates
- Use Docker network isolation

### External API Access

Required for cloud LLM providers:
- OpenAI API: https://api.openai.com
- Anthropic API: https://api.anthropic.com
- GitHub API: https://api.github.com
- Google APIs: https://www.googleapis.com

## Testing Your Installation

### Quick Compatibility Check

```bash
# Check Docker version
docker --version  # Should be 20.10+

# Check Docker Compose version
docker compose version  # Should be 1.29+

# Check Python version
python3 --version  # Should be 3.10+

# Check available resources
docker system info | grep -E "CPUs|Total Memory"
```

### Run Compatibility Tests

```bash
# Clone repository
git clone https://github.com/dwilli15/OsMEN.git
cd OsMEN

# Run compatibility check
python3 check_operational.py

# Run test suite
python3 test_agents.py
```

## Troubleshooting

### Docker Won't Start

**Linux:**
```bash
sudo systemctl status docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

**macOS/Windows:**
- Restart Docker Desktop
- Check Docker Desktop settings
- Ensure WSL2 is enabled (Windows)

### Python Version Issues

```bash
# Install pyenv for version management
curl https://pyenv.run | bash

# Install Python 3.12
pyenv install 3.12
pyenv local 3.12
```

### Insufficient Memory

```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS

# Increase Docker memory (Docker Desktop Settings)
# Or stop other services to free up RAM
```

### Port Conflicts

```bash
# Check what's using a port
sudo lsof -i :5678  # Linux/macOS
netstat -ano | findstr :5678  # Windows

# Stop conflicting service or change port in docker-compose.yml
```

## Reporting Compatibility Issues

If you encounter compatibility issues:

1. Check this document for known issues
2. Search [GitHub Issues](https://github.com/dwilli15/OsMEN/issues)
3. Open a new issue with:
   - OS and version
   - Docker version
   - Python version
   - Error messages
   - Steps to reproduce

## Updates and Support

- **Compatibility updates:** Check this document with each release
- **Version support:** We support the latest 2 major versions
- **LTS support:** Ubuntu LTS versions get extended support

---

**Last Updated:** 2024-11-18  
**Document Version:** 1.0  
**OsMEN Version:** 2.0+
