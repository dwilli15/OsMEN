# LLM Agent Integration Guide

## Overview

OsMEN integrates with production LLM agents following this priority order:

1. **Production Cloud Agents** (Primary)
   - OpenAI (Codex, GPT-4)
   - GitHub Copilot
   - Amazon Q
   - Anthropic Claude

2. **Local LLM Runtime** (Secondary)
   - LM Studio (Primary local option)
   - Ollama (Secondary local option)

## Agent Gateway

The Agent Gateway (`gateway/gateway.py`) provides a unified API for all agents:

- **Port**: 8080
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health
- **List Agents**: http://localhost:8080/agents

## Setup by Agent

### 1. OpenAI (Codex, GPT-4) - PRIMARY

**Setup:**
```bash
# Get API key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-..."
```

**In .env:**
```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4
```

**Usage:**
```bash
curl -X POST http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to reverse a string",
    "agent": "openai",
    "model": "gpt-4"
  }'
```

**Models Available:**
- `gpt-4` - Most capable
- `gpt-4-turbo-preview` - Faster, more affordable
- `gpt-3.5-turbo` - Fast, cost-effective

### 2. GitHub Copilot

**Setup via VSCode:**

1. Install GitHub Copilot extension in VSCode
2. Sign in with GitHub account
3. Copilot works automatically in VSCode

**Setup via CLI:**

```bash
# Install GitHub CLI
gh extension install github/gh-copilot

# Authenticate
gh auth login

# Use Copilot CLI
gh copilot suggest "write a bash script to backup files"
gh copilot explain "docker-compose up -d"
```

**API Integration:**

```bash
# Get GitHub token
GITHUB_TOKEN=ghp_your_token_here
```

**In .env:**
```bash
GITHUB_TOKEN=ghp_your_token_here
```

### 3. Amazon Q

**Setup via AWS CLI:**

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
```

**In .env:**
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

**Usage via CLI:**
```bash
# Amazon Q Developer CLI
aws q chat --message "How do I create an S3 bucket?"
```

**Web UI:**
- AWS Console: https://console.aws.amazon.com/q/
- VSCode Extension: AWS Toolkit

### 4. Anthropic Claude

**Setup:**
```bash
# Get API key from: https://console.anthropic.com/
export ANTHROPIC_API_KEY="sk-ant-..."
```

**In .env:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229
```

**Usage:**
```bash
curl -X POST http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain async/await in Python",
    "agent": "claude",
    "model": "claude-3-opus-20240229"
  }'
```

**Models Available:**
- `claude-3-opus-20240229` - Most capable
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-haiku-20240307` - Fast

### 5. LM Studio - PRIMARY LOCAL OPTION

**Setup:**

1. **Download LM Studio**
   - Visit: https://lmstudio.ai/
   - Download for your OS (Windows/Mac/Linux)
   - Install and launch

2. **Download Models**
   - Open LM Studio
   - Go to "Discover" tab
   - Download models:
     - `TheBloke/Mistral-7B-Instruct-v0.2-GGUF` (recommended)
     - `TheBloke/CodeLlama-13B-Instruct-GGUF` (for code)
     - `TheBloke/deepseek-coder-6.7b-instruct-GGUF` (for code)

3. **Enable API Server**
   - Click "Local Server" tab
   - Select a model
   - Click "Start Server"
   - Default URL: http://localhost:1234

**In .env:**
```bash
LM_STUDIO_URL=http://host.docker.internal:1234/v1
LM_STUDIO_MODEL=mistral-7b-instruct
```

**Usage:**
```bash
curl -X POST http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to parse JSON",
    "agent": "lmstudio"
  }'
```

**Advantages:**
- ✅ Runs locally (privacy)
- ✅ No API costs
- ✅ Works offline
- ✅ OpenAI-compatible API
- ✅ Easy to use GUI

### 6. Ollama - SECONDARY LOCAL OPTION

**Setup:**

```bash
# Start with Ollama profile
docker-compose --profile ollama up -d

# Pull models
docker exec -it osmen-ollama ollama pull llama2
docker exec -it osmen-ollama ollama pull mistral
docker exec -it osmen-ollama ollama pull codellama
```

**In .env:**
```bash
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama2
```

**Usage:**
```bash
curl -X POST http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain Docker volumes",
    "agent": "ollama",
    "model": "mistral"
  }'
```

## VSCode Integration

### Setup Extensions

Install these VSCode extensions:

1. **GitHub Copilot**
   - Extension ID: `GitHub.copilot`
   - Provides inline code suggestions

2. **AWS Toolkit**
   - Extension ID: `amazonwebservices.aws-toolkit-vscode`
   - Includes Amazon Q integration

3. **Continue** (Open-source Copilot alternative)
   - Extension ID: `Continue.continue`
   - Works with OpenAI, Claude, LM Studio, Ollama

### Configure Continue Extension

Create `.vscode/continue.json`:

```json
{
  "models": [
    {
      "title": "GPT-4",
      "provider": "openai",
      "model": "gpt-4",
      "apiKey": "${OPENAI_API_KEY}"
    },
    {
      "title": "Claude",
      "provider": "anthropic",
      "model": "claude-3-opus-20240229",
      "apiKey": "${ANTHROPIC_API_KEY}"
    },
    {
      "title": "LM Studio",
      "provider": "openai",
      "model": "local-model",
      "apiBase": "http://localhost:1234/v1"
    },
    {
      "title": "Ollama",
      "provider": "ollama",
      "model": "mistral",
      "apiBase": "http://localhost:11434"
    }
  ],
  "slashCommands": [
    {
      "name": "edit",
      "description": "Edit selected code"
    },
    {
      "name": "comment",
      "description": "Add comments to code"
    },
    {
      "name": "test",
      "description": "Generate unit tests"
    }
  ]
}
```

## Cline Integration

**Cline** is an autonomous coding agent for VSCode.

### Setup Cline

1. **Install Extension**
   ```bash
   # In VSCode, search for "Cline" and install
   # Extension ID: saoudrizwan.claude-dev
   ```

2. **Configure API Keys**
   - Open Command Palette (Ctrl+Shift+P)
   - Type "Cline: Set API Key"
   - Enter your OpenAI or Anthropic API key

3. **Usage**
   - Open Cline panel (sidebar)
   - Describe what you want to build
   - Cline will autonomously write and test code

### Integrate Cline with OsMEN

Configure Cline to use OsMEN's Agent Gateway:

```json
{
  "apiProvider": "openai",
  "apiKey": "${OPENAI_API_KEY}",
  "model": "gpt-4",
  "maxTokens": 4096,
  "temperature": 0.7
}
```

## CLI Tools Integration

### GitHub CLI with Copilot

```bash
# Install
gh extension install github/gh-copilot

# Suggest commands
gh copilot suggest "create a docker network"

# Explain commands
gh copilot explain "docker-compose up -d"
```

### AWS CLI with Amazon Q

```bash
# Interactive chat
aws q chat

# Query
aws q query "How do I secure an S3 bucket?"
```

### Aider (AI Pair Programming)

```bash
# Install
pip install aider-chat

# Use with OpenAI
aider --openai-api-key $OPENAI_API_KEY

# Use with Claude
aider --anthropic-api-key $ANTHROPIC_API_KEY

# Use with LM Studio
aider --openai-api-base http://localhost:1234/v1
```

## Agent Priority and Fallback

The Agent Gateway uses this priority order:

1. **OpenAI** - If API key configured
2. **GitHub Copilot** - If GitHub token configured
3. **Amazon Q** - If AWS credentials configured
4. **Claude** - If Anthropic key configured
5. **LM Studio** - If running on host
6. **Ollama** - If started with --profile ollama

**Fallback Strategy:**
- If primary agent fails, gateway tries next available
- For offline work, use LM Studio or Ollama
- For privacy-sensitive work, use local-only agents

## Testing Agent Gateway

```bash
# Start gateway
docker-compose up -d agent-gateway

# Check available agents
curl http://localhost:8080/agents

# Test OpenAI
curl -X POST http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Say hello",
    "agent": "openai"
  }'

# Test LM Studio
curl -X POST http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Say hello",
    "agent": "lmstudio"
  }'
```

## Best Practices

### When to Use Each Agent

**OpenAI GPT-4:**
- Complex reasoning tasks
- Production code generation
- Critical decisions

**GitHub Copilot:**
- Real-time code completion in VSCode
- Refactoring assistance
- Quick code snippets

**Amazon Q:**
- AWS-specific tasks
- Infrastructure as Code
- AWS best practices

**Anthropic Claude:**
- Long context analysis
- Code review
- Detailed explanations

**LM Studio:**
- Privacy-sensitive work
- Offline development
- Cost-conscious development

**Ollama:**
- Experimentation
- Testing different models
- Resource-constrained environments

### Cost Optimization

1. Use **LM Studio** for development and testing
2. Use **OpenAI GPT-3.5-turbo** for simple tasks
3. Use **GPT-4** only for complex reasoning
4. Use **GitHub Copilot** for code completion (flat rate)
5. Cache responses where possible

### Privacy Considerations

For sensitive code:
- Use **LM Studio** (runs locally)
- Use **Ollama** (runs locally)
- Avoid cloud agents

For general development:
- Cloud agents are fine
- Follow your organization's policies

## Troubleshooting

### LM Studio Not Connecting

```bash
# Check if LM Studio server is running
curl http://localhost:1234/v1/models

# If fails, start LM Studio and enable "Local Server"
```

### Ollama Not Responding

```bash
# Start with Ollama profile
docker-compose --profile ollama up -d

# Check if running
docker ps | grep ollama

# Pull models
docker exec -it osmen-ollama ollama pull llama2
```

### API Key Issues

```bash
# Check environment variables
docker-compose exec agent-gateway env | grep API_KEY

# Restart gateway after changing .env
docker-compose restart agent-gateway
```

## Further Reading

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [GitHub Copilot Documentation](https://docs.github.com/copilot)
- [Amazon Q Documentation](https://aws.amazon.com/q/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [LM Studio Documentation](https://lmstudio.ai/docs)
- [Ollama Documentation](https://ollama.ai/)
