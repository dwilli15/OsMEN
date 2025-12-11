#!/usr/bin/env python3
"""Test script for workspace scanner integration with infrastructure agent."""

import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.infrastructure.infrastructure_agent import InfrastructureAgent


def test_integration():
    """Test the complete workspace awareness integration."""
    print("=" * 60)
    print("WORKSPACE SCANNER INTEGRATION TEST")
    print("=" * 60)

    # Initialize Infrastructure Agent
    agent = InfrastructureAgent()

    print("\n=== Infrastructure Agent Status ===")
    status = agent.get_status()
    print(f"Nodes: {status['nodes']['total']}")
    print(f"Tools: {status['tools']['total']}")
    print(f"Agents: {status['agents']['total']}")
    print(f"Pipelines: {status['pipelines']['total']}")

    print("\n=== Workspace Map Status ===")
    if agent.workspace_map:
        summary = agent.get_workspace_summary()
        print(f"Total Files: {summary.get('total_files', 0)}")
        print(f"Total Dirs: {summary.get('total_dirs', 0)}")
        print(f"Total Agents: {summary.get('total_agents', 0)}")
        print(f"Total Capabilities: {summary.get('total_capabilities', 0)}")

        print("\n=== Top 10 Capabilities ===")
        caps = agent.get_workspace_capabilities()
        sorted_caps = sorted(caps.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        for cap, files in sorted_caps:
            print(f"  {cap}: {len(files)} files")

        print("\n=== Find Files by Capability ===")
        for cap_name in [
            "tts",
            "stt",
            "audiobook",
            "calendar_sync",
            "email",
            "image_generation",
            "social_media_management",
        ]:
            files = agent.find_files_by_capability(cap_name)
            print(f"  {cap_name}: {len(files)} files")

        print("\n=== Agent Instruction Files ===")
        instructions = agent.get_instruction_files()
        if instructions:
            for path, info in instructions.items():
                print(f"  {path}")
        else:
            print("  No instruction files found")

        print("\n=== Workspace Agents ===")
        ws_agents = agent.get_all_workspace_agents()
        print(f"  Found {len(ws_agents)} agents in workspace map")

        print("\n✅ Workspace map integration: WORKING")
    else:
        print("❌ Workspace map not loaded")
        print("   Run: python -m agents.workspace_scanner.workspace_scanner_agent")

    print("\n=== Pipeline Summary ===")
    pipeline_summary = agent.get_pipeline_summary()
    print(json.dumps(pipeline_summary, indent=2))

    print("\n=== Langflow Flows ===")
    langflow_flows = agent.get_langflow_flows()
    for flow in langflow_flows:
        print(f"  {flow.pipeline_id}: {flow.name}")

    print("\n=== n8n Workflows ===")
    n8n_workflows = agent.get_n8n_workflows()
    for wf in n8n_workflows:
        print(f"  {wf.pipeline_id}: {wf.name}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_integration()
    test_integration()
