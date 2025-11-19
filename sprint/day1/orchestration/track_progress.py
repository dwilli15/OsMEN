#!/usr/bin/env python3
"""
Progress Tracking Dashboard for Orchestration Team

Monitors progress across all 5 teams, tracks milestones, and generates
status reports for Day 1 OAuth & API Foundation sprint.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import re


class ProgressTracker:
    """Track and visualize progress across all Day 1 teams."""
    
    def __init__(self, sprint_dir: Optional[Path] = None):
        """Initialize progress tracker.
        
        Args:
            sprint_dir: Path to sprint/day1 directory
        """
        if sprint_dir is None:
            sprint_dir = Path(__file__).parent.parent
        self.sprint_dir = Path(sprint_dir)
        self.teams = [
            "team1_google_oauth",
            "team2_microsoft_oauth",
            "team3_api_clients",
            "team4_testing",
            "team5_token_security"
        ]
        self.hourly_milestones = self._load_milestones()
    
    def _load_milestones(self) -> Dict[int, Dict[str, str]]:
        """Load hourly milestone definitions."""
        return {
            2: {
                "team1_google_oauth": "Base class ✓",
                "team2_microsoft_oauth": "Azure config ✓",
                "team3_api_clients": "Generator setup ✓",
                "team4_testing": "pytest setup ✓",
                "team5_token_security": "Encryption ✓"
            },
            4: {
                "team1_google_oauth": "Google OAuth ✓",
                "team2_microsoft_oauth": "MS OAuth start ✓",
                "team3_api_clients": "Calendar client ✓",
                "team4_testing": "Mock server ✓",
                "team5_token_security": "TokenManager ✓"
            },
            6: {
                "team1_google_oauth": "Token refresh ✓",
                "team2_microsoft_oauth": "Token exchange ✓",
                "team3_api_clients": "All clients ✓",
                "team4_testing": "30+ tests ✓",
                "team5_token_security": "Auto refresh ✓"
            },
            8: {
                "team1_google_oauth": "Complete ✓",
                "team2_microsoft_oauth": "Complete ✓",
                "team3_api_clients": "Complete ✓",
                "team4_testing": "50+ tests ✓",
                "team5_token_security": "Complete ✓"
            }
        }
    
    def parse_todo(self, todo_path: Path) -> Dict:
        """Parse a TODO.md file and extract task status.
        
        Args:
            todo_path: Path to TODO.md file
            
        Returns:
            Dictionary with task statistics
        """
        if not todo_path.exists():
            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "blocked": 0,
                "percentage": 0
            }
        
        content = todo_path.read_text()
        
        # Count checkboxes
        total = len(re.findall(r'- \[[x ]\]', content))
        completed = len(re.findall(r'- \[x\]', content))
        
        # Look for blockers in content
        blocked = len(re.findall(r'🚫|BLOCKED|blocker', content, re.IGNORECASE))
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": total - completed - blocked,
            "blocked": blocked,
            "percentage": round((completed / total * 100) if total > 0 else 0, 1)
        }
    
    def get_team_status(self, team_name: str) -> Dict:
        """Get current status for a team.
        
        Args:
            team_name: Name of the team directory
            
        Returns:
            Dictionary with team status
        """
        team_dir = self.sprint_dir / team_name
        todo_path = team_dir / "TODO.md"
        
        stats = self.parse_todo(todo_path)
        
        return {
            "name": team_name.replace("_", " ").title(),
            "stats": stats,
            "last_updated": datetime.fromtimestamp(
                todo_path.stat().st_mtime
            ).isoformat() if todo_path.exists() else None
        }
    
    def get_all_status(self) -> Dict:
        """Get status for all teams.
        
        Returns:
            Dictionary with all team statuses
        """
        return {
            team: self.get_team_status(team)
            for team in self.teams
        }
    
    def generate_dashboard(self) -> str:
        """Generate ASCII dashboard showing all team progress.
        
        Returns:
            Formatted dashboard string
        """
        all_status = self.get_all_status()
        
        output = []
        output.append("\n" + "=" * 80)
        output.append("DAY 1 PROGRESS DASHBOARD".center(80))
        output.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        output.append("=" * 80 + "\n")
        
        # Overall stats
        total_tasks = sum(s["stats"]["total"] for s in all_status.values())
        completed_tasks = sum(s["stats"]["completed"] for s in all_status.values())
        overall_pct = round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
        
        output.append(f"Overall Progress: {completed_tasks}/{total_tasks} tasks ({overall_pct}%)")
        output.append(self._render_progress_bar(overall_pct))
        output.append("")
        
        # Individual team progress
        for team, status in all_status.items():
            team_name = status["name"]
            stats = status["stats"]
            pct = stats["percentage"]
            
            output.append(f"{team_name}")
            output.append(f"  Progress: {stats['completed']}/{stats['total']} tasks ({pct}%)")
            output.append(f"  {self._render_progress_bar(pct, width=60)}")
            
            if stats["blocked"] > 0:
                output.append(f"  🚫 BLOCKERS: {stats['blocked']}")
            
            output.append("")
        
        output.append("=" * 80)
        
        return "\n".join(output)
    
    def _render_progress_bar(self, percentage: float, width: int = 70) -> str:
        """Render a text progress bar.
        
        Args:
            percentage: Completion percentage (0-100)
            width: Width of the bar in characters
            
        Returns:
            ASCII progress bar string
        """
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage}%"
    
    def check_milestones(self, current_hour: int) -> Dict:
        """Check if teams have met their hourly milestones.
        
        Args:
            current_hour: Current hour of the sprint (2, 4, 6, or 8)
            
        Returns:
            Dictionary with milestone status
        """
        if current_hour not in self.hourly_milestones:
            return {}
        
        milestones = self.hourly_milestones[current_hour]
        all_status = self.get_all_status()
        
        results = {}
        for team, expected in milestones.items():
            team_stats = all_status[team]["stats"]
            # Consider milestone met if >50% complete
            met = team_stats["percentage"] >= 50
            results[team] = {
                "expected": expected,
                "met": met,
                "percentage": team_stats["percentage"]
            }
        
        return results
    
    def generate_milestone_report(self, current_hour: int) -> str:
        """Generate milestone check report.
        
        Args:
            current_hour: Current hour of the sprint
            
        Returns:
            Formatted milestone report
        """
        milestone_status = self.check_milestones(current_hour)
        
        if not milestone_status:
            return f"No milestones defined for hour {current_hour}"
        
        output = []
        output.append("\n" + "=" * 80)
        output.append(f"HOUR {current_hour} MILESTONE CHECK".center(80))
        output.append("=" * 80 + "\n")
        
        met_count = sum(1 for s in milestone_status.values() if s["met"])
        total_count = len(milestone_status)
        
        output.append(f"Milestones Met: {met_count}/{total_count}\n")
        
        for team, status in milestone_status.items():
            team_name = team.replace("_", " ").title()
            met_icon = "✅" if status["met"] else "❌"
            
            output.append(f"{met_icon} {team_name}: {status['expected']}")
            output.append(f"   Current progress: {status['percentage']}%")
            
            if not status["met"]:
                output.append(f"   ⚠️  BEHIND SCHEDULE")
            
            output.append("")
        
        output.append("=" * 80)
        
        return "\n".join(output)
    
    def export_metrics(self, output_file: Optional[Path] = None) -> Dict:
        """Export current metrics as JSON.
        
        Args:
            output_file: Optional path to save JSON file
            
        Returns:
            Metrics dictionary
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "teams": self.get_all_status(),
            "overall": {
                "total_tasks": sum(s["stats"]["total"] for s in self.get_all_status().values()),
                "completed_tasks": sum(s["stats"]["completed"] for s in self.get_all_status().values()),
                "blocked_count": sum(s["stats"]["blocked"] for s in self.get_all_status().values())
            }
        }
        
        metrics["overall"]["percentage"] = round(
            (metrics["overall"]["completed_tasks"] / metrics["overall"]["total_tasks"] * 100)
            if metrics["overall"]["total_tasks"] > 0 else 0,
            1
        )
        
        if output_file:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(json.dumps(metrics, indent=2))
        
        return metrics


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Track progress across Day 1 sprint teams"
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Show progress dashboard"
    )
    parser.add_argument(
        "--milestone",
        type=int,
        choices=[2, 4, 6, 8],
        help="Check milestone for hour (2, 4, 6, or 8)"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export metrics to JSON file"
    )
    parser.add_argument(
        "--sprint-dir",
        type=str,
        help="Path to sprint/day1 directory"
    )
    
    args = parser.parse_args()
    
    tracker = ProgressTracker(
        sprint_dir=Path(args.sprint_dir) if args.sprint_dir else None
    )
    
    if args.milestone:
        print(tracker.generate_milestone_report(args.milestone))
    elif args.export:
        metrics = tracker.export_metrics(Path(args.export))
        print(f"Metrics exported to {args.export}")
        print(f"Overall: {metrics['overall']['completed_tasks']}/{metrics['overall']['total_tasks']} tasks")
    else:
        # Default: show dashboard
        print(tracker.generate_dashboard())


if __name__ == "__main__":
    main()
