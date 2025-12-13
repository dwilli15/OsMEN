# OsMEN v2 Refactor Kickoff — TEMP SPEC (Conversation-Backed)

**Filename:** `temp_spec.md`  
**Date:** 2025-12-12  
**Scope:** This document is the single starting point for the upcoming refactor session. It captures (a) the user’s operating constraints and decisions, (b) the “semester_start onboarding demo” incident and lessons, (c) required system integrations (n8n/Langflow/Chroma/Context7/etc.), and (d) current repo/status as of today.

---

## 0) Product Identity (Locked)

- **User model:** single-user personal system (not enterprise/team)
- **Primary platform:** Windows-first
- **Core identity:** ADHD/focus management + autonomous personal assistant
- **Agent autonomy:** full autonomy in normal operation (no constant confirmations)
- **This repository (D:\OsMEN) is not just “dev code”:** it is also the live local system that the student (you) uses.

Reference: the PHOENIX protocol agent mode spec in [.github/agents/osmen_agent_team_refactor.md](.github/agents/osmen_agent_team_refactor.md).

---

## 1) Hard Rules (User-Approved)

### 1.1 Repo Hygiene / Filesystem Policy

- **The primary directory `D:\OsMEN` must only contain** code/config/assets that serve OsMEN as a product/system.
- **Semester-specific artifacts must not “clog” the repo.**
  - Onboarding new semesters MUST happen in a **user-provided external path** (e.g., `D:\<semester_name>\...`).
  - If a use case lacks a designated workspace directory under `D:\OsMEN`, the system MUST prompt the user to provide a path.
- OsMEN is both:
  - a GitHub repository (source code), AND
  - a live system directory on your machine.

### 1.2 Canonical “Semester Workspace” Pattern

- Each semester has a **unique folder** (outside `D:\OsMEN`).
- That semester folder contains:
  - the Obsidian vault (if used)
  - any dependencies/artifacts required for that semester’s workflows (scripts, exports, transcripts, audio outputs, etc.)

### 1.3 Orchestration Expectation

- When using this chat (during development/refactor), the assistant must behave as a **partner to n8n**.
- “Constant contact with n8n” means:
  - n8n is treated as the execution fabric for scheduled/triggered actions
  - the assistant helps decide what belongs in code vs n8n vs Langflow
  - workflows are validated end-to-end, not just described

### 1.4 No Dry-Run for the Refactor

- You explicitly do NOT want a “dry run” mode for the refactor itself.
- We only get **one** realistic system-level validation run, but the refactor should aim to be complete before that.

### 1.5 Student Persona Simulation Requirement

- A subagent must adopt the persona of the **student user** and simulate:
  - full semester usage
  - daily check-ins
  - sample course notes
  - class transcripts
  - memory usage (recall, linking, temporal context)

### 1.6 Deletions

- Deletions are allowed **only if truly unused**.
- Caveat: some code may be unused because it was never integrated properly; deletion must be evidence-driven.

### 1.7 Templates / Scripts Policy

- Text files are “user prompt accepted” (i.e., user can approve/curate content), BUT:
  - weekly and daily check-in scripts and audio reports are **not optional**
  - they begin as **drafts generated at semester start** incorporating the syllabus
  - they are updated:
    - **daily**: updated day-of
    - **weekly**: updated on Friday of the previous week

### 1.8 End State

- The refactor ends with a final merge.
- After that, we create/operate a different agent persona:
  - a **super personal assistant agent**
  - it treats the repo as the program (not a workspace)
  - it should NOT have repo edit rights unless explicitly authorized

### 1.9 Repo Privacy (Operational Note)

- You want the GitHub repo switched to **private**.
- This cannot be performed from inside VS Code in this chat unless we have GitHub admin/API permissions available; treat as an owner action in GitHub settings.

---

## 2) What Happened (Key Conversation-Backed Events)

This is the minimum factual narrative we will carry into the refactor.

### 2.1 The “semester_start onboarding demo”

- A vault was created at `D:\semester_start\vault` as an onboarding demo.
- This created confusion because there were also repo-internal course paths being edited at one point.
- Lesson: **vault/semester artifacts must never end up inside repo directories**, and the system must enforce this.

### 2.2 Course duplication inside the repo

- A duplicate/incorrect course folder structure existed under `D:\OsMEN\content\courses\...`.
- It was later deleted to re-establish repo hygiene.

### 2.3 Audiobooks claim mismatch

- Initial “audiobooks” claims were challenged.
- Reality: an audiobook creator existed, but wasn’t actually producing course audiobooks at the time.
- Audiblez + Kokoro TTS was confirmed working with CUDA GPU enabled, voice `af_heart`.
- At least one real `.m4b` was successfully generated in the onboarding demo area.

### 2.4 Onboarding instructions discovery

- There was not a single consolidated “onboarding runbook” file initially.
- Evidence of intended onboarding automation exists as an n8n workflow:
  - `n8n/workflows/course_semester_setup.json` (and a `fixed/` variant)
  - it defines a webhook course import pipeline that calls gateway endpoints and memory store.

---

## 3) System Architecture — The Target Contract

### 3.1 Execution Fabric Split

- **n8n**: the automation fabric (schedules, webhooks, multi-step ops, retries, notifications)
- **Langflow**: reasoning graphs / LLM interaction flows that can be exported and versioned
- **OsMEN Python code**: stable APIs + agents + integrations (deterministic logic, IO, security)

### 3.2 Single Source of Truth

- OsMEN must have a single orchestration source of truth (historically referenced as `integrations/orchestration.py`).
- Any workflow/tool/agent should be discoverable via that registry layer, so that:
  - CLI, gateway, n8n, and Langflow don’t drift
  - paths and pipeline identifiers remain stable

### 3.3 Memory System Requirements (Obsidian-Equivalent)

Minimum required capabilities:

- hierarchical tagging & categorization
- topic synchronization across sources
- short-term working memory
- long-term embeddings vector store
- semantic recall & similarity search
- temporal context (“what was I doing when?”)
- bidirectional linking
- incremental learning from interactions

Important: **Obsidian integration is optional, not a dependency**.

### 3.4 Required External Integrations

Must exist and be operational:

- Google Calendar + Gmail (OAuth)
- Outlook Calendar + Email (Graph/OAuth)
- GitHub integration
- Live transcription pipeline (Zoom/courses) feeding memory

---

## 4) Repo Reality Check (Existing Assets Worth Preserving)

This section anchors to existing repository documents and implementations.

### 4.1 “Conversation/Runtime” known issue

- The repository contains a troubleshooting spec about Copilot Chat runtime/caching issues:
  - [CONVERSATION_SPEC_SHEET.md](CONVERSATION_SPEC_SHEET.md)
  - it is about VS Code Copilot cache corruption and shell session failures.

### 4.2 Operational guides exist

- High-level navigation / product evaluation:
  - [START_HERE.md](START_HERE.md)
- Scenarios that explicitly describe n8n + Langflow usage:
  - [SCENARIOS.md](SCENARIOS.md)

### 4.3 OAuth workflow exists

- The repo includes OAuth-based workflow scaffolding and docs:
  - [OAUTH_IMPLEMENTATION_SUMMARY.md](OAUTH_IMPLEMENTATION_SUMMARY.md)
  - [OAUTH_QUICKSTART.md](OAUTH_QUICKSTART.md)
  - plus docs under `docs/`

This is relevant because you want Copilot/model access to be a first-class orchestration component.

---

## 5) Guardrails to Implement During Refactor (Non-Negotiable)

### 5.1 Workspace isolation (no semester artifacts in repo)

- Any “semester onboarding” action MUST require a user-specified external base directory.
- Any attempt to write to a path under `D:\OsMEN` for semester artifacts must hard-fail (or be rerouted) unless explicitly a product asset.

### 5.2 Workflow coherence

- If a feature is “automated,” it should have:
  - a stable gateway/CLI entrypoint
  - a tested n8n workflow (or n8n importable JSON)
  - a versioned Langflow flow if LLM reasoning is core

### 5.3 Evidence-driven deletions

- Before deleting modules/agents/workflows:
  - identify references (imports, CLI hooks, gateway routes, orchestration registry, n8n HTTP calls)
  - confirm not used by tests and not required by docs

### 5.4 Build/test gating

- Changes should not regress:
  - core agent tests
  - infrastructure tests
  - OAuth integration tests (where configured)

---

## 6) Current Status Snapshot (As Of This Chat)

- Repo is on branch `main` (per workspace metadata).
- The user has explicitly approved:
  - strict repo hygiene
  - n8n + Langflow usage now (not later)
  - no refactor dry-run
  - student persona simulation requirement
  - non-optional daily/weekly templates/scripts policy
  - final merge then transition to non-dev personal agent persona
- Known operational outcomes from earlier work (outside repo):
  - onboarding demo vault created externally (`D:\semester_start\vault`)
  - at least one audiobook `.m4b` produced under `D:\semester_start\audiobooks` using GPU

---

## 7) Refactor Session Kickoff Checklist (Next Chat)

The next chat session should start by doing these, in order:

1. **Create refactor branch** (name to be confirmed in-session; user earlier requested “core upgrades”).
2. **Inventory & wire-up verification**:
   - confirm n8n workflows exist and are the authoritative automation entrypoints
   - confirm Langflow flows exist and are versioned
   - confirm gateway routes used by n8n actually exist and match expected schemas
3. **Establish canonical path policy**:
   - central config for external workspace roots
   - hard guardrail preventing semester artifacts inside repo
4. **Define the student-simulation harness**:
   - scripted “semester run” that generates daily check-ins, notes, transcripts
   - verify memory recall and weekly/daily update cadence
5. **Harden & de-stub**:
   - remove placeholders and integrate orphaned-but-intended modules
   - ensure every major feature has a tested execution path

---

## 8) Recommendation: VS Code Chat vs n8n/Langflow vs Copilot CLI

You’re right to question the tool split. Here’s the cleanest division that matches your requirements:

- **VS Code Chat**: best for refactor execution (editing code, tests, repo-wide changes). It is not a reliable long-running orchestrator by itself.
- **n8n**: should be the always-on, operational orchestrator (schedules/webhooks/retries/audit). It’s the “runtime brainstem.”
- **Langflow**: should host the reasoning graphs and tool-calling logic that benefits from visual composition/versioning.
- **Copilot CLI (or a model gateway)**: should be the hub for model access inside workflows if you want consistent model invocation outside VS Code.

Practical takeaway:

- Don’t “stop” using VS Code for refactor work.
- Do move day-to-day operational orchestration into **n8n + Langflow**, with VS Code used to maintain the program.

---

## 9) Open Items (Owner Actions / Non-Code)

- Switch GitHub repo visibility to **Private** (owner action in GitHub settings).
- Decide whether the operational assistant agent will be deployed as:
  - a constrained local service that calls stable APIs, or
  - an n8n/Langflow-first agent that treats Python code as tools.

---
