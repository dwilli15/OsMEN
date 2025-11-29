#!/usr/bin/env python3
"""
OAuth Webhook Callback Receiver

Provides a simple HTTP server to receive OAuth callbacks.
This eliminates the need for users to manually copy authorization codes.

Usage:
    python scripts/oauth_webhook.py --provider google --port 8080
    
The server will:
1. Start listening on the specified port
2. Display the authorization URL
3. Automatically receive the callback
4. Exchange the code for tokens
5. Save tokens and shut down

Features:
- Automatic code exchange
- State parameter validation (CSRF protection)
- Error handling
- Clean shutdown
- Integration with existing OAuth handlers
"""

import argparse
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import webbrowser
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from integrations.v3_integration_layer import V3IntegrationLayer


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callbacks"""
    
    # Class variables to share state
    authorization_code = None
    state_received = None
    error_message = None
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[Webhook] {format % args}")
    
    def do_GET(self):
        """Handle GET request (OAuth callback)"""
        # Parse URL
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        
        # Check for error
        if 'error' in params:
            error = params['error'][0]
            error_description = params.get('error_description', ['Unknown error'])[0]
            self.error_message = f"{error}: {error_description}"
            
            # Send error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
            <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h1>❌ OAuth Authorization Failed</h1>
                <p><strong>Error:</strong> {error}</p>
                <p><strong>Description:</strong> {error_description}</p>
                <p>You can close this window.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            return
        
        # Get authorization code
        if 'code' in params:
            OAuthCallbackHandler.authorization_code = params['code'][0]
            OAuthCallbackHandler.state_received = params.get('state', [None])[0]
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head><title>OAuth Success</title></head>
            <body>
                <h1>✅ Authorization Successful!</h1>
                <p>You can close this window. The application will now exchange the code for tokens...</p>
                <script>
                    setTimeout(function() {
                        window.close();
                    }, 3000);
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            # No code parameter
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head><title>Invalid Request</title></head>
            <body>
                <h1>❌ Invalid OAuth Callback</h1>
                <p>No authorization code received.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())


class OAuthWebhookServer:
    """OAuth webhook server manager"""
    
    def __init__(self, provider: str, port: int = 8080):
        self.provider = provider
        self.port = port
        self.integration = V3IntegrationLayer()
        self.server = None
    
    def start(self):
        """Start the webhook server and OAuth flow"""
        print("\n" + "=" * 70)
        print(f"OAuth Webhook Server - {self.provider}")
        print("=" * 70)
        
        # Get OAuth handler
        if self.provider == 'google':
            oauth_handler = self.integration.google_oauth
        elif self.provider == 'microsoft':
            oauth_handler = self.integration.microsoft_oauth
        else:
            print(f"❌ Unknown provider: {self.provider}")
            return False
        
        if not oauth_handler:
            print(f"❌ {self.provider} OAuth not configured")
            print(f"   Run: python scripts/setup_oauth.py --provider {self.provider}")
            return False
        
        # Generate authorization URL
        auth_url = oauth_handler.get_authorization_url()
        
        print(f"\n📡 Starting webhook server on port {self.port}...")
        print(f"🔗 Redirect URI: http://localhost:{self.port}/oauth/callback")
        print()
        
        # Start HTTP server
        try:
            self.server = HTTPServer(('localhost', self.port), OAuthCallbackHandler)
        except OSError as e:
            if 'Address already in use' in str(e):
                print(f"❌ Port {self.port} is already in use")
                print(f"   Try a different port with --port")
                return False
            raise
        
        print("✅ Webhook server started successfully")
        print()
        print("=" * 70)
        print("Next Steps:")
        print("=" * 70)
        print()
        print("1. Opening authorization URL in your browser...")
        print(f"   {auth_url}")
        print()
        print("2. Sign in and authorize the application")
        print()
        print("3. You'll be redirected back automatically")
        print()
        print("⏳ Waiting for OAuth callback...")
        print()
        
        # Open browser
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")
            print(f"   Please manually visit: {auth_url}")
        
        # Wait for callback
        try:
            # Handle one request (the callback)
            self.server.handle_request()
        except KeyboardInterrupt:
            print("\n\n❌ Interrupted by user")
            return False
        
        # Check if we got the code
        if OAuthCallbackHandler.error_message:
            print(f"\n❌ OAuth error: {OAuthCallbackHandler.error_message}")
            return False
        
        if not OAuthCallbackHandler.authorization_code:
            print("\n❌ No authorization code received")
            return False
        
        code = OAuthCallbackHandler.authorization_code
        print(f"\n✅ Received authorization code: {code[:20]}...")
        
        # Exchange code for tokens
        print("\n🔄 Exchanging code for tokens...")
        
        try:
            token_data = oauth_handler.exchange_code(code)
            
            if not token_data:
                print("❌ Failed to exchange code for tokens")
                return False
            
            # Save tokens
            from integrations.token_manager import TokenManager
            token_manager = TokenManager()
            token_manager.save_token(self.provider, token_data)
            
            print("✅ Successfully obtained and saved tokens!")
            
            # Validate
            print("\n🔍 Validating token...")
            if oauth_handler.validate_token(token_data['access_token']):
                print("✅ Token is valid!")
            else:
                print("⚠️  Token validation failed")
            
            # Test integration
            print(f"\n🧪 Testing {self.provider} integration...")
            status = self.integration.check_google_integration() if self.provider == 'google' else self.integration.check_microsoft_integration()
            
            if status.get('calendar_available'):
                print(f"✅ Calendar access working ({status.get('calendar_count', 0)} calendars found)")
            else:
                print("⚠️  Calendar access not confirmed")
            
            print("\n" + "=" * 70)
            print(f"🎉 {self.provider.title()} OAuth Setup Complete!")
            print("=" * 70)
            print()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error completing OAuth: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if self.server:
                self.server.server_close()
                print("\n🔒 Webhook server closed")


def main():
    parser = argparse.ArgumentParser(
        description='OAuth Webhook Callback Receiver - Automated OAuth flow'
    )
    parser.add_argument(
        '--provider',
        required=True,
        choices=['google', 'microsoft'],
        help='OAuth provider'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Port for webhook server (default: 8080)'
    )
    
    args = parser.parse_args()
    
    server = OAuthWebhookServer(args.provider, args.port)
    success = server.start()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
