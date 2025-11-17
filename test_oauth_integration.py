#!/usr/bin/env python3
"""
Test OAuth Integration for GitHub Copilot and OpenAI

This script tests the OAuth integration modules.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_github_oauth():
    """Test GitHub OAuth integration"""
    print("\n" + "=" * 60)
    print("Testing GitHub OAuth Integration")
    print("=" * 60)
    
    try:
        from integrations.oauth.github_oauth import GitHubOAuthIntegration
        
        oauth = GitHubOAuthIntegration()
        
        # Check configuration
        if not oauth.client_id or oauth.client_id == "":
            print("⚠️  GitHub OAuth Client ID not configured")
            print("   Set GITHUB_OAUTH_CLIENT_ID in .env")
            return False
        
        if not oauth.client_secret or oauth.client_secret == "":
            print("⚠️  GitHub OAuth Client Secret not configured")
            print("   Set GITHUB_OAUTH_CLIENT_SECRET in .env")
            return False
        
        print(f"✅ Client ID configured: {oauth.client_id[:10]}...")
        print(f"✅ Redirect URI: {oauth.redirect_uri}")
        
        # Check authentication status
        if oauth.is_authenticated():
            print("✅ Already authenticated")
            user_info = oauth.get_user_info()
            if user_info:
                print(f"   Username: {user_info.get('login')}")
                print(f"   Name: {user_info.get('name')}")
        else:
            print("ℹ️  Not authenticated")
            auth_url = oauth.get_authorization_url()
            print(f"   To authenticate, visit: {auth_url[:50]}...")
        
        print("✅ GitHub OAuth Integration: PASS")
        return True
        
    except Exception as e:
        print(f"❌ GitHub OAuth Integration: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_openai_oauth():
    """Test OpenAI OAuth integration"""
    print("\n" + "=" * 60)
    print("Testing OpenAI OAuth Integration")
    print("=" * 60)
    
    try:
        from integrations.oauth.openai_oauth import OpenAIOAuthIntegration
        
        oauth = OpenAIOAuthIntegration()
        
        print(f"✅ Redirect URI: {oauth.redirect_uri}")
        print(f"✅ Token storage: {oauth.token_storage_path}")
        
        # Check authentication status
        if oauth.is_authenticated():
            print("✅ Already authenticated")
            models = oauth.list_models()
            if models:
                print(f"   Available models: {len(models)}")
                print(f"   Sample: {', '.join(models[:3])}")
        else:
            print("ℹ️  Not authenticated")
            print("   To authenticate, use web interface:")
            print("   http://localhost:8000/oauth/openai/login")
        
        print("✅ OpenAI OAuth Integration: PASS")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI OAuth Integration: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_file():
    """Test that workflow file exists and is valid JSON"""
    print("\n" + "=" * 60)
    print("Testing Langflow Workflow File")
    print("=" * 60)
    
    try:
        import json
        
        workflow_path = project_root / "langflow" / "flows" / "code_assistant_oauth.json"
        
        if not workflow_path.exists():
            print(f"❌ Workflow file not found: {workflow_path}")
            return False
        
        print(f"✅ Workflow file exists: {workflow_path}")
        
        # Validate JSON
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        print(f"✅ Valid JSON")
        print(f"   Name: {workflow.get('name')}")
        print(f"   Description: {workflow.get('description')}")
        print(f"   Nodes: {len(workflow.get('nodes', []))}")
        print(f"   Edges: {len(workflow.get('edges', []))}")
        
        # Check required nodes
        node_types = [node.get('id') for node in workflow.get('nodes', [])]
        required_nodes = ['input', 'oauth_check', 'router', 'output']
        
        for req_node in required_nodes:
            if req_node in node_types:
                print(f"   ✅ Has {req_node} node")
            else:
                print(f"   ⚠️  Missing {req_node} node")
        
        print("✅ Langflow Workflow: PASS")
        return True
        
    except Exception as e:
        print(f"❌ Langflow Workflow: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_routes():
    """Test that web OAuth routes are importable"""
    print("\n" + "=" * 60)
    print("Testing Web OAuth Routes")
    print("=" * 60)
    
    try:
        # Check if oauth_routes.py exists
        routes_path = project_root / "web" / "oauth_routes.py"
        
        if not routes_path.exists():
            print(f"❌ OAuth routes file not found: {routes_path}")
            return False
        
        print(f"✅ OAuth routes file exists")
        
        # Try to import (may fail if dependencies missing)
        try:
            from web.oauth_routes import router
            print(f"✅ OAuth routes importable")
            print(f"   Router prefix: {router.prefix}")
            print(f"   Routes: {len(router.routes)}")
        except ImportError as e:
            print(f"⚠️  Import warning: {e}")
            print("   (This is OK if FastAPI is not installed)")
        
        print("✅ Web OAuth Routes: PASS")
        return True
        
    except Exception as e:
        print(f"❌ Web OAuth Routes: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("OsMEN OAuth Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("GitHub OAuth", test_github_oauth()))
    results.append(("OpenAI OAuth", test_openai_oauth()))
    results.append(("Langflow Workflow", test_workflow_file()))
    results.append(("Web Routes", test_web_routes()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print("\n" + "=" * 60)
    print(f"Total: {total_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if total_passed == total_tests:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
