#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for bidirectional orchestration layer connections.

Usage:
    python scripts/test_bidirectional.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.orchestration import (
    Agents,
    ConnectionGraph,
    Pipelines,
    Templates,
    Trackers,
    Workflows,
)


def test_agent_to_resources():
    """Test Agent → Resources navigation"""
    print("\n" + "═" * 60)
    print("📌 AGENT → Resources (daily_brief)")
    print("═" * 60)

    # Get pipelines for agent
    pipelines = Agents.get_pipelines("daily_brief")
    print(f"\n  Pipelines ({len(pipelines)}):")
    for p in pipelines:
        print(f"    • {p.name}: {p.description[:50]}...")

    # Get workflows for agent
    workflows = Agents.get_workflows("daily_brief")
    print(f"\n  Workflows ({len(workflows)}):")
    for w in workflows:
        print(f"    • [{w.system}] {w.name}")

    # Get templates for agent
    templates = Agents.get_templates("daily_brief")
    print(f"\n  Templates ({len(templates)}):")
    for t in templates:
        print(f"    • {t.name}")


def test_pipeline_to_resources():
    """Test Pipeline → Resources navigation"""
    print("\n" + "═" * 60)
    print("📌 PIPELINE → Resources (daily_briefing)")
    print("═" * 60)

    # Get agents for pipeline
    agents = Pipelines.get_agents("daily_briefing")
    print(f"\n  Agents ({len(agents)}):")
    for a in agents:
        print(f"    • {a.name}: {a.description}")

    # Get workflows for pipeline
    workflows = Pipelines.get_workflows("daily_briefing")
    print(f"\n  Workflows ({len(workflows)}):")
    for w in workflows:
        print(f"    • [{w.system}] {w.name}")

    # Get templates for pipeline
    templates = Pipelines.get_templates("daily_briefing")
    print(f"\n  Templates ({len(templates)}):")
    for t in templates:
        print(f"    • {t.name}")

    # Get trackers for pipeline
    trackers = Pipelines.get_trackers("adhd_tracking")
    print(f"\n  Trackers for 'adhd_tracking' ({len(trackers)}):")
    for tr in trackers:
        print(f"    • {tr.name}: {tr.purpose}")


def test_workflow_to_resources():
    """Test Workflow → Resources navigation"""
    print("\n" + "═" * 60)
    print("📌 WORKFLOW → Resources (checkin_triggered_briefing)")
    print("═" * 60)

    # Get pipeline for workflow
    pipeline = Workflows.get_pipeline("checkin_triggered_briefing")
    if pipeline:
        print(f"\n  Pipeline: {pipeline.name}")
        print(f"    CLI: {pipeline.cli_command}")
        print(f"    Python: {pipeline.python_module}")

    # Get agents for workflow
    agents = Workflows.get_agents("checkin_triggered_briefing")
    print(f"\n  Agents ({len(agents)}):")
    for a in agents:
        print(f"    • {a.name}")


def test_template_to_resources():
    """Test Template → Resources navigation"""
    print("\n" + "═" * 60)
    print("📌 TEMPLATE → Resources")
    print("═" * 60)

    templates = ["AM Check-In", "PM Check-In", "Briefing Script"]
    for template_name in templates:
        pipeline = Templates.get_pipeline(template_name)
        full_path = Templates.get_full_path(template_name)
        agents = Templates.get_agents(template_name)

        print(f"\n  {template_name}:")
        print(f"    Pipeline: {pipeline.name if pipeline else 'None'}")
        print(f"    Agents: {[a.name for a in agents]}")
        print(f"    Path: {full_path}")


def test_connection_graph():
    """Test full ConnectionGraph traversal"""
    print("\n" + "═" * 60)
    print("📌 CONNECTION GRAPH - Full traversal from 'daily_brief'")
    print("═" * 60)

    graph = ConnectionGraph.for_agent("daily_brief")
    data = graph.to_dict()

    for category, items in data.items():
        if items:
            print(f"\n  {category.upper()} ({len(items)}):")
            for item in items[:5]:  # Limit display
                if hasattr(item, "name"):
                    print(f"    • {item.name}")
                else:
                    print(f"    • {item}")

    # Test from pipeline
    print("\n" + "-" * 60)
    print("📌 CONNECTION GRAPH - From 'am_checkin' pipeline")
    print("-" * 60)

    graph = ConnectionGraph.for_pipeline("am_checkin")
    print(f"  Agents: {[a.name for a in graph.agents]}")
    print(f"  Workflows: {[w.name for w in graph.workflows]}")
    print(f"  Templates: {[t.name for t in graph.templates]}")

    # Test from workflow
    print("\n" + "-" * 60)
    print("📌 CONNECTION GRAPH - From 'daily_brief_specialist' workflow")
    print("-" * 60)

    graph = ConnectionGraph.for_workflow("daily_brief_specialist")
    print(f"  Pipeline: {[p.name for p in graph.pipelines]}")
    print(f"  Agents: {[a.name for a in graph.agents]}")


def run_all_tests():
    """Run all bidirectional tests"""
    print("\n" + "=" * 60)
    print(" BIDIRECTIONAL ORCHESTRATION LAYER TESTS ".center(60))
    print("=" * 60)

    test_agent_to_resources()
    test_pipeline_to_resources()
    test_workflow_to_resources()
    test_template_to_resources()
    test_connection_graph()

    print("\n" + "=" * 60)
    print("All bidirectional traversal tests complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()
