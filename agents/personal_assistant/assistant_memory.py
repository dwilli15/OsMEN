#!/usr/bin/env python3
"""
Personal Assistant Memory Integration

Adds HybridMemory-backed user preference learning and context.

Capabilities:
- Learn user preferences from interactions
- Remember user context across sessions
- Personalize responses based on history
- Surface relevant context for tasks/reminders
"""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger("osmen.assistant.memory")

# Try to import HybridMemory
try:
    from integrations.memory import HybridMemory, MemoryConfig, MemoryItem, MemoryTier

    MEMORY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"HybridMemory not available for PersonalAssistant: {e}")
    MEMORY_AVAILABLE = False
    HybridMemory = None  # type: ignore
    MemoryConfig = None  # type: ignore
    MemoryTier = None  # type: ignore


@dataclass
class UserPreference:
    """A learned user preference"""

    preference_type: str
    value: Any
    confidence: float
    learned_from: str
    learned_at: str


@dataclass
class RelevantContext:
    """Context relevant to current activity"""

    context_type: str
    content: str
    relevance_score: float
    source: str


class AssistantMemoryIntegration:
    """
    HybridMemory integration for personal assistant.

    Enables the assistant to:
    1. Learn user preferences over time
    2. Remember important context
    3. Personalize recommendations
    4. Surface relevant past interactions
    """

    def __init__(self):
        """Initialize memory integration with lazy loading"""
        self._memory: Optional["HybridMemory"] = None
        self.enabled = MEMORY_AVAILABLE

        if self.enabled:
            logger.info("AssistantMemoryIntegration initialized (memory available)")
        else:
            logger.warning("AssistantMemoryIntegration disabled (memory unavailable)")

    @property
    def memory(self) -> Optional["HybridMemory"]:
        """Lazy-load HybridMemory"""
        if not self.enabled:
            return None
        if self._memory is None:
            try:
                self._memory = HybridMemory(MemoryConfig.from_env())
                logger.info("HybridMemory connected for assistant memory")
            except Exception as e:
                logger.error(f"Failed to connect HybridMemory: {e}")
                self.enabled = False
        return self._memory

    def learn_preference(
        self, preference_type: str, value: Any, context: str, confidence: float = 0.8
    ) -> Optional[str]:
        """
        Store a learned user preference.

        Args:
            preference_type: Type of preference (e.g., "work_hours", "priority_style")
            value: The preference value
            context: Context in which this was learned
            confidence: How confident we are about this preference

        Returns:
            Memory ID if stored successfully
        """
        if not self.memory:
            return None

        content = (
            f"User preference: {preference_type}. "
            f"Value: {value}. "
            f"Learned from: {context}. "
            f"Confidence: {confidence}."
        )

        # Context7 for preference discovery
        context7 = {
            "intent": "preference",
            "domain": self._categorize_preference(preference_type),
            "emotion": "neutral",
            "temporal": datetime.now().strftime("%Y-%m"),
            "spatial": "personal",
            "relational": "user",
            "abstract": preference_type.replace("_", " "),
        }

        try:
            item = self.memory.remember(
                content=content,
                source="assistant_preference",
                context={
                    "preference_type": preference_type,
                    "value": value,
                    "learned_context": context,
                    "confidence": confidence,
                    "learned_at": datetime.now().isoformat(),
                },
                tier=MemoryTier.LONG_TERM,  # Preferences are long-term
                context7=context7,
            )
            logger.info(f"Learned preference '{preference_type}': {value}")
            return item.id
        except Exception as e:
            logger.error(f"Failed to store preference: {e}")
            return None

    def _categorize_preference(self, preference_type: str) -> str:
        """Categorize preference into domain"""
        scheduling = ["work_hours", "meeting_time", "reminder_timing", "schedule"]
        productivity = ["priority_style", "task_format", "focus_time", "work_style"]
        communication = ["notification", "reminder_style", "language", "tone"]

        pref_lower = preference_type.lower()

        if any(s in pref_lower for s in scheduling):
            return "scheduling"
        elif any(p in pref_lower for p in productivity):
            return "productivity"
        elif any(c in pref_lower for c in communication):
            return "communication"

        return "general"

    def get_preference(self, preference_type: str) -> Optional[UserPreference]:
        """
        Retrieve a learned user preference.

        Args:
            preference_type: Type of preference to retrieve

        Returns:
            UserPreference if found
        """
        if not self.memory:
            return None

        try:
            results = self.memory.recall(
                query=f"user preference {preference_type}",
                n_results=3,
                mode="foundation",
            )

            for item in results:
                if item.source == "assistant_preference":
                    if item.context.get("preference_type") == preference_type:
                        return UserPreference(
                            preference_type=preference_type,
                            value=item.context.get("value"),
                            confidence=item.context.get("confidence", 0.5),
                            learned_from=item.context.get("learned_context", ""),
                            learned_at=item.context.get("learned_at", ""),
                        )

            return None

        except Exception as e:
            logger.error(f"Failed to get preference: {e}")
            return None

    def get_all_preferences(self) -> List[UserPreference]:
        """Get all learned user preferences."""
        if not self.memory:
            return []

        try:
            results = self.memory.recall(
                query="user preferences", n_results=50, mode="foundation"
            )

            preferences = []
            seen_types = set()

            for item in results:
                if item.source == "assistant_preference":
                    pref_type = item.context.get("preference_type", "")
                    if pref_type and pref_type not in seen_types:
                        seen_types.add(pref_type)
                        preferences.append(
                            UserPreference(
                                preference_type=pref_type,
                                value=item.context.get("value"),
                                confidence=item.context.get("confidence", 0.5),
                                learned_from=item.context.get("learned_context", ""),
                                learned_at=item.context.get("learned_at", ""),
                            )
                        )

            return preferences

        except Exception as e:
            logger.error(f"Failed to get preferences: {e}")
            return []

    def store_interaction(
        self, interaction_type: str, content: str, metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Store an interaction for context learning.

        Args:
            interaction_type: Type of interaction (e.g., "task_creation", "query")
            content: Content of the interaction
            metadata: Additional metadata

        Returns:
            Memory ID if stored successfully
        """
        if not self.memory:
            return None

        metadata = metadata or {}

        # Context7 for interaction
        context7 = {
            "intent": interaction_type,
            "domain": metadata.get("domain", "general"),
            "emotion": metadata.get("emotion", "neutral"),
            "temporal": datetime.now().strftime("%Y-%m-%d"),
            "spatial": "personal",
            "relational": "user",
            "abstract": interaction_type.replace("_", " "),
        }

        try:
            item = self.memory.remember(
                content=f"{interaction_type}: {content}",
                source="assistant_interaction",
                context={
                    "interaction_type": interaction_type,
                    "timestamp": datetime.now().isoformat(),
                    **metadata,
                },
                tier=MemoryTier.WORKING,  # Interactions start in working
                context7=context7,
            )
            logger.debug(f"Stored interaction: {interaction_type}")
            return item.id
        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")
            return None

    def get_relevant_context(
        self, current_activity: str, n_results: int = 5
    ) -> List[RelevantContext]:
        """
        Get context relevant to current activity.

        Args:
            current_activity: What the user is currently doing
            n_results: Maximum results to return

        Returns:
            List of relevant context items
        """
        if not self.memory:
            return []

        try:
            results = self.memory.recall(
                query=current_activity,
                n_results=n_results,
                mode="lateral",  # Use lateral for non-obvious connections
            )

            contexts = []
            for item in results:
                if item.source in ["assistant_interaction", "assistant_preference"]:
                    contexts.append(
                        RelevantContext(
                            context_type=item.source,
                            content=item.content[:200],
                            relevance_score=0.8,
                            source=item.context.get("interaction_type", "preference"),
                        )
                    )

            return contexts

        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return []

    def get_personalized_recommendations(
        self, task_context: str, n_recommendations: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations based on user history.

        Args:
            task_context: Context of the current task
            n_recommendations: Number of recommendations

        Returns:
            List of personalized recommendations
        """
        if not self.memory:
            return [{"type": "generic", "suggestion": "No personalization available"}]

        recommendations = []

        try:
            # Get relevant preferences
            preferences = self.get_all_preferences()

            # Get relevant past interactions
            context = self.get_relevant_context(task_context, n_results=10)

            # Build recommendations
            for pref in preferences[:n_recommendations]:
                if pref.confidence > 0.6:
                    recommendations.append(
                        {
                            "type": "preference",
                            "suggestion": f"Based on your preference for {pref.preference_type}: {pref.value}",
                            "confidence": pref.confidence,
                        }
                    )

            # Add context-based recommendations
            for ctx in context[: n_recommendations - len(recommendations)]:
                recommendations.append(
                    {
                        "type": "context",
                        "suggestion": f"Related to past activity: {ctx.content[:100]}",
                        "relevance": ctx.relevance_score,
                    }
                )

            if not recommendations:
                recommendations.append(
                    {
                        "type": "generic",
                        "suggestion": "Start creating tasks to build your personalized experience",
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return [
                {"type": "error", "suggestion": "Unable to generate recommendations"}
            ]

    def infer_preferences_from_history(self) -> List[Dict[str, Any]]:
        """
        Analyze interaction history to infer preferences.

        Returns:
            List of inferred preferences
        """
        if not self.memory:
            return []

        try:
            # Get all interactions
            results = self.memory.recall(
                query="task creation interaction", n_results=100, mode="foundation"
            )

            # Analyze patterns
            time_of_day = {}
            priorities = {}

            for item in results:
                if item.source == "assistant_interaction":
                    # Extract timestamp hour
                    ts = item.context.get("timestamp", "")
                    if ts:
                        try:
                            hour = datetime.fromisoformat(ts).hour
                            period = (
                                "morning"
                                if 5 <= hour < 12
                                else (
                                    "afternoon"
                                    if 12 <= hour < 17
                                    else "evening" if 17 <= hour < 21 else "night"
                                )
                            )
                            time_of_day[period] = time_of_day.get(period, 0) + 1
                        except:
                            pass

                    # Extract priority if present
                    priority = item.context.get("priority")
                    if priority:
                        priorities[priority] = priorities.get(priority, 0) + 1

            inferences = []

            # Infer preferred work time
            if time_of_day:
                preferred_time = max(time_of_day, key=time_of_day.get)
                inferences.append(
                    {
                        "preference_type": "active_time",
                        "inferred_value": preferred_time,
                        "evidence_count": time_of_day[preferred_time],
                        "confidence": min(time_of_day[preferred_time] / 10, 1.0),
                    }
                )

            # Infer priority style
            if priorities:
                common_priority = max(priorities, key=priorities.get)
                inferences.append(
                    {
                        "preference_type": "default_priority",
                        "inferred_value": common_priority,
                        "evidence_count": priorities[common_priority],
                        "confidence": min(priorities[common_priority] / 10, 1.0),
                    }
                )

            return inferences

        except Exception as e:
            logger.error(f"Failed to infer preferences: {e}")
            return []


# Singleton instance
_assistant_memory: Optional[AssistantMemoryIntegration] = None


def get_assistant_memory() -> AssistantMemoryIntegration:
    """Get or create the assistant memory integration singleton"""
    global _assistant_memory
    if _assistant_memory is None:
        _assistant_memory = AssistantMemoryIntegration()
    return _assistant_memory


# Self-test
if __name__ == "__main__":
    print("=" * 70)
    print("  Assistant Memory Integration - Self Test")
    print("=" * 70)

    am = get_assistant_memory()

    print(f"\n🔌 Memory Available: {'✅ Yes' if am.enabled else '❌ No'}")

    if am.enabled:
        # Learn a preference
        print("\n📝 Learning test preference...")
        memory_id = am.learn_preference(
            preference_type="work_hours",
            value="9am-5pm",
            context="User mentioned they work standard hours",
            confidence=0.85,
        )
        print(f"   Stored: {memory_id}")

        # Store an interaction
        print("\n💬 Storing test interaction...")
        memory_id = am.store_interaction(
            interaction_type="task_creation",
            content="Created high-priority task for project review",
            metadata={"priority": "high", "domain": "work"},
        )
        print(f"   Stored: {memory_id}")

        # Get preferences
        print("\n🔍 Retrieving preferences...")
        pref = am.get_preference("work_hours")
        if pref:
            print(f"   work_hours: {pref.value} (confidence: {pref.confidence})")

        # Get recommendations
        print("\n💡 Getting personalized recommendations...")
        recs = am.get_personalized_recommendations("scheduling a meeting")
        for r in recs:
            print(f"   - {r['type']}: {r['suggestion'][:60]}...")

    print("\n" + "=" * 70)
