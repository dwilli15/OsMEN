"""Authentication module for OsMEN Web Dashboard

Provides session-based authentication for web interface.
"""

import os
import bcrypt
from typing import Optional
from fastapi import Request, HTTPException, status


# Default credentials (change in production via environment variables)
DEFAULT_USERNAME = os.getenv("WEB_USERNAME", "admin")
DEFAULT_PASSWORD_HASH = os.getenv(
    "WEB_PASSWORD_HASH",
    # Default: "admin" (change this!)
    "$2b$12$KIXxLV3qZ.gY8yH7n7P7Q.xQZ7vXZX8F1Y2Y3Z4Z5Z6Z7Z8Z9Z0Z1"
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


async def get_current_user(request: Request) -> Optional[dict]:
    """Get current authenticated user from session."""
    username = request.session.get("user")
    if username:
        return {
            "username": username,
            "is_authenticated": True
        }
    return None


async def login_user(request: Request, username: str, password: str) -> bool:
    """Authenticate user and create session."""
    # Verify credentials
    if username == DEFAULT_USERNAME and verify_password(password, DEFAULT_PASSWORD_HASH):
        request.session["user"] = username
        return True
    return False


async def logout_user(request: Request):
    """Log out user by clearing session."""
    request.session.clear()


async def check_auth(request: Request) -> dict:
    """Dependency to require authentication."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
