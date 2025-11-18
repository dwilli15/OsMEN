#!/usr/bin/env python3
"""
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
from collections import defaultdict

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class OrchestrationAgent:
    """
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
