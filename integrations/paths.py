"""integrations.paths

Canonical source of file system paths used by OsMEN.

Key rule (per temp_spec): semester/course artifacts MUST live outside the repo.
This module therefore supports an external "semester workspace" and provides
validation helpers to prevent writing semester artifacts inside the repo.

This module is imported by orchestration.py and logging_system.py; keep it
stdlib-only to avoid circular imports.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class WorkspaceNotConfiguredError(RuntimeError):
    """Raised when a required external semester workspace is missing."""


class InvalidWorkspaceError(ValueError):
    """Raised when a provided workspace path is invalid (e.g., inside repo)."""


# =============================================================================
# ROOT PATHS (repo-internal; safe)
# =============================================================================

# Resolve repo root dynamically instead of hardcoding a drive path.
# File location: <repo>/integrations/paths.py
OSMEN_ROOT = Path(__file__).resolve().parents[1]

CONTENT_ROOT = OSMEN_ROOT / "content"  # product assets only (NOT semester artifacts)
LOGS_ROOT = OSMEN_ROOT / "logs"
AGENTS_ROOT = OSMEN_ROOT / "agents"
INTEGRATIONS_ROOT = OSMEN_ROOT / "integrations"

# Product-shipped templates (safe fallback)
PRODUCT_TEMPLATES_ROOT = OSMEN_ROOT / "templates"


def _is_within(child: Path, parent: Path) -> bool:
    """Return True if child is the same as or inside parent."""
    try:
        child = child.resolve()
        parent = parent.resolve()
    except Exception:
        # If resolution fails, be conservative and treat as within.
        return True

    return child == parent or parent in child.parents


def validate_external_workspace(path: Path) -> Path:
    """Validate that workspace path is outside the repo.

    This is the primary repo-hygiene guardrail.
    """
    path = Path(path).expanduser().resolve()
    if _is_within(path, OSMEN_ROOT):
        raise InvalidWorkspaceError(
            f"Semester workspace must be outside the repo ({OSMEN_ROOT}). Got: {path}"
        )
    return path


def get_semester_workspace(required: bool = False) -> Optional[Path]:
    """Return external semester workspace if configured.

    Set via env var `OSMEN_SEMESTER_WORKSPACE`.
    """
    raw = os.getenv("OSMEN_SEMESTER_WORKSPACE", "").strip()
    if not raw:
        if required:
            raise WorkspaceNotConfiguredError(
                "External semester workspace not configured. "
                "Set OSMEN_SEMESTER_WORKSPACE to a folder outside the repo (e.g. D:\\semester_start)."
            )
        return None

    return validate_external_workspace(Path(raw))


# =============================================================================
# SEMESTER / COURSE PATHS (external; preferred)
# =============================================================================

# Legacy defaults (kept for backward compatibility only). These should NOT be
# used for new semester operations.
_LEGACY_HB411_ROOT = CONTENT_ROOT / "courses/HB411_HealthyBoundaries"


def get_vault_root(required: bool = False) -> Path:
    """Return vault root inside external workspace (preferred) or legacy path."""
    ws = get_semester_workspace(required=required)
    if ws is None:
        return _LEGACY_HB411_ROOT / "obsidian"
    return ws / "vault"


def get_course_root(course_code: str, required: bool = False) -> Path:
    """Return course root inside external workspace vault."""
    vault_root = get_vault_root(required=required)
    # Standard external layout: <workspace>/vault/courses/<CODE>
    return vault_root / "courses" / course_code


# Exported course paths (HB411) — resolve via external workspace when configured.
_vault_root = get_vault_root(required=False)
HB411_ROOT = (
    get_course_root("HB411", required=False)
    if get_semester_workspace(required=False)
    else _LEGACY_HB411_ROOT
)
HB411_OBSIDIAN = _vault_root
HB411_AUDIOBOOKS = (
    (get_semester_workspace(required=False) / "audiobooks")
    if get_semester_workspace(required=False)
    else _LEGACY_HB411_ROOT / "audiobooks"
)
HB411_SCRIPTS = (
    (get_semester_workspace(required=False) / "vault" / "audio" / "weekly_scripts")
    if get_semester_workspace(required=False)
    else _LEGACY_HB411_ROOT / "audio" / "scripts"
)
HB411_RAG = (
    (get_semester_workspace(required=False) / "vault" / "readings")
    if get_semester_workspace(required=False)
    else _LEGACY_HB411_ROOT / "rag_sources"
)

# =============================================================================
# VAULT PATHS
# =============================================================================

VAULT_ROOT = get_vault_root(required=False)

# External standard layout uses `templates/`, not Obsidian's `_templates/`.
# Keep a safe fallback to product-shipped templates.
VAULT_TEMPLATES = (
    VAULT_ROOT / "templates"
    if get_semester_workspace(required=False)
    else (VAULT_ROOT / "_templates")
)
VAULT_DAILY = VAULT_ROOT / "journal" / "daily"
VAULT_WEEKLY = VAULT_ROOT / "journal" / "weekly"
VAULT_PROGRESS = VAULT_ROOT / "journal" / "weekly"  # legacy-compatible alias
VAULT_RESOURCES = VAULT_ROOT / "resources"
VAULT_CHAPTERS = VAULT_ROOT / "courses"

# =============================================================================
# LOG DIRECTORIES
# =============================================================================
LOG_AGENT_SESSIONS = LOGS_ROOT / "agent_sessions"
LOG_CHECK_INS = LOGS_ROOT / "check_ins"
LOG_AUDIO_GENERATIONS = LOGS_ROOT / "audio_generations"
LOG_SYSTEM_EVENTS = LOGS_ROOT / "system_events"

# =============================================================================
# TEMPLATE FILES
# =============================================================================


def _template_root() -> Path:
    # Prefer external workspace templates; else use product templates.
    if get_semester_workspace(required=False):
        return VAULT_TEMPLATES
    return PRODUCT_TEMPLATES_ROOT


TEMPLATE_AM_CHECKIN = _template_root() / "AM Check-In.md"
TEMPLATE_PM_CHECKIN = _template_root() / "PM Check-In.md"
TEMPLATE_WEEKLY_REVIEW = _template_root() / "Weekly Review.md"
TEMPLATE_DAILY_NOTE = _template_root() / "Daily Note.md"
TEMPLATE_BRIEFING = _template_root() / "Daily Briefing Script.md"
TEMPLATE_PODCAST = _template_root() / "Weekly Podcast Script.md"

# =============================================================================
# TRACKER FILES
# =============================================================================
TRACKER_PROGRESS = VAULT_PROGRESS / "progress-tracker.md"
TRACKER_READINGS = VAULT_PROGRESS / "readings-tracker.md"
TRACKER_METRICS = VAULT_PROGRESS / "metrics-tracker.md"

# =============================================================================
# WORKFLOW FILES
# =============================================================================
N8N_WORKFLOWS = OSMEN_ROOT / "n8n/workflows"
LANGFLOW_FLOWS = OSMEN_ROOT / "langflow/flows"


# =============================================================================
# ENSURE LOG DIRECTORIES EXIST
# =============================================================================
def ensure_log_dirs():
    """Create all log directories if they don't exist"""
    for d in [
        LOG_AGENT_SESSIONS,
        LOG_CHECK_INS,
        LOG_AUDIO_GENERATIONS,
        LOG_SYSTEM_EVENTS,
    ]:
        d.mkdir(parents=True, exist_ok=True)


# Auto-create on import
ensure_log_dirs()


# =============================================================================
# PATH VALIDATION
# =============================================================================
def validate_critical_paths() -> dict:
    """Validate that critical paths exist"""
    critical = {
        "OSMEN_ROOT": OSMEN_ROOT,
        "LOGS_ROOT": LOGS_ROOT,
        "AGENTS_ROOT": AGENTS_ROOT,
        "INTEGRATIONS_ROOT": INTEGRATIONS_ROOT,
        "N8N_WORKFLOWS": N8N_WORKFLOWS,
        "LANGFLOW_FLOWS": LANGFLOW_FLOWS,
        "SEMESTER_WORKSPACE": get_semester_workspace(required=False) or Path(""),
        "VAULT_ROOT": VAULT_ROOT,
        "VAULT_TEMPLATES": VAULT_TEMPLATES,
    }

    results = {}
    for name, path in critical.items():
        results[name] = {
            "path": str(path),
            "exists": path.exists(),
            "is_dir": path.is_dir() if path.exists() else None,
        }
    return results


if __name__ == "__main__":
    print("OsMEN Path Constants")
    print("=" * 60)

    validation = validate_critical_paths()
    for name, info in validation.items():
        status = "✅" if info["exists"] else "⚠️"
        print(f"{status} {name}: {info['path']}")
