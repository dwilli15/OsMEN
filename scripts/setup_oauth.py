#!/usr/bin/env python3
"""
OAuth Setup CLI - v3.0

Interactive command-line tool for setting up OAuth integrations
without writing any code. Part of the no-code first principle.

Usage:
    python scripts/setup_oauth.py --provider google
    python scripts/setup_oauth.py --provider microsoft
    python scripts/setup_oauth.py --list
    python scripts/setup_oauth.py --status
"""

import argparse
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from integrations.v3_integration_layer import V3IntegrationLayer
from loguru import logger


class OAuthSetupCLI:
    """Interactive OAuth setup command-line interface"""
    
    def __init__(self):
        self.integration = V3IntegrationLayer()
        self.config_dir = self.integration.config_dir
    
    def setup_google(self):
        """Interactive Google OAuth setup"""
        print("\n" + "=" * 70)
        print("Google OAuth Setup")
        print("=" * 70)
        print()
        print("You will need:")
        print("  1. Google Cloud Project with OAuth 2.0 credentials")
        print("  2. Client ID and Client Secret")
        print("  3. Redirect URI configured in Google Cloud Console")
        print()
        print("If you haven't set these up yet, follow the guide:")
        print("  https://developers.google.com/identity/protocols/oauth2")
        print()
        
        # Get client ID
        client_id = input("Enter your Google OAuth Client ID: ").strip()
        if not client_id:
            print("❌ Client ID is required")
            return False
        
        # Get client secret
        client_secret = input("Enter your Google OAuth Client Secret: ").strip()
        if not client_secret:
            print("❌ Client Secret is required")
            return False
        
        # Get redirect URI
        default_redirect = "http://localhost:8080/oauth/callback"
        redirect_uri = input(f"Enter redirect URI (default: {default_redirect}): ").strip()
        if not redirect_uri:
            redirect_uri = default_redirect
        
        # Select scopes
        print("\nSelect Google API scopes:")
        print("  1. Calendar only")
        print("  2. Gmail only")
        print("  3. Calendar + Gmail")
        print("  4. Calendar + Gmail + Contacts (recommended)")
        print("  5. Custom")
        
        scope_choice = input("Enter choice (1-5, default: 4): ").strip() or "4"
        
        scopes_map = {
            "1": ['https://www.googleapis.com/auth/calendar'],
            "2": ['https://www.googleapis.com/auth/gmail.modify'],
            "3": [
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/gmail.modify'
            ],
            "4": [
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/contacts'
            ]
        }
        
        if scope_choice == "5":
            print("\nEnter scopes (comma-separated):")
            scopes_input = input("> ").strip()
            scopes = [s.strip() for s in scopes_input.split(',') if s.strip()]
        else:
            scopes = scopes_map.get(scope_choice, scopes_map["4"])
        
        # Confirm
        print("\n" + "-" * 70)
        print("Configuration Summary:")
        print(f"  Client ID: {client_id[:20]}...")
        print(f"  Redirect URI: {redirect_uri}")
        print(f"  Scopes: {', '.join(scopes)}")
        print("-" * 70)
        
        confirm = input("\nProceed with this configuration? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Setup cancelled")
            return False
        
        # Setup OAuth
        try:
            oauth_handler = self.integration.setup_google_oauth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scopes=scopes
            )
            
            print("\n✅ Google OAuth configured successfully!")
            print(f"\nConfiguration saved to: {self.config_dir}/config.json")
            
            # Generate authorization URL
            print("\n" + "=" * 70)
            print("Next Steps:")
            print("=" * 70)
            auth_url = oauth_handler.get_authorization_url()
            print("\n1. Visit this URL to authorize the application:")
            print(f"\n   {auth_url}\n")
            print("2. After authorization, you'll be redirected to your redirect URI")
            print("3. Copy the authorization code from the URL")
            print("4. Run: python scripts/complete_oauth.py --provider google --code <CODE>")
            print()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error setting up Google OAuth: {e}")
            logger.exception("Google OAuth setup failed")
            return False
    
    def setup_microsoft(self):
        """Interactive Microsoft OAuth setup"""
        print("\n" + "=" * 70)
        print("Microsoft OAuth Setup")
        print("=" * 70)
        print()
        print("You will need:")
        print("  1. Azure AD application with OAuth 2.0 credentials")
        print("  2. Application (client) ID")
        print("  3. Client Secret")
        print("  4. Redirect URI configured in Azure Portal")
        print()
        print("If you haven't set these up yet, follow the guide:")
        print("  https://docs.microsoft.com/en-us/graph/auth-register-app-v2")
        print()
        
        # Get client ID
        client_id = input("Enter your Microsoft Application (client) ID: ").strip()
        if not client_id:
            print("❌ Client ID is required")
            return False
        
        # Get client secret
        client_secret = input("Enter your Microsoft Client Secret: ").strip()
        if not client_secret:
            print("❌ Client Secret is required")
            return False
        
        # Get tenant ID
        default_tenant = "common"
        tenant_id = input(f"Enter tenant ID (default: {default_tenant}): ").strip()
        if not tenant_id:
            tenant_id = default_tenant
        
        # Get redirect URI
        default_redirect = "http://localhost:8080/oauth/callback"
        redirect_uri = input(f"Enter redirect URI (default: {default_redirect}): ").strip()
        if not redirect_uri:
            redirect_uri = default_redirect
        
        # Select scopes
        print("\nSelect Microsoft Graph API scopes:")
        print("  1. Calendar only")
        print("  2. Mail only")
        print("  3. Calendar + Mail")
        print("  4. Calendar + Mail + Contacts (recommended)")
        print("  5. Custom")
        
        scope_choice = input("Enter choice (1-5, default: 4): ").strip() or "4"
        
        scopes_map = {
            "1": ['Calendars.ReadWrite'],
            "2": ['Mail.ReadWrite'],
            "3": ['Calendars.ReadWrite', 'Mail.ReadWrite'],
            "4": ['Calendars.ReadWrite', 'Mail.ReadWrite', 'Contacts.ReadWrite']
        }
        
        if scope_choice == "5":
            print("\nEnter scopes (comma-separated):")
            scopes_input = input("> ").strip()
            scopes = [s.strip() for s in scopes_input.split(',') if s.strip()]
        else:
            scopes = scopes_map.get(scope_choice, scopes_map["4"])
        
        # Confirm
        print("\n" + "-" * 70)
        print("Configuration Summary:")
        print(f"  Client ID: {client_id[:20]}...")
        print(f"  Tenant ID: {tenant_id}")
        print(f"  Redirect URI: {redirect_uri}")
        print(f"  Scopes: {', '.join(scopes)}")
        print("-" * 70)
        
        confirm = input("\nProceed with this configuration? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Setup cancelled")
            return False
        
        # Setup OAuth
        try:
            oauth_handler = self.integration.setup_microsoft_oauth(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
                redirect_uri=redirect_uri,
                scopes=scopes
            )
            
            print("\n✅ Microsoft OAuth configured successfully!")
            print(f"\nConfiguration saved to: {self.config_dir}/config.json")
            
            # Generate authorization URL
            print("\n" + "=" * 70)
            print("Next Steps:")
            print("=" * 70)
            auth_url = oauth_handler.get_authorization_url()
            print("\n1. Visit this URL to authorize the application:")
            print(f"\n   {auth_url}\n")
            print("2. After authorization, you'll be redirected to your redirect URI")
            print("3. Copy the authorization code from the URL")
            print("4. Run: python scripts/complete_oauth.py --provider microsoft --code <CODE>")
            print()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error setting up Microsoft OAuth: {e}")
            logger.exception("Microsoft OAuth setup failed")
            return False
    
    def list_providers(self):
        """List available OAuth providers"""
        print("\nAvailable OAuth Providers:")
        print("=" * 70)
        print("\n1. Google")
        print("   - Google Calendar")
        print("   - Gmail")
        print("   - Google Contacts")
        print("\n2. Microsoft")
        print("   - Outlook Calendar")
        print("   - Outlook Mail")
        print("   - Microsoft Contacts")
        print()
    
    def show_status(self):
        """Show current OAuth configuration status"""
        print("\nOAuth Configuration Status:")
        print("=" * 70)
        
        status = self.integration.get_integration_status()
        
        # Google status
        print("\nGoogle:")
        google = status.get('google', {})
        print(f"  OAuth Configured: {'✅' if google.get('oauth_configured') else '❌'}")
        print(f"  Calendar Available: {'✅' if google.get('calendar_available') else '❌'}")
        print(f"  Gmail Available: {'✅' if google.get('gmail_available') else '❌'}")
        print(f"  Contacts Available: {'✅' if google.get('contacts_available') else '❌'}")
        if google.get('calendar_count'):
            print(f"  Calendars Found: {google['calendar_count']}")
        
        # Microsoft status
        print("\nMicrosoft:")
        microsoft = status.get('microsoft', {})
        print(f"  OAuth Configured: {'✅' if microsoft.get('oauth_configured') else '❌'}")
        print(f"  Calendar Available: {'✅' if microsoft.get('calendar_available') else '❌'}")
        print(f"  Mail Available: {'✅' if microsoft.get('mail_available') else '❌'}")
        print(f"  Contacts Available: {'✅' if microsoft.get('contacts_available') else '❌'}")
        if microsoft.get('calendar_count'):
            print(f"  Calendars Found: {microsoft['calendar_count']}")
        
        print()


def main():
    parser = argparse.ArgumentParser(
        description="OAuth Setup CLI - Configure integrations without writing code"
    )
    parser.add_argument(
        '--provider',
        choices=['google', 'microsoft'],
        help='OAuth provider to configure'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available providers'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current configuration status'
    )
    
    args = parser.parse_args()
    
    cli = OAuthSetupCLI()
    
    if args.list:
        cli.list_providers()
    elif args.status:
        cli.show_status()
    elif args.provider == 'google':
        cli.setup_google()
    elif args.provider == 'microsoft':
        cli.setup_microsoft()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
