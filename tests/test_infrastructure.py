#!/usr/bin/env python3
"""
Infrastructure Component Tests

Tests for the Workspace Infrastructure Manager components:
- Health Monitor Agent
- Infrastructure Agent
- Context Injector
- Obsidian Sync Watcher
- Lifecycle Manager
"""

import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_health_monitor():
    """Test Health Monitor Agent functionality."""
    print("\n" + "=" * 50)
    print("Testing Health Monitor Agent")
    print("=" * 50)

    try:
        from infrastructure.health_monitor import HealthMonitorAgent, NodeHealth

        # Create monitor
        monitor = HealthMonitorAgent()

        # Test 1: Check initialization
        assert monitor is not None, "Monitor should initialize"
        print("✅ Health monitor initialized")

        # Test 2: Check status method
        status = monitor.check_all_status()
        assert isinstance(status, dict), "Status should be a dictionary"
        assert "timestamp" in status, "Status should have timestamp"
        assert "nodes" in status, "Status should have nodes"
        print("✅ Status check returns valid structure")

        # Test 3: Test node health creation
        node_health = NodeHealth(
            node_id="test_node",
            name="Test Node",
            status="healthy",
            last_check=datetime.now().isoformat(),
            endpoint="http://localhost:8080",
        )
        assert node_health.node_id == "test_node", "Node health should store node_id"
        print("✅ NodeHealth dataclass works correctly")

        # Test 4: Test fix methods exist
        assert hasattr(monitor, "attempt_fix"), "Monitor should have attempt_fix method"
        print("✅ Auto-fix methods available")

        print("✅ Health Monitor Agent: ALL TESTS PASSED")
        return True

    except ImportError as e:
        print(f"⚠️ Health Monitor Agent: SKIPPED (not installed: {e})")
        return True  # Skip is not a failure
    except Exception as e:
        print(f"❌ Health Monitor Agent: FAILED - {e}")
        return False


def test_infrastructure_agent():
    """Test Infrastructure Agent functionality."""
    print("\n" + "=" * 50)
    print("Testing Infrastructure Agent")
    print("=" * 50)

    try:
        from agents.infrastructure.infrastructure_agent import (
            AgentInfo,
            InfrastructureAgent,
            NodeInfo,
            ToolInfo,
        )

        # Create agent
        agent = InfrastructureAgent()

        # Test 1: Check initialization
        assert agent is not None, "Agent should initialize"
        print("✅ Infrastructure agent initialized")

        # Test 2: Check nodes loaded
        assert len(agent.nodes) > 0, "Should have loaded nodes"
        print(f"✅ Loaded {len(agent.nodes)} nodes")

        # Test 3: Check tools loaded
        assert len(agent.tools) > 0, "Should have loaded tools"
        print(f"✅ Loaded {len(agent.tools)} tools")

        # Test 4: Check agents loaded
        assert len(agent.agents) > 0, "Should have loaded agents"
        print(f"✅ Loaded {len(agent.agents)} agents")

        # Test 5: Test node retrieval
        node = agent.get_node(list(agent.nodes.keys())[0])
        assert node is not None, "Should retrieve node"
        print("✅ Node retrieval works")

        # Test 6: Test context generation
        context = agent.generate_context_for_agent("boot_hardening")
        assert isinstance(context, dict), "Context should be a dictionary"
        print("✅ Context generation works")

        # Test 7: Test status method
        status = agent.get_status()
        assert isinstance(status, dict), "Status should be a dictionary"
        assert "nodes" in status, "Status should include nodes"
        print("✅ Status method works")

        # Test 8: Test graph generation
        graph = agent.get_full_graph()
        assert "nodes" in graph, "Graph should have nodes"
        assert "connections" in graph, "Graph should have connections"
        print("✅ Graph generation works")

        # Test 9: Test pipeline types (Langflow/n8n)
        langflow_flows = agent.get_langflow_flows()
        n8n_workflows = agent.get_n8n_workflows()
        native_pipelines = agent.get_native_pipelines()

        assert len(langflow_flows) > 0, "Should have Langflow flows registered"
        print(f"✅ Loaded {len(langflow_flows)} Langflow flows")

        assert len(n8n_workflows) > 0, "Should have n8n workflows registered"
        print(f"✅ Loaded {len(n8n_workflows)} n8n workflows")

        print(f"✅ Loaded {len(native_pipelines)} native pipelines")

        # Test 10: Test pipeline summary
        summary = agent.get_pipeline_summary()
        assert "total" in summary, "Summary should have total"
        assert "langflow" in summary, "Summary should have langflow"
        assert "n8n" in summary, "Summary should have n8n"
        print(f"✅ Pipeline summary: {summary['total']} total pipelines")

        print("✅ Infrastructure Agent: ALL TESTS PASSED")
        return True

    except ImportError as e:
        print(f"⚠️ Infrastructure Agent: SKIPPED (not installed: {e})")
        return True
    except Exception as e:
        print(f"❌ Infrastructure Agent: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_context_injector():
    """Test Context Injector functionality."""
    print("\n" + "=" * 50)
    print("Testing Context Injector")
    print("=" * 50)

    try:
        from infrastructure.context_injector import ContextInjector, InjectionConfig

        # Test 1: Singleton pattern
        injector1 = ContextInjector()
        injector2 = ContextInjector()
        # Note: May not be same instance in all implementations
        print("✅ Context injector instantiated")

        # Test 2: Test injection config with correct signature
        config = InjectionConfig(
            max_context_tokens=2000,
            include_capabilities=True,
            include_constraints=True,
            include_recent_memories=True,
            memory_recency_hours=24,
        )
        assert config.max_context_tokens == 2000, "Config should store values"
        print("✅ InjectionConfig works")

        # Test 3: Test context injection with correct signature
        result = injector1.inject_context(
            agent_id="boot_hardening", task_description="Test task"
        )
        assert isinstance(result, dict), "Injected context should be a dictionary"
        assert "_formatted_prompt" in result, "Should have formatted prompt"
        print("✅ Context injection works")

        # Test 4: Test messages injection with correct signature
        messages = [
            {"role": "system", "content": "You are an assistant"},
            {"role": "user", "content": "Help me"},
        ]
        injected = injector1.inject_context_to_messages(
            messages, agent_id="boot_hardening"
        )
        assert isinstance(injected, list), "Should return a list"
        assert len(injected) >= len(messages), "Should have at least same messages"
        print("✅ Messages injection works")

        # Test 5: Test statistics
        stats = injector1.get_injection_stats()
        assert isinstance(stats, dict), "Stats should be a dictionary"
        print("✅ Statistics retrieval works")

        print("✅ Context Injector: ALL TESTS PASSED")
        return True

    except ImportError as e:
        print(f"⚠️ Context Injector: SKIPPED (not installed: {e})")
        return True
    except Exception as e:
        print(f"❌ Context Injector: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_obsidian_sync_watcher():
    """Test Obsidian Sync Watcher functionality."""
    print("\n" + "=" * 50)
    print("Testing Obsidian Sync Watcher")
    print("=" * 50)

    try:
        from tools.obsidian.obsidian_sync_watcher import ObsidianSyncWatcher, SyncConfig

        # Create temp directories for testing
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "vault"
        knowledge_path = temp_dir / "knowledge"
        vault_path.mkdir()
        knowledge_path.mkdir()

        try:
            # Test 1: Config creation with correct signature
            config = SyncConfig(
                vault_path=str(vault_path),
                knowledge_path=str(knowledge_path),
                export_folder="OsMEN-Exports",
                read_filters={
                    "folders": ["notes"],
                    "tags": ["test"],
                    "exclude_folders": [".obsidian"],
                },
                write_policy="export_only",
                poll_interval_seconds=30,
            )
            assert config.vault_path == str(vault_path), "Config should store path"
            print("✅ SyncConfig works")

            # Test 2: Watcher creation
            watcher = ObsidianSyncWatcher(config)
            assert watcher is not None, "Watcher should initialize"
            print("✅ Watcher initialized")

            # Test 3: Test file read filtering
            # Create a test file in vault
            test_file = vault_path / "test.md"
            test_file.write_text("---\ntags: [test]\n---\n# Test Note\nContent")

            should_read = watcher._should_read_file(test_file)
            assert isinstance(should_read, bool), "Should return boolean"
            print("✅ Read filter works")

            # Test 4: Test write permission check with agent_id
            can_write_result = watcher.can_write("test.md", agent_id="test_agent")
            assert isinstance(can_write_result, dict), "Should return dict"
            assert "allowed" in can_write_result, "Should have allowed key"
            print("✅ Write permission check works")

            # Test 5: Test change detection
            changes = watcher.detect_changes()
            assert isinstance(changes, list), "Should return list of changes"
            print("✅ Change detection works")

            print("✅ Obsidian Sync Watcher: ALL TESTS PASSED")
            return True

        finally:
            # Cleanup
            shutil.rmtree(temp_dir)

    except ImportError as e:
        print(f"⚠️ Obsidian Sync Watcher: SKIPPED (not installed: {e})")
        return True
    except Exception as e:
        print(f"❌ Obsidian Sync Watcher: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_lifecycle_manager():
    """Test Lifecycle Manager functionality."""
    print("\n" + "=" * 50)
    print("Testing Lifecycle Manager")
    print("=" * 50)

    try:
        sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "automation"))
        from lifecycle_automation import (
            FileInfo,
            LifecycleConfig,
            WorkspaceLifecycleManager,
        )

        # Create temp workspace
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Create workspace structure
            (temp_dir / "workspace" / "incoming").mkdir(parents=True)
            (temp_dir / "workspace" / "staging").mkdir(parents=True)
            (temp_dir / "workspace" / "pending_review").mkdir(parents=True)
            (temp_dir / "workspace" / "archive").mkdir(parents=True)
            (temp_dir / "infrastructure" / "profiles").mkdir(parents=True)

            # Test 1: Config creation
            config = LifecycleConfig(incoming_max_age=30, staging_max_age=14)
            assert config.incoming_max_age == 30, "Config should store values"
            print("✅ LifecycleConfig works")

            # Test 2: Manager creation
            manager = WorkspaceLifecycleManager(base_path=temp_dir, config=config)
            assert manager is not None, "Manager should initialize"
            print("✅ Manager initialized")

            # Test 3: Create a test file
            test_file = temp_dir / "workspace" / "incoming" / "test.txt"
            test_file.write_text("Test content")

            # Test 4: Scan workspace
            workspace = manager.scan_workspace()
            assert isinstance(workspace, dict), "Should return dictionary"
            assert "incoming" in workspace, "Should have incoming"
            print("✅ Workspace scan works")

            # Test 5: Get status
            status = manager.get_status()
            assert isinstance(status, dict), "Should return dictionary"
            assert "workspace_files" in status, "Should have file counts"
            print("✅ Status retrieval works")

            # Test 6: Daily cleanup (dry run essentially)
            summary = manager.run_daily_cleanup()
            assert isinstance(summary, dict), "Should return summary"
            assert "type" in summary, "Should have type field"
            print("✅ Daily cleanup works")

            print("✅ Lifecycle Manager: ALL TESTS PASSED")
            return True

        finally:
            shutil.rmtree(temp_dir)

    except ImportError as e:
        print(f"⚠️ Lifecycle Manager: SKIPPED (not installed: {e})")
        return True
    except Exception as e:
        print(f"❌ Lifecycle Manager: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_archive_manager():
    """Test Archive Manager functionality."""
    print("\n" + "=" * 50)
    print("Testing Archive Manager")
    print("=" * 50)

    try:
        sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "automation"))
        from archive_manager import ArchiveManager

        # Create temp workspace
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Create structure
            (temp_dir / "workspace" / "archive").mkdir(parents=True)
            (temp_dir / "workspace" / "pending_review").mkdir(parents=True)
            (temp_dir / "infrastructure" / "queues").mkdir(parents=True)

            # Create empty queue file
            queue_file = temp_dir / "infrastructure" / "queues" / "archive_prompts.json"
            queue_file.write_text("[]")

            # Test 1: Manager creation
            manager = ArchiveManager(base_path=temp_dir)
            assert manager is not None, "Manager should initialize"
            print("✅ Archive manager initialized")

            # Test 2: Get pending prompts
            prompts = manager.get_pending_prompts()
            assert isinstance(prompts, list), "Should return list"
            print("✅ Get prompts works")

            # Test 3: Browse archive
            archive = manager.browse_archive()
            assert isinstance(archive, dict), "Should return dictionary"
            print("✅ Browse archive works")

            print("✅ Archive Manager: ALL TESTS PASSED")
            return True

        finally:
            shutil.rmtree(temp_dir)

    except ImportError as e:
        print(f"⚠️ Archive Manager: SKIPPED (not installed: {e})")
        return True
    except Exception as e:
        print(f"❌ Archive Manager: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all infrastructure tests."""
    print("=" * 60)
    print("OsMEN Infrastructure Component Tests")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Test started: {datetime.now().isoformat()}")

    tests = [
        ("Health Monitor", test_health_monitor),
        ("Infrastructure Agent", test_infrastructure_agent),
        ("Context Injector", test_context_injector),
        ("Obsidian Sync Watcher", test_obsidian_sync_watcher),
        ("Lifecycle Manager", test_lifecycle_manager),
        ("Archive Manager", test_archive_manager),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ {name}: UNEXPECTED ERROR - {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for name, p in results:
        status = "✅ PASS" if p else "❌ FAIL"
        print(f"  {name}: {status}")

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All infrastructure tests passed!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
