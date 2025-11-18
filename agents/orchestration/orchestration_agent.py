#!/usr/bin/env python3
"""
Orchestration Agent - Coordinates Team Agents

This agent coordinates all team agents (Team 1-5) to execute the Day 1 sprint tasks.
It manages dependencies, handles secret requests, creates pull requests, and ensures
all teams are working in coordination.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrchestrationAgent:
    """
    Orchestration agent that coordinates all team agents.
    
    Responsibilities:
    - Coordinate team agent execution
    - Manage dependencies between teams
    - Handle secret requests from teams
    - Create pull requests when teams complete tasks
    - Track overall progress
    - Resolve blockers
    """
    
    def __init__(self):
        """Initialize Orchestration Agent."""
        self.name = "Orchestration Agent"
        self.teams = {}
        self.status_log = []
        self.secret_requests = []
        self.pr_requests = []
        self.start_time = datetime.now()
        
        logger.info(f"{self.name} initialized")
    
    def register_team_agent(self, team_id: str, agent: Any):
        """Register a team agent with orchestration.
        
        Args:
            team_id: Team identifier (e.g., 'team5')
            agent: Team agent instance
        """
        self.teams[team_id] = {
            "agent": agent,
            "status": "registered",
            "last_update": datetime.now().isoformat()
        }
        logger.info(f"Registered {team_id} with orchestration")
    
    def receive_status_update(self, team_id: str, message: str, 
                            level: str = "info", timestamp: str = None):
        """Receive status update from a team agent.
        
        Args:
            team_id: Team identifier
            message: Status message
            level: Log level
            timestamp: Update timestamp
        """
        update = {
            "team_id": team_id,
            "message": message,
            "level": level,
            "timestamp": timestamp or datetime.now().isoformat()
        }
        
        self.status_log.append(update)
        
        # Update team status
        if team_id in self.teams:
            self.teams[team_id]["last_update"] = update["timestamp"]
            self.teams[team_id]["last_message"] = message
        
        # Log the update
        log_msg = f"[{team_id}] {message}"
        if level == "info":
            logger.info(log_msg)
        elif level == "warning":
            logger.warning(log_msg)
        elif level == "error":
            logger.error(log_msg)
    
    def request_user_secret(self, team_id: str, secret_name: str, 
                          description: str) -> Optional[str]:
        """Request a secret from the user.
        
        This method coordinates when and how to request secrets from @dwilli15.
        
        Args:
            team_id: Team requesting the secret
            secret_name: Name of the secret
            description: Description of what the secret is for
            
        Returns:
            The secret value if available
        """
        request = {
            "team_id": team_id,
            "secret_name": secret_name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        self.secret_requests.append(request)
        
        logger.info(f"Secret request from {team_id}: {secret_name}")
        logger.info(f"  Description: {description}")
        logger.info(f"  User @dwilli15 needs to provide: {secret_name}")
        
        # For now, check environment variable
        # In a real scenario, this would prompt the user or check a secure store
        secret_value = os.getenv(secret_name)
        
        if secret_value:
            request["status"] = "fulfilled"
            logger.info(f"Secret {secret_name} found in environment")
        else:
            request["status"] = "awaiting_user_input"
            logger.warning(f"Secret {secret_name} not found - user input required")
            logger.warning(f"Please set environment variable: {secret_name}")
        
        return secret_value
    
    def request_pull_request(self, team_id: str, title: str, description: str):
        """Request creation of a pull request.
        
        Args:
            team_id: Team requesting the PR
            title: PR title
            description: PR description
        """
        pr_request = {
            "team_id": team_id,
            "title": title,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "status": "requested"
        }
        
        self.pr_requests.append(pr_request)
        
        logger.info(f"PR request from {team_id}")
        logger.info(f"  Title: {title}")
        logger.info(f"  Description preview: {description[:200]}...")
    
    def get_overall_status(self) -> Dict[str, Any]:
        """Get overall orchestration status.
        
        Returns:
            Overall status dictionary
        """
        return {
            "orchestration_agent": self.name,
            "start_time": self.start_time.isoformat(),
            "current_time": datetime.now().isoformat(),
            "teams_registered": list(self.teams.keys()),
            "total_status_updates": len(self.status_log),
            "secret_requests": len(self.secret_requests),
            "pr_requests": len(self.pr_requests),
            "team_statuses": {
                team_id: {
                    "status": info["status"],
                    "last_update": info["last_update"],
                    "last_message": info.get("last_message", "")
                }
                for team_id, info in self.teams.items()
            }
        }
    
    def save_status_report(self, filepath: str = None):
        """Save orchestration status report to file.
        
        Args:
            filepath: Path to save report (default: logs/orchestration_status.json)
        """
        if filepath is None:
            logs_dir = Path(__file__).parent.parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)
            filepath = logs_dir / "orchestration_status.json"
        
        status = self.get_overall_status()
        status["status_log"] = self.status_log
        status["secret_requests"] = self.secret_requests
        status["pr_requests"] = self.pr_requests
        
        with open(filepath, 'w') as f:
            json.dump(status, f, indent=2)
        
        logger.info(f"Status report saved to {filepath}")
    
    def execute_team(self, team_id: str) -> Dict[str, Any]:
        """Execute a specific team's tasks.
        
        Args:
            team_id: Team to execute
            
        Returns:
            Execution results
        """
        if team_id not in self.teams:
            logger.error(f"Team {team_id} not registered")
            return {"status": "error", "message": "Team not registered"}
        
        team_info = self.teams[team_id]
        agent = team_info["agent"]
        
        logger.info(f"Executing {team_id}")
        team_info["status"] = "executing"
        
        try:
            # Execute team's tasks
            if hasattr(agent, 'execute_all_tasks'):
                results = agent.execute_all_tasks()
                team_info["status"] = results.get("status", "completed")
                return results
            else:
                logger.warning(f"Team {team_id} agent doesn't have execute_all_tasks method")
                return {"status": "error", "message": "Agent missing execute method"}
        
        except Exception as e:
            logger.error(f"Error executing {team_id}: {e}")
            team_info["status"] = "failed"
            return {"status": "failed", "error": str(e)}
    
    def coordinate_all_teams(self) -> Dict[str, Any]:
        """Coordinate execution of all registered teams.
        
        Returns:
            Overall coordination results
        """
        logger.info("Starting coordination of all teams")
        
        results = {
            "start_time": datetime.now().isoformat(),
            "teams": {},
            "overall_status": "in_progress"
        }
        
        # Execute teams in dependency order
        # For now, we'll execute teams that are ready
        for team_id in self.teams.keys():
            logger.info(f"Coordinating {team_id}")
            team_results = self.execute_team(team_id)
            results["teams"][team_id] = team_results
        
        results["end_time"] = datetime.now().isoformat()
        
        # Determine overall status
        all_completed = all(
            r.get("status") == "completed" 
            for r in results["teams"].values()
        )
        
        if all_completed:
            results["overall_status"] = "completed"
        else:
            any_failed = any(
                r.get("status") == "failed"
                for r in results["teams"].values()
            )
            results["overall_status"] = "failed" if any_failed else "partial"
        
        # Save final status report
        self.save_status_report()
        
        return results


def main():
    """Main entry point for orchestration agent."""
    logger.info("Starting Orchestration Agent")
    
    # Create orchestration agent
    orchestration = OrchestrationAgent()
    
    # Import and register Team 5 agent
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        from team5_security.team5_agent import Team5SecurityAgent
        
        # Create Team 5 agent with orchestration
        team5 = Team5SecurityAgent(orchestration_agent=orchestration)
        orchestration.register_team_agent("team5", team5)
        
        logger.info("Team 5 registered successfully")
        
        # Execute all teams
        results = orchestration.coordinate_all_teams()
        
        # Print results
        print("\n" + "="*80)
        print("ORCHESTRATION AGENT - COORDINATION RESULTS")
        print("="*80)
        print(f"Overall Status: {results['overall_status']}")
        print(f"\nTeam Results:")
        for team_id, team_result in results["teams"].items():
            print(f"  {team_id}: {team_result.get('status', 'unknown')}")
        print("="*80)
        
        # Check for secret requests
        if orchestration.secret_requests:
            print("\nSecret Requests:")
            for req in orchestration.secret_requests:
                if req["status"] == "awaiting_user_input":
                    print(f"  ⚠️  {req['secret_name']}: {req['description']}")
                    print(f"      Requested by: {req['team_id']}")
        
        # Check for PR requests
        if orchestration.pr_requests:
            print("\nPull Request Requests:")
            for pr_req in orchestration.pr_requests:
                print(f"  📝 {pr_req['title']} (from {pr_req['team_id']})")
        
        return 0 if results['overall_status'] == 'completed' else 1
        
    except ImportError as e:
        logger.error(f"Failed to import team agents: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
