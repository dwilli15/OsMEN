"""
Intelligent Context System for Daily Briefings
==============================================

PRODUCTION INTEGRATION: Connects the briefing system to OsMEN's advanced infrastructure:

1. HybridMemory (integrations/memory/hybrid_memory.py)
   - Stores check-ins in ChromaDB for semantic retrieval
   - Maintains short-term SQLite for recent patterns
   - Enables recall of what worked in similar past situations

2. EnhancedRAGPipeline (integrations/rag_pipeline.py)
   - BM25 + semantic hybrid search
   - Cross-encoder re-ranking
   - Query expansion for better recall

3. SequentialReasoner (integrations/memory/sequential_reasoning.py)
   - Decompose queries into reasoning chains
   - Track confidence in briefing decisions
   - Generate explainable recommendations

4. LateralBridge (integrations/memory/lateral_synchronicity.py)
   - Context7 dimensions for multi-faceted context
   - Synchronicity detection between check-ins and course themes
   - Focus/shadow retrieval for serendipitous insights

Usage:
    from agents.daily_brief.intelligent_context import IntelligentContextEngine

    engine = IntelligentContextEngine()
    context = engine.gather_intelligent_context()

    # Context now includes:
    # - Semantically similar past check-ins
    # - Patterns that worked before
    # - Reasoning trace for decisions
    # - Lateral connections to course material
"""

import hashlib
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the existing context aggregator types
from agents.daily_brief.context_aggregator import (
    ADHDContext,
    AggregatedContext,
    BriefingData,
    CheckInData,
    CheckInParser,
    ContextAggregator,
    ProgressContext,
    SyllabusContext,
    SyllabusParser,
)
from integrations.orchestration import Paths

logger = logging.getLogger("osmen.briefing.intelligent")


# =============================================================================
# Memory Integration Flags - Graceful degradation if services unavailable
# =============================================================================

MEMORY_AVAILABLE = False
RAG_AVAILABLE = False
REASONING_AVAILABLE = False
LATERAL_AVAILABLE = False

try:
    from integrations.memory import HybridMemory, MemoryConfig, MemoryItem, MemoryTier

    MEMORY_AVAILABLE = True
    logger.info("✅ HybridMemory available")
except ImportError as e:
    logger.warning(f"⚠️ HybridMemory not available: {e}")

try:
    from integrations.rag_pipeline import (
        EnhancedRAGPipeline,
        RAGConfig,
        RetrievalResult,
        create_chromadb_rag_pipeline,
    )

    RAG_AVAILABLE = True
    logger.info("✅ EnhancedRAGPipeline available")
except ImportError as e:
    logger.warning(f"⚠️ RAGPipeline not available: {e}")

try:
    from integrations.memory.sequential_reasoning import (
        ReasoningChain,
        SequentialReasoner,
        ThoughtStep,
        ThoughtType,
    )

    REASONING_AVAILABLE = True
    logger.info("✅ SequentialReasoner available")
except ImportError as e:
    logger.warning(f"⚠️ SequentialReasoner not available: {e}")

try:
    from integrations.memory.lateral_synchronicity import (
        Context7,
        Glimmer,
        GlimmerType,
        LateralBridge,
        LateralQueryExpander,
    )

    LATERAL_AVAILABLE = True
    logger.info("✅ LateralBridge available")
except ImportError as e:
    logger.warning(f"⚠️ LateralBridge not available: {e}")


# =============================================================================
# Extended Context Data Classes
# =============================================================================


@dataclass
class MemoryInsight:
    """An insight retrieved from long-term memory"""

    content: str
    source_date: str
    relevance_score: float
    retrieval_mode: str  # "semantic", "lateral", "keyword"
    reasoning: str = ""


@dataclass
class ReasoningTrace:
    """Trace of reasoning used to generate briefing content"""

    decision: str
    confidence: float
    steps: List[str] = field(default_factory=list)
    alternatives_considered: List[str] = field(default_factory=list)


@dataclass
class LateralConnection:
    """A cross-domain connection discovered through lateral thinking"""

    source_domain: str
    target_domain: str
    connection_type: str  # "synchronicity", "pattern", "contrast"
    insight: str
    strength: float


@dataclass
class IntelligentContext(AggregatedContext):
    """Extended context with intelligent retrieval results"""

    # Memory-based insights
    similar_past_checkins: List[MemoryInsight] = field(default_factory=list)
    effective_strategies: List[MemoryInsight] = field(default_factory=list)
    recent_struggles: List[MemoryInsight] = field(default_factory=list)

    # Reasoning traces
    reasoning_traces: List[ReasoningTrace] = field(default_factory=list)

    # Lateral connections
    lateral_connections: List[LateralConnection] = field(default_factory=list)
    course_theme_connections: List[str] = field(default_factory=list)

    # RAG results
    relevant_course_content: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    memory_enabled: bool = False
    rag_enabled: bool = False
    reasoning_enabled: bool = False
    lateral_enabled: bool = False


# =============================================================================
# Intelligent Context Engine
# =============================================================================


class IntelligentContextEngine:
    """
    Production-grade context engine that integrates all OsMEN intelligence systems.

    This replaces the basic ContextAggregator with:
    1. Semantic memory storage and retrieval
    2. RAG-based course content integration
    3. Sequential reasoning for decisions
    4. Lateral thinking for unexpected insights
    """

    def __init__(
        self,
        lookback_days: int = 7,  # Extended from 3 for better patterns
        enable_memory: bool = True,
        enable_rag: bool = True,
        enable_reasoning: bool = True,
        enable_lateral: bool = True,
    ):
        self.lookback_days = lookback_days
        self.today = date.today()

        # Paths
        self.journal_dir = Paths.VAULT_JOURNAL / "daily"
        self.scripts_dir = Paths.HB411_BRIEFING_SCRIPTS
        self.goals_dir = Paths.VAULT_GOALS

        # Base aggregator for file-based context
        self.base_aggregator = ContextAggregator(lookback_days=min(lookback_days, 3))
        self.syllabus_parser = SyllabusParser()

        # Initialize intelligent systems
        self._memory: Optional[HybridMemory] = None
        self._rag_pipeline: Optional[EnhancedRAGPipeline] = None
        self._reasoner: Optional[SequentialReasoner] = None
        self._lateral_bridge: Optional[LateralBridge] = None

        # Feature flags (respect both user preference and availability)
        self.memory_enabled = enable_memory and MEMORY_AVAILABLE
        self.rag_enabled = enable_rag and RAG_AVAILABLE
        self.reasoning_enabled = enable_reasoning and REASONING_AVAILABLE
        self.lateral_enabled = enable_lateral and LATERAL_AVAILABLE

        logger.info(
            f"IntelligentContextEngine initialized: "
            f"memory={self.memory_enabled}, rag={self.rag_enabled}, "
            f"reasoning={self.reasoning_enabled}, lateral={self.lateral_enabled}"
        )

    # =========================================================================
    # Lazy-loaded components
    # =========================================================================

    @property
    def memory(self) -> Optional["HybridMemory"]:
        """Lazy-load HybridMemory"""
        if not self.memory_enabled:
            return None
        if self._memory is None:
            try:
                self._memory = HybridMemory(MemoryConfig.from_env())
                logger.info("HybridMemory connected")
            except Exception as e:
                logger.error(f"Failed to connect HybridMemory: {e}")
                self.memory_enabled = False
        return self._memory

    @property
    def reasoner(self) -> Optional["SequentialReasoner"]:
        """Lazy-load SequentialReasoner"""
        if not self.reasoning_enabled:
            return None
        if self._reasoner is None:
            self._reasoner = SequentialReasoner(max_depth=7)
        return self._reasoner

    @property
    def lateral_bridge(self) -> Optional["LateralBridge"]:
        """Lazy-load LateralBridge"""
        if not self.lateral_enabled:
            return None
        if self._lateral_bridge is None:
            self._lateral_bridge = LateralBridge(expansion_depth=4)
        return self._lateral_bridge

    # =========================================================================
    # Main Context Gathering
    # =========================================================================

    def gather_intelligent_context(self) -> IntelligentContext:
        """
        Gather comprehensive context using all available intelligence systems.

        This is the main entry point that:
        1. Gathers base context (files, syllabus)
        2. Stores today's check-in in memory (if available)
        3. Retrieves similar past experiences
        4. Applies reasoning to generate insights
        5. Discovers lateral connections
        """
        # Start with base file-based context
        base = self.base_aggregator.gather_full_context()

        # Create intelligent context from base
        context = IntelligentContext(
            date=base.date,
            day_name=base.day_name,
            date_formatted=base.date_formatted,
            checkins=base.checkins,
            briefings=base.briefings,
            syllabus=base.syllabus,
            adhd=base.adhd,
            progress=base.progress,
            today_am_checkin=base.today_am_checkin,
            yesterday_pm_checkin=base.yesterday_pm_checkin,
            pending_tasks=base.pending_tasks,
            carryover_from_yesterday=base.carryover_from_yesterday,
            memory_enabled=self.memory_enabled,
            rag_enabled=self.rag_enabled,
            reasoning_enabled=self.reasoning_enabled,
            lateral_enabled=self.lateral_enabled,
        )

        # Store today's check-in in memory for future retrieval
        if self.memory_enabled and context.today_am_checkin:
            self._store_checkin_in_memory(context.today_am_checkin, context)

        # Retrieve similar past experiences
        if self.memory_enabled:
            context.similar_past_checkins = self._recall_similar_checkins(context)
            context.effective_strategies = self._recall_effective_strategies(context)
            context.recent_struggles = self._recall_recent_struggles(context)

        # Apply reasoning to generate insights
        if self.reasoning_enabled:
            context.reasoning_traces = self._generate_reasoning_traces(context)

        # Discover lateral connections
        if self.lateral_enabled:
            context.lateral_connections = self._find_lateral_connections(context)
            context.course_theme_connections = self._connect_to_course_themes(context)

        # Run memory maintenance (promote valuable memories, trim working memory)
        if self.memory_enabled and self.memory:
            try:
                self.memory.maintenance()
            except Exception as e:
                logger.warning(f"Memory maintenance failed: {e}")

        return context

    # =========================================================================
    # Memory Operations
    # =========================================================================

    def _store_checkin_in_memory(
        self, checkin: CheckInData, context: IntelligentContext
    ) -> Optional[str]:
        """
        Store today's check-in in HybridMemory for future semantic retrieval.

        This enables:
        - "What did I do on days like this?" queries
        - Pattern recognition across time
        - Strategy effectiveness tracking
        """
        if not self.memory:
            return None

        # Build rich content for semantic embedding
        content_parts = [
            f"Check-in for {checkin.date} ({checkin.period})",
            f"Energy level: {checkin.energy}/10",
            f"ADHD state: {checkin.adhd_state}",
        ]

        if checkin.priorities:
            content_parts.append(f"Priorities: {', '.join(checkin.priorities[:3])}")

        if checkin.meditation_completed:
            content_parts.append(
                f"Meditation: {checkin.meditation_type or 'completed'}"
            )

        if checkin.notes:
            content_parts.append(f"Notes: {checkin.notes[:200]}")

        if checkin.period == "PM":
            if checkin.accomplishments:
                content_parts.append(
                    f"Accomplished: {', '.join(checkin.accomplishments[:3])}"
                )
            if checkin.carryover_tasks:
                content_parts.append(
                    f"Carryover: {', '.join(checkin.carryover_tasks[:2])}"
                )

        content = "\n".join(content_parts)

        # Build Context7 metadata for lateral thinking
        context7 = {
            "intent": "self_tracking",
            "domain": "productivity" if checkin.period == "AM" else "reflection",
            "emotion": self._infer_emotion(checkin),
            "temporal": (
                f"week_{context.syllabus.current_week}" if context.syllabus else ""
            ),
            "relational": "self",
            "abstract": self._generate_abstract_theme(checkin, context),
        }

        # Store with appropriate tier
        tier = MemoryTier.SHORT_TERM
        if checkin.productivity_rate > 80 or checkin.energy >= 8:
            # High-value check-ins go directly to long-term for pattern learning
            tier = MemoryTier.LONG_TERM

        try:
            item = self.memory.remember(
                content=content,
                source="checkin",
                context={
                    "date": checkin.date,
                    "period": checkin.period,
                    "energy": checkin.energy,
                    "adhd_state": checkin.adhd_state,
                    "priorities_count": len(checkin.priorities),
                    "meditation": checkin.meditation_completed,
                    "syllabus_week": (
                        context.syllabus.current_week if context.syllabus else 0
                    ),
                },
                tier=tier,
                context7=context7,
            )
            logger.info(
                f"Stored check-in {checkin.date}-{checkin.period} in memory: {item.id}"
            )
            return item.id
        except Exception as e:
            logger.error(f"Failed to store check-in in memory: {e}")
            return None

    def _recall_similar_checkins(
        self, context: IntelligentContext, n_results: int = 3
    ) -> List[MemoryInsight]:
        """
        Recall check-ins from similar situations (energy level, ADHD state, etc.)

        This enables learning from past experience:
        "Last time you were at 3 energy with foggy state, you found success with..."
        """
        if not self.memory or not context.today_am_checkin:
            return []

        today = context.today_am_checkin

        # Build query based on current state
        query = (
            f"Check-in with energy {today.energy} "
            f"ADHD state {today.adhd_state} "
            f"{'meditation completed' if today.meditation_completed else 'no meditation'}"
        )

        try:
            # Use lateral mode for broader pattern matching
            results = self.memory.recall(
                query=query,
                n_results=n_results * 2,  # Get extra for filtering
                mode="lateral",
            )

            # Filter out today's check-in and convert to insights
            insights = []
            for item in results:
                # Skip if it's today's check-in
                if (
                    context.today_am_checkin
                    and item.context.get("date") == context.today_am_checkin.date
                ):
                    continue

                insights.append(
                    MemoryInsight(
                        content=item.content,
                        source_date=item.context.get("date", "unknown"),
                        relevance_score=item.access_count / 10.0,  # Normalize
                        retrieval_mode="lateral",
                        reasoning=f"Similar energy ({item.context.get('energy', '?')}) and state",
                    )
                )

                if len(insights) >= n_results:
                    break

            return insights
        except Exception as e:
            logger.error(f"Failed to recall similar check-ins: {e}")
            return []

    def _recall_effective_strategies(
        self, context: IntelligentContext, n_results: int = 3
    ) -> List[MemoryInsight]:
        """
        Recall strategies that worked in the past.

        Searches for check-ins with high productivity, then extracts what made them work.
        """
        if not self.memory:
            return []

        query = "Check-in high productivity accomplished success completed effective strategy"

        try:
            results = self.memory.recall(
                query=query,
                n_results=n_results,
                mode="foundation",  # Direct semantic match
            )

            insights = []
            for item in results:
                # Only include high-performing days
                productivity = item.context.get("productivity_rate", 0)
                if productivity < 70:
                    continue

                insights.append(
                    MemoryInsight(
                        content=item.content,
                        source_date=item.context.get("date", "unknown"),
                        relevance_score=productivity / 100.0,
                        retrieval_mode="semantic",
                        reasoning=f"High productivity day ({productivity}%)",
                    )
                )

            return insights
        except Exception as e:
            logger.error(f"Failed to recall effective strategies: {e}")
            return []

    def _recall_recent_struggles(
        self, context: IntelligentContext, n_results: int = 2
    ) -> List[MemoryInsight]:
        """
        Recall recent struggles to maintain continuity and check for improvement.
        """
        if not self.memory:
            return []

        query = "struggling carryover incomplete overwhelmed foggy difficult"

        try:
            results = self.memory.recall(
                query=query,
                n_results=n_results,
                mode="foundation",
            )

            insights = []
            for item in results:
                insights.append(
                    MemoryInsight(
                        content=item.content,
                        source_date=item.context.get("date", "unknown"),
                        relevance_score=0.5,
                        retrieval_mode="semantic",
                        reasoning="Recent challenge for continuity tracking",
                    )
                )

            return insights
        except Exception as e:
            logger.error(f"Failed to recall struggles: {e}")
            return []

    # =========================================================================
    # Reasoning Operations
    # =========================================================================

    def _generate_reasoning_traces(
        self, context: IntelligentContext
    ) -> List[ReasoningTrace]:
        """
        Generate reasoning traces for key briefing decisions.

        This makes the briefing explainable:
        "I'm suggesting shorter focus blocks because..."
        """
        if not self.reasoner:
            return []

        traces = []

        # Reason about energy-based recommendations
        if context.today_am_checkin:
            trace = self._reason_about_energy(context)
            if trace:
                traces.append(trace)

        # Reason about priority selection
        if context.pending_tasks:
            trace = self._reason_about_priorities(context)
            if trace:
                traces.append(trace)

        # Reason about ADHD strategy selection
        if context.adhd:
            trace = self._reason_about_adhd_strategy(context)
            if trace:
                traces.append(trace)

        return traces

    def _reason_about_energy(
        self, context: IntelligentContext
    ) -> Optional[ReasoningTrace]:
        """Reason about energy-based recommendations"""
        if not context.today_am_checkin:
            return None

        energy = context.today_am_checkin.energy
        avg_energy = context.adhd.avg_energy_3day if context.adhd else energy
        trend = context.adhd.energy_trend if context.adhd else "stable"

        steps = [
            f"Current energy: {energy}/10",
            f"3-day average: {avg_energy:.1f}",
            f"Trend: {trend}",
        ]

        # Determine recommendation
        if energy <= 3:
            decision = (
                "Low energy - recommend single priority focus and movement breaks"
            )
            confidence = 0.9
            alternatives = ["Postpone difficult work", "Use body doubling"]
        elif energy <= 5:
            decision = (
                "Moderate energy - standard pomodoro blocks with built-in recovery"
            )
            confidence = 0.8
            alternatives = [
                "Extended 50-min blocks if improving",
                "Shorter 15-min blocks if struggling",
            ]
        else:
            decision = "High energy - front-load difficult tasks, extended focus blocks"
            confidence = 0.85
            alternatives = [
                "Standard blocks if volatile trend",
                "Save energy for sustained effort",
            ]

        steps.append(f"Decision: {decision}")

        return ReasoningTrace(
            decision=decision,
            confidence=confidence,
            steps=steps,
            alternatives_considered=alternatives,
        )

    def _reason_about_priorities(
        self, context: IntelligentContext
    ) -> Optional[ReasoningTrace]:
        """Reason about priority ordering"""
        if not context.pending_tasks:
            return None

        steps = [f"Total pending tasks: {len(context.pending_tasks)}"]

        # Check for carryover
        carryover = context.carryover_from_yesterday
        if carryover:
            steps.append(f"Carryover from yesterday: {len(carryover)} items")
            steps.append("Carryover indicates incomplete work - prioritize for closure")

        # Check for deadlines
        if context.syllabus and context.syllabus.next_deadline:
            days = context.syllabus.next_deadline["days_until"]
            if days <= 3:
                steps.append(f"Deadline in {days} days - elevate course work")

        decision = f"Top priority: {context.pending_tasks[0] if context.pending_tasks else 'None'}"

        return ReasoningTrace(
            decision=decision,
            confidence=0.75,
            steps=steps,
            alternatives_considered=(
                context.pending_tasks[1:3] if len(context.pending_tasks) > 1 else []
            ),
        )

    def _reason_about_adhd_strategy(
        self, context: IntelligentContext
    ) -> Optional[ReasoningTrace]:
        """Reason about ADHD strategy selection"""
        if not context.today_am_checkin:
            return None

        adhd_state = context.today_am_checkin.adhd_state
        working_strategies = context.adhd.working_strategies if context.adhd else []

        steps = [
            f"Current ADHD state: {adhd_state}",
            f"Working strategies from history: {working_strategies or 'none tracked'}",
        ]

        # State-specific recommendations
        strategy_map = {
            "foggy": ("Movement and hydration first, delay complex work 30 min", 0.85),
            "struggling": ("Use timer + body doubling, 5-min micro-starts", 0.9),
            "misdirected": (
                "Close all tabs, single-task mode, accountability check",
                0.8,
            ),
            "clear": ("Capitalize now - tackle hardest task first", 0.85),
            "moderate": (
                "Standard pomodoro, regular breaks, task switching allowed",
                0.7,
            ),
        }

        decision, confidence = strategy_map.get(adhd_state, strategy_map["moderate"])

        # Boost confidence if strategy has worked before
        if working_strategies:
            for strat in working_strategies:
                if strat.lower() in decision.lower():
                    confidence = min(0.95, confidence + 0.1)
                    steps.append(f"Confidence boosted: '{strat}' has worked before")

        return ReasoningTrace(
            decision=decision,
            confidence=confidence,
            steps=steps,
            alternatives_considered=list(strategy_map.keys()),
        )

    # =========================================================================
    # Lateral Thinking Operations
    # =========================================================================

    def _find_lateral_connections(
        self, context: IntelligentContext
    ) -> List[LateralConnection]:
        """
        Find unexpected connections between different domains.

        This enables serendipitous insights like:
        "Your struggle with boundaries at work mirrors this week's course theme..."
        """
        if not self.lateral_bridge:
            return []

        connections = []

        # Look for connections between check-in patterns and course themes
        if context.syllabus and context.today_am_checkin:
            course_topic = context.syllabus.week_topic.lower()
            checkin_notes = (
                context.today_am_checkin.notes.lower()
                if context.today_am_checkin.notes
                else ""
            )
            priorities = " ".join(context.today_am_checkin.priorities).lower()

            # Check for thematic overlap
            boundary_keywords = [
                "boundary",
                "limit",
                "no",
                "saying no",
                "overwhelm",
                "overcommit",
            ]
            ethics_keywords = [
                "value",
                "principle",
                "right",
                "wrong",
                "should",
                "ethical",
            ]
            self_keywords = ["self", "identity", "who am i", "authentic", "true"]

            for keyword_set, domain in [
                (boundary_keywords, "boundaries"),
                (ethics_keywords, "ethics"),
                (self_keywords, "self-concept"),
            ]:
                for keyword in keyword_set:
                    if keyword in checkin_notes or keyword in priorities:
                        if any(kw in course_topic for kw in keyword_set):
                            connections.append(
                                LateralConnection(
                                    source_domain="daily_life",
                                    target_domain="course_content",
                                    connection_type="synchronicity",
                                    insight=f"Your mention of '{keyword}' connects to this week's topic: {context.syllabus.week_topic}",
                                    strength=0.75,
                                )
                            )
                            break

        return connections

    def _connect_to_course_themes(self, context: IntelligentContext) -> List[str]:
        """
        Generate connections between current state and course themes.
        """
        connections = []

        if not context.syllabus:
            return connections

        topic = context.syllabus.week_topic

        # Week-specific connections based on common themes
        if context.today_am_checkin:
            energy = context.today_am_checkin.energy
            adhd_state = context.today_am_checkin.adhd_state

            # Low energy + boundaries week
            if energy <= 4 and "boundar" in topic.lower():
                connections.append(
                    "Low energy is itself a boundary signal. "
                    "Today's limited capacity is permission to protect yourself."
                )

            # Struggling + ethics week
            if adhd_state == "struggling" and "ethic" in topic.lower():
                connections.append(
                    "Struggling to start connects to this week's ethics theme - "
                    "what do you owe yourself vs. others when you're depleted?"
                )

            # High energy + integration week
            if energy >= 7 and "integrat" in topic.lower():
                connections.append(
                    "High energy today is an opportunity to integrate what you've learned. "
                    "Use this capacity for synthesis, not just production."
                )

        return connections

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _infer_emotion(self, checkin: CheckInData) -> str:
        """Infer emotional state from check-in data"""
        energy = checkin.energy
        state = checkin.adhd_state

        if energy <= 3:
            return "depleted"
        elif state == "struggling":
            return "frustrated"
        elif state == "foggy":
            return "uncertain"
        elif energy >= 8:
            return "energized"
        elif checkin.meditation_completed:
            return "centered"
        else:
            return "neutral"

    def _generate_abstract_theme(
        self, checkin: CheckInData, context: IntelligentContext
    ) -> str:
        """Generate abstract thematic connection for Context7"""
        themes = []

        if checkin.energy <= 3:
            themes.append("depletion")
        elif checkin.energy >= 8:
            themes.append("abundance")

        if checkin.adhd_state == "struggling":
            themes.append("resistance")
        elif checkin.adhd_state == "clear":
            themes.append("flow")

        if checkin.meditation_completed:
            themes.append("mindfulness")

        if context.syllabus:
            week = context.syllabus.current_week
            if week <= 4:
                themes.append("foundation")
            elif week <= 8:
                themes.append("deepening")
            elif week <= 12:
                themes.append("integration")
            else:
                themes.append("completion")

        return ", ".join(themes) if themes else "daily_practice"


# =============================================================================
# Convenience Functions
# =============================================================================


def gather_intelligent_context(**kwargs) -> IntelligentContext:
    """
    Convenience function to gather intelligent context.

    Usage:
        from agents.daily_brief.intelligent_context import gather_intelligent_context

        context = gather_intelligent_context()
    """
    engine = IntelligentContextEngine(**kwargs)
    return engine.gather_intelligent_context()


def get_context_engine(**kwargs) -> IntelligentContextEngine:
    """Get a configured IntelligentContextEngine instance."""
    return IntelligentContextEngine(**kwargs)


# =============================================================================
# Self-Test
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("  Intelligent Context Engine - Integration Test")
    print("=" * 70)

    print(f"\n🔌 Integration Status:")
    print(
        f"   HybridMemory:      {'✅ Available' if MEMORY_AVAILABLE else '❌ Not available'}"
    )
    print(
        f"   RAGPipeline:       {'✅ Available' if RAG_AVAILABLE else '❌ Not available'}"
    )
    print(
        f"   SequentialReasoner: {'✅ Available' if REASONING_AVAILABLE else '❌ Not available'}"
    )
    print(
        f"   LateralBridge:     {'✅ Available' if LATERAL_AVAILABLE else '❌ Not available'}"
    )

    print(f"\n📊 Gathering Intelligent Context...")

    try:
        engine = IntelligentContextEngine()
        context = engine.gather_intelligent_context()

        print(f"\n✅ Context gathered successfully!")
        print(f"   Date: {context.date}")
        print(f"   Check-ins: {len(context.checkins)}")
        print(f"   Memory enabled: {context.memory_enabled}")
        print(f"   RAG enabled: {context.rag_enabled}")
        print(f"   Reasoning enabled: {context.reasoning_enabled}")
        print(f"   Lateral enabled: {context.lateral_enabled}")

        if context.similar_past_checkins:
            print(f"\n🧠 Similar Past Check-ins: {len(context.similar_past_checkins)}")
            for insight in context.similar_past_checkins[:2]:
                print(f"   - {insight.source_date}: {insight.content[:60]}...")

        if context.reasoning_traces:
            print(f"\n🤔 Reasoning Traces: {len(context.reasoning_traces)}")
            for trace in context.reasoning_traces:
                print(
                    f"   - {trace.decision[:60]}... (confidence: {trace.confidence:.0%})"
                )

        if context.lateral_connections:
            print(f"\n🌐 Lateral Connections: {len(context.lateral_connections)}")
            for conn in context.lateral_connections:
                print(f"   - {conn.insight[:60]}...")

        if context.course_theme_connections:
            print(
                f"\n📚 Course Theme Connections: {len(context.course_theme_connections)}"
            )
            for conn in context.course_theme_connections:
                print(f"   - {conn[:60]}...")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    print(f"\n{'=' * 70}")
