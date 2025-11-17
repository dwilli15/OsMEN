#!/usr/bin/env python3
"""
OAuth Routes for Web Dashboard

Handles OAuth callback flows for GitHub Copilot and OpenAI.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import sys
from pathlib import Path

# Add integrations to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "integrations"))

from oauth.github_oauth import GitHubOAuthIntegration
from oauth.openai_oauth import OpenAIOAuthIntegration

router = APIRouter(prefix="/oauth", tags=["oauth"])

# Initialize OAuth integrations
github_oauth = GitHubOAuthIntegration()
openai_oauth = OpenAIOAuthIntegration()


@router.get("/github/login")
async def github_login(request: Request):
    """Initiate GitHub OAuth login flow"""
    # Generate state token and store in session
    import secrets
    state = secrets.token_urlsafe(32)
    request.session["github_oauth_state"] = state
    
    # Redirect to GitHub authorization page
    auth_url = github_oauth.get_authorization_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle GitHub OAuth callback"""
    # Check for errors
    if error:
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>GitHub OAuth Error</title></head>
                <body>
                    <h1>Authentication Error</h1>
                    <p>Error: {error}</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body>
            </html>
            """,
            status_code=400
        )
    
    # Verify state parameter (CSRF protection)
    stored_state = request.session.get("github_oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Exchange code for token
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    success = github_oauth.exchange_code_for_token(code)
    
    if success:
        # Store authentication status in session
        request.session["github_authenticated"] = True
        user_info = github_oauth.get_user_info()
        if user_info:
            request.session["github_username"] = user_info.get("login")
        
        return HTMLResponse(
            content=f"""
            <html>
                <head>
                    <title>GitHub OAuth Success</title>
                    <meta http-equiv="refresh" content="3;url=/dashboard">
                </head>
                <body style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
                    <h1 style="color: green;">✅ GitHub Authentication Successful</h1>
                    <p>You are now authenticated with GitHub Copilot.</p>
                    <p>Username: {user_info.get('login') if user_info else 'Unknown'}</p>
                    <p>Redirecting to dashboard...</p>
                    <p><a href="/dashboard">Go to Dashboard</a></p>
                </body>
            </html>
            """
        )
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>GitHub OAuth Failed</title></head>
                <body style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
                    <h1 style="color: red;">❌ Authentication Failed</h1>
                    <p>Failed to authenticate with GitHub.</p>
                    <p><a href="/oauth/github/login">Try Again</a></p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body>
            </html>
            """,
            status_code=400
        )


@router.get("/openai/login")
async def openai_login(request: Request):
    """Initiate OpenAI OAuth login flow"""
    # Generate state token and store in session
    import secrets
    state = secrets.token_urlsafe(32)
    request.session["openai_oauth_state"] = state
    
    # For OpenAI, we'll use API key authentication wrapped in OAuth-like flow
    # Redirect to API key entry page
    return HTMLResponse(
        content="""
        <html>
            <head>
                <title>OpenAI API Key</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                    input[type="password"] { width: 100%; padding: 10px; margin: 10px 0; }
                    button { background: #10a37f; color: white; padding: 10px 20px; border: none; cursor: pointer; }
                    button:hover { background: #0d8566; }
                </style>
            </head>
            <body>
                <h1>OpenAI API Key Authentication</h1>
                <p>Enter your OpenAI API key to authenticate:</p>
                <form action="/oauth/openai/callback" method="post">
                    <input type="password" name="api_key" placeholder="sk-..." required>
                    <br>
                    <button type="submit">Authenticate</button>
                </form>
                <p><small>Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a></small></p>
                <p><a href="/dashboard">Cancel</a></p>
            </body>
        </html>
        """
    )


@router.post("/openai/callback")
async def openai_callback(request: Request):
    """Handle OpenAI API key submission"""
    from fastapi import Form
    
    # Get form data
    form_data = await request.form()
    api_key = form_data.get("api_key")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    # Set the API key
    success = openai_oauth.set_api_key(api_key)
    
    if success:
        # Store authentication status in session
        request.session["openai_authenticated"] = True
        
        return HTMLResponse(
            content="""
            <html>
                <head>
                    <title>OpenAI Authentication Success</title>
                    <meta http-equiv="refresh" content="3;url=/dashboard">
                </head>
                <body style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
                    <h1 style="color: green;">✅ OpenAI Authentication Successful</h1>
                    <p>Your API key has been validated and stored securely.</p>
                    <p>Redirecting to dashboard...</p>
                    <p><a href="/dashboard">Go to Dashboard</a></p>
                </body>
            </html>
            """
        )
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>OpenAI Authentication Failed</title></head>
                <body style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
                    <h1 style="color: red;">❌ Authentication Failed</h1>
                    <p>Invalid API key. Please check and try again.</p>
                    <p><a href="/oauth/openai/login">Try Again</a></p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body>
            </html>
            """,
            status_code=400
        )


@router.get("/status")
async def oauth_status(request: Request):
    """Check OAuth authentication status"""
    return {
        "github": {
            "authenticated": request.session.get("github_authenticated", False),
            "username": request.session.get("github_username"),
            "valid_token": github_oauth.is_authenticated()
        },
        "openai": {
            "authenticated": request.session.get("openai_authenticated", False),
            "valid_token": openai_oauth.is_authenticated()
        }
    }


@router.post("/github/logout")
async def github_logout(request: Request):
    """Logout from GitHub OAuth"""
    github_oauth.logout()
    request.session.pop("github_authenticated", None)
    request.session.pop("github_username", None)
    return {"status": "logged_out"}


@router.post("/openai/logout")
async def openai_logout(request: Request):
    """Logout from OpenAI"""
    openai_oauth.logout()
    request.session.pop("openai_authenticated", None)
    return {"status": "logged_out"}
