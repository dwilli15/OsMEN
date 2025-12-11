"""
Memory Bridge System
====================

Handles dynamic transitions between memory tiers and detects
synchronicity events for lateral thinking bridges.

Philosophy (Dao of Complexity):
- Memory is not static; it flows between states
- Valuable patterns emerge from unexpected connections
- The bridge reveals itself when both sides are ready

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                       MemoryBridge                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   WORKING ────────────────────────────────► SHORT-TERM         │
│      ↑                                          │               │
│      │  (immediate                    (session  │               │
│      │   recall)                       persist) │               │
│      │                                          ▼               │
│      │                                    LONG-TERM             │
│      │                                          │               │
│      └──────────────────────────────────────────┘               │
│                    (salient recall)                             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                 SynchronicityDetector                           │
│                                                                 │
│   Memory A ─────────[unexpected connection]────────► Memory B   │
│                            ↓                                    │
│                  SynchronicityEvent                             │
│              (bridge_type, strength, context)                   │
└─────────────────────────────────────────────────────────────────┘
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("osmen.memory.bridge")


# =============================================================================
# Bridge Types and Events
# =============================================================================


class BridgeType(Enum):
    """Types of synchronicity bridges."""

    SEMANTIC = "semantic"  # Similar meaning, different domains
    TEMPORAL = "temporal"  # Time-related connections
    CONCEPTUAL = "conceptual"  # Abstract concept links
    EMOTIONAL = "emotional"  # Shared emotional resonance
    STRUCTURAL = "structural"  # Similar patterns/structures
    EMERGENT = "emergent"  # Unexpected, novel connections


class TransitionReason(Enum):
    """Reasons for tier transitions."""

    TTL_EXCEEDED = "ttl_exceeded"  # Time-based promotion
    HIGH_ACCESS = "high_access"  # Frequently accessed
    USER_MARKED = "user_marked"  # Explicitly marked important
    BRIDGE_ANCHOR = "bridge_anchor"  # Part of synchronicity bridge
    DECAY = "decay"  # Low relevance decay
    MERGE = "merge"  # Merged with similar memory


@dataclass
class SynchronicityEvent:
    """
    A detected synchronicity between two memories.

    Represents a "glimmer" - an unexpected connection that
    may reveal deeper patterns.
    """

    id: str
    memory_id_1: str
    memory_id_2: str
    bridge_type: BridgeType
    strength: float  # 0.0 to 1.0
    discovered_at: float

    # Context about the connection
    shared_concepts: List[str] = field(default_factory=list)
    divergent_concepts: List[str] = field(default_factory=list)

    # The "glimmer" - a generated insight about the connection
    insight: str = ""

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "memory_id_1": self.memory_id_1,
            "memory_id_2": self.memory_id_2,
            "bridge_type": self.bridge_type.value,
            "strength": self.strength,
            "discovered_at": self.discovered_at,
            "shared_concepts": self.shared_concepts,
            "divergent_concepts": self.divergent_concepts,
            "insight": self.insight,
            "metadata": self.metadata,
        }


@dataclass
class TierTransition:
    """Record of a memory tier transition."""

    memory_id: str
    from_tier: str
    to_tier: str
    reason: TransitionReason
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Synchronicity Detector
# =============================================================================


class SynchronicityDetector:
    """
    Detects unexpected connections between memories.

    Uses multiple strategies to find "glimmers of synchronicity":
    1. Semantic similarity across different domains
    2. Structural pattern matching
    3. Temporal proximity with conceptual distance
    4. Emotional resonance detection
    """

    def __init__(self, threshold: float = 0.75, min_divergence: float = 0.3):
        """
        Args:
            threshold: Minimum similarity for bridge detection
            min_divergence: Minimum domain divergence (to avoid obvious connections)
        """
        self.threshold = threshold
        self.min_divergence = min_divergence
        self.detected_bridges: List[SynchronicityEvent] = []

    def detect(
        self,
        memory_1: Dict[str, Any],
        memory_2: Dict[str, Any],
        embedding_similarity: Optional[float] = None,
    ) -> Optional[SynchronicityEvent]:
        """
        Detect synchronicity between two memories.

        Returns SynchronicityEvent if a bridge is detected, None otherwise.
        """
        # Skip if same memory
        if memory_1.get("id") == memory_2.get("id"):
            return None

        # Get domains from Context7 metadata
        domain_1 = memory_1.get("metadata", {}).get("c7_domain", "")
        domain_2 = memory_2.get("metadata", {}).get("c7_domain", "")

        # Check for cross-domain connection (interesting bridges cross boundaries)
        domains_different = domain_1 != domain_2 and domain_1 and domain_2

        # Calculate various similarity dimensions
        semantic_sim = embedding_similarity or 0.0
        structural_sim = self._structural_similarity(memory_1, memory_2)
        temporal_sim = self._temporal_proximity(memory_1, memory_2)
        emotional_sim = self._emotional_resonance(memory_1, memory_2)

        # Composite score with domain divergence bonus
        base_score = (
            semantic_sim * 0.4
            + structural_sim * 0.2
            + temporal_sim * 0.2
            + emotional_sim * 0.2
        )

        # Boost score for cross-domain connections (more interesting)
        if domains_different:
            base_score *= 1.2

        # Clamp to [0, 1]
        final_score = min(1.0, base_score)

        # Check if it meets the threshold
        if final_score < self.threshold:
            return None

        # Determine bridge type based on strongest dimension
        bridge_type = self._determine_bridge_type(
            semantic_sim, structural_sim, temporal_sim, emotional_sim
        )

        # Generate synchronicity event
        event = SynchronicityEvent(
            id=self._generate_bridge_id(memory_1, memory_2),
            memory_id_1=memory_1["id"],
            memory_id_2=memory_2["id"],
            bridge_type=bridge_type,
            strength=final_score,
            discovered_at=time.time(),
            shared_concepts=self._extract_shared_concepts(memory_1, memory_2),
            divergent_concepts=self._extract_divergent_concepts(memory_1, memory_2),
            insight=self._generate_insight(memory_1, memory_2, bridge_type),
            metadata={
                "domain_1": domain_1,
                "domain_2": domain_2,
                "scores": {
                    "semantic": semantic_sim,
                    "structural": structural_sim,
                    "temporal": temporal_sim,
                    "emotional": emotional_sim,
                },
            },
        )

        self.detected_bridges.append(event)
        logger.info(f"Synchronicity detected: {event.id} ({bridge_type.value})")

        return event

    def _structural_similarity(
        self, mem1: Dict[str, Any], mem2: Dict[str, Any]
    ) -> float:
        """Compare structural patterns (length, format, etc.)"""
        content_1 = mem1.get("content", "")
        content_2 = mem2.get("content", "")

        # Simple length ratio
        len_1, len_2 = len(content_1), len(content_2)
        if len_1 == 0 or len_2 == 0:
            return 0.0

        length_ratio = min(len_1, len_2) / max(len_1, len_2)

        # Check for similar formatting (lists, code, etc.)
        has_list_1 = "- " in content_1 or "* " in content_1
        has_list_2 = "- " in content_2 or "* " in content_2
        format_match = 1.0 if has_list_1 == has_list_2 else 0.5

        return (length_ratio + format_match) / 2

    def _temporal_proximity(self, mem1: Dict[str, Any], mem2: Dict[str, Any]) -> float:
        """Check if memories were created close in time."""
        time_1 = mem1.get("metadata", {}).get("created_at", 0)
        time_2 = mem2.get("metadata", {}).get("created_at", 0)

        if not time_1 or not time_2:
            return 0.5  # Unknown, neutral

        # Calculate time difference in hours
        diff_hours = abs(time_1 - time_2) / 3600

        # Exponential decay: closer = higher score
        # Same hour = 1.0, 24h apart ≈ 0.5, 1 week apart ≈ 0.1
        return max(0.0, 1.0 - (diff_hours / 168))  # 168 = hours in a week

    def _emotional_resonance(self, mem1: Dict[str, Any], mem2: Dict[str, Any]) -> float:
        """Compare emotional tone from Context7."""
        emotion_1 = mem1.get("metadata", {}).get("c7_emotion", "")
        emotion_2 = mem2.get("metadata", {}).get("c7_emotion", "")

        if not emotion_1 or not emotion_2:
            return 0.5  # Unknown, neutral

        # Exact match
        if emotion_1 == emotion_2:
            return 1.0

        # Group similar emotions
        positive = {"joy", "excitement", "curiosity", "satisfaction"}
        negative = {"frustration", "confusion", "concern", "doubt"}
        neutral = {"neutral", "analytical", "factual"}

        same_group = (
            (emotion_1 in positive and emotion_2 in positive)
            or (emotion_1 in negative and emotion_2 in negative)
            or (emotion_1 in neutral and emotion_2 in neutral)
        )

        return 0.7 if same_group else 0.3

    def _determine_bridge_type(
        self, semantic: float, structural: float, temporal: float, emotional: float
    ) -> BridgeType:
        """Determine the primary bridge type based on scores."""
        scores = {
            BridgeType.SEMANTIC: semantic,
            BridgeType.STRUCTURAL: structural,
            BridgeType.TEMPORAL: temporal,
            BridgeType.EMOTIONAL: emotional,
        }

        max_type = max(scores, key=scores.get)

        # Check for emergent (multiple strong signals)
        strong_signals = sum(1 for s in scores.values() if s > 0.7)
        if strong_signals >= 3:
            return BridgeType.EMERGENT

        return max_type

    def _extract_shared_concepts(
        self, mem1: Dict[str, Any], mem2: Dict[str, Any]
    ) -> List[str]:
        """Extract concepts shared between memories."""
        content_1 = mem1.get("content", "").lower()
        content_2 = mem2.get("content", "").lower()

        # Simple word overlap (could be enhanced with NLP)
        words_1 = set(content_1.split())
        words_2 = set(content_2.split())

        # Filter stopwords and short words
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "to",
            "of",
            "in",
            "for",
            "and",
            "or",
        }
        shared = words_1 & words_2 - stopwords
        meaningful = [w for w in shared if len(w) > 3]

        return meaningful[:10]  # Top 10

    def _extract_divergent_concepts(
        self, mem1: Dict[str, Any], mem2: Dict[str, Any]
    ) -> List[str]:
        """Extract concepts unique to each memory."""
        meta_1 = mem1.get("metadata", {})
        meta_2 = mem2.get("metadata", {})

        divergent = []

        # Domain differences
        d1 = meta_1.get("c7_domain", "")
        d2 = meta_2.get("c7_domain", "")
        if d1 and d2 and d1 != d2:
            divergent.extend([f"domain:{d1}", f"domain:{d2}"])

        # Abstract dimension differences
        a1 = meta_1.get("c7_abstract", "")
        a2 = meta_2.get("c7_abstract", "")
        if a1 and a2 and a1 != a2:
            divergent.extend([f"abstract:{a1}", f"abstract:{a2}"])

        return divergent

    def _generate_insight(
        self, mem1: Dict[str, Any], mem2: Dict[str, Any], bridge_type: BridgeType
    ) -> str:
        """Generate a brief insight about the connection."""
        domain_1 = mem1.get("metadata", {}).get("c7_domain", "unknown")
        domain_2 = mem2.get("metadata", {}).get("c7_domain", "unknown")

        insights = {
            BridgeType.SEMANTIC: f"These {domain_1} and {domain_2} concepts share deep semantic meaning.",
            BridgeType.TEMPORAL: f"These memories emerged around the same time, suggesting a shared context.",
            BridgeType.STRUCTURAL: f"Similar patterns appear in both {domain_1} and {domain_2} contexts.",
            BridgeType.EMOTIONAL: f"Both evoke similar emotional responses despite different domains.",
            BridgeType.CONCEPTUAL: f"An abstract connection links {domain_1} to {domain_2}.",
            BridgeType.EMERGENT: f"Multiple dimensions align - this is a strong emergent connection.",
        }

        return insights.get(bridge_type, "An unexpected connection was detected.")

    def _generate_bridge_id(self, mem1: Dict[str, Any], mem2: Dict[str, Any]) -> str:
        """Generate unique bridge ID."""
        # Sort IDs for consistency (A-B == B-A)
        ids = sorted([mem1["id"], mem2["id"]])
        data = f"{ids[0]}:{ids[1]}:{time.time()}"
        return f"bridge_{hashlib.md5(data.encode()).hexdigest()[:12]}"

    def get_recent_bridges(self, limit: int = 10) -> List[SynchronicityEvent]:
        """Get most recently detected bridges."""
        sorted_bridges = sorted(
            self.detected_bridges, key=lambda x: x.discovered_at, reverse=True
        )
        return sorted_bridges[:limit]


# =============================================================================
# Memory Bridge (Tier Management)
# =============================================================================


class MemoryBridge:
    """
    Manages transitions between memory tiers.

    Handles:
    - Automatic promotion based on access patterns
    - Time-based tier transitions
    - Bridge-anchor preservation
    - Decay and archival
    """

    def __init__(
        self,
        promotion_threshold: int = 3,  # Access count for promotion
        decay_days: int = 30,  # Days before archive consideration
        bridge_boost: float = 1.5,  # Multiplier for bridge anchors
    ):
        self.promotion_threshold = promotion_threshold
        self.decay_days = decay_days
        self.bridge_boost = bridge_boost

        # Synchronicity detector
        self.sync_detector = SynchronicityDetector()

        # Transition history
        self.transitions: List[TierTransition] = []

        # Callbacks for tier changes
        self._callbacks: Dict[str, List[Callable]] = {
            "on_promote": [],
            "on_demote": [],
            "on_bridge": [],
        }

    def evaluate_promotion(
        self, memory: Dict[str, Any]
    ) -> Tuple[bool, Optional[TransitionReason]]:
        """
        Evaluate if a memory should be promoted to long-term.

        Returns:
            (should_promote, reason)
        """
        access_count = memory.get("access_count", 0)
        bridges = memory.get("bridges", [])
        created_at = memory.get("created_at", time.time())

        # Check access count threshold
        if access_count >= self.promotion_threshold:
            return True, TransitionReason.HIGH_ACCESS

        # Check if part of synchronicity bridge (anchors should persist)
        if len(bridges) > 0:
            # Bridge anchors get boosted threshold
            boosted_threshold = self.promotion_threshold / self.bridge_boost
            if access_count >= boosted_threshold:
                return True, TransitionReason.BRIDGE_ANCHOR

        # Check TTL-based promotion (old but accessed = valuable)
        age_days = (time.time() - created_at) / 86400
        if age_days > 7 and access_count > 0:
            return True, TransitionReason.TTL_EXCEEDED

        return False, None

    def evaluate_decay(
        self, memory: Dict[str, Any]
    ) -> Tuple[bool, Optional[TransitionReason]]:
        """
        Evaluate if a memory should be archived (decay).

        Returns:
            (should_archive, reason)
        """
        accessed_at = memory.get("accessed_at", 0)
        access_count = memory.get("access_count", 0)
        bridges = memory.get("bridges", [])

        # Never decay bridge anchors
        if len(bridges) > 0:
            return False, None

        # Check last access time
        days_since_access = (time.time() - accessed_at) / 86400

        # Low access + old = decay candidate
        if days_since_access > self.decay_days and access_count < 2:
            return True, TransitionReason.DECAY

        return False, None

    def create_bridge(
        self,
        memory_1: Dict[str, Any],
        memory_2: Dict[str, Any],
        embedding_similarity: Optional[float] = None,
    ) -> Optional[SynchronicityEvent]:
        """
        Attempt to create a synchronicity bridge between memories.

        Uses the SynchronicityDetector to evaluate the connection.
        """
        event = self.sync_detector.detect(memory_1, memory_2, embedding_similarity)

        if event:
            # Trigger callbacks
            for callback in self._callbacks.get("on_bridge", []):
                callback(event)

        return event

    def record_transition(
        self, memory_id: str, from_tier: str, to_tier: str, reason: TransitionReason
    ) -> TierTransition:
        """Record a tier transition for audit trail."""
        transition = TierTransition(
            memory_id=memory_id,
            from_tier=from_tier,
            to_tier=to_tier,
            reason=reason,
            timestamp=time.time(),
        )

        self.transitions.append(transition)
        logger.info(f"Transition: {memory_id} {from_tier}→{to_tier} ({reason.value})")

        return transition

    def register_callback(self, event: str, callback: Callable):
        """Register callback for bridge events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def get_transition_history(
        self, memory_id: Optional[str] = None, limit: int = 100
    ) -> List[TierTransition]:
        """Get transition history, optionally filtered by memory."""
        if memory_id:
            filtered = [t for t in self.transitions if t.memory_id == memory_id]
        else:
            filtered = self.transitions

        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_bridge_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected bridges."""
        bridges = self.sync_detector.detected_bridges

        if not bridges:
            return {
                "total_bridges": 0,
                "by_type": {},
                "avg_strength": 0.0,
            }

        by_type = {}
        for bridge in bridges:
            bt = bridge.bridge_type.value
            by_type[bt] = by_type.get(bt, 0) + 1

        avg_strength = sum(b.strength for b in bridges) / len(bridges)

        return {
            "total_bridges": len(bridges),
            "by_type": by_type,
            "avg_strength": round(avg_strength, 3),
            "strongest": (
                max(bridges, key=lambda x: x.strength).to_dict() if bridges else None
            ),
            "most_recent": bridges[-1].to_dict() if bridges else None,
        }


# =============================================================================
# Convenience Functions
# =============================================================================


def create_bridge_system(
    promotion_threshold: int = 3, decay_days: int = 30
) -> MemoryBridge:
    """Create a configured MemoryBridge instance."""
    return MemoryBridge(promotion_threshold=promotion_threshold, decay_days=decay_days)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.DEBUG)

    bridge = MemoryBridge()

    # Test synchronicity detection
    mem1 = {
        "id": "mem_001",
        "content": "Python uses indentation for code blocks, making it readable.",
        "metadata": {
            "c7_domain": "technical",
            "c7_emotion": "analytical",
            "created_at": time.time() - 3600,  # 1 hour ago
        },
    }

    mem2 = {
        "id": "mem_002",
        "content": "The Zen of Python emphasizes readability and simplicity in design.",
        "metadata": {
            "c7_domain": "philosophical",
            "c7_emotion": "analytical",
            "created_at": time.time() - 1800,  # 30 min ago
        },
    }

    # Detect synchronicity
    event = bridge.create_bridge(mem1, mem2, embedding_similarity=0.85)

    if event:
        print(f"\n🌟 Synchronicity Detected!")
        print(f"   Type: {event.bridge_type.value}")
        print(f"   Strength: {event.strength:.2f}")
        print(f"   Insight: {event.insight}")
        print(f"   Shared: {event.shared_concepts}")

    # Get statistics
    stats = bridge.get_bridge_statistics()
    print(f"\n📊 Bridge Statistics: {stats}")
