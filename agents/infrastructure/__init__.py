"""
Infrastructure Agent for OsMEN Workspace

Manages node registry, tool inventory, connection graph, and provides
dynamic context injection for agent awareness.
"""

from .infrastructure_agent import InfrastructureAgent

__all__ = ["InfrastructureAgent"]
