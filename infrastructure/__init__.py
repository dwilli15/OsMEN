"""
OsMEN Infrastructure Layer

Provides workspace-wide infrastructure awareness, health monitoring,
and dynamic context injection for all agents.

Key Components:
- context_injector: Automatic context injection for agent prompts
- nodes/registry.json: Service definitions and endpoints
- tools/inventory.json: Tool capabilities and health states
- graph/connections.json: Agent↔Tool↔Node↔Pipeline relationships
- profiles/policies.json: Workspace policies and permissions

Usage:
    from infrastructure import inject_context, with_infrastructure_context

    # Direct injection
    context = inject_context('librarian', 'Research task')

    # Decorator pattern
    @with_infrastructure_context('personal_assistant')
    async def process_request(self, query):
        # self._injected_context available here
        pass
"""

from .context_injector import (
    ContextInjector,
    InjectionConfig,
    InjectionRecord,
    get_injector,
    inject_context,
    with_infrastructure_context,
)

__all__ = [
    "ContextInjector",
    "InjectionConfig",
    "InjectionRecord",
    "get_injector",
    "inject_context",
    "with_infrastructure_context",
]

__version__ = "1.3.0"
