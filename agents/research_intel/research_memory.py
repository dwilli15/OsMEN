#!/usr/bin/env python3
"""
Research Memory Integration

Adds HybridMemory-backed storage and retrieval for research findings.

Capabilities:
- Store research findings for future recall
- Find similar past research
- Build research history and patterns
- Surface relevant past findings when researching new topics
"""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger("osmen.research.memory")

# Try to import HybridMemory
try:
    from integrations.memory import HybridMemory, MemoryConfig, MemoryItem, MemoryTier

    MEMORY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"HybridMemory not available for ResearchAgent: {e}")
    MEMORY_AVAILABLE = False
    HybridMemory = None  # type: ignore
    MemoryConfig = None  # type: ignore
    MemoryTier = None  # type: ignore


@dataclass
class ResearchRecall:
    """A recalled research finding"""

    topic: str
    summary: str
    key_points: List[str]
    relevance_score: float
    research_date: str
    depth: str
    mode: str


class ResearchMemoryIntegration:
    """
    HybridMemory integration for research findings.

    Enables the research agent to:
    1. Store research findings for future use
    2. Recall relevant past research
    3. Build research history
    4. Find connections between research topics
    """

    def __init__(self):
        """Initialize memory integration with lazy loading"""
        self._memory: Optional["HybridMemory"] = None
        self.enabled = MEMORY_AVAILABLE

        if self.enabled:
            logger.info("ResearchMemoryIntegration initialized (memory available)")
        else:
            logger.warning("ResearchMemoryIntegration disabled (memory unavailable)")

    @property
    def memory(self) -> Optional["HybridMemory"]:
        """Lazy-load HybridMemory"""
        if not self.enabled:
            return None
        if self._memory is None:
            try:
                self._memory = HybridMemory(MemoryConfig.from_env())
                logger.info("HybridMemory connected for research storage")
            except Exception as e:
                logger.error(f"Failed to connect HybridMemory: {e}")
                self.enabled = False
        return self._memory

    def store_research(
        self,
        topic: str,
        summary: str,
        key_points: List[str],
        sources: List[Dict] = None,
        depth: str = "medium",
        mode: str = "foundation",
        lateral_connections: List[str] = None,
    ) -> Optional[str]:
        """
        Store research findings in memory.

        Args:
            topic: Research topic
            summary: Research summary
            key_points: Key findings
            sources: Source documents
            depth: Research depth (shallow, medium, deep)
            mode: Retrieval mode used
            lateral_connections: Related domains found

        Returns:
            Memory ID if stored successfully
        """
        if not self.memory:
            return None

        sources = sources or []
        lateral_connections = lateral_connections or []

        # Build comprehensive content for semantic search
        content = (
            f"Research on {topic}. "
            f"{summary} "
            f"Key points: {'; '.join(key_points)}. "
            f"{'Related domains: ' + ', '.join(lateral_connections) if lateral_connections else ''}"
        )

        # Infer domain from topic and connections
        domain = self._infer_domain(topic, lateral_connections)

        # Context7 for lateral discovery
        context7 = {
            "intent": "research",
            "domain": domain,
            "emotion": "curious",
            "temporal": datetime.now().strftime("%Y-%m"),
            "spatial": f"depth_{depth}",
            "relational": (
                ", ".join(lateral_connections[:5])
                if lateral_connections
                else "standalone"
            ),
            "abstract": topic.lower().replace(" ", "_"),
        }

        try:
            item = self.memory.remember(
                content=content,
                source="research_intel",
                context={
                    "topic": topic,
                    "summary": summary,
                    "key_points": key_points,
                    "sources_count": len(sources),
                    "depth": depth,
                    "mode": mode,
                    "lateral_connections": lateral_connections,
                    "researched_at": datetime.now().isoformat(),
                },
                tier=MemoryTier.WORKING,  # Start in working, promote if accessed
                context7=context7,
            )
            logger.info(f"Stored research on '{topic}': {item.id}")
            return item.id
        except Exception as e:
            logger.error(f"Failed to store research on '{topic}': {e}")
            return None

    def _infer_domain(self, topic: str, connections: List[str]) -> str:
        """Infer research domain from topic and connections"""
        combined = f"{topic} {' '.join(connections)}".lower()

        domain_indicators = {
            "technical": [
                "code",
                "programming",
                "api",
                "software",
                "system",
                "architecture",
            ],
            "scientific": ["research", "study", "experiment", "theory", "hypothesis"],
            "psychology": ["therapy", "mental", "cognitive", "behavior", "emotion"],
            "business": ["strategy", "market", "product", "customer", "growth"],
            "health": ["medical", "health", "treatment", "wellness", "nutrition"],
            "education": ["learning", "teaching", "course", "curriculum", "student"],
        }

        for domain, indicators in domain_indicators.items():
            if any(ind in combined for ind in indicators):
                return domain

        return "general"

    def recall_similar_research(
        self, topic: str, n_results: int = 5, mode: str = "lateral"
    ) -> List[ResearchRecall]:
        """
        Find similar past research on a topic.

        Args:
            topic: Topic to find similar research for
            n_results: Maximum results to return
            mode: Search mode (foundation, lateral, factcheck)

        Returns:
            List of similar research findings
        """
        if not self.memory:
            return []

        try:
            results = self.memory.recall(
                query=f"research on {topic}", n_results=n_results, mode=mode
            )

            recalls = []
            for item in results:
                if item.source == "research_intel":
                    recalls.append(
                        ResearchRecall(
                            topic=item.context.get("topic", "Unknown"),
                            summary=item.context.get("summary", ""),
                            key_points=item.context.get("key_points", []),
                            relevance_score=0.8,
                            research_date=item.context.get("researched_at", ""),
                            depth=item.context.get("depth", "medium"),
                            mode=item.context.get("mode", "foundation"),
                        )
                    )

            return recalls

        except Exception as e:
            logger.error(f"Failed to recall similar research: {e}")
            return []

    def get_research_context(
        self, current_topic: str, max_context_items: int = 3
    ) -> Dict[str, Any]:
        """
        Get relevant research context for a new research session.

        Surfaces past research that might be useful for the current topic.

        Args:
            current_topic: Topic being researched now
            max_context_items: Maximum context items to include

        Returns:
            Dict with relevant past research and connections
        """
        context = {
            "similar_research": [],
            "related_topics": [],
            "recommended_depth": "medium",
            "insights": [],
        }

        if not self.memory:
            return context

        try:
            # Find similar past research
            similar = self.recall_similar_research(
                current_topic, n_results=max_context_items
            )

            for research in similar:
                context["similar_research"].append(
                    {
                        "topic": research.topic,
                        "summary_preview": (
                            research.summary[:200] if research.summary else ""
                        ),
                        "date": research.research_date,
                        "relevance": research.relevance_score,
                    }
                )

                # Collect related topics from key points
                for point in research.key_points[:2]:
                    if len(point) > 10:
                        context["related_topics"].append(point[:50])

            # Generate insights
            if similar:
                context["insights"].append(
                    f"Found {len(similar)} related past research topics"
                )

                # Recommend deeper research if topic was covered shallowly before
                shallow_research = [r for r in similar if r.depth == "shallow"]
                if shallow_research:
                    context["recommended_depth"] = "deep"
                    context["insights"].append(
                        f"Previous research on '{shallow_research[0].topic}' was shallow - recommend deep dive"
                    )

            return context

        except Exception as e:
            logger.error(f"Failed to get research context: {e}")
            return context

    def get_research_history(
        self, limit: int = 10, domain_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent research history.

        Args:
            limit: Maximum number of research items
            domain_filter: Optional domain to filter by

        Returns:
            List of recent research summaries
        """
        if not self.memory:
            return []

        try:
            # Query for all research items
            results = self.memory.recall(
                query="research",
                n_results=limit * 2,  # Over-fetch to account for filtering
                mode="foundation",
            )

            history = []
            for item in results:
                if item.source != "research_intel":
                    continue

                # Apply domain filter if specified
                if domain_filter and item.domain != domain_filter:
                    continue

                history.append(
                    {
                        "topic": item.context.get("topic", "Unknown"),
                        "summary_preview": item.context.get("summary", "")[:100],
                        "depth": item.context.get("depth", "medium"),
                        "date": item.context.get("researched_at", ""),
                        "domain": item.domain,
                    }
                )

                if len(history) >= limit:
                    break

            return history

        except Exception as e:
            logger.error(f"Failed to get research history: {e}")
            return []

    def find_research_gaps(self, domain: str, n_suggestions: int = 5) -> List[str]:
        """
        Suggest research gaps based on past research patterns.

        Args:
            domain: Domain to analyze
            n_suggestions: Number of suggestions to return

        Returns:
            List of suggested research topics
        """
        if not self.memory:
            return [f"Research {domain} fundamentals"]

        try:
            # Get lateral connections in domain
            results = self.memory.recall(
                query=f"research in {domain}", n_results=20, mode="lateral"
            )

            # Collect all mentioned topics and lateral connections
            researched_topics = set()
            mentioned_connections = set()

            for item in results:
                if item.source == "research_intel":
                    researched_topics.add(item.context.get("topic", "").lower())
                    for conn in item.context.get("lateral_connections", []):
                        mentioned_connections.add(conn.lower())

            # Gaps are connections that were mentioned but not researched
            gaps = mentioned_connections - researched_topics

            suggestions = list(gaps)[:n_suggestions]

            if not suggestions:
                suggestions = [f"Deep dive into {domain}"]

            return suggestions

        except Exception as e:
            logger.error(f"Failed to find research gaps: {e}")
            return [f"Research {domain} fundamentals"]


# Singleton instance
_research_memory: Optional[ResearchMemoryIntegration] = None


def get_research_memory() -> ResearchMemoryIntegration:
    """Get or create the research memory integration singleton"""
    global _research_memory
    if _research_memory is None:
        _research_memory = ResearchMemoryIntegration()
    return _research_memory


# Self-test
if __name__ == "__main__":
    print("=" * 70)
    print("  Research Memory Integration - Self Test")
    print("=" * 70)

    rm = get_research_memory()

    print(f"\n🔌 Memory Available: {'✅ Yes' if rm.enabled else '❌ No'}")

    if rm.enabled:
        # Store test research
        print("\n📝 Storing test research...")
        memory_id = rm.store_research(
            topic="Machine Learning in Healthcare",
            summary="This research explores the application of machine learning algorithms in healthcare settings, focusing on diagnostic accuracy and patient outcomes.",
            key_points=[
                "ML models can improve diagnostic accuracy by 15-20%",
                "Data privacy remains a key concern",
                "Integration with existing systems is challenging",
            ],
            depth="medium",
            mode="lateral",
            lateral_connections=["healthcare", "AI", "diagnostics", "privacy"],
        )
        print(f"   Stored: {memory_id}")

        # Recall similar research
        print("\n🔍 Recalling similar research...")
        similar = rm.recall_similar_research("AI in medicine", n_results=3)
        for r in similar:
            print(f"   - {r.topic} ({r.depth})")

        # Get context
        print("\n📊 Getting research context...")
        context = rm.get_research_context("healthcare AI applications")
        print(f"   Similar: {len(context['similar_research'])} items")
        print(f"   Recommended depth: {context['recommended_depth']}")
        for insight in context["insights"]:
            print(f"   💡 {insight}")

    print("\n" + "=" * 70)
