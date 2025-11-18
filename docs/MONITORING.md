# Monitoring and Observability Guide

Complete guide for monitoring, logging, and observability in OsMEN production deployments.

## Monitoring Stack Recommendations

### Recommended Stack

- **Metrics:** Prometheus + Grafana
- **Logs:** Loki or ELK Stack
- **Traces:** Jaeger or Zipkin
- **Alerts:** Alertmanager
- **Uptime:** UptimeRobot or Pingdom

## Prometheus Metrics

### Installing Prometheus

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false

volumes:
  prometheus_data:
  grafana_data:
```

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'osmen_gateway'
    static_configs:
      - targets: ['gateway:8080']
    metrics_path: '/metrics'

  - job_name: 'osmen_postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'osmen_redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'docker'
    static_configs:
      - targets: ['cadvisor:8080']
```

### Key Metrics to Monitor

**Application Metrics:**
```
# Request rate
osmen_requests_total
osmen_requests_per_second

# Response time
osmen_request_duration_seconds

# Error rate
osmen_errors_total
osmen_error_rate

# Agent executions
osmen_agent_executions_total
osmen_agent_duration_seconds

# Active users
osmen_active_users

# Token usage
osmen_tokens_used_total
osmen_llm_cost_dollars
```

**System Metrics:**
```
# CPU
container_cpu_usage_seconds_total

# Memory
container_memory_usage_bytes
container_memory_working_set_bytes

# Disk
container_fs_usage_bytes
container_fs_writes_total

# Network
container_network_receive_bytes_total
container_network_transmit_bytes_total
```

## Grafana Dashboards

### Import OsMEN Dashboard

```bash
# Dashboard ID: (to be published on grafana.com)
# Or import from JSON:
curl -o osmen-dashboard.json https://raw.githubusercontent.com/dwilli15/OsMEN/main/monitoring/grafana-dashboard.json
```

### Key Dashboard Panels

1. **Overview**
   - Total requests/sec
   - Error rate
   - Average response time
   - Active users

2. **Agent Performance**
   - Executions per agent
   - Average execution time
   - Success rate by agent
   - Token usage by agent

3. **System Health**
   - CPU usage by service
   - Memory usage by service
   - Disk I/O
   - Network throughput

4. **Database**
   - Query rate
   - Connection pool usage
   - Slow queries
   - Cache hit rate

5. **Costs**
   - LLM API costs
   - Token usage trends
   - Cost per agent
   - Daily/monthly projections

## Logging

### Centralized Logging with Loki

```yaml
# docker-compose.logging.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
```

### Loki Configuration

```yaml
# loki-config.yml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks
```

### Log Levels

```bash
# In .env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Service-specific levels
GATEWAY_LOG_LEVEL=INFO
AGENT_LOG_LEVEL=DEBUG
```

### Log Format

```json
{
  "timestamp": "2024-11-18T10:00:00Z",
  "level": "INFO",
  "service": "gateway",
  "request_id": "req_abc123",
  "user_id": "user123",
  "agent": "daily_brief",
  "duration_ms": 2341,
  "status": "success",
  "message": "Agent execution completed"
}
```

### Querying Logs

```logql
# Loki queries

# All errors
{service="gateway"} |= "ERROR"

# Specific agent logs
{service="gateway"} | json | agent="daily_brief"

# Slow requests (>5s)
{service="gateway"} | json | duration_ms > 5000

# Error rate
rate({service="gateway"} |= "ERROR" [5m])
```

## Distributed Tracing

### Jaeger Setup

```yaml
# docker-compose.tracing.yml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "5775:5775/udp"
      - "6831:6831/udp"
      - "6832:6832/udp"
      - "5778:5778"
      - "16686:16686"
      - "14268:14268"
      - "14250:14250"
      - "9411:9411"
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
```

### Instrument Code

```python
# Add to gateway.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Use in code
@tracer.start_as_current_span("execute_agent")
def execute_agent(agent_name, input_text):
    span = trace.get_current_span()
    span.set_attribute("agent.name", agent_name)
    # ... rest of code
```

## Alerting

### Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'pagerduty'
  - match:
      severity: warning
    receiver: 'slack'

receivers:
- name: 'default'
  email_configs:
  - to: 'alerts@osmen.dev'

- name: 'slack'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    channel: '#osmen-alerts'

- name: 'pagerduty'
  pagerduty_configs:
  - service_key: 'your-pagerduty-key'
```

### Alert Rules

```yaml
# prometheus-alerts.yml
groups:
- name: osmen_alerts
  rules:
  # High error rate
  - alert: HighErrorRate
    expr: rate(osmen_errors_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors/sec"

  # Service down
  - alert: ServiceDown
    expr: up{job="osmen_gateway"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "OsMEN Gateway is down"

  # High response time
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(osmen_request_duration_seconds_bucket[5m])) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time"
      description: "P95 latency is {{ $value }}s"

  # High memory usage
  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes{name="osmen-gateway"} / container_spec_memory_limit_bytes{name="osmen-gateway"} > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"

  # Database connection pool exhausted
  - alert: DatabasePoolExhausted
    expr: pg_stat_activity_count > 90
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Database connection pool nearly exhausted"
```

## Health Checks

### Endpoint

```python
# Gateway health endpoint
@app.get("/health")
async def health_check():
    checks = {
        "status": "healthy",
        "services": {
            "postgres": check_postgres(),
            "redis": check_redis(),
            "qdrant": check_qdrant(),
            "langflow": check_langflow(),
            "n8n": check_n8n()
        },
        "timestamp": datetime.now().isoformat()
    }
    
    all_healthy = all(s == "healthy" for s in checks["services"].values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(content=checks, status_code=status_code)
```

### Kubernetes Probes

```yaml
# k8s deployment with probes
spec:
  containers:
  - name: gateway
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
      
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
```

## Performance Monitoring

### Application Performance Monitoring (APM)

**Options:**
- Self-hosted: Grafana Tempo, Elastic APM
- Cloud: New Relic, Datadog, AppDynamics

**Integration Example (New Relic):**

```python
# Install: pip install newrelic
import newrelic.agent

newrelic.agent.initialize('newrelic.ini')

@newrelic.agent.background_task()
def process_agent_request(input):
    # Your code here
    pass
```

## Monitoring Checklist

### Daily Checks
- [ ] Check Grafana dashboards
- [ ] Review error logs
- [ ] Monitor response times
- [ ] Check disk space
- [ ] Review alert notifications

### Weekly Checks
- [ ] Analyze performance trends
- [ ] Review slow queries
- [ ] Check backup completion
- [ ] Update monitoring thresholds
- [ ] Review cost metrics

### Monthly Checks
- [ ] Capacity planning review
- [ ] Update dashboards
- [ ] Review and update alerts
- [ ] Security audit logs
- [ ] Performance optimization review

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)

---

**Last Updated:** 2024-11-18  
**Monitoring Version:** 1.0  
**Review Cycle:** Monthly
