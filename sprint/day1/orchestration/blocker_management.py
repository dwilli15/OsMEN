#!/usr/bin/env python3
"""
Blocker Management System for Orchestration

Track, prioritize, and resolve blockers across all Day 1 teams with
severity levels and escalation protocols.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


class Severity(Enum):
    """Blocker severity levels."""
    P0_CRITICAL = "P0 (Critical)"
    P1_HIGH = "P1 (High)"
    P2_MEDIUM = "P2 (Medium)"
    P3_LOW = "P3 (Low)"


class BlockerStatus(Enum):
    """Blocker resolution status."""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    DEFERRED = "Deferred"


class Blocker:
    """Represents a single blocker."""
    
    def __init__(
        self,
        id: str,
        team: str,
        description: str,
        severity: Severity,
        impact: str,
        affected_teams: List[str],
        reported_by: str = "Unknown",
        reported_at: Optional[datetime] = None
    ):
        """Initialize a blocker.
        
        Args:
            id: Unique identifier
            team: Team reporting the blocker
            description: Description of the blocker
            severity: Severity level
            impact: Impact description
            affected_teams: List of teams affected
            reported_by: Who reported it
            reported_at: When it was reported
        """
        self.id = id
        self.team = team
        self.description = description
        self.severity = severity
        self.impact = impact
        self.affected_teams = affected_teams
        self.reported_by = reported_by
        self.reported_at = reported_at or datetime.now()
        self.status = BlockerStatus.OPEN
        self.assigned_to = None
        self.updates = []
        self.resolved_at = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "team": self.team,
            "description": self.description,
            "severity": self.severity.value,
            "impact": self.impact,
            "affected_teams": self.affected_teams,
            "reported_by": self.reported_by,
            "reported_at": self.reported_at.isoformat(),
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "updates": self.updates,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "age_minutes": self.age_minutes()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Blocker':
        """Create blocker from dictionary."""
        blocker = cls(
            id=data["id"],
            team=data["team"],
            description=data["description"],
            severity=Severity(data["severity"]),
            impact=data["impact"],
            affected_teams=data["affected_teams"],
            reported_by=data.get("reported_by", "Unknown"),
            reported_at=datetime.fromisoformat(data["reported_at"])
        )
        blocker.status = BlockerStatus(data["status"])
        blocker.assigned_to = data.get("assigned_to")
        blocker.updates = data.get("updates", [])
        
        if data.get("resolved_at"):
            blocker.resolved_at = datetime.fromisoformat(data["resolved_at"])
        
        return blocker
    
    def age_minutes(self) -> int:
        """Get age of blocker in minutes."""
        if self.resolved_at:
            delta = self.resolved_at - self.reported_at
        else:
            delta = datetime.now() - self.reported_at
        
        return int(delta.total_seconds() / 60)
    
    def is_overdue(self) -> bool:
        """Check if blocker is overdue based on severity."""
        age = self.age_minutes()
        
        if self.severity == Severity.P0_CRITICAL:
            return age > 15  # Critical must be resolved in 15 min
        elif self.severity == Severity.P1_HIGH:
            return age > 60  # High must be resolved in 1 hour
        elif self.severity == Severity.P2_MEDIUM:
            return age > 120  # Medium must be resolved in 2 hours
        
        return False


class BlockerManager:
    """Manage blockers across all teams."""
    
    def __init__(self, sprint_dir: Optional[Path] = None):
        """Initialize blocker manager.
        
        Args:
            sprint_dir: Path to sprint/day1 directory
        """
        if sprint_dir is None:
            sprint_dir = Path(__file__).parent.parent
        self.sprint_dir = Path(sprint_dir)
        self.blockers_file = self.sprint_dir / "orchestration" / "blockers.json"
        self.blockers: Dict[str, Blocker] = self._load_blockers()
    
    def create_blocker(
        self,
        team: str,
        description: str,
        severity: str,
        impact: str,
        affected_teams: List[str],
        reported_by: str = "Unknown"
    ) -> Blocker:
        """Create a new blocker.
        
        Args:
            team: Team reporting the blocker
            description: Description of the blocker
            severity: Severity level (P0, P1, P2, P3)
            impact: Impact description
            affected_teams: List of affected teams
            reported_by: Who reported it
            
        Returns:
            Created Blocker instance
        """
        # Generate ID
        blocker_id = f"BLK-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Parse severity
        severity_map = {
            "P0": Severity.P0_CRITICAL,
            "P1": Severity.P1_HIGH,
            "P2": Severity.P2_MEDIUM,
            "P3": Severity.P3_LOW
        }
        severity_enum = severity_map.get(severity.upper(), Severity.P2_MEDIUM)
        
        blocker = Blocker(
            id=blocker_id,
            team=team,
            description=description,
            severity=severity_enum,
            impact=impact,
            affected_teams=affected_teams,
            reported_by=reported_by
        )
        
        self.blockers[blocker_id] = blocker
        self._save_blockers()
        
        return blocker
    
    def update_blocker(
        self,
        blocker_id: str,
        update: str,
        updated_by: str = "Unknown"
    ) -> None:
        """Add an update to a blocker.
        
        Args:
            blocker_id: Blocker ID
            update: Update text
            updated_by: Who provided the update
        """
        if blocker_id not in self.blockers:
            raise ValueError(f"Blocker {blocker_id} not found")
        
        self.blockers[blocker_id].updates.append({
            "timestamp": datetime.now().isoformat(),
            "update": update,
            "updated_by": updated_by
        })
        
        self._save_blockers()
    
    def assign_blocker(self, blocker_id: str, assignee: str) -> None:
        """Assign a blocker to someone.
        
        Args:
            blocker_id: Blocker ID
            assignee: Person to assign to
        """
        if blocker_id not in self.blockers:
            raise ValueError(f"Blocker {blocker_id} not found")
        
        self.blockers[blocker_id].assigned_to = assignee
        self.blockers[blocker_id].status = BlockerStatus.IN_PROGRESS
        self._save_blockers()
    
    def resolve_blocker(
        self,
        blocker_id: str,
        resolution: str,
        resolved_by: str = "Unknown"
    ) -> None:
        """Resolve a blocker.
        
        Args:
            blocker_id: Blocker ID
            resolution: Resolution description
            resolved_by: Who resolved it
        """
        if blocker_id not in self.blockers:
            raise ValueError(f"Blocker {blocker_id} not found")
        
        blocker = self.blockers[blocker_id]
        blocker.status = BlockerStatus.RESOLVED
        blocker.resolved_at = datetime.now()
        blocker.updates.append({
            "timestamp": datetime.now().isoformat(),
            "update": f"RESOLVED: {resolution}",
            "updated_by": resolved_by
        })
        
        self._save_blockers()
    
    def get_open_blockers(self) -> List[Blocker]:
        """Get all open blockers.
        
        Returns:
            List of open blockers sorted by severity
        """
        open_blockers = [
            b for b in self.blockers.values()
            if b.status in [BlockerStatus.OPEN, BlockerStatus.IN_PROGRESS]
        ]
        
        # Sort by severity (P0 first)
        severity_order = {
            Severity.P0_CRITICAL: 0,
            Severity.P1_HIGH: 1,
            Severity.P2_MEDIUM: 2,
            Severity.P3_LOW: 3
        }
        
        return sorted(open_blockers, key=lambda b: severity_order[b.severity])
    
    def get_overdue_blockers(self) -> List[Blocker]:
        """Get all overdue blockers.
        
        Returns:
            List of overdue blockers
        """
        return [b for b in self.get_open_blockers() if b.is_overdue()]
    
    def generate_report(self) -> str:
        """Generate blocker status report.
        
        Returns:
            Formatted report
        """
        output = []
        output.append("\n" + "=" * 80)
        output.append("BLOCKER STATUS REPORT".center(80))
        output.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        output.append("=" * 80 + "\n")
        
        open_blockers = self.get_open_blockers()
        overdue = self.get_overdue_blockers()
        
        # Summary
        output.append(f"Total Blockers: {len(self.blockers)}")
        output.append(f"Open: {len(open_blockers)}")
        output.append(f"Overdue: {len(overdue)} ⚠️" if overdue else "Overdue: 0")
        output.append("")
        
        if not open_blockers:
            output.append("✅ No open blockers!\n")
        else:
            # Critical alerts
            critical = [b for b in open_blockers if b.severity == Severity.P0_CRITICAL]
            if critical:
                output.append("🚨 CRITICAL BLOCKERS (P0):")
                for blocker in critical:
                    output.append(f"\n  {blocker.id} - {blocker.team}")
                    output.append(f"  {blocker.description}")
                    output.append(f"  Impact: {blocker.impact}")
                    output.append(f"  Age: {blocker.age_minutes()} minutes")
                    if blocker.is_overdue():
                        output.append("  ⚠️  OVERDUE - IMMEDIATE ACTION REQUIRED")
                    if blocker.assigned_to:
                        output.append(f"  Assigned to: {blocker.assigned_to}")
                output.append("")
            
            # Other open blockers
            other = [b for b in open_blockers if b.severity != Severity.P0_CRITICAL]
            if other:
                output.append("📋 OTHER OPEN BLOCKERS:")
                for blocker in other:
                    overdue_marker = " ⚠️ OVERDUE" if blocker.is_overdue() else ""
                    output.append(f"\n  {blocker.id} - {blocker.severity.value} - {blocker.team}{overdue_marker}")
                    output.append(f"  {blocker.description}")
                    output.append(f"  Age: {blocker.age_minutes()} minutes")
                    if blocker.assigned_to:
                        output.append(f"  Assigned to: {blocker.assigned_to}")
        
        output.append("\n" + "=" * 80)
        
        return "\n".join(output)
    
    def generate_blocker_details(self, blocker_id: str) -> str:
        """Generate detailed report for a specific blocker.
        
        Args:
            blocker_id: Blocker ID
            
        Returns:
            Formatted detailed report
        """
        if blocker_id not in self.blockers:
            return f"Blocker {blocker_id} not found"
        
        blocker = self.blockers[blocker_id]
        
        output = []
        output.append("\n" + "=" * 80)
        output.append(f"BLOCKER DETAILS: {blocker.id}".center(80))
        output.append("=" * 80 + "\n")
        
        output.append(f"Team: {blocker.team}")
        output.append(f"Severity: {blocker.severity.value}")
        output.append(f"Status: {blocker.status.value}")
        output.append(f"Reported by: {blocker.reported_by}")
        output.append(f"Reported at: {blocker.reported_at.strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"Age: {blocker.age_minutes()} minutes")
        
        if blocker.assigned_to:
            output.append(f"Assigned to: {blocker.assigned_to}")
        
        output.append(f"\nDescription:")
        output.append(f"  {blocker.description}")
        
        output.append(f"\nImpact:")
        output.append(f"  {blocker.impact}")
        
        output.append(f"\nAffected Teams:")
        for team in blocker.affected_teams:
            output.append(f"  - {team}")
        
        if blocker.updates:
            output.append(f"\nUpdates:")
            for update in blocker.updates:
                timestamp = datetime.fromisoformat(update["timestamp"]).strftime('%H:%M:%S')
                output.append(f"  [{timestamp}] {update['updated_by']}: {update['update']}")
        
        if blocker.is_overdue():
            output.append("\n⚠️  WARNING: This blocker is OVERDUE!")
        
        output.append("\n" + "=" * 80)
        
        return "\n".join(output)
    
    def _load_blockers(self) -> Dict[str, Blocker]:
        """Load blockers from file."""
        if not self.blockers_file.exists():
            return {}
        
        try:
            data = json.loads(self.blockers_file.read_text())
            return {
                blocker_id: Blocker.from_dict(blocker_data)
                for blocker_id, blocker_data in data.items()
            }
        except Exception:
            return {}
    
    def _save_blockers(self) -> None:
        """Save blockers to file."""
        self.blockers_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            blocker_id: blocker.to_dict()
            for blocker_id, blocker in self.blockers.items()
        }
        self.blockers_file.write_text(json.dumps(data, indent=2))


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Manage blockers for Day 1 sprint"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create blocker
    create_parser = subparsers.add_parser("create", help="Create a new blocker")
    create_parser.add_argument("team", help="Team reporting the blocker")
    create_parser.add_argument("description", help="Blocker description")
    create_parser.add_argument("--severity", choices=["P0", "P1", "P2", "P3"],
                               default="P2", help="Severity level")
    create_parser.add_argument("--impact", required=True, help="Impact description")
    create_parser.add_argument("--affected", nargs="+", required=True,
                              help="Affected teams")
    create_parser.add_argument("--reported-by", default="Unknown",
                              help="Who reported it")
    
    # Update blocker
    update_parser = subparsers.add_parser("update", help="Update a blocker")
    update_parser.add_argument("blocker_id", help="Blocker ID")
    update_parser.add_argument("update", help="Update text")
    update_parser.add_argument("--updated-by", default="Unknown",
                              help="Who provided the update")
    
    # Assign blocker
    assign_parser = subparsers.add_parser("assign", help="Assign a blocker")
    assign_parser.add_argument("blocker_id", help="Blocker ID")
    assign_parser.add_argument("assignee", help="Person to assign to")
    
    # Resolve blocker
    resolve_parser = subparsers.add_parser("resolve", help="Resolve a blocker")
    resolve_parser.add_argument("blocker_id", help="Blocker ID")
    resolve_parser.add_argument("resolution", help="Resolution description")
    resolve_parser.add_argument("--resolved-by", default="Unknown",
                               help="Who resolved it")
    
    # List blockers
    subparsers.add_parser("list", help="List all blockers")
    
    # Show blocker details
    details_parser = subparsers.add_parser("details", help="Show blocker details")
    details_parser.add_argument("blocker_id", help="Blocker ID")
    
    parser.add_argument("--sprint-dir", type=str, help="Path to sprint/day1 directory")
    
    args = parser.parse_args()
    
    manager = BlockerManager(
        sprint_dir=Path(args.sprint_dir) if args.sprint_dir else None
    )
    
    if args.command == "create":
        blocker = manager.create_blocker(
            team=args.team,
            description=args.description,
            severity=args.severity,
            impact=args.impact,
            affected_teams=args.affected,
            reported_by=args.reported_by
        )
        print(f"✅ Blocker created: {blocker.id}")
        print(f"   Severity: {blocker.severity.value}")
        print(f"   Team: {blocker.team}")
    
    elif args.command == "update":
        manager.update_blocker(args.blocker_id, args.update, args.updated_by)
        print(f"✅ Blocker {args.blocker_id} updated")
    
    elif args.command == "assign":
        manager.assign_blocker(args.blocker_id, args.assignee)
        print(f"✅ Blocker {args.blocker_id} assigned to {args.assignee}")
    
    elif args.command == "resolve":
        manager.resolve_blocker(args.blocker_id, args.resolution, args.resolved_by)
        print(f"✅ Blocker {args.blocker_id} resolved")
    
    elif args.command == "list":
        print(manager.generate_report())
    
    elif args.command == "details":
        print(manager.generate_blocker_details(args.blocker_id))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
