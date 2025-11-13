# AGENT BETA TASK LIST & RESTART SPEC
**Role:** Infrastructure & Security Lead  
**Branch:** `agent-beta-infrastructure` (reset to `origin/main` via `.worktrees/beta`)  
**Plan:** 6-Day Accelerated Launch → Focus on Day 1-2 (B1.1-B1.8)  
**Status:** Hour 0 / 48 — 0 / 48 tasks complete  
**Shared Secret Echo:** OsMEN v1.7.0 | Accelerated Plan | merge points @ 48h/96h/144h

---

## 🔐 RESTART DIRECTIVES
- ✅ Identity lock recorded in `3agent_chat.md` (2025-11-12 10:49 UTC) with branch, status, and shared-secret verification.
- ✅ Dedicated worktree at `.worktrees/beta` created with `git worktree add -B agent-beta-infrastructure .worktrees/beta origin/main` to guarantee clean checkouts.
- ✅ Legacy `[temp-switch]` stash dropped to prevent further drift. Remaining stashes are scoped to Alpha WIP and historical Beta WIP (do not apply without review).
- ✅ Coordination cadence: log progress/blockers in `3agent_chat.md` after every major milestone (B1.* block, security scan, infra delivery).
- 🚩 Guardrails: no commits from other agent branches, keep security artefacts (vault secrets, TLS certs) out of git, and re-run `scripts/automation/validate_security.py` after every credential change.

---

## 📦 PRODUCTION ASSETS SNAPSHOT (B1.1)
- `docker-compose.prod.yml` — production-only stack with health checks, explicit networks, and env-file driven secrets.
- `.env.production.example` — hardened template; copy to `.env.production`, supply strong secrets, and ensure file permissions `chmod 600` before deploy.
- `scripts/automation/validate_security.py` — run with `PYTHONIOENCODING=UTF-8 python3 ...` to validate .env presence, permissions, and default passwords.
- Launch verification:
  ```bash
  cp .env.production.example .env.production   # edit secure values first
  docker compose -f docker-compose.prod.yml config
  docker compose -f docker-compose.prod.yml up -d
  ```

---

## 🛡️ SECURITY BASELINE (2025-11-12 10:55 UTC)
| Level | Check | Result | Planned Action |
|-------|-------|--------|----------------|
| Critical | `.env` missing | ❌ | Copy `.env.example` → `.env` locally (ignored) before running tooling; enforce same for production `.env.production`. |
| Warning | `config/firewall_baseline.yaml` world-readable | ⚠️ | Restrict permissions in deployment package (`chmod 600 config/firewall_baseline.yaml`) and document requirement in ops runbook. |
| Info | Default credentials (n8n/admin, etc.) | ⚠️ contextual | Use new `.env.production.example` values and require rotation checklist before handoff. |

> Re-run the validator after provisioning `.env` / `.env.production`; fail deployment if any critical issue remains.

---

## 📋 DAY 1 TASKS (HOUR 0-24)

### B1.1 Production Docker Configuration (3h)
**Files:** `docker-compose.prod.yml`, `.env.production.example`, `start.sh`, `docs/PRODUCTION_DEPLOYMENT.md`  
**Checklist:**
- [x] Map every service (postgres, redis, qdrant, langflow, n8n, gateway, mcp, ollama) with `healthcheck` blocks and `depends_on` conditions.
- [x] Ensure env vars never embed secrets directly; reference `.env.production` only.
- [x] Harden networks: single internal bridge (`osmen-internal`), expose only gateway/mcp/ollama through host ports.
- [x] Document `docker compose` workflows in `PRODUCTION_DEPLOYMENT.md`.

### B1.2 Service-Level Health Checks (3h)
**Files:** `gateway/gateway.py`, `gateway/mcp_server.py`, `web/status.py`, `scripts/check_operational.py`  
**Checklist:**
- [x] Expand `/health` to include DB + Redis smoke queries and propagate status codes.
- [x] Add `/healthz` endpoints for postgres/redis/qdrant containers via lightweight FastAPI router or sidecar.
- [x] Wire `web/status.py` to real host paths/env vars instead of Actions paths.
- [x] Provide CLI `scripts/check_operational.py --all` aggregator for Gamma to reuse.

### B1.3 Secrets Management (3h)
**Files:** `.env.production.example`, `config/boot_hardening_settings.yaml`, `scripts/automation/validate_security.py`, `docs/PRODUCTION_READINESS_PLAN.md`  
**Checklist:**
- [x] Define required secrets (API keys, DB creds, session keys) + ownership in doc.
- [x] Enforce runtime checks (e.g., `SESSION_SECRET_KEY` length) inside `gateway/gateway.py` startup.
- [x] Document vault workflow (e.g., 1Password / AWS Secrets Manager) and rotate defaults (`N8N_BASIC_AUTH_PASSWORD`, postgres, redis) before deploy.

### B1.4 TLS / HTTPS Configuration (3h)
**Files:** `gateway/gateway.py`, `start.sh`, `docs/PRODUCTION_DEPLOYMENT.md`  
**Checklist:**
- [x] Terminate TLS via nginx/Caddy fronting gateway + MCP (optionally use Let's Encrypt).
- [x] Enforce HTTPS redirects + HSTS headers (FastAPI middleware or proxy config).
- [x] Provide certificate provisioning runbook (acme.sh or certbot) with renewal steps.

### B1.5 Authentication Hardening (3h)
**Files:** `web/auth.py`, `web/main.py`, `web/templates/login.html`, `gateway/gateway.py`  
**Checklist:**
- [x] Replace default admin credentials with env-driven bcrypt hashes, supply helper script to generate.
- [x] Enforce session expiration + secure cookies (`SESSION_SECRET_KEY`, `SESSION_COOKIE_SECURE` under TLS).
- [x] Audit OAuth/token storage so user secrets never land in plain files.

### B1.6 RBAC / Permissions (3h)
**Files:** `web/auth.py`, `gateway/config/agents.json`, `config/teams/core_operations.json`, `config/access_control.json`  
**Checklist:**
- [x] Define roles (`admin`, `operator`, `viewer`) + per-route dependencies via `role_required`.
- [x] Gate sensitive endpoints (agent management, secrets) behind RBAC decorator.
- [x] Store role assignments in `config/access_control.json` + team metadata (`required_role`).

### B1.7 Rate Limiting & DoS Protection (3h)
**Files:** `gateway/rate_limiter.py`, `gateway/gateway.py`, `web/auth.py`, `docs/PRODUCTION_READINESS_PLAN.md`  
**Checklist:**
- [x] Implement middleware (Redis-backed token bucket) for API + auth endpoints.
- [x] Separate limits for `/completion`, `/api/agents/*`, `/health`, and throttle login attempts.
- [x] Surface configuration knobs via env vars (`RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_PREFIX`).

### B1.8 Security Headers & Scanning (3h)
**Files:** `web/main.py`, `web/templates/base.html`, `start.sh`, `scripts/automation/validate_security.py`, `docs/SECRETS_MANAGEMENT.md`  
**Checklist:**
- [x] Apply CSP, HSTS, X-Frame-Options, Referrer-Policy via FastAPI middleware.
- [x] Enable CSRF tokens for form posts (login/digest/upload) and document how Gamma can test.
- [x] Integrate automated scanners (`bandit`, `safety`) into `validate_security.py` + add docs/startup hooks.

---

## 📋 DAY 2 TASKS (HOUR 24-48)

### B2.1 Database Setup & Migrations (3h)
**Files:** `postgres/init/`, `config/firewall_baseline.yaml`, `docs/PRODUCTION_DEPLOYMENT.md`  
**Checklist:** schema migrations, connection pooling, backup users.

### B2.2 Qdrant Configuration (3h)
**Files:** `qdrant/`, `integrations/knowledge/`, `scripts/automation/setup_first_team.py`  
**Checklist:** indexes, snapshots, ACLs.

### B2.3 Redis Caching (3h)
**Files:** `redis/`, `web/status.py`, `gateway/gateway.py`  
**Checklist:** TTL policies, eviction alerts, session store hardening.

### B2.4 Logging Infrastructure (3h)
**Files:** `logs/`, `gateway/resilience.py`, `scripts/innovation/notifications.py`  
**Checklist:** structured logging, log rotation, forwarding to ELK/OpenSearch.

### B2.5 Error Tracking (3h)
**Files:** `web/main.py`, `gateway/gateway.py`, `.env.production.example`  
**Checklist:** Sentry (DSN env var), release tagging, alert routing.

### B2.6 Monitoring Setup (3h)
**Files:** `scripts/check_operational.py`, `Makefile`, `docs/PRODUCTION_READINESS_PLAN.md`  
**Checklist:** metrics endpoint, dashboards, alert thresholds.

### B2.7 Backup Automation (3h)
**Files:** `scripts/automation/`, `postgres/init/backup.sql`, `docs/PRODUCTION_DEPLOYMENT.md`  
**Checklist:** nightly DB + file backups, verification playbook.

### B2.8 CI/CD Pipeline (3h)
**Files:** `.github/workflows/`, `Makefile`, `PRODUCTION_READY.md`  
**Checklist:** gated builds, security scan jobs, deploy promotion.

---

## 📞 HANDOFF NOTES
- Gamma: expect sanitized `.env.production.example`, documented health endpoints, and rate-limit metrics once B1.* complete.
- Alpha: Beta to notify when OAuth secret storage + RBAC hooks land, since UI will depend on them.
- Merge Point 1 (Hour 48): re-run full Docker + security validation, update `3agent_chat.md` with readiness checklist, and coordinate with Gamma for testing window.
