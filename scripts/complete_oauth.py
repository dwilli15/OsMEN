#!/usr/bin/env python3
"""
Complete OAuth Flow - v3.0

Completes the OAuth authorization flow by exchanging the authorization
code for access and refresh tokens.

Usage:
    python scripts/complete_oauth.py --provider google --code <AUTHORIZATION_CODE>
    python scripts/complete_oauth.py --provider microsoft --code <AUTHORIZATION_CODE>
"""

import argparse
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from integrations.v3_integration_layer import V3IntegrationLayer
from loguru import logger


class OAuthCompletionCLI:
    """Complete OAuth authorization flow"""
    
    def __init__(self):
        self.integration = V3IntegrationLayer()
        self.config_dir = self.integration.config_dir
        self.tokens_dir = os.path.join(self.config_dir, 'tokens')
        Path(self.tokens_dir).mkdir(parents=True, exist_ok=True)
    
    def complete_google_oauth(self, code: str) -> bool:
        """
        Complete Google OAuth flow.
        
        Args:
            code: Authorization code from OAuth redirect
            
        Returns:
            True if successful
        """
        print("\n" + "=" * 70)
        print("Completing Google OAuth Authorization")
        print("=" * 70)
        
        if not self.integration.google_oauth:
            print("\n❌ Google OAuth not configured.")
            print("   Run: python scripts/setup_oauth.py --provider google")
            return False
        
        try:
            # Exchange code for tokens
            print("\nExchanging authorization code for tokens...")
            token_data = self.integration.google_oauth.exchange_code(code)
            
            if not token_data:
                print("❌ Failed to exchange code for tokens")
                return False
            
            # Save tokens
            token_file = os.path.join(self.tokens_dir, 'google_tokens.json')
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            print("✅ Successfully obtained access token!")
            print(f"✅ Tokens saved to: {token_file}")
            
            # Validate token
            print("\nValidating token...")
            if self.integration.google_oauth.validate_token(token_data['access_token']):
                print("✅ Token is valid!")
            else:
                print("⚠️  Token validation failed")
            
            # Test calendar access
            print("\nTesting Google Calendar access...")
            try:
                calendar = self.integration.get_google_calendar()
                if calendar:
                    calendars = calendar.list_calendars()
                    print(f"✅ Found {len(calendars)} calendars:")
                    for cal in calendars[:5]:  # Show first 5
                        print(f"   - {cal.get('summary', 'Unnamed')}")
                    if len(calendars) > 5:
                        print(f"   ... and {len(calendars) - 5} more")
            except Exception as e:
                print(f"⚠️  Calendar access test failed: {e}")
            
            print("\n" + "=" * 70)
            print("Google OAuth Setup Complete!")
            print("=" * 70)
            print("\nYou can now use Google integrations:")
            print("  - Google Calendar")
            print("  - Gmail")
            print("  - Google Contacts")
            print()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error completing OAuth: {e}")
            logger.exception("Google OAuth completion failed")
            return False
    
    def complete_microsoft_oauth(self, code: str) -> bool:
        """
        Complete Microsoft OAuth flow.
        
        Args:
            code: Authorization code from OAuth redirect
            
        Returns:
            True if successful
        """
        print("\n" + "=" * 70)
        print("Completing Microsoft OAuth Authorization")
        print("=" * 70)
        
        if not self.integration.microsoft_oauth:
            print("\n❌ Microsoft OAuth not configured.")
            print("   Run: python scripts/setup_oauth.py --provider microsoft")
            return False
        
        try:
            # Exchange code for tokens
            print("\nExchanging authorization code for tokens...")
            token_data = self.integration.microsoft_oauth.exchange_code(code)
            
            if not token_data:
                print("❌ Failed to exchange code for tokens")
                return False
            
            # Save tokens
            token_file = os.path.join(self.tokens_dir, 'microsoft_tokens.json')
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            print("✅ Successfully obtained access token!")
            print(f"✅ Tokens saved to: {token_file}")
            
            # Validate token
            print("\nValidating token...")
            if self.integration.microsoft_oauth.validate_token(token_data['access_token']):
                print("✅ Token is valid!")
            else:
                print("⚠️  Token validation failed")
            
            # Test calendar access
            print("\nTesting Outlook Calendar access...")
            try:
                calendar = self.integration.get_outlook_calendar()
                if calendar:
                    calendars = calendar.list_calendars()
                    print(f"✅ Found {len(calendars)} calendars:")
                    for cal in calendars[:5]:  # Show first 5
                        print(f"   - {cal.get('name', 'Unnamed')}")
                    if len(calendars) > 5:
                        print(f"   ... and {len(calendars) - 5} more")
            except Exception as e:
                print(f"⚠️  Calendar access test failed: {e}")
            
            print("\n" + "=" * 70)
            print("Microsoft OAuth Setup Complete!")
            print("=" * 70)
            print("\nYou can now use Microsoft integrations:")
            print("  - Outlook Calendar")
            print("  - Outlook Mail")
            print("  - Microsoft Contacts")
            print()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error completing OAuth: {e}")
            logger.exception("Microsoft OAuth completion failed")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Complete OAuth authorization flow"
    )
    parser.add_argument(
        '--provider',
        required=True,
        choices=['google', 'microsoft'],
        help='OAuth provider'
    )
    parser.add_argument(
        '--code',
        required=True,
        help='Authorization code from OAuth redirect'
    )
    
    args = parser.parse_args()
    
    cli = OAuthCompletionCLI()
    
    if args.provider == 'google':
        success = cli.complete_google_oauth(args.code)
    elif args.provider == 'microsoft':
        success = cli.complete_microsoft_oauth(args.code)
    else:
        print(f"Unknown provider: {args.provider}")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
