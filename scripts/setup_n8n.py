#!/usr/bin/env python3
"""
YOLO-OPS: n8n Setup Script
Uploads all OsMEN workflows to n8n and configures them
"""
import json
import sys
import time
from pathlib import Path

import requests

N8N_URL = "http://127.0.0.1:5678"
WORKFLOWS_DIR = Path("n8n/workflows")

# Credentials
N8N_EMAIL = "armadeus03@hotmail.com"
N8N_PASSWORD = "Dw8533Dw"


def get_session():
    """Get authenticated session"""
    session = requests.Session()

    # Try to login
    login_url = f"{N8N_URL}/rest/login"
    login_data = {"emailOrLdapLoginId": N8N_EMAIL, "password": N8N_PASSWORD}

    resp = session.post(login_url, json=login_data)
    if resp.status_code == 200:
        print(f"✅ Logged in to n8n as {N8N_EMAIL}")
        return session

    # Maybe it's first-time setup
    print(f"Login failed ({resp.status_code}): {resp.text[:200]}")
    return None


def list_workflows(session):
    """List all workflows"""
    resp = session.get(f"{N8N_URL}/rest/workflows")
    if resp.status_code == 200:
        data = resp.json()
        workflows = data.get("data", [])
        print(f"\n📋 Current workflows ({len(workflows)} total):")
        for wf in workflows:
            status = "🟢" if wf.get("active") else "⚪"
            print(f"  {status} {wf.get('name')}")
        return workflows
    print(f"Failed to list workflows: {resp.text[:200]}")
    return []


def import_workflow(session, workflow_path):
    """Import a workflow from JSON file"""
    with open(workflow_path, "r") as f:
        workflow_data = json.load(f)

    workflow_name = workflow_data.get("name", workflow_path.stem)

    # Create workflow
    resp = session.post(f"{N8N_URL}/rest/workflows", json=workflow_data)

    if resp.status_code in [200, 201]:
        result = resp.json()
        wf = result.get("data", {})
        print(f"✅ Imported: {workflow_path.name} -> {wf.get('name', workflow_name)}")
        return wf.get("id")
    else:
        print(
            f"❌ Failed to import {workflow_path.name}: {resp.status_code} - {resp.text[:200]}"
        )
        return None


def activate_workflow(session, workflow_id, name):
    """Activate a workflow"""
    resp = session.patch(
        f"{N8N_URL}/rest/workflows/{workflow_id}", json={"active": True}
    )
    if resp.status_code == 200:
        print(f"  🟢 Activated: {name}")
        return True
    else:
        print(f"  ⚠️ Could not activate {name}: {resp.text[:100]}")
        return False


def check_settings(session):
    """Check n8n settings"""
    resp = session.get(f"{N8N_URL}/rest/settings")
    if resp.status_code == 200:
        settings = resp.json()
        data = settings.get("data", {})
        print(f"\n⚙️ n8n Settings:")
        print(f"   Version: {data.get('versionCli', 'unknown')}")
        print(f"   Instance ID: {data.get('instanceId', 'unknown')[:20]}...")
        return data
    return None


def main():
    print("🔥 YOLO-OPS: n8n Setup")
    print("=" * 50)

    # Get authenticated session
    session = get_session()
    if not session:
        print("\n❌ Could not authenticate with n8n")
        print("Please log in to n8n at http://localhost:5678 first")
        print("Then re-run this script")
        sys.exit(1)

    # Check settings
    check_settings(session)

    # List existing workflows
    existing_workflows = list_workflows(session)
    existing_names = {wf.get("name") for wf in existing_workflows}

    # Import OsMEN workflows
    print("\n📤 Importing OsMEN workflows...")
    imported_ids = []

    if WORKFLOWS_DIR.exists():
        for workflow_file in WORKFLOWS_DIR.glob("*.json"):
            # Read workflow to check name
            with open(workflow_file, "r") as f:
                try:
                    workflow_data = json.load(f)
                    workflow_name = workflow_data.get("name", workflow_file.stem)
                    if workflow_name in existing_names:
                        print(f"⏭️  Skipping {workflow_file.name} (already exists)")
                        continue
                except Exception as e:
                    print(f"⚠️ Could not parse {workflow_file.name}: {e}")
                    continue

            wf_id = import_workflow(session, workflow_file)
            if wf_id:
                imported_ids.append((wf_id, workflow_name))
    else:
        print(f"❌ Workflows directory not found: {WORKFLOWS_DIR}")

    # Activate imported workflows
    if imported_ids:
        print("\n⚡ Activating workflows...")
        for wf_id, wf_name in imported_ids:
            # Only activate trigger workflows
            if "trigger" in wf_name.lower() or "webhook" in wf_name.lower():
                activate_workflow(session, wf_id, wf_name)

    # Final summary
    print("\n" + "=" * 50)
    print("🎉 n8n setup complete!")
    list_workflows(session)


if __name__ == "__main__":
    main()
