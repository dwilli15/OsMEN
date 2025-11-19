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
Orchestration Agent - Day 1 Coordination

Coordinates all team agents and manages dependencies, blockers, and progress.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


@dataclass
class TeamStatus:
    """Status of a team."""
    team_id: str
    team_name: str
    current_hour: int
    completion_percentage: int
    tasks_completed: int
    tasks_total: int
    blockers: List[str]
    last_update: str
from collections import defaultdict

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class OrchestrationAgent:
    """
    Orchestration Agent for Day 1 Sprint Coordination
    
    Responsibilities:
    - Coordinate all 5 teams executing Day 1 work
    - Manage critical path dependencies
    - Conduct hourly check-ins and stand-ups
    - Resolve blockers within 15 minutes
    - Ensure code integration across teams
    - Track progress against Day 1 milestones
    - Deliver all Day 1 objectives on time
    """
    
    def __init__(self, work_dir: Optional[Path] = None):
        """Initialize the orchestration agent."""
        self.agent_name = "Orchestration Agent"
        
        # Set working directory
        if work_dir is None:
            self.work_dir = Path(__file__).parent.parent.parent.parent
        else:
            self.work_dir = Path(work_dir)
        
        # Message queue directory
        self.message_dir = Path(__file__).parent / "messages"
        self.message_dir.mkdir(parents=True, exist_ok=True)
        
        # Team tracking
        self.teams: Dict[str, TeamStatus] = {
            'team1_google_oauth': TeamStatus('team1_google_oauth', 'Team 1: Google OAuth', 0, 0, 0, 10, [], ''),
            'team2_microsoft_oauth': TeamStatus('team2_microsoft_oauth', 'Team 2: Microsoft OAuth', 0, 0, 0, 10, [], ''),
            'team3_api_clients': TeamStatus('team3_api_clients', 'Team 3: API Clients', 0, 0, 0, 10, [], ''),
            'team4_testing': TeamStatus('team4_testing', 'Team 4: Testing Infrastructure', 0, 0, 0, 10, [], ''),
            'team5_token_security': TeamStatus('team5_token_security', 'Team 5: Token Security', 0, 0, 0, 10, [], ''),
        }
        
        # Communication log
        self.message_log: List[Dict] = []
        
        # Secret requests
        self.secret_requests: List[Dict] = []
        
        # PR requests
        self.pr_requests: List[Dict] = []
        
        # Start time
        self.start_time = datetime.now()
        self.current_hour = 0
    
    def read_messages(self) -> List[Dict]:
        """Read all pending messages from teams."""
        messages = []
        
        if not self.message_dir.exists():
            return messages
        
        for msg_file in self.message_dir.glob("*.json"):
            try:
                with open(msg_file, 'r') as f:
                    msg = json.load(f)
                    messages.append(msg)
                    self.message_log.append(msg)
                
                # Archive the message
                archive_dir = self.message_dir / "archive"
                archive_dir.mkdir(exist_ok=True)
                msg_file.rename(archive_dir / msg_file.name)
            except Exception as e:
                print(f"Error reading message {msg_file}: {e}")
        
        return messages
    
    def process_messages(self):
        """Process all pending messages from teams."""
        messages = self.read_messages()
        
        for msg in messages:
            msg_type = msg.get('message_type', '')
            team = msg.get('team', '')
            content = msg.get('content', {})
            
            print(f"\n[Orchestration] Received {msg_type} from {team}")
            
            if msg_type == 'status_update':
                self.handle_status_update(team, content)
            elif msg_type == 'blocker':
                self.handle_blocker(team, content)
            elif msg_type == 'request_secret':
                self.handle_secret_request(team, content)
            elif msg_type == 'request_pr':
                self.handle_pr_request(team, content)
            else:
                print(f"Unknown message type: {msg_type}")
    
    def handle_status_update(self, team: str, content: Dict):
        """Handle status update from a team."""
        if team in self.teams:
            team_status = self.teams[team]
            summary = content.get('summary', {})
            
            team_status.completion_percentage = summary.get('completion_percentage', 0)
            team_status.tasks_completed = summary.get('completed', 0)
            team_status.tasks_total = summary.get('total_tasks', 10)
            team_status.current_hour = content.get('current_hour', 0)
            team_status.last_update = content.get('timestamp', datetime.now().isoformat())
            
            # Update blockers
            blocked_tasks = content.get('blocked_tasks', [])
            team_status.blockers = [t.get('description', '') for t in blocked_tasks]
            
            print(f"  Status: {team_status.completion_percentage}% complete ({team_status.tasks_completed}/{team_status.tasks_total} tasks)")
    
    def handle_blocker(self, team: str, content: Dict):
        """Handle blocker report from a team."""
        print(f"\n🚨 BLOCKER from {team}:")
        print(f"  Task: {content.get('task_id', 'unknown')}")
        print(f"  Description: {content.get('description', 'No description')}")
        print(f"  Severity: {content.get('severity', 'P1')}")
        print(f"  Impact: {content.get('impact', 'Unknown impact')}")
        
        # Add to team's blocker list
        if team in self.teams:
            blocker_desc = content.get('description', 'Unknown blocker')
            if blocker_desc not in self.teams[team].blockers:
                self.teams[team].blockers.append(blocker_desc)
        
        # Log for user attention
        print(f"\n  ACTION REQUIRED: Orchestration needs to resolve this blocker!")
    
    def handle_secret_request(self, team: str, content: Dict):
        """Handle secret request from a team."""
        print(f"\n🔐 SECRET REQUEST from {team}:")
        print(f"  Secret: {content.get('secret_name', 'unknown')}")
        print(f"  Reason: {content.get('reason', 'No reason provided')}")
        print(f"  Urgency: {content.get('urgency', 'medium')}")
        
        # Add to secret requests for user to fulfill
        self.secret_requests.append({
            'team': team,
            'timestamp': datetime.now().isoformat(),
            'secret_name': content.get('secret_name', ''),
            'reason': content.get('reason', ''),
            'urgency': content.get('urgency', 'medium'),
            'status': 'pending'
        })
        
        print(f"\n  ACTION REQUIRED: User @dwilli15 needs to provide this secret!")
    
    def handle_pr_request(self, team: str, content: Dict):
        """Handle PR request from a team."""
        print(f"\n📋 PULL REQUEST REQUEST from {team}:")
        print(f"  Title: {content.get('title', 'No title')}")
        print(f"  Branch: {content.get('branch', 'unknown')}")
        
        # Add to PR requests
        self.pr_requests.append({
            'team': team,
            'timestamp': datetime.now().isoformat(),
            'title': content.get('title', ''),
            'description': content.get('description', ''),
            'branch': content.get('branch', ''),
            'status': 'pending'
        })
        
        print(f"\n  ACTION REQUIRED: Create PR for {team}!")
    
    def generate_dashboard(self) -> str:
        """Generate a status dashboard for all teams."""
        dashboard = f"\n{'='*80}\n"
        dashboard += f"Day 1 Sprint Dashboard - Hour {self.current_hour}\n"
        dashboard += f"Elapsed Time: {datetime.now() - self.start_time}\n"
        dashboard += f"{'='*80}\n\n"
        
        # Team status table
        dashboard += "Team Status:\n"
        dashboard += f"{'-'*80}\n"
        dashboard += f"{'Team':<30} {'Progress':<15} {'Tasks':<15} {'Blockers':<20}\n"
        dashboard += f"{'-'*80}\n"
        
        for team_id, team in self.teams.items():
            progress_bar = '█' * (team.completion_percentage // 10) + '░' * (10 - team.completion_percentage // 10)
            tasks_str = f"{team.tasks_completed}/{team.tasks_total}"
            blockers_str = str(len(team.blockers))
            
            dashboard += f"{team.team_name:<30} {progress_bar} {team.completion_percentage}%  {tasks_str:<15} {blockers_str:<20}\n"
        
        dashboard += f"{'-'*80}\n\n"
        
        # Overall progress
        total_completion = sum(t.completion_percentage for t in self.teams.values()) / len(self.teams)
        dashboard += f"Overall Sprint Progress: {total_completion:.1f}%\n"
        
        # Pending actions
        if self.secret_requests:
            pending_secrets = [r for r in self.secret_requests if r['status'] == 'pending']
            if pending_secrets:
                dashboard += f"\nPending Secret Requests: {len(pending_secrets)}\n"
                for req in pending_secrets:
                    dashboard += f"  - {req['team']}: {req['secret_name']} ({req['urgency']})\n"
        
        if self.pr_requests:
            pending_prs = [r for r in self.pr_requests if r['status'] == 'pending']
            if pending_prs:
                dashboard += f"\nPending PR Requests: {len(pending_prs)}\n"
                for req in pending_prs:
                    dashboard += f"  - {req['team']}: {req['title']}\n"
        
        # Active blockers
        active_blockers = [(t.team_name, b) for t in self.teams.values() for b in t.blockers]
        if active_blockers:
            dashboard += f"\n🚨 Active Blockers: {len(active_blockers)}\n"
            for team_name, blocker in active_blockers:
                dashboard += f"  - {team_name}: {blocker}\n"
        
        dashboard += f"\n{'='*80}\n"
        
        return dashboard
    
    def run_coordination_cycle(self):
        """Run one coordination cycle."""
        # Process all pending messages
        self.process_messages()
        
        # Display dashboard
        print(self.generate_dashboard())
    
    def coordinate_teams(self, max_hours: int = 8):
        """Coordinate all teams for the duration of the sprint."""
        print(f"\n{'='*80}")
        print(f"Orchestration Agent - Starting Day 1 Sprint Coordination")
        print(f"{'='*80}\n")
        
        for hour in range(1, max_hours + 1):
            self.current_hour = hour
            print(f"\n{'#'*80}")
            print(f"# Hour {hour} - Sprint Coordination")
            print(f"{'#'*80}\n")
            
            # Run coordination cycle
            self.run_coordination_cycle()
            
            # Hourly checkpoint messages
            if hour == 2:
                print("\n⏰ Hour 2 Checkpoint: Foundation Phase Complete?")
            elif hour == 4:
                print("\n⏰ Hour 4 Checkpoint: Implementation Phase - Midpoint Check")
            elif hour == 6:
                print("\n⏰ Hour 6 Checkpoint: Integration Phase")
            elif hour == 8:
                print("\n⏰ Hour 8 Checkpoint: Final Validation")
            
            # Simulate time passing (in real scenario, would wait)
            time.sleep(1)
        
        # Final summary
        print(f"\n{'='*80}")
        print(f"Day 1 Sprint Coordination Complete")
        print(f"{'='*80}\n")
        print(self.generate_dashboard())


def main():
    """Main entry point for orchestration agent."""
    print("\n" + "="*80)
    print("Orchestration Agent - Day 1 Sprint Coordinator")
    print("="*80 + "\n")
    
    # Initialize agent
    agent = OrchestrationAgent()
    
    # Run initial coordination cycle
    agent.run_coordination_cycle()
    
    print("\n✅ Orchestration agent initialized successfully")
    print("Monitoring messages from all teams...")
    
    return agent


if __name__ == '__main__':
    agent = main()
    Orchestration agent that coordinates all team agents.
    
    Responsibilities:
    - Receive status updates from team agents
    - Manage dependencies and blockers
    - Coordinate secret requests to user
    - Facilitate team communication
    - Track overall progress
    """
    
    def __init__(self):
        """Initialize orchestration agent"""
        self.agent_name = "Orchestration Agent"
        self.base_path = Path(__file__).parent.parent.parent
        self.messages_file = Path(__file__).parent / "messages.jsonl"
        self.status_file = Path(__file__).parent / "orchestration_status.json"
        
        # Team tracking
        self.teams = {
            "team1": "Google OAuth",
            "team2": "Microsoft OAuth",
            "team3": "API Clients",
            "team4": "Testing",
            "team5": "Token Security"
        }
        
        self.team_status: Dict[str, Dict[str, Any]] = {}
        self.blockers: List[Dict[str, Any]] = []
        self.secret_requests: List[Dict[str, Any]] = []
        self.messages: List[Dict[str, Any]] = []
        
        # Load existing state
        self._load_state()
    
    def _load_state(self):
        """Load orchestration state from file"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    data = json.load(f)
                    self.team_status = data.get('team_status', {})
                    self.blockers = data.get('blockers', [])
                    self.secret_requests = data.get('secret_requests', [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load state: {e}")
        
        # Load messages from JSONL
        if self.messages_file.exists():
            try:
                with open(self.messages_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            self.messages.append(json.loads(line))
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load messages: {e}")
    
    def _save_state(self):
        """Save orchestration state to file"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'team_status': self.team_status,
            'blockers': self.blockers,
            'secret_requests': self.secret_requests
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def receive_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receive and process a message from a team agent.
        
        Args:
            message: Message from team agent
            
        Returns:
            Response to team agent
        """
        message_type = message.get('message_type')
        team_id = message.get('team_id')
        
        print(f"\n📨 Received {message_type} from {self.teams.get(team_id, team_id)}")
        
        # Route message based on type
        if message_type == 'status_update':
            return self._handle_status_update(message)
        elif message_type == 'task_update':
            return self._handle_task_update(message)
        elif message_type == 'blocker':
            return self._handle_blocker(message)
        elif message_type == 'request_secret':
            return self._handle_secret_request(message)
        else:
            return {'status': 'unknown_message_type'}
    
    def _handle_status_update(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status update from team"""
        team_id = message.get('team_id')
        data = message.get('data', {})
        
        self.team_status[team_id] = {
            'timestamp': message.get('timestamp'),
            'summary': data.get('summary', {}),
            'current_hour': data.get('current_hour'),
            'tasks': data.get('tasks', {})
        }
        
        self._save_state()
        
        return {
            'status': 'acknowledged',
            'team_id': team_id,
            'message': f"Status update received for {self.teams.get(team_id)}"
        }
    
    def _handle_task_update(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task status update"""
        team_id = message.get('team_id')
        data = message.get('data', {})
        
        print(f"   Task: {data.get('task_name')}")
        print(f"   Status: {data.get('old_status')} → {data.get('new_status')}")
        
        return {
            'status': 'acknowledged',
            'team_id': team_id
        }
    
    def _handle_blocker(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle blocker report"""
        team_id = message.get('team_id')
        data = message.get('data', {})
        
        blocker = {
            'team_id': team_id,
            'team_name': self.teams.get(team_id),
            'timestamp': message.get('timestamp'),
            'severity': data.get('severity'),
            'task': data.get('task_name'),
            'description': data.get('description')
        }
        
        self.blockers.append(blocker)
        self._save_state()
        
        print(f"   ⚠️  BLOCKER: {data.get('description')}")
        print(f"   Severity: {data.get('severity')}")
        
        return {
            'status': 'blocker_logged',
            'team_id': team_id,
            'action': 'Blocker logged and will be addressed'
        }
    
    def _handle_secret_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request for secret/credential"""
        team_id = message.get('team_id')
        data = message.get('data', {})
        
        secret_name = data.get('secret_name')
        description = data.get('description')
        
        request = {
            'team_id': team_id,
            'team_name': self.teams.get(team_id),
            'timestamp': message.get('timestamp'),
            'secret_name': secret_name,
            'description': description,
            'urgency': data.get('urgency'),
            'status': 'pending'
        }
        
        self.secret_requests.append(request)
        self._save_state()
        
        print(f"\n   🔐 SECRET REQUEST: {secret_name}")
        print(f"   Team: {self.teams.get(team_id)}")
        print(f"   Description: {description}")
        print(f"   Urgency: {data.get('urgency')}")
        print(f"\n   📝 Action Required:")
        print(f"   User @dwilli15 should provide: {secret_name}")
        print(f"   Set as environment variable or provide to orchestration agent")
        
        return {
            'status': 'request_logged',
            'team_id': team_id,
            'message': f"Secret request logged. User will be notified to provide {secret_name}",
            'secret_available': False  # In real implementation, check if available
        }
    
    def print_dashboard(self):
        """Print orchestration dashboard"""
        print("\n" + "="*80)
        print("ORCHESTRATION DASHBOARD - Day 1 Coordination")
        print("="*80)
        
        # Overall progress
        if self.team_status:
            total_completion = 0
            active_teams = 0
            
            print("\n📊 Team Progress:")
            for team_id, status in self.team_status.items():
                team_name = self.teams.get(team_id, team_id)
                summary = status.get('summary', {})
                completion = summary.get('completion_percentage', 0)
                
                print(f"\n  {team_name}:")
                print(f"    Hour: {status.get('current_hour', 0)}")
                print(f"    Progress: {completion:.1f}%")
                print(f"    Completed: {summary.get('completed', 0)}")
                print(f"    In Progress: {summary.get('in_progress', 0)}")
                print(f"    Blocked: {summary.get('blocked', 0)}")
                
                total_completion += completion
                active_teams += 1
            
            if active_teams > 0:
                avg_completion = total_completion / active_teams
                print(f"\n  Overall Progress: {avg_completion:.1f}%")
        
        # Active blockers
        if self.blockers:
            print(f"\n🚫 Active Blockers ({len(self.blockers)}):")
            for blocker in self.blockers[-5:]:  # Show last 5
                print(f"  - [{blocker['team_name']}] {blocker['description']}")
                print(f"    Severity: {blocker['severity']}")
        
        # Secret requests
        if self.secret_requests:
            pending = [r for r in self.secret_requests if r.get('status') == 'pending']
            if pending:
                print(f"\n🔐 Pending Secret Requests ({len(pending)}):")
                for request in pending:
                    print(f"  - {request['secret_name']}")
                    print(f"    Team: {request['team_name']}")
                    print(f"    Urgency: {request['urgency']}")
        
        # Recent messages
        if self.messages:
            print(f"\n📨 Recent Messages ({len(self.messages)} total):")
            for msg in self.messages[-3:]:  # Show last 3
                team_name = self.teams.get(msg.get('team_id'), 'Unknown')
                msg_type = msg.get('message_type')
                print(f"  - [{team_name}] {msg_type}")
        
        print("\n" + "="*80)
    
    def process_messages(self):
        """Process new messages from message log"""
        # In a real implementation, this would poll for new messages
        # For now, just show the dashboard
        self.print_dashboard()


def main():
    """Main entry point for orchestration agent"""
    print("="*80)
    print("Orchestration Agent - Day 1 Coordination")
    print("="*80)
    
    agent = OrchestrationAgent()
    
    # Process any pending messages
    agent.process_messages()
    
    print("\n\n💡 Orchestration Agent Running")
    print("\nCapabilities:")
    print("  ✅ Receive status updates from team agents")
    print("  ✅ Log and track blockers")
    print("  ✅ Coordinate secret requests to user")
    print("  ✅ Monitor overall progress")
    print("\nTeam agents can send messages via:")
    print("  - team_agent.report_to_orchestration()")
    print("\nMessages logged to:")
    print(f"  - {agent.messages_file}")


if __name__ == "__main__":
    main()
