# Agent Gamma Restart Spec (v1.7.0 - 6-Day Accelerated Plan)

## Kickoff Checklist (Day 1)
- [x] Clean checkout on `agent-gamma-testing` (dedicated `.worktrees/gamma` worktree)
- [x] Sync with `main` (UTC 2025-11-12 10:45); tracking Alpha/Beta branches read-only
- [x] Coordination log updated from Gamma branch (`3agent_chat.md`, 10:50 UTC)
- [x] Consolidate duplicate `D:\OsMEN*` directories -> target state: single synced repo (2025-11-12 21:45 UTC). Contents from `D:\OsMENs` moved to `D:\OsMEN_archives\`; empty shell remains pinned by Windows handles and can be removed once no processes keep it open.
- [x] Confirm Alpha/Beta handoff checklist compliance before 48h merge window (2025-11-12 21:50 UTC) — Alpha still has uncommitted diffs and Beta queue not started, so checklist is not yet satisfied; status logged for merge-planning awareness.

## Governance & Communication
- Single-source log: `3agent_chat.md` (Gamma updates after each test block with `[Timestamp] GAMMA | Status`).
- Branch discipline: commits remain on `agent-gamma-testing`; cross-branch edits require explicit request in log.
- Evidence capture: archive pytest output + key logs under `logs/gamma/<date>/`.
- Blockers flagged with `[BLOCKER]` prefix + owner/action.

## G1.1 - G1.4 Validation Scope (Days 1-2)

### G1.1: Revalidate A1.1 Calendar OAuth Endpoints
**Coverage Targets**
- Extend `test_calendar_integration.py` with pytest cases for:
  - `/api/calendar/google/oauth` + `/api/calendar/outlook/oauth` handshake stubs (mock provider secrets, assert redirect URIs).
  - Callback handler validation: missing code/state, token exchange failures, credential persistence.
  - Provider availability toggles (`CalendarManager.providers`, `primary_provider` fallback).
- Instrument `integrations/calendar/google_calendar.py` + `outlook_calendar.py` with dependency injection hooks for mock clients (facilitates offline tests).
**Artifacts**
- Pytest markers `alpha_a1_1` for targeted runs.
- Log capture: `logs/gamma/2025-11-12/oauth_validation.log`.

### G1.2: Syllabus Upload Endpoint (A1.2) Validation
**Coverage Targets**
- Add fast tests in `test_agents.py` or new `tests/test_syllabus_upload.py` to simulate multipart upload via FastAPI test client (`web/main.py`).
- Inputs:
  - Valid PDF/DOCX from `tests/fixtures/syllabi`.
  - Oversized/invalid mime to assert 4xx responses.
- Verify async processing shim (Celery/background queue) is invoked; stub queue if not available.
- Track throughput metric (<5s) by timing handler; log to `logs/gamma/...`.
- [x] `test_syllabus_upload.py` (Gamma-only) stubs `SyllabusParser`, covers PDF happy path, unsupported extensions, and >10 MB guardrails; upload route now re-raises FastAPI `HTTPException`s and seeds `active_uploads`.

### G1.3: Parser + Calendar Pipeline Integration (A1.3)
**Coverage Targets**
- Create integration test harness that chains:
  1. `parsers/syllabus/syllabus_parser.py` -> event payload
  2. `integrations/calendar/multi_calendar_sync.py` -> normalized events
  3. `scheduling/priority_ranker.py` for conflict detection.
- Validate conflict resolution + batch event creation (simulate 5-10 events).
- Expand fixtures in `tests/fixtures/syllabi/expected_results.json` to include conflict-heavy schedule.
- Document pipeline assumptions + error handling in this spec.
- [x] `test_parser_calendar_pipeline.py` chains `SyllabusParser.normalize_data` → `PriorityRanker` → `MultiCalendarSync` with stub calendars, ensuring conflict detection and sync-map population across Google/Outlook stubs.

### G1.4: Event Preview UI (A1.4) Readiness
**Coverage Targets**
- Frontend smoke: use `pytest + playwright` (or Selenium-lite) to validate `web/templates/event_preview.html` once Alpha lands UI.
- Backend: add FastAPI test ensuring preview endpoint returns parsed events + conflict metadata.
- Manual QA checklist (table rendering, bulk accept/reject, individual edit) to run after UI merges.
- [x] Backend preview retrieval now validated via `test_syllabus_upload.py::test_syllabus_preview_endpoint_returns_normalized_data`; awaiting Alpha UI drop before Playwright/QA automation.

## Regression Harness & Infra Hooks (Beta Dependencies)
- Mirror Beta's compose stack once `docker-compose.prod.yml` stabilizes; plan `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build` smoke test.
- Consume Beta secrets tooling: define `.env.gamma` referencing sanitized secrets; never reuse Alpha creds.
- Security sweeps:
  - Static scan via `pip install bandit && bandit -r integrations/calendar parsers/syllabus`.
  - Dependency check: `pip install safety && safety check`.
- Logging: standardize `pytest -q --maxfail=1 --disable-warnings -k "gamma or alpha_a1"` for regression gate.
- [x] Authored `docs/GAMMA_REGRESSION_PLAN.md` outlining compose/secrets flow, command matrix, and evidence expectations; initial logs captured under `logs/gamma/2025-11-13/`.

## Outstanding Risks & Actions
- **Alpha uncommitted diffset**: remains in base workspace; cannot merge until Alpha commits/stashes. Gamma isolated but cross-branch PR will block. (Owner: Alpha)
- **Beta secrets compose**: pending; regression harness blocked until provided. (Owner: Beta)
- **Directory duplication**: `D:\OsMEN` + `D:\OsMENs` both contain repo assets. Plan: archive whichever is stale, confirm only synced directory remains, update documentation. (Owner: Ops, support from Gamma for verification)

## Immediate Next Actions (Prioritized)
1. Coordinate with Alpha on the event preview UI delivery + schedule Playwright smoke tests (G1.4 frontend).
2. Run the regression harness against Beta’s compose stack once secrets drop arrives; prep `.env.gamma` + compose overrides.
3. Continue capturing evidence for each test block under `logs/gamma/<date>/`.
4. Track Alpha diff cleanup and Beta secrets status in `3agent_chat.md` ahead of the 48 h merge checkpoint.
5. Schedule bandit + safety sweeps before the next merge window.
