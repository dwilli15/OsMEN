#!/usr/bin/env python3
"""
Example: Using OAuth Code Assistant

This script demonstrates how to use the OAuth-based code generation workflow
programmatically.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def example_github_copilot():
    """Example: Generate code using GitHub Copilot with OAuth"""
    print("\n" + "=" * 60)
    print("Example: GitHub Copilot Code Generation")
    print("=" * 60)
    
    from integrations.oauth.github_oauth import GitHubOAuthIntegration
    
    # Initialize OAuth
    copilot = GitHubOAuthIntegration()
    
    # Check if authenticated
    if not copilot.is_authenticated():
        print("\n❌ Not authenticated with GitHub")
        print("\nTo authenticate:")
        print(f"1. Visit: {copilot.get_authorization_url()[:80]}...")
        print("2. Authorize the application")
        print("3. After redirect, the token will be saved")
        print("\nOr visit the web interface:")
        print("   http://localhost:8000/oauth/github/login")
        return
    
    print("\n✅ Authenticated with GitHub Copilot")
    
    # Get user info
    user_info = copilot.get_user_info()
    if user_info:
        print(f"   User: {user_info.get('login')}")
    
    # Generate code
    print("\n📝 Generating code...")
    prompt = "Write a Python function to calculate the Fibonacci sequence recursively"
    
    code = copilot.generate_code(prompt, language="python")
    
    if code:
        print("\n✅ Code generated successfully:")
        print("\n" + "-" * 60)
        print(code)
        print("-" * 60)
    else:
        print("\n❌ Failed to generate code")


def example_openai_codex():
    """Example: Generate code using OpenAI with OAuth"""
    print("\n" + "=" * 60)
    print("Example: OpenAI Codex Code Generation")
    print("=" * 60)
    
    from integrations.oauth.openai_oauth import OpenAIOAuthIntegration
    
    # Initialize OAuth
    openai = OpenAIOAuthIntegration()
    
    # Check if authenticated
    if not openai.is_authenticated():
        print("\n❌ Not authenticated with OpenAI")
        print("\nTo authenticate:")
        print("1. Get your API key from https://platform.openai.com/api-keys")
        print("2. Visit: http://localhost:8000/oauth/openai/login")
        print("3. Enter your API key and authenticate")
        print("\nOr use the API directly:")
        print("   api_key = 'sk-...'")
        print("   openai.set_api_key(api_key)")
        return
    
    print("\n✅ Authenticated with OpenAI")
    
    # List available models
    models = openai.list_models()
    if models:
        print(f"   Available models: {len(models)}")
        print(f"   Including: {', '.join(models[:3])}")
    
    # Generate code
    print("\n📝 Generating code...")
    prompt = "Write a Python function to implement binary search on a sorted list"
    
    code = openai.generate_code(prompt, model="gpt-4")
    
    if code:
        print("\n✅ Code generated successfully:")
        print("\n" + "-" * 60)
        print(code)
        print("-" * 60)
    else:
        print("\n❌ Failed to generate code")


def example_check_status():
    """Example: Check OAuth authentication status"""
    print("\n" + "=" * 60)
    print("Example: Check Authentication Status")
    print("=" * 60)
    
    from integrations.oauth.github_oauth import GitHubOAuthIntegration
    from integrations.oauth.openai_oauth import OpenAIOAuthIntegration
    
    github = GitHubOAuthIntegration()
    openai = OpenAIOAuthIntegration()
    
    print("\nAuthentication Status:")
    print("-" * 60)
    
    # GitHub status
    if github.is_authenticated():
        user_info = github.get_user_info()
        username = user_info.get('login') if user_info else 'Unknown'
        print(f"✅ GitHub Copilot: Authenticated ({username})")
    else:
        print("❌ GitHub Copilot: Not authenticated")
        print(f"   Login at: http://localhost:8000/oauth/github/login")
    
    # OpenAI status
    if openai.is_authenticated():
        models = openai.list_models()
        model_count = len(models) if models else 0
        print(f"✅ OpenAI: Authenticated ({model_count} models available)")
    else:
        print("❌ OpenAI: Not authenticated")
        print(f"   Login at: http://localhost:8000/oauth/openai/login")
    
    print("-" * 60)


def example_web_api():
    """Example: Using the web API to check status"""
    print("\n" + "=" * 60)
    print("Example: Web API Usage")
    print("=" * 60)
    
    try:
        import requests
        
        print("\n📡 Checking OAuth status via API...")
        
        response = requests.get("http://localhost:8000/oauth/status", timeout=5)
        
        if response.status_code == 200:
            status = response.json()
            
            print("\n✅ API Response:")
            print("-" * 60)
            
            # GitHub status
            github = status.get('github', {})
            if github.get('authenticated'):
                username = github.get('username', 'Unknown')
                print(f"GitHub: ✅ Authenticated ({username})")
            else:
                print("GitHub: ❌ Not authenticated")
            
            # OpenAI status
            openai = status.get('openai', {})
            if openai.get('authenticated'):
                print("OpenAI: ✅ Authenticated")
            else:
                print("OpenAI: ❌ Not authenticated")
            
            print("-" * 60)
        else:
            print(f"\n❌ API request failed: {response.status_code}")
            print("   Make sure the web service is running:")
            print("   docker-compose up -d")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to web service")
        print("   Make sure services are running:")
        print("   docker-compose up -d")
    except ImportError:
        print("\n⚠️  'requests' library not installed")
        print("   Install with: pip install requests")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("OAuth Code Assistant - Usage Examples")
    print("=" * 60)
    
    print("\nThis script demonstrates how to use the OAuth workflow:")
    print("1. Check authentication status")
    print("2. Generate code with GitHub Copilot")
    print("3. Generate code with OpenAI Codex")
    print("4. Use the web API")
    
    print("\n" + "=" * 60)
    
    # Run examples
    example_check_status()
    example_web_api()
    
    print("\n" + "=" * 60)
    print("Code Generation Examples")
    print("=" * 60)
    print("\nTo run code generation examples, uncomment the desired example:")
    print("  - example_github_copilot()")
    print("  - example_openai_codex()")
    print("\nNote: These require authentication first.")
    
    # Uncomment to run code generation:
    # example_github_copilot()
    # example_openai_codex()
    
    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    print("\n1. Authenticate with a provider:")
    print("   - GitHub: http://localhost:8000/oauth/github/login")
    print("   - OpenAI: http://localhost:8000/oauth/openai/login")
    print("\n2. Re-run this script to see code generation in action")
    print("\n3. Try the Langflow workflow:")
    print("   - Open: http://localhost:7860")
    print("   - Import: langflow/flows/code_assistant_oauth.json")
    print("\n4. Read the documentation:")
    print("   - Quick Start: OAUTH_QUICKSTART.md")
    print("   - Full Guide: docs/OAUTH_WORKFLOW.md")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
