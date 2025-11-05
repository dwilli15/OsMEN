# OsMEN · Operating System Multi-Agent Ecosystem (Spec)

## 1. Vision & Scope
- Build a **local-first, no-code/low-code agent hub** that automates daily OS tasks, graduate-school workflows, productivity hygiene, and content creation.
- Leverage **n8n** as the event-driven automation backbone and **Langflow** as the visual agent design studio.
- Support modular agent “teams” that can be extended without writing imperative code.

### Goals
- Deliver a reusable playbook for orchestrating specialized agents through drag-and-drop tooling.
- Keep sensitive data local while allowing optional cloud augmentations.
- Provide human-in-the-loop controls for guardrails and transparency.
- Showcase a modern Langflow + n8n stack as the reference pattern for no-code, multi-agent orchestration.

### Non-goals
- Building custom Python pipelines or bespoke backend services.
- Supporting legacy OSes prior to Windows 10 or non-desktop form factors in v1.
- Providing hosted SaaS; deployment is user-managed.

## 2. Target Users & Use Cases
- **Primary user:** Power user / graduate student seeking automation without coding.
- **Secondary stakeholders:** Productivity mentor, content editor, research collaborator (optional shared workflows).

Key scenarios:
- Post-reboot hardening, app-aware firewall control, and routine health checks.
- Academic planning (deadlines, references, reading summaries).
- Distraction management with righteous context gating.
- Content drafting, editing, and publishing assist.

## 3. System Architecture

```mermaid
flowchart TD
    subgraph A[n8n Automation Fabric]
        T1[System Triggers<br/>Restart, Schedules, Hooks]
        T2[Manual Triggers<br/>Buttons, Webhooks]
        T3[Event Listeners<br/>Process/App Monitors]
    end

    subgraph B[Langflow Agent Studio]
        L1[Coordinator Agent<br/>task decomposition]
        L2[Specialist Agents<br/>OS, Grad, Productivity, Content]
        L3[Memory Blocks<br/>Vector DB, Local Storage]
    end

    subgraph C[Action Layer]
        C1[Firewall Control<br/>Simplewall CLI]
        C2[Process Insight<br/>Sysinternals, PowerShell]
        C3[Doc & Media Ops<br/>Office Automation, FFmpeg, Pandoc]
        C4[External APIs<br/>Calendar, Email, Notion (optional)]
    end

    T1 & T2 & T3 -->|JSON payloads| L1
    L1 -->|delegation| L2
    L2 -->|tool calls| C1 & C2 & C3 & C4
    L2 -->|feedback| L3
    L3 -->|context injections| L1
```

### Component Responsibilities
- **n8n**: Trigger ingestion, routing, retries, human approvals, secrets management, audit trail. Utilize AI Agent nodes for looped reasoning and workflow pausing, and Subworkflow nodes for reusable templates (e.g., notifications, approvals).
- **Langflow**: Visual agent graph construction, LLM selection, prompt templating, memory wiring, tool invocation. Leverage FlowOps for versioned graph management and the Playground for rapid hypothesis testing before exporting JSON definitions back into repo.
- **Local LLM runtime** (Ollama/LM Studio): inference for reasoning, rewriting, summarization. Maintain model registry with performance notes and fallback order.
- **Tool layer**: OS-native commands and integrations invoked via n8n HTTP/CLI nodes or Langflow tool adapters. Encapsulate privileged operations behind n8n credentials to preserve no-code abstraction while enabling extensions (e.g., Simplewall, Sysinternals, FFmpeg, Pandoc connectors).

### Platform Selection Rationale
- **Langflow** provides cutting-edge visual composition of multi-agent reasoning, structured tool-calling graphs, and integrated vector memory without requiring Python authoring. The community releases weekly updates introducing new node types, OpenAI-compatible router blocks, and advanced control flow (conditional branches, guardrails).
- **n8n** extends those agents into tangible OS actions through its automation fabric, enabling local-first deployment, credential vaulting, and built-in change history. Recent releases added an AI Actions collection (LLM Evaluate, Prompt templates) and Workflow Sharing for team collaboration.
- Combined, both platforms satisfy the requirement for a code-free yet future-facing stack: Langflow owns cognition, n8n owns execution, and both export/import JSON definitions that Copilot can manage inside the repo.

## 4. Agent Portfolio

| Agent | Mission | Inputs | Outputs | Acceptance Criteria |
|-------|---------|--------|---------|---------------------|
| **OS Sentry** | Harden system on boot, monitor anomalies. | Restart event, process list, network status. | Firewall rule updates, log reports. | Applies baseline policy <30s after boot; generates human-readable report; fails safe on error. |
| **Grad Navigator** | Manage academic tasks, literature, reminders. | Calendar data, citation backlog, user intents. | Daily priority digest, reading schedule, task queue entries. | Digest delivered by 09:05; references tagged with metadata; actionable next steps surfaced. |
| **Focus Steward** | Enforce productivity heuristics, timeboxing. | Active app, calendar context, focus settings. | Network toggles, nudges, focus timers. | Blocks flagged apps during focus sessions; prompts user before overrides; logs decisions. |
| **Content Forge** | Draft, edit, and format content assets. | Source text/media, style guide, target channel. | Edited drafts, formatted assets, publishing checklist. | Generates draft within 2 minutes; formatting matches template; versioned output stored locally. |
| **Research Scout** | Summarize papers, maintain knowledge base. | PDFs, web articles, citation queries. | Structured notes, vector embeddings, citation exports. | Extracts abstract, key points, questions; updates vector store per document; ensures cite-ready metadata. |

## 5. Prompt & Memory Strategy
- **Coordinator Prompt Template**: Capture trigger metadata, agent roster, decision policy (“choose agent or escalate to human”). Governed in Langflow global prompt node.
- **Specialist Prompt Template**: Each agent graph includes: role definition, expected outputs, toolcall schema, refusal policy, log instructions.
- **Memory**:
  - Short-term: Langflow session memory (per workflow run).
  - Long-term: Vector store (Chroma/Qdrant) for research notes, style guides, firewall justifications.
   - n8n data store for durable state (key-value) and human approval history.
   - Optional secure notebook (Obsidian vault or OneNote section) synchronized by n8n for human-readable audit narratives.

## 6. Workflow Blueprints

### 6.1 Boot Hardening Loop
1. n8n “System Restart” trigger fires from Windows Task Scheduler webhook.
2. n8n collects process list (PowerShell) and baseline rules.
3. Langflow OS Sentry evaluates deviations; suggests firewall diffs.
4. n8n executes Simplewall CLI updates; logs results.
5. Human approval path if risky action detected.

### 6.2 Academic Daily Brief
1. n8n cron 09:00; fetch calendar events & deadlines.
2. Langflow Grad Navigator prioritizes tasks, cross-references bibliography memory.
3. Output digest via email/Notion page; optional text-to-speech playback.
4. n8n archives summary and appends to progress log.

### 6.3 Focus Session Guardrails
1. n8n monitors active window changes (AutoHotkey or PowerShell event log bridge).
2. On focus session start, Langflow Focus Steward validates app whitelist and cross-references current Pomodoro streak stored in vector memory for tailored nudges.
3. n8n toggles Simplewall profiles, arms Pomodoro timer, posts reminders.
4. If override requested, escalate to user with reasoning.

### 6.4 Content Production Pipeline
1. User drops draft into `content/inbox/`.
2. n8n file watcher triggers Langflow Content Forge.
3. Agent chain: Outline generator → editor → formatter (templates stored in memory).
4. Deliverables saved to `content/output/` with metadata JSON.
5. Notification to user; optional auto-publish connector disabled by default.

### 6.5 Research Sweep
1. Manual button in n8n or Slack slash command passes PDF URL.
2. n8n downloads file, extracts text (PDFPlumber), stores in staging.
3. Langflow Research Scout summarizes, extracts citations, stores embeddings.
4. n8n syncs structured notes to Obsidian/Notion.

## 7. Data & Integration Contracts
- **Event payloads (n8n → Langflow)**: JSON with `trigger`, `context`, `artifacts`, `requested_outcome`.
- **Tool response (Langflow → n8n)**: JSON containing `actions`, `explanations`, `confidence`, `requires_human`.
- **Logs**: Centralized in n8n execution history; optional forwarding to local SQLite/ELK.
- **Secrets**: Stored in n8n credential manager; Langflow references via environment variables.
- **Version control**: Exported Langflow `.json` and n8n workflow exports must include semantic version in filename (e.g., `os-sentry-v0.2.json`) to simplify diff reviews.

## 8. Security, Privacy, & Safety
- Local-first runtime; cloud connectors are opt-in and scoped.
- Maintain allowlist/denylist policies for command execution.
- Provide manual override switches in n8n UI.
- Implement logging + redaction rules for sensitive strings (API keys, personal data).
- Adopt role-based prompts to prevent unauthorized actions.
- Run quarterly tabletop exercises simulating credential compromise and n8n workflow rollback using its execution history and backup snapshots.

## 9. Deployment & Hosting
- Packaging: Docker Compose stack (n8n, Langflow, vector DB, Ollama) or native installs.
- OS prerequisites: Windows 10/11 with WSL2 for containers, admin rights for firewall control.
- Backups: Git-managed workflow JSON, Langflow exports, n8n credentials encrypted.
- Update cadence: Monthly maintenance window; test in staging workspace before prod.
- Observability: Enable n8n telemetry dashboards and Langflow run logs stored in `logs/` for post-mortem analysis, with optional Grafana integration via Loki if WSL resources allow.

## 10. MVP Milestones
1. **Environment Bring-up**  
   - Install n8n, Langflow, Ollama, Simplewall, Sysinternals.  
   - Verify inter-service networking and credential vault.
2. **Core Workflows (P0)**  
   - Boot Hardening Loop  
   - Academic Daily Brief (text digest)  
   - Focus Session Guardrails (manual trigger)  
3. **Content Pipeline (P1)**  
   - Draft > edit > format path with local LLM.  
4. **Research Sweep (P1)**  
   - PDF summarization with vector store update.  
5. **User Interface Enhancements (P2)**  
   - n8n dashboard, status board, manual override toggles.

### Definition of Done (MVP)
- All P0 workflows automated end-to-end, fully local.
- Runbooks written and stored in repo.
- Safety interlocks (approvals, logging) validated.
- User can enable/disable each agent without reconfiguration.

## 11. Testing & Validation Strategy
- **Dry runs** using sample payloads in Langflow simulation mode.
- **n8n built-in workflow test** with mocked responses before enabling triggers.
- **Endpoint checks**: firewall rule diff, content file checksum, digest accuracy spot-checks.
- **User acceptance**: weekly review of automation logs and agent decisions.
- **Langflow regression suite**: save canonical input/output pairs per agent and re-run after each model update to confirm expected tone, formatting, and safety behaviors.

## 12. Future Enhancements
- Voice control with local speech-to-text (Whisper.cpp).
- Cross-device sync (mobile companion triggers).
- Analytics dashboard (agent performance, time saved).
- Marketplace of reusable Langflow graphs (export/import).
- Dynamic agent staffing using Langflow conditional orchestration (spin up additional specialist agents when queue backlog exceeds SLA).
- Integrate n8n Workflow Sharing to offer prebuilt templates for collaborators while keeping credentials isolated.

## 13. Copilot / Scaffold Instructions
Use this prompt once repo is created:

```
Create the OsMEN project scaffold with:
- docs/spec.md (seeded with current spec) and docs/runbooks/*.md placeholders.
- /flows/n8n/ for workflow JSON exports; include README describing import steps.
- /flows/langflow/ for agent graphs with .json templates and instructions.
- /config/ containing sample .env template and firewall baseline YAML.
- /scripts/automation/ placeholders for PowerShell wrappers (no code required yet).
- /content/{inbox,output}/ with .gitkeep.
Provide README outlining local deployment via Docker Compose (n8n + Langflow + vector DB + Ollama), safety guidelines, and contribution checklist tailored for no-code editing.
```

## 14. Immediate Next Steps
- Approve architecture and agent lineup.
- Stand up local stack in a clean sandbox and document install steps.
- Export initial empty n8n and Langflow templates into repo.
- Draft runbooks for each workflow to support future collaborators.

---
This spec guides the private repository setup and subsequent Copilot-assisted scaffolding for OsMEN.
