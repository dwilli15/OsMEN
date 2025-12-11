"""
Lateral Synchronicity - Dao of Complexity
=========================================

Implements lateral thinking through synchronicity bridges - unexpected
connections that reveal deeper patterns.

Philosophy (Dao of Complexity):
- "The Dao that can be told is not the eternal Dao"
- Complexity emerges from simple rules
- Synchronicity is meaningful coincidence
- Lateral connections cross domain boundaries
- Glimmers appear at the edge of understanding

This module provides:
1. Multi-dimensional query expansion (Context7)
2. Cross-domain bridge detection
3. Synchronicity emergence patterns
4. Novel reuse of existing infrastructure

Key Concepts:
- Focus Vector: Direct, precise retrieval
- Shadow Vector: Context, implications, lateral expansion
- Glimmer: An unexpected connection that feels meaningful
- Bridge: A persistent link between disparate memories
"""

import hashlib
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("osmen.memory.lateral")


# =============================================================================
# Context7 Dimensions
# =============================================================================


@dataclass
class Context7:
    """
    The 7-Dimensional Context Model.

    Represents the complete context space for lateral thinking.
    Each dimension is a lens through which meaning can be explored.
    """

    intent: str = ""  # 1. Direct user goal / purpose
    domain: str = ""  # 2. Subject matter field / discipline
    emotion: str = ""  # 3. Tone, sentiment, feeling
    temporal: str = ""  # 4. Time-based relevance / era
    spatial: str = ""  # 5. Location / environment / scale
    relational: str = ""  # 6. Social / interpersonal dynamics
    abstract: str = ""  # 7. Metaphorical / symbolic connections

    def to_metadata(self) -> Dict[str, str]:
        """Convert to metadata dict for storage."""
        return {
            "c7_intent": self.intent,
            "c7_domain": self.domain,
            "c7_emotion": self.emotion,
            "c7_temporal": self.temporal,
            "c7_spatial": self.spatial,
            "c7_relational": self.relational,
            "c7_abstract": self.abstract,
        }

    @classmethod
    def from_metadata(cls, meta: Dict[str, Any]) -> "Context7":
        """Create from metadata dict."""
        return cls(
            intent=meta.get("c7_intent", ""),
            domain=meta.get("c7_domain", ""),
            emotion=meta.get("c7_emotion", ""),
            temporal=meta.get("c7_temporal", ""),
            spatial=meta.get("c7_spatial", ""),
            relational=meta.get("c7_relational", ""),
            abstract=meta.get("c7_abstract", ""),
        )

    def dimensions_set(self) -> Set[str]:
        """Return set of non-empty dimensions."""
        dims = set()
        if self.intent:
            dims.add("intent")
        if self.domain:
            dims.add("domain")
        if self.emotion:
            dims.add("emotion")
        if self.temporal:
            dims.add("temporal")
        if self.spatial:
            dims.add("spatial")
        if self.relational:
            dims.add("relational")
        if self.abstract:
            dims.add("abstract")
        return dims

    def shared_dimensions(self, other: "Context7") -> Set[str]:
        """Find dimensions that both contexts have set."""
        return self.dimensions_set() & other.dimensions_set()

    def similarity(self, other: "Context7") -> float:
        """Calculate similarity score between two contexts."""
        shared = self.shared_dimensions(other)
        if not shared:
            return 0.0

        matches = 0
        for dim in shared:
            if getattr(self, dim) == getattr(other, dim):
                matches += 1

        return matches / len(shared)


class GlimmerType(Enum):
    """Types of synchronicity glimmers."""

    SEMANTIC = "semantic"  # Meaning-based connection
    TEMPORAL = "temporal"  # Time-based coincidence
    STRUCTURAL = "structural"  # Pattern similarity
    EMOTIONAL = "emotional"  # Shared feeling
    SYMBOLIC = "symbolic"  # Metaphorical link
    EMERGENT = "emergent"  # Novel, unexpected


@dataclass
class Glimmer:
    """
    A glimmer of synchronicity.

    Represents an unexpected connection that may reveal deeper meaning.
    Glimmers are ephemeral - they may or may not become bridges.
    """

    id: str
    source_id: str  # First memory
    target_id: str  # Second memory
    glimmer_type: GlimmerType
    strength: float  # 0.0 to 1.0
    discovered_at: float

    # The connection
    shared_concepts: List[str] = field(default_factory=list)
    connecting_insight: str = ""

    # Context7 analysis
    shared_dimensions: List[str] = field(default_factory=list)
    dimension_contrasts: Dict[str, Tuple[str, str]] = field(default_factory=dict)

    # Status
    acknowledged: bool = False  # User/system has seen this
    promoted_to_bridge: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.glimmer_type.value,
            "strength": self.strength,
            "discovered_at": self.discovered_at,
            "shared_concepts": self.shared_concepts,
            "connecting_insight": self.connecting_insight,
            "shared_dimensions": self.shared_dimensions,
            "dimension_contrasts": self.dimension_contrasts,
            "acknowledged": self.acknowledged,
            "promoted_to_bridge": self.promoted_to_bridge,
        }


# =============================================================================
# Lateral Query Expansion
# =============================================================================


class LateralQueryExpander:
    """
    Expands queries across Context7 dimensions for lateral retrieval.

    Generates multiple query vectors:
    1. Focus: Direct, precise query
    2. Shadow: Contextual, implied meanings
    3. Abstract: Metaphorical, symbolic
    4. Temporal: Historical and future
    5. Relational: Social and interpersonal
    """

    def __init__(self):
        self.expansion_templates = {
            "focus": "Exact answer to: {query}",
            "shadow": "Broader context, themes, and implications of: {query}",
            "abstract": "Metaphorical meanings and symbolic interpretations of: {query}",
            "temporal": "Historical evolution and future implications of: {query}",
            "relational": "Social dynamics and interpersonal aspects of: {query}",
            "domain_cross": "How {query} relates to other fields and disciplines",
            "pattern": "Underlying patterns and structures in: {query}",
        }

    def expand(
        self, query: str, context: Optional[Context7] = None, expansion_depth: int = 3
    ) -> Dict[str, str]:
        """
        Expand query into multiple lateral vectors.

        Args:
            query: Original query
            context: Optional Context7 for informed expansion
            expansion_depth: How many dimensions to explore (1-7)

        Returns:
            Dict of expansion_type -> expanded_query
        """
        expansions = {}

        # Always include focus and shadow
        expansions["focus"] = self.expansion_templates["focus"].format(query=query)
        expansions["shadow"] = self.expansion_templates["shadow"].format(query=query)

        if expansion_depth >= 2:
            expansions["abstract"] = self.expansion_templates["abstract"].format(
                query=query
            )

        if expansion_depth >= 3:
            expansions["domain_cross"] = self.expansion_templates[
                "domain_cross"
            ].format(query=query)

        if expansion_depth >= 4:
            expansions["temporal"] = self.expansion_templates["temporal"].format(
                query=query
            )

        if expansion_depth >= 5:
            expansions["relational"] = self.expansion_templates["relational"].format(
                query=query
            )

        if expansion_depth >= 6:
            expansions["pattern"] = self.expansion_templates["pattern"].format(
                query=query
            )

        # Context-informed expansions
        if context:
            if context.domain:
                expansions["in_domain"] = f"{query} in the context of {context.domain}"
            if context.abstract:
                expansions["abstract_hint"] = f"{query} {context.abstract}"

        logger.debug(f"Expanded query into {len(expansions)} vectors")
        return expansions


# =============================================================================
# Synchronicity Emergence
# =============================================================================


class SynchronicityEmergence:
    """
    Detects and cultivates synchronicity patterns.

    Implements the "Dao of Complexity" approach:
    - Allow patterns to emerge rather than force them
    - Cross-domain connections are more valuable
    - Timing matters (temporal proximity suggests meaning)
    - Repeated patterns strengthen bridges
    """

    def __init__(
        self,
        base_threshold: float = 0.65,
        cross_domain_boost: float = 1.3,
        temporal_window_hours: float = 24.0,
    ):
        """
        Args:
            base_threshold: Base similarity for glimmer detection
            cross_domain_boost: Multiplier for cross-domain connections
            temporal_window_hours: Time window for temporal proximity boost
        """
        self.base_threshold = base_threshold
        self.cross_domain_boost = cross_domain_boost
        self.temporal_window_hours = temporal_window_hours

        # Glimmer cache (ephemeral)
        self.glimmers: List[Glimmer] = []

        # Pattern tracking for emergence
        self.concept_frequency: Dict[str, int] = {}
        self.domain_connections: Dict[Tuple[str, str], int] = {}

    def detect_glimmer(
        self,
        memory_1: Dict[str, Any],
        memory_2: Dict[str, Any],
        similarity_score: float,
    ) -> Optional[Glimmer]:
        """
        Detect if two memories form a synchronicity glimmer.

        Returns Glimmer if detected, None otherwise.
        """
        # Extract Context7
        c7_1 = Context7.from_metadata(memory_1.get("metadata", {}))
        c7_2 = Context7.from_metadata(memory_2.get("metadata", {}))

        # Calculate adjusted threshold
        threshold = self.base_threshold

        # Cross-domain boost (more interesting)
        if c7_1.domain and c7_2.domain and c7_1.domain != c7_2.domain:
            threshold /= self.cross_domain_boost

        # Temporal proximity boost
        time_1 = memory_1.get("metadata", {}).get("created_at", 0)
        time_2 = memory_2.get("metadata", {}).get("created_at", 0)
        if time_1 and time_2:
            hours_apart = abs(time_1 - time_2) / 3600
            if hours_apart < self.temporal_window_hours:
                threshold *= 0.9  # Lower threshold for temporally close

        # Check if meets threshold
        if similarity_score < threshold:
            return None

        # Determine glimmer type
        glimmer_type = self._determine_type(c7_1, c7_2, similarity_score)

        # Extract shared concepts
        shared = self._extract_shared_concepts(
            memory_1.get("content", ""), memory_2.get("content", "")
        )

        # Find dimension contrasts (interesting differences)
        contrasts = self._find_contrasts(c7_1, c7_2)

        # Generate connecting insight
        insight = self._generate_insight(c7_1, c7_2, shared, contrasts, glimmer_type)

        glimmer = Glimmer(
            id=self._generate_id(memory_1, memory_2),
            source_id=memory_1["id"],
            target_id=memory_2["id"],
            glimmer_type=glimmer_type,
            strength=similarity_score,
            discovered_at=time.time(),
            shared_concepts=shared,
            connecting_insight=insight,
            shared_dimensions=list(c7_1.shared_dimensions(c7_2)),
            dimension_contrasts=contrasts,
        )

        self.glimmers.append(glimmer)

        # Track patterns for emergence
        self._track_patterns(c7_1, c7_2, shared)

        logger.info(
            f"Glimmer detected: {glimmer_type.value} (strength: {similarity_score:.2f})"
        )
        return glimmer

    def get_emerging_patterns(self) -> List[Dict[str, Any]]:
        """
        Identify emerging patterns from accumulated glimmers.

        Returns patterns that appear across multiple connections.
        """
        patterns = []

        # Frequent concepts
        for concept, count in sorted(
            self.concept_frequency.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            if count > 2:
                patterns.append(
                    {
                        "type": "concept",
                        "value": concept,
                        "frequency": count,
                        "insight": f"'{concept}' appears across multiple connections",
                    }
                )

        # Domain bridges
        for (d1, d2), count in sorted(
            self.domain_connections.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            if count > 1:
                patterns.append(
                    {
                        "type": "domain_bridge",
                        "domains": [d1, d2],
                        "frequency": count,
                        "insight": f"Recurring connection between {d1} and {d2}",
                    }
                )

        return patterns

    def _determine_type(
        self, c7_1: Context7, c7_2: Context7, similarity: float
    ) -> GlimmerType:
        """Determine the type of glimmer based on contexts."""
        # Check for emotional resonance
        if c7_1.emotion and c7_2.emotion and c7_1.emotion == c7_2.emotion:
            return GlimmerType.EMOTIONAL

        # Check for abstract/symbolic
        if c7_1.abstract or c7_2.abstract:
            return GlimmerType.SYMBOLIC

        # Cross-domain = emergent
        if c7_1.domain and c7_2.domain and c7_1.domain != c7_2.domain:
            if similarity > 0.8:
                return GlimmerType.EMERGENT
            return GlimmerType.STRUCTURAL

        # Default to semantic
        return GlimmerType.SEMANTIC

    def _extract_shared_concepts(self, content_1: str, content_2: str) -> List[str]:
        """Extract concepts shared between two contents."""
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
            "but",
            "with",
            "this",
            "that",
            "these",
            "those",
        }

        words_1 = set(content_1.lower().split())
        words_2 = set(content_2.lower().split())

        shared = words_1 & words_2 - stopwords
        meaningful = [w for w in shared if len(w) > 3]

        return meaningful[:10]

    def _find_contrasts(
        self, c7_1: Context7, c7_2: Context7
    ) -> Dict[str, Tuple[str, str]]:
        """Find interesting dimension contrasts."""
        contrasts = {}

        if c7_1.domain and c7_2.domain and c7_1.domain != c7_2.domain:
            contrasts["domain"] = (c7_1.domain, c7_2.domain)

        if c7_1.temporal and c7_2.temporal and c7_1.temporal != c7_2.temporal:
            contrasts["temporal"] = (c7_1.temporal, c7_2.temporal)

        if c7_1.abstract and c7_2.abstract and c7_1.abstract != c7_2.abstract:
            contrasts["abstract"] = (c7_1.abstract, c7_2.abstract)

        return contrasts

    def _generate_insight(
        self,
        c7_1: Context7,
        c7_2: Context7,
        shared: List[str],
        contrasts: Dict[str, Tuple[str, str]],
        glimmer_type: GlimmerType,
    ) -> str:
        """Generate a connecting insight about the glimmer."""
        # Cross-domain insight
        if "domain" in contrasts:
            d1, d2 = contrasts["domain"]
            return f"A bridge emerges between {d1} and {d2} through shared concepts: {', '.join(shared[:3])}"

        # Type-specific insights
        if glimmer_type == GlimmerType.EMOTIONAL:
            return f"Both carry a sense of '{c7_1.emotion or c7_2.emotion}', creating resonance"

        if glimmer_type == GlimmerType.SYMBOLIC:
            return f"Symbolic connection through: {c7_1.abstract or c7_2.abstract}"

        if glimmer_type == GlimmerType.EMERGENT:
            return f"Novel pattern detected - multiple dimensions align unexpectedly"

        # Default
        if shared:
            return f"Connected through concepts: {', '.join(shared[:3])}"

        return "An unexpected connection awaits exploration"

    def _track_patterns(
        self, c7_1: Context7, c7_2: Context7, shared_concepts: List[str]
    ):
        """Track patterns for emergence detection."""
        # Track concept frequency
        for concept in shared_concepts:
            self.concept_frequency[concept] = self.concept_frequency.get(concept, 0) + 1

        # Track domain connections
        if c7_1.domain and c7_2.domain and c7_1.domain != c7_2.domain:
            key = tuple(sorted([c7_1.domain, c7_2.domain]))
            self.domain_connections[key] = self.domain_connections.get(key, 0) + 1

    def _generate_id(self, mem1: Dict[str, Any], mem2: Dict[str, Any]) -> str:
        """Generate unique glimmer ID."""
        ids = sorted([mem1["id"], mem2["id"]])
        data = f"glimmer:{ids[0]}:{ids[1]}:{time.time()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]


# =============================================================================
# Lateral Bridge
# =============================================================================


class LateralBridge:
    """
    High-level interface for lateral thinking in memory operations.

    Combines:
    - Query expansion (LateralQueryExpander)
    - Synchronicity detection (SynchronicityEmergence)
    - Result weaving (focus + shadow interleaving)
    """

    def __init__(self, expansion_depth: int = 4, glimmer_threshold: float = 0.65):
        """
        Args:
            expansion_depth: How many dimensions to explore (1-7)
            glimmer_threshold: Similarity threshold for glimmer detection
        """
        self.expander = LateralQueryExpander()
        self.emergence = SynchronicityEmergence(base_threshold=glimmer_threshold)
        self.expansion_depth = expansion_depth

    def expand_query(
        self, query: str, context: Optional[Context7] = None
    ) -> Dict[str, str]:
        """
        Expand query for lateral search.

        Returns dict of expansion_type -> expanded_query.
        """
        return self.expander.expand(query, context, self.expansion_depth)

    def detect_synchronicity(
        self, memory_1: Dict[str, Any], memory_2: Dict[str, Any], similarity: float
    ) -> Optional[Glimmer]:
        """
        Check for synchronicity glimmer between memories.

        Returns Glimmer if detected.
        """
        return self.emergence.detect_glimmer(memory_1, memory_2, similarity)

    def weave_results(
        self, focus_results: List[Dict], shadow_results: List[Dict], n_results: int = 5
    ) -> List[Dict]:
        """
        Weave focus and shadow results for balanced retrieval.

        Pattern: Focus, Focus, Shadow, Focus, Shadow...
        This ensures precision while allowing lateral discovery.
        """
        woven = []
        seen_ids = set()

        focus_iter = iter(focus_results)
        shadow_iter = iter(shadow_results)

        pattern = [focus_iter, focus_iter, shadow_iter]  # 2:1 ratio
        pattern_idx = 0

        while len(woven) < n_results:
            current_iter = pattern[pattern_idx % len(pattern)]

            try:
                result = next(current_iter)
                result_id = result.get("id", str(len(woven)))

                if result_id not in seen_ids:
                    # Mark retrieval layer
                    if current_iter == shadow_iter:
                        result["retrieval_layer"] = "shadow_context"
                    else:
                        result["retrieval_layer"] = "focus"

                    woven.append(result)
                    seen_ids.add(result_id)
            except StopIteration:
                pass

            pattern_idx += 1

            # Break if both exhausted
            if pattern_idx > (len(focus_results) + len(shadow_results)) * 2:
                break

        # Check for glimmers between adjacent results
        for i in range(len(woven) - 1):
            glimmer = self.detect_synchronicity(
                woven[i],
                woven[i + 1],
                similarity=0.7,  # Assume some similarity if adjacent
            )
            if glimmer:
                woven[i]["has_glimmer"] = True
                woven[i + 1]["has_glimmer"] = True

        return woven[:n_results]

    def get_glimmers(self, limit: int = 10) -> List[Glimmer]:
        """Get recent glimmers."""
        return sorted(
            self.emergence.glimmers, key=lambda g: g.discovered_at, reverse=True
        )[:limit]

    def get_emerging_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns emerging from accumulated glimmers."""
        return self.emergence.get_emerging_patterns()

    def enrich_with_context7(
        self, content: str, existing_context: Optional[Dict] = None
    ) -> Context7:
        """
        Enrich content with Context7 dimensions.

        Uses simple heuristics (could be enhanced with LLM).
        """
        content_lower = content.lower()
        c7 = Context7()

        # Domain detection
        if any(
            kw in content_lower
            for kw in ["code", "python", "function", "api", "software"]
        ):
            c7.domain = "technical"
        elif any(
            kw in content_lower for kw in ["philosophy", "meaning", "concept", "theory"]
        ):
            c7.domain = "philosophical"
        elif any(
            kw in content_lower for kw in ["memory", "thinking", "cognitive", "brain"]
        ):
            c7.domain = "cognitive"

        # Abstract detection
        if any(
            kw in content_lower for kw in ["like", "as if", "metaphor", "similar to"]
        ):
            c7.abstract = "metaphorical"

        # Relational detection
        if any(
            kw in content_lower
            for kw in ["user", "agent", "interaction", "conversation"]
        ):
            c7.relational = "interaction"

        # Temporal detection
        if any(
            kw in content_lower for kw in ["history", "evolution", "future", "timeline"]
        ):
            c7.temporal = "historical"

        # Merge with existing context
        if existing_context:
            if existing_context.get("intent"):
                c7.intent = existing_context["intent"]
            if existing_context.get("emotion"):
                c7.emotion = existing_context["emotion"]

        return c7


# =============================================================================
# Convenience Functions
# =============================================================================

_default_lateral_bridge: Optional[LateralBridge] = None


def get_lateral_bridge() -> LateralBridge:
    """Get or create the default LateralBridge."""
    global _default_lateral_bridge
    if _default_lateral_bridge is None:
        _default_lateral_bridge = LateralBridge()
    return _default_lateral_bridge


def expand_for_lateral_search(query: str) -> Dict[str, str]:
    """Expand query for lateral memory search."""
    return get_lateral_bridge().expand_query(query)


def weave_lateral_results(
    focus: List[Dict], shadow: List[Dict], n: int = 5
) -> List[Dict]:
    """Weave focus and shadow results."""
    return get_lateral_bridge().weave_results(focus, shadow, n)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.DEBUG)

    bridge = LateralBridge()

    # Expand a query
    query = "How do memory systems work?"
    expansions = bridge.expand_query(query)

    print("\n🔍 Query Expansions:")
    for exp_type, exp_query in expansions.items():
        print(f"  [{exp_type}]: {exp_query}")

    # Test glimmer detection
    mem1 = {
        "id": "mem_001",
        "content": "Vector databases store embeddings for semantic search.",
        "metadata": {
            "c7_domain": "technical",
            "c7_intent": "learning",
            "created_at": time.time() - 3600,
        },
    }

    mem2 = {
        "id": "mem_002",
        "content": "The mind stores memories in associative networks.",
        "metadata": {
            "c7_domain": "cognitive",
            "c7_intent": "learning",
            "created_at": time.time() - 1800,
        },
    }

    glimmer = bridge.detect_synchronicity(mem1, mem2, similarity=0.72)

    if glimmer:
        print(f"\n✨ Glimmer Detected!")
        print(f"   Type: {glimmer.glimmer_type.value}")
        print(f"   Strength: {glimmer.strength:.2f}")
        print(f"   Insight: {glimmer.connecting_insight}")
        print(f"   Shared: {glimmer.shared_concepts}")
        print(f"   Contrasts: {glimmer.dimension_contrasts}")

    # Check emerging patterns
    patterns = bridge.get_emerging_patterns()
    if patterns:
        print(f"\n🌟 Emerging Patterns: {patterns}")
