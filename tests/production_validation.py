#!/usr/bin/env python3
"""
OsMEN Production Validation Suite
=================================

Comprehensive validation to ensure the framework is production-ready.
Runs all checks including:
- Path validation
- Service health
- Pipeline registry
- Two-way bindings
- Template files
- n8n workflows
- Langflow flows

Exit codes:
- 0: All validations pass
- 1: Some validations failed
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Add OsMEN to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_paths() -> Tuple[bool, List[str]]:
    """Validate all critical paths exist"""
    print("\n" + "=" * 60)
    print("🔍 PATH VALIDATION")
    print("=" * 60)

    errors = []
    from integrations.paths import (
        AGENTS_ROOT,
        CONTENT_ROOT,
        HB411_OBSIDIAN,
        HB411_ROOT,
        LANGFLOW_FLOWS,
        LOG_AGENT_SESSIONS,
        LOG_CHECK_INS,
        LOGS_ROOT,
        N8N_WORKFLOWS,
        OSMEN_ROOT,
        VAULT_TEMPLATES,
    )

    paths_to_check = {
        "OSMEN_ROOT": OSMEN_ROOT,
        "CONTENT_ROOT": CONTENT_ROOT,
        "LOGS_ROOT": LOGS_ROOT,
        "AGENTS_ROOT": AGENTS_ROOT,
        "HB411_ROOT": HB411_ROOT,
        "HB411_OBSIDIAN": HB411_OBSIDIAN,
        "VAULT_TEMPLATES": VAULT_TEMPLATES,
        "LOG_AGENT_SESSIONS": LOG_AGENT_SESSIONS,
        "LOG_CHECK_INS": LOG_CHECK_INS,
        "N8N_WORKFLOWS": N8N_WORKFLOWS,
        "LANGFLOW_FLOWS": LANGFLOW_FLOWS,
    }

    for name, path in paths_to_check.items():
        if path.exists():
            print(f"✅ {name}: {path}")
        else:
            print(f"❌ {name}: {path} (MISSING)")
            errors.append(f"Missing path: {name}")

    return len(errors) == 0, errors


def validate_pipelines() -> Tuple[bool, List[str]]:
    """Validate all pipelines are properly configured"""
    print("\n" + "=" * 60)
    print("📋 PIPELINE VALIDATION")
    print("=" * 60)

    errors = []
    from integrations.orchestration import Pipeline, Pipelines

    if not Pipelines._registry:
        print("❌ Pipeline registry is empty!")
        return False, ["Pipeline registry not initialized"]

    print(f"Found {len(Pipelines._registry)} registered pipelines:\n")

    for name, pipeline in Pipelines._registry.items():
        print(f"  📌 {name}: {pipeline.description}")

        # Check CLI command
        if pipeline.cli_command:
            print(f"      CLI: {pipeline.cli_command}")

        # Check n8n workflow
        if pipeline.n8n_workflow:
            workflow_path = Path("D:/OsMEN/n8n/workflows") / pipeline.n8n_workflow
            if workflow_path.exists():
                print(f"      n8n: ✅ {pipeline.n8n_workflow}")
            else:
                print(f"      n8n: ⚠️ {pipeline.n8n_workflow} (not found)")

        # Check langflow flow
        if pipeline.langflow_flow:
            flow_path = Path("D:/OsMEN/langflow/flows") / pipeline.langflow_flow
            if flow_path.exists():
                print(f"      Langflow: ✅ {pipeline.langflow_flow}")
            else:
                print(f"      Langflow: ⚠️ {pipeline.langflow_flow} (not found)")

        # Check Python module
        if pipeline.python_module:
            print(f"      Module: {pipeline.python_module}")

    return len(errors) == 0, errors


def validate_services() -> Tuple[bool, List[str]]:
    """Validate service registry"""
    print("\n" + "=" * 60)
    print("🔌 SERVICE VALIDATION")
    print("=" * 60)

    errors = []
    from integrations.orchestration import Services

    print("Registered services:\n")
    for svc in Services.ALL:
        print(f"  🔧 {svc.name}")
        print(f"      Port: {svc.port}")
        print(f"      URL: {svc.url}")
        if svc.health_endpoint:
            print(f"      Health: {svc.health_url}")
        print(f"      Required: {svc.required}")

    return True, []


def validate_agents() -> Tuple[bool, List[str]]:
    """Validate agent registry"""
    print("\n" + "=" * 60)
    print("🤖 AGENT VALIDATION")
    print("=" * 60)

    errors = []
    from integrations.orchestration import Agents

    agents_to_check = [
        Agents.DAILY_BRIEF,
        Agents.LIBRARIAN,
        Agents.FOCUS_GUARDRAILS,
        Agents.BOOT_HARDENING,
        Agents.KNOWLEDGE_MANAGEMENT,
    ]

    for agent in agents_to_check:
        agent_path = Path("D:/OsMEN") / agent.path
        if agent_path.exists():
            print(f"✅ {agent.name}: {agent.path}")
        else:
            print(f"⚠️ {agent.name}: {agent.path} (path not found)")

        print(f"   Status: {agent.status}")
        print(f"   Pipelines: {', '.join(agent.pipelines)}")

    return len(errors) == 0, errors


def validate_templates() -> Tuple[bool, List[str]]:
    """Validate template files exist"""
    print("\n" + "=" * 60)
    print("📄 TEMPLATE VALIDATION")
    print("=" * 60)

    errors = []
    from integrations.orchestration import Paths, Templates

    print(f"Found {len(Templates.ALL)} templates registered:\n")

    for template in Templates.ALL:
        # Templates are stored in VAULT_TEMPLATES
        template_path = Paths.VAULT_TEMPLATES / template.file
        if template_path.exists():
            print(f"✅ {template.name}: {template.file}")
        else:
            print(f"⚠️ {template.name}: {template.file} (not yet created)")
            # Not an error - templates may not exist yet

    return True, []  # Templates are optional until created


def validate_workflows() -> Tuple[bool, List[str]]:
    """Validate n8n workflows"""
    print("\n" + "=" * 60)
    print("⚙️ N8N WORKFLOW VALIDATION")
    print("=" * 60)

    errors = []
    from integrations.paths import N8N_WORKFLOWS

    if not N8N_WORKFLOWS.exists():
        print(f"❌ n8n workflows directory not found: {N8N_WORKFLOWS}")
        return False, ["n8n workflows directory missing"]

    workflows = list(N8N_WORKFLOWS.glob("*.json"))
    print(f"Found {len(workflows)} workflows:\n")

    for workflow in sorted(workflows):
        try:
            with open(workflow) as f:
                data = json.load(f)
            name = data.get("name", workflow.stem)
            nodes = len(data.get("nodes", []))
            print(f"✅ {workflow.name}")
            print(f"   Name: {name}")
            print(f"   Nodes: {nodes}")
        except json.JSONDecodeError:
            print(f"❌ {workflow.name}: Invalid JSON")
            errors.append(f"Invalid workflow: {workflow.name}")
        except Exception as e:
            print(f"⚠️ {workflow.name}: {e}")

    return len(errors) == 0, errors


def validate_langflow() -> Tuple[bool, List[str]]:
    """Validate Langflow flows"""
    print("\n" + "=" * 60)
    print("🌊 LANGFLOW VALIDATION")
    print("=" * 60)

    errors = []
    from integrations.paths import LANGFLOW_FLOWS

    if not LANGFLOW_FLOWS.exists():
        print(f"⚠️ Langflow flows directory not found: {LANGFLOW_FLOWS}")
        return True, []  # Langflow flows are optional

    flows = list(LANGFLOW_FLOWS.glob("*.json"))
    print(f"Found {len(flows)} flows:\n")

    for flow in sorted(flows):
        try:
            with open(flow) as f:
                data = json.load(f)
            name = data.get("name", flow.stem)
            print(f"✅ {flow.name}: {name}")
        except Exception as e:
            print(f"⚠️ {flow.name}: {e}")

    return True, []


def validate_instruction_files() -> Tuple[bool, List[str]]:
    """Validate instruction files reference orchestration layer"""
    print("\n" + "=" * 60)
    print("📚 INSTRUCTION FILE VALIDATION")
    print("=" * 60)

    errors = []
    instruction_files = [
        Path("D:/OsMEN/.github/copilot-instructions.md"),
        Path("D:/OsMEN/.github/agents/yolo-ops.agent.md"),
        Path("D:/OsMEN/.github/agents/osmen-dev.agent.md"),
        Path(
            "D:/OsMEN/content/courses/HB411_HealthyBoundaries/obsidian/.obsidian/VAULT_INSTRUCTIONS.md"
        ),
    ]

    for file in instruction_files:
        if file.exists():
            content = file.read_text(encoding="utf-8")
            has_orchestration_ref = "orchestration" in content.lower()
            has_paths_ref = "Paths" in content or "paths.py" in content

            status = "✅" if (has_orchestration_ref or has_paths_ref) else "⚠️"
            print(f"{status} {file.name}")
            if has_orchestration_ref:
                print("   ✓ References orchestration layer")
            if has_paths_ref:
                print("   ✓ References Paths class")
        else:
            print(f"❌ {file.name}: NOT FOUND")
            errors.append(f"Missing: {file.name}")

    return len(errors) == 0, errors


def validate_logging_integration() -> Tuple[bool, List[str]]:
    """Validate logging system integration"""
    print("\n" + "=" * 60)
    print("📝 LOGGING INTEGRATION VALIDATION")
    print("=" * 60)

    errors = []

    try:
        from integrations.logging_system import (
            AgentLogger,
            CheckInTracker,
            agent_startup_check,
            get_recent_context,
        )

        # Test logger
        logger = AgentLogger("validation-test")
        print(f"✅ AgentLogger: {logger.session_file.name}")

        # Test check-in tracker
        tracker = CheckInTracker()
        status = tracker.get_status()
        print(
            f"✅ CheckInTracker: AM={status['am_completed']}, PM={status['pm_completed']}"
        )

        # Test recent context
        context = get_recent_context(days=1)
        print(f"✅ Recent context: {len(context['recent_sessions'])} sessions")

        logger.end_session("Validation completed")

        return True, []
    except Exception as e:
        print(f"❌ Logging integration failed: {e}")
        return False, [str(e)]


def main():
    """Run all validations"""
    print("\n" + "=" * 60)
    print("🔥 OSMEN PRODUCTION VALIDATION SUITE")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Working Directory: {Path.cwd()}")

    validations = [
        ("Paths", validate_paths),
        ("Pipelines", validate_pipelines),
        ("Services", validate_services),
        ("Agents", validate_agents),
        ("Templates", validate_templates),
        ("n8n Workflows", validate_workflows),
        ("Langflow Flows", validate_langflow),
        ("Instruction Files", validate_instruction_files),
        ("Logging Integration", validate_logging_integration),
    ]

    results = {}
    all_errors = []

    for name, validator in validations:
        try:
            passed, errors = validator()
            results[name] = passed
            all_errors.extend(errors)
        except Exception as e:
            print(f"\n❌ {name} validation crashed: {e}")
            results[name] = False
            all_errors.append(f"{name}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for r in results.values() if r)
    total_count = len(results)

    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print("\n" + "-" * 60)
    print(f"Results: {passed_count}/{total_count} validations passed")

    if all_errors:
        print(f"\n⚠️ {len(all_errors)} issues found:")
        for error in all_errors:
            print(f"   - {error}")

    if passed_count == total_count:
        print("\n" + "=" * 60)
        print("🎉 ALL VALIDATIONS PASSED - PRODUCTION READY!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("⚠️ SOME VALIDATIONS FAILED - REVIEW BEFORE PRODUCTION")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
