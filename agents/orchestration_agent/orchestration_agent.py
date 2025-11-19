"""
Orchestration Agent for coordinating team agents during sprints.

This agent coordinates multiple team agents working on parallel tasks,
manages dependencies, resolves blockers, and tracks progress.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger


class OrchestrationAgent:
    """
    Orchestration Agent that coordinates all team agents.
    
    Responsibilities:
    - Coordinate team agents executing parallel tasks
    - Manage critical path dependencies
    - Resolve blockers within 15 minutes
    - Track progress against milestones
    - Coordinate PR creation at appropriate times
    - Facilitate secret requests from user
    """
    
    def __init__(self, message_dir: str = "/tmp/osmen_messages"):
        """
        Initialize the Orchestration Agent.
        
        Args:
            message_dir: Directory for inter-agent message queue
        """
        self.message_dir = Path(message_dir)
        self.message_dir.mkdir(parents=True, exist_ok=True)
        
        # Message queues
        self.inbox = self.message_dir / "orchestration" / "inbox"
        self.outbox = self.message_dir / "orchestration" / "outbox"
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.outbox.mkdir(parents=True, exist_ok=True)
        
        # Team tracking
        self.teams: Dict[str, Dict[str, Any]] = {}
        self.blockers: List[Dict[str, Any]] = []
        self.milestones: List[Dict[str, Any]] = []
        
        # Sprint state
        self.sprint_start_time = datetime.now()
        self.status = "initialized"
        
        logger.info("OrchestrationAgent initialized successfully")
    
    def register_team(self, team_name: str, team_info: Dict[str, Any]) -> None:
        """
        Register a team agent with the orchestration agent.
        
        Args:
            team_name: Name of the team (e.g., "team1_google_oauth")
            team_info: Team metadata (lead, focus area, dependencies, etc.)
        """
        self.teams[team_name] = {
            **team_info,
            "status": "registered",
            "last_update": datetime.now().isoformat(),
            "tasks_completed": [],
            "current_task": None,
            "blockers": []
        }
        logger.info(f"Registered team: {team_name}")
    
    def send_message(self, to_team: str, message: Dict[str, Any]) -> None:
        """
        Send a message to a team agent.
        
        Args:
            to_team: Target team name
            message: Message content with type and payload
        """
        team_inbox = self.message_dir / to_team / "inbox"
        team_inbox.mkdir(parents=True, exist_ok=True)
        
        msg_id = f"{int(time.time() * 1000)}"
        msg_file = team_inbox / f"{msg_id}.json"
        
        full_message = {
            "id": msg_id,
            "from": "orchestration",
            "to": to_team,
            "timestamp": datetime.now().isoformat(),
            **message
        }
        
        with open(msg_file, 'w') as f:
            json.dump(full_message, f, indent=2)
        
        logger.info(f"Sent message to {to_team}: {message.get('type', 'unknown')}")
    
    def receive_messages(self) -> List[Dict[str, Any]]:
        """
        Receive all pending messages from team agents.
        
        Returns:
            List of messages from team agents
        """
        messages = []
        
        if not self.inbox.exists():
            return messages
        
        for msg_file in sorted(self.inbox.glob("*.json")):
            try:
                with open(msg_file, 'r') as f:
                    msg = json.load(f)
                messages.append(msg)
                msg_file.unlink()  # Remove after reading
            except Exception as e:
                logger.error(f"Error reading message {msg_file}: {e}")
        
        return messages
    
    def process_messages(self) -> None:
        """Process all incoming messages from team agents."""
        messages = self.receive_messages()
        
        for msg in messages:
            msg_type = msg.get('type')
            from_team = msg.get('from')
            
            if msg_type == 'status_update':
                self._handle_status_update(from_team, msg)
            elif msg_type == 'blocker_report':
                self._handle_blocker(from_team, msg)
            elif msg_type == 'secret_request':
                self._handle_secret_request(from_team, msg)
            elif msg_type == 'pr_request':
                self._handle_pr_request(from_team, msg)
            elif msg_type == 'milestone_completed':
                self._handle_milestone(from_team, msg)
            else:
                logger.warning(f"Unknown message type from {from_team}: {msg_type}")
    
    def _handle_status_update(self, team: str, msg: Dict[str, Any]) -> None:
        """Handle status update from a team."""
        if team in self.teams:
            payload = msg.get('payload', {})
            self.teams[team].update({
                'last_update': msg.get('timestamp'),
                'current_task': payload.get('current_task'),
                'status': payload.get('status', 'working')
            })
            
            if 'completed_tasks' in payload:
                self.teams[team]['tasks_completed'].extend(payload['completed_tasks'])
            
            logger.info(f"Status update from {team}: {payload.get('status')}")
    
    def _handle_blocker(self, team: str, msg: Dict[str, Any]) -> None:
        """Handle blocker report from a team."""
        payload = msg.get('payload', {})
        blocker = {
            'team': team,
            'timestamp': msg.get('timestamp'),
            'description': payload.get('description'),
            'impact': payload.get('impact'),
            'severity': payload.get('severity', 'P2'),
            'status': 'open'
        }
        self.blockers.append(blocker)
        
        if team in self.teams:
            self.teams[team]['blockers'].append(blocker)
        
        logger.warning(f"BLOCKER from {team}: {payload.get('description')}")
        
        # Auto-respond with acknowledgment
        self.send_message(team, {
            'type': 'blocker_acknowledged',
            'payload': {
                'blocker_id': len(self.blockers) - 1,
                'message': 'Blocker acknowledged. Working on resolution.'
            }
        })
    
    def _handle_secret_request(self, team: str, msg: Dict[str, Any]) -> None:
        """
        Handle secret request from a team.
        
        This would typically prompt the user for credentials, but for now
        we'll log the request and send a placeholder response.
        """
        payload = msg.get('payload', {})
        secret_name = payload.get('secret_name')
        purpose = payload.get('purpose')
        
        logger.info(f"SECRET REQUEST from {team}: {secret_name} - {purpose}")
        
        # In a real system, this would prompt the user @dwilli15
        # For now, we acknowledge the request
        self.send_message(team, {
            'type': 'secret_request_pending',
            'payload': {
                'secret_name': secret_name,
                'message': f'Secret request logged. User will be notified to provide {secret_name}.',
                'status': 'pending_user_input'
            }
        })
    
    def _handle_pr_request(self, team: str, msg: Dict[str, Any]) -> None:
        """Handle PR creation request from a team."""
        payload = msg.get('payload', {})
        pr_title = payload.get('title')
        pr_description = payload.get('description')
        
        logger.info(f"PR REQUEST from {team}: {pr_title}")
        
        # Acknowledge PR request
        self.send_message(team, {
            'type': 'pr_request_acknowledged',
            'payload': {
                'message': 'PR request acknowledged. Will coordinate with other teams.',
                'status': 'pending_coordination'
            }
        })
    
    def _handle_milestone(self, team: str, msg: Dict[str, Any]) -> None:
        """Handle milestone completion from a team."""
        payload = msg.get('payload', {})
        milestone = {
            'team': team,
            'timestamp': msg.get('timestamp'),
            'name': payload.get('milestone_name'),
            'description': payload.get('description')
        }
        self.milestones.append(milestone)
        
        logger.info(f"MILESTONE from {team}: {payload.get('milestone_name')}")
    
    def get_sprint_status(self) -> Dict[str, Any]:
        """
        Get overall sprint status.
        
        Returns:
            Dictionary with sprint metrics and team statuses
        """
        elapsed_time = (datetime.now() - self.sprint_start_time).total_seconds() / 3600
        
        return {
            'timestamp': datetime.now().isoformat(),
            'status': self.status,
            'elapsed_hours': round(elapsed_time, 2),
            'teams': self.teams,
            'open_blockers': [b for b in self.blockers if b['status'] == 'open'],
            'milestones': self.milestones,
            'total_tasks_completed': sum(len(t.get('tasks_completed', [])) for t in self.teams.values())
        }
    
    def run_coordination_loop(self, iterations: int = 10, interval: int = 30) -> None:
        """
        Run the orchestration coordination loop.
        
        Args:
            iterations: Number of coordination cycles to run
            interval: Seconds between coordination cycles
        """
        logger.info(f"Starting orchestration loop: {iterations} iterations, {interval}s interval")
        self.status = "running"
        
        for i in range(iterations):
            logger.info(f"Coordination cycle {i+1}/{iterations}")
            
            # Process incoming messages
            self.process_messages()
            
            # Check team health
            for team_name, team_data in self.teams.items():
                if team_data.get('status') == 'registered':
                    # Send start signal to newly registered teams
                    self.send_message(team_name, {
                        'type': 'start_work',
                        'payload': {
                            'message': 'Begin executing your tasks',
                            'check_in_interval': interval
                        }
                    })
                    team_data['status'] = 'started'
            
            # Log status
            status = self.get_sprint_status()
            logger.info(f"Sprint status: {status['total_tasks_completed']} tasks completed, "
                       f"{len(status['open_blockers'])} open blockers")
            
            # Sleep until next cycle
            if i < iterations - 1:
                time.sleep(interval)
        
        self.status = "completed"
        logger.info("Orchestration loop completed")
