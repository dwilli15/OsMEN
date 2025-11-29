"""
Agent Teams Module

Provides infrastructure for creating and managing teams of agents that work together
on complex tasks. Built on LangGraph StateGraph patterns for robust orchestration.

Key Components:
- AgentTeam: A collection of agents that collaborate on tasks
- TeamManager: Singleton that orchestrates all teams
- TeamState: Shared state for team coordination
- Pre-built team configurations for common workflows

Usage:
    from agents.teams import TeamManager, AgentTeam, TeamRole
    
    # Get team manager
    manager = TeamManager()
    
    # Create a research team
    team = manager.create_team("research", [
        TeamRole(agent_type="research_intel", role="lead"),
        TeamRole(agent_type="librarian", role="researcher"),
        TeamRole(agent_type="content_creator", role="writer")
    ])
    
    # Execute team task
    result = await team.execute_async("Research quantum computing")
"""

from .base import (
    TeamRole,
    TeamState,
    TeamConfig,
    TeamResult,
    TeamStatus,
    AgentCapability,
)

from .team import AgentTeam

from .manager import TeamManager

from .predefined import (
    RESEARCH_TEAM,
    DAILY_OPS_TEAM,
    CONTENT_TEAM,
    SECURITY_TEAM,
    FULL_STACK_TEAM,
)

__all__ = [
    # Base types
    "TeamRole",
    "TeamState", 
    "TeamConfig",
    "TeamResult",
    "TeamStatus",
    "AgentCapability",
    # Core classes
    "AgentTeam",
    "TeamManager",
    # Pre-defined teams
    "RESEARCH_TEAM",
    "DAILY_OPS_TEAM",
    "CONTENT_TEAM",
    "SECURITY_TEAM",
    "FULL_STACK_TEAM",
]
