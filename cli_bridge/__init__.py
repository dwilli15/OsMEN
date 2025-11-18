"""
CLI Bridge Module
Bridge between OsMEN and Codex CLI / Copilot CLI
"""

from .codex_bridge import CodexBridge
from .copilot_bridge import CopilotBridge
from .bridge_manager import CLIBridgeManager

__all__ = ['CodexBridge', 'CopilotBridge', 'CLIBridgeManager']
