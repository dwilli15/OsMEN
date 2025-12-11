"""
OsMEN Path Constants
Canonical source of all file system paths used by OsMEN

This module is imported by both orchestration.py and logging_system.py
to avoid circular imports while maintaining a single source of truth.
"""

from pathlib import Path

# =============================================================================
# ROOT PATHS
# =============================================================================
OSMEN_ROOT = Path("D:/OsMEN")
CONTENT_ROOT = OSMEN_ROOT / "content"
LOGS_ROOT = OSMEN_ROOT / "logs"
AGENTS_ROOT = OSMEN_ROOT / "agents"
INTEGRATIONS_ROOT = OSMEN_ROOT / "integrations"

# =============================================================================
# COURSE PATHS
# =============================================================================
HB411_ROOT = CONTENT_ROOT / "courses/HB411_HealthyBoundaries"
HB411_OBSIDIAN = HB411_ROOT / "obsidian"
HB411_AUDIOBOOKS = HB411_ROOT / "audiobooks"
HB411_SCRIPTS = HB411_ROOT / "audio/scripts"
HB411_RAG = HB411_ROOT / "rag_sources"

# =============================================================================
# VAULT PATHS
# =============================================================================
VAULT_ROOT = HB411_OBSIDIAN
VAULT_TEMPLATES = VAULT_ROOT / "_templates"
VAULT_DAILY = VAULT_ROOT / "daily-notes"
VAULT_WEEKLY = VAULT_ROOT / "weekly-notes"
VAULT_PROGRESS = VAULT_ROOT / "progress-tracking"
VAULT_RESOURCES = VAULT_ROOT / "resources"
VAULT_CHAPTERS = VAULT_ROOT / "chapters"

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
TEMPLATE_AM_CHECKIN = VAULT_TEMPLATES / "am-check-in.md"
TEMPLATE_PM_CHECKIN = VAULT_TEMPLATES / "pm-check-in.md"
TEMPLATE_WEEKLY_REVIEW = VAULT_TEMPLATES / "weekly-review.md"
TEMPLATE_DAILY_NOTE = VAULT_TEMPLATES / "daily-note.md"
TEMPLATE_BRIEFING = VAULT_TEMPLATES / "daily-briefing.md"
TEMPLATE_PODCAST = VAULT_TEMPLATES / "podcast-episode.md"

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
        "CONTENT_ROOT": CONTENT_ROOT,
        "LOGS_ROOT": LOGS_ROOT,
        "AGENTS_ROOT": AGENTS_ROOT,
        "HB411_OBSIDIAN": HB411_OBSIDIAN,
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
        status = "✅" if info["exists"] else "❌"
        print(f"{status} {name}: {info['path']}")
