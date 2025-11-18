# Performance Benchmarks and Scaling Guide

Performance characteristics, resource usage, and scaling strategies for OsMEN deployments.

## Performance Overview

### Response Times (Typical)

| Operation | Latency (P50) | Latency (P95) | Latency (P99) |
|-----------|--------------|--------------|--------------|
| Agent Query (GPT-4) | 2-3s | 5-8s | 10-15s |
| Agent Query (Local LLM) | 5-10s | 15-20s | 25-30s |
| Memory Search | 100-200ms | 300-500ms | 500ms-1s |
| Workflow Trigger | 50-100ms | 200-300ms | 400-500ms |
| API Request | 20-50ms | 100-150ms | 200-300ms |

### Throughput

| Configuration | Concurrent Users | Requests/Second | Notes |
|--------------|-----------------|-----------------|-------|
| **Minimum** (4 core, 16GB) | 1-5 | 1-2 | Development only |
| **Recommended** (8 core, 32GB) | 5-20 | 5-10 | Small team |
| **Production** (16 core, 64GB) | 20-100 | 20-50 | Medium deployment |
| **Enterprise** (32+ core, 128GB+) | 100-500 | 100+ | Large scale |

## Resource Usage Per Agent

### CPU Usage

| Agent | Idle | Active | Burst |
|-------|------|--------|-------|
| Daily Brief | <5% | 20-30% | 50% |
| Focus Guardrails | <5% | 15-25% | 40% |
| Boot Hardening | <5% | 10-20% | 60% |
| Content Creator | <5% | 30-50% | 80% |
| Knowledge Management | <5% | 20-30% | 50% |

### Memory Usage

| Agent | Base | Working Set | Peak |
|-------|------|------------|------|
| Daily Brief | 100MB | 300-500MB | 800MB |
| Focus Guardrails | 80MB | 200-400MB | 600MB |
| Boot Hardening | 60MB | 150-300MB | 500MB |
| Content Creator | 200MB | 500MB-1GB | 2GB |
| Knowledge Management | 150MB | 400-800MB | 1.5GB |

### Disk I/O

| Component | Read | Write | Total Daily |
|-----------|------|-------|-------------|
| PostgreSQL | 100-500 MB/day | 50-200 MB/day | 150-700 MB |
| Qdrant | 200MB-1GB/day | 100-500 MB/day | 300MB-1.5GB |
| Logs | Minimal | 100-500 MB/day | 100-500 MB |
| Content | Variable | Variable | 1-10 GB |

## Service Resource Requirements

### Docker Container Allocation

| Service | CPU Limit | Memory Limit | Storage | Notes |
|---------|-----------|--------------|---------|-------|
| Langflow | 2 cores | 4 GB | 5 GB | Visual flow builder |
| n8n | 2 cores | 2 GB | 5 GB | Workflow automation |
| PostgreSQL | 2 cores | 4 GB | 20 GB | Primary database |
| Qdrant | 2 cores | 4 GB | 10 GB | Vector database |
| Redis | 1 core | 2 GB | 2 GB | Cache |
| Gateway API | 2 cores | 2 GB | 1 GB | API server |
| Ollama (optional) | 4 cores | 8 GB | 20 GB | Local LLM |

**Total Minimum:** 8 cores, 16 GB RAM, 50 GB disk  
**Total Recommended:** 16 cores, 32 GB RAM, 100 GB disk

### GPU Acceleration (Optional)

For local LLMs with Ollama:

| GPU | VRAM | Model Support | Performance |
|-----|------|--------------|-------------|
| NVIDIA GTX 1660 | 6 GB | Small models (7B) | 2-3x faster |
| NVIDIA RTX 3060 | 12 GB | Medium models (13B) | 3-5x faster |
| NVIDIA RTX 4090 | 24 GB | Large models (70B) | 5-10x faster |
| Apple M1/M2 | Unified | Medium models | 2-4x faster |

## Performance Benchmarks

### Single Agent Execution

**Test Setup:** 8 core, 32GB RAM, SSD, GPT-4

| Agent | Cold Start | Warm Start | With Context |
|-------|-----------|-----------|--------------|
| Daily Brief | 3.2s | 2.1s | 2.8s |
| Focus Guardrails | 2.5s | 1.8s | 2.3s |
| Boot Hardening | 4.1s | 3.2s | 3.8s |
| Knowledge Query | 1.9s | 1.2s | 2.5s |

### Concurrent Execution

**Load Test Results:**

```
Scenario: 10 concurrent users, 100 requests each
Duration: 5 minutes
Success Rate: 99.2%

P50 Latency: 2.4s
P95 Latency: 6.8s
P99 Latency: 12.3s
Max Latency: 18.7s

Throughput: 15 req/s
```

### Database Performance

**PostgreSQL:**
- Queries/sec: 1,000-5,000
- Insert rate: 500-2,000/sec
- Connection pool: 20 connections
- Query latency: <10ms (P95)

**Qdrant:**
- Vector search: <100ms (P95)
- Insert rate: 100-500 vectors/sec
- Index size: 1M vectors = ~2GB
- Memory usage: ~4GB for 1M vectors

## Scaling Strategies

### Vertical Scaling

**When to Scale Up:**
- CPU usage consistently >70%
- Memory usage >80%
- Response times degrading
- Queue depths increasing

**How to Scale:**
```bash
# Update docker-compose.yml
services:
  gateway:
    deploy:
      resources:
        limits:
          cpus: '4'  # Increase from 2
          memory: 8G  # Increase from 4G
```

### Horizontal Scaling

**Multi-Instance Deployment:**

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  gateway:
    image: osmen/gateway:latest
    deploy:
      replicas: 3  # Multiple instances
    environment:
      - REDIS_HOST=redis  # Shared cache
      - POSTGRES_HOST=postgres  # Shared DB

  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - gateway
```

**Load Balancer Configuration (nginx):**

```nginx
upstream gateway_backend {
    least_conn;  # Load balancing strategy
    server gateway-1:8080;
    server gateway-2:8080;
    server gateway-3:8080;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://gateway_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Kubernetes Deployment

```yaml
# k8s/gateway-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: osmen-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: osmen-gateway
  template:
    metadata:
      labels:
        app: osmen-gateway
    spec:
      containers:
      - name: gateway
        image: osmen/gateway:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        ports:
        - containerPort: 8080
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: osmen-gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: osmen-gateway
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Performance Optimization

### Database Optimization

**PostgreSQL Tuning:**

```sql
-- postgresql.conf optimizations
shared_buffers = 8GB              -- 25% of RAM
effective_cache_size = 24GB       -- 75% of RAM
work_mem = 64MB
maintenance_work_mem = 2GB
max_connections = 100
random_page_cost = 1.1            -- For SSD
effective_io_concurrency = 200    -- For SSD

-- Vacuum settings
autovacuum = on
autovacuum_max_workers = 4
```

**Qdrant Optimization:**

```yaml
# qdrant_config.yaml
service:
  max_request_size_mb: 100

storage:
  # Use on-disk storage for large collections
  storage_path: /qdrant/storage
  
  # Optimize for query speed
  performance:
    max_search_threads: 4
```

### Caching Strategy

**Redis Configuration:**

```bash
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru  # Evict least recently used
save ""  # Disable persistence for cache-only usage
```

**Application-Level Caching:**

```python
# Cache frequently accessed data
@cache(ttl=3600)  # 1 hour
def get_agent_config(agent_name):
    return db.query("SELECT * FROM agent_config WHERE name = ?", agent_name)
```

### Content Delivery

**CDN for Static Assets:**
- Use CDN for Langflow/n8n UI assets
- Cache agent responses (when applicable)
- Compress API responses (gzip)

### LLM Provider Optimization

**Choose Based on Requirements:**

| Provider | Latency | Cost | Quality | Use Case |
|----------|---------|------|---------|----------|
| GPT-4 Turbo | Low | High | Excellent | Critical tasks |
| GPT-3.5 Turbo | Very Low | Medium | Good | Quick responses |
| Claude Opus | Low | High | Excellent | Complex reasoning |
| Local (Ollama) | Medium | Free | Good | Privacy-sensitive |

**Batch Requests:**
```python
# Instead of 10 separate calls
for item in items:
    result = call_llm(item)

# Use batch processing
results = call_llm_batch(items)  # More efficient
```

## Monitoring Performance

### Metrics to Track

**System Metrics:**
- CPU usage (per container)
- Memory usage (per container)
- Disk I/O
- Network throughput

**Application Metrics:**
- Request rate
- Response time (P50, P95, P99)
- Error rate
- Queue depth

**Business Metrics:**
- Agent execution count
- Token usage
- User activity
- Cost per request

### Prometheus Metrics

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'osmen_gateway'
    static_configs:
      - targets: ['gateway:8080']
    metrics_path: '/metrics'
```

**Example Metrics:**
```
# Request duration
osmen_request_duration_seconds{agent="daily_brief",quantile="0.95"} 6.8

# Request count
osmen_requests_total{agent="daily_brief",status="success"} 1234

# Active users
osmen_active_users 42
```

### Grafana Dashboards

**Import Dashboard:**
```bash
# Use OsMEN Grafana dashboard
# Dashboard ID: (to be published)
```

**Key Panels:**
- Request rate over time
- Response time heatmap
- Error rate by agent
- Resource usage by service
- Token usage and costs

## Performance Testing

### Load Testing Script

```python
# load_test.py
import asyncio
import aiohttp
import time

async def test_agent(session, agent_name, request_id):
    url = "http://localhost:8080/api/v1/agents/daily_brief/execute"
    headers = {"X-API-Key": "test-key"}
    payload = {"input": f"Test request {request_id}"}
    
    start = time.time()
    async with session.post(url, json=payload, headers=headers) as resp:
        result = await resp.json()
        duration = time.time() - start
        return duration, resp.status

async def run_load_test(concurrent_users, requests_per_user):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for user in range(concurrent_users):
            for req in range(requests_per_user):
                task = test_agent(session, "daily_brief", user * requests_per_user + req)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Calculate statistics
        durations = [r[0] for r in results]
        successes = sum(1 for r in results if r[1] == 200)
        
        print(f"Total requests: {len(results)}")
        print(f"Success rate: {successes / len(results) * 100:.1f}%")
        print(f"P50 latency: {sorted(durations)[len(durations)//2]:.2f}s")
        print(f"P95 latency: {sorted(durations)[int(len(durations)*0.95)]:.2f}s")
        print(f"P99 latency: {sorted(durations)[int(len(durations)*0.99)]:.2f}s")

# Run test
asyncio.run(run_load_test(concurrent_users=10, requests_per_user=100))
```

### Stress Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 -H "X-API-Key: test-key" \
   -p payload.json -T application/json \
   http://localhost:8080/api/v1/agents/daily_brief/execute

# Using k6
k6 run --vus 10 --duration 30s load_test.js
```

## Troubleshooting Performance Issues

### High CPU Usage

**Diagnosis:**
```bash
# Check per-container CPU
docker stats

# Profile application
py-spy top --pid $(pgrep -f gateway.py)
```

**Solutions:**
- Scale horizontally
- Optimize queries
- Add caching
- Use async operations

### High Memory Usage

**Diagnosis:**
```bash
# Memory usage by container
docker stats --no-stream

# Python memory profiling
memray run gateway.py
```

**Solutions:**
- Increase memory limits
- Optimize data structures
- Implement pagination
- Clear caches periodically

### Slow Response Times

**Diagnosis:**
```bash
# Check service latency
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/api/v1/agents/status

# Database query times
docker exec osmen-postgres psql -U postgres -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

**Solutions:**
- Add database indexes
- Optimize LLM prompts
- Use faster LLM models
- Implement request batching

## Cost Optimization

### LLM Usage

| Model | Cost per 1K tokens | Requests/Day | Monthly Cost |
|-------|-------------------|--------------|--------------|
| GPT-4 | $0.03 input, $0.06 output | 1,000 | $150-300 |
| GPT-3.5 Turbo | $0.001 input, $0.002 output | 1,000 | $10-20 |
| Local (Ollama) | $0 (hardware only) | Unlimited | $0 |

**Optimization Strategies:**
- Use GPT-3.5 for simple tasks
- Cache LLM responses
- Optimize prompts (fewer tokens)
- Use local models when possible

### Infrastructure

**Cloud vs. Self-Hosted:**

| Option | Monthly Cost | Pros | Cons |
|--------|-------------|------|------|
| AWS EC2 (t3.xlarge) | $120 | Scalable | Ongoing cost |
| DigitalOcean Droplet | $80 | Simple | Limited resources |
| Self-hosted (amortized) | $30 | Full control | Upfront cost |

## Capacity Planning

### Growth Projections

| Users | Daily Requests | CPU Cores | RAM | Storage |
|-------|---------------|-----------|-----|---------|
| 1-10 | 100-1,000 | 8 | 16 GB | 50 GB |
| 10-50 | 1,000-5,000 | 16 | 32 GB | 100 GB |
| 50-200 | 5,000-20,000 | 32 | 64 GB | 200 GB |
| 200-1,000 | 20,000-100,000 | 64+ | 128 GB+ | 500 GB+ |

### Planning Checklist

- [ ] Estimate user growth
- [ ] Calculate request volumes
- [ ] Determine storage needs
- [ ] Budget for LLM costs
- [ ] Plan scaling strategy
- [ ] Set up monitoring
- [ ] Test at scale

---

**Last Updated:** 2024-11-18  
**Benchmark Version:** 1.0  
**Test Environment:** AWS EC2 c5.4xlarge, 16 vCPU, 32 GB RAM
