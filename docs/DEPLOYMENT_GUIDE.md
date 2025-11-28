# OsMEN v3.0 Deployment Guide

> Complete guide for deploying OsMEN in development, staging, and production environments

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Production Deployment](#production-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Provider Guides](#cloud-provider-guides)
6. [Configuration](#configuration)
7. [Security Hardening](#security-hardening)
8. [Monitoring & Observability](#monitoring--observability)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 20 GB | 50+ GB SSD |
| OS | Ubuntu 20.04+, macOS 12+ | Ubuntu 22.04 LTS |

### Software Dependencies

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **Python** 3.12+ (for local development)
- **Git** (for source deployment)
- **curl** or **wget** (for health checks)

### Optional (for Kubernetes)

- **kubectl** 1.28+
- **Helm** 3.12+

---

## Quick Start (Docker)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/OsMEN.git
cd OsMEN
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

**Minimum Required Settings:**

```env
# LLM Provider (at least one)
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# Database (auto-configured in Docker)
POSTGRES_PASSWORD=your-secure-password

# Security
JWT_SECRET=$(openssl rand -hex 64)
ENCRYPTION_KEY=$(openssl rand -base64 32)
```

### 3. Start Services

```bash
# Start all services
make start
# or
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Verify Installation

```bash
# Check health
curl http://localhost:8080/health

# Run a test workflow
python workflows/daily_brief.py --provider ollama
```

### Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Gateway API | http://localhost:8080 | Main API |
| Langflow | http://localhost:7860 | Visual flow editor |
| n8n | http://localhost:5678 | Workflow automation |
| Qdrant | http://localhost:6333 | Vector database |

---

## Production Deployment

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer                           │
│                      (HTTPS termination)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌─────▼─────┐       ┌────▼────┐
    │ Gateway │        │  Gateway  │       │ Gateway │
    │ (Pod 1) │        │  (Pod 2)  │       │ (Pod 3) │
    └────┬────┘        └─────┬─────┘       └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    │                        │                        │
┌───▼───┐              ┌─────▼─────┐            ┌─────▼─────┐
│PostgreSQL│           │   Redis   │            │  Qdrant   │
│(Primary) │           │ (Cluster) │            │ (Cluster) │
└─────────┘            └───────────┘            └───────────┘
```

### 1. Production Docker Compose

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d
```

**docker-compose.prod.yml highlights:**

```yaml
version: '3.8'

services:
  gateway:
    image: osmen/gateway:3.0.0
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    secrets:
      - db_password

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:v1.7.0
    volumes:
      - qdrant_data:/qdrant/storage

secrets:
  db_password:
    file: ./secrets/db_password.txt

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

### 2. SSL/TLS Configuration

**Using Traefik (recommended):**

```yaml
# Add to docker-compose.prod.yml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt

  gateway:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.gateway.rule=Host(`api.example.com`)"
      - "traefik.http.routers.gateway.tls.certresolver=letsencrypt"
```

### 3. Database Setup

```bash
# Initialize database
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE osmen;"

# Run migrations
docker-compose exec gateway python scripts/migrate.py

# Create indexes
docker-compose exec postgres psql -U postgres -d osmen -f /app/database/indexes.sql
```

---

## Kubernetes Deployment

### 1. Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### 2. Create Namespace

```bash
kubectl create namespace osmen
kubectl config set-context --current --namespace=osmen
```

### 3. Create Secrets

```bash
# Create secrets from file
kubectl create secret generic osmen-secrets \
  --from-literal=openai-api-key='sk-...' \
  --from-literal=postgres-password='...' \
  --from-literal=jwt-secret='...'
```

### 4. Deploy with Helm

```bash
# Add OsMEN Helm repo (if published)
helm repo add osmen https://charts.osmen.io

# Install
helm install osmen osmen/osmen \
  --namespace osmen \
  --values values-production.yaml
```

**values-production.yaml:**

```yaml
replicaCount: 3

image:
  repository: osmen/gateway
  tag: "3.0.0"

resources:
  limits:
    cpu: "2"
    memory: 4Gi
  requests:
    cpu: "500m"
    memory: 1Gi

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: osmen-tls
      hosts:
        - api.example.com

postgresql:
  enabled: true
  auth:
    existingSecret: osmen-secrets
    secretKeys:
      adminPasswordKey: postgres-password

redis:
  enabled: true
  auth:
    enabled: true
    existingSecret: osmen-secrets

qdrant:
  enabled: true
  persistence:
    enabled: true
    size: 50Gi
```

### 5. Apply Kubernetes Manifests (Alternative)

```bash
# Apply all manifests
kubectl apply -f infra/kubernetes/

# Watch deployment
kubectl get pods -w
```

---

## Cloud Provider Guides

### AWS (EKS)

```bash
# Create EKS cluster
eksctl create cluster \
  --name osmen-prod \
  --region us-west-2 \
  --node-type m5.large \
  --nodes 3

# Deploy
helm install osmen ./charts/osmen \
  --set cloud.provider=aws \
  --set postgresql.storageClass=gp3 \
  --set ingress.className=alb
```

### Google Cloud (GKE)

```bash
# Create GKE cluster
gcloud container clusters create osmen-prod \
  --zone us-central1-a \
  --machine-type e2-standard-4 \
  --num-nodes 3

# Deploy
helm install osmen ./charts/osmen \
  --set cloud.provider=gcp \
  --set ingress.className=gce
```

### Azure (AKS)

```bash
# Create AKS cluster
az aks create \
  --resource-group osmen-rg \
  --name osmen-prod \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3

# Deploy
helm install osmen ./charts/osmen \
  --set cloud.provider=azure \
  --set ingress.className=azure
```

### DigitalOcean (DOKS)

```bash
# Create cluster
doctl kubernetes cluster create osmen-prod \
  --region nyc1 \
  --size s-4vcpu-8gb \
  --count 3

# Deploy
helm install osmen ./charts/osmen \
  --set cloud.provider=do
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `development` |
| `LOG_LEVEL` | Logging level | `info` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `DATABASE_URL` | PostgreSQL connection | - |
| `REDIS_URL` | Redis connection | - |
| `QDRANT_URL` | Qdrant connection | `http://localhost:6333` |
| `JWT_SECRET` | JWT signing secret | - |
| `RATE_LIMIT_RPM` | Requests per minute | `100` |

### Configuration Files

```
config/
├── development.yaml    # Dev settings
├── staging.yaml        # Staging settings
├── production.yaml     # Production settings
└── secrets.yaml        # Secret references
```

---

## Security Hardening

### 1. Network Security

```yaml
# Kubernetes NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: osmen-network-policy
spec:
  podSelector:
    matchLabels:
      app: osmen-gateway
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
```

### 2. Secret Management

```bash
# Use external secrets operator
kubectl apply -f https://raw.githubusercontent.com/external-secrets/external-secrets/main/deploy/crds/bundle.yaml

# Create ExternalSecret
cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: osmen-secrets
spec:
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: osmen-secrets
  data:
    - secretKey: openai-api-key
      remoteRef:
        key: osmen/api-keys
        property: openai
EOF
```

### 3. Pod Security

```yaml
# PodSecurityPolicy
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: osmen-restricted
spec:
  privileged: false
  runAsUser:
    rule: MustRunAsNonRoot
  fsGroup:
    rule: RunAsAny
  volumes:
    - 'configMap'
    - 'secret'
    - 'persistentVolumeClaim'
```

---

## Monitoring & Observability

### 1. Prometheus + Grafana

```bash
# Install Prometheus stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Import OsMEN dashboards
kubectl apply -f monitoring/grafana-dashboards/
```

### 2. Service Metrics

```yaml
# ServiceMonitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: osmen-gateway
spec:
  selector:
    matchLabels:
      app: osmen-gateway
  endpoints:
    - port: metrics
      interval: 30s
      path: /health/metrics
```

### 3. Logging

```bash
# Install Loki stack
helm install loki grafana/loki-stack \
  --namespace logging \
  --create-namespace \
  --set promtail.enabled=true
```

---

## Backup & Recovery

### 1. Automated Backups

```bash
# Schedule PostgreSQL backup
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres:16
              command:
                - /bin/sh
                - -c
                - |
                  pg_dump -h postgres -U postgres osmen | \
                  gzip > /backups/osmen-$(date +%Y%m%d).sql.gz
          restartPolicy: OnFailure
EOF
```

### 2. Verify Backups

```bash
# Run backup verification
python scripts/backup_verify.py --check-age --max-hours 24
python scripts/backup_verify.py --verify latest
```

### 3. Disaster Recovery

```bash
# Restore from backup
docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS osmen;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE osmen;"
zcat backups/osmen-20241128.sql.gz | docker-compose exec -T postgres psql -U postgres -d osmen
```

---

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check Docker logs
docker-compose logs gateway

# Check resource usage
docker stats

# Verify network
docker network ls
```

#### Database Connection Failed

```bash
# Test connectivity
docker-compose exec gateway python -c "
import psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
print('Connected!')
"

# Check credentials
docker-compose exec postgres psql -U postgres -c "\l"
```

#### LLM Provider Errors

```bash
# Test OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Ollama
curl http://localhost:11434/api/tags
```

### Health Check Failures

```bash
# Check all components
curl http://localhost:8080/health/deep | jq

# Check specific service
docker-compose exec gateway curl http://postgres:5432
```

### Performance Issues

```bash
# Check resource usage
docker stats --no-stream

# Check database connections
docker-compose exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis memory
docker-compose exec redis redis-cli INFO memory
```

---

## Support

- **Documentation**: https://docs.osmen.io
- **GitHub Issues**: https://github.com/your-org/OsMEN/issues
- **Community Discord**: https://discord.gg/osmen

---

## Changelog

- **v3.0.0**: Initial production deployment guide
