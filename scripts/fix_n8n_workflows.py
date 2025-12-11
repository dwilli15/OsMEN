#!/usr/bin/env python3
"""
YOLO-OPS: n8n Workflow Creator
Creates n8n-compatible workflow JSONs and imports them via CLI
"""
import json
import uuid
from pathlib import Path

WORKFLOWS_DIR = Path("n8n/workflows")


def add_n8n_metadata(workflow_data):
    """Add required n8n metadata to workflow"""
    # Generate versionId if missing
    if "versionId" not in workflow_data:
        workflow_data["versionId"] = str(uuid.uuid4())

    # Ensure proper settings
    if "settings" not in workflow_data:
        workflow_data["settings"] = {}

    workflow_data["settings"]["executionOrder"] = "v1"

    # Add meta section
    if "meta" not in workflow_data:
        workflow_data["meta"] = {}
    workflow_data["meta"]["instanceId"] = "osmen-local"

    # Set active to false (can be activated later)
    workflow_data["active"] = False

    # Remove tags (they cause issues on import)
    if "tags" in workflow_data:
        del workflow_data["tags"]

    # Ensure nodes have IDs
    for i, node in enumerate(workflow_data.get("nodes", [])):
        if "id" not in node:
            node["id"] = str(uuid.uuid4())

    # Remove custom IDs that conflict
    if "id" in workflow_data:
        del workflow_data["id"]

    return workflow_data


def fix_workflow_files():
    """Fix all workflow files in the directory"""
    if not WORKFLOWS_DIR.exists():
        print(f"❌ Directory not found: {WORKFLOWS_DIR}")
        return

    fixed_dir = WORKFLOWS_DIR / "fixed"
    fixed_dir.mkdir(exist_ok=True)

    for wf_file in WORKFLOWS_DIR.glob("*.json"):
        try:
            with open(wf_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            fixed_data = add_n8n_metadata(data)

            output_file = fixed_dir / wf_file.name
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(fixed_data, f, indent=2)

            print(f"✅ Fixed: {wf_file.name}")
        except Exception as e:
            print(f"❌ Failed {wf_file.name}: {e}")


if __name__ == "__main__":
    print("🔥 YOLO-OPS: Fixing n8n workflow files")
    print("=" * 50)
    fix_workflow_files()
    print("\n✅ Fixed workflows saved to n8n/workflows/fixed/")
    print(
        "Import with: docker exec osmen-n8n n8n import:workflow --separate --input=/tmp/osmen-workflows-fixed/"
    )
