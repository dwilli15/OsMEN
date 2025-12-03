"""Authentication and authorization helpers for the OsMEN web dashboard."""

from __future__ import annotations

import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import bcrypt
from fastapi import Depends, HTTPException, Request, status

ADMIN_USERNAME = os.getenv("WEB_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv(
    "WEB_ADMIN_PASSWORD_HASH",
    "$2b$12$M.YlE8WZR5bIjFvxpGmwveKsM/ib4zbB4i.ehYDbvvbA3r0aypkdG",
)
ADMIN_ROLE = os.getenv("WEB_ADMIN_ROLE", "admin")
DEFAULT_ROLE = os.getenv("WEB_DEFAULT_ROLE", "viewer")
SESSION_MAX_AGE = int(os.getenv("SESSION_COOKIE_MAX_AGE", "3600"))
MAX_ATTEMPTS = int(os.getenv("WEB_LOGIN_MAX_ATTEMPTS", "5"))
ATTEMPT_WINDOW = int(os.getenv("WEB_LOGIN_WINDOW_SECONDS", "60"))

ACCESS_CONTROL_PATH = Path(__file__).resolve().parent.parent / "config" / "access_control.json"

_login_attempts: Dict[str, List[float]] = {}
_access_cache: Dict[str, Any] | None = None
_access_mtime: float = 0.0


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def _load_access_control() -> Dict[str, Any]:
    try:
        with ACCESS_CONTROL_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"roles": {}, "users": []}


def _get_access_control() -> Dict[str, Any]:
    global _access_cache, _access_mtime
    try:
        mtime = ACCESS_CONTROL_PATH.stat().st_mtime
    except FileNotFoundError:
        mtime = 0.0
    if _access_cache is None or mtime > _access_mtime:
        _access_cache = _load_access_control()
        _access_mtime = mtime
    return _access_cache or {"roles": {}, "users": []}


def _get_roles() -> Dict[str, Dict[str, Any]]:
    return _get_access_control().get("roles", {})


def _get_role_for_user(username: str) -> str:
    config = _get_access_control()
    for entry in config.get("users", []):
        if entry.get("username") == username:
            return entry.get("role", DEFAULT_ROLE)
    if username == ADMIN_USERNAME:
        return ADMIN_ROLE
    return DEFAULT_ROLE


def _resolve_permissions(role: str, visited: Optional[Set[str]] = None) -> Set[str]:
    roles = _get_roles()
    visited = visited or set()
    if role not in roles or role in visited:
        return set()
    visited.add(role)
    permissions = set(roles[role].get("permissions", []))
    for parent in roles[role].get("inherits", []):
        permissions |= _resolve_permissions(parent, visited)
    return permissions


def _role_inherits(role: str, target: str, visited: Optional[Set[str]] = None) -> bool:
    if role == target:
        return True
    roles = _get_roles()
    visited = visited or set()
    if role in visited:
        return False
    visited.add(role)
    for parent in roles.get(role, {}).get("inherits", []):
        if _role_inherits(parent, target, visited):
            return True
    return False


def _prune_attempts(bucket: str) -> List[float]:
    now = time.time()
    attempts = _login_attempts.get(bucket, [])
    attempts = [ts for ts in attempts if now - ts < ATTEMPT_WINDOW]
    _login_attempts[bucket] = attempts
    return attempts


def _attempt_bucket(request: Request, username: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{username}:{host}"


def ensure_csrf_token(request: Request) -> str:
    """Ensure a CSRF token exists for the current session."""
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def validate_csrf(request: Request, token: Optional[str]) -> None:
    """Validate CSRF tokens found in headers or form data."""
    expected = request.session.get("csrf_token")
    if not expected or not token or not hmac.compare_digest(expected, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )


def _session_expired(session: Dict[str, Any]) -> bool:
    last_active = session.get("last_active")
    now = time.time()
    if last_active is None:
        session["last_active"] = now
        return False
    if now - last_active > SESSION_MAX_AGE:
        return True
    session["last_active"] = now
    return False


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Return authenticated user payload if a valid session exists."""
    stored = request.session.get("user")
    if not stored:
        return None
    if _session_expired(request.session):
        request.session.clear()
        return None

    if isinstance(stored, str):
        username = stored
        role = _get_role_for_user(username)
    else:
        username = stored.get("username")
        role = stored.get("role") or _get_role_for_user(username or "")

    if not username:
        request.session.clear()
        return None

    permissions = sorted(_resolve_permissions(role))
    user = {
        "username": username,
        "role": role or DEFAULT_ROLE,
        "permissions": permissions,
        "is_authenticated": True,
    }
    request.session["user"] = {"username": username, "role": user["role"]}
    request.session["permissions"] = permissions
    return user


async def login_user(request: Request, username: str, password: str) -> bool:
    """Authenticate a user with rate limiting."""
    bucket = _attempt_bucket(request, username)
    attempts = _prune_attempts(bucket)
    if len(attempts) >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )

    if username == ADMIN_USERNAME and verify_password(password, ADMIN_PASSWORD_HASH):
        role = _get_role_for_user(username)
        request.session["user"] = {"username": username, "role": role}
        request.session["permissions"] = sorted(_resolve_permissions(role))
        request.session["last_active"] = time.time()
        ensure_csrf_token(request)
        _login_attempts[bucket] = []
        return True

    attempts.append(time.time())
    _login_attempts[bucket] = attempts
    return False


async def logout_user(request: Request) -> None:
    """Clear session data for the current user."""
    request.session.clear()


async def check_auth(request: Request) -> Dict[str, Any]:
    """Dependency enforcing authentication."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Session"},
        )
    return user


def role_required(required: str):
    """Dependency factory enforcing a role or permission."""

    async def dependency(user: Dict[str, Any] = Depends(check_auth)) -> Dict[str, Any]:
        role = user.get("role", DEFAULT_ROLE)
        if required in _get_roles():
            if not _role_inherits(role, required):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{required} role required",
                )
        else:
            permissions = set(user.get("permissions", []))
            if required not in permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{required} permission required",
                )
        return user

    return dependency
