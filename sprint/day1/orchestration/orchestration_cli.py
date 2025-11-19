#!/usr/bin/env python3
"""
Orchestration Command Center

Main CLI tool for orchestration team to manage Day 1 sprint coordination.
Integrates progress tracking, team coordination, and blocker management.
"""

import sys
from pathlib import Path
from typing import Optional

# Add sprint directory to path for imports
sprint_dir = Path(__file__).parent.parent
sys.path.insert(0, str(sprint_dir / "orchestration"))

from track_progress import ProgressTracker
from team_coordination import TeamCoordinator
from blocker_management import BlockerManager


class OrchestrationCenter:
    """Central command center for orchestration team."""
    
    def __init__(self, sprint_dir: Optional[Path] = None):
        """Initialize orchestration center.
        
        Args:
            sprint_dir: Path to sprint/day1 directory
        """
        if sprint_dir is None:
            sprint_dir = Path(__file__).parent.parent
        
        self.sprint_dir = Path(sprint_dir)
        self.progress_tracker = ProgressTracker(sprint_dir)
        self.coordinator = TeamCoordinator(sprint_dir)
        self.blocker_manager = BlockerManager(sprint_dir)
    
    def hourly_checkpoint(self, hour: int) -> str:
        """Generate comprehensive hourly checkpoint report.
        
        Args:
            hour: Current hour (2, 4, 6, or 8)
            
        Returns:
            Formatted checkpoint report
        """
        output = []
        
        # Header
        output.append("\n" + "=" * 100)
        output.append(f"HOUR {hour} CHECKPOINT - DAY 1 SPRINT".center(100))
        output.append("=" * 100 + "\n")
        
        # Progress Dashboard
        output.append("📊 PROGRESS DASHBOARD")
        output.append("-" * 100)
        output.append(self.progress_tracker.generate_dashboard())
        
        # Milestone Check
        output.append("\n🎯 MILESTONE CHECK")
        output.append("-" * 100)
        output.append(self.progress_tracker.generate_milestone_report(hour))
        
        # Coordination Status
        output.append("\n👥 TEAM COORDINATION")
        output.append("-" * 100)
        output.append(self.coordinator.generate_coordination_report(hour))
        
        # Blocker Status
        output.append("\n🚫 BLOCKER STATUS")
        output.append("-" * 100)
        output.append(self.blocker_manager.generate_report())
        
        # Action Items
        output.append("\n✅ ACTION ITEMS")
        output.append("-" * 100)
        
        # Check for issues
        overdue_blockers = self.blocker_manager.get_overdue_blockers()
        if overdue_blockers:
            output.append("⚠️  CRITICAL: Resolve overdue blockers immediately!")
            for blocker in overdue_blockers:
                output.append(f"   - {blocker.id}: {blocker.description}")
        
        # Check milestone gaps
        milestones = self.progress_tracker.check_milestones(hour)
        behind_teams = [
            team for team, status in milestones.items()
            if not status["met"]
        ]
        
        if behind_teams:
            output.append("\n⚠️  Teams behind schedule:")
            for team in behind_teams:
                team_name = team.replace("_", " ").title()
                output.append(f"   - {team_name}: Consider resource reallocation")
        
        if not overdue_blockers and not behind_teams:
            output.append("✅ All teams on track! Continue execution.")
        
        output.append("\n" + "=" * 100)
        
        return "\n".join(output)
    
    def quick_status(self) -> str:
        """Generate quick status overview.
        
        Returns:
            Quick status summary
        """
        output = []
        output.append("\n" + "=" * 80)
        output.append("QUICK STATUS - DAY 1 SPRINT".center(80))
        output.append("=" * 80 + "\n")
        
        # Overall progress
        all_status = self.progress_tracker.get_all_status()
        total_tasks = sum(s["stats"]["total"] for s in all_status.values())
        completed_tasks = sum(s["stats"]["completed"] for s in all_status.values())
        pct = round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
        
        output.append(f"Overall: {completed_tasks}/{total_tasks} tasks ({pct}%)")
        output.append(self.progress_tracker._render_progress_bar(pct))
        output.append("")
        
        # Team status
        for team, status in all_status.items():
            name = status["name"]
            stats = status["stats"]
            output.append(f"{name}: {stats['completed']}/{stats['total']} ({stats['percentage']}%)")
        
        output.append("")
        
        # Blockers
        open_blockers = self.blocker_manager.get_open_blockers()
        if open_blockers:
            output.append(f"🚫 Open Blockers: {len(open_blockers)}")
            critical = sum(1 for b in open_blockers if b.severity.value.startswith("P0"))
            if critical:
                output.append(f"   ⚠️  {critical} CRITICAL")
        else:
            output.append("✅ No open blockers")
        
        output.append("\n" + "=" * 80)
        
        return "\n".join(output)
    
    def team_summary(self, team: str) -> str:
        """Generate summary for specific team.
        
        Args:
            team: Team identifier
            
        Returns:
            Team summary
        """
        output = []
        
        team_info = self.coordinator.teams.get(team)
        if not team_info:
            return f"Team {team} not found"
        
        output.append("\n" + "=" * 80)
        output.append(f"{team_info['name']} - SUMMARY".center(80))
        output.append("=" * 80 + "\n")
        
        output.append(f"Lead: {team_info['lead']}")
        output.append(f"Focus: {team_info['focus']}")
        output.append("")
        
        # Progress
        team_status = self.progress_tracker.get_team_status(team)
        stats = team_status["stats"]
        output.append(f"Progress: {stats['completed']}/{stats['total']} tasks ({stats['percentage']}%)")
        output.append(self.progress_tracker._render_progress_bar(stats['percentage']))
        output.append("")
        
        # Latest status
        latest = self.coordinator.get_latest_status(team)
        if latest:
            output.append("Latest Update:")
            if latest.get("completed"):
                output.append(f"  ✅ Completed: {len(latest['completed'])} items")
            if latest.get("in_progress"):
                output.append(f"  🏗️  In Progress: {len(latest['in_progress'])} items")
            if latest.get("blocked"):
                output.append(f"  🚫 Blocked: {len(latest['blocked'])} items")
        else:
            output.append("⚠️  No status updates received")
        
        output.append("\n" + "=" * 80)
        
        return "\n".join(output)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Orchestration Command Center for Day 1 Sprint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show quick status
  %(prog)s status
  
  # Run hour 4 checkpoint
  %(prog)s checkpoint 4
  
  # View team summary
  %(prog)s team team1_google_oauth
  
  # Create a blocker
  %(prog)s blocker --team team1 --description "Base class not ready" \\
                   --severity P0 --impact "Blocks Team 2" --affected team2
  
  # Full dashboard
  %(prog)s dashboard
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Status command
    subparsers.add_parser("status", help="Quick status overview")
    
    # Dashboard command
    subparsers.add_parser("dashboard", help="Full progress dashboard")
    
    # Checkpoint command
    checkpoint_parser = subparsers.add_parser("checkpoint", 
                                              help="Hourly checkpoint report")
    checkpoint_parser.add_argument("hour", type=int, choices=[2, 4, 6, 8],
                                  help="Hour number")
    
    # Team command
    team_parser = subparsers.add_parser("team", help="Team-specific summary")
    team_parser.add_argument("team", choices=[
        "team1_google_oauth",
        "team2_microsoft_oauth",
        "team3_api_clients",
        "team4_testing",
        "team5_token_security"
    ])
    
    # Blocker command
    blocker_parser = subparsers.add_parser("blocker", help="Create/manage blockers")
    blocker_parser.add_argument("--team", help="Team reporting blocker")
    blocker_parser.add_argument("--description", help="Blocker description")
    blocker_parser.add_argument("--severity", choices=["P0", "P1", "P2", "P3"],
                                help="Severity level")
    blocker_parser.add_argument("--impact", help="Impact description")
    blocker_parser.add_argument("--affected", nargs="+", help="Affected teams")
    blocker_parser.add_argument("--list", action="store_true", 
                                help="List all blockers")
    
    # Milestone command
    milestone_parser = subparsers.add_parser("milestone", 
                                            help="Check milestone status")
    milestone_parser.add_argument("hour", type=int, choices=[2, 4, 6, 8])
    
    parser.add_argument("--sprint-dir", type=str, 
                       help="Path to sprint/day1 directory")
    
    args = parser.parse_args()
    
    center = OrchestrationCenter(
        sprint_dir=Path(args.sprint_dir) if args.sprint_dir else None
    )
    
    if args.command == "status":
        print(center.quick_status())
    
    elif args.command == "dashboard":
        print(center.progress_tracker.generate_dashboard())
    
    elif args.command == "checkpoint":
        print(center.hourly_checkpoint(args.hour))
    
    elif args.command == "team":
        print(center.team_summary(args.team))
    
    elif args.command == "blocker":
        if args.list:
            print(center.blocker_manager.generate_report())
        elif all([args.team, args.description, args.severity, args.impact, args.affected]):
            blocker = center.blocker_manager.create_blocker(
                team=args.team,
                description=args.description,
                severity=args.severity,
                impact=args.impact,
                affected_teams=args.affected
            )
            print(f"✅ Blocker created: {blocker.id}")
        else:
            print("Error: When creating a blocker, provide --team, --description, "
                  "--severity, --impact, and --affected")
            print("Or use --list to show all blockers")
    
    elif args.command == "milestone":
        print(center.progress_tracker.generate_milestone_report(args.hour))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
