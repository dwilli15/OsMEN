# Workflows Package
"""
OsMEN Workflow Library

This package contains production-ready workflow implementations:
- daily_brief: Daily briefing with calendar, email, and task summarization
- research: Deep research workflow using multi-agent orchestration
- content: Content generation workflow

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

__all__ = [
    'DailyBriefWorkflow',
    'DailyBriefConfig',
    'WorkflowResult',
    'WorkflowStatus',
    'run_daily_brief'
]
