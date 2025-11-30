"""
Pre-defined team configurations for common workflows.

Each template provides:
- TeamConfig: Configuration for the team
- List[TeamRole]: Roles/agents in the team

Available Templates:
- RESEARCH_TEAM: For research and investigation tasks
- DAILY_OPS_TEAM: For daily briefings and operational status
- CONTENT_TEAM: For content creation and media processing
- SECURITY_TEAM: For security audits and monitoring
- FULL_STACK_TEAM: Full-capability team for complex tasks
"""

from .base import TeamRole, TeamConfig, AgentCapability


# =============================================================================
# Research Team
# =============================================================================

RESEARCH_TEAM_CONFIG = TeamConfig(
    name="research",
    description="Research and investigation team for gathering and synthesizing information",
    max_iterations=15,
    timeout_seconds=600.0,
    parallel_execution=False,
    error_handling="continue",
)

RESEARCH_TEAM_ROLES = [
    TeamRole(
        agent_type="research_intel",
        role="lead",
        capabilities=[AgentCapability.RESEARCH, AgentCapability.ANALYSIS],
        priority=10,
        required=True,
    ),
    TeamRole(
        agent_type="librarian",
        role="researcher",
        capabilities=[AgentCapability.RETRIEVAL, AgentCapability.SYNTHESIS],
        priority=8,
        required=True,
    ),
    TeamRole(
        agent_type="knowledge_management",
        role="analyst",
        capabilities=[AgentCapability.PERSISTENCE, AgentCapability.ANALYSIS],
        priority=5,
        required=False,
    ),
]

RESEARCH_TEAM = {
    "config": RESEARCH_TEAM_CONFIG,
    "roles": RESEARCH_TEAM_ROLES,
}


# =============================================================================
# Daily Operations Team
# =============================================================================

DAILY_OPS_TEAM_CONFIG = TeamConfig(
    name="daily_ops",
    description="Daily briefing and operational status team",
    max_iterations=10,
    timeout_seconds=300.0,
    parallel_execution=True,  # Can gather info in parallel
    error_handling="continue",
)

DAILY_OPS_TEAM_ROLES = [
    TeamRole(
        agent_type="daily_brief",
        role="lead",
        capabilities=[AgentCapability.MONITORING, AgentCapability.SYNTHESIS],
        priority=10,
        required=True,
    ),
    TeamRole(
        agent_type="personal_assistant",
        role="analyst",
        capabilities=[AgentCapability.PERSISTENCE, AgentCapability.COMMUNICATION],
        priority=7,
        required=True,
    ),
    TeamRole(
        agent_type="security_ops",
        role="monitor",
        capabilities=[AgentCapability.MONITORING, AgentCapability.ANALYSIS],
        priority=5,
        required=False,
    ),
]

DAILY_OPS_TEAM = {
    "config": DAILY_OPS_TEAM_CONFIG,
    "roles": DAILY_OPS_TEAM_ROLES,
}


# =============================================================================
# Content Creation Team
# =============================================================================

CONTENT_TEAM_CONFIG = TeamConfig(
    name="content",
    description="Content creation and media processing team",
    max_iterations=12,
    timeout_seconds=900.0,  # Media processing can take time
    parallel_execution=False,
    error_handling="continue",
)

CONTENT_TEAM_ROLES = [
    TeamRole(
        agent_type="content_creator",
        role="lead",
        capabilities=[AgentCapability.GENERATION, AgentCapability.MEDIA_PROCESSING],
        priority=10,
        required=True,
    ),
    TeamRole(
        agent_type="research_intel",
        role="researcher",
        capabilities=[AgentCapability.RESEARCH, AgentCapability.ANALYSIS],
        priority=8,
        required=False,
    ),
    TeamRole(
        agent_type="librarian",
        role="reviewer",
        capabilities=[AgentCapability.RETRIEVAL, AgentCapability.ANALYSIS],
        priority=5,
        required=False,
    ),
]

CONTENT_TEAM = {
    "config": CONTENT_TEAM_CONFIG,
    "roles": CONTENT_TEAM_ROLES,
}


# =============================================================================
# Security Team
# =============================================================================

SECURITY_TEAM_CONFIG = TeamConfig(
    name="security",
    description="Security auditing and monitoring team",
    max_iterations=10,
    timeout_seconds=300.0,
    parallel_execution=True,
    error_handling="stop",  # Security issues should halt
)

SECURITY_TEAM_ROLES = [
    TeamRole(
        agent_type="security_ops",
        role="lead",
        capabilities=[AgentCapability.MONITORING, AgentCapability.ANALYSIS],
        priority=10,
        required=True,
    ),
    TeamRole(
        agent_type="boot_hardening",
        role="analyst",
        capabilities=[AgentCapability.ANALYSIS, AgentCapability.MONITORING],
        priority=8,
        required=True,
    ),
    TeamRole(
        agent_type="daily_brief",
        role="monitor",
        capabilities=[AgentCapability.MONITORING, AgentCapability.SYNTHESIS],
        priority=5,
        required=False,
    ),
]

SECURITY_TEAM = {
    "config": SECURITY_TEAM_CONFIG,
    "roles": SECURITY_TEAM_ROLES,
}


# =============================================================================
# Full Stack Team (All Capabilities)
# =============================================================================

FULL_STACK_TEAM_CONFIG = TeamConfig(
    name="full_stack",
    description="Full-capability team for complex multi-domain tasks",
    max_iterations=20,
    timeout_seconds=1200.0,
    parallel_execution=False,
    error_handling="continue",
)

FULL_STACK_TEAM_ROLES = [
    TeamRole(
        agent_type="research_intel",
        role="lead",
        capabilities=[AgentCapability.RESEARCH, AgentCapability.ANALYSIS],
        priority=10,
        required=True,
    ),
    TeamRole(
        agent_type="librarian",
        role="researcher",
        capabilities=[AgentCapability.RETRIEVAL, AgentCapability.SYNTHESIS],
        priority=9,
        required=True,
    ),
    TeamRole(
        agent_type="daily_brief",
        role="monitor",
        capabilities=[AgentCapability.MONITORING, AgentCapability.SYNTHESIS],
        priority=8,
        required=False,
    ),
    TeamRole(
        agent_type="content_creator",
        role="writer",
        capabilities=[AgentCapability.GENERATION, AgentCapability.MEDIA_PROCESSING],
        priority=7,
        required=False,
    ),
    TeamRole(
        agent_type="personal_assistant",
        role="executor",
        capabilities=[AgentCapability.PERSISTENCE, AgentCapability.COMMUNICATION],
        priority=6,
        required=False,
    ),
    TeamRole(
        agent_type="security_ops",
        role="reviewer",
        capabilities=[AgentCapability.MONITORING, AgentCapability.ANALYSIS],
        priority=5,
        required=False,
    ),
]

FULL_STACK_TEAM = {
    "config": FULL_STACK_TEAM_CONFIG,
    "roles": FULL_STACK_TEAM_ROLES,
}


# =============================================================================
# Template Registry
# =============================================================================

TEAM_TEMPLATES = {
    "research": RESEARCH_TEAM,
    "daily_ops": DAILY_OPS_TEAM,
    "content": CONTENT_TEAM,
    "security": SECURITY_TEAM,
    "full_stack": FULL_STACK_TEAM,
}
