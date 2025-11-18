# API Integration Guide

Complete API documentation for integrating with OsMEN's Gateway and MCP Server.

## Overview

OsMEN provides two main APIs for integration:

1. **Gateway API** (port 8080) - REST API for agent orchestration
2. **MCP Server** (port 8081) - Model Context Protocol for LLM integrations

## Gateway API

### Base URL

```
http://localhost:8080
```

For production, use HTTPS with your domain:
```
https://api.yourdomain.com
```

### Authentication

All API requests require authentication via API key or session token.

**API Key Header:**
```http
X-API-Key: your-api-key-here
```

**Session Token:**
```http
Authorization: Bearer your-jwt-token-here
```

### Generate API Key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Store in `.env`:
```bash
API_KEY=your-generated-key-here
```

## Core Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "services": {
    "langflow": "running",
    "n8n": "running",
    "qdrant": "running",
    "postgres": "running"
  },
  "timestamp": "2024-11-18T10:00:00Z"
}
```

### Agent Execution

#### Execute Agent

```http
POST /api/v1/agents/{agent_name}/execute
Content-Type: application/json
X-API-Key: your-api-key

{
  "input": "Your prompt or task here",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 1000
  },
  "context": {
    "user_id": "user123",
    "session_id": "session456"
  }
}
```

**Response:**
```json
{
  "request_id": "req_abc123",
  "agent": "daily_brief",
  "status": "completed",
  "result": {
    "output": "Agent response here...",
    "metadata": {
      "tokens_used": 250,
      "execution_time_ms": 1500
    }
  },
  "timestamp": "2024-11-18T10:00:00Z"
}
```

**Available Agents:**
- `daily_brief` - Daily briefing agent
- `focus_guardrails` - Productivity management
- `boot_hardening` - Security agent
- `knowledge_management` - Knowledge base queries
- `personal_assistant` - General assistance
- `content_creator` - Content generation
- `email_manager` - Email automation

#### Get Agent Status

```http
GET /api/v1/agents/{agent_name}/status
X-API-Key: your-api-key
```

**Response:**
```json
{
  "agent": "daily_brief",
  "status": "running",
  "enabled": true,
  "last_execution": "2024-11-18T09:00:00Z",
  "total_executions": 42,
  "average_response_time_ms": 1200
}
```

### Workflow Management

#### List Workflows

```http
GET /api/v1/workflows
X-API-Key: your-api-key
```

**Response:**
```json
{
  "workflows": [
    {
      "id": "wf_123",
      "name": "Daily Brief Automation",
      "status": "active",
      "trigger": "cron",
      "schedule": "0 8 * * *"
    }
  ],
  "total": 1
}
```

#### Trigger Workflow

```http
POST /api/v1/workflows/{workflow_id}/trigger
Content-Type: application/json
X-API-Key: your-api-key

{
  "input": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

### Memory Management

#### Store Memory

```http
POST /api/v1/memory/store
Content-Type: application/json
X-API-Key: your-api-key

{
  "collection": "agent_memory",
  "content": "Information to remember",
  "metadata": {
    "source": "user_input",
    "user_id": "user123",
    "tags": ["important", "project"]
  }
}
```

**Response:**
```json
{
  "memory_id": "mem_xyz789",
  "vector_id": 12345,
  "status": "stored"
}
```

#### Query Memory

```http
POST /api/v1/memory/query
Content-Type: application/json
X-API-Key: your-api-key

{
  "query": "What did we discuss about the project?",
  "collection": "agent_memory",
  "limit": 5,
  "filters": {
    "tags": ["project"]
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "Previous conversation about project...",
      "score": 0.92,
      "metadata": {
        "timestamp": "2024-11-18T08:00:00Z",
        "tags": ["important", "project"]
      }
    }
  ],
  "total": 1
}
```

## MCP Server API

The Model Context Protocol (MCP) server provides LLM-specific integrations.

### Base URL

```
http://localhost:8081
```

### Protocol Specification

MCP follows the [Model Context Protocol Specification](https://modelcontextprotocol.io/). 

### List Available Tools

```http
GET /mcp/tools
X-API-Key: your-api-key
```

**Response:**
```json
{
  "tools": [
    {
      "name": "obsidian_search",
      "description": "Search Obsidian vault",
      "parameters": {
        "query": "string",
        "limit": "integer"
      }
    },
    {
      "name": "simplewall_status",
      "description": "Check firewall status",
      "parameters": {}
    }
  ]
}
```

### Execute Tool

```http
POST /mcp/tools/{tool_name}/execute
Content-Type: application/json
X-API-Key: your-api-key

{
  "parameters": {
    "query": "search term",
    "limit": 10
  }
}
```

### Context Injection

```http
POST /mcp/context
Content-Type: application/json
X-API-Key: your-api-key

{
  "context_type": "file",
  "content": {
    "path": "/path/to/file.md",
    "encoding": "utf-8"
  }
}
```

## Rate Limiting

Default rate limits:

| Tier | Requests/Minute | Requests/Hour |
|------|----------------|---------------|
| Free | 60 | 1000 |
| Basic | 300 | 10000 |
| Pro | 1000 | 50000 |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1634567890
```

**Rate Limit Exceeded Response:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Retry after 60 seconds.",
  "retry_after": 60
}
```

## Error Responses

### Error Format

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Missing required parameter: input",
    "details": {
      "parameter": "input",
      "expected_type": "string"
    }
  },
  "request_id": "req_abc123",
  "timestamp": "2024-11-18T10:00:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `invalid_request` | 400 | Malformed request |
| `unauthorized` | 401 | Missing or invalid API key |
| `forbidden` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `rate_limit_exceeded` | 429 | Too many requests |
| `internal_error` | 500 | Server error |
| `service_unavailable` | 503 | Service temporarily unavailable |

## SDK Examples

### Python

```python
import requests

class OsMENClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def execute_agent(self, agent_name, input_text, parameters=None):
        url = f"{self.base_url}/api/v1/agents/{agent_name}/execute"
        payload = {
            "input": input_text,
            "parameters": parameters or {}
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

# Usage
client = OsMENClient("http://localhost:8080", "your-api-key")
result = client.execute_agent("daily_brief", "Generate my morning brief")
print(result["result"]["output"])
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

class OsMENClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async executeAgent(agentName, input, parameters = {}) {
    const response = await axios.post(
      `${this.baseUrl}/api/v1/agents/${agentName}/execute`,
      { input, parameters },
      { headers: { 'X-API-Key': this.apiKey } }
    );
    return response.data;
  }
}

// Usage
const client = new OsMENClient('http://localhost:8080', 'your-api-key');
const result = await client.executeAgent('daily_brief', 'Generate my morning brief');
console.log(result.result.output);
```

### cURL

```bash
# Execute agent
curl -X POST http://localhost:8080/api/v1/agents/daily_brief/execute \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Generate my morning brief",
    "parameters": {
      "temperature": 0.7
    }
  }'

# Check health
curl http://localhost:8080/health

# Query memory
curl -X POST http://localhost:8080/api/v1/memory/query \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "project information",
    "limit": 5
  }'
```

## Webhooks

### Register Webhook

```http
POST /api/v1/webhooks
Content-Type: application/json
X-API-Key: your-api-key

{
  "url": "https://your-domain.com/webhook",
  "events": ["agent.completed", "workflow.triggered"],
  "secret": "webhook-secret-key"
}
```

### Webhook Payload

```json
{
  "event": "agent.completed",
  "data": {
    "agent": "daily_brief",
    "request_id": "req_abc123",
    "status": "completed",
    "result": { ... }
  },
  "timestamp": "2024-11-18T10:00:00Z",
  "signature": "sha256=..."
}
```

### Verify Webhook Signature

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:
```
http://localhost:8080/openapi.json
```

View Swagger UI documentation:
```
http://localhost:8080/docs
```

## Support and Resources

- **API Issues:** [GitHub Issues](https://github.com/dwilli15/OsMEN/issues)
- **API Changes:** See [CHANGELOG.md](../CHANGELOG.md)
- **Rate Limit Increase:** Contact support@osmen.dev

---

**Last Updated:** 2024-11-18  
**API Version:** v1  
**Document Version:** 1.0
