#!/usr/bin/env python3
"""
Orchestration Agent

This agent coordinates all 5 teams during Day 1 sprint execution.
It manages dependencies, resolves blockers, and ensures successful delivery.
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
