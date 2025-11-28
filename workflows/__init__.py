# Workflows Package
"""
OsMEN Workflow Library

This package contains production-ready workflow implementations:
- daily_brief: Daily briefing with calendar, email, and task summarization
- research: Deep research workflow using multi-agent orchestration
- content: Content generation workflow for blogs, social media, newsletters
- approval: Human-in-the-loop approval gating for sensitive operations

Each workflow demonstrates:
- OAuth integration (Google, Microsoft)
- LLM provider abstraction (OpenAI, Anthropic, Ollama)
- Multi-agent orchestration
- Retrieval-augmented generation
"""

from workflows.daily_brief import (
    DailyBriefWorkflow,
    DailyBriefConfig,
    WorkflowResult,
    WorkflowStatus,
    run_daily_brief
)

from workflows.research import (
    ResearchWorkflow,
    ResearchResult,
    ResearchDepth,
    SourceType,
    Citation
)

from workflows.content import (
    ContentWorkflow,
    ContentResult,
    ContentType,
    ContentTone,
    ContentLength
)

from workflows.approval import (
    ApprovalGate,
    ApprovalRule,
    ApprovalRequest,
    ApprovalStatus,
    RiskLevel,
    ApprovalMixin,
    get_approval_gate
)

__all__ = [
    # Daily Brief
    'DailyBriefWorkflow',
    'DailyBriefConfig',
    'WorkflowResult',
    'WorkflowStatus',
    'run_daily_brief',
    
    # Research
    'ResearchWorkflow',
    'ResearchResult',
    'ResearchDepth',
    'SourceType',
    'Citation',
    
    # Content
    'ContentWorkflow',
    'ContentResult',
    'ContentType',
    'ContentTone',
    'ContentLength',
    
    # Approval
    'ApprovalGate',
    'ApprovalRule',
    'ApprovalRequest',
    'ApprovalStatus',
    'RiskLevel',
    'ApprovalMixin',
    'get_approval_gate'
]
