#!/usr/bin/env python3
"""
Team Coordination Tool for Orchestration

Manages team check-ins, dependency tracking, and cross-team communication
for Day 1 sprint coordination.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


class TeamCoordinator:
    """Coordinate work across multiple teams and manage dependencies."""
    
    def __init__(self, sprint_dir: Optional[Path] = None):
        """Initialize team coordinator.
        
        Args:
            sprint_dir: Path to sprint/day1 directory
        """
        if sprint_dir is None:
            sprint_dir = Path(__file__).parent.parent
        self.sprint_dir = Path(sprint_dir)
        
        # Define team structure
        self.teams = {
            "team1_google_oauth": {
                "name": "Google OAuth",
                "lead": "OAuth/API Integration Lead",
                "focus": "Universal OAuth framework + Google OAuth flows"
            },
            "team2_microsoft_oauth": {
                "name": "Microsoft OAuth",
                "lead": "OAuth Lead (Secondary)",
                "focus": "Microsoft OAuth + Azure AD integration"
            },
            "team3_api_clients": {
                "name": "API Client Generation",
                "lead": "Automation Engineer",
                "focus": "Auto-generate Python API clients"
            },
            "team4_testing": {
                "name": "Testing Infrastructure",
                "lead": "QA Engineer",
                "focus": "Comprehensive testing framework"
            },
            "team5_token_security": {
                "name": "Token Security",
                "lead": "Security Engineer",
                "focus": "Secure token handling"
            }
        }
        
        # Define dependencies between teams
        self.dependencies = {
            2: {  # Hour 2 dependencies
                "team2_microsoft_oauth": ["team1_google_oauth"],  # Team 2 needs Team 1 base class
                "team5_token_security": ["team1_google_oauth"],   # Team 5 needs token structure
                "team3_api_clients": ["team1_google_oauth"]       # Team 3 needs OAuth interface
            },
            4: {  # Hour 4 dependencies
                "team4_testing": ["team3_api_clients"],           # Team 4 needs API clients
                "team1_google_oauth": ["team5_token_security"],   # Team 1 integrates encryption
                "team2_microsoft_oauth": ["team5_token_security"],
                "team3_api_clients": ["team5_token_security"]
            },
            6: {  # Hour 6 dependencies
                "team4_testing": ["team1_google_oauth", "team2_microsoft_oauth", 
                                 "team3_api_clients", "team5_token_security"]
            }
        }
        
        self.status_file = self.sprint_dir / "orchestration" / "team_status.json"
    
    def record_status(self, team: str, status: Dict) -> None:
        """Record a status update from a team.
        
        Args:
            team: Team identifier
            status: Status dictionary with completed, in_progress, blocked, next
        """
        all_status = self._load_status()
        
        if team not in all_status:
            all_status[team] = []
        
        status["timestamp"] = datetime.now().isoformat()
        all_status[team].append(status)
        
        self._save_status(all_status)
    
    def get_latest_status(self, team: str) -> Optional[Dict]:
        """Get the most recent status for a team.
        
        Args:
            team: Team identifier
            
        Returns:
            Latest status dictionary or None
        """
        all_status = self._load_status()
        
        if team not in all_status or not all_status[team]:
            return None
        
        return all_status[team][-1]
    
    def check_dependencies(self, team: str, current_hour: int) -> Dict:
        """Check if a team's dependencies are met.
        
        Args:
            team: Team identifier
            current_hour: Current hour of the sprint
            
        Returns:
            Dictionary with dependency status
        """
        if current_hour not in self.dependencies:
            return {"ready": True, "blocking_teams": []}
        
        if team not in self.dependencies[current_hour]:
            return {"ready": True, "blocking_teams": []}
        
        required_teams = self.dependencies[current_hour][team]
        blocking_teams = []
        
        for required_team in required_teams:
            status = self.get_latest_status(required_team)
            
            # Check if dependency team has completed their milestone
            if not status or not status.get("milestone_complete", False):
                blocking_teams.append({
                    "team": required_team,
                    "name": self.teams[required_team]["name"]
                })
        
        return {
            "ready": len(blocking_teams) == 0,
            "blocking_teams": blocking_teams
        }
    
    def generate_standup_prompt(self, team: str) -> str:
        """Generate a stand-up prompt for a team.
        
        Args:
            team: Team identifier
            
        Returns:
            Formatted stand-up prompt
        """
        team_info = self.teams[team]
        
        prompt = []
        prompt.append(f"\n{'=' * 60}")
        prompt.append(f"{team_info['name']} - Stand-up Update".center(60))
        prompt.append(f"{'=' * 60}\n")
        prompt.append("Please provide updates for the following:\n")
        prompt.append("✅ COMPLETED:")
        prompt.append("   What tasks have you finished since last check-in?\n")
        prompt.append("🏗️  IN PROGRESS:")
        prompt.append("   What are you currently working on?\n")
        prompt.append("🚫 BLOCKED:")
        prompt.append("   Any blockers preventing progress?\n")
        prompt.append("⏭️  NEXT:")
        prompt.append("   What will you work on next?\n")
        prompt.append(f"{'=' * 60}\n")
        
        return "\n".join(prompt)
    
    def parse_standup_response(self, team: str, response: str) -> Dict:
        """Parse a stand-up response from a team.
        
        Args:
            team: Team identifier
            response: Team's stand-up response text
            
        Returns:
            Parsed status dictionary
        """
        # Simple parsing - look for sections
        sections = {
            "completed": [],
            "in_progress": [],
            "blocked": [],
            "next": []
        }
        
        current_section = None
        for line in response.split("\n"):
            line = line.strip()
            
            if not line:
                continue
            
            # Detect section headers
            if "COMPLETED" in line.upper() or "✅" in line:
                current_section = "completed"
            elif "IN PROGRESS" in line.upper() or "🏗️" in line:
                current_section = "in_progress"
            elif "BLOCKED" in line.upper() or "🚫" in line:
                current_section = "blocked"
            elif "NEXT" in line.upper() or "⏭️" in line:
                current_section = "next"
            elif current_section and (line.startswith("-") or line.startswith("*")):
                # Task item
                sections[current_section].append(line.lstrip("-*").strip())
        
        return sections
    
    def generate_coordination_report(self, current_hour: int) -> str:
        """Generate a coordination report for current hour.
        
        Args:
            current_hour: Current hour of the sprint
            
        Returns:
            Formatted coordination report
        """
        output = []
        output.append("\n" + "=" * 80)
        output.append(f"HOUR {current_hour} COORDINATION REPORT".center(80))
        output.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        output.append("=" * 80 + "\n")
        
        # Check each team
        for team_id, team_info in self.teams.items():
            output.append(f"📋 {team_info['name']}")
            output.append(f"   Lead: {team_info['lead']}")
            
            # Get latest status
            status = self.get_latest_status(team_id)
            if status:
                age_minutes = (datetime.now() - datetime.fromisoformat(status["timestamp"])).total_seconds() / 60
                output.append(f"   Last update: {int(age_minutes)} minutes ago")
                
                if status.get("completed"):
                    output.append(f"   ✅ Completed: {len(status['completed'])} items")
                if status.get("blocked"):
                    output.append(f"   🚫 Blocked: {len(status['blocked'])} items")
            else:
                output.append("   ⚠️  No status updates received")
            
            # Check dependencies
            deps = self.check_dependencies(team_id, current_hour)
            if not deps["ready"]:
                output.append("   ⏸️  WAITING ON:")
                for blocking in deps["blocking_teams"]:
                    output.append(f"      - {blocking['name']}")
            
            output.append("")
        
        output.append("=" * 80)
        
        return "\n".join(output)
    
    def identify_blockers(self) -> List[Dict]:
        """Identify all current blockers across teams.
        
        Returns:
            List of blocker dictionaries
        """
        blockers = []
        
        for team_id in self.teams.keys():
            status = self.get_latest_status(team_id)
            
            if status and status.get("blocked"):
                for blocker in status["blocked"]:
                    blockers.append({
                        "team": self.teams[team_id]["name"],
                        "team_id": team_id,
                        "issue": blocker,
                        "timestamp": status["timestamp"]
                    })
        
        return blockers
    
    def generate_blocker_report(self) -> str:
        """Generate a report of all current blockers.
        
        Returns:
            Formatted blocker report
        """
        blockers = self.identify_blockers()
        
        output = []
        output.append("\n" + "=" * 80)
        output.append("BLOCKER REPORT".center(80))
        output.append("=" * 80 + "\n")
        
        if not blockers:
            output.append("✅ No blockers reported!\n")
        else:
            output.append(f"🚫 {len(blockers)} BLOCKER(S) IDENTIFIED\n")
            
            for i, blocker in enumerate(blockers, 1):
                output.append(f"{i}. {blocker['team']}")
                output.append(f"   Issue: {blocker['issue']}")
                
                age_minutes = (datetime.now() - datetime.fromisoformat(blocker["timestamp"])).total_seconds() / 60
                output.append(f"   Reported: {int(age_minutes)} minutes ago")
                
                if age_minutes > 15:
                    output.append("   ⚠️  CRITICAL: Blocker over 15 minutes old!")
                
                output.append("")
        
        output.append("=" * 80)
        
        return "\n".join(output)
    
    def _load_status(self) -> Dict:
        """Load team status from file."""
        if not self.status_file.exists():
            return {}
        
        try:
            return json.loads(self.status_file.read_text())
        except Exception:
            return {}
    
    def _save_status(self, status: Dict) -> None:
        """Save team status to file."""
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        self.status_file.write_text(json.dumps(status, indent=2))


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Coordinate teams for Day 1 sprint"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Record team status")
    status_parser.add_argument("team", choices=[
        "team1_google_oauth",
        "team2_microsoft_oauth",
        "team3_api_clients",
        "team4_testing",
        "team5_token_security"
    ])
    status_parser.add_argument("--completed", nargs="+", help="Completed items")
    status_parser.add_argument("--in-progress", nargs="+", help="In progress items")
    status_parser.add_argument("--blocked", nargs="+", help="Blocked items")
    status_parser.add_argument("--next", nargs="+", help="Next items")
    status_parser.add_argument("--milestone-complete", action="store_true", 
                              help="Mark milestone as complete")
    
    # Standup command
    standup_parser = subparsers.add_parser("standup", help="Generate stand-up prompt")
    standup_parser.add_argument("team", choices=[
        "team1_google_oauth",
        "team2_microsoft_oauth",
        "team3_api_clients",
        "team4_testing",
        "team5_token_security"
    ])
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate coordination report")
    report_parser.add_argument("hour", type=int, choices=[2, 4, 6, 8], 
                              help="Current hour")
    
    # Blockers command
    subparsers.add_parser("blockers", help="Show all blockers")
    
    # Check deps command
    deps_parser = subparsers.add_parser("check-deps", help="Check dependencies")
    deps_parser.add_argument("team", choices=[
        "team1_google_oauth",
        "team2_microsoft_oauth",
        "team3_api_clients",
        "team4_testing",
        "team5_token_security"
    ])
    deps_parser.add_argument("hour", type=int, choices=[2, 4, 6, 8])
    
    parser.add_argument("--sprint-dir", type=str, help="Path to sprint/day1 directory")
    
    args = parser.parse_args()
    
    coordinator = TeamCoordinator(
        sprint_dir=Path(args.sprint_dir) if args.sprint_dir else None
    )
    
    if args.command == "status":
        status = {
            "completed": args.completed or [],
            "in_progress": getattr(args, "in_progress") or [],
            "blocked": args.blocked or [],
            "next": getattr(args, "next") or [],
            "milestone_complete": args.milestone_complete
        }
        coordinator.record_status(args.team, status)
        print(f"✅ Status recorded for {coordinator.teams[args.team]['name']}")
    
    elif args.command == "standup":
        print(coordinator.generate_standup_prompt(args.team))
    
    elif args.command == "report":
        print(coordinator.generate_coordination_report(args.hour))
    
    elif args.command == "blockers":
        print(coordinator.generate_blocker_report())
    
    elif args.command == "check-deps":
        deps = coordinator.check_dependencies(args.team, args.hour)
        team_name = coordinator.teams[args.team]['name']
        
        if deps["ready"]:
            print(f"✅ {team_name} is ready to proceed (all dependencies met)")
        else:
            print(f"⏸️  {team_name} is waiting on:")
            for blocking in deps["blocking_teams"]:
                print(f"   - {blocking['name']}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
