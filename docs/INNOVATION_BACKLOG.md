# Innovation Backlog

**Purpose:** Track discoveries, evaluations, and implementations of innovations to improve OsMEN

**Last Updated:** 2025-11-09  
**Next Review:** 2025-11-16

## Current Week Discoveries

### Week of 2025-11-09

*No new discoveries yet - innovation agent not yet active*

**Status:** Innovation monitoring framework being implemented this week

---

## Under Evaluation

- **LangGraph Workflow Export Bridge**
  - **Focus:** Enable exporting OsMEN agent teams into LangGraph graphs for advanced orchestration
  - **Questions:** Map capabilities? Maintain memory hand-off? Support hybrid Langflow/LangGraph deployments?

---

## Approved for Implementation

### Memory System Auto-Update
**Category:** Infrastructure  
**Priority:** P0  
**Target:** v1.2.0

**Description:**  
Automatically update memory.json and context files when PRs are merged to main branch.

**Implementation Plan:**
1. Create post-merge GitHub Action
2. Extract commit messages and changes
3. Update memory.json fields
4. Regenerate CONTEXT.md
5. Commit updates back to repo

**Expected Benefits:**
- Always-current system state
- No manual memory management
- Better context for future agents

**Status:** Approved, implementing

---

### Conversation History Storage
**Category:** Infrastructure  
**Priority:** P0  
**Target:** v1.2.0

**Description:**  
Store all agent-user conversations with 45-day retention, permanent summaries.

**Implementation Plan:**
1. Create conversation storage schema
2. Build storage backend (SQLite or JSON files)
3. Implement retention policy
4. Create summary generator
5. Build search/retrieval interface

**Expected Benefits:**
- Context continuity across sessions
- Learning from past interactions
- Audit trail for decisions

**Status:** Approved, implementing

---

### Weekly Innovation Scan
**Category:** Automation  
**Priority:** P1  
**Target:** v1.3.0

**Description:**  
Automated weekly scan of AI/agent frameworks, tools, and patterns.

**Implementation Plan:**
1. Create scan script
2. Monitor RSS feeds, GitHub releases
3. Evaluate against criteria
4. Generate weekly digest
5. Queue for user review

**Expected Benefits:**
- Stay current with ecosystem
- Discover relevant improvements
- Proactive enhancement

**Status:** Approved, planned for next version

---

### LLM Requirement Parser
**Category:** Core Platform
**Priority:** P0
**Target:** v1.2.0

**Description:**
Use production LLMs to translate natural language intents into structured agent requirements (domain, automation level, cadence, KPIs).

**Implementation Plan:**
1. Define prompt + schema contracts
2. Add resilient API client with fallback heuristics
3. Wire intake agent state machine to LLM outputs
4. Capture telemetry for parsing confidence
5. Document operator overrides and testing matrix

**Status:** In progress (beta shipping in Agent Hub)

---

### Agent Hub Structured Review UI
**Category:** No-Code Experience
**Priority:** P1
**Target:** v1.3.0

**Description:**
Form-based controls inside the Agent Hub allowing non-technical users to adjust proposed agent teams without typing natural-language commands.

**Implementation Plan:**
1. Build reusable Jinja partials for selectors and review form
2. Add FastAPI endpoints for template + structured modification APIs
3. Render form inside Agent Hub with stateful JS helpers
4. Sync structured edits back to intake agent context and files
5. Gather usability feedback and refine accessibility styling

**Status:** Beta released (feedback loop open)

---

## Implemented

### Tenacity Retry Logic
**Implemented:** v1.1.0 (2025-11-09)  
**Category:** Reliability

**Summary:**  
Automatic retry with exponential backoff for LLM API calls using Tenacity library.

**Impact:**
- Reliability: 95% → 99.9%
- Zero breaking changes
- Minimal code changes (~25 lines)

**Lessons Learned:**
- Decorator pattern keeps code clean
- Selective retry (not 4xx) important
- Exponential backoff prevents thundering herd

---

## Rejected

*No rejected innovations yet*

---

## Innovation Pipeline

### Proposed Ideas (Not Yet Evaluated)

#### MS Agent Framework Migration
**Source:** User mention  
**Status:** Research needed

**Summary:**  
Microsoft's Agent Framework (formerly AutoGen) + Agent Lightning enhancements

**Next Steps:**
1. Review MS Agent Framework docs
2. Compare to current architecture
3. Assess migration effort
4. Determine if benefits justify complexity

**Questions:**
- Is it compatible with no-code requirement?
- What's the learning curve?
- Does it replace or augment current system?

---

#### LangGraph for Multi-Agent Orchestration
**Source:** Innovation guidelines watch list  
**Status:** Monitoring

**Summary:**  
LangGraph provides graph-based agent orchestration

**Next Steps:**
- Monitor for no-code interfaces
- Evaluate vs. current n8n/Langflow setup
- Check integration complexity

---

#### Semantic Kernel Integration
**Source:** Innovation guidelines watch list  
**Status:** Monitoring

**Summary:**  
Microsoft's AI orchestration SDK

**Next Steps:**
- Assess Python SDK maturity
- Check no-code compatibility
- Evaluate vs. current architecture

---

## Technology Watch List

### Active Monitoring (Weekly Check)

| Technology | Last Checked | Version | Status | Notes |
|------------|--------------|---------|--------|-------|
| MS Agent Framework | N/A | - | 🔍 New | Formerly AutoGen |
| Agent Lightning | N/A | - | 🔍 New | MS enhancement |
| LangGraph | N/A | - | 📊 Monitoring | - |
| CrewAI | N/A | - | 📊 Monitoring | - |
| Semantic Kernel | N/A | - | 📊 Monitoring | - |
| LlamaIndex | N/A | - | 📊 Monitoring | - |
| OpenAI Assistants API | N/A | - | 📊 Monitoring | - |

**Legend:**
- 🔍 New: Recently added to watch list
- 📊 Monitoring: Regular weekly checks
- ✅ Evaluated: Assessment complete
- 🚀 Implementing: In active development
- ✔️ Implemented: Live in production
- ❌ Rejected: Not suitable

---

## Evaluation Criteria

All innovations evaluated on:

1. **Relevance (1-10):** How well does it fit grad school use case?
2. **Complexity (1-10):** How hard to integrate? (lower is better)
3. **Impact (1-10):** Expected improvement to user experience?
4. **Risk (low/medium/high):** Security, privacy, stability concerns?
5. **No-Code Compatible (yes/no):** Can non-technical user manage it?

**Approval Threshold:**
- Relevance ≥ 7
- Complexity ≤ 6
- Impact ≥ 6
- Risk ≤ medium
- No-Code Compatible = yes

---

## User Feedback Integration

### From Planning Discussion (2025-11-09)

**User Preferences Captured:**
- No coding experience - need full no-code
- Agents handle file edits
- Web dashboard primary interface
- Email daily summaries
- Obsidian, Google, Outlook integration
- Semester-based syllabus updates
- Health data integration (Android, Google)
- Weekly review of pre-approved tasks
- 45-day conversation + permanent summaries

**Incorporated Into:**
- [ADR-002] No-Code First Architecture
- [ADR-003] Semester-Based Update Cycle
- [ADR-004] 45-Day Conversation Retention
- [ADR-005] Pre-Approved Task List
- Memory system design
- Roadmap priorities

---

## Metrics

### Innovation Agent Performance
*Not yet active - starting with v1.3.0*

**Target Metrics:**
- Suggestions per month: 3-5 high-quality
- Approval rate: >40%
- Implementation rate: Track % approved → implemented
- User satisfaction: Qualitative feedback
- Time saved: Quantify automation improvements

---

## Weekly Review Template

```markdown
## Week of YYYY-MM-DD

### New Discoveries
1. [Technology/Pattern] - [Source] - [Relevance Score]
2. ...

### Evaluations Completed
1. [Technology] - [Decision: Approve/Reject/Hold] - [Rationale]
2. ...

### Implementations Started
1. [Technology] - [Target Version] - [Progress %]
2. ...

### Implementations Completed
1. [Technology] - [Version Deployed] - [Impact Summary]
2. ...

### Watch List Updates
- [Technology]: [Status change or version update]
- ...

### User Feedback
- [Feedback summary and action items]

### Next Week Focus
- [Priority 1]
- [Priority 2]
- [Priority 3]
```

---

## Notes

- Innovation agent officially starts with v1.3.0
- First automated scan: Week of 2025-11-16
- User reviews weekly digest every Sunday 6 PM
- Pre-approved task list maintained in `.copilot/pre_approved_tasks.json`
- All suggestions require user approval before implementation

---

*This backlog updates weekly as innovation agent discovers and evaluates new opportunities.*
