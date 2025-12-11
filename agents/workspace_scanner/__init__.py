"""
OsMEN Workspace Scanner Agent

Creates and maintains a dynamic, living map of the entire workspace.
Provides complete workspace awareness to all agents.
"""

from .workspace_scanner_agent import (
    AgentInstructionFile,
    Capability,
    ComponentType,
    DirectoryInfo,
    FileInfo,
    WorkspaceMap,
    WorkspaceScannerAgent,
    detect_capabilities,
    detect_component_type,
)

__all__ = [
    "WorkspaceScannerAgent",
    "WorkspaceMap",
    "FileInfo",
    "DirectoryInfo",
    "AgentInstructionFile",
    "ComponentType",
    "Capability",
    "detect_capabilities",
    "detect_component_type",
]
