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

## 7) CORE-UPGRADES Branch — Detailed Execution Plan

### 7.0 Branch Creation & Setup

```bash
git checkout -b core-upgrades
```

**Commit conventions during refactor:**

- `[SKELETON]` — core architecture / orchestration changes
- `[NERVOUS]` — agent implementation changes
- `[CIRCULATORY]` — gateway / CLI / data flow changes
- `[IMMUNE]` — security / validation / error handling
- `[MUSCULAR]` — tools / workflows / automation
- `[MEMORY]` — hybrid memory system changes
- `[SCRIBE]` — transcription pipeline changes
- `[DOCS]` — documentation only

---

### 7.1 PHASE 0: Reconnaissance & Inventory (Day 1)

**Objective:** Complete map of every file, function, dependency, and integration point.

#### 7.1.1 File/Module Inventory

| Directory | Action | Deliverable |
|-----------|--------|-------------|
| `integrations/` | Full AST scan, import graph | `inventory/integrations_map.json` |
| `agents/` | List all agents, their interfaces, test coverage | `inventory/agents_map.json` |
| `gateway/` | List all routes, their handlers, request/response schemas | `inventory/gateway_routes.json` |
| `cli_bridge/` | Map CLI commands to functions | `inventory/cli_commands.json` |
| `n8n/workflows/` | Parse all workflow JSONs, extract HTTP endpoints called | `inventory/n8n_endpoints.json` |
| `langflow/flows/` | Parse all flow JSONs, extract component dependencies | `inventory/langflow_components.json` |
| `tools/` | List tool integrations and their status | `inventory/tools_status.json` |
| `tests/` | Map test files to modules they cover | `inventory/test_coverage.json` |

#### 7.1.2 Dependency Analysis

- **Python imports:** generate full import graph, identify circular dependencies
- **n8n → Gateway:** verify every HTTP node URL in n8n workflows has a matching gateway route
- **Langflow → Python:** verify every custom component imports exist
- **CLI → Agents:** verify every CLI command's target function exists

#### 7.1.3 Dead Code Detection

- Identify modules with 0 imports from other modules
- Identify functions/classes with 0 call sites
- Cross-reference against n8n workflows (they may call via HTTP, not import)
- Flag but do not delete until Phase 6

#### 7.1.4 Hardcoded Value Extraction

- Scan for hardcoded paths (especially `D:\...`, `/home/...`, `C:\...`)
- Scan for hardcoded URLs (localhost ports, external APIs)
- Scan for magic numbers and string literals
- Output: `inventory/hardcoded_values.json`

---

### 7.2 PHASE 1: Orchestration Layer Hardening (Days 2-3)

**Objective:** Establish `integrations/orchestration.py` as the single source of truth.

#### 7.2.1 Paths Registry

All filesystem paths must be registered centrally:

```python
# integrations/orchestration.py

class Paths:
    """Canonical path registry - ALL paths must be defined here."""
    
    # === REPO INTERNAL (safe to reference) ===
    REPO_ROOT = Path("D:/OsMEN")
    AGENTS_DIR = REPO_ROOT / "agents"
    INTEGRATIONS_DIR = REPO_ROOT / "integrations"
    GATEWAY_DIR = REPO_ROOT / "gateway"
    N8N_WORKFLOWS = REPO_ROOT / "n8n/workflows"
    LANGFLOW_FLOWS = REPO_ROOT / "langflow/flows"
    CONFIG_DIR = REPO_ROOT / "config"
    LOGS_DIR = REPO_ROOT / "logs"
    
    # === EXTERNAL (must be user-configured) ===
    _external_workspace: Optional[Path] = None
    
    @classmethod
    def get_semester_workspace(cls) -> Path:
        """Returns external workspace path. Raises if not configured."""
        if cls._external_workspace is None:
            raise WorkspaceNotConfiguredError(
                "Semester workspace not configured. "
                "Set OSMEN_SEMESTER_WORKSPACE in .env or call configure_workspace()"
            )
        return cls._external_workspace
    
    @classmethod
    def configure_workspace(cls, path: str) -> Path:
        """Set external workspace. Validates it's not inside repo."""
        p = Path(path).resolve()
        if cls.REPO_ROOT in p.parents or p == cls.REPO_ROOT:
            raise InvalidWorkspaceError(
                f"Workspace {p} is inside repo. "
                "Semester workspaces must be external to D:\\OsMEN"
            )
        cls._external_workspace = p
        return p
```

#### 7.2.2 Pipelines Registry

All automatable workflows must be registered:

```python
class Pipelines:
    """Canonical pipeline registry."""
    
    REGISTRY = {
        # === DAILY OPERATIONS ===
        "daily_briefing": {
            "description": "Generate morning briefing",
            "agent": "daily_brief",
            "gateway_route": "/api/agents/daily-brief/run",
            "n8n_workflow": "daily_brief_trigger.json",
            "langflow_flow": "daily_brief_flow.json",
            "schedule": "0 8 * * *",  # 8 AM daily
            "requires_workspace": False,
        },
        "am_checkin": {
            "description": "Morning check-in prompt",
            "agent": "daily_brief",
            "gateway_route": "/api/checkin/am",
            "n8n_workflow": "am_checkin_trigger.json",
            "schedule": "0 7 * * *",  # 7 AM daily
            "requires_workspace": True,
        },
        "pm_checkin": {
            "description": "Evening check-in prompt",
            "agent": "daily_brief",
            "gateway_route": "/api/checkin/pm",
            "n8n_workflow": "pm_checkin_trigger.json",
            "schedule": "0 21 * * *",  # 9 PM daily
            "requires_workspace": True,
        },
        
        # === SEMESTER OPERATIONS ===
        "semester_onboard": {
            "description": "Onboard new semester from syllabus",
            "agent": "intake_agent",
            "gateway_route": "/api/semester/onboard",
            "n8n_workflow": "course_semester_setup.json",
            "requires_workspace": True,
            "workspace_creates": ["vault/", "transcripts/", "audiobooks/", "notes/"],
        },
        "syllabus_analyze": {
            "description": "Parse and analyze syllabus PDF",
            "agent": "intake_agent",
            "gateway_route": "/api/syllabus/analyze",
            "requires_workspace": True,
        },
        "weekly_script_generate": {
            "description": "Generate weekly audio script",
            "agent": "daily_brief",
            "gateway_route": "/api/scripts/weekly",
            "n8n_workflow": "weekly_script_trigger.json",
            "schedule": "0 18 * * 5",  # 6 PM Friday
            "requires_workspace": True,
        },
        
        # === CONTENT CREATION ===
        "audiobook_convert": {
            "description": "Convert EPUB to M4B audiobook",
            "agent": "audiobook_creator",
            "gateway_route": "/api/audiobook/convert",
            "requires_workspace": True,
            "gpu_required": True,
        },
        "transcript_process": {
            "description": "Process live transcript into memory",
            "agent": "live_caption",
            "gateway_route": "/api/transcript/process",
            "requires_workspace": True,
        },
        
        # === INTEGRATIONS ===
        "calendar_sync_google": {
            "description": "Sync Google Calendar events",
            "agent": "personal_assistant",
            "gateway_route": "/api/calendar/google/sync",
            "n8n_workflow": "google_calendar_sync.json",
            "oauth_required": "google",
        },
        "calendar_sync_outlook": {
            "description": "Sync Outlook Calendar events",
            "agent": "personal_assistant",
            "gateway_route": "/api/calendar/outlook/sync",
            "n8n_workflow": "outlook_calendar_sync.json",
            "oauth_required": "microsoft",
        },
        "email_digest": {
            "description": "Generate email digest",
            "agent": "email_manager",
            "gateway_route": "/api/email/digest",
            "oauth_required": ["google", "microsoft"],
        },
    }
    
    @classmethod
    def get(cls, name: str) -> dict:
        if name not in cls.REGISTRY:
            raise PipelineNotFoundError(f"Pipeline '{name}' not registered")
        return cls.REGISTRY[name]
    
    @classmethod
    def get_by_agent(cls, agent_name: str) -> list[str]:
        return [k for k, v in cls.REGISTRY.items() if v.get("agent") == agent_name]
    
    @classmethod
    def get_scheduled(cls) -> list[str]:
        return [k for k, v in cls.REGISTRY.items() if v.get("schedule")]
```

#### 7.2.3 Agents Registry

```python
class Agents:
    """Canonical agent registry."""
    
    REGISTRY = {
        "daily_brief": {
            "module": "agents.daily_brief.daily_brief_agent",
            "class": "DailyBriefAgent",
            "status": "active",
            "test_file": "tests/test_daily_brief.py",
            "pipelines": ["daily_briefing", "am_checkin", "pm_checkin", "weekly_script_generate"],
        },
        "audiobook_creator": {
            "module": "agents.audiobook_creator.audiobook_creator_agent",
            "class": "AudiobookCreatorAgent",
            "status": "active",
            "test_file": "tests/test_audiobook_creator.py",
            "pipelines": ["audiobook_convert"],
            "gpu_accelerated": True,
        },
        "intake_agent": {
            "module": "agents.intake_agent.intake_agent",
            "class": "IntakeAgent",
            "status": "active",
            "pipelines": ["semester_onboard", "syllabus_analyze"],
        },
        "live_caption": {
            "module": "agents.live_caption.live_caption_agent",
            "class": "LiveCaptionAgent",
            "status": "needs_integration",
            "pipelines": ["transcript_process"],
        },
        "personal_assistant": {
            "module": "agents.personal_assistant.personal_assistant_agent",
            "class": "PersonalAssistantAgent",
            "status": "needs_integration",
            "pipelines": ["calendar_sync_google", "calendar_sync_outlook"],
        },
        "email_manager": {
            "module": "agents.email_manager.email_manager_agent",
            "class": "EmailManagerAgent",
            "status": "needs_integration",
            "pipelines": ["email_digest"],
        },
        "focus_guardrails": {
            "module": "agents.focus_guardrails.focus_guardrails_agent",
            "class": "FocusGuardrailsAgent",
            "status": "active",
            "pipelines": [],
        },
        "boot_hardening": {
            "module": "agents.boot_hardening.boot_hardening_agent",
            "class": "BootHardeningAgent",
            "status": "active",
            "pipelines": [],
        },
        "knowledge_management": {
            "module": "agents.knowledge_management.knowledge_management_agent",
            "class": "KnowledgeManagementAgent",
            "status": "active",
            "pipelines": [],
        },
        "librarian": {
            "module": "agents.librarian.librarian_agent",
            "class": "LibrarianAgent",
            "status": "needs_integration",
            "pipelines": [],
        },
    }
```

#### 7.2.4 Services Registry

```python
class Services:
    """Docker/infrastructure services registry."""
    
    REGISTRY = {
        "n8n": {
            "container": "osmen-n8n",
            "port": 5678,
            "health_endpoint": "/healthz",
            "required_for": ["scheduled_pipelines", "webhook_triggers"],
        },
        "langflow": {
            "container": "osmen-langflow",
            "port": 7860,
            "health_endpoint": "/health",
            "required_for": ["llm_reasoning_flows"],
        },
        "gateway": {
            "container": "osmen-gateway",
            "port": 8080,
            "health_endpoint": "/health",
            "required_for": ["api_access", "n8n_http_calls"],
        },
        "mcp_server": {
            "container": "osmen-mcp",
            "port": 8081,
            "health_endpoint": "/health",
            "required_for": ["memory_store", "tool_access"],
        },
        "chromadb": {
            "container": "osmen-chromadb",
            "port": 8000,
            "health_endpoint": "/api/v1/heartbeat",
            "required_for": ["vector_memory", "embeddings"],
        },
        "postgres": {
            "container": "osmen-postgres",
            "port": 5432,
            "required_for": ["persistent_storage", "n8n_backend"],
        },
        "redis": {
            "container": "osmen-redis",
            "port": 6379,
            "required_for": ["caching", "session_management"],
        },
    }
```

---

### 7.3 PHASE 2: Gateway & API Hardening (Days 4-5)

**Objective:** Ensure every n8n workflow HTTP call has a working gateway endpoint.

#### 7.3.1 Gateway Route Audit

For each route in `gateway/`:

| Check | Pass Criteria |
|-------|--------------|
| Route exists | Handler function defined |
| Request schema | Pydantic model or typed parameters |
| Response schema | Pydantic model with examples |
| Error handling | Proper HTTP status codes, structured errors |
| Authentication | Auth decorator where required |
| Logging | Request/response logged |
| Test exists | At least one test in `tests/` |

#### 7.3.2 n8n Workflow Validation

For each workflow in `n8n/workflows/`:

| Check | Pass Criteria |
|-------|--------------|
| HTTP endpoints valid | All URLs resolve to gateway routes |
| Auth configured | Credentials properly referenced |
| Error handling | Retry logic + error branch |
| Webhook security | Secret/signature validation |
| Schedule valid | Cron expression parses |
| Variables defined | No undefined `{{variables}}` |

#### 7.3.3 New Gateway Routes Required

Based on Pipelines registry, these routes must exist:

```
POST /api/agents/daily-brief/run
POST /api/checkin/am
POST /api/checkin/pm
POST /api/semester/onboard
POST /api/syllabus/analyze
POST /api/scripts/weekly
POST /api/audiobook/convert
POST /api/transcript/process
POST /api/calendar/google/sync
POST /api/calendar/outlook/sync
POST /api/email/digest
GET  /api/memory/recall
POST /api/memory/store
GET  /health
GET  /api/status
```

#### 7.3.4 Request/Response Schemas

```python
# gateway/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

# === CHECK-IN SCHEMAS ===

class CheckInRequest(BaseModel):
    """AM or PM check-in submission."""
    checkin_type: Literal["am", "pm"]
    mood: Optional[int] = Field(None, ge=1, le=10)
    energy: Optional[int] = Field(None, ge=1, le=10)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    tasks_planned: Optional[list[str]] = None
    tasks_completed: Optional[list[str]] = None
    notes: Optional[str] = None
    workspace_path: str = Field(..., description="External workspace path")

class CheckInResponse(BaseModel):
    """Check-in confirmation."""
    success: bool
    checkin_id: str
    timestamp: datetime
    memory_stored: bool
    briefing_triggered: bool = False

# === SEMESTER ONBOARD SCHEMAS ===

class SemesterOnboardRequest(BaseModel):
    """Onboard a new semester."""
    workspace_path: str = Field(..., description="External directory for semester")
    semester_name: str = Field(..., description="e.g., 'Spring2025'")
    syllabus_path: Optional[str] = None
    courses: list[dict] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class SemesterOnboardResponse(BaseModel):
    """Onboard result."""
    success: bool
    workspace_created: str
    folders_created: list[str]
    syllabus_analysis: Optional[dict] = None
    next_steps: list[str]

# === AUDIOBOOK SCHEMAS ===

class AudiobookConvertRequest(BaseModel):
    """Convert EPUB to audiobook."""
    epub_path: str
    output_dir: str
    voice: str = "af_heart"
    use_gpu: bool = True
    chapter_markers: bool = True

class AudiobookConvertResponse(BaseModel):
    """Conversion result."""
    success: bool
    output_path: Optional[str] = None
    duration_seconds: Optional[int] = None
    chapters: Optional[int] = None
    error: Optional[str] = None

# === MEMORY SCHEMAS ===

class MemoryStoreRequest(BaseModel):
    """Store a memory."""
    content: str
    content_type: Literal["note", "transcript", "checkin", "briefing", "task", "event"]
    source: str
    tags: list[str] = Field(default_factory=list)
    context: dict = Field(default_factory=dict)
    links_to: list[str] = Field(default_factory=list)

class MemoryRecallRequest(BaseModel):
    """Query memories."""
    query: str
    mode: Literal["semantic", "temporal", "linked"] = "semantic"
    n_results: int = Field(10, ge=1, le=100)
    filters: dict = Field(default_factory=dict)
```

---

### 7.4 PHASE 3: Memory System Implementation (Days 6-8)

**Objective:** Native memory system matching or exceeding Obsidian capabilities.

#### 7.4.1 Memory Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      HybridMemory API                           │
├─────────────────────────────────────────────────────────────────┤
│  remember(content, context, tags, links)                        │
│  recall(query, mode="semantic"|"temporal"|"linked", n=10)       │
│  recall_with_reasoning(query, n=5) → (results, reasoning_trace) │
│  link(source_id, target_id, relation_type)                      │
│  tag(memory_id, tags)                                           │
│  get_temporal_context(timestamp, window_hours=24)               │
│  maintenance() → prune stale, promote important                 │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   SHORT-TERM    │  │   LONG-TERM     │  │    LINKING      │
│   (SQLite FTS)  │  │   (ChromaDB)    │  │   (SQLite)      │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ - Working memory│  │ - Embeddings    │  │ - Bidirectional │
│ - Recent items  │  │ - Fast lookup   │  │ - Typed rels    │
│ - TTL-based     │  │ - Persistent    │  │ - Graph queries │
│                 │  │ - Similarity    │  │ - Backlinks     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

#### 7.4.2 Memory Schema

```python
@dataclass
class Memory:
    id: str  # UUID
    content: str
    content_type: Literal["note", "transcript", "checkin", "briefing", "task", "event"]
    source: str  # agent or user
    timestamp: datetime
    tags: list[str]
    context: dict  # structured metadata
    embedding: Optional[list[float]]  # 1536-dim
    
    # Temporal context
    session_id: Optional[str]  # group related memories
    parent_id: Optional[str]  # hierarchical
    
    # Lifecycle
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    promoted_to_longterm: bool = False
    ttl_hours: Optional[int] = None  # None = permanent

@dataclass
class MemoryLink:
    source_id: str
    target_id: str
    relation_type: str  # "references", "follows", "contradicts", "elaborates"
    created_at: datetime
    bidirectional: bool = True
```

#### 7.4.3 Required Memory Operations

| Operation | Description | Implementation |
|-----------|-------------|----------------|
| `remember()` | Store new memory | Insert SQLite + upsert ChromaDB |
| `recall()` | Query memories | Hybrid: FTS for recent, vector for semantic |
| `recall_temporal()` | Get context around time | SQLite range query |
| `link()` | Create bidirectional link | SQLite insert + update backlinks |
| `get_backlinks()` | Find what links to X | SQLite query on incoming_links |
| `tag()` | Add/update tags | SQLite update + reindex |
| `promote()` | Move short→long term | Based on access frequency |
| `prune()` | Remove stale short-term | TTL check |

---

### 7.5 PHASE 4: External Integrations (Days 9-12)

**Objective:** Working OAuth flows for Google, Microsoft, GitHub + live transcription.

#### 7.5.1 Google Integration

| Component | File | Status | Work Required |
|-----------|------|--------|---------------|
| OAuth module | `integrations/oauth/google_oauth.py` | EXISTS | Validate token refresh |
| Calendar read | `integrations/calendar/google_calendar.py` | EXISTS | Test with real account |
| Calendar write | same | PARTIAL | Implement event creation |
| Gmail read | `integrations/email/gmail.py` | MISSING | Create module |
| Gmail send | same | MISSING | Implement compose/send |

#### 7.5.2 Microsoft Integration

| Component | File | Status | Work Required |
|-----------|------|--------|---------------|
| OAuth module | `integrations/oauth/microsoft_oauth.py` | EXISTS | Validate Graph API scopes |
| Calendar read | `integrations/calendar/outlook_calendar.py` | PARTIAL | Test with real account |
| Calendar write | same | MISSING | Implement event creation |
| Outlook read | `integrations/email/outlook.py` | MISSING | Create module |
| Outlook send | same | MISSING | Implement compose/send |

**Required Graph API Scopes:**

```
Calendars.Read, Calendars.ReadWrite, Mail.Read, Mail.Send, User.Read
```

#### 7.5.3 Live Transcription Pipeline

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Audio Source    │────▶│  Whisper         │────▶│  Memory Store    │
│  (Zoom/System)   │     │  Transcription   │     │  + Summarize     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
        │                         │                        │
        ▼                         ▼                        ▼
   OBS/Loopback             Local GPU or             HybridMemory
   Audio Capture            OpenAI Whisper           + Auto-tagging
```

---

### 7.6 PHASE 5: Student Simulation Harness (Days 13-15)

**Objective:** Automated "semester run" that validates the entire system.

#### 7.6.1 Simulation Configuration

```python
SEMESTER_CONFIG = {
    "name": "Spring2025_Simulation",
    "start_date": "2025-01-13",
    "end_date": "2025-05-09",
    "courses": [
        {
            "code": "HB411",
            "name": "Healthy Boundaries",
            "schedule": "MWF 10:00-10:50",
            "readings_per_week": 2,
            "has_transcripts": True,
        },
    ],
    "daily_checkins": True,
    "weekly_scripts": True,
    "simulate_transcripts": True,
    "simulate_notes": True,
}
```

#### 7.6.2 Simulator Core Logic

```python
class StudentSimulator:
    """Simulates a full semester of student activity."""
    
    async def run_semester(self) -> SimulationStats:
        while self.current_date <= self.end_date:
            await self.run_day(self.current_date)
            self.current_date += timedelta(days=1)
        await self.validate_results()
        return self.stats
    
    async def run_day(self, date: date):
        weekday = date.weekday()
        
        # Morning
        await self.am_checkin(date)
        
        # Classes
        for course in self.config["courses"]:
            if self._has_class(course, weekday):
                transcript = await self.attend_class(date, course)
                await self.take_notes(date, course, transcript)
        
        # Evening
        await self.pm_checkin(date)
        
        # Friday: weekly script
        if weekday == 4:
            await self.generate_weekly_script(date)
```

#### 7.6.3 Validation Checkpoints

| Checkpoint | Pass Criteria |
|------------|---------------|
| Memory populated | ≥100 memories stored |
| Temporal recall | Query "what did I do Monday" returns results |
| Semantic recall | Query "boundaries in relationships" returns relevant |
| Links created | Transcripts link to notes |
| Check-ins complete | AM + PM for every simulated day |
| Weekly scripts | One per week of semester |

---

### 7.7 PHASE 6: De-Stub & Cleanup (Days 16-18)

**Objective:** Remove all placeholders, integrate orphaned code, delete truly dead code.

#### 7.7.1 Stub Detection Patterns

```python
STUB_PATTERNS = [
    r"#\s*TODO:",
    r"#\s*FIXME:",
    r"raise NotImplementedError",
    r"pass\s*#\s*placeholder",
    r"return None\s*#\s*(placeholder|stub)",
]
```

#### 7.7.2 Orphan Code Categories

| Category | Action |
|----------|--------|
| Agent exists, no gateway route | Create route + n8n workflow |
| Agent exists, no test | Create test |
| Integration exists, not registered | Register in orchestration |
| n8n workflow, broken HTTP calls | Fix or delete |
| Langflow flow, missing components | Fix or delete |

#### 7.7.3 Deletion Criteria

Code can be deleted if ALL are true:

- [ ] No imports from other modules
- [ ] No gateway route references it
- [ ] No n8n workflow calls it
- [ ] No CLI command invokes it
- [ ] No test exercises it
- [ ] Not documented as planned feature
- [ ] Owner confirms not needed

---

### 7.8 PHASE 7: Testing & Documentation (Days 19-21)

**Objective:** Comprehensive tests and updated docs.

#### 7.8.1 Test Coverage Targets

| Module | Current | Target |
|--------|---------|--------|
| `integrations/` | ~40% | 80% |
| `agents/` | ~60% | 80% |
| `gateway/` | ~30% | 80% |
| `cli_bridge/` | ~20% | 70% |
| Overall | ~45% | 75% |

#### 7.8.2 Documentation Updates

| Doc | Update Required |
|-----|-----------------|
| README.md | Reflect actual current state |
| QUICKSTART.md | Working getting-started flow |
| ARCHITECTURE.md | Match new orchestration layer |
| API.md | All gateway routes documented |
| AGENTS.md | All agents, their status, usage |
| WORKFLOWS.md | All n8n workflows, their triggers |

---

### 7.9 PHASE 8: Final Merge & Transition (Day 22+)

**Objective:** Merge to main, transition to operational mode.

#### 7.9.1 Merge Checklist

- [ ] All tests pass
- [ ] Student simulation completes successfully
- [ ] No TODO/FIXME in critical paths
- [ ] Documentation reflects reality
- [ ] .env.example has all required vars
- [ ] docker-compose.yml starts all services
- [ ] n8n workflows importable and functional
- [ ] Langflow flows importable and functional

#### 7.9.2 Post-Merge: Personal Assistant Agent

Create new agent mode for operational use:

```yaml
# .github/agents/personal-assistant.agent.md
name: OsMEN Personal Assistant
description: Autonomous personal assistant for daily operations
authorization: OPERATIONAL (no repo edit rights)
capabilities:
  - Execute registered pipelines via gateway API
  - Query and store memories
  - Generate daily briefings and scripts
  - Manage calendar/email (with OAuth)
  - Process transcripts and notes
restrictions:
  - CANNOT modify files in D:\OsMEN
  - CANNOT create new agents or workflows
  - CANNOT modify n8n workflows directly
  - MUST use gateway API for all actions
```

---

## 8) Recommendation: VS Code Chat vs n8n/Langflow vs Copilot CLI

- **Keep VS Code Chat** for refactor/building the program (code + tests). It’s the best place to do repo-wide surgery.
- **Make n8n** the always-on operational orchestrator (schedules/webhooks/retries/audit trail).
- **Use Langflow** for the reasoning graphs you want versioned and visible.
- **Using Copilot CLI (or your gateway)** as the model-access hub for workflows is a good move if you want model calls to be consistent outside VS Code.

---

## 9) Open Items (Owner Actions / Non-Code)

- Switch GitHub repo visibility to **Private** (owner action in GitHub settings).
- Decide whether the operational assistant agent will be deployed as:
  - a constrained local service that calls stable APIs, or
  - an n8n/Langflow-first agent that treats Python code as tools.

---
