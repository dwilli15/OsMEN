#!/usr/bin/env python3
"""
Orchestration Agent

This agent coordinates all 5 teams during Day 1 sprint execution.
It manages dependencies, resolves blockers, and ensures successful delivery.
Coordinates all 5 teams during Day 1 sprint execution
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TeamStatus(Enum):
    """Team status enumeration"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OrchestrationAgent:
    """Agent for coordinating all teams during Day 1 sprint"""
    
    def __init__(self):
        """Initialize the orchestration agent"""
        try:
            self.start_time = datetime.now()
            self.teams = {
                'team1': {'name': 'Google OAuth', 'status': TeamStatus.NOT_STARTED, 'progress': 0},
                'team2': {'name': 'Microsoft OAuth', 'status': TeamStatus.NOT_STARTED, 'progress': 0},
                'team3': {'name': 'API Clients', 'status': TeamStatus.NOT_STARTED, 'progress': 0},
                'team4': {'name': 'Testing', 'status': TeamStatus.NOT_STARTED, 'progress': 0},
                'team5': {'name': 'Token Security', 'status': TeamStatus.NOT_STARTED, 'progress': 0}
            }
            self.messages = []
            self.blockers = []
            self.pr_requests = []
            self.secret_requests = []
            
            # State file for persistence
            self.state_file = Path(__file__).parent / 'orchestration_state.json'
            self._load_state()
            
            logger.info("OrchestrationAgent initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OrchestrationAgent: {e}")
            raise
    
    def _load_state(self):
        """Load orchestration state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.messages = state.get('messages', [])
                    self.blockers = state.get('blockers', [])
                    self.pr_requests = state.get('pr_requests', [])
                    self.secret_requests = state.get('secret_requests', [])
                    logger.info("Loaded orchestration state from file")
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
    
    def _save_state(self):
        """Save orchestration state to file"""
        try:
            state = {
                'messages': self.messages,
                'blockers': self.blockers,
                'pr_requests': self.pr_requests,
                'secret_requests': self.secret_requests,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug("Saved orchestration state to file")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def receive_message(self, team_id: str, message: str, priority: TaskPriority = TaskPriority.MEDIUM) -> Dict:
        """
        Receive a message from a team agent
        
        Args:
            team_id: Team identifier (team1, team2, etc.)
            message: Message content
            priority: Message priority level
            
        Returns:
            Response dictionary with acknowledgment and instructions
        """
        try:
            if team_id not in self.teams:
                raise ValueError(f"Invalid team_id: {team_id}")
            
            msg_record = {
                'team_id': team_id,
                'team_name': self.teams[team_id]['name'],
                'message': message,
                'priority': priority.value,
                'timestamp': datetime.now().isoformat(),
                'acknowledged': True
            }
            
            self.messages.append(msg_record)
            self._save_state()
            
            logger.info(f"Message from {team_id} ({priority.value}): {message}")
            
            # Return acknowledgment with potential instructions
            return {
                'acknowledged': True,
                'team_id': team_id,
                'timestamp': datetime.now().isoformat(),
                'instructions': self._generate_instructions(team_id, message),
                'dependencies': self._check_dependencies(team_id)
            }
        except Exception as e:
            logger.error(f"Error receiving message from {team_id}: {e}")
            return {
                'acknowledged': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_instructions(self, team_id: str, message: str) -> str:
        """Generate context-aware instructions for a team"""
        # Simple instruction generation based on message content
        if 'blocked' in message.lower():
            return "Please provide blocker details for resolution"
        elif 'complete' in message.lower():
            return "Great work! Please run tests and prepare for integration"
        elif 'started' in message.lower():
            return "Acknowledged. Continue with your TODO tasks. Report progress every 2 hours."
        else:
            return "Continue work. Report any blockers immediately."
    
    def _check_dependencies(self, team_id: str) -> Dict:
        """Check if team dependencies are met"""
        dependencies = {
            'team1': [],
            'team2': ['team1'],  # Needs base class from team1
            'team3': ['team1'],  # Needs OAuth interface from team1
            'team4': ['team3'],  # Needs API clients from team3
            'team5': ['team1']   # Needs token structure from team1
        }
        
        team_deps = dependencies.get(team_id, [])
        met_dependencies = []
        unmet_dependencies = []
        
        for dep_team in team_deps:
            if self.teams[dep_team]['status'] in [TeamStatus.COMPLETED, TeamStatus.IN_PROGRESS]:
                met_dependencies.append(dep_team)
            else:
                unmet_dependencies.append(dep_team)
        
        return {
            'required_dependencies': team_deps,
            'met': met_dependencies,
            'unmet': unmet_dependencies,
            'can_proceed': len(unmet_dependencies) == 0
        }
    
    def update_team_status(self, team_id: str, status: TeamStatus, progress: int = None) -> Dict:
        """
        Update team status
        
        Args:
            team_id: Team identifier
            status: New status
            progress: Progress percentage (0-100)
            
        Returns:
            Updated team information
        """
        try:
            if team_id not in self.teams:
                raise ValueError(f"Invalid team_id: {team_id}")
            
            self.teams[team_id]['status'] = status
            if progress is not None:
                self.teams[team_id]['progress'] = min(100, max(0, progress))
            
            self.teams[team_id]['last_update'] = datetime.now().isoformat()
            
            logger.info(f"Team {team_id} status updated: {status.value}, progress: {progress}%")
            
            return {
                'team_id': team_id,
                'status': status.value,
                'progress': self.teams[team_id]['progress'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error updating team status: {e}")
            return {'error': str(e)}
    
    def report_blocker(self, team_id: str, blocker_description: str, severity: str = "medium") -> Dict:
        """
        Report a blocker from a team
        
        Args:
            team_id: Team identifier
            blocker_description: Description of the blocker
            severity: Severity level (critical, high, medium, low)
            
        Returns:
            Blocker tracking information
        """
        try:
            blocker = {
                'id': f"BLOCK-{len(self.blockers) + 1}",
                'team_id': team_id,
                'team_name': self.teams[team_id]['name'],
                'description': blocker_description,
                'severity': severity,
                'status': 'open',
                'reported_at': datetime.now().isoformat(),
                'resolution': None
            }
            
            self.blockers.append(blocker)
            self._save_state()
            
            logger.warning(f"BLOCKER reported by {team_id} ({severity}): {blocker_description}")
            
            # Auto-escalate critical blockers
            if severity == 'critical':
                logger.critical(f"CRITICAL BLOCKER: {blocker_description}")
            
            return {
                'blocker_id': blocker['id'],
                'acknowledged': True,
                'severity': severity,
                'expected_resolution_time': self._estimate_resolution_time(severity),
                'suggested_action': self._suggest_blocker_resolution(team_id, blocker_description)
            }
        except Exception as e:
            logger.error(f"Error reporting blocker: {e}")
            return {'error': str(e)}
    
    def _estimate_resolution_time(self, severity: str) -> str:
        """Estimate blocker resolution time based on severity"""
        times = {
            'critical': '15 minutes',
            'high': '1 hour',
            'medium': '2 hours',
            'low': '4 hours'
        }
        return times.get(severity, '2 hours')
    
    def _suggest_blocker_resolution(self, team_id: str, description: str) -> str:
        """Suggest resolution approach for blocker"""
        desc_lower = description.lower()
        
        if 'oauth' in desc_lower or 'token' in desc_lower:
            return "Check with Team 1 (Google OAuth) and Team 5 (Token Security) for assistance"
        elif 'api' in desc_lower or 'client' in desc_lower:
            return "Review API documentation and check Team 3 (API Clients) for patterns"
        elif 'test' in desc_lower:
            return "Coordinate with Team 4 (Testing) for test infrastructure support"
        elif 'dependency' in desc_lower or 'install' in desc_lower:
            return "Check requirements.txt and run: pip install -r requirements.txt"
        else:
            return "Review TODO.md and check with other teams in #day1-orchestration"
    
    def request_secret(self, team_id: str, secret_name: str, reason: str) -> Dict:
        """
        Request a secret from the user
        
        Args:
            team_id: Team requesting the secret
            secret_name: Name of the secret (e.g., 'GOOGLE_CLIENT_ID')
            reason: Reason for requesting the secret
            
        Returns:
            Secret request tracking information
        """
        try:
            request = {
                'id': f"SECRET-{len(self.secret_requests) + 1}",
                'team_id': team_id,
                'secret_name': secret_name,
                'reason': reason,
                'status': 'pending',
                'requested_at': datetime.now().isoformat(),
                'fulfilled_at': None
            }
            
            self.secret_requests.append(request)
            self._save_state()
            
            logger.info(f"SECRET REQUEST from {team_id}: {secret_name} - {reason}")
            
            # Generate user-friendly request message
            user_message = f"""
🔐 Secret Request #{request['id']}

Team: {self.teams[team_id]['name']} ({team_id})
Secret: {secret_name}
Reason: {reason}

@dwilli15 Please provide the value for {secret_name} to enable {team_id} to continue.

To fulfill this request, you can:
1. Add {secret_name} to the .env file
2. Or provide it as an environment variable
"""
            
            return {
                'request_id': request['id'],
                'status': 'pending',
                'user_message': user_message,
                'secret_name': secret_name,
                'instructions': f"Waiting for {secret_name} to be provided by @dwilli15"
            }
        except Exception as e:
            logger.error(f"Error requesting secret: {e}")
            return {'error': str(e)}
    
    def request_pull_request(self, team_id: str, branch_name: str, description: str) -> Dict:
        """
        Request creation of a pull request
        
        Args:
            team_id: Team requesting the PR
            branch_name: Git branch name
            description: PR description
            
        Returns:
            PR request tracking information
        """
        try:
            pr_request = {
                'id': f"PR-{len(self.pr_requests) + 1}",
                'team_id': team_id,
                'branch_name': branch_name,
                'description': description,
                'status': 'pending',
                'requested_at': datetime.now().isoformat(),
                'created_at': None,
                'pr_url': None
            }
            
            self.pr_requests.append(pr_request)
            self._save_state()
            
            logger.info(f"PR REQUEST from {team_id}: {branch_name}")
            
            return {
                'request_id': pr_request['id'],
                'status': 'pending',
                'branch_name': branch_name,
                'instructions': f"PR will be created for branch: {branch_name}",
                'next_steps': [
                    'Ensure all changes are committed',
                    'Ensure all tests pass',
                    'Provide PR title and detailed description',
                    'Wait for PR creation by orchestration'
                ]
            }
        except Exception as e:
            logger.error(f"Error requesting PR: {e}")
            return {'error': str(e)}
    
    def get_overall_status(self) -> Dict:
        """
        Get overall orchestration status
        
        Returns:
            Complete status of all teams and coordination
        """
        try:
            elapsed_time = (datetime.now() - self.start_time).total_seconds() / 3600  # hours
            
            team_statuses = {}
            for team_id, team_info in self.teams.items():
                team_statuses[team_id] = {
                    'name': team_info['name'],
                    'status': team_info['status'].value,
                    'progress': team_info.get('progress', 0)
                }
            
            open_blockers = [b for b in self.blockers if b['status'] == 'open']
            pending_secrets = [s for s in self.secret_requests if s['status'] == 'pending']
            pending_prs = [p for p in self.pr_requests if p['status'] == 'pending']
            
            return {
                'timestamp': datetime.now().isoformat(),
                'elapsed_hours': round(elapsed_time, 2),
                'teams': team_statuses,
                'overall_progress': self._calculate_overall_progress(),
                'messages_count': len(self.messages),
                'open_blockers': len(open_blockers),
                'pending_secrets': len(pending_secrets),
                'pending_prs': len(pending_prs),
                'blockers': open_blockers,
                'secret_requests': pending_secrets,
                'pr_requests': pending_prs
            }
        except Exception as e:
            logger.error(f"Error getting overall status: {e}")
            return {'error': str(e)}
    
    def _calculate_overall_progress(self) -> int:
        """Calculate overall progress across all teams"""
        total_progress = sum(team['progress'] for team in self.teams.values())
        return total_progress // len(self.teams)
    
    def generate_status_report(self) -> str:
        """
        Generate a human-readable status report
        
        Returns:
            Formatted status report string
        """
        try:
            status = self.get_overall_status()
            
            report = []
            report.append("=" * 60)
            report.append("ORCHESTRATION STATUS REPORT")
            report.append("=" * 60)
            report.append(f"Timestamp: {status['timestamp']}")
            report.append(f"Elapsed Time: {status['elapsed_hours']} hours")
            report.append(f"Overall Progress: {status['overall_progress']}%")
            report.append("")
            
            report.append("TEAM STATUS:")
            report.append("-" * 60)
            for team_id, team_info in status['teams'].items():
                status_emoji = {
                    'not_started': '⚪',
                    'in_progress': '🔵',
                    'blocked': '🔴',
                    'completed': '✅'
                }.get(team_info['status'], '❓')
                
                report.append(f"{status_emoji} {team_info['name']}: {team_info['status']} ({team_info['progress']}%)")
            
            report.append("")
            
            if status['open_blockers'] > 0:
                report.append(f"⚠️  BLOCKERS: {status['open_blockers']} open")
                for blocker in status['blockers']:
                    report.append(f"  - [{blocker['severity']}] {blocker['description']}")
                report.append("")
            
            if status['pending_secrets'] > 0:
                report.append(f"🔐 SECRET REQUESTS: {status['pending_secrets']} pending")
                for secret in status['secret_requests']:
                    report.append(f"  - {secret['secret_name']} (for {secret['team_id']})")
                report.append("")
            
            if status['pending_prs'] > 0:
                report.append(f"📋 PR REQUESTS: {status['pending_prs']} pending")
                for pr in status['pr_requests']:
                    report.append(f"  - {pr['branch_name']} (from {pr['team_id']})")
                report.append("")
            
            report.append(f"📨 Total Messages: {status['messages_count']}")
            report.append("=" * 60)
            
            return "\n".join(report)
        except Exception as e:
            logger.error(f"Error generating status report: {e}")
            return f"Error generating report: {e}"


def main():
    """Main function for testing"""
    print("Orchestration Agent - Test Mode")
    print("=" * 60)
    
    agent = OrchestrationAgent()
    
    # Test team status update
    agent.update_team_status('team3', TeamStatus.IN_PROGRESS, 10)
    
    # Test message reception
    response = agent.receive_message('team3', 'Starting API client generation tasks')
    print(f"\nMessage response: {json.dumps(response, indent=2)}")
    
    # Test status report
    print("\n" + agent.generate_status_report())


if __name__ == '__main__':
    main()
