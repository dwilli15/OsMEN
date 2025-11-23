#!/usr/bin/env python3
"""
OAuth Setup Wizard - Interactive CLI for setting up OAuth providers.

This wizard guides users through the OAuth setup process for Google,
Microsoft, and other providers.
"""

import os
import sys
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Add parent directory to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

try:
    from integrations.oauth import GoogleOAuthHandler, MicrosoftOAuthHandler, get_oauth_handler
    from loguru import logger
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)


class OAuthSetupWizard:
    """Interactive OAuth setup wizard."""
    
    def __init__(self):
        """Initialize the OAuth setup wizard."""
        self.repo_root = Path(__file__).parent.parent
        self.tokens_dir = Path.home() / ".osmen" / "tokens"
        self.tokens_dir.mkdir(parents=True, exist_ok=True)
    
    def print_banner(self):
        """Print welcome banner."""
        print("\n" + "=" * 60)
        print("    OsMEN OAuth Setup Wizard")
        print("=" * 60)
        print()
    
    def print_section(self, title: str):
        """Print section header."""
        print()
        print("-" * 60)
        print(f"  {title}")
        print("-" * 60)
    
    def setup_google_oauth(self):
        """
        Interactive Google OAuth setup wizard.
        
        Guides user through:
        1. Checking for credentials
        2. Generating authorization URL
        3. Opening browser
        4. Exchanging code for tokens
        5. Testing token
        6. Saving configuration
        """
        self.print_section("Google OAuth Setup")
        
        print("\nThis wizard will help you set up Google OAuth for:")
        print("  - Google Calendar")
        print("  - Gmail")
        print("  - Google Contacts")
        print()
        
        # Step 1: Check for credentials
        print("Step 1: Check Credentials")
        print("-" * 40)
        
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            print("\n⚠️  Google OAuth credentials not found in environment!")
            print()
            print("To get credentials:")
            print("  1. Go to https://console.cloud.google.com/")
            print("  2. Create a new project (or select existing)")
            print("  3. Enable APIs: Calendar, Gmail, Contacts")
            print("  4. Go to 'Credentials' → Create OAuth 2.0 Client ID")
            print("  5. Add redirect URI: http://localhost:8080/oauth/callback")
            print("  6. Copy the Client ID and Client Secret")
            print()
            
            response = input("Do you have your credentials ready? (y/n): ").strip().lower()
            if response != 'y':
                print("\nPlease get your credentials first, then run this wizard again.")
                return False
            
            print()
            client_id = input("Enter your Google Client ID: ").strip()
            client_secret = input("Enter your Google Client Secret: ").strip()
            
            if not client_id or not client_secret:
                print("\n❌ Credentials cannot be empty!")
                return False
            
            # Offer to save to .env
            save_to_env = input("\nSave credentials to .env file? (y/n): ").strip().lower()
            if save_to_env == 'y':
                env_file = self.repo_root / ".env"
                self._update_env_file(env_file, {
                    'GOOGLE_CLIENT_ID': client_id,
                    'GOOGLE_CLIENT_SECRET': client_secret
                })
                print(f"✅ Credentials saved to {env_file}")
        else:
            print("✅ Google OAuth credentials found in environment")
            print(f"   Client ID: {client_id[:20]}...")
        
        print()
        
        # Step 2: Create OAuth handler and generate auth URL
        print("\nStep 2: Generate Authorization URL")
        print("-" * 40)
        
        config = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': 'http://localhost:8080/oauth/callback',
            'scopes': [
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/contacts',
                'https://www.googleapis.com/auth/userinfo.email',
                'openid'
            ]
        }
        
        try:
            handler = GoogleOAuthHandler(config)
            auth_url = handler.get_authorization_url()
            
            print("\n✅ Authorization URL generated")
            print()
            print("Copy this URL and open it in your browser:")
            print("-" * 60)
            print(auth_url)
            print("-" * 60)
            print()
            
            # Step 3: Open browser
            open_browser = input("Open this URL in your default browser? (y/n): ").strip().lower()
            if open_browser == 'y':
                try:
                    webbrowser.open(auth_url)
                    print("✅ Browser opened")
                except Exception as e:
                    print(f"⚠️  Could not open browser: {e}")
                    print("Please copy the URL manually")
            
            print()
            print("After authorizing the application:")
            print("  1. You'll be redirected to the callback URL")
            print("  2. The URL will contain a 'code' parameter")
            print("  3. Copy the entire callback URL or just the code")
            print()
            
            # Step 4: Get authorization code
            print("\nStep 3: Enter Authorization Code")
            print("-" * 40)
            
            callback_or_code = input("\nPaste the callback URL or authorization code: ").strip()
            
            # Extract code from URL if full URL was provided
            if 'code=' in callback_or_code:
                code = callback_or_code.split('code=')[1].split('&')[0]
            else:
                code = callback_or_code
            
            if not code:
                print("\n❌ No authorization code provided!")
                return False
            
            # Step 5: Exchange code for tokens
            print("\nStep 4: Exchange Code for Tokens")
            print("-" * 40)
            print("Exchanging authorization code for access tokens...")
            
            tokens = handler.exchange_code_for_token(code)
            
            print("\n✅ Tokens received successfully!")
            print(f"   Access Token: {tokens['access_token'][:20]}...")
            print(f"   Token Type: {tokens['token_type']}")
            print(f"   Expires In: {tokens['expires_in']} seconds")
            if 'refresh_token' in tokens:
                print(f"   Refresh Token: {tokens['refresh_token'][:20]}...")
            
            # Step 6: Test token with validation
            print("\nStep 5: Validate Token")
            print("-" * 40)
            print("Testing token with Google API...")
            
            try:
                token_info = handler.validate_token(tokens['access_token'])
                if token_info.get('valid'):
                    print("✅ Token is valid!")
                    if 'email' in token_info:
                        print(f"   Email: {token_info['email']}")
                    if 'scope' in token_info:
                        print(f"   Scopes: {token_info['scope']}")
                else:
                    print("⚠️  Token validation returned unexpected result")
            except Exception as e:
                print(f"⚠️  Token validation failed: {e}")
            
            # Step 7: Save tokens
            print("\nStep 6: Save Tokens")
            print("-" * 40)
            
            token_file = self.tokens_dir / "google_tokens.json"
            
            save_tokens = input(f"\nSave tokens to {token_file}? (y/n): ").strip().lower()
            if save_tokens == 'y':
                with open(token_file, 'w') as f:
                    json.dump(tokens, f, indent=2)
                print(f"✅ Tokens saved to {token_file}")
                
                # Set restrictive permissions
                token_file.chmod(0o600)
                print("✅ File permissions set to 600 (owner read/write only)")
            
            # Success summary
            print()
            print("=" * 60)
            print("  Google OAuth Setup Complete! 🎉")
            print("=" * 60)
            print()
            print("Next steps:")
            print("  1. Your OAuth tokens are ready to use")
            print("  2. Tokens will auto-refresh when they expire")
            print("  3. You can now use Google Calendar, Gmail, and Contacts APIs")
            print()
            print("Example usage:")
            print("  from integrations.oauth import get_oauth_handler")
            print("  handler = get_oauth_handler('google', config)")
            print()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error during OAuth setup: {e}")
            logger.exception("OAuth setup failed")
            return False
    
    def setup_microsoft_oauth(self):
        """
        Interactive Microsoft OAuth setup wizard.
        
        Guides user through:
        1. Checking for credentials
        2. Selecting tenant type
        3. Generating authorization URL
        4. Exchanging code for tokens
        5. Testing token
        6. Saving configuration
        """
        self.print_section("Microsoft OAuth Setup")
        
        print("\nThis wizard will help you set up Microsoft OAuth for:")
        print("  - Outlook Calendar")
        print("  - Outlook Mail")
        print("  - Microsoft Contacts")
        print()
        
        # Step 1: Check for credentials
        print("Step 1: Check Credentials")
        print("-" * 40)
        
        client_id = os.getenv('MICROSOFT_CLIENT_ID')
        client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
        tenant = os.getenv('MICROSOFT_TENANT_ID', 'common')
        
        if not client_id or not client_secret:
            print("\n⚠️  Microsoft OAuth credentials not found in environment!")
            print()
            print("To get credentials:")
            print("  1. Go to https://portal.azure.com/")
            print("  2. Go to Azure Active Directory → App registrations")
            print("  3. Create a new registration (or select existing)")
            print("  4. Add redirect URI: http://localhost:8080/oauth/callback")
            print("  5. Go to 'Certificates & secrets' → Create new client secret")
            print("  6. Copy the Application (client) ID and Client Secret value")
            print()
            
            response = input("Do you have your credentials ready? (y/n): ").strip().lower()
            if response != 'y':
                print("\nPlease get your credentials first, then run this wizard again.")
                return False
            
            print()
            client_id = input("Enter your Microsoft Client ID (Application ID): ").strip()
            client_secret = input("Enter your Microsoft Client Secret: ").strip()
            
            if not client_id or not client_secret:
                print("\n❌ Credentials cannot be empty!")
                return False
            
            print()
            print("Tenant Type:")
            print("  1. common - Any Microsoft account or work/school account")
            print("  2. organizations - Work or school accounts only")
            print("  3. consumers - Personal Microsoft accounts only")
            print("  4. <tenant-id> - Specific organization only")
            print()
            tenant_choice = input("Select tenant type (1-4) or enter tenant ID: ").strip()
            
            tenant_map = {
                '1': 'common',
                '2': 'organizations',
                '3': 'consumers'
            }
            tenant = tenant_map.get(tenant_choice, tenant_choice if tenant_choice == '4' else 'common')
            
            # Offer to save to .env
            save_to_env = input("\nSave credentials to .env file? (y/n): ").strip().lower()
            if save_to_env == 'y':
                env_file = self.repo_root / ".env"
                self._update_env_file(env_file, {
                    'MICROSOFT_CLIENT_ID': client_id,
                    'MICROSOFT_CLIENT_SECRET': client_secret,
                    'MICROSOFT_TENANT_ID': tenant
                })
                print(f"✅ Credentials saved to {env_file}")
        else:
            print("✅ Microsoft OAuth credentials found in environment")
            print(f"   Client ID: {client_id[:20]}...")
            print(f"   Tenant: {tenant}")
        
        print()
        
        # Step 2: Create OAuth handler and generate auth URL
        print("\nStep 2: Generate Authorization URL")
        print("-" * 40)
        
        config = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': 'http://localhost:8080/oauth/callback',
            'tenant': tenant,
            'scopes': [
                'https://graph.microsoft.com/Calendars.ReadWrite',
                'https://graph.microsoft.com/Mail.ReadWrite',
                'https://graph.microsoft.com/Contacts.ReadWrite',
                'https://graph.microsoft.com/User.Read',
                'offline_access'
            ]
        }
        
        try:
            handler = MicrosoftOAuthHandler(config)
            auth_url = handler.get_authorization_url()
            
            print("\n✅ Authorization URL generated")
            print()
            print("Copy this URL and open it in your browser:")
            print("-" * 60)
            print(auth_url)
            print("-" * 60)
            print()
            
            # Step 3: Open browser
            open_browser = input("Open this URL in your default browser? (y/n): ").strip().lower()
            if open_browser == 'y':
                try:
                    webbrowser.open(auth_url)
                    print("✅ Browser opened")
                except Exception as e:
                    print(f"⚠️  Could not open browser: {e}")
                    print("Please copy the URL manually")
            
            print()
            print("After authorizing the application:")
            print("  1. You'll be redirected to the callback URL")
            print("  2. The URL will contain a 'code' parameter")
            print("  3. Copy the entire callback URL or just the code")
            print()
            
            # Step 4: Get authorization code
            print("\nStep 3: Enter Authorization Code")
            print("-" * 40)
            
            callback_or_code = input("\nPaste the callback URL or authorization code: ").strip()
            
            # Extract code from URL if full URL was provided
            if 'code=' in callback_or_code:
                code = callback_or_code.split('code=')[1].split('&')[0]
            else:
                code = callback_or_code
            
            if not code:
                print("\n❌ No authorization code provided!")
                return False
            
            # Step 5: Exchange code for tokens
            print("\nStep 4: Exchange Code for Tokens")
            print("-" * 40)
            print("Exchanging authorization code for access tokens...")
            
            tokens = handler.exchange_code_for_token(code)
            
            print("\n✅ Tokens received successfully!")
            print(f"   Access Token: {tokens['access_token'][:20]}...")
            print(f"   Token Type: {tokens['token_type']}")
            print(f"   Expires In: {tokens['expires_in']} seconds")
            if 'refresh_token' in tokens:
                print(f"   Refresh Token: {tokens['refresh_token'][:20]}...")
            if 'id_token' in tokens:
                print(f"   ID Token received (contains user info)")
            
            # Step 6: Validate token
            print("\nStep 5: Validate Token")
            print("-" * 40)
            print("Testing token with Microsoft Graph API...")
            
            try:
                is_valid = handler.validate_token(tokens['access_token'])
                if is_valid:
                    print("✅ Token is valid!")
                    
                    # Try to get user info
                    try:
                        user_info = handler.get_user_info(tokens['access_token'])
                        if user_info:
                            print(f"   User: {user_info.get('displayName', 'N/A')}")
                            print(f"   Email: {user_info.get('mail') or user_info.get('userPrincipalName', 'N/A')}")
                    except Exception:
                        pass
                else:
                    print("⚠️  Token validation returned unexpected result")
            except Exception as e:
                print(f"⚠️  Token validation failed: {e}")
            
            # Step 7: Save tokens
            print("\nStep 6: Save Tokens")
            print("-" * 40)
            
            token_file = self.tokens_dir / "microsoft_tokens.json"
            
            save_tokens = input(f"\nSave tokens to {token_file}? (y/n): ").strip().lower()
            if save_tokens == 'y':
                with open(token_file, 'w') as f:
                    json.dump(tokens, f, indent=2)
                print(f"✅ Tokens saved to {token_file}")
                
                # Set restrictive permissions
                token_file.chmod(0o600)
                print("✅ File permissions set to 600 (owner read/write only)")
            
            # Success summary
            print()
            print("=" * 60)
            print("  Microsoft OAuth Setup Complete! 🎉")
            print("=" * 60)
            print()
            print("Next steps:")
            print("  1. Your OAuth tokens are ready to use")
            print("  2. Tokens will auto-refresh when they expire")
            print("  3. You can now use Outlook Calendar, Mail, and Contacts APIs")
            print()
            print("Example usage:")
            print("  from integrations.oauth import get_oauth_handler")
            print("  handler = get_oauth_handler('microsoft', config)")
            print()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error during OAuth setup: {e}")
            logger.exception("OAuth setup failed")
            return False
    
    def _update_env_file(self, env_file: Path, updates: Dict[str, str]):
        """Update .env file with new values."""
        # Read existing .env if it exists
        env_content = {}
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key.strip()] = value.strip()
        
        # Update with new values
        env_content.update(updates)
        
        # Write back
        with open(env_file, 'w') as f:
            f.write("# OsMEN Environment Configuration\n")
            f.write("# Auto-updated by OAuth Setup Wizard\n\n")
            for key, value in sorted(env_content.items()):
                f.write(f"{key}={value}\n")
    
    def run(self):
        """Run the OAuth setup wizard."""
        self.print_banner()
        
        print("This wizard will help you set up OAuth for OsMEN.")
        print()
        print("Available providers:")
        print("  1. Google (Calendar, Gmail, Contacts)")
        print("  2. Microsoft (Outlook Calendar, Mail, Contacts)")
        print("  3. Exit")
        print()
        
        choice = input("Select a provider (1-3): ").strip()
        
        if choice == '1':
            success = self.setup_google_oauth()
            if success:
                print("\n✅ Setup completed successfully!")
            else:
                print("\n❌ Setup was not completed")
        elif choice == '2':
            success = self.setup_microsoft_oauth()
            if success:
                print("\n✅ Setup completed successfully!")
            else:
                print("\n❌ Setup was not completed")
        elif choice == '3':
            print("\nExiting wizard...")
        else:
            print("\n❌ Invalid choice")
        
        print()


def main():
    """Main entry point."""
    wizard = OAuthSetupWizard()
    wizard.run()


if __name__ == "__main__":
    main()
