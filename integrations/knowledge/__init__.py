"""
Knowledge and task management integrations.
Supports Notion, Todoist, and Obsidian synchronization.
"""

# Import with error handling to avoid issues with missing dependencies
try:
    from .notion_client import NotionClient
except ImportError as e:
    print(f"Warning: Could not import NotionClient: {e}")
    NotionClient = None

try:
    from .todoist_client import TodoistClient
except ImportError as e:
    print(f"Warning: Could not import TodoistClient: {e}")
    TodoistClient = None

try:
    from .obsidian_sync import ObsidianSync
except ImportError as e:
    print(f"Warning: Could not import ObsidianSync: {e}")
    ObsidianSync = None

try:
    from .sync_engine import SyncEngine
except ImportError as e:
    print(f"Warning: Could not import SyncEngine: {e}")
    SyncEngine = None

__all__ = [
    'NotionClient',
    'TodoistClient',
    'ObsidianSync',
    'SyncEngine',
]
