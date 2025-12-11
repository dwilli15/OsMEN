"""
Sequential Reasoning - Deeply Embedded
======================================

Sequential reasoning as a first-class cognitive pattern, not just an MCP tool.

This module embeds step-by-step reasoning into ALL memory and retrieval operations:
- Query decomposition before search
- Progressive context building
- Hypothesis generation and verification
- Branching and backtracking support

Philosophy:
- Thinking should be visible and traceable
- Each step builds on previous understanding
- Uncertainty is acknowledged, not hidden
- Course correction is expected, not failure

Integration Points:
- Memory.recall() uses reasoning to decompose queries
- Memory.remember() captures reasoning traces
- Retrieval modes include reasoning metadata
- Bridge detection uses reasoning to explain connections
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("osmen.memory.sequential")


# =============================================================================
# Thought Structures
# =============================================================================


class ThoughtType(Enum):
    """Types of reasoning steps."""

    DECOMPOSITION = "decomposition"  # Breaking down the problem
    ANALYSIS = "analysis"  # Examining evidence
    HYPOTHESIS = "hypothesis"  # Proposed answer
    VERIFICATION = "verification"  # Checking hypothesis
    REVISION = "revision"  # Correcting previous thought
    BRANCH = "branch"  # Exploring alternative
    SYNTHESIS = "synthesis"  # Combining insights
    CONCLUSION = "conclusion"  # Final answer


@dataclass
class ThoughtStep:
    """
    A single step in sequential reasoning.

    Represents one unit of thought that builds on previous context.
    """

    id: str
    number: int
    thought_type: ThoughtType
    content: str
    timestamp: float

    # Context
    context: Dict[str, Any] = field(default_factory=dict)

    # Revision tracking
    is_revision: bool = False
    revises_step: Optional[int] = None

    # Branching
    branch_id: Optional[str] = None
    branch_from: Optional[int] = None

    # Confidence
    confidence: float = 0.5  # 0.0 to 1.0
    uncertainty_notes: str = ""

    # Dependencies
    builds_on: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "number": self.number,
            "type": self.thought_type.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "context": self.context,
            "is_revision": self.is_revision,
            "revises_step": self.revises_step,
            "branch_id": self.branch_id,
            "branch_from": self.branch_from,
            "confidence": self.confidence,
            "uncertainty_notes": self.uncertainty_notes,
            "builds_on": self.builds_on,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThoughtStep":
        return cls(
            id=data["id"],
            number=data["number"],
            thought_type=ThoughtType(data["type"]),
            content=data["content"],
            timestamp=data.get("timestamp", time.time()),
            context=data.get("context", {}),
            is_revision=data.get("is_revision", False),
            revises_step=data.get("revises_step"),
            branch_id=data.get("branch_id"),
            branch_from=data.get("branch_from"),
            confidence=data.get("confidence", 0.5),
            uncertainty_notes=data.get("uncertainty_notes", ""),
            builds_on=data.get("builds_on", []),
        )


@dataclass
class ReasoningChain:
    """
    A complete chain of sequential reasoning.

    Captures the full thought process from query to conclusion.
    """

    id: str
    query: str
    started_at: float
    completed_at: Optional[float] = None

    # The chain of thoughts
    steps: List[ThoughtStep] = field(default_factory=list)

    # Metadata
    total_estimate: int = 5  # Estimated total steps
    current_step: int = 0

    # Outcome
    conclusion: str = ""
    final_confidence: float = 0.0

    # Branches explored
    branches: Dict[str, List[int]] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if reasoning chain has concluded."""
        return self.completed_at is not None

    @property
    def summary(self) -> str:
        """Generate a summary of the reasoning chain."""
        if not self.steps:
            return "No reasoning steps recorded."

        lines = [f"Query: {self.query}", ""]
        for step in self.steps:
            prefix = "  " * (1 if step.branch_id else 0)
            revision = " (revision)" if step.is_revision else ""
            lines.append(
                f"{prefix}{step.number}. [{step.thought_type.value}]{revision}"
            )
            lines.append(f"{prefix}   {step.content[:100]}...")
            if step.uncertainty_notes:
                lines.append(f"{prefix}   ⚠️ {step.uncertainty_notes}")

        if self.conclusion:
            lines.append(f"\nConclusion (confidence: {self.final_confidence:.0%}):")
            lines.append(f"  {self.conclusion}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "steps": [s.to_dict() for s in self.steps],
            "total_estimate": self.total_estimate,
            "current_step": self.current_step,
            "conclusion": self.conclusion,
            "final_confidence": self.final_confidence,
            "branches": self.branches,
        }


# =============================================================================
# Sequential Reasoner
# =============================================================================


class SequentialReasoner:
    """
    Engine for deeply embedded sequential reasoning.

    Use Cases:
    1. Query decomposition before memory search
    2. Hypothesis generation during retrieval
    3. Progressive context building
    4. Insight synthesis from multiple sources

    This is NOT just a tool to call - it's integrated into memory operations.
    """

    def __init__(
        self,
        max_depth: int = 7,  # Context7 inspired
        confidence_threshold: float = 0.7,
        allow_branching: bool = True,
    ):
        """
        Args:
            max_depth: Maximum reasoning depth before forcing conclusion
            confidence_threshold: Confidence needed to conclude
            allow_branching: Whether to explore alternative paths
        """
        self.max_depth = max_depth
        self.confidence_threshold = confidence_threshold
        self.allow_branching = allow_branching

        # Active reasoning chains
        self.active_chains: Dict[str, ReasoningChain] = {}

        # Completed chains (for learning)
        self.completed_chains: List[ReasoningChain] = []

    def begin_reasoning(
        self, query: str, initial_context: Optional[Dict] = None
    ) -> ReasoningChain:
        """
        Start a new reasoning chain.

        Args:
            query: The question or task to reason about
            initial_context: Starting context/knowledge

        Returns:
            A new ReasoningChain to build upon
        """
        chain_id = self._generate_chain_id(query)

        chain = ReasoningChain(
            id=chain_id,
            query=query,
            started_at=time.time(),
            total_estimate=self._estimate_steps(query),
        )

        # Add initial decomposition step
        first_step = self._create_step(
            chain=chain,
            thought_type=ThoughtType.DECOMPOSITION,
            content=f"Analyzing query: '{query}'",
            context=initial_context or {},
        )
        chain.steps.append(first_step)

        self.active_chains[chain_id] = chain
        logger.debug(f"Started reasoning chain: {chain_id}")

        return chain

    def add_thought(
        self,
        chain: ReasoningChain,
        thought_type: ThoughtType,
        content: str,
        confidence: float = 0.5,
        context: Optional[Dict] = None,
        is_revision: bool = False,
        revises_step: Optional[int] = None,
        branch_id: Optional[str] = None,
    ) -> ThoughtStep:
        """
        Add a thought step to the chain.

        Args:
            chain: The reasoning chain to extend
            thought_type: Type of thought
            content: The actual thought content
            confidence: Confidence in this thought (0-1)
            context: Additional context for this step
            is_revision: Whether this revises a previous thought
            revises_step: Which step number is being revised
            branch_id: ID if this is on a branch

        Returns:
            The created ThoughtStep
        """
        step = ThoughtStep(
            id=f"{chain.id}_{chain.current_step + 1}",
            number=chain.current_step + 1,
            thought_type=thought_type,
            content=content,
            timestamp=time.time(),
            context=context or {},
            is_revision=is_revision,
            revises_step=revises_step,
            branch_id=branch_id,
            confidence=confidence,
            builds_on=[chain.current_step] if chain.current_step > 0 else [],
        )

        chain.steps.append(step)
        chain.current_step += 1

        # Track branches
        if branch_id:
            if branch_id not in chain.branches:
                chain.branches[branch_id] = []
            chain.branches[branch_id].append(step.number)

        logger.debug(f"Added thought {step.number}: {thought_type.value}")

        return step

    def conclude(
        self, chain: ReasoningChain, conclusion: str, confidence: float
    ) -> ReasoningChain:
        """
        Conclude a reasoning chain.

        Args:
            chain: The chain to conclude
            conclusion: Final conclusion/answer
            confidence: Confidence in the conclusion

        Returns:
            The completed chain
        """
        # Add conclusion step
        self.add_thought(
            chain=chain,
            thought_type=ThoughtType.CONCLUSION,
            content=conclusion,
            confidence=confidence,
        )

        chain.conclusion = conclusion
        chain.final_confidence = confidence
        chain.completed_at = time.time()

        # Move to completed
        if chain.id in self.active_chains:
            del self.active_chains[chain.id]
        self.completed_chains.append(chain)

        logger.info(f"Concluded chain {chain.id} with confidence {confidence:.0%}")

        return chain

    def branch(
        self, chain: ReasoningChain, branch_reason: str, from_step: Optional[int] = None
    ) -> str:
        """
        Create a branch to explore an alternative path.

        Args:
            chain: The chain to branch from
            branch_reason: Why we're branching
            from_step: Which step to branch from (default: current)

        Returns:
            The branch ID
        """
        if not self.allow_branching:
            logger.warning("Branching disabled, continuing linear")
            return ""

        branch_from = from_step or chain.current_step
        branch_id = f"branch_{len(chain.branches) + 1}"

        # Add branching thought
        self.add_thought(
            chain=chain,
            thought_type=ThoughtType.BRANCH,
            content=f"Exploring alternative: {branch_reason}",
            branch_id=branch_id,
            context={"branch_from": branch_from},
        )

        logger.debug(f"Created branch {branch_id} from step {branch_from}")

        return branch_id

    def revise(
        self, chain: ReasoningChain, revises_step: int, new_content: str, reason: str
    ) -> ThoughtStep:
        """
        Revise a previous thought step.

        Args:
            chain: The reasoning chain
            revises_step: Which step to revise
            new_content: The revised thought
            reason: Why we're revising

        Returns:
            The revision step
        """
        return self.add_thought(
            chain=chain,
            thought_type=ThoughtType.REVISION,
            content=f"{reason}. Revised: {new_content}",
            is_revision=True,
            revises_step=revises_step,
        )

    def decompose_query(
        self, query: str, context: Optional[Dict] = None
    ) -> Tuple[List[str], ReasoningChain]:
        """
        Decompose a query into sub-queries for memory search.

        This is the primary integration point with memory.recall().

        Args:
            query: The query to decompose
            context: Additional context

        Returns:
            (sub_queries, reasoning_chain)
        """
        chain = self.begin_reasoning(query, context)

        # Simple decomposition strategy
        sub_queries = []

        # 1. Direct interpretation
        self.add_thought(
            chain,
            ThoughtType.ANALYSIS,
            f"Direct interpretation: search for '{query}'",
            confidence=0.8,
        )
        sub_queries.append(query)

        # 2. Concept extraction
        concepts = self._extract_concepts(query)
        if concepts:
            self.add_thought(
                chain,
                ThoughtType.DECOMPOSITION,
                f"Key concepts identified: {', '.join(concepts)}",
                confidence=0.7,
            )
            for concept in concepts[:3]:  # Top 3 concepts
                sub_queries.append(concept)

        # 3. Related domain search
        domain = context.get("domain") if context else None
        if domain:
            self.add_thought(
                chain,
                ThoughtType.ANALYSIS,
                f"Searching within domain: {domain}",
                confidence=0.6,
            )
            sub_queries.append(f"{domain} {query}")

        # 4. Abstract/lateral expansion
        abstract = self._generate_abstract_query(query)
        if abstract:
            self.add_thought(
                chain,
                ThoughtType.BRANCH,
                f"Lateral expansion: {abstract}",
                confidence=0.5,
            )
            sub_queries.append(abstract)

        return sub_queries, chain

    def synthesize_results(
        self, chain: ReasoningChain, results: List[Dict[str, Any]], original_query: str
    ) -> Tuple[str, float]:
        """
        Synthesize multiple retrieval results into a coherent answer.

        Args:
            chain: The reasoning chain
            results: Retrieved memory results
            original_query: The original query

        Returns:
            (synthesized_answer, confidence)
        """
        if not results:
            self.add_thought(
                chain,
                ThoughtType.ANALYSIS,
                "No results found to synthesize",
                confidence=0.2,
            )
            return "", 0.2

        # Analyze each result
        relevant_content = []
        for i, result in enumerate(results):
            content = result.get("content", "")
            relevance = self._assess_relevance(content, original_query)

            self.add_thought(
                chain,
                ThoughtType.ANALYSIS,
                f"Result {i+1}: relevance {relevance:.0%} - {content[:50]}...",
                confidence=relevance,
            )

            if relevance > 0.5:
                relevant_content.append((content, relevance))

        if not relevant_content:
            self.add_thought(
                chain,
                ThoughtType.HYPOTHESIS,
                "No sufficiently relevant results found",
                confidence=0.3,
            )
            return "Insufficient information to answer", 0.3

        # Generate hypothesis
        hypothesis = self._generate_hypothesis(relevant_content, original_query)

        self.add_thought(
            chain, ThoughtType.HYPOTHESIS, f"Hypothesis: {hypothesis}", confidence=0.7
        )

        # Verify hypothesis
        verification_score = self._verify_hypothesis(hypothesis, relevant_content)

        self.add_thought(
            chain,
            ThoughtType.VERIFICATION,
            f"Verification score: {verification_score:.0%}",
            confidence=verification_score,
        )

        # Synthesize final answer
        if verification_score >= self.confidence_threshold:
            final = hypothesis
            self.add_thought(
                chain,
                ThoughtType.SYNTHESIS,
                f"Synthesis confirmed: {final}",
                confidence=verification_score,
            )
        else:
            # Uncertainty acknowledgment
            final = f"Based on available information: {hypothesis} (confidence: {verification_score:.0%})"
            self.add_thought(
                chain,
                ThoughtType.SYNTHESIS,
                final,
                confidence=verification_score,
                uncertainty_notes="Below confidence threshold, uncertainty acknowledged",
            )

        return final, verification_score

    def _create_step(
        self,
        chain: ReasoningChain,
        thought_type: ThoughtType,
        content: str,
        context: Dict,
    ) -> ThoughtStep:
        """Create a new thought step."""
        chain.current_step += 1
        return ThoughtStep(
            id=f"{chain.id}_{chain.current_step}",
            number=chain.current_step,
            thought_type=thought_type,
            content=content,
            timestamp=time.time(),
            context=context,
        )

    def _estimate_steps(self, query: str) -> int:
        """Estimate how many reasoning steps will be needed."""
        # Simple heuristic based on query complexity
        words = len(query.split())

        if words < 5:
            return 3
        elif words < 15:
            return 5
        else:
            return min(self.max_depth, 7)

    def _extract_concepts(self, query: str) -> List[str]:
        """Extract key concepts from query."""
        # Simple keyword extraction (could be enhanced with NLP)
        stopwords = {
            "what",
            "how",
            "why",
            "when",
            "where",
            "is",
            "are",
            "the",
            "a",
            "an",
            "to",
            "for",
            "of",
            "in",
        }
        words = query.lower().split()
        concepts = [w for w in words if w not in stopwords and len(w) > 2]
        return concepts

    def _generate_abstract_query(self, query: str) -> str:
        """Generate an abstract/lateral version of the query."""
        # Simple transformation (could be enhanced with LLM)
        return f"themes and patterns related to: {query}"

    def _assess_relevance(self, content: str, query: str) -> float:
        """Assess relevance of content to query."""
        # Simple word overlap (could be enhanced)
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())

        overlap = len(query_words & content_words)
        if not query_words:
            return 0.0

        return min(1.0, overlap / len(query_words))

    def _generate_hypothesis(
        self, relevant_content: List[Tuple[str, float]], query: str
    ) -> str:
        """Generate a hypothesis from relevant content."""
        # Simple: use most relevant content as basis
        if not relevant_content:
            return "Insufficient data for hypothesis"

        best_content, _ = max(relevant_content, key=lambda x: x[1])
        return best_content[:200]  # Truncate for hypothesis

    def _verify_hypothesis(
        self, hypothesis: str, relevant_content: List[Tuple[str, float]]
    ) -> float:
        """Verify hypothesis against evidence."""
        # Simple: average relevance of supporting content
        if not relevant_content:
            return 0.0

        return sum(r for _, r in relevant_content) / len(relevant_content)

    def _generate_chain_id(self, query: str) -> str:
        """Generate unique chain ID."""
        data = f"{query}{time.time()}"
        return f"chain_{hashlib.md5(data.encode()).hexdigest()[:12]}"

    def get_active_chains(self) -> List[ReasoningChain]:
        """Get all active reasoning chains."""
        return list(self.active_chains.values())

    def get_chain_summary(self, chain_id: str) -> Optional[str]:
        """Get summary of a specific chain."""
        chain = self.active_chains.get(chain_id)
        if not chain:
            # Check completed
            for c in self.completed_chains:
                if c.id == chain_id:
                    return c.summary
            return None
        return chain.summary


# =============================================================================
# Convenience Functions for Memory Integration
# =============================================================================

_default_reasoner: Optional[SequentialReasoner] = None


def get_reasoner() -> SequentialReasoner:
    """Get or create the default reasoner."""
    global _default_reasoner
    if _default_reasoner is None:
        _default_reasoner = SequentialReasoner()
    return _default_reasoner


def decompose_for_search(query: str, context: Optional[Dict] = None) -> List[str]:
    """
    Decompose a query into sub-queries for memory search.

    This is the main entry point for integrating reasoning into recall().
    """
    sub_queries, chain = get_reasoner().decompose_query(query, context)
    return sub_queries


def reason_about_results(
    results: List[Dict], query: str
) -> Tuple[str, float, List[Dict]]:
    """
    Apply sequential reasoning to search results.

    Returns:
        (answer, confidence, reasoning_trace)
    """
    reasoner = get_reasoner()
    chain = reasoner.begin_reasoning(query)

    answer, confidence = reasoner.synthesize_results(chain, results, query)
    reasoner.conclude(chain, answer, confidence)

    trace = [step.to_dict() for step in chain.steps]
    return answer, confidence, trace


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.DEBUG)

    reasoner = SequentialReasoner()

    # Start reasoning about a query
    chain = reasoner.begin_reasoning(
        "How do memory systems support lateral thinking?",
        {"domain": "cognitive_architecture"},
    )

    # Add analysis steps
    reasoner.add_thought(
        chain,
        ThoughtType.ANALYSIS,
        "Memory systems can store connections between disparate concepts",
        confidence=0.8,
    )

    reasoner.add_thought(
        chain,
        ThoughtType.HYPOTHESIS,
        "Lateral thinking emerges from unexpected memory bridges",
        confidence=0.7,
    )

    # Verify
    reasoner.add_thought(
        chain,
        ThoughtType.VERIFICATION,
        "The synchronicity detection system supports this hypothesis",
        confidence=0.85,
    )

    # Conclude
    reasoner.conclude(
        chain,
        "Memory bridges between different domains enable lateral thinking by revealing unexpected connections",
        confidence=0.85,
    )

    print("\n📝 Reasoning Summary:")
    print(chain.summary)
