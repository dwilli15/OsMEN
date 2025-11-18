# OsMEN Examples

This directory contains example scripts demonstrating the new Setup Manager + CLI Bridge architecture.

## Examples

### 1. `setup_manager_example.py`

Demonstrates how to use the Setup Manager to initialize and manage agents.

**Features shown**:
- Environment validation
- Service connection management
- Agent initialization
- System status retrieval
- Graceful shutdown

**Run**:
```bash
python3 setup_manager_example.py
```

### 2. `cli_bridge_example.py`

Demonstrates how to use the CLI Bridge for AI-powered assistance.

**Features shown**:
- Code generation with Codex
- Command suggestion with Copilot
- Code explanation
- Git workflow help
- Auto-routing tasks

**Run**:
```bash
python3 cli_bridge_example.py
```

**Requirements**:
- `OPENAI_API_KEY` in .env for Codex
- `GITHUB_TOKEN` in .env for Copilot
- OR install gh copilot: `gh extension install github/gh-copilot`

### 3. `integration_example.py`

Demonstrates the complete integration of Setup Manager and CLI Bridge.

**Features shown**:
- Combined initialization
- Agent lifecycle management
- AI assistance integration
- System-wide configuration
- Comprehensive status monitoring

**Run**:
```bash
python3 integration_example.py
```

## Prerequisites

1. **Environment Configuration**:
```bash
# From repository root
cp .env.example .env
# Edit .env with your settings
```

2. **Python Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Optional - Start Services** (for full functionality):
```bash
# From repository root
docker-compose up -d
```

## Expected Output

All examples run successfully even without services running, but will show warnings for:
- Missing .env configuration
- Services not connected (Langflow, n8n, Qdrant)

With full configuration:
- ✅ All environment checks pass
- ✅ Services connect successfully
- ✅ Agents initialize properly
- ✅ CLI bridges are operational

## Troubleshooting

### "Configuration file not found"

**Solution**: Create `.env` file in repository root:
```bash
cd /path/to/OsMEN
cp .env.example .env
```

### "Missing required configuration: N8N_BASIC_AUTH_PASSWORD"

**Solution**: Edit `.env` and set:
```bash
N8N_BASIC_AUTH_PASSWORD=your-secure-password
WEB_SECRET_KEY=your-secret-key-min-32-chars
```

### "Failed to connect to Langflow/n8n/Qdrant"

**Solution**: Start services:
```bash
docker-compose up -d
```

### "CLI Bridge not operational"

**Solution**: Set API keys in `.env`:
```bash
OPENAI_API_KEY=sk-your-key
GITHUB_TOKEN=ghp_your-token
```

## Learn More

- [Refactoring Guide](../docs/REFACTORING_GUIDE.md) - Complete architecture overview
- [Architecture](../docs/ARCHITECTURE.md) - System design details
- [Setup Guide](../docs/SETUP.md) - Installation instructions

## Contributing

Have an example to share? Submit a PR with:
1. Well-commented code
2. Clear description of what it demonstrates
3. Updated README with usage instructions
