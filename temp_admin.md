# TEMP: Admin Agent Instructions (4th Agent)

Purpose: Analyze, optimize, and de-duplicate the repository; resolve conflicts and redundancies; consolidate artifacts; and remove the 3-agent framework. When complete, remove this file and any temporary coordination files to leave a clean, production-ready repo.

Status: Temporary instruction – do NOT commit this file yet. Admin should only commit consolidation changes once Alpha, Beta, and Gamma complete all planned days (Hour 144), and remove this file in the final cleanup commit.

---

## Mission Objectives
- Single-owner cleanup pass across code, tests, docs, and CI/dev scripts.
- Identify and remove redundant files, dead code, stale branches, and duplicated documentation.
- Resolve merge conflicts and overlapping responsibilities created by multi-agent parallelization.
- Consolidate the multi-agent scaffolding into a single, clean, production layout.
- Validate the stack (build, tests, security checks) and ensure docs reflect final state.
- Self-cleanup: delete this `temp_admin.md` and any other temporary coordination artifacts.

---

## Operating Guardrails
- Do not expose secrets. Never commit `.env` or real credentials.
- Prefer minimal, targeted edits; avoid broad refactors unless they remove duplication or fix conflicts.
- Preserve working behavior. If removing a file, confirm it has no live references (imports, scripts, CI jobs, or docs).
- Always run validations (`make validate` or equivalent) between phases.
- Keep commits atomic with clear messages. If large changes are needed, split by subsystem (web, integrations, docs).

---

## Deliverables
- Clean, consolidated repository without multi-agent scaffolding and redundant files.
- Resolved conflicts, eliminated duplicates, updated documentation.
- Passing tests and validations.
- Final summary commit message and removal of `temp_admin.md`.

---

## Execution Plan (Phased)

1. Repo Analysis
   - Inventory branches and local worktrees; identify drift from `main`.
   - Enumerate temporary/coordination artifacts and per-agent docs.
   - Build a quick dependency graph: imports, entry points, scripts, tests.

2. Redundancy + Conflict Resolution
   - Deduplicate overlapping modules, templates, or endpoints.
   - Resolve any divergent implementations created by agents (prefer the most complete, tested path).
   - Normalize file locations and naming conventions to match repo standards.

3. Consolidation and Framework Removal
   - Remove multi-agent framework artifacts once consolidated:
     - Coordination logs: `3agent_chat.md` (after info copied into CHANGELOG/STATUS as needed).
     - Per-agent task lists and distribution docs if superseded (`AGENT_*` files), or migrate key content into canonical docs under `docs/`.
     - Worktree scaffolding under `.worktrees/` if no longer needed.
   - Ensure the dashboard, API, scheduling, and integrations remain fully functional (no dead references).

4. Validation and Hardening
   - Run: unit + integration tests; performance and resilience tests if available.
   - Run: operational and security validations.
   - Docs pass: update quick start, setup, and production deployment pages to reflect the consolidated architecture.

5. Cleanup and Self-Removal
   - Remove temporary artifacts, including this `temp_admin.md`.
   - Re-run validations; ensure the repo is clean and ready.

---

## Concrete Checklist

Branch and Worktree Hygiene:
- [ ] List branches; rebase/squash as needed; standardize naming.
- [ ] Remove `.worktrees/*` if obsolete.

Files and Structure:
- [ ] Remove `3agent_chat.md` after extracting useful notes into `CHANGELOG.md` / `STATUS.md`.
- [ ] Review and remove or archive agent-specific docs: `AGENT_ALPHA_TASKS.md`, `AGENT_DISTRIBUTION_SUMMARY.md`, set of `AGENT_*` where content is superseded by canonical docs.
- [ ] Ensure `web/`, `integrations/`, `scheduling/`, `reminders/`, `gateway/` reflect final single-owner structures.
- [ ] Keep environment examples: `.env.example`, `.env.production.example`; never add real secrets.

Tests and Validation:
- [ ] `python -m pytest -q` or equivalent test runners
- [ ] `python run_all_tests.py` (if applicable)
- [ ] `make validate` (security + tests + operational)

Docs:
- [ ] Update `README.md` quick start to reflect final flows.
- [ ] Ensure `docs/USAGE.md`, `docs/SETUP.md`, `docs/PRODUCTION_DEPLOYMENT.md` match consolidated structure.

Self-Removal:
- [ ] Delete `temp_admin.md` in the final commit after validations pass.

---

## Alpha Completed TODOs (for progress context)
You are the Admin agent; the following list shows only the Alpha agent’s completed items. Use this as reference when consolidating.

Alpha (Integration & Core Features):
- A1.1: Calendar OAuth endpoints (Google & Outlook) in `web/main.py`; UI at `web/templates/calendar_setup.html`.
- A1.2: Syllabus upload UI (`web/templates/syllabus_upload.html`) and API (upload/progress/cancel) in `web/main.py`.
- A1.3: Event preview backend routes in `web/main.py` (update/bulk actions for parsed events).
- A1.4: Event preview UI (`web/templates/event_preview.html`) with inline edit, reject, accept-all, and sync trigger.
- A1.5: Calendar sync endpoint `POST /api/calendar/sync` (via `integrations/calendar/CalendarManager`, auto-select provider).
- A1.6: Schedule generation endpoint `POST /api/schedule/generate` (uses `scheduling/priority_ranker.py` + `scheduling/schedule_optimizer.py`).
- A1.7: Task source stubs `GET /api/tasks/todoist` and `GET /api/tasks/notion` (integration pending).
- A1.8: Priority ranking API `POST /api/priority/rank` for tasks/events (supports `upload_id`).

Beta (Infrastructure & Security):
- [No items recorded here by Alpha; Admin should inventory and extract from commit history and docs.]

Gamma (Testing & Quality):
- [No items recorded here by Alpha; Admin should inventory and extract from test runs and commit history.]

---

## Suggested Commands (PowerShell)

```pwsh
# Validate
python -m pytest -q
python run_all_tests.py
make validate

# Search for references before removing a file
git grep -n "3agent_chat.md"

# Remove obsolete worktrees (if present/unused)
# Note: Ensure there are no uncommitted changes within those trees
Remove-Item -Recurse -Force .worktrees

# After cleanup and validations
git add -A
git commit -m "chore(admin): consolidate repo, remove multi-agent scaffolding, docs updated"
# Remove this temp file as last step
git rm temp_admin.md
git commit -m "chore(admin): remove temp_admin.md"
```

---

## Rollback Plan
- Keep changes atomic; revert any problematic commit via `git revert`.
- If a removal breaks imports or tests, restore the file, add deprecation notes, and replace incrementally.
- Maintain a short-lived branch with the pre-cleanup state until consolidation is fully validated.

---

## Final Notes
- This is a temporary instruction artifact. Delete `temp_admin.md` when the consolidation is complete and validated.
- If any ambiguity arises, prefer working, test-covered paths and update docs accordingly.
