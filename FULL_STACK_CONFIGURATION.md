# OsMEN Full Stack Configuration Summary

## ✅ Configuration Complete

This document summarizes the full stack configuration completed for OsMEN.

---

## 🔗 Services Running

| Service | Port | Status |
|---------|------|--------|
| **Langflow** | 7860 | ✅ Healthy |
| **n8n** | 5678 | ✅ Healthy |
| **MCP Server** | 8081 | ✅ Running |
| **Librarian** | 8200 | ✅ Healthy |
| **Gateway** | 8080 | ⚠️ Degraded |
| **PostgreSQL** | 5432 | ✅ Healthy |
| **Redis** | 6379 | ✅ Running |
| **ChromaDB** | 8000 | ⚠️ Running |
| **ConvertX** | 3000 | ⚠️ Running |

---

## 📊 Langflow Flows (8 OsMEN flows)

1. **OsMEN Coordinator Agent** - Central routing and orchestration
2. **YOLO-OPS Coordinator** - Autonomous execution agent
3. **Knowledge Management Specialist Agent** - Obsidian integration
4. **Boot Hardening Specialist Agent** - System security
5. **Daily Brief Specialist Agent** - Daily summaries
6. **Focus Guardrails Specialist Agent** - Productivity
7. **Code Assistant with OAuth** - OAuth-enabled coding
8. **Vector Store RAG** - RAG template

---

## ⚡ n8n Workflows (9 workflows, 6 active)

### Active Workflows:
1. **Boot Hardening Trigger** ✅
2. **Daily Brief Trigger** ✅
3. **Knowledge Capture Trigger** ✅
4. **Librarian Document Ingestion** ✅
5. **Librarian RAG Query Webhook** ✅
6. **YOLO-OPS Master Workflow** ✅

### Inactive Workflows:
- ConvertX File Converter
- Course Semester Setup
- Focus Guardrails Monitor

---

## 🔧 MCP Tools Available (40+)

### Categories:
- **System**: execute_command, check_services, get_system_info
- **Knowledge**: obsidian_*, librarian_*
- **Memory**: memory_store, memory_recall, memory_forget
- **Workflow**: workflow_trigger, langflow_run
- **Security**: firewall_*, sysinternals_*
- **Media**: media_*, convert_file, convert_batch
- **Productivity**: task_*, reminder_*, daily_summary
- **Agent**: agent_spawn, agent_status

---

## 🔌 VS Code Integration

### MCP Configuration (`.vscode/settings.json`):
```json
{
  "github.copilot.chat.experimental.mcp.enabled": true,
  "github.copilot.chat.experimental.mcp.servers": {
    "osmen": {
      "command": "python",
      "args": ["-m", "gateway.mcp.server"],
      "cwd": "D:\\OsMEN"
    }
  }
}
```

### How to Use in VS Code:
1. Open Copilot Chat (Ctrl+Shift+I)
2. Use `@osmen` to invoke MCP tools
3. Or ask naturally - tools are auto-selected

---

## 📚 Librarian RAG

- **Status**: Healthy
- **Embedding Model**: dunzhang/stella_en_1.5B_v5
- **Modes**: foundation, lateral, factcheck
- **Documents Indexed**: 0 (ready for indexing)

### To Index Obsidian Vault:
```python
import httpx
response = httpx.post(
    "http://localhost:8200/index/directory",
    json={"path": "./obsidian-vault", "recursive": True}
)
```

---

## 🤖 Local LLM Configuration

### LM Studio (Primary):
- URL: `http://localhost:1234/v1`
- Used for: Complex reasoning, code generation

### Ollama (Secondary):
- URL: `http://localhost:11434`
- Used for: Quick responses, embeddings

### Agent Routing:
| Agent | Provider |
|-------|----------|
| Coordinator | lm_studio |
| Knowledge Specialist | ollama |
| Security Specialist | lm_studio |
| Daily Brief | ollama |

---

## 🎤 Voice/Whisper (Pending)

Configuration created in `config/voice.json`:
- **Model**: small (faster-whisper)
- **Wake Words**: "hey osmen", "osmen", "computer"
- **Input Webhook**: `/webhook/voice-input`

To enable, install: `pip install faster-whisper`

---

## 📁 Configuration Files Created

| File | Description |
|------|-------------|
| `config/orchestration.json` | Full stack orchestration config |
| `config/langflow_routing.json` | Langflow flow routing |
| `config/n8n_webhooks.json` | n8n webhook paths |
| `config/llm_routing.json` | Local LLM provider config |
| `config/voice.json` | Voice/Whisper config |
| `config/vscode_mcp.json` | VS Code MCP settings |
| `.vscode/settings.json` | VS Code workspace settings |

---

## 🚀 Quick Start Commands

### Check Status:
```bash
python check_operational.py
```

### Run Full Stack Setup:
```bash
python scripts/setup_full_stack.py
```

### Trigger n8n Workflow:
```bash
curl -X POST http://localhost:5678/webhook/daily-brief
```

### Query Librarian:
```bash
curl -X POST http://localhost:8200/search \
  -H "Content-Type: application/json" \
  -d '{"query": "your question", "mode": "lateral"}'
```

### List MCP Tools:
```bash
curl http://localhost:8081/tools
```

---

## 🔄 Service URLs

| Service | URL |
|---------|-----|
| Langflow UI | http://localhost:7860 |
| n8n UI | http://localhost:5678 |
| MCP Server | http://localhost:8081 |
| Librarian API | http://localhost:8200 |
| Gateway API | http://localhost:8080 |
| ConvertX UI | http://localhost:3000 |
| ChromaDB | http://localhost:8000 |

---

## ⚠️ Known Issues

1. **Gateway Postgres Auth**: Password authentication failing (uses internal network)
2. **Qdrant**: Replaced by ChromaDB in this configuration
3. **faster-whisper**: Not installed (voice features pending)
4. **Local LLMs**: LM Studio/Ollama need to be started manually

---

## 📋 Next Steps

1. **Start LM Studio** or **Ollama** for local LLM support
2. **Index Obsidian vault** via Librarian API
3. **Test MCP** from VS Code Copilot Chat
4. **Activate remaining n8n workflows** as needed
5. **Install faster-whisper** for voice support

---

*Configuration completed: 2025-12-04*
