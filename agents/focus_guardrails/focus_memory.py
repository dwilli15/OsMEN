#!/usr/bin/env python3
"""
Focus Memory Integration

Adds HybridMemory-backed pattern learning to FocusGuardrailsAgent.

Capabilities:
- Store focus session outcomes with semantic metadata
- Recall similar past sessions to predict success
- Learn which blocking strategies work best
- Track productivity patterns over time
- Provide insights for session planning
"""

import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger("osmen.focus.memory")

# Try to import HybridMemory
try:
    from integrations.memory import HybridMemory, MemoryConfig, MemoryItem, MemoryTier

    MEMORY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"HybridMemory not available for FocusGuardrails: {e}")
    MEMORY_AVAILABLE = False
    HybridMemory = None  # type: ignore
    MemoryConfig = None  # type: ignore
    MemoryTier = None  # type: ignore


@dataclass
class FocusPattern:
    """A learned focus pattern from past sessions"""

    time_of_day: str  # morning, afternoon, evening, night
    day_of_week: str  # Monday, Tuesday, etc.
    duration_minutes: int
    success_rate: float  # 0.0 to 1.0
    avg_interruptions: float
    effective_blocks: List[str]  # Sites that helped when blocked
    ineffective_blocks: List[str]  # Sites that didn't matter
    productivity_rating: float  # Self-reported 1-5


@dataclass
class FocusInsight:
    """An actionable insight from focus memory"""

    insight_type: str  # "recommendation", "warning", "pattern"
    message: str
    confidence: float
    source_sessions: int
    data: Dict[str, Any]


class FocusMemoryIntegration:
    """
    HybridMemory integration for learning from focus sessions.

    Enables the focus agent to:
    1. Remember outcomes of past sessions
    2. Learn what works for this specific user
    3. Provide personalized recommendations
    4. Predict session success likelihood
    """

    def __init__(self):
        """Initialize memory integration with lazy loading"""
        self._memory: Optional[HybridMemory] = None
        self.enabled = MEMORY_AVAILABLE

        if self.enabled:
            logger.info("FocusMemoryIntegration initialized (memory available)")
        else:
            logger.warning("FocusMemoryIntegration disabled (memory unavailable)")

    @property
    def memory(self) -> Optional["HybridMemory"]:
        """Lazy-load HybridMemory"""
        if not self.enabled:
            return None
        if self._memory is None:
            try:
                self._memory = HybridMemory(MemoryConfig.from_env())
                logger.info("HybridMemory connected for focus sessions")
            except Exception as e:
                logger.error(f"Failed to connect HybridMemory: {e}")
                self.enabled = False
        return self._memory

    def store_session(
        self,
        session_data: Dict[str, Any],
        outcome: str,  # "completed", "interrupted", "abandoned"
        productivity_rating: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Optional[str]:
        """
        Store a focus session in memory for pattern learning.

        Args:
            session_data: Session information (id, duration, blocked_sites, etc.)
            outcome: How the session ended
            productivity_rating: Self-reported productivity (1-5)
            notes: Optional notes about the session

        Returns:
            Memory ID if stored successfully
        """
        if not self.memory:
            return None

        # Parse session timing
        start_time = datetime.fromisoformat(
            session_data.get("start_time", datetime.now().isoformat())
        )

        # Determine time of day
        hour = start_time.hour
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        # Build content string for semantic search
        blocked_sites = session_data.get("blocked_sites", [])
        duration = session_data.get("duration_minutes", 25)
        interruptions = session_data.get("interruptions", 0)

        content = (
            f"Focus session on {start_time.strftime('%A')} {time_of_day}: "
            f"{duration} minutes, {outcome}. "
            f"{'Blocked: ' + ', '.join(blocked_sites[:5]) + '. ' if blocked_sites else ''}"
            f"Interruptions: {interruptions}. "
            f"{'Productivity: ' + str(productivity_rating) + '/5. ' if productivity_rating else ''}"
            f"{notes or ''}"
        )

        # Context7 dimensions for lateral connections
        context7 = {
            "intent": "focus",
            "domain": "productivity",
            "emotion": self._infer_emotion(outcome, productivity_rating),
            "temporal": f"{start_time.strftime('%A')}_{time_of_day}",
            "spatial": "workspace",
            "relational": "self",
            "abstract": self._generate_abstract_theme(
                outcome, interruptions, productivity_rating
            ),
        }

        # Determine tier based on outcome
        tier = MemoryTier.LONG_TERM if outcome == "completed" else MemoryTier.SHORT_TERM

        try:
            item = self.memory.remember(
                content=content,
                source="focus_session",
                context={
                    "session_id": session_data.get("id"),
                    "outcome": outcome,
                    "duration_minutes": duration,
                    "blocked_sites": blocked_sites,
                    "interruptions": interruptions,
                    "productivity_rating": productivity_rating,
                    "time_of_day": time_of_day,
                    "day_of_week": start_time.strftime("%A"),
                    "date": start_time.date().isoformat(),
                },
                tier=tier,
                context7=context7,
            )
            logger.info(
                f"Stored focus session {session_data.get('id')} in memory: {item.id}"
            )
            return item.id
        except Exception as e:
            logger.error(f"Failed to store focus session: {e}")
            return None

    def _infer_emotion(self, outcome: str, productivity: Optional[float]) -> str:
        """Infer emotional state from session outcome"""
        if outcome == "completed":
            if productivity and productivity >= 4:
                return "satisfied"
            return "neutral"
        elif outcome == "interrupted":
            return "frustrated"
        else:
            return "disappointed"

    def _generate_abstract_theme(
        self, outcome: str, interruptions: int, productivity: Optional[float]
    ) -> str:
        """Generate abstract theme for lateral connections"""
        themes = []

        if outcome == "completed":
            themes.append("persistence")
            if interruptions == 0:
                themes.append("flow_state")
            elif interruptions <= 2:
                themes.append("resilience")
        elif interruptions > 3:
            themes.append("distraction")

        if productivity:
            if productivity >= 4:
                themes.append("effectiveness")
            elif productivity <= 2:
                themes.append("struggle")

        return " ".join(themes) if themes else "focus"

    def get_insights_for_session(
        self,
        duration_minutes: int = 25,
        time_of_day: Optional[str] = None,
        n_insights: int = 3,
    ) -> List[FocusInsight]:
        """
        Get personalized insights for planning a focus session.

        Args:
            duration_minutes: Planned session duration
            time_of_day: Current time of day (auto-detected if None)
            n_insights: Number of insights to return

        Returns:
            List of actionable insights based on past patterns
        """
        if not self.memory:
            return []

        # Auto-detect time of day
        if time_of_day is None:
            hour = datetime.now().hour
            if 5 <= hour < 12:
                time_of_day = "morning"
            elif 12 <= hour < 17:
                time_of_day = "afternoon"
            elif 17 <= hour < 21:
                time_of_day = "evening"
            else:
                time_of_day = "night"

        insights = []

        try:
            # Query for similar past sessions
            query = f"Focus session {time_of_day} {duration_minutes} minutes"
            results = self.memory.recall(
                query=query, n_results=10, mode="lateral"  # Cross-domain connections
            )

            if not results:
                return [
                    FocusInsight(
                        insight_type="recommendation",
                        message="No past sessions recorded yet. This will be your baseline!",
                        confidence=0.5,
                        source_sessions=0,
                        data={},
                    )
                ]

            # Analyze patterns
            completed = [r for r in results if r.context.get("outcome") == "completed"]
            total = len(results)
            success_rate = len(completed) / total if total > 0 else 0

            # Success rate insight
            if success_rate >= 0.7:
                insights.append(
                    FocusInsight(
                        insight_type="pattern",
                        message=f"You complete {success_rate*100:.0f}% of sessions at this time. Keep it up!",
                        confidence=min(0.9, 0.5 + total * 0.05),
                        source_sessions=total,
                        data={"success_rate": success_rate},
                    )
                )
            elif success_rate < 0.4 and total >= 3:
                insights.append(
                    FocusInsight(
                        insight_type="warning",
                        message=f"Only {success_rate*100:.0f}% of {time_of_day} sessions complete. Consider a different time.",
                        confidence=min(0.9, 0.5 + total * 0.05),
                        source_sessions=total,
                        data={"success_rate": success_rate},
                    )
                )

            # Find effective blocking patterns
            if completed:
                all_blocked = []
                for r in completed:
                    all_blocked.extend(r.context.get("blocked_sites", []))

                if all_blocked:
                    # Count most common blocked sites in successful sessions
                    from collections import Counter

                    common_blocks = Counter(all_blocked).most_common(3)

                    insights.append(
                        FocusInsight(
                            insight_type="recommendation",
                            message=f"Blocking {common_blocks[0][0]} helps. Used in {common_blocks[0][1]} successful sessions.",
                            confidence=0.7,
                            source_sessions=len(completed),
                            data={"effective_blocks": [b[0] for b in common_blocks]},
                        )
                    )

            # Duration insight
            avg_productivity = sum(
                r.context.get("productivity_rating", 3)
                for r in results
                if r.context.get("productivity_rating")
            ) / max(
                1, len([r for r in results if r.context.get("productivity_rating")])
            )

            if avg_productivity >= 3.5:
                insights.append(
                    FocusInsight(
                        insight_type="pattern",
                        message=f"Average productivity: {avg_productivity:.1f}/5. You're on track!",
                        confidence=0.8,
                        source_sessions=total,
                        data={"avg_productivity": avg_productivity},
                    )
                )

        except Exception as e:
            logger.error(f"Failed to get focus insights: {e}")

        return insights[:n_insights]

    def get_best_time_recommendation(self) -> Optional[FocusInsight]:
        """
        Recommend the best time of day for focus sessions based on history.

        Returns:
            Insight with recommendation or None if not enough data
        """
        if not self.memory:
            return None

        try:
            # Query all focus sessions
            results = self.memory.recall(
                query="Focus session completed productivity",
                n_results=50,
                mode="foundation",
            )

            if len(results) < 5:
                return None

            # Group by time of day
            by_time: Dict[str, List[float]] = {}
            for r in results:
                time_of_day = r.context.get("time_of_day", "unknown")
                outcome = r.context.get("outcome")
                productivity = r.context.get("productivity_rating", 3)

                if time_of_day not in by_time:
                    by_time[time_of_day] = []

                # Score: completed = productivity, else = 1
                score = productivity if outcome == "completed" else 1
                by_time[time_of_day].append(score)

            # Find best time
            best_time = None
            best_score = 0

            for time, scores in by_time.items():
                if len(scores) >= 2:  # Need at least 2 sessions
                    avg = sum(scores) / len(scores)
                    if avg > best_score:
                        best_score = avg
                        best_time = time

            if best_time:
                return FocusInsight(
                    insight_type="recommendation",
                    message=f"Your peak focus time is {best_time} (avg score: {best_score:.1f}/5)",
                    confidence=min(0.9, 0.5 + len(results) * 0.01),
                    source_sessions=len(results),
                    data={"best_time": best_time, "avg_score": best_score},
                )

        except Exception as e:
            logger.error(f"Failed to get best time recommendation: {e}")

        return None


# Singleton instance
_focus_memory: Optional[FocusMemoryIntegration] = None


def get_focus_memory() -> FocusMemoryIntegration:
    """Get or create the focus memory integration singleton"""
    global _focus_memory
    if _focus_memory is None:
        _focus_memory = FocusMemoryIntegration()
    return _focus_memory


# Self-test
if __name__ == "__main__":
    print("=" * 70)
    print("  Focus Memory Integration - Self Test")
    print("=" * 70)

    fm = get_focus_memory()

    print(f"\n🔌 Memory Available: {'✅ Yes' if fm.enabled else '❌ No'}")

    if fm.enabled:
        # Store a test session
        print("\n📝 Storing test session...")
        session_id = fm.store_session(
            session_data={
                "id": "test_session_001",
                "start_time": datetime.now().isoformat(),
                "duration_minutes": 25,
                "blocked_sites": ["youtube.com", "twitter.com"],
                "interruptions": 1,
            },
            outcome="completed",
            productivity_rating=4.0,
            notes="Good focus, got the main task done",
        )
        print(f"   Stored: {session_id}")

        # Get insights
        print("\n💡 Getting insights for next session...")
        insights = fm.get_insights_for_session(duration_minutes=25)
        for insight in insights:
            print(f"   [{insight.insight_type}] {insight.message}")

        # Get best time
        print("\n⏰ Best time recommendation...")
        best_time = fm.get_best_time_recommendation()
        if best_time:
            print(f"   {best_time.message}")
        else:
            print("   Not enough data yet")

    print("\n" + "=" * 70)
