#!/usr/bin/env python3
"""
Example Usage Scenarios for Orchestration Tools

This script demonstrates common workflows and usage patterns for the
orchestration project management tools.
"""

from pathlib import Path
import sys

# Setup paths
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from track_progress import ProgressTracker
from team_coordination import TeamCoordinator
from blocker_management import BlockerManager, Severity


def example_1_progress_tracking():
    """Example: Track progress across teams."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Progress Tracking")
    print("=" * 80 + "\n")
    
    tracker = ProgressTracker(sprint_dir=script_dir.parent)
    
    # Show current progress
    print("Current Progress Dashboard:")
    print(tracker.generate_dashboard())
    
    # Check specific milestone
    print("\nChecking Hour 2 Milestones:")
    print(tracker.generate_milestone_report(2))
    
    # Export metrics
    metrics_file = script_dir / "example_metrics.json"
    metrics = tracker.export_metrics(metrics_file)
    print(f"\nMetrics exported to: {metrics_file}")
    print(f"Overall: {metrics['overall']['completed_tasks']}/{metrics['overall']['total_tasks']} tasks")
    
    # Clean up example file
    if metrics_file.exists():
        metrics_file.unlink()


def example_2_team_coordination():
    """Example: Coordinate team check-ins."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Team Coordination")
    print("=" * 80 + "\n")
    
    coordinator = TeamCoordinator(sprint_dir=script_dir.parent)
    
    # Generate stand-up prompt
    print("Stand-up Prompt for Team 1:")
    print(coordinator.generate_standup_prompt("team1_google_oauth"))
    
    # Record a status update
    print("\nRecording Team 1 Status Update...")
    status = {
        "completed": ["OAuth base class", "Unit tests"],
        "in_progress": ["Google OAuth flow"],
        "blocked": [],
        "next": ["Token exchange"],
        "milestone_complete": True
    }
    coordinator.record_status("team1_google_oauth", status)
    print("✅ Status recorded")
    
    # Check dependencies
    print("\nChecking if Team 2 can proceed (Hour 2):")
    deps = coordinator.check_dependencies("team2_microsoft_oauth", 2)
    if deps["ready"]:
        print("✅ Team 2 is ready to proceed")
    else:
        print("⏸️  Team 2 is waiting on:")
        for blocking in deps["blocking_teams"]:
            print(f"   - {blocking['name']}")
    
    # Generate coordination report
    print("\nHour 2 Coordination Report:")
    print(coordinator.generate_coordination_report(2))


def example_3_blocker_management():
    """Example: Manage blockers."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Blocker Management")
    print("=" * 80 + "\n")
    
    manager = BlockerManager(sprint_dir=script_dir.parent)
    
    # Create a blocker
    print("Creating a test blocker...")
    blocker = manager.create_blocker(
        team="team3_api_clients",
        description="openapi-generator installation failing on Windows",
        severity="P1",
        impact="Cannot generate API clients, blocks testing",
        affected_teams=["team3_api_clients", "team4_testing"],
        reported_by="API Team Lead"
    )
    print(f"✅ Blocker created: {blocker.id}")
    
    # Add an update
    print("\nAdding update to blocker...")
    manager.update_blocker(
        blocker.id,
        "Trying Docker-based approach as workaround",
        updated_by="DevOps Engineer"
    )
    print("✅ Update added")
    
    # Assign the blocker
    print("\nAssigning blocker...")
    manager.assign_blocker(blocker.id, "DevOps Engineer")
    print("✅ Blocker assigned")
    
    # Show blocker details
    print("\nBlocker Details:")
    print(manager.generate_blocker_details(blocker.id))
    
    # List all blockers
    print("\nAll Blockers:")
    print(manager.generate_report())
    
    # Resolve the blocker
    print("\nResolving blocker...")
    manager.resolve_blocker(
        blocker.id,
        "Switched to Docker image, generator now working",
        resolved_by="DevOps Engineer"
    )
    print("✅ Blocker resolved")
    
    # Show final status
    print("\nFinal Blocker Status:")
    print(manager.generate_report())
    
    # Clean up example blocker
    if blocker.id in manager.blockers:
        del manager.blockers[blocker.id]
        manager._save_blockers()


def example_4_integrated_workflow():
    """Example: Complete hourly checkpoint workflow."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Integrated Hourly Checkpoint Workflow")
    print("=" * 80 + "\n")
    
    print("Simulating Hour 4 Checkpoint...\n")
    
    # 1. Progress check
    tracker = ProgressTracker(sprint_dir=script_dir.parent)
    print("1. Checking Progress:")
    all_status = tracker.get_all_status()
    for team, status in all_status.items():
        stats = status["stats"]
        print(f"   {status['name']}: {stats['percentage']}% complete")
    
    # 2. Milestone validation
    print("\n2. Validating Milestones:")
    milestones = tracker.check_milestones(4)
    met = sum(1 for s in milestones.values() if s["met"])
    total = len(milestones)
    print(f"   {met}/{total} milestones met")
    
    # 3. Dependency check
    coordinator = TeamCoordinator(sprint_dir=script_dir.parent)
    print("\n3. Checking Dependencies:")
    for team in ["team4_testing"]:
        deps = coordinator.check_dependencies(team, 4)
        team_name = coordinator.teams[team]["name"]
        if deps["ready"]:
            print(f"   ✅ {team_name} ready to proceed")
        else:
            print(f"   ⏸️  {team_name} waiting on {len(deps['blocking_teams'])} teams")
    
    # 4. Blocker review
    manager = BlockerManager(sprint_dir=script_dir.parent)
    print("\n4. Reviewing Blockers:")
    open_blockers = manager.get_open_blockers()
    if open_blockers:
        print(f"   🚫 {len(open_blockers)} open blockers")
        critical = [b for b in open_blockers if b.severity == Severity.P0_CRITICAL]
        if critical:
            print(f"   ⚠️  {len(critical)} CRITICAL blockers")
    else:
        print("   ✅ No open blockers")
    
    # 5. Action items
    print("\n5. Action Items:")
    behind_teams = [
        team for team, status in milestones.items()
        if not status["met"]
    ]
    if behind_teams:
        print("   ⚠️  Teams need assistance:")
        for team in behind_teams[:3]:  # Show top 3
            print(f"      - {team.replace('_', ' ').title()}")
    else:
        print("   ✅ All teams on track")
    
    print("\n" + "=" * 80)


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("ORCHESTRATION TOOLS - EXAMPLE USAGE SCENARIOS")
    print("=" * 80)
    print("\nThis script demonstrates how to use the orchestration tools.")
    print("In production, you would use the CLI tools instead of Python imports.")
    
    try:
        example_1_progress_tracking()
        example_2_team_coordination()
        example_3_blocker_management()
        example_4_integrated_workflow()
        
        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error in examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
