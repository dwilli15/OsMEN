"""
TeamManager - Singleton that orchestrates all agent teams.

Provides:
- Team creation and lifecycle management
- Pre-defined team templates
- Team discovery and listing
- Cross-team coordination
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading

from .base import TeamRole, TeamConfig, TeamResult, TeamStatus
from .team import AgentTeam

logger = logging.getLogger("osmen.teams.manager")


class TeamManager:
    """
    Singleton manager for all agent teams.
    
    Provides:
    - Team creation from templates or custom configs
    - Team lifecycle management (create, start, stop, destroy)
    - Team discovery and listing
    - Cross-team task routing
    
    Example:
        manager = TeamManager()
        
        # Create from predefined template
        team = manager.create_team("research")
        
        # Or create custom team
        team = manager.create_team("custom", [
            TeamRole("research_intel", "lead"),
            TeamRole("librarian", "researcher"),
        ])
        
        # Execute task
        result = team.execute("Research quantum computing")
        
        # List all teams
        teams = manager.list_teams()
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize team manager."""
        if self._initialized:
            return
        
        self._teams: Dict[str, AgentTeam] = {}
        self._llm_provider = None
        self._initialized = True
        
        logger.info("TeamManager initialized")
    
    def set_llm_provider(self, provider: Any) -> None:
        """
        Set LLM provider for all teams.
        
        Args:
            provider: LLM provider instance
        """
        self._llm_provider = provider
        # Update existing teams
        for team in self._teams.values():
            team.llm_provider = provider
    
    def create_team(
        self,
        name: str,
        roles: Optional[List[TeamRole]] = None,
        config: Optional[TeamConfig] = None,
    ) -> AgentTeam:
        """
        Create a new agent team.
        
        Args:
            name: Team name (or predefined template name)
            roles: Optional list of roles (if not using template)
            config: Optional team configuration
            
        Returns:
            Created AgentTeam instance
        """
        # Check for predefined templates
        from .predefined import TEAM_TEMPLATES
        
        if name in TEAM_TEMPLATES and roles is None:
            template = TEAM_TEMPLATES[name]
            roles = template["roles"]
            if config is None:
                config = template["config"]
        
        if roles is None:
            raise ValueError(f"No roles provided and '{name}' is not a predefined template")
        
        if config is None:
            config = TeamConfig(name=name)
        
        # Create team
        team = AgentTeam(
            config=config,
            roles=roles,
            llm_provider=self._llm_provider,
        )
        
        # Register team
        self._teams[name] = team
        
        logger.info(f"Created team '{name}' with {len(roles)} roles")
        return team
    
    def get_team(self, name: str) -> Optional[AgentTeam]:
        """
        Get an existing team by name.
        
        Args:
            name: Team name
            
        Returns:
            AgentTeam instance or None
        """
        return self._teams.get(name)
    
    def list_teams(self) -> List[Dict[str, Any]]:
        """
        List all registered teams.
        
        Returns:
            List of team info dictionaries
        """
        return [
            {
                "name": name,
                "roles": [r.agent_type for r in team.roles],
                "status": team.get_status(),
            }
            for name, team in self._teams.items()
        ]
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List available team templates.
        
        Returns:
            List of template info dictionaries
        """
        from .predefined import TEAM_TEMPLATES
        
        return [
            {
                "name": name,
                "description": template["config"].description,
                "roles": [r.agent_type for r in template["roles"]],
            }
            for name, template in TEAM_TEMPLATES.items()
        ]
    
    def destroy_team(self, name: str) -> bool:
        """
        Destroy a team.
        
        Args:
            name: Team name
            
        Returns:
            True if team was destroyed
        """
        if name in self._teams:
            del self._teams[name]
            logger.info(f"Destroyed team '{name}'")
            return True
        return False
    
    async def route_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TeamResult:
        """
        Route a task to the most appropriate team.
        
        Uses heuristics to determine which team should handle the task.
        
        Args:
            task: Task description
            context: Optional context
            
        Returns:
            TeamResult from the selected team
        """
        # Simple keyword-based routing
        task_lower = task.lower()
        
        team_name = None
        
        if any(kw in task_lower for kw in ["research", "investigate", "find", "search"]):
            team_name = "research"
        elif any(kw in task_lower for kw in ["brief", "daily", "status", "summary"]):
            team_name = "daily_ops"
        elif any(kw in task_lower for kw in ["content", "write", "create", "generate"]):
            team_name = "content"
        elif any(kw in task_lower for kw in ["security", "audit", "vulnerability", "threat"]):
            team_name = "security"
        else:
            team_name = "full_stack"  # Default to full team
        
        # Ensure team exists
        if team_name not in self._teams:
            self.create_team(team_name)
        
        team = self._teams[team_name]
        logger.info(f"Routing task to team '{team_name}': {task[:50]}...")
        
        return await team.execute_async(task, context)
    
    def execute_task(
        self,
        team_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TeamResult:
        """
        Execute a task on a specific team.
        
        Args:
            team_name: Name of team to use
            task: Task description
            context: Optional context
            
        Returns:
            TeamResult from execution
        """
        if team_name not in self._teams:
            self.create_team(team_name)
        
        team = self._teams[team_name]
        return team.execute(task, context)
    
    def get_capabilities(self) -> Dict[str, List[str]]:
        """
        Get capabilities of all teams.
        
        Returns:
            Dictionary mapping team names to their capabilities
        """
        from .base import AgentCapability
        
        capabilities = {}
        for name, team in self._teams.items():
            team_caps = set()
            for role in team.roles:
                team_caps.update(c.value for c in role.capabilities)
            capabilities[name] = list(team_caps)
        
        return capabilities
    
    def __repr__(self) -> str:
        return f"TeamManager(teams={len(self._teams)})"
