# AGENT BETA TASKS - Infrastructure & Security
**Agent:** Beta  
**Branch:** `agent-beta-infrastructure`  
**Focus:** Production infrastructure, security hardening, and operational excellence  
**Tasks:** 48 (16 per 2-day sprint)  
**Timeline:** 6 days (144 hours)

---

## 🎯 AGENT BETA MISSION

You are responsible for making OsMEN production-ready by hardening infrastructure, securing services, implementing monitoring, and ensuring operational excellence. Every service must be deployable, observable, recoverable, and secure without manual intervention.

### Core Responsibilities
- **Container orchestration:** Docker, Compose, production deployment
- **Security:** AuthN/AuthZ, secrets, TLS, rate limiting, compliance
- **Data plane:** PostgreSQL, Qdrant, Redis optimization
- **Observability:** Health checks, logging, monitoring, alerting
- **CI/CD:** Automated testing, security scanning, deployment pipelines
- **Operations:** Backup/restore, disaster recovery, runbooks

---

## 📅 DAY 1-2: FOUNDATION (Hour 0-48)
**Goal:** Secure foundation with hardened containers and baseline security  
**Deliverables:** Production docker-compose, secrets management, health checks, basic CI/CD

### Day 1: Container & Security Foundation (Hour 0-24)

#### **B1.1** Production Docker Compose Hardening (3h)
**File:** `docker-compose.yml`  
**Objective:** Harden existing docker-compose.yml for production use

- [ ] Add health checks to all services (HTTP, TCP, or exec-based)
- [ ] Configure restart policies (`restart: unless-stopped` → `on-failure:3`)
- [ ] Set resource limits (memory, CPU) for all containers
- [ ] Remove `privileged: true` flags if present
- [ ] Use read-only root filesystems where possible (`read_only: true`)
- [ ] Add `security_opt` for AppArmor/SELinux
- [ ] Configure logging drivers (json-file with rotation)
- [ ] Test: `docker compose config` validates, all services start healthy

**Validation:**
```powershell
docker compose config
docker compose up -d
docker compose ps  # All services healthy
```

---

#### **B1.2** Create docker-compose.prod.yml (3h)
**File:** `docker-compose.prod.yml` (NEW)  
**Objective:** Production overrides with security-first configuration

- [ ] Create production override file with hardened settings
- [ ] Use specific image tags (no `:latest`)
- [ ] Bind to 127.0.0.1 instead of 0.0.0.0 for internal services
- [ ] Add TLS/SSL volume mounts for certificates
- [ ] Configure environment-specific networks (isolated backend)
- [ ] Set production environment variables
- [ ] Document rationale in header comments
- [ ] Test: Production stack starts with overrides

**Example structure:**
```yaml
# docker-compose.prod.yml
# Production overrides for OsMEN infrastructure
# Usage: docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

services:
  postgres:
    image: postgres:15-alpine  # Pinned version
    ports:
      - "127.0.0.1:5432:5432"  # Localhost only
    restart: on-failure:3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

**Validation:**
```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
```

---

#### **B1.3** Implement Secrets Management (3h)
**Files:** `.env.example`, `scripts/automation/validate_secrets.py` (NEW)  
**Objective:** Ensure no secrets in code, validate environment configuration

- [ ] Audit all services for hardcoded secrets → replace with env vars
- [ ] Enhance `.env.example` with all required secrets (use placeholders)
- [ ] Create `scripts/automation/validate_secrets.py` - check for exposed secrets
- [ ] Add secret validation to Makefile (`make validate-secrets`)
- [ ] Update `.gitignore` to exclude `.env`, `*.key`, `*.pem`
- [ ] Document secret rotation process in `docs/PRODUCTION_DEPLOYMENT.md`
- [ ] Test: No secrets in code, validation script catches issues

**Validation script outline:**
```python
# scripts/automation/validate_secrets.py
def check_env_file():
    """Ensure .env exists and has no defaults"""
    pass

def scan_for_hardcoded_secrets():
    """Scan codebase for API keys, passwords"""
    pass

def validate_docker_compose():
    """Check docker-compose doesn't have hardcoded secrets"""
    pass
```

**Validation:**
```powershell
python scripts/automation/validate_secrets.py
make validate-secrets
```

---

#### **B1.4** Add Health Check Endpoints (3h)
**Files:** `gateway/gateway.py`, `gateway/mcp_server.py`, `web/main.py`  
**Objective:** Comprehensive health checks for all services

- [ ] Enhance `/health` endpoint in gateway.py (check dependencies)
- [ ] Add `/readiness` endpoint (ready to serve traffic)
- [ ] Add `/liveness` endpoint (process alive)
- [ ] Implement dependency checks (PostgreSQL, Qdrant, Redis)
- [ ] Add version info to health response
- [ ] Document health check format in API docs
- [ ] Test: All endpoints return proper status codes

**Enhanced health response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-12T10:00:00Z",
  "dependencies": {
    "postgres": "healthy",
    "qdrant": "healthy",
    "redis": "healthy"
  }
}
```

**Validation:**
```powershell
curl http://localhost:8080/health
curl http://localhost:8080/readiness
curl http://localhost:8080/liveness
```

---

#### **B1.5** Configure Logging Infrastructure (3h)
**Files:** `docker-compose.yml`, `gateway/gateway.py`, `web/main.py`  
**Objective:** Centralized, structured logging with rotation

- [ ] Configure Docker logging driver (json-file with max-size, max-file)
- [ ] Add structured logging to gateway.py (JSON format)
- [ ] Add correlation IDs to all log entries
- [ ] Configure log levels via environment variables
- [ ] Add request/response logging middleware
- [ ] Create `logs/` directory structure
- [ ] Test: Logs are structured, rotated, searchable

**Docker Compose logging:**
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "5"
    labels: "service,component"
```

**Validation:**
```powershell
docker compose logs gateway | Select-String "ERROR"
Get-Content logs/gateway.log | Select-String "correlation_id"
```

---

#### **B1.6** Implement Rate Limiting (3h)
**Files:** `gateway/gateway.py`, `gateway/rate_limiter.py` (NEW)  
**Objective:** Protect APIs from abuse and DoS attacks

- [ ] Create `gateway/rate_limiter.py` with Redis-backed rate limiting
- [ ] Add rate limiting middleware to FastAPI
- [ ] Configure limits: 100 req/min per IP, 10 req/min for auth endpoints
- [ ] Add rate limit headers (X-RateLimit-*)
- [ ] Handle rate limit exceeded (429 status)
- [ ] Allow bypassing for health checks
- [ ] Test: Rate limiting works, documented in API

**Rate limiter implementation:**
```python
# gateway/rate_limiter.py
from fastapi import Request, HTTPException
import redis
import time

class RateLimiter:
    def __init__(self, redis_client, max_requests=100, window=60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window
    
    async def check_rate_limit(self, request: Request):
        # Implementation
        pass
```

**Validation:**
```powershell
# Send 101 requests in 1 minute
1..101 | ForEach-Object { Invoke-RestMethod http://localhost:8080/health }
# Should get 429 on request 101
```

---

#### **B1.7** Add Security Headers (3h)
**Files:** `gateway/gateway.py`, `web/main.py`  
**Objective:** Protect against XSS, clickjacking, CSRF attacks

- [ ] Add security headers middleware to FastAPI
- [ ] Implement CSP (Content-Security-Policy)
- [ ] Add HSTS (Strict-Transport-Security)
- [ ] Add X-Frame-Options (DENY)
- [ ] Add X-Content-Type-Options (nosniff)
- [ ] Add CSRF token validation
- [ ] Test: Security scan passes (OWASP ZAP or similar)

**Security headers:**
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

**Validation:**
```powershell
curl -I http://localhost:8080/health | Select-String "X-Frame-Options"
```

---

#### **B1.8** Update CI/CD for Security Scanning (3h)
**File:** `.github/workflows/ci.yml`  
**Objective:** Automated security validation on every commit

- [ ] Add Trivy container scanning to CI
- [ ] Add dependency vulnerability scanning (Safety, pip-audit)
- [ ] Add SAST (Bandit for Python)
- [ ] Add secret scanning (TruffleHog - already present, enhance)
- [ ] Configure security scan failure thresholds
- [ ] Add security scan results to PR comments
- [ ] Test: Security scans run on PR, block merge on critical issues

**CI additions:**
```yaml
- name: Scan Docker images with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: osmen-agent-gateway:test
    format: 'sarif'
    severity: 'CRITICAL,HIGH'
```

**Validation:**
```powershell
# Trigger CI workflow
git add .github/workflows/ci.yml
git commit -m "Add security scanning to CI"
git push origin agent-beta-infrastructure
```

---

### Day 2: Data Plane & Monitoring (Hour 24-48)

#### **B2.1** PostgreSQL Production Configuration (3h)
**Files:** `postgres/init/01-init-databases.sql`, `docker-compose.yml`  
**Objective:** Optimize PostgreSQL for production workloads

- [ ] Review/enhance init SQL script for all required databases
- [ ] Configure connection pooling settings (max_connections=100)
- [ ] Add indexes for common queries
- [ ] Configure autovacuum settings
- [ ] Set shared_buffers, work_mem appropriately
- [ ] Add PostgreSQL health check script
- [ ] Test: Database performs well under load

**PostgreSQL tuning:**
```sql
-- Add to init script
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
```

**Validation:**
```powershell
docker exec osmen-postgres psql -U postgres -c "SHOW max_connections;"
```

---

#### **B2.2** Qdrant Vector DB Configuration (3h)
**Files:** `docker-compose.yml`  
**Objective:** Optimize Qdrant for agent memory storage

- [ ] Configure persistent storage (volume mount)
- [ ] Set collection creation defaults (vector size, distance metric)
- [ ] Configure quantization for memory efficiency
- [ ] Add health check endpoint
- [ ] Document collection schemas
- [ ] Test: Vector search performs <100ms

**Qdrant configuration:**
```yaml
qdrant:
  environment:
    - QDRANT__SERVICE__GRPC_PORT=6334
    - QDRANT__SERVICE__HTTP_PORT=6333
    - QDRANT__STORAGE__OPTIMIZERS__DEFAULT_SEGMENT_SIZE=100000
  volumes:
    - qdrant-data:/qdrant/storage:rw
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
```

**Validation:**
```powershell
curl http://localhost:6333/healthz
```

---

#### **B2.3** Redis Caching Strategy (3h)
**Files:** `docker-compose.yml`, `gateway/cache.py` (NEW)  
**Objective:** Implement effective caching to reduce latency

- [ ] Configure Redis persistence (AOF + RDB)
- [ ] Create cache utility module (`gateway/cache.py`)
- [ ] Implement cache decorators for common queries
- [ ] Set appropriate TTLs for different data types
- [ ] Add cache warming on startup
- [ ] Monitor cache hit rate
- [ ] Test: Cache hit rate >80% for repeated requests

**Cache utility:**
```python
# gateway/cache.py
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

def cached(ttl=300):
    """Cache decorator with TTL"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

**Validation:**
```powershell
docker exec osmen-redis redis-cli INFO stats | Select-String "keyspace_hits"
```

---

#### **B2.4** Backup Automation (3h)
**Files:** `scripts/automation/backup.py` (NEW), `Makefile`  
**Objective:** Automated backups with verification

- [ ] Create `scripts/automation/backup.py` for automated backups
- [ ] Implement PostgreSQL backup (pg_dump)
- [ ] Implement Qdrant backup (snapshot API)
- [ ] Implement config file backup (tar.gz)
- [ ] Add backup verification (restore test)
- [ ] Schedule backups (document cron setup)
- [ ] Test: Can restore from backup successfully

**Backup script:**
```python
#!/usr/bin/env python3
"""
OsMEN Backup Automation
Backs up PostgreSQL, Qdrant, and configuration files
"""
import subprocess
from datetime import datetime
from pathlib import Path

def backup_postgres():
    """Backup all PostgreSQL databases"""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_file = f"backups/postgres-{timestamp}.sql"
    subprocess.run([
        "docker", "exec", "osmen-postgres",
        "pg_dumpall", "-U", "postgres"
    ], stdout=open(backup_file, 'w'))
    return backup_file

def backup_qdrant():
    """Backup Qdrant collections"""
    # Use Qdrant snapshot API
    pass

def backup_config():
    """Backup configuration files"""
    pass

if __name__ == "__main__":
    backup_postgres()
    backup_qdrant()
    backup_config()
```

**Validation:**
```powershell
python scripts/automation/backup.py
# Verify backup file created
Get-ChildItem backups/ | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

---

#### **B2.5** Monitoring & Alerting Setup (3h)
**Files:** `docker-compose.yml`, `docs/PRODUCTION_DEPLOYMENT.md`  
**Objective:** Proactive monitoring with alerting

- [ ] Add Prometheus for metrics collection (optional service)
- [ ] Add Grafana for dashboards (optional service)
- [ ] Configure application metrics export
- [ ] Create monitoring dashboard
- [ ] Set up alerting rules (disk space, memory, errors)
- [ ] Document monitoring setup in production docs
- [ ] Test: Alerts trigger on simulated issues

**Monitoring stack (optional profile):**
```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: osmen-prometheus
  ports:
    - "127.0.0.1:9090:9090"
  volumes:
    - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
  profiles:
    - monitoring

grafana:
  image: grafana/grafana:latest
  container_name: osmen-grafana
  ports:
    - "127.0.0.1:3000:3000"
  profiles:
    - monitoring
```

**Validation:**
```powershell
docker compose --profile monitoring up -d
curl http://localhost:9090/metrics
```

---

#### **B2.6** Enhance Makefile Commands (3h)
**File:** `Makefile`  
**Objective:** Production-ready operational commands

- [ ] Add `make prod-start` - start with production compose file
- [ ] Add `make prod-stop` - stop production stack
- [ ] Add `make prod-deploy` - full production deployment
- [ ] Add `make backup-now` - immediate backup
- [ ] Add `make restore BACKUP=<file>` - restore from backup
- [ ] Add `make security-audit` - comprehensive security check
- [ ] Enhance `make validate` - all validation checks
- [ ] Test: All commands work correctly

**Makefile additions:**
```makefile
prod-start:
	@echo "Starting OsMEN in PRODUCTION mode..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production services started!"

prod-deploy: validate backup-now prod-start
	@echo "Production deployment complete!"

backup-now:
	@python scripts/automation/backup.py

security-audit: security-check validate-secrets
	@echo "Security audit complete!"
```

**Validation:**
```powershell
make prod-start
make status
make prod-stop
```

---

#### **B2.7** Create Operational Runbooks (3h)
**Files:** `docs/runbooks/infrastructure.md` (NEW), `docs/runbooks/disaster_recovery.md` (NEW)  
**Objective:** Document operational procedures

- [ ] Create `docs/runbooks/infrastructure.md` - deployment, scaling, updates
- [ ] Create `docs/runbooks/disaster_recovery.md` - backup/restore, failover
- [ ] Create `docs/runbooks/security_incident.md` - incident response
- [ ] Document common troubleshooting scenarios
- [ ] Add on-call procedures
- [ ] Document escalation paths
- [ ] Test: Follow runbook to deploy from scratch

**Runbook structure:**
```markdown
# Infrastructure Runbook

## Deployment Procedures
### Initial Deployment
1. Clone repository
2. Copy .env.example to .env
3. Configure secrets
4. Run `make prod-deploy`

### Updates
1. Pull latest code
2. Run `make backup-now`
3. Run `make prod-deploy`

## Troubleshooting
### Service Won't Start
- Check logs: `make logs`
- Check config: `docker compose config`
```

**Validation:**
```powershell
# Follow runbook to verify it works
Get-Content docs/runbooks/infrastructure.md
```

---

#### **B2.8** End-to-End Production Test (3h)
**Files:** `tests/test_production.py` (NEW)  
**Objective:** Validate entire production stack

- [ ] Create comprehensive production test suite
- [ ] Test all service health checks
- [ ] Test service dependencies
- [ ] Test backup/restore workflow
- [ ] Test failover scenarios
- [ ] Test monitoring alerts
- [ ] Document test results
- [ ] Test: All production validation passes

**Test suite:**
```python
#!/usr/bin/env python3
"""
Production Stack Validation Tests
"""
import requests
import subprocess

def test_all_services_healthy():
    """Verify all services report healthy"""
    services = [
        ("Gateway", "http://localhost:8080/health"),
        ("MCP Server", "http://localhost:8081/health"),
        ("Qdrant", "http://localhost:6333/healthz"),
    ]
    for name, url in services:
        response = requests.get(url, timeout=5)
        assert response.status_code == 200, f"{name} not healthy"

def test_postgres_connectivity():
    """Test PostgreSQL is accessible"""
    result = subprocess.run([
        "docker", "exec", "osmen-postgres",
        "pg_isready", "-U", "postgres"
    ], capture_output=True)
    assert result.returncode == 0

if __name__ == "__main__":
    test_all_services_healthy()
    test_postgres_connectivity()
```

**Validation:**
```powershell
python tests/test_production.py
```

---

## 📅 DAY 3-4: INTEGRATION (Hour 48-96)
**Goal:** Advanced security, performance optimization, operational hardening  
**Deliverables:** TLS/HTTPS, advanced monitoring, performance tuning, compliance

### Day 3: Security Hardening (Hour 48-72)

#### **B3.1** Implement HTTPS/TLS (3h)
**Files:** `docker-compose.prod.yml`, `gateway/Dockerfile`, `config/nginx.conf` (NEW)  
**Objective:** Encrypt all external traffic

- [ ] Add Nginx reverse proxy service to docker-compose.prod.yml
- [ ] Configure TLS certificate mounting (Let's Encrypt or self-signed)
- [ ] Create `config/nginx.conf` with HTTPS redirect
- [ ] Add certbot for automatic certificate renewal
- [ ] Configure HTTPS for all exposed services
- [ ] Test: All traffic over HTTPS, HTTP redirects to HTTPS

**Nginx configuration:**
```nginx
# config/nginx.conf
server {
    listen 80;
    server_name osmen.local;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name osmen.local;
    
    ssl_certificate /etc/ssl/certs/osmen.crt;
    ssl_certificate_key /etc/ssl/private/osmen.key;
    
    location / {
        proxy_pass http://agent-gateway:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Validation:**
```powershell
curl -I https://localhost
curl -I http://localhost  # Should redirect to HTTPS
```

---

#### **B3.2** Implement Authentication & Authorization (3h)
**Files:** `web/auth.py`, `gateway/auth.py` (NEW)  
**Objective:** Secure user authentication with JWT

- [ ] Enhance `web/auth.py` with bcrypt password hashing
- [ ] Create `gateway/auth.py` for JWT token validation
- [ ] Implement session management with Redis
- [ ] Add role-based access control (RBAC)
- [ ] Add API key authentication for service-to-service
- [ ] Document auth flow in API docs
- [ ] Test: Auth works, unauthorized requests blocked

**JWT authentication:**
```python
# gateway/auth.py
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Validation:**
```powershell
# Try accessing protected endpoint without token
curl http://localhost:8080/api/protected  # Should get 401

# With valid token
curl -H "Authorization: Bearer <token>" http://localhost:8080/api/protected
```

---

#### **B3.3** Implement Audit Logging (3h)
**Files:** `gateway/audit.py` (NEW), `web/audit.py` (NEW)  
**Objective:** Track all security-relevant events

- [ ] Create audit logging middleware
- [ ] Log all authentication attempts (success/failure)
- [ ] Log all authorization failures
- [ ] Log all data access (who, what, when)
- [ ] Log all configuration changes
- [ ] Store audit logs in separate database/file
- [ ] Test: Audit trail is complete and tamper-evident

**Audit logging:**
```python
# gateway/audit.py
import logging
from datetime import datetime

audit_logger = logging.getLogger("audit")

def log_auth_attempt(username, ip_address, success):
    audit_logger.info({
        "event": "auth_attempt",
        "username": username,
        "ip": ip_address,
        "success": success,
        "timestamp": datetime.utcnow().isoformat()
    })

def log_data_access(user, resource, action):
    audit_logger.info({
        "event": "data_access",
        "user": user,
        "resource": resource,
        "action": action,
        "timestamp": datetime.utcnow().isoformat()
    })
```

**Validation:**
```powershell
Get-Content logs/audit.log | Select-String "auth_attempt"
```

---

#### **B3.4** Network Segmentation (3h)
**Files:** `docker-compose.yml`, `docker-compose.prod.yml`  
**Objective:** Isolate services with separate networks

- [ ] Create multiple Docker networks (frontend, backend, data)
- [ ] Move PostgreSQL, Qdrant, Redis to isolated backend network
- [ ] Only gateway and web connect to frontend
- [ ] Remove unnecessary port exposures
- [ ] Document network architecture
- [ ] Test: Services can't access each other inappropriately

**Network configuration:**
```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access

services:
  postgres:
    networks:
      - backend
    # Remove ports exposure - only internal access

  gateway:
    networks:
      - frontend
      - backend
    ports:
      - "127.0.0.1:8080:8080"
```

**Validation:**
```powershell
docker network ls
docker network inspect osmen_backend
```

---

#### **B3.5** Vulnerability Scanning (3h)
**Files:** `.github/workflows/security-scan.yml` (NEW), `scripts/automation/vulnerability_scan.sh` (NEW)  
**Objective:** Continuous vulnerability detection

- [ ] Create dedicated security scanning workflow
- [ ] Add Trivy for container image scanning
- [ ] Add Safety/pip-audit for Python dependencies
- [ ] Add Snyk or Dependabot for dependency scanning
- [ ] Create vulnerability scan script for local use
- [ ] Set up weekly automated scans
- [ ] Test: Scans run and report vulnerabilities

**Security scan workflow:**
```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  vulnerability-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Scan Python dependencies
        run: |
          pip install safety
          safety check --json
      
      - name: Scan Docker images
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
```

**Validation:**
```powershell
# Run local scan
bash scripts/automation/vulnerability_scan.sh
```

---

#### **B3.6** Compliance Configuration (3h)
**Files:** `docs/COMPLIANCE.md` (NEW), `config/compliance/` (NEW)  
**Objective:** GDPR, SOC2 compliance readiness

- [ ] Document data retention policies
- [ ] Implement data encryption at rest
- [ ] Add user data export capability
- [ ] Add user data deletion capability (right to be forgotten)
- [ ] Create compliance checklist
- [ ] Document privacy policy
- [ ] Test: Compliance requirements met

**Compliance checklist:**
```markdown
# GDPR Compliance Checklist

- [ ] Data encryption at rest (PostgreSQL, Qdrant)
- [ ] Data encryption in transit (TLS/HTTPS)
- [ ] User consent tracking
- [ ] Data export capability
- [ ] Data deletion capability
- [ ] Audit logging
- [ ] Data retention policy
- [ ] Privacy policy
- [ ] Data processing agreement
```

**Validation:**
```powershell
Get-Content docs/COMPLIANCE.md
```

---

#### **B3.7** Secrets Rotation Automation (3h)
**Files:** `scripts/automation/rotate_secrets.py` (NEW)  
**Objective:** Automate credential rotation

- [ ] Create secret rotation script
- [ ] Implement database password rotation
- [ ] Implement API key rotation
- [ ] Implement certificate renewal
- [ ] Document rotation procedures
- [ ] Test rotation without downtime
- [ ] Test: Secrets can be rotated safely

**Rotation script:**
```python
#!/usr/bin/env python3
"""
Secret Rotation Automation
Rotates database passwords, API keys, certificates
"""
import subprocess
import os
from datetime import datetime

def rotate_postgres_password():
    """Rotate PostgreSQL password"""
    new_password = generate_secure_password()
    # Update .env
    # Restart postgres with new password
    # Update applications
    pass

def rotate_api_keys():
    """Rotate API keys"""
    pass

def rotate_certificates():
    """Renew TLS certificates"""
    subprocess.run(["certbot", "renew"])
```

**Validation:**
```powershell
python scripts/automation/rotate_secrets.py --dry-run
```

---

#### **B3.8** Penetration Testing Preparation (3h)
**Files:** `docs/SECURITY.md` (NEW), `tests/security/` (NEW)  
**Objective:** Prepare for and document security testing

- [ ] Create security documentation
- [ ] Document threat model
- [ ] Create test scenarios for common attacks (SQLi, XSS, CSRF)
- [ ] Set up isolated test environment
- [ ] Document findings remediation process
- [ ] Create security contact/disclosure policy
- [ ] Test: Security test scenarios execute

**Security test scenarios:**
```python
# tests/security/test_sql_injection.py
def test_sql_injection_protection():
    """Verify SQL injection is prevented"""
    malicious_input = "'; DROP TABLE users; --"
    response = requests.post(
        "http://localhost:8080/api/search",
        json={"query": malicious_input}
    )
    # Should not execute SQL, should sanitize input
    assert response.status_code != 500
```

**Validation:**
```powershell
python -m pytest tests/security/
```

---

### Day 4: Performance & Reliability (Hour 72-96)

#### **B4.1** Database Performance Tuning (3h)
**Files:** `postgres/init/02-performance-tuning.sql` (NEW)  
**Objective:** Optimize database for production load

- [ ] Create performance tuning SQL script
- [ ] Add indexes for all foreign keys
- [ ] Add indexes for frequently queried columns
- [ ] Configure query plan statistics
- [ ] Enable query logging for slow queries (>100ms)
- [ ] Set up pg_stat_statements extension
- [ ] Test: Queries meet <100ms target

**Performance tuning:**
```sql
-- postgres/init/02-performance-tuning.sql
-- Enable query statistics
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Add indexes for common queries
CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_start_time ON events(start_time);
CREATE INDEX idx_tasks_priority ON tasks(priority DESC);

-- Configure autovacuum
ALTER SYSTEM SET autovacuum_naptime = '30s';
```

**Validation:**
```powershell
docker exec osmen-postgres psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5;"
```

---

#### **B4.2** API Performance Optimization (3h)
**Files:** `gateway/gateway.py`, `gateway/performance.py` (NEW)  
**Objective:** Ensure API responses <200ms

- [ ] Add response compression (gzip)
- [ ] Implement connection pooling for databases
- [ ] Add query result caching
- [ ] Optimize serialization (use orjson)
- [ ] Add pagination to list endpoints
- [ ] Implement lazy loading
- [ ] Test: All endpoints <200ms

**Performance optimizations:**
```python
# gateway/performance.py
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
import orjson

app.add_middleware(GZipMiddleware, minimum_size=1000)

class ORJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return orjson.dumps(content)

@app.get("/api/events", response_class=ORJSONResponse)
async def list_events(skip: int = 0, limit: int = 100):
    # Paginated response
    pass
```

**Validation:**
```powershell
# Test response time
Measure-Command { Invoke-RestMethod http://localhost:8080/api/events }
```

---

#### **B4.3** Load Balancing Configuration (3h)
**Files:** `config/nginx.conf`, `docker-compose.prod.yml`  
**Objective:** Horizontal scaling with load balancing

- [ ] Configure Nginx upstream for multiple gateway instances
- [ ] Add health checks to upstream servers
- [ ] Configure load balancing algorithm (least_conn)
- [ ] Add session affinity if needed
- [ ] Document scaling procedures
- [ ] Test: Load distributes across instances

**Nginx load balancing:**
```nginx
upstream gateway_backend {
    least_conn;
    server gateway-1:8080 max_fails=3 fail_timeout=30s;
    server gateway-2:8080 max_fails=3 fail_timeout=30s;
}

server {
    location / {
        proxy_pass http://gateway_backend;
    }
}
```

**Validation:**
```powershell
# Scale gateway service
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale gateway=3
```

---

#### **B4.4** Implement Circuit Breakers (3h)
**Files:** `gateway/resilience.py`  
**Objective:** Graceful degradation under failure

- [ ] Enhance resilience.py with circuit breaker pattern
- [ ] Add circuit breaker for external API calls
- [ ] Add circuit breaker for database connections
- [ ] Configure thresholds (failure rate, timeout)
- [ ] Add fallback responses
- [ ] Test: System degrades gracefully

**Circuit breaker:**
```python
# gateway/resilience.py
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_external_api(url):
    """Call external API with circuit breaker"""
    response = await client.get(url, timeout=5)
    response.raise_for_status()
    return response.json()
```

**Validation:**
```powershell
# Simulate external API failure
# Verify circuit breaker opens after 5 failures
```

---

#### **B4.5** Disaster Recovery Testing (3h)
**Files:** `scripts/automation/disaster_recovery_test.py` (NEW)  
**Objective:** Validate backup/restore procedures

- [ ] Create automated DR test script
- [ ] Test PostgreSQL restore from backup
- [ ] Test Qdrant restore from snapshot
- [ ] Test configuration restore
- [ ] Measure Recovery Time Objective (RTO)
- [ ] Measure Recovery Point Objective (RPO)
- [ ] Document DR procedures

**DR test script:**
```python
#!/usr/bin/env python3
"""
Disaster Recovery Test
Validates backup and restore procedures
"""
import subprocess
import time

def test_postgres_restore():
    """Test PostgreSQL backup restore"""
    # Stop postgres
    # Restore from latest backup
    # Start postgres
    # Verify data integrity
    pass

def test_full_recovery():
    """Test complete system recovery"""
    start_time = time.time()
    # Simulate disaster
    # Restore all services
    recovery_time = time.time() - start_time
    print(f"RTO: {recovery_time}s")
    assert recovery_time < 300, "RTO exceeded 5 minutes"
```

**Validation:**
```powershell
python scripts/automation/disaster_recovery_test.py
```

---

#### **B4.6** Observability Enhancement (3h)
**Files:** `gateway/telemetry.py` (NEW), `docker-compose.yml`  
**Objective:** Distributed tracing and metrics

- [ ] Add OpenTelemetry instrumentation
- [ ] Implement distributed tracing (Jaeger)
- [ ] Add custom metrics (request duration, error rate)
- [ ] Create performance dashboard
- [ ] Add alerting rules for SLOs
- [ ] Test: Full request tracing works

**Telemetry:**
```python
# gateway/telemetry.py
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

tracer = trace.get_tracer(__name__)

@app.get("/api/events")
async def list_events():
    with tracer.start_as_current_span("list_events"):
        # Implementation
        pass

FastAPIInstrumentor.instrument_app(app)
```

**Validation:**
```powershell
curl http://localhost:16686  # Jaeger UI
```

---

#### **B4.7** Chaos Engineering Setup (3h)
**Files:** `tests/chaos/` (NEW), `scripts/automation/chaos_test.sh` (NEW)  
**Objective:** Test resilience under failure

- [ ] Create chaos testing scenarios
- [ ] Test service failure (kill random container)
- [ ] Test network failure (simulate latency)
- [ ] Test resource exhaustion (CPU, memory)
- [ ] Document failure behaviors
- [ ] Verify automatic recovery
- [ ] Test: System recovers from chaos

**Chaos test:**
```bash
# scripts/automation/chaos_test.sh
#!/bin/bash
# Chaos Engineering Tests

echo "Killing random service..."
docker kill osmen-gateway

echo "Waiting 10s..."
sleep 10

echo "Checking if service recovered..."
docker ps | grep osmen-gateway
```

**Validation:**
```powershell
bash scripts/automation/chaos_test.sh
```

---

#### **B4.8** Production Deployment Checklist (3h)
**Files:** `docs/PRODUCTION_DEPLOYMENT.md`, `scripts/automation/pre_deploy_check.py` (NEW)  
**Objective:** Automated pre-deployment validation

- [ ] Create comprehensive deployment checklist
- [ ] Create automated pre-deploy validation script
- [ ] Verify all secrets configured
- [ ] Verify all services healthy
- [ ] Verify backups working
- [ ] Verify monitoring active
- [ ] Create deployment runbook
- [ ] Test: Automated checks pass

**Pre-deploy check:**
```python
#!/usr/bin/env python3
"""
Pre-Deployment Validation
Checks all production readiness criteria
"""
def check_secrets():
    """Verify all required secrets are set"""
    pass

def check_services():
    """Verify all services are healthy"""
    pass

def check_backups():
    """Verify backup system is working"""
    pass

def check_monitoring():
    """Verify monitoring is active"""
    pass

if __name__ == "__main__":
    all_checks = [
        check_secrets,
        check_services,
        check_backups,
        check_monitoring
    ]
    for check in all_checks:
        check()
```

**Validation:**
```powershell
python scripts/automation/pre_deploy_check.py
```

---

## 📅 DAY 5-6: PRODUCTION LAUNCH (Hour 96-144)
**Goal:** Final hardening, launch readiness, operational excellence  
**Deliverables:** Production deployed, monitored, documented, ready for users

### Day 5: Final Hardening (Hour 96-120)

#### **B5.1** Security Audit & Remediation (3h)
**Files:** Various  
**Objective:** Fix all security findings

- [ ] Run comprehensive security scan
- [ ] Review all security findings
- [ ] Remediate critical and high severity issues
- [ ] Document accepted risks (low/medium)
- [ ] Update security documentation
- [ ] Verify no secrets in repository
- [ ] Test: Zero critical/high vulnerabilities

**Validation:**
```powershell
python scripts/automation/validate_security.py
make security-audit
```

---

#### **B5.2** Performance Benchmarking (3h)
**Files:** `tests/performance/benchmark.py` (NEW)  
**Objective:** Validate performance targets

- [ ] Create performance benchmark suite
- [ ] Test API response times (<200ms)
- [ ] Test database query times (<100ms)
- [ ] Test concurrent user capacity (100 users)
- [ ] Test throughput (1000 events/min)
- [ ] Document performance baselines
- [ ] Test: All targets met

**Benchmark suite:**
```python
#!/usr/bin/env python3
"""
Performance Benchmark Suite
"""
import asyncio
import aiohttp
import time

async def benchmark_api_response_time():
    """Benchmark API response time"""
    async with aiohttp.ClientSession() as session:
        times = []
        for _ in range(100):
            start = time.time()
            async with session.get('http://localhost:8080/api/events') as response:
                await response.json()
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        p95_time = sorted(times)[95]
        
        print(f"Avg: {avg_time*1000:.2f}ms, P95: {p95_time*1000:.2f}ms")
        assert avg_time < 0.2, "API response time >200ms"

if __name__ == "__main__":
    asyncio.run(benchmark_api_response_time())
```

**Validation:**
```powershell
python tests/performance/benchmark.py
```

---

#### **B5.3** Infrastructure Documentation (3h)
**Files:** `docs/INFRASTRUCTURE.md` (NEW), `docs/ARCHITECTURE.md`  
**Objective:** Complete infrastructure documentation

- [ ] Create `docs/INFRASTRUCTURE.md`
- [ ] Document all services and their purpose
- [ ] Document network architecture
- [ ] Document data flows
- [ ] Create architecture diagrams
- [ ] Document scaling procedures
- [ ] Test: New engineer can understand infrastructure

**Infrastructure documentation:**
```markdown
# Infrastructure Documentation

## Service Overview
- **Gateway**: API gateway for LLM agents
- **MCP Server**: Model Context Protocol server
- **PostgreSQL**: Primary database
- **Qdrant**: Vector database for memory
- **Redis**: Caching and sessions

## Network Architecture
```
[Internet] → [Nginx:443] → [Gateway:8080] → [Backend Services]
                                          → [PostgreSQL:5432]
                                          → [Qdrant:6333]
                                          → [Redis:6379]
```

## Scaling Procedures
- Horizontal: Scale gateway with `docker compose up -d --scale gateway=N`
- Vertical: Adjust resource limits in docker-compose.prod.yml
```

**Validation:**
```powershell
Get-Content docs/INFRASTRUCTURE.md
```

---

#### **B5.4** Monitoring Dashboard Creation (3h)
**Files:** `config/grafana/dashboards/` (NEW)  
**Objective:** Operational visibility dashboard

- [ ] Create Grafana dashboards
- [ ] Add system health overview dashboard
- [ ] Add service-specific dashboards
- [ ] Add business metrics dashboard
- [ ] Configure dashboard auto-refresh
- [ ] Export dashboards as JSON
- [ ] Test: Dashboards show real-time data

**Dashboard configuration:**
```json
{
  "dashboard": {
    "title": "OsMEN System Health",
    "panels": [
      {
        "title": "Service Health",
        "targets": [
          {"expr": "up{job='gateway'}"}
        ]
      },
      {
        "title": "API Response Time",
        "targets": [
          {"expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"}
        ]
      }
    ]
  }
}
```

**Validation:**
```powershell
# Access Grafana
Start-Process http://localhost:3000
```

---

#### **B5.5** Alert Configuration (3h)
**Files:** `config/prometheus/alerts.yml` (NEW)  
**Objective:** Proactive issue detection

- [ ] Create Prometheus alerting rules
- [ ] Configure alerts for service down
- [ ] Configure alerts for high error rate
- [ ] Configure alerts for high latency
- [ ] Configure alerts for resource exhaustion
- [ ] Set up alert notification (email, Slack)
- [ ] Test: Alerts trigger and notify

**Alert rules:**
```yaml
# config/prometheus/alerts.yml
groups:
  - name: osmen_alerts
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
      
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.job }}"
```

**Validation:**
```powershell
# Trigger test alert
docker stop osmen-gateway
# Wait for alert
# Verify notification received
```

---

#### **B5.6** Capacity Planning Documentation (3h)
**Files:** `docs/CAPACITY_PLANNING.md` (NEW)  
**Objective:** Plan for growth

- [ ] Document current resource utilization
- [ ] Calculate cost per user
- [ ] Project resource needs for 100, 1000, 10000 users
- [ ] Document scaling triggers
- [ ] Create capacity planning spreadsheet
- [ ] Document cost optimization strategies
- [ ] Test: Capacity plan is actionable

**Capacity planning:**
```markdown
# Capacity Planning

## Current Baseline (10 users)
- CPU: 1 core (20% utilization)
- Memory: 2GB (50% utilization)
- Storage: 10GB (5% utilization)
- Network: 1MB/s

## Scaling Projections
| Users | CPU Cores | Memory (GB) | Storage (GB) | Cost/month |
|-------|-----------|-------------|--------------|------------|
| 100   | 2         | 4           | 50           | $50        |
| 1000  | 8         | 16          | 500          | $200       |
| 10000 | 32        | 64          | 5000         | $800       |

## Scaling Triggers
- CPU >70% for 10 minutes → Scale up
- Memory >80% for 5 minutes → Scale up
```

**Validation:**
```powershell
Get-Content docs/CAPACITY_PLANNING.md
```

---

#### **B5.7** Incident Response Procedures (3h)
**Files:** `docs/runbooks/incident_response.md` (NEW)  
**Objective:** Prepared for incidents

- [ ] Create incident response runbook
- [ ] Document incident severity levels
- [ ] Document escalation procedures
- [ ] Create incident templates
- [ ] Document postmortem process
- [ ] Set up incident communication channels
- [ ] Test: Can respond to simulated incident

**Incident response:**
```markdown
# Incident Response Runbook

## Severity Levels
- **P0 (Critical)**: Service completely down, data loss
- **P1 (High)**: Major feature broken, degraded performance
- **P2 (Medium)**: Minor feature broken, workaround available
- **P3 (Low)**: Cosmetic issue, no user impact

## Response Procedures
### P0 - Critical Incident
1. Declare incident in #incidents channel
2. Page on-call engineer
3. Assemble incident response team
4. Begin mitigation immediately
5. Communicate status every 15 minutes
6. Document actions in incident log

## Postmortem Template
- **Incident Summary**: What happened
- **Impact**: Users affected, duration
- **Root Cause**: Why it happened
- **Resolution**: How it was fixed
- **Action Items**: Prevent recurrence
```

**Validation:**
```powershell
# Simulate incident
# Follow runbook
# Verify procedures work
```

---

#### **B5.8** Production Readiness Review (3h)
**Files:** `docs/PRODUCTION_READY_CHECKLIST.md` (NEW)  
**Objective:** Final go/no-go decision

- [ ] Create production readiness checklist
- [ ] Review all security requirements
- [ ] Review all performance requirements
- [ ] Review all operational requirements
- [ ] Conduct readiness review meeting
- [ ] Document any risks/mitigations
- [ ] Make go/no-go decision
- [ ] Test: All criteria met or risks accepted

**Readiness checklist:**
```markdown
# Production Readiness Checklist

## Security ✅
- [x] All secrets in environment variables
- [x] HTTPS/TLS configured
- [x] Authentication implemented
- [x] Rate limiting active
- [x] Security headers configured
- [x] No critical vulnerabilities

## Performance ✅
- [x] API responses <200ms
- [x] Database queries <100ms
- [x] Handles 100 concurrent users
- [x] Load tested

## Operations ✅
- [x] Backups automated and tested
- [x] Monitoring active
- [x] Alerts configured
- [x] Runbooks documented
- [x] Disaster recovery tested

## Documentation ✅
- [x] User documentation complete
- [x] API documentation complete
- [x] Deployment documentation complete
- [x] Runbooks complete

## Go/No-Go Decision: GO ✅
```

**Validation:**
```powershell
Get-Content docs/PRODUCTION_READY_CHECKLIST.md
```

---

### Day 6: Launch & Operations (Hour 120-144)

#### **B6.1** Production Deployment Execution (3h)
**Files:** Various  
**Objective:** Deploy to production environment

- [ ] Run pre-deployment checks
- [ ] Execute production deployment
- [ ] Verify all services started
- [ ] Run smoke tests
- [ ] Verify monitoring active
- [ ] Verify backups running
- [ ] Document deployment
- [ ] Test: Production deployment successful

**Deployment execution:**
```powershell
# Pre-deployment
python scripts/automation/pre_deploy_check.py
make backup-now

# Deployment
make prod-deploy

# Post-deployment
make status
python check_operational.py
python tests/test_production.py
```

**Validation:**
```powershell
# All services healthy
docker compose ps | Select-String "healthy"
```

---

#### **B6.2** Post-Deployment Monitoring (3h)
**Files:** N/A (monitoring activity)  
**Objective:** Ensure stable launch

- [ ] Monitor all service health
- [ ] Monitor error rates
- [ ] Monitor performance metrics
- [ ] Monitor resource utilization
- [ ] Check for any alerts
- [ ] Review logs for issues
- [ ] Document any issues found
- [ ] Test: System stable for 3 hours

**Monitoring checklist:**
```markdown
# Post-Deployment Monitoring Checklist

## Hour 1
- [x] All services healthy
- [x] No error spikes
- [x] Response times normal
- [x] No alerts triggered

## Hour 2
- [x] Services still healthy
- [x] Performance stable
- [x] Resource usage normal
- [x] Backups completed

## Hour 3
- [x] System stable
- [x] Ready for users
```

---

#### **B6.3** Performance Tuning (3h)
**Files:** Various  
**Objective:** Optimize based on production data

- [ ] Analyze production performance data
- [ ] Identify bottlenecks
- [ ] Apply optimizations
- [ ] Measure improvements
- [ ] Document optimizations
- [ ] Update performance baselines
- [ ] Test: Performance improved

**Tuning activities:**
- Adjust cache TTLs based on hit rates
- Optimize slow queries identified in production
- Adjust resource limits based on actual usage
- Fine-tune connection pool sizes

**Validation:**
```powershell
# Compare before/after metrics
```

---

#### **B6.4** Security Hardening (3h)
**Files:** Various  
**Objective:** Final security lockdown

- [ ] Review production security logs
- [ ] Tighten firewall rules
- [ ] Remove any debug/test accounts
- [ ] Verify no test data in production
- [ ] Enable all security features
- [ ] Run final security scan
- [ ] Document security posture
- [ ] Test: Security audit passes

**Security checklist:**
- Remove debug endpoints
- Ensure all default passwords changed
- Verify audit logging capturing all events
- Confirm rate limits are effective

**Validation:**
```powershell
python scripts/automation/validate_security.py
```

---

#### **B6.5** Backup Verification (3h)
**Files:** N/A (operational activity)  
**Objective:** Ensure backups are working

- [ ] Verify automated backups running
- [ ] Test backup restoration
- [ ] Measure backup size and duration
- [ ] Verify backup retention policy
- [ ] Test backup alerts
- [ ] Document backup procedures
- [ ] Test: Can restore from production backup

**Backup verification:**
```powershell
# Trigger manual backup
make backup-now

# Verify backup created
Get-ChildItem backups/ | Sort-Object LastWriteTime -Descending

# Test restore (in isolated environment)
```

---

#### **B6.6** Documentation Finalization (3h)
**Files:** All documentation  
**Objective:** Complete and accurate documentation

- [ ] Review all documentation for accuracy
- [ ] Update any outdated information
- [ ] Add screenshots where helpful
- [ ] Create quick reference guides
- [ ] Verify all links work
- [ ] Add FAQ section
- [ ] Test: Documentation is comprehensive

**Documentation review:**
- README.md - up to date
- docs/SETUP.md - accurate
- docs/ARCHITECTURE.md - complete
- docs/PRODUCTION_DEPLOYMENT.md - verified
- docs/runbooks/* - tested
- API documentation - accurate

**Validation:**
```powershell
# Review all docs
Get-ChildItem docs/ -Recurse -Filter *.md | ForEach-Object { Get-Content $_.FullName }
```

---

#### **B6.7** Operational Handoff (3h)
**Files:** `docs/OPERATIONS_HANDOFF.md` (NEW)  
**Objective:** Transfer knowledge to operations team

- [ ] Create operations handoff document
- [ ] Document all credentials and access
- [ ] Document on-call procedures
- [ ] Document common issues and solutions
- [ ] Conduct handoff meeting
- [ ] Transfer access/credentials
- [ ] Verify operations team can operate system
- [ ] Test: Operations team self-sufficient

**Handoff document:**
```markdown
# Operations Handoff

## Access & Credentials
- Production server: <URL>
- Admin credentials: See 1Password vault
- Monitoring: <URL>
- Logs: <URL>

## On-Call Procedures
- On-call schedule: <Link>
- Escalation path: Level 1 → Level 2 → Engineering
- Incident response: See docs/runbooks/incident_response.md

## Common Issues
1. **Service won't start**: Check logs, verify .env configuration
2. **High memory usage**: Restart service, check for memory leaks
3. **Slow queries**: Check pg_stat_statements, add indexes

## Key Contacts
- Lead Engineer: <Contact>
- Database Admin: <Contact>
- Security: <Contact>
```

**Validation:**
```powershell
# Operations team performs deployment
# Verify they can operate independently
```

---

#### **B6.8** Launch Success Validation (3h)
**Files:** N/A (validation activity)  
**Objective:** Confirm successful launch

- [ ] Verify all success criteria met
- [ ] Review all metrics and KPIs
- [ ] Collect initial user feedback
- [ ] Document lessons learned
- [ ] Celebrate success! 🎉
- [ ] Plan next iteration
- [ ] Test: All launch criteria achieved

**Success criteria:**
- ✅ All services deployed and healthy
- ✅ Zero critical issues
- ✅ Performance targets met
- ✅ Security requirements met
- ✅ Monitoring and alerting active
- ✅ Documentation complete
- ✅ Operations team trained
- ✅ Users successfully onboarding

**Launch metrics:**
```markdown
# Launch Success Metrics

## Technical
- Uptime: 100% (first 24h)
- Response time: 150ms avg (target: <200ms)
- Error rate: 0.01% (target: <1%)
- Zero critical vulnerabilities

## Operational
- Deployment time: 15 minutes (target: <30min)
- Backup success: 100%
- Alert accuracy: 100% (no false positives)

## User
- Onboarding time: 3 minutes avg (target: <5min)
- User satisfaction: 95%+ (initial feedback)
```

---

## 🎯 SUCCESS CRITERIA

### Technical Excellence
- [ ] All 48 tasks completed
- [ ] All services deployed and healthy
- [ ] All security requirements met
- [ ] All performance targets achieved
- [ ] All operational procedures documented

### Production Readiness
- [ ] Zero critical vulnerabilities
- [ ] >99% uptime in first week
- [ ] All APIs <200ms response time
- [ ] Automated backups and restores tested
- [ ] Monitoring and alerting functional

### Operational Excellence
- [ ] Complete runbooks for all procedures
- [ ] Operations team trained
- [ ] Incident response tested
- [ ] Disaster recovery validated
- [ ] Documentation comprehensive

---

## 📊 DELIVERABLES CHECKLIST

### Configuration Files
- [x] `docker-compose.yml` - hardened
- [x] `docker-compose.prod.yml` - created
- [x] `.env.example` - complete
- [x] `config/nginx.conf` - HTTPS configured
- [x] `config/prometheus.yml` - monitoring setup
- [x] `config/grafana/dashboards/` - dashboards created

### Scripts
- [x] `scripts/automation/validate_secrets.py`
- [x] `scripts/automation/backup.py`
- [x] `scripts/automation/pre_deploy_check.py`
- [x] `scripts/automation/disaster_recovery_test.py`
- [x] `scripts/automation/vulnerability_scan.sh`
- [x] `scripts/automation/chaos_test.sh`

### Documentation
- [x] `docs/INFRASTRUCTURE.md`
- [x] `docs/COMPLIANCE.md`
- [x] `docs/CAPACITY_PLANNING.md`
- [x] `docs/PRODUCTION_READY_CHECKLIST.md`
- [x] `docs/OPERATIONS_HANDOFF.md`
- [x] `docs/runbooks/infrastructure.md`
- [x] `docs/runbooks/disaster_recovery.md`
- [x] `docs/runbooks/incident_response.md`

### Tests
- [x] `tests/test_production.py`
- [x] `tests/performance/benchmark.py`
- [x] `tests/security/test_sql_injection.py`
- [x] `tests/chaos/` - chaos engineering tests

### CI/CD
- [x] `.github/workflows/ci.yml` - enhanced
- [x] `.github/workflows/security-scan.yml` - created

---

## 🚀 NEXT STEPS AFTER COMPLETION

1. **Merge to main** - Create PR with all infrastructure work
2. **Deploy to staging** - Validate in staging environment
3. **Production deployment** - Execute production deployment
4. **Monitor closely** - Watch metrics for first 48 hours
5. **Iterate** - Collect feedback and improve

---

**Agent Beta Status:** READY TO EXECUTE  
**Branch:** `agent-beta-infrastructure`  
**Timeline:** 6 days (144 hours)  
**Commitment:** Production-ready infrastructure and security

Let's ship it! 🚀
