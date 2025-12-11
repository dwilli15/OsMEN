#!/usr/bin/env python3
"""Test Obsidian integration and ChromaDB sync"""

import json
import sys

sys.path.insert(0, "D:/OsMEN")

from pathlib import Path

from agents.knowledge_management.obsidian_sync import ObsidianSync, SyncConfig
from tools.obsidian.obsidian_integration import ObsidianIntegration


def test_basic_integration():
    """Test basic Obsidian operations"""
    print("=" * 60)
    print("Testing Obsidian Integration")
    print("=" * 60)

    obs = ObsidianIntegration("D:/OsMEN/obsidian-vault")

    # List notes
    notes = obs.list_notes()
    print(f"\n📁 Found {len(notes)} notes in vault:")
    for note in notes:
        print(f"   - {note['path']}")

    # Search
    print("\n🔍 Searching for 'course'...")
    results = obs.search_notes("course")
    print(f"   Found {len(results)} matches")

    # Read a note
    if notes:
        print(f"\n📖 Reading: {notes[0]['path']}")
        content = obs.read_note(notes[0]["path"])
        if "error" not in content:
            print(f"   Title: {content['title']}")
            print(f"   Tags: {content.get('tags', [])}")
            print(f"   Links: {content.get('links', [])}")
            print(f"   Content preview: {content['content'][:100]}...")

    # Export graph
    print("\n📊 Knowledge Graph:")
    graph = obs.export_graph()
    print(f"   Nodes: {len(graph['nodes'])}")
    print(f"   Edges: {len(graph['edges'])}")

    return True


def test_chroma_sync():
    """Test ChromaDB sync"""
    print("\n" + "=" * 60)
    print("Testing ChromaDB Sync")
    print("=" * 60)

    config = SyncConfig(
        vault_path=Path("D:/OsMEN/obsidian-vault"),
        chroma_host="localhost",
        chroma_port=8000,
        collection_name="obsidian_vault",
    )

    sync = ObsidianSync(config)

    # Get stats
    print("\n📈 ChromaDB Stats:")
    stats = sync.get_stats()
    print(json.dumps(stats, indent=2))

    # Try sync
    if stats.get("status") == "connected":
        print("\n🔄 Syncing vault to ChromaDB...")
        result = sync.sync()
        print(json.dumps(result, indent=2))

        # Test search
        print("\n🔍 Semantic search for 'course schedule'...")
        results = sync.search("course schedule", limit=3)
        for r in results:
            print(
                f"   - {r['metadata'].get('title', 'Unknown')} (score: {1-r.get('distance', 0):.3f})"
            )
    else:
        print("   ⚠️ ChromaDB not connected")

    return True


def test_knowledge_agent():
    """Test knowledge agent"""
    print("\n" + "=" * 60)
    print("Testing Knowledge Agent")
    print("=" * 60)

    from agents.knowledge_management.knowledge_agent import KnowledgeAgent

    agent = KnowledgeAgent()

    # Get summary
    print("\n📊 Knowledge Base Summary:")
    summary = agent.generate_summary()
    print(f"   Total notes: {summary['total_notes']}")
    print(f"   Recent notes: {len(summary['recent_notes'])}")

    # Organize analysis
    print("\n🔗 Organization Analysis:")
    org = agent.organize_notes()
    print(f"   Total: {org['total_notes']}")
    print(f"   Linked: {org['linked_notes']}")
    print(f"   Orphans: {len(org['orphan_notes'])}")
    print(f"   Graph density: {org['graph_density']:.3f}")

    return True


if __name__ == "__main__":
    print("\n🦊 OsMEN Obsidian Integration Test Suite\n")

    test_basic_integration()
    test_chroma_sync()
    test_knowledge_agent()

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
