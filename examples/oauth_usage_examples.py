#!/usr/bin/env python3
"""
OAuth Usage Examples

Comprehensive examples demonstrating how to use the OAuth system
for Google and Microsoft APIs.
"""

import sys
from pathlib import Path

# Add parent directory to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from integrations.oauth import GoogleOAuthHandler, MicrosoftOAuthHandler, get_oauth_handler
from integrations.google.wrappers import GoogleCalendarWrapper, GoogleGmailWrapper, GoogleContactsWrapper
from integrations.microsoft.wrappers import MicrosoftCalendarWrapper, MicrosoftMailWrapper, MicrosoftContactsWrapper
from integrations.security import TokenManager, EncryptionManager
from datetime import datetime, timedelta


def example_google_oauth_flow():
    """
    Example 1: Complete Google OAuth Flow
    
    Demonstrates the full OAuth flow from authorization to token exchange.
    """
    print("\n" + "=" * 60)
    print("Example 1: Google OAuth Flow")
    print("=" * 60)
    
    # Configuration
    config = {
        'client_id': 'YOUR_GOOGLE_CLIENT_ID',
        'client_secret': 'YOUR_GOOGLE_CLIENT_SECRET',
        'redirect_uri': 'http://localhost:8080/oauth/callback',
        'scopes': [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/contacts'
        ]
    }
    
    # Initialize OAuth handler
    handler = GoogleOAuthHandler(config)
    
    # Step 1: Generate authorization URL
    auth_url = handler.get_authorization_url()
    print(f"\n1. Visit this URL to authorize:\n{auth_url}")
    
    # Step 2: User authorizes and gets redirected with code
    # In real usage, you'd extract this from the callback URL
    auth_code = input("\n2. Enter the authorization code from callback URL: ").strip()
    
    # Step 3: Exchange code for tokens
    tokens = handler.exchange_code_for_token(auth_code)
    print(f"\n3. Tokens received:")
    print(f"   - Access Token: {tokens['access_token'][:30]}...")
    print(f"   - Expires in: {tokens['expires_in']} seconds")
    if 'refresh_token' in tokens:
        print(f"   - Refresh Token: {tokens['refresh_token'][:30]}...")
    
    # Step 4: Validate token
    is_valid = handler.validate_token(tokens['access_token'])
    print(f"\n4. Token validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    return tokens


def example_microsoft_oauth_flow():
    """
    Example 2: Complete Microsoft OAuth Flow
    
    Demonstrates the full OAuth flow for Microsoft with tenant selection.
    """
    print("\n" + "=" * 60)
    print("Example 2: Microsoft OAuth Flow")
    print("=" * 60)
    
    # Configuration
    config = {
        'client_id': 'YOUR_MICROSOFT_CLIENT_ID',
        'client_secret': 'YOUR_MICROSOFT_CLIENT_SECRET',
        'redirect_uri': 'http://localhost:8080/oauth/callback',
        'tenant': 'common',  # or 'organizations', 'consumers', or specific tenant ID
        'scopes': [
            'https://graph.microsoft.com/Calendars.ReadWrite',
            'https://graph.microsoft.com/Mail.ReadWrite',
            'https://graph.microsoft.com/Contacts.ReadWrite',
            'offline_access'
        ]
    }
    
    # Initialize OAuth handler
    handler = MicrosoftOAuthHandler(config)
    
    # Step 1: Generate authorization URL
    auth_url = handler.get_authorization_url()
    print(f"\n1. Visit this URL to authorize:\n{auth_url}")
    
    # Step 2: User authorizes and gets redirected with code
    auth_code = input("\n2. Enter the authorization code from callback URL: ").strip()
    
    # Step 3: Exchange code for tokens
    tokens = handler.exchange_code_for_token(auth_code)
    print(f"\n3. Tokens received:")
    print(f"   - Access Token: {tokens['access_token'][:30]}...")
    print(f"   - Expires in: {tokens['expires_in']} seconds")
    if 'refresh_token' in tokens:
        print(f"   - Refresh Token: {tokens['refresh_token'][:30]}...")
    if 'id_token' in tokens:
        print(f"   - ID Token received (contains user info)")
    
    # Step 4: Get user info from ID token
    try:
        user_info = handler.get_user_info(tokens['access_token'])
        print(f"\n4. User Info:")
        print(f"   - Name: {user_info.get('displayName')}")
        print(f"   - Email: {user_info.get('mail') or user_info.get('userPrincipalName')}")
    except Exception as e:
        print(f"\n4. Could not retrieve user info: {e}")
    
    return tokens


def example_secure_token_storage():
    """
    Example 3: Secure Token Storage with Encryption
    
    Demonstrates using TokenManager for encrypted token storage.
    """
    print("\n" + "=" * 60)
    print("Example 3: Secure Token Storage")
    print("=" * 60)
    
    # Initialize encryption manager
    encryption_key = EncryptionManager.generate_key()
    token_manager = TokenManager(
        db_path='~/.osmen/tokens.db',
        encryption_key=encryption_key
    )
    
    # Save tokens (automatically encrypted)
    token_data = {
        'access_token': 'ya29.a0AfH6SMB...',
        'refresh_token': '1//0gB7...',
        'expires_in': 3600,
        'scopes': ['calendar', 'gmail']
    }
    
    token_manager.save_token(
        provider='google',
        user_id='user@example.com',
        token_data=token_data
    )
    print("\n1. ✅ Token saved (encrypted at rest)")
    
    # Retrieve tokens (automatically decrypted)
    retrieved_token = token_manager.get_token('google', 'user@example.com')
    print(f"\n2. ✅ Token retrieved:")
    print(f"   - Access Token: {retrieved_token['access_token'][:30]}...")
    print(f"   - Expires at: {retrieved_token['expires_at']}")
    
    # List all stored tokens (without decrypting)
    all_tokens = token_manager.list_tokens()
    print(f"\n3. ✅ Stored tokens: {len(all_tokens)}")
    for token_info in all_tokens:
        print(f"   - {token_info['provider']}/{token_info['user_id']}")
    
    return token_manager


def example_automatic_token_refresh():
    """
    Example 4: Automatic Token Refresh
    
    Demonstrates automatic token refresh when tokens expire.
    """
    print("\n" + "=" * 60)
    print("Example 4: Automatic Token Refresh")
    print("=" * 60)
    
    from integrations.security import TokenRefresher
    from integrations.oauth import oauth_registry
    
    # Initialize token manager
    token_manager = TokenManager()
    
    # Initialize token refresher
    refresher = TokenRefresher(
        token_manager=token_manager,
        oauth_registry=oauth_registry
    )
    
    # Check and refresh if needed
    provider = 'google'
    user_id = 'user@example.com'
    
    print(f"\n1. Checking token for {provider}/{user_id}...")
    success = refresher.check_and_refresh_token(provider, user_id)
    
    if success:
        print("   ✅ Token is valid or was refreshed successfully")
    else:
        print("   ❌ Token refresh failed")
    
    # Start background refresh scheduler
    from integrations.security.token_refresher import TokenRefreshScheduler
    
    scheduler = TokenRefreshScheduler(
        token_refresher=refresher,
        check_interval=300  # Check every 5 minutes
    )
    
    scheduler.start()
    print("\n2. ✅ Background token refresh scheduler started")
    print("   - Tokens will be automatically refreshed before expiring")
    
    # Later, stop the scheduler
    # scheduler.stop()


def example_google_calendar_api():
    """
    Example 5: Using Google Calendar API
    
    Demonstrates using the Calendar API wrapper with OAuth.
    """
    print("\n" + "=" * 60)
    print("Example 5: Google Calendar API")
    print("=" * 60)
    
    # Initialize OAuth handler
    config = {
        'client_id': 'YOUR_GOOGLE_CLIENT_ID',
        'client_secret': 'YOUR_GOOGLE_CLIENT_SECRET',
        'redirect_uri': 'http://localhost:8080/oauth/callback'
    }
    oauth_handler = GoogleOAuthHandler(config)
    
    # Initialize Calendar wrapper
    calendar = GoogleCalendarWrapper(oauth_handler=oauth_handler)
    
    # List calendars
    print("\n1. Listing calendars...")
    calendars = calendar.list_calendars()
    for cal in calendars[:3]:  # Show first 3
        print(f"   - {cal.get('summary')} ({cal.get('id')})")
    
    # Get events for next 7 days
    print("\n2. Listing upcoming events...")
    start_time = datetime.now()
    end_time = start_time + timedelta(days=7)
    
    events = calendar.list_events(
        calendar_id='primary',
        time_min=start_time,
        time_max=end_time
    )
    
    for event in events[:5]:  # Show first 5
        print(f"   - {event.get('summary')} at {event.get('start', {}).get('dateTime')}")
    
    # Create a new event
    print("\n3. Creating new event...")
    new_event = {
        'summary': 'Team Meeting',
        'description': 'Discuss Q1 objectives',
        'start': {
            'dateTime': (datetime.now() + timedelta(days=1)).isoformat(),
            'timeZone': 'UTC'
        },
        'end': {
            'dateTime': (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
            'timeZone': 'UTC'
        }
    }
    
    created_event = calendar.create_event('primary', new_event)
    print(f"   ✅ Event created: {created_event.get('id')}")


def example_microsoft_mail_api():
    """
    Example 6: Using Microsoft Mail API
    
    Demonstrates using the Outlook Mail API wrapper.
    """
    print("\n" + "=" * 60)
    print("Example 6: Microsoft Mail API")
    print("=" * 60)
    
    # Initialize OAuth handler
    config = {
        'client_id': 'YOUR_MICROSOFT_CLIENT_ID',
        'client_secret': 'YOUR_MICROSOFT_CLIENT_SECRET',
        'redirect_uri': 'http://localhost:8080/oauth/callback',
        'tenant': 'common'
    }
    oauth_handler = MicrosoftOAuthHandler(config)
    
    # Initialize Mail wrapper
    mail = MicrosoftMailWrapper(oauth_handler=oauth_handler)
    
    # List recent messages
    print("\n1. Listing recent messages...")
    messages = mail.list_messages(max_results=10)
    for msg in messages[:5]:
        print(f"   - {msg.get('subject')} from {msg.get('from', {}).get('emailAddress', {}).get('address')}")
    
    # Send an email
    print("\n2. Sending email...")
    mail.send_email(
        to=['recipient@example.com'],
        subject='Test Email',
        body='This is a test email sent via Microsoft Graph API',
        html=False
    )
    print("   ✅ Email sent successfully")
    
    # Search messages
    print("\n3. Searching messages...")
    search_results = mail.search_messages('subject:"Important"')
    print(f"   Found {len(search_results)} messages matching criteria")


def example_error_handling():
    """
    Example 7: Error Handling
    
    Demonstrates proper error handling for OAuth operations.
    """
    print("\n" + "=" * 60)
    print("Example 7: Error Handling")
    print("=" * 60)
    
    from integrations.oauth.oauth_errors import (
        OAuthError,
        OAuthConfigError,
        OAuthTokenExchangeError,
        OAuthInvalidTokenError
    )
    
    config = {
        'client_id': 'INVALID_ID',
        'client_secret': 'INVALID_SECRET',
        'redirect_uri': 'http://localhost:8080/callback'
    }
    
    try:
        handler = GoogleOAuthHandler(config)
        
        # This will fail with invalid credentials
        tokens = handler.exchange_code_for_token('invalid_code')
        
    except OAuthTokenExchangeError as e:
        print(f"   ❌ Token exchange failed: {e}")
    except OAuthConfigError as e:
        print(f"   ❌ Configuration error: {e}")
    except OAuthInvalidTokenError as e:
        print(f"   ❌ Invalid token: {e}")
    except OAuthError as e:
        print(f"   ❌ OAuth error: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")


def example_multi_provider_management():
    """
    Example 8: Managing Multiple OAuth Providers
    
    Demonstrates using the OAuth registry to manage multiple providers.
    """
    print("\n" + "=" * 60)
    print("Example 8: Multi-Provider Management")
    print("=" * 60)
    
    from integrations.oauth import oauth_registry
    
    # List registered providers
    providers = oauth_registry.list_providers()
    print(f"\n1. Registered OAuth providers: {', '.join(providers)}")
    
    # Get handler for specific provider
    google_config = {
        'client_id': 'GOOGLE_CLIENT_ID',
        'client_secret': 'GOOGLE_CLIENT_SECRET',
        'redirect_uri': 'http://localhost:8080/callback'
    }
    
    google_handler = oauth_registry.get_handler('google', google_config)
    print(f"\n2. ✅ Got Google OAuth handler: {type(google_handler).__name__}")
    
    # Get handler for another provider
    microsoft_config = {
        'client_id': 'MICROSOFT_CLIENT_ID',
        'client_secret': 'MICROSOFT_CLIENT_SECRET',
        'redirect_uri': 'http://localhost:8080/callback',
        'tenant': 'common'
    }
    
    microsoft_handler = oauth_registry.get_handler('microsoft', microsoft_config)
    print(f"3. ✅ Got Microsoft OAuth handler: {type(microsoft_handler).__name__}")
    
    # Check if provider is registered
    is_registered = oauth_registry.is_registered('google')
    print(f"\n4. Google is registered: {is_registered}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("  OsMEN OAuth Usage Examples")
    print("=" * 70)
    print("\nThese examples demonstrate how to use OAuth in OsMEN.")
    print("Replace placeholder credentials with your actual OAuth credentials.")
    print()
    
    examples = [
        ("Google OAuth Flow", example_google_oauth_flow, False),
        ("Microsoft OAuth Flow", example_microsoft_oauth_flow, False),
        ("Secure Token Storage", example_secure_token_storage, True),
        ("Automatic Token Refresh", example_automatic_token_refresh, True),
        ("Google Calendar API", example_google_calendar_api, False),
        ("Microsoft Mail API", example_microsoft_mail_api, False),
        ("Error Handling", example_error_handling, True),
        ("Multi-Provider Management", example_multi_provider_management, True),
    ]
    
    print("Available examples:")
    for i, (name, _, can_run) in enumerate(examples, 1):
        status = "✅ Runnable" if can_run else "⚠️  Needs credentials"
        print(f"  {i}. {name} - {status}")
    
    print()
    choice = input("Select an example to run (1-8, or 'all' for runnable examples): ").strip()
    
    if choice.lower() == 'all':
        for name, func, can_run in examples:
            if can_run:
                try:
                    func()
                except Exception as e:
                    print(f"\n❌ Example failed: {e}")
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        name, func, _ = examples[int(choice) - 1]
        try:
            func()
        except Exception as e:
            print(f"\n❌ Example failed: {e}")
    else:
        print("\n❌ Invalid choice")
    
    print("\n" + "=" * 70)
    print("  Examples Complete")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
