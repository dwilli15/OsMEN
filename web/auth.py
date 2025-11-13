"""Authentication and authorization utilities for the OsMEN dashboard."""

import json
import os
import secrets
import time
from collections import defaultdict, deque
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional

import bcrypt
from fastapi import HTTPException, Request, status


ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
ROOT_DIR = Path(__file__).resolve().parent.parent
ACCESS_CONTROL_PATH = ROOT_DIR / "config" / "access_control.json"
ROLE_PRIORITY = {"viewer": 0, "operator": 1, "admin": 2}
WEB_ADMIN_ROLE = os.getenv("WEB_ADMIN_ROLE", "admin")
WEB_DEFAULT_ROLE = os.getenv("WEB_DEFAULT_ROLE", "viewer")
CSRF_SESSION_KEY = "csrf_token"
LOGIN_MAX_ATTEMPTS = int(os.getenv("WEB_LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_WINDOW_SECONDS = int(os.getenv("WEB_LOGIN_WINDOW_SECONDS", "60"))
_LOGIN_ATTEMPTS = defaultdict(deque)


def _get_admin_credential(var_name: str, default: str) -> str:
    """Load admin credentials, enforcing explicit values for production."""
    value = os.getenv(var_name)
    if value:
        return value
    if ENVIRONMENT == "production":
        raise RuntimeError(f"{var_name} must be set via environment in production deployments.")
    return default


@lru_cache()
def _load_access_control() -> dict:
    """Load access-control configuration."""
    if ACCESS_CONTROL_PATH.exists():
        try:
            return json.loads(ACCESS_CONTROL_PATH.read_text())
        except json.JSONDecodeError as exc:
            raise RuntimeError("config/access_control.json is invalid JSON") from exc
    return {
        "roles": {
            "viewer": {},
            "operator": {},
            "admin": {}
        },
        "users": [
            {"username": DEFAULT_USERNAME, "role": WEB_ADMIN_ROLE}
        ]
    }


def _resolve_role(username: str) -> str:
    config = _load_access_control()
    for entry in config.get("users", []):
        if entry.get("username", "").lower() == username.lower():
            return entry.get("role", WEB_DEFAULT_ROLE)
    if username == DEFAULT_USERNAME:
        return WEB_ADMIN_ROLE
    return WEB_DEFAULT_ROLE


def _role_allows(user_role: str, required_role: str) -> bool:
    return ROLE_PRIORITY.get(user_role, 0) >= ROLE_PRIORITY.get(required_role, 0)


def role_required(required_role: str) -> Callable:
    """FastAPI dependency enforcing role requirements."""
    async def dependency(request: Request) -> dict:
        user = await check_auth(request)
        user_role = user.get("role", WEB_DEFAULT_ROLE)
        if not _role_allows(user_role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role"
            )
        return user
    return dependency


def ensure_csrf_token(request: Request) -> str:
    """Return (and persist) CSRF token for the current session."""
    token = request.session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[CSRF_SESSION_KEY] = token
    return token


def validate_csrf(request: Request, supplied_token: Optional[str] = None) -> None:
    """Validate CSRF token from header or form-data."""
    session_token = request.session.get(CSRF_SESSION_KEY)
    candidate = supplied_token or request.headers.get("X-CSRF-Token")
    if not session_token or not candidate or not secrets.compare_digest(session_token, candidate):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )


def enforce_login_rate_limit(request: Request) -> None:
    """Rate-limit login attempts per client IP."""
    client_ip = (request.client.host if request.client else "unknown") or "unknown"
    attempts = _LOGIN_ATTEMPTS[client_ip]
    now = time.monotonic()
    while attempts and now - attempts[0] > LOGIN_WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait and try again."
        )
    attempts.append(now)


# Default credentials
DEFAULT_USERNAME = _get_admin_credential("WEB_ADMIN_USERNAME", "admin")
DEFAULT_PASSWORD_HASH = _get_admin_credential(
    "WEB_ADMIN_PASSWORD_HASH",
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
    """Return the authenticated user (if any)."""
    username = request.session.get("user")
    if username:
        role = request.session.get("role") or _resolve_role(username)
        request.session["role"] = role
        return {
            "username": username,
            "role": role,
            "is_authenticated": True
        }
    return None


async def login_user(request: Request, username: str, password: str) -> bool:
    """Authenticate user and create session."""
    enforce_login_rate_limit(request)
    if username == DEFAULT_USERNAME and verify_password(password, DEFAULT_PASSWORD_HASH):
        role = _resolve_role(username)
        request.session["user"] = username
        request.session["role"] = role
        ensure_csrf_token(request)
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
