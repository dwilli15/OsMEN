"""
OsMEN Hybrid Memory System
========================

A unified memory architecture combining:
- ChromaDB: Long-term vector memory (semantic RAG, persistent knowledge)
- SQLite: Short-term structured memory (sessions, tasks, conversations)

With deeply embedded cognitive patterns:
- Sequential Reasoning: Step decomposition in all memory operations
- Lateral Thinking: Synchronicity bridges between disparate concepts
- Dynamic Bridges: Automatic promotion/demotion between stores

Philosophy (Dao of Complexity):
- Embrace emergence over rigid structure
- Allow glimmers of synchronicity to surface
- Balance focused retrieval with shadow context
"""

from .bridge import MemoryBridge, SynchronicityDetector, SynchronicityEvent
from .hybrid_memory import HybridMemory, MemoryConfig, MemoryItem, MemoryTier
from .lateral_synchronicity import (
    Context7,
    Glimmer,
    GlimmerType,
    LateralBridge,
    LateralQueryExpander,
)
from .sequential_reasoning import (
    ReasoningChain,
    SequentialReasoner,
    ThoughtStep,
    ThoughtType,
)

__all__ = [
    # Core Memory
    "HybridMemory",
    "MemoryConfig",
    "MemoryItem",
    "MemoryTier",
    # Bridge System
    "MemoryBridge",
    "SynchronicityDetector",
    "SynchronicityEvent",
    # Sequential Reasoning
    "SequentialReasoner",
    "ReasoningChain",
    "ThoughtStep",
    "ThoughtType",
    # Lateral Thinking
    "LateralBridge",
    "LateralQueryExpander",
    "Context7",
    "Glimmer",
    "GlimmerType",
]
