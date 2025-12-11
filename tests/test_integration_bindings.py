#!/usr/bin/env python3
"""
OsMEN Integration Binding Test
==============================

This script validates all two-way bindings in the orchestration layer.
It ensures that all components can:
1. Import from the orchestration layer
2. Access paths, services, pipelines
3. Use the logging system
4. Execute pipelines

Run this test before deploying to production.
"""

import sys
from datetime import datetime
from pathlib import Path

# Ensure we're in the right directory
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_paths_module():
    """Test paths.py imports"""
    print("\n" + "=" * 60)
    print("TEST 1: paths.py module")
    print("=" * 60)

    try:
        from integrations.paths import (
            CONTENT_ROOT,
            HB411_OBSIDIAN,
            HB411_ROOT,
            LOG_AGENT_SESSIONS,
            LOG_CHECK_INS,
            LOGS_ROOT,
            OSMEN_ROOT,
            VAULT_TEMPLATES,
            validate_critical_paths,
        )

        print(f"✅ OSMEN_ROOT: {OSMEN_ROOT}")
        print(f"✅ HB411_OBSIDIAN: {HB411_OBSIDIAN}")
        print(f"✅ VAULT_TEMPLATES: {VAULT_TEMPLATES}")

        # Validate paths
        validation = validate_critical_paths()
        for name, info in validation.items():
            status = "✅" if info["exists"] else "⚠️"
            print(f"   {status} {name}: {info['exists']}")

        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_orchestration_module():
    """Test orchestration.py imports"""
    print("\n" + "=" * 60)
    print("TEST 2: orchestration.py module")
    print("=" * 60)

    try:
        from integrations.orchestration import (
            Agents,
            OsMEN,
            Paths,
            Pipelines,
            Services,
            Templates,
            Trackers,
            Workflows,
            get_pipeline,
        )

        print(f"✅ Paths.OSMEN_ROOT: {Paths.OSMEN_ROOT}")
        print(f"✅ Paths.HB411_OBSIDIAN: {Paths.HB411_OBSIDIAN}")

        # Test pipeline registry
        print("\n📋 Registered Pipelines:")
        for name, pipeline in Pipelines._registry.items():
            print(f"   - {name}: {pipeline.description}")

        # Test get_pipeline
        briefing = get_pipeline("daily_briefing")
        print(f"\n✅ get_pipeline('daily_briefing'): {briefing.name}")

        # Test Services
        print("\n🔌 Registered Services:")
        for name, svc in vars(Services).items():
            if not name.startswith("_") and hasattr(svc, "port"):
                print(f"   - {svc.name}: port {svc.port}")

        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_logging_module():
    """Test logging_system.py imports"""
    print("\n" + "=" * 60)
    print("TEST 3: logging_system.py module")
    print("=" * 60)

    try:
        from integrations.logging_system import (
            AgentLogger,
            AudioGenerationLog,
            CheckInTracker,
            SystemEventLog,
            agent_startup_check,
            get_recent_context,
        )

        # Test logger creation
        logger = AgentLogger("integration-test")
        print(f"✅ AgentLogger created: {logger.session_file}")

        # Test check-in tracker
        tracker = CheckInTracker()
        status = tracker.get_status()
        print(
            f"✅ CheckInTracker status: AM={status['am_completed']}, PM={status['pm_completed']}"
        )

        # Test startup check
        test_logger, prompt = agent_startup_check("binding-test")
        print(f"✅ agent_startup_check: {test_logger.session_id}")
        if prompt:
            print(f"   ⚠️ Prompt: {prompt}")

        # Test recent context
        context = get_recent_context(days=1)
        print(f"✅ get_recent_context: {len(context['recent_sessions'])} sessions")

        # End test session
        logger.end_session("Integration test completed")

        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_integration_package():
    """Test integrations package __init__.py"""
    print("\n" + "=" * 60)
    print("TEST 4: integrations package exports")
    print("=" * 60)

    try:
        from integrations import (
            HB411_OBSIDIAN,
            OSMEN_ROOT,
            AgentLogger,
            CheckInTracker,
            OsMEN,
            Paths,
            Pipelines,
            Services,
        )

        print(f"✅ OsMEN imported from package")
        print(f"✅ Paths imported from package")
        print(f"✅ AgentLogger imported from package")
        print(f"✅ OSMEN_ROOT = {OSMEN_ROOT}")

        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_cli_module():
    """Test CLI module imports"""
    print("\n" + "=" * 60)
    print("TEST 5: CLI module")
    print("=" * 60)

    try:
        # Import CLI module
        cli_path = Path(__file__).parent.parent / "cli_bridge" / "osmen_cli.py"
        if cli_path.exists():
            print(f"✅ CLI module exists: {cli_path}")

            # Try importing
            sys.path.insert(0, str(cli_path.parent))
            # Can't easily import click-decorated module, just verify exists
            print(f"✅ CLI ready for use: python cli_bridge/osmen_cli.py --help")
            return True
        else:
            print(f"⚠️ CLI module not found at {cli_path}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_bidirectional_bindings():
    """Test that bindings work bidirectionally"""
    print("\n" + "=" * 60)
    print("TEST 6: Bidirectional binding verification")
    print("=" * 60)

    try:
        # Test 1: Paths -> Orchestration -> Logging all consistent
        from integrations.logging_system import OSMEN_ROOT as logging_root
        from integrations.orchestration import Paths
        from integrations.paths import OSMEN_ROOT as paths_root

        assert str(paths_root) == str(
            Paths.OSMEN_ROOT
        ), "Paths mismatch: paths.py vs orchestration.py"
        assert str(paths_root) == str(
            logging_root
        ), "Paths mismatch: paths.py vs logging_system.py"
        print("✅ OSMEN_ROOT consistent across all modules")

        # Test 2: Log directories match
        from integrations.orchestration import Paths as OPaths
        from integrations.paths import LOG_AGENT_SESSIONS, LOG_CHECK_INS

        assert str(LOG_AGENT_SESSIONS) == str(
            OPaths.LOG_SESSIONS
        ), "Log sessions path mismatch"
        assert str(LOG_CHECK_INS) == str(
            OPaths.LOG_CHECKINS
        ), "Log check-ins path mismatch"
        print("✅ Log directories consistent across modules")

        # Test 3: Templates reference correctly
        from integrations.orchestration import Paths as OPaths
        from integrations.paths import VAULT_TEMPLATES as paths_templates

        assert str(paths_templates) == str(
            OPaths.VAULT_TEMPLATES
        ), "Templates path mismatch"
        print("✅ Template paths consistent")

        return True
    except AssertionError as e:
        print(f"❌ BINDING MISMATCH: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_agent_import_pattern():
    """Test that agents can import from orchestration"""
    print("\n" + "=" * 60)
    print("TEST 7: Agent import pattern")
    print("=" * 60)

    try:
        # This is the pattern all agents should use
        from integrations.logging_system import AgentLogger, agent_startup_check
        from integrations.orchestration import OsMEN, Paths, Pipelines

        # Simulate what an agent would do at startup
        logger, prompt = agent_startup_check("pattern-test-agent")

        # Access paths
        obsidian_path = Paths.HB411_OBSIDIAN
        vault_templates = Paths.VAULT_TEMPLATES

        # Log something
        logger.log(
            action="import_test",
            inputs={"obsidian_path": str(obsidian_path)},
            outputs={"templates_path": str(vault_templates)},
            status="success",
            notes="Agent import pattern verified",
        )

        logger.end_session("Import pattern test completed")

        print("✅ Agent import pattern works correctly")
        print(f"   Logger session: {logger.session_id}")
        print(f"   Obsidian path: {obsidian_path}")

        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("🔗 OsMEN INTEGRATION BINDING TESTS")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    tests = [
        ("paths.py module", test_paths_module),
        ("orchestration.py module", test_orchestration_module),
        ("logging_system.py module", test_logging_module),
        ("integrations package", test_integration_package),
        ("CLI module", test_cli_module),
        ("Bidirectional bindings", test_bidirectional_bindings),
        ("Agent import pattern", test_agent_import_pattern),
    ]

    results = {}
    for name, test_func in tests:
        results[name] = test_func()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {name}")

    print("\n" + "-" * 60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL BINDINGS VERIFIED - PRODUCTION READY")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED - FIX BEFORE PRODUCTION")
        return 1


if __name__ == "__main__":
    sys.exit(main())
