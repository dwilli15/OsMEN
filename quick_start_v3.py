#!/usr/bin/env python3
"""
OsMEN v3.0 Quick Start Guide

Interactive setup wizard to get OsMEN up and running with
integrated services in minutes.

Usage:
    python quick_start_v3.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))


def print_banner():
    """Print welcome banner"""
    print("\n" + "=" * 70)
    print(" " * 20 + "OsMEN v3.0 Quick Start")
    print("=" * 70)
    print()
    print("This wizard will help you set up OsMEN with working integrations")
    print("in just a few minutes - no coding required!")
    print()


def check_prerequisites():
    """Check if system prerequisites are met"""
    print("\n📋 Checking Prerequisites...")
    print("-" * 70)
    
    # Check Python version
    import sys
    python_version = sys.version_info
    if python_version >= (3, 12):
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor} - Need 3.12+")
        return False
    
    # Check dependencies
    deps_ok = True
    required_deps = [
        ('loguru', 'Logging'),
        ('cryptography', 'Token encryption'),
        ('requests', 'HTTP requests'),
    ]
    
    for module, name in required_deps:
        try:
            __import__(module)
            print(f"✅ {name} ({module})")
        except ImportError:
            print(f"❌ {name} ({module}) - Run: pip install {module}")
            deps_ok = False
    
    return deps_ok


def show_menu():
    """Show main menu"""
    print("\n📚 What would you like to do?")
    print("-" * 70)
    print()
    print("1. 🔐 Setup Google OAuth (Calendar, Gmail, Contacts)")
    print("2. 🔐 Setup Microsoft OAuth (Outlook, Mail, Contacts)")
    print("3. 📊 Check Integration Status")
    print("4. 🧪 Test Integrations")
    print("5. 📖 View Documentation")
    print("6. 🚀 Start OsMEN Services")
    print("7. ❌ Exit")
    print()


def setup_google():
    """Guide user through Google OAuth setup"""
    print("\n🔐 Setting up Google OAuth...")
    print("-" * 70)
    
    os.system("python scripts/setup_oauth.py --provider google")


def setup_microsoft():
    """Guide user through Microsoft OAuth setup"""
    print("\n🔐 Setting up Microsoft OAuth...")
    print("-" * 70)
    
    os.system("python scripts/setup_oauth.py --provider microsoft")


def check_status():
    """Check and display integration status"""
    print("\n📊 Checking Integration Status...")
    print("-" * 70)
    
    os.system("python scripts/setup_oauth.py --status")


def test_integrations():
    """Test configured integrations"""
    print("\n🧪 Testing Integrations...")
    print("-" * 70)
    
    try:
        from integrations.v3_integration_layer import get_integration_layer
        
        integration = get_integration_layer()
        status = integration.get_integration_status()
        
        print("\nGoogle Services:")
        google = status.get('google', {})
        if google.get('oauth_configured'):
            print("  ✅ OAuth configured")
            
            if google.get('calendar_available'):
                print(f"  ✅ Calendar (found {google.get('calendar_count', 0)} calendars)")
            else:
                print("  ⚠️  Calendar not available")
            
            if google.get('gmail_available'):
                print("  ✅ Gmail")
            else:
                print("  ⚠️  Gmail not available")
        else:
            print("  ❌ OAuth not configured")
        
        print("\nMicrosoft Services:")
        microsoft = status.get('microsoft', {})
        if microsoft.get('oauth_configured'):
            print("  ✅ OAuth configured")
            
            if microsoft.get('calendar_available'):
                print(f"  ✅ Calendar (found {microsoft.get('calendar_count', 0)} calendars)")
            else:
                print("  ⚠️  Calendar not available")
            
            if microsoft.get('mail_available'):
                print("  ✅ Mail")
            else:
                print("  ⚠️  Mail not available")
        else:
            print("  ❌ OAuth not configured")
        
        print()
        
    except Exception as e:
        print(f"❌ Error testing integrations: {e}")


def view_docs():
    """Show documentation links"""
    print("\n📖 Documentation")
    print("-" * 70)
    print()
    print("📄 v3.0 Implementation Guide:")
    print("   docs/v3.0_IMPLEMENTATION_GUIDE.md")
    print()
    print("📄 README:")
    print("   README.md")
    print()
    print("📄 v3.0 Changelog:")
    print("   CHANGELOG_V3.md")
    print()
    print("📄 Setup Guide:")
    print("   docs/SETUP.md")
    print()
    print("🌐 Online Documentation:")
    print("   https://github.com/dwilli15/OsMEN")
    print()


def start_services():
    """Start OsMEN Docker services"""
    print("\n🚀 Starting OsMEN Services...")
    print("-" * 70)
    
    print("\nStarting Docker Compose services...")
    os.system("docker-compose up -d")
    
    print("\n✅ Services started!")
    print("\nAccess points:")
    print("  - Langflow: http://localhost:7860")
    print("  - n8n: http://localhost:5678 (admin/changeme)")
    print("  - Qdrant: http://localhost:6333/dashboard")
    print()


def main():
    """Main interactive loop"""
    print_banner()
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install missing dependencies.")
        print("\nRun: pip install -r requirements.txt")
        sys.exit(1)
    
    while True:
        show_menu()
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == '1':
            setup_google()
        elif choice == '2':
            setup_microsoft()
        elif choice == '3':
            check_status()
        elif choice == '4':
            test_integrations()
        elif choice == '5':
            view_docs()
        elif choice == '6':
            start_services()
        elif choice == '7':
            print("\n👋 Thanks for using OsMEN!")
            print("   For support: https://github.com/dwilli15/OsMEN/issues")
            print()
            break
        else:
            print("\n❌ Invalid choice. Please enter a number between 1-7.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup interrupted. Run again anytime!")
        sys.exit(0)
