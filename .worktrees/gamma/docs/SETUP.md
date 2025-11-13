# OsMEN Setup Guide

## Overview

OsMEN (OS Management and Engagement Network) is a local-first no/low-code agent hub that integrates Langflow reasoning graphs with n8n automation fabric, powered by local LLM via Ollama.

## Prerequisites

### Required Software

1. **Docker & Docker Compose**
   - Docker Desktop (Windows/Mac) or Docker Engine (Linux)
   - Docker Compose v3.8 or higher

2. **Git**
   - For cloning the repository

3. **System Tools (Windows)**
   - Sysinternals Suite
   - Simplewall
   - FFmpeg

### Optional Requirements

- NVIDIA GPU for faster LLM inference (recommended)
- At least 16GB RAM
- 50GB free disk space

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/dwilli15/OsMEN.git
cd OsMEN
```

### 2. Configure Environment

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` and set your preferences:
- Update passwords for n8n and PostgreSQL
- Configure tool paths for Windows applications
- Set Ollama model preferences

### 3. Download Ollama Models

Pull the required LLM models:

```bash
docker-compose up -d ollama
docker exec -it osmen-ollama ollama pull llama2
docker exec -it osmen-ollama ollama pull mistral
```

### 4. Start All Services

Start the complete OsMEN stack:

```bash
docker-compose up -d
```

This will start:
- Langflow (port 7860)
- n8n (port 5678)
- Ollama (port 11434)
- Qdrant (port 6333)
- PostgreSQL (port 5432)
- Redis (port 6379)

### 5. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

All services should show status "Up".

### 6. Access the Interfaces

- **Langflow UI**: http://localhost:7860
- **n8n UI**: http://localhost:5678
  - Default credentials: admin / changeme
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## Initial Configuration

### Langflow Setup

1. Open Langflow at http://localhost:7860
2. Import the flows from `langflow/flows/`:
   - coordinator.json
   - boot_hardening_specialist.json
   - daily_brief_specialist.json
   - focus_guardrails_specialist.json
3. Test each flow to ensure Ollama connectivity

### n8n Setup

1. Open n8n at http://localhost:5678
2. Log in with credentials from .env file
3. Import workflows from `n8n/workflows/`:
   - boot_hardening_trigger.json
   - daily_brief_trigger.json
   - focus_guardrails_monitor.json
4. Activate each workflow

### Qdrant Setup

1. Open Qdrant dashboard at http://localhost:6333/dashboard
2. Verify collections are created:
   - osmen_memory
   - boot_hardening_memory
   - daily_brief_memory
   - focus_guardrails_memory

## Tool Integration (Windows)

### Sysinternals Suite

1. Download from: https://docs.microsoft.com/sysinternals
2. Extract to: C:\Tools\Sysinternals
3. Update SYSINTERNALS_PATH in .env

### Simplewall

1. Download from: https://www.henrypp.org/product/simplewall
2. Install to: C:\Program Files\simplewall
3. Update SIMPLEWALL_PATH in .env

### FFmpeg

1. Download from: https://ffmpeg.org/download.html
2. Extract to: C:\Tools\ffmpeg
3. Update FFMPEG_PATH in .env

## Testing the MVP Features

### Boot Hardening

Test the boot hardening agent:

```bash
python agents/boot_hardening/boot_hardening_agent.py
```

### Daily Brief

Generate a daily brief:

```bash
python agents/daily_brief/daily_brief_agent.py
```

### Focus Guardrails

Test focus guardrails:

```bash
python agents/focus_guardrails/focus_guardrails_agent.py
```

## Troubleshooting

### Services Won't Start

Check logs for specific service:
```bash
docker-compose logs <service-name>
```

### Ollama Model Issues

Re-pull the model:
```bash
docker exec -it osmen-ollama ollama pull llama2
```

### n8n Connection Issues

Verify n8n can reach Langflow:
```bash
docker exec -it osmen-n8n curl http://langflow:7860
```

### Database Connection Issues

Restart PostgreSQL:
```bash
docker-compose restart postgres
```

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Read [USAGE.md](USAGE.md) for usage instructions
- Explore the Langflow flows and customize them
- Create custom n8n workflows
- Add new specialist agents

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in `/docs`
