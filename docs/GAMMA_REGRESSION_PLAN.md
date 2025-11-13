# Gamma Regression Harness Plan

## Purpose
Provide a repeatable validation harness for Gamma covering Alpha (A1.x) and Beta (B1.x) deliverables before each 48-hour merge checkpoint. The harness composes unit, integration, and full-stack checks using Beta's infrastructure artifacts (docker compose + secrets) while preserving Gamma's branch isolation.

## Environments
| Layer | Source | Notes |
|-------|--------|-------|
| Local worktree | `.worktrees/gamma` | Dedicated Gamma checkout; no Alpha/Beta diffs |
| Containers | `docker-compose.yml` + `docker-compose.prod.yml` | Run via `docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build` once Beta secrets land |
| Secrets | `.env.gamma` | Sanitized copy of Beta's secret bundle; mount via compose overrides |

## Setup Steps
1. `git fetch origin && git -C .worktrees/gamma pull --ff-only`
2. `pip install --break-system-packages pytest fastapi itsdangerous reportlab psutil python-multipart`
3. Populate `.env.gamma` from Beta; set `COMPOSE_PROFILES=gamma-regression`
4. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d db redis gateway`
5. `python scripts/automation/setup_first_team.py --env gamma` (if migrations/seeding needed)

## Test Matrix
| Layer | Command | Purpose |
|-------|---------|---------|
| Fast unit/integration | `/home/dwill/.local/bin/pytest -q test_calendar_integration.py test_agents.py test_syllabus_upload.py test_parser_calendar_pipeline.py` | Validates A1.1–A1.4 + parser/scheduling bridges |
| API smoke (compose) | `scripts/automation/test_llm_providers.py --env gamma` | Ensures containerized endpoints respond |
| Security sweep | `bandit -r integrations/calendar parsers/syllabus scheduling` | Static scan (Beta dependency) |
| Dependency scan | `safety check --full-report` | CVE drift |
| Manual UI (post Alpha UI drop) | Playwright checklist | Confirms event preview UX |

## Evidence & Logging
- Capture `pytest -s` output to `logs/gamma/<ISO_DATE>/pytest.log`
- When compose runs, store `docker compose logs` alongside artifacts
- Update `logs/gamma/<date>/TEST_RUNS.md` with timestamped commands (+ pass/fail)

## Merge-Ready Checklist Hooks
1. Confirm Gamma test suite green
2. Document Alpha/Beta blockers in `3agent_chat.md`
3. Attach evidence paths when requesting merge review

## Open Items
- Await Beta's sanitized compose + secrets bundle
- Add Playwright automation once Alpha lands `event_preview.html`
