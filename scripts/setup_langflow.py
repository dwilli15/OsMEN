#!/usr/bin/env python3
"""
YOLO-OPS: Langflow Setup Script
Uploads all OsMEN flows to Langflow and configures them
"""
import json
import sys
from pathlib import Path

import requests

LANGFLOW_URL = "http://127.0.0.1:7860"
FLOWS_DIR = Path("langflow/flows")


def get_token():
    """Get auto-login token"""
    resp = requests.get(f"{LANGFLOW_URL}/api/v1/auto_login")
    if resp.status_code == 200:
        return resp.json().get("access_token")
    print(f"Failed to get token: {resp.text}")
    return None


def get_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def create_folder(token, name, description):
    """Create a folder in Langflow"""
    headers = get_headers(token)
    data = {"name": name, "description": description}
    resp = requests.post(f"{LANGFLOW_URL}/api/v1/folders/", headers=headers, json=data)
    if resp.status_code in [200, 201]:
        folder = resp.json()
        print(f"✅ Created folder: {folder.get('name')} (ID: {folder.get('id')})")
        return folder.get("id")
    print(f"❌ Failed to create folder: {resp.text}")
    return None


def list_folders(token):
    """List all folders"""
    headers = get_headers(token)
    resp = requests.get(f"{LANGFLOW_URL}/api/v1/folders/", headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return []


def upload_flow(token, flow_path, folder_id=None):
    """Upload a flow JSON file"""
    headers = get_headers(token)

    with open(flow_path, "r") as f:
        flow_data = json.load(f)

    # Set folder if provided
    if folder_id:
        flow_data["folder_id"] = folder_id

    resp = requests.post(
        f"{LANGFLOW_URL}/api/v1/flows/", headers=headers, json=flow_data
    )
    if resp.status_code in [200, 201]:
        result = resp.json()
        print(f"✅ Uploaded: {flow_path.name} -> {result.get('name', 'unknown')}")
        return True
    else:
        print(
            f"❌ Failed to upload {flow_path.name}: {resp.status_code} - {resp.text[:200]}"
        )
        return False


def list_flows(token):
    """List all flows"""
    headers = get_headers(token)
    resp = requests.get(f"{LANGFLOW_URL}/api/v1/flows/", headers=headers)
    if resp.status_code == 200:
        flows = resp.json()
        print(f"\n📋 Current flows ({len(flows)} total):")
        for flow in flows:
            print(
                f"  - {flow.get('name')}: {flow.get('description', 'No description')[:50]}"
            )
        return flows
    return []


def main():
    print("🔥 YOLO-OPS: Langflow Setup")
    print("=" * 50)

    # Get token
    token = get_token()
    if not token:
        print("❌ Failed to authenticate with Langflow")
        sys.exit(1)
    print(f"✅ Authenticated with Langflow")

    # List existing folders
    folders = list_folders(token)
    print(f"\n📁 Existing folders: {len(folders)}")
    for f in folders if isinstance(folders, list) else [folders]:
        print(f"  - {f.get('name')}: {f.get('id')}")

    # Create OsMEN folder
    folder_id = create_folder(
        token,
        "OsMEN Agents",
        "OsMEN Agent Flows - Boot Hardening, Daily Brief, Focus, Knowledge Management, YOLO-OPS",
    )

    # List existing flows
    existing_flows = list_flows(token)
    existing_names = {f.get("name") for f in existing_flows}

    # Upload OsMEN flows
    print("\n📤 Uploading OsMEN flows...")
    if FLOWS_DIR.exists():
        for flow_file in FLOWS_DIR.glob("*.json"):
            # Read flow to check name
            with open(flow_file, "r") as f:
                try:
                    flow_data = json.load(f)
                    flow_name = flow_data.get("name", flow_file.stem)
                    if flow_name in existing_names:
                        print(f"⏭️  Skipping {flow_file.name} (already exists)")
                        continue
                except:
                    pass
            upload_flow(token, flow_file, folder_id)
    else:
        print(f"❌ Flows directory not found: {FLOWS_DIR}")

    # Final summary
    print("\n" + "=" * 50)
    print("🎉 Langflow setup complete!")
    list_flows(token)


if __name__ == "__main__":
    main()
    main()
    main()
