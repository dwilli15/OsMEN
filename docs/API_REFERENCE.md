# OsMEN v3.0 API Reference

> Comprehensive API documentation for OsMEN Gateway endpoints

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Workflows API](#workflows-api)
5. [Runs API](#runs-api)
6. [Streaming API](#streaming-api)
7. [Approvals API](#approvals-api)
8. [Health API](#health-api)
9. [Security API](#security-api)
10. [Error Handling](#error-handling)

---

## Overview

### Base URL

```
http://localhost:8080/api/v1
```

### Content Type

All requests and responses use JSON:

```
Content-Type: application/json
```

### Versioning

The API is versioned via URL path. Current version: `v1`

---

## Authentication

### API Key Authentication

Include your API key in the request header:

```http
Authorization: Bearer <your-api-key>
```

### Example

```bash
curl -X GET "http://localhost:8080/api/v1/runs" \
  -H "Authorization: Bearer sk-osmen-abc123def456"
```

---

## Rate Limiting

### Default Limits

- **100 requests/minute** per client IP
- **10 request burst** capacity
- **5 minute block** after 5 violations

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
Retry-After: 60
```

### Response When Limited

```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Workflows API

### List Workflows

```http
GET /api/v1/workflows
```

**Response:**

```json
{
  "workflows": [
    {
      "id": "daily_brief",
      "name": "Daily Brief",
      "description": "Generate daily briefing with calendar, email, and tasks",
      "version": "3.0.0"
    },
    {
      "id": "research",
      "name": "Research",
      "description": "Deep research on any topic",
      "version": "3.0.0"
    },
    {
      "id": "content",
      "name": "Content Generation",
      "description": "Generate blog posts, social media, newsletters",
      "version": "3.0.0"
    }
  ]
}
```

### Get Workflow Details

```http
GET /api/v1/workflows/{workflow_id}
```

**Response:**

```json
{
  "id": "daily_brief",
  "name": "Daily Brief",
  "description": "Generate daily briefing with calendar, email, and tasks",
  "version": "3.0.0",
  "parameters": {
    "provider": {
      "type": "string",
      "enum": ["openai", "anthropic", "ollama"],
      "default": "ollama"
    },
    "include_calendar": {
      "type": "boolean",
      "default": true
    },
    "include_email": {
      "type": "boolean",
      "default": true
    },
    "include_tasks": {
      "type": "boolean",
      "default": true
    }
  }
}
```

### Execute Workflow

```http
POST /api/v1/workflows/{workflow_id}/run
```

**Request Body:**

```json
{
  "parameters": {
    "provider": "openai",
    "include_calendar": true,
    "include_email": true,
    "include_tasks": true
  },
  "async": true
}
```

**Response:**

```json
{
  "run_id": "run_abc123",
  "workflow_id": "daily_brief",
  "status": "pending",
  "created_at": "2024-11-28T10:00:00Z",
  "stream_url": "/api/v1/stream/runs/run_abc123"
}
```

---

## Runs API

### List Runs

```http
GET /api/v1/runs
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `workflow` | string | Filter by workflow ID |
| `status` | string | Filter by status (pending, running, completed, failed, cancelled) |
| `user` | string | Filter by user ID |
| `since` | datetime | Filter by start date (ISO 8601) |
| `until` | datetime | Filter by end date (ISO 8601) |
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Results per page (default: 20, max: 100) |

**Response:**

```json
{
  "runs": [
    {
      "id": "run_abc123",
      "workflow_id": "daily_brief",
      "status": "completed",
      "created_at": "2024-11-28T10:00:00Z",
      "completed_at": "2024-11-28T10:01:30Z",
      "duration_seconds": 90
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

### Get Run Details

```http
GET /api/v1/runs/{run_id}
```

**Response:**

```json
{
  "id": "run_abc123",
  "workflow_id": "daily_brief",
  "status": "completed",
  "created_at": "2024-11-28T10:00:00Z",
  "completed_at": "2024-11-28T10:01:30Z",
  "parameters": {
    "provider": "openai"
  },
  "steps": [
    {
      "id": "step_1",
      "name": "collect_calendar",
      "status": "completed",
      "started_at": "2024-11-28T10:00:01Z",
      "completed_at": "2024-11-28T10:00:15Z",
      "result": {
        "events_count": 5
      }
    },
    {
      "id": "step_2",
      "name": "collect_email",
      "status": "completed",
      "started_at": "2024-11-28T10:00:15Z",
      "completed_at": "2024-11-28T10:00:30Z",
      "result": {
        "unread_count": 12
      }
    }
  ],
  "result": {
    "summary": "# Daily Brief - November 28, 2024\n\n## Today's Schedule..."
  }
}
```

### Cancel Run

```http
POST /api/v1/runs/{run_id}/cancel
```

**Response:**

```json
{
  "id": "run_abc123",
  "status": "cancelled",
  "cancelled_at": "2024-11-28T10:00:45Z"
}
```

### Retry Run

```http
POST /api/v1/runs/{run_id}/retry
```

**Response:**

```json
{
  "new_run_id": "run_def456",
  "original_run_id": "run_abc123",
  "status": "pending",
  "created_at": "2024-11-28T10:05:00Z"
}
```

### Get Run Statistics

```http
GET /api/v1/runs/stats
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | datetime | Start of period |
| `until` | datetime | End of period |
| `workflow` | string | Filter by workflow |

**Response:**

```json
{
  "total_runs": 1250,
  "completed": 1180,
  "failed": 45,
  "cancelled": 25,
  "success_rate": 0.944,
  "average_duration_seconds": 85.5,
  "by_workflow": {
    "daily_brief": 800,
    "research": 300,
    "content": 150
  }
}
```

### Export Runs

```http
GET /api/v1/runs/export
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Export format: `json` or `csv` |
| `since` | datetime | Filter by start date |
| `until` | datetime | Filter by end date |

**Response:**

Returns file download with appropriate Content-Type.

---

## Streaming API

### Subscribe to Run Events

```http
GET /api/v1/stream/runs/{run_id}
```

**Server-Sent Events (SSE) stream**

**Event Types:**

| Event | Description |
|-------|-------------|
| `run_start` | Run has started |
| `run_step` | Step started or completed |
| `run_tool_call` | Tool was invoked |
| `run_tool_result` | Tool returned result |
| `run_error` | Error occurred |
| `run_approval_required` | Human approval needed |
| `run_complete` | Run finished |
| `heartbeat` | Keep-alive (every 30s) |

**Example Event:**

```
event: run_step
data: {"step_id": "step_1", "name": "collect_calendar", "status": "completed", "result": {"events_count": 5}}

event: run_complete
data: {"run_id": "run_abc123", "status": "completed", "duration_seconds": 90}
```

### JavaScript Client Example

```javascript
const eventSource = new EventSource('/api/v1/stream/runs/run_abc123');

eventSource.addEventListener('run_step', (event) => {
  const data = JSON.parse(event.data);
  console.log(`Step ${data.name}: ${data.status}`);
});

eventSource.addEventListener('run_complete', (event) => {
  const data = JSON.parse(event.data);
  console.log(`Run completed in ${data.duration_seconds}s`);
  eventSource.close();
});
```

---

## Approvals API

### List Pending Approvals

```http
GET /api/v1/approvals/pending
```

**Response:**

```json
{
  "approvals": [
    {
      "id": "approval_abc123",
      "run_id": "run_xyz789",
      "action": "send_email",
      "risk_level": "medium",
      "context": {
        "to": "external@company.com",
        "subject": "Important Update"
      },
      "requested_at": "2024-11-28T10:00:00Z",
      "timeout_at": "2024-11-28T10:05:00Z"
    }
  ]
}
```

### Approve Action

```http
POST /api/v1/approvals/{approval_id}/approve
```

**Request Body:**

```json
{
  "comment": "Approved for external communication"
}
```

**Response:**

```json
{
  "id": "approval_abc123",
  "status": "approved",
  "approved_by": "user_123",
  "approved_at": "2024-11-28T10:02:00Z"
}
```

### Deny Action

```http
POST /api/v1/approvals/{approval_id}/deny
```

**Request Body:**

```json
{
  "reason": "Content needs review before sending"
}
```

**Response:**

```json
{
  "id": "approval_abc123",
  "status": "denied",
  "denied_by": "user_123",
  "denied_at": "2024-11-28T10:02:00Z",
  "reason": "Content needs review before sending"
}
```

### Get Approval History

```http
GET /api/v1/approvals/history
```

**Response:**

```json
{
  "approvals": [
    {
      "id": "approval_abc123",
      "action": "send_email",
      "status": "approved",
      "requested_at": "2024-11-28T10:00:00Z",
      "resolved_at": "2024-11-28T10:02:00Z",
      "resolved_by": "user_123"
    }
  ]
}
```

---

## Health API

### Basic Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-11-28T10:00:00Z",
  "uptime_seconds": 86400,
  "version": "3.0.0"
}
```

### Detailed Health Check

```http
GET /health/deep
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-11-28T10:00:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 5
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 2
    },
    "qdrant": {
      "status": "healthy",
      "collections_count": 3
    },
    "ollama": {
      "status": "healthy",
      "models_available": ["llama3.2", "mistral"]
    }
  },
  "system": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "disk_percent": 60.1
  }
}
```

### Kubernetes Probes

```http
GET /health/live    # Liveness probe
GET /health/ready   # Readiness probe
GET /health/startup # Startup probe
```

### Prometheus Metrics

```http
GET /health/metrics
```

**Response:**

```
# HELP osmen_uptime_seconds Application uptime in seconds
# TYPE osmen_uptime_seconds gauge
osmen_uptime_seconds 86400

# HELP osmen_runs_total Total workflow runs
# TYPE osmen_runs_total counter
osmen_runs_total{workflow="daily_brief",status="completed"} 800
osmen_runs_total{workflow="daily_brief",status="failed"} 25
```

---

## Security API

### Get Security Statistics

```http
GET /api/v1/security/stats
```

**Response:**

```json
{
  "rate_limiter": {
    "total_clients": 50,
    "blocked_ips": [],
    "config": {
      "requests_per_minute": 100,
      "burst_capacity": 10,
      "block_duration": 300
    }
  },
  "ddos_detector": {
    "tracked_ips": 100,
    "recent_detections": [],
    "total_detections": 5
  }
}
```

### Get Blocked IPs

```http
GET /api/v1/security/blocked
```

**Response:**

```json
{
  "blocked_ips": [
    "192.168.1.100",
    "10.0.0.50"
  ]
}
```

### Unblock IP

```http
POST /api/v1/security/unblock/{ip}
```

**Response:**

```json
{
  "ip": "192.168.1.100",
  "unblocked": true
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "provider",
        "message": "Must be one of: openai, anthropic, ollama"
      }
    ]
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limited |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Dependency failure |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Invalid request parameters |
| `AUTHENTICATION_ERROR` | Invalid API key |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `WORKFLOW_ERROR` | Workflow execution failed |
| `PROVIDER_ERROR` | LLM provider error |
| `TIMEOUT_ERROR` | Request timeout |

---

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:

```
GET /api/v1/openapi.json
GET /api/v1/docs  # Swagger UI
```

---

## SDKs and Examples

### Python SDK

```python
from osmen import OsMENClient

client = OsMENClient(api_key="sk-osmen-...")

# Run workflow
run = client.workflows.run("daily_brief", {
    "provider": "openai"
})

# Stream events
for event in run.stream():
    print(f"{event.type}: {event.data}")

# Get result
result = run.wait()
print(result.summary)
```

### JavaScript SDK

```javascript
import { OsMEN } from '@osmen/sdk';

const client = new OsMEN({ apiKey: 'sk-osmen-...' });

// Run workflow
const run = await client.workflows.run('daily_brief', {
  provider: 'openai'
});

// Stream events
run.on('step', (step) => console.log(step));
run.on('complete', (result) => console.log(result.summary));
```

---

## Changelog

### v3.0.0 (2024-11-28)

- Initial API release
- Workflows: daily_brief, research, content
- SSE streaming support
- Approval gating
- Rate limiting
- Security headers
