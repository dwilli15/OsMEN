#!/usr/bin/env python3
"""
Dynamic Context Injector for OsMEN Workspace

Provides automatic infrastructure awareness injection into agent prompts.
Implements pre-hooks (before agent execution) and post-hooks (logging outcomes).

This module is the bridge between the Infrastructure Agent's knowledge and
every agent's execution context.
"""

import asyncio
import functools
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.infrastructure.infrastructure_agent import InfrastructureAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class InjectionConfig:
    """Configuration for context injection"""

    max_context_tokens: int = 2000
    include_capabilities: bool = True
    include_constraints: bool = True
    include_recent_memories: bool = True
    memory_recency_hours: int = 24
    log_injections: bool = True
    audit_file: str = "logs/context_injections.jsonl"


@dataclass
class InjectionRecord:
    """Record of a context injection"""

    timestamp: str
    agent_id: str
    task_description: Optional[str]
    context_tokens: int
    sources: List[str]
    duration_ms: float
    success: bool
    error: Optional[str] = None


class ContextInjector:
    """
    Dynamic Context Injector for workspace-wide agent awareness.

    Responsibilities:
    - Pre-hook: Generate and inject context before agent execution
    - Post-hook: Log results and capture outcomes for learning
    - Memory integration: Include relevant recent memories
    - Audit logging: Track all injections for debugging

    Usage:
        injector = ContextInjector()

        # Method 1: Direct injection
        context = injector.inject_context('librarian', 'Find research papers')

        # Method 2: Decorator for agent methods
        @injector.with_context('personal_assistant')
        async def process_request(self, user_input):
            # self._injected_context is available here
            pass
    """

    _instance: Optional["ContextInjector"] = None

    def __new__(cls):
        """Singleton pattern for global context injector."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the context injector."""
        if self._initialized:
            return

        self.base_path = Path(__file__).parent.parent
        self.config = self._load_config()
        self.infrastructure = InfrastructureAgent()
        self.injection_records: List[InjectionRecord] = []

        # Ensure audit directory exists
        audit_dir = self.base_path / Path(self.config.audit_file).parent
        audit_dir.mkdir(parents=True, exist_ok=True)

        self._initialized = True
        logger.info("ContextInjector initialized (singleton)")

    def _load_config(self) -> InjectionConfig:
        """Load injection configuration from policies."""
        policies_path = self.base_path / "infrastructure" / "profiles" / "policies.json"

        if policies_path.exists():
            with open(policies_path, "r") as f:
                policies = json.load(f)

            config_data = policies.get("workspace_policies", {}).get(
                "context_injection", {}
            )
            return InjectionConfig(
                max_context_tokens=config_data.get("max_context_tokens", 2000),
                include_capabilities=config_data.get("include_capabilities", True),
                include_constraints=config_data.get("include_constraints", True),
                include_recent_memories=config_data.get(
                    "include_recent_memories", True
                ),
                memory_recency_hours=config_data.get("memory_recency_hours", 24),
                log_injections=config_data.get("log_injections", True),
                audit_file=config_data.get(
                    "audit_file", "logs/context_injections.jsonl"
                ),
            )

        return InjectionConfig()

    # =========================================================================
    # Pre-Hook: Context Injection
    # =========================================================================

    def inject_context(
        self,
        agent_id: str,
        task_description: Optional[str] = None,
        include_memories: bool = None,
    ) -> Dict[str, Any]:
        """
        Generate and return infrastructure context for an agent.

        This is the main pre-hook method that should be called before
        agent execution.

        Args:
            agent_id: ID of the agent requesting context
            task_description: Optional description of the current task
            include_memories: Override config for memory inclusion

        Returns:
            Dictionary with context to inject into agent prompt
        """
        import time

        start_time = time.time()

        try:
            # Get infrastructure context
            context = self.infrastructure.generate_context_for_agent(
                agent_id=agent_id,
                task_description=task_description,
                max_tokens=self.config.max_context_tokens,
            )

            # Optionally add recent memories
            should_include_memories = (
                include_memories
                if include_memories is not None
                else self.config.include_recent_memories
            )

            if should_include_memories:
                memories = self._get_recent_memories(agent_id)
                if memories:
                    context["recent_memories"] = memories

            # Add workspace map summary if available
            workspace_summary = self._get_workspace_summary()
            if workspace_summary:
                context["workspace_map"] = workspace_summary

            # Add formatted prompt string
            context["_formatted_prompt"] = self.infrastructure.format_context_as_prompt(
                context
            )

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log injection
            if self.config.log_injections:
                self._log_injection(
                    agent_id=agent_id,
                    task_description=task_description,
                    context=context,
                    duration_ms=duration_ms,
                    success=True,
                )

            return context

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Context injection failed for {agent_id}: {e}")

            if self.config.log_injections:
                self._log_injection(
                    agent_id=agent_id,
                    task_description=task_description,
                    context={},
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e),
                )

            # Return minimal context on failure
            return {
                "_formatted_prompt": "## Workspace Context Unavailable\nInfrastructure context could not be loaded.",
                "_error": str(e),
            }

    def inject_context_to_messages(
        self,
        messages: List[Dict[str, str]],
        agent_id: str,
        task_description: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Inject context into a messages list (for chat-style APIs).

        Adds infrastructure context as a system message at the beginning.

        Args:
            messages: List of message dicts with 'role' and 'content'
            agent_id: ID of the agent
            task_description: Optional task description

        Returns:
            Modified messages list with context injected
        """
        context = self.inject_context(agent_id, task_description)
        formatted = context.get("_formatted_prompt", "")

        if not formatted:
            return messages

        # Check if there's already a system message
        if messages and messages[0].get("role") == "system":
            # Append to existing system message
            messages[0]["content"] = formatted + "\n\n" + messages[0]["content"]
        else:
            # Insert new system message
            messages.insert(0, {"role": "system", "content": formatted})

        return messages

    def _get_recent_memories(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get recent relevant memories for an agent."""
        memories = []

        # Check memories directory
        memories_path = self.base_path / "knowledge" / "memories"
        if not memories_path.exists():
            return memories

        # Load recent memory files
        cutoff = datetime.now().timestamp() - (self.config.memory_recency_hours * 3600)

        for memory_file in memories_path.glob("*.json"):
            try:
                stat = memory_file.stat()
                if stat.st_mtime > cutoff:
                    with open(memory_file, "r") as f:
                        memory_data = json.load(f)

                    # Filter by relevance to agent if metadata available
                    if "agent" in memory_data:
                        if memory_data["agent"] != agent_id:
                            continue

                    memories.append(
                        {
                            "id": memory_file.stem,
                            "content": memory_data.get(
                                "content", memory_data.get("summary", "")
                            ),
                            "timestamp": memory_data.get("timestamp", stat.st_mtime),
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to load memory {memory_file}: {e}")

        # Sort by timestamp, most recent first
        memories.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        # Limit to prevent context overflow
        return memories[:5]

    def _get_workspace_summary(self) -> Optional[Dict[str, Any]]:
        """Get workspace map summary for context injection."""
        if (
            not hasattr(self.infrastructure, "workspace_map")
            or not self.infrastructure.workspace_map
        ):
            # Try to reload
            if hasattr(self.infrastructure, "reload_workspace_map"):
                self.infrastructure.reload_workspace_map()

        if not self.infrastructure.workspace_map:
            return None

        wm = self.infrastructure.workspace_map
        capabilities = wm.get("capabilities", {})

        # Create a compact summary for injection
        return {
            "total_files": wm.get("total_files", 0),
            "total_agents": wm.get("total_agents", 0),
            "total_capabilities": wm.get("total_capabilities", 0),
            "top_capabilities": sorted(
                [(k, len(v)) for k, v in capabilities.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
            "last_scan": wm.get("last_updated", wm.get("generated_at", "unknown")),
        }

    # =========================================================================
    # Post-Hook: Logging and Audit
    # =========================================================================

    def _log_injection(
        self,
        agent_id: str,
        task_description: Optional[str],
        context: Dict[str, Any],
        duration_ms: float,
        success: bool,
        error: Optional[str] = None,
    ):
        """Log an injection for audit purposes."""
        # Estimate tokens
        context_tokens = len(json.dumps(context)) // 4

        # Create record
        record = InjectionRecord(
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            task_description=task_description,
            context_tokens=context_tokens,
            sources=["infrastructure", "policies", "memories"] if success else [],
            duration_ms=duration_ms,
            success=success,
            error=error,
        )

        # Store in memory
        self.injection_records.append(record)
        if len(self.injection_records) > 1000:
            self.injection_records = self.injection_records[-1000:]

        # Write to audit file
        audit_path = self.base_path / self.config.audit_file
        try:
            with open(audit_path, "a") as f:
                f.write(json.dumps(asdict(record)) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")

    def log_outcome(
        self,
        agent_id: str,
        task_description: str,
        outcome: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log the outcome of an agent execution (post-hook).

        This should be called after agent execution to capture
        whether the injected context was helpful.

        Args:
            agent_id: ID of the agent
            task_description: What the agent was doing
            outcome: Description of what happened
            success: Whether the task succeeded
            metadata: Additional outcome data
        """
        outcome_record = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "task": task_description,
            "outcome": outcome,
            "success": success,
            "metadata": metadata or {},
        }

        # Write to outcomes log
        outcomes_path = self.base_path / "logs" / "agent_outcomes.jsonl"
        try:
            with open(outcomes_path, "a") as f:
                f.write(json.dumps(outcome_record) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write outcome log: {e}")

    # =========================================================================
    # Decorator for Agent Methods
    # =========================================================================

    def with_context(self, agent_id: str):
        """
        Decorator to automatically inject context into agent methods.

        The decorated method will have `self._injected_context` available.

        Usage:
            @injector.with_context('librarian')
            async def process_query(self, query: str):
                context = self._injected_context
                # Use context in processing
        """

        def decorator(func: F) -> F:
            @functools.wraps(func)
            async def async_wrapper(self_arg, *args, **kwargs):
                # Get task description from first positional arg if string
                task_desc = args[0] if args and isinstance(args[0], str) else None

                # Inject context
                context = self.inject_context(agent_id, task_desc)

                # Store on instance
                self_arg._injected_context = context

                try:
                    result = await func(self_arg, *args, **kwargs)

                    # Log success outcome
                    self.log_outcome(
                        agent_id=agent_id,
                        task_description=task_desc or "unknown",
                        outcome="completed",
                        success=True,
                    )

                    return result

                except Exception as e:
                    # Log failure outcome
                    self.log_outcome(
                        agent_id=agent_id,
                        task_description=task_desc or "unknown",
                        outcome=str(e),
                        success=False,
                    )
                    raise

            @functools.wraps(func)
            def sync_wrapper(self_arg, *args, **kwargs):
                # Get task description from first positional arg if string
                task_desc = args[0] if args and isinstance(args[0], str) else None

                # Inject context
                context = self.inject_context(agent_id, task_desc)

                # Store on instance
                self_arg._injected_context = context

                try:
                    result = func(self_arg, *args, **kwargs)

                    # Log success outcome
                    self.log_outcome(
                        agent_id=agent_id,
                        task_description=task_desc or "unknown",
                        outcome="completed",
                        success=True,
                    )

                    return result

                except Exception as e:
                    # Log failure outcome
                    self.log_outcome(
                        agent_id=agent_id,
                        task_description=task_desc or "unknown",
                        outcome=str(e),
                        success=False,
                    )
                    raise

            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    # =========================================================================
    # Status and Analytics
    # =========================================================================

    def get_injection_stats(self) -> Dict[str, Any]:
        """Get statistics about context injections."""
        if not self.injection_records:
            return {"total_injections": 0}

        successful = [r for r in self.injection_records if r.success]
        failed = [r for r in self.injection_records if not r.success]

        avg_tokens = (
            sum(r.context_tokens for r in successful) / len(successful)
            if successful
            else 0
        )
        avg_duration = (
            sum(r.duration_ms for r in successful) / len(successful)
            if successful
            else 0
        )

        # Count by agent
        by_agent = {}
        for record in self.injection_records:
            by_agent[record.agent_id] = by_agent.get(record.agent_id, 0) + 1

        return {
            "total_injections": len(self.injection_records),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": (
                len(successful) / len(self.injection_records)
                if self.injection_records
                else 0
            ),
            "avg_context_tokens": round(avg_tokens, 1),
            "avg_duration_ms": round(avg_duration, 2),
            "by_agent": by_agent,
            "recent_errors": [r.error for r in failed[-5:] if r.error],
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current injector status."""
        return {
            "initialized": self._initialized,
            "config": asdict(self.config),
            "infrastructure_status": self.infrastructure.get_status(),
            "injection_stats": self.get_injection_stats(),
        }


# =============================================================================
# Global Instance and Convenience Functions
# =============================================================================

# Global singleton instance
_injector: Optional[ContextInjector] = None


def get_injector() -> ContextInjector:
    """Get the global context injector instance."""
    global _injector
    if _injector is None:
        _injector = ContextInjector()
    return _injector


def inject_context(
    agent_id: str, task_description: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function to inject context."""
    return get_injector().inject_context(agent_id, task_description)


def with_infrastructure_context(agent_id: str):
    """Convenience decorator for context injection."""
    return get_injector().with_context(agent_id)


# =============================================================================
# CLI Entry Point
# =============================================================================


def main():
    """Test the context injector."""
    injector = ContextInjector()

    print("Context Injector Status:")
    print(json.dumps(injector.get_status(), indent=2))

    print("\n--- Test Injection for Librarian ---")
    context = injector.inject_context(
        "librarian", "Find research papers on attachment theory"
    )
    print(context.get("_formatted_prompt", "No context"))

    print("\n--- Injection Stats ---")
    print(json.dumps(injector.get_injection_stats(), indent=2))


if __name__ == "__main__":
    main()
