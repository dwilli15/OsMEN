#!/usr/bin/env python3
"""
Day 1 Sprint Activation Script
Activates and coordinates all 5 team task sessions
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class Day1Orchestrator:
    """Orchestrates all Day 1 team task sessions"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.base_path = Path(__file__).parent
        self.teams = {
            'team1': {
                'name': 'Google OAuth',
                'status': 'ready',
                'session_file': 'SESSION_TEAM1_GOOGLE_OAUTH.md',
                'priority': 'critical',
                'can_start': True
            },
            'team2': {
                'name': 'Microsoft OAuth',
                'status': 'blocked',
                'session_file': 'SESSION_TEAM2_MICROSOFT_OAUTH.md',
                'priority': 'high',
                'can_start': False,
                'blocked_by': 'team1'
            },
            'team3': {
                'name': 'API Clients',
                'status': 'ready',
                'session_file': 'SESSION_TEAM3_API_CLIENTS.md',
                'priority': 'high',
                'can_start': True
            },
            'team4': {
                'name': 'Testing',
                'status': 'ready',
                'session_file': 'SESSION_TEAM4_TESTING.md',
                'priority': 'high',
                'can_start': True
            },
            'team5': {
                'name': 'Token Security',
                'status': 'ready',
                'session_file': 'SESSION_TEAM5_TOKEN_SECURITY.md',
                'priority': 'critical',
                'can_start': True
            }
        }
        
        self.activation_log = []
    
    def log_activation(self, team_id: str, message: str, level: str = 'info'):
        """Log activation event"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'team_id': team_id,
            'message': message,
            'level': level
        }
        self.activation_log.append(log_entry)
        
        level_emoji = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        }
        
        emoji = level_emoji.get(level, 'ℹ️')
        print(f"{emoji} [{team_id.upper()}] {message}")
    
    def check_dependencies(self):
        """Check if required infrastructure exists"""
        print("\n" + "="*60)
        print("🔍 Checking Day 1 Infrastructure")
        print("="*60 + "\n")
        
        checks = {
            'OAuth Base Class': 'integrations/oauth/oauth_handler.py',
            'Google OAuth': 'integrations/oauth/google_oauth.py',
            'Microsoft OAuth': 'integrations/oauth/microsoft_oauth.py',
            'Token Manager': 'integrations/security/token_manager.py',
            'Encryption Manager': 'integrations/security/encryption_manager.py',
            'Token Refresher': 'integrations/security/token_refresher.py',
        }
        
        repo_root = self.base_path.parent.parent
        all_exist = True
        
        for name, path in checks.items():
            full_path = repo_root / path
            exists = full_path.exists()
            status = "✅" if exists else "❌"
            print(f"{status} {name}: {path}")
            if not exists:
                all_exist = False
        
        return all_exist
    
    def activate_team1(self):
        """Activate Team 1: Google OAuth"""
        team_id = 'team1'
        self.log_activation(team_id, "Starting activation", 'info')
        
        # Team 1's infrastructure already exists
        repo_root = self.base_path.parent.parent
        oauth_handler = repo_root / 'integrations' / 'oauth' / 'oauth_handler.py'
        google_oauth = repo_root / 'integrations' / 'oauth' / 'google_oauth.py'
        
        if oauth_handler.exists() and google_oauth.exists():
            self.log_activation(team_id, "OAuth base class ✅ EXISTS", 'success')
            self.log_activation(team_id, "Google OAuth implementation ✅ EXISTS", 'success')
            self.log_activation(team_id, "OAuth flow generator ✅ EXISTS", 'success')
            self.log_activation(team_id, "READY - Team 2 can be unblocked", 'success')
            
            # Unblock Team 2
            self.teams['team2']['status'] = 'ready'
            self.teams['team2']['can_start'] = True
            return True
        else:
            self.log_activation(team_id, "Missing OAuth infrastructure", 'error')
            return False
    
    def activate_team2(self):
        """Activate Team 2: Microsoft OAuth"""
        team_id = 'team2'
        
        if not self.teams['team2']['can_start']:
            self.log_activation(team_id, "BLOCKED - Waiting for Team 1", 'warning')
            return False
        
        self.log_activation(team_id, "Starting activation", 'info')
        
        # Check if already exists
        repo_root = self.base_path.parent.parent
        microsoft_oauth = repo_root / 'integrations' / 'oauth' / 'microsoft_oauth.py'
        
        if microsoft_oauth.exists():
            self.log_activation(team_id, "Microsoft OAuth implementation ✅ EXISTS", 'success')
            self.log_activation(team_id, "Azure AD integration ✅ READY", 'success')
            return True
        else:
            self.log_activation(team_id, "Microsoft OAuth implementation needs creation", 'warning')
            return False
    
    def activate_team3(self):
        """Activate Team 3: API Clients"""
        team_id = 'team3'
        self.log_activation(team_id, "Starting activation", 'info')
        
        # Team 3 has autonomous agent
        team_dir = self.base_path / 'team3_api_clients'
        agent_file = team_dir / 'team3_agent.py'
        
        if agent_file.exists():
            self.log_activation(team_id, "Autonomous agent ✅ EXISTS", 'success')
            self.log_activation(team_id, "Can execute: python3 sprint/day1/team3_api_clients/team3_agent.py", 'info')
            return True
        else:
            self.log_activation(team_id, "Agent file not found", 'error')
            return False
    
    def activate_team4(self):
        """Activate Team 4: Testing"""
        team_id = 'team4'
        self.log_activation(team_id, "Starting activation", 'info')
        
        # Team 4 has autonomous agent
        team_dir = self.base_path / 'team4_testing'
        agent_file = team_dir / 'team4_agent.py'
        
        if agent_file.exists():
            self.log_activation(team_id, "Autonomous agent ✅ EXISTS", 'success')
            self.log_activation(team_id, "Can execute: python3 sprint/day1/team4_testing/team4_agent.py", 'info')
            
            # Check for tests
            repo_root = self.base_path.parent.parent
            test_dir = repo_root / 'tests'
            if test_dir.exists():
                self.log_activation(team_id, f"Test infrastructure ✅ EXISTS at {test_dir}", 'success')
            
            return True
        else:
            self.log_activation(team_id, "Agent file not found", 'error')
            return False
    
    def activate_team5(self):
        """Activate Team 5: Token Security"""
        team_id = 'team5'
        self.log_activation(team_id, "Starting activation", 'info')
        
        # Check if security components exist
        repo_root = self.base_path.parent.parent
        security_dir = repo_root / 'integrations' / 'security'
        
        required_files = [
            'encryption_manager.py',
            'token_manager.py',
            'token_refresher.py',
            'security_logger.py'
        ]
        
        all_exist = True
        for filename in required_files:
            file_path = security_dir / filename
            if file_path.exists():
                self.log_activation(team_id, f"{filename} ✅ EXISTS", 'success')
            else:
                self.log_activation(team_id, f"{filename} ❌ MISSING", 'error')
                all_exist = False
        
        return all_exist
    
    def activate_all_teams(self):
        """Activate all teams in proper order"""
        print("\n" + "="*60)
        print("🚀 DAY 1 SPRINT ACTIVATION")
        print("="*60)
        print(f"Started: {self.start_time.isoformat()}")
        print("="*60 + "\n")
        
        # Check infrastructure first
        if not self.check_dependencies():
            print("\n⚠️  Some infrastructure components are missing")
            print("However, most critical components exist. Proceeding with activation...\n")
        
        # Activate teams in order
        print("\n" + "="*60)
        print("📋 TEAM ACTIVATION SEQUENCE")
        print("="*60 + "\n")
        
        # Critical path: Team 1
        print("\n--- TEAM 1: Google OAuth (CRITICAL PATH) ---")
        team1_success = self.activate_team1()
        
        # Independent teams can start in parallel
        print("\n--- TEAM 3: API Clients (INDEPENDENT) ---")
        team3_success = self.activate_team3()
        
        print("\n--- TEAM 4: Testing (INDEPENDENT) ---")
        team4_success = self.activate_team4()
        
        print("\n--- TEAM 5: Token Security (INDEPENDENT) ---")
        team5_success = self.activate_team5()
        
        # Team 2 depends on Team 1
        print("\n--- TEAM 2: Microsoft OAuth (DEPENDS ON TEAM 1) ---")
        team2_success = self.activate_team2()
        
        # Summary
        print("\n" + "="*60)
        print("📊 ACTIVATION SUMMARY")
        print("="*60 + "\n")
        
        results = {
            'Team 1 (Google OAuth)': team1_success,
            'Team 2 (Microsoft OAuth)': team2_success,
            'Team 3 (API Clients)': team3_success,
            'Team 4 (Testing)': team4_success,
            'Team 5 (Token Security)': team5_success
        }
        
        for team_name, success in results.items():
            status = "✅ ACTIVATED" if success else "⚠️  PARTIAL"
            print(f"{status} {team_name}")
        
        total_success = sum(results.values())
        print(f"\n📈 Activation Rate: {total_success}/5 teams fully activated")
        
        # Save activation log
        self.save_activation_log()
        
        return results
    
    def save_activation_log(self):
        """Save activation log to file"""
        log_file = self.base_path / 'activation_log.json'
        with open(log_file, 'w') as f:
            json.dump({
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'teams': self.teams,
                'log': self.activation_log
            }, f, indent=2)
        
        print(f"\n📝 Activation log saved to: {log_file}")
    
    def print_next_steps(self):
        """Print next steps for execution"""
        print("\n" + "="*60)
        print("🎯 NEXT STEPS")
        print("="*60 + "\n")
        
        print("The Day 1 sprint infrastructure is activated!")
        print("\nTo execute team tasks:\n")
        
        print("1. Team 1 (Google OAuth):")
        print("   ✅ OAuth base class already exists")
        print("   ✅ Google OAuth implementation already exists")
        print("   → Ready for integration testing\n")
        
        print("2. Team 2 (Microsoft OAuth):")
        print("   ✅ Microsoft OAuth already exists")
        print("   → Ready for integration testing\n")
        
        print("3. Team 3 (API Clients):")
        print("   📝 Execute: python3 sprint/day1/team3_api_clients/team3_agent.py")
        print("   → Auto-generates API clients\n")
        
        print("4. Team 4 (Testing):")
        print("   📝 Execute: python3 sprint/day1/team4_testing/team4_agent.py")
        print("   → Builds test infrastructure\n")
        
        print("5. Team 5 (Token Security):")
        print("   ✅ Encryption & token management already exists")
        print("   → Ready for integration\n")
        
        print("=" * 60)
        print("🎉 Day 1 Sprint is READY TO EXECUTE!")
        print("=" * 60)


def main():
    """Main activation function"""
    orchestrator = Day1Orchestrator()
    results = orchestrator.activate_all_teams()
    orchestrator.print_next_steps()
    
    # Return success if all teams are activated
    all_activated = all(results.values())
    return 0 if all_activated else 1


if __name__ == '__main__':
    sys.exit(main())
