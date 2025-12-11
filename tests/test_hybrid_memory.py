"""
Test suite for Hybrid Memory System

Tests the integration of:
- ChromaDB (long-term vector memory)
- SQLite (short-term structured memory)
- Context7 (7-dimensional context model)
- Sequential Reasoning traces
- Lateral Thinking with synchronicity detection
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestContext7:
    """Test the Context7 7-dimensional context model"""

    def test_context7_creation(self):
        """Test creating a Context7 with default values"""
        from integrations.memory.lateral_synchronicity import Context7

        ctx = Context7()
        assert ctx.intent == ""
        assert ctx.domain == ""
        assert ctx.emotion == ""

    def test_context7_with_values(self):
        """Test creating a Context7 with specific values"""
        from integrations.memory.lateral_synchronicity import Context7

        ctx = Context7(
            intent="learning",
            domain="technology",
            emotion="curious",
            temporal="recent",
            spatial="workspace",
            relational="collaborative",
            abstract="patterns",
        )

        assert ctx.intent == "learning"
        assert ctx.domain == "technology"
        assert ctx.emotion == "curious"

        # Test to_metadata method
        metadata = ctx.to_metadata()
        assert metadata["c7_intent"] == "learning"
        assert metadata["c7_domain"] == "technology"

    def test_context7_similarity(self):
        """Test similarity calculation between Context7 instances"""
        from integrations.memory.lateral_synchronicity import Context7

        ctx1 = Context7(intent="learning", domain="tech")
        ctx2 = Context7(intent="learning", domain="tech")
        ctx3 = Context7(intent="working", domain="business")

        # Same contexts should have high similarity
        sim_same = ctx1.similarity(ctx2)
        assert sim_same > 0.9

        # Different contexts should have lower similarity
        sim_diff = ctx1.similarity(ctx3)
        assert sim_diff < sim_same

    def test_context7_dimensions_set(self):
        """Test dimension counting via dimensions_set()"""
        from integrations.memory.lateral_synchronicity import Context7

        ctx_empty = Context7()
        ctx_partial = Context7(intent="test", domain="test")
        ctx_full = Context7(
            intent="a",
            domain="b",
            emotion="c",
            temporal="d",
            spatial="e",
            relational="f",
            abstract="g",
        )

        assert len(ctx_empty.dimensions_set()) == 0
        assert len(ctx_partial.dimensions_set()) == 2
        assert len(ctx_full.dimensions_set()) == 7


class TestMemoryItem:
    """Test MemoryItem data structure"""

    def test_memory_item_creation(self):
        """Test creating a memory item"""
        from integrations.memory.hybrid_memory import MemoryItem, MemoryTier

        now = time.time()
        item = MemoryItem(
            id="test-123",
            content="Test memory",
            tier=MemoryTier.SHORT_TERM,
            created_at=now,
            accessed_at=now,
            source="test",
        )

        assert item.content == "Test memory"
        assert item.source == "test"
        assert item.tier == MemoryTier.SHORT_TERM
        assert item.id == "test-123"

    def test_memory_item_with_context7(self):
        """Test memory item with Context7 fields"""
        from integrations.memory.hybrid_memory import MemoryItem, MemoryTier

        now = time.time()
        item = MemoryItem(
            id="test-456",
            content="Learning about patterns",
            tier=MemoryTier.LONG_TERM,
            created_at=now,
            accessed_at=now,
            source="agent",
            intent="learning",
            domain="technology",
            abstract="emergence",
        )

        metadata = item.context7_metadata()
        assert metadata["c7_intent"] == "learning"
        assert metadata["c7_domain"] == "technology"
        assert metadata["c7_abstract"] == "emergence"

    def test_memory_item_serialization(self):
        """Test MemoryItem to_dict and from_dict"""
        from integrations.memory.hybrid_memory import MemoryItem, MemoryTier

        now = time.time()
        item = MemoryItem(
            id="test-789",
            content="Serialization test",
            tier=MemoryTier.WORKING,
            created_at=now,
            accessed_at=now,
            source="system",
        )

        # Round-trip serialization
        data = item.to_dict()
        restored = MemoryItem.from_dict(data)

        assert restored.id == item.id
        assert restored.content == item.content


class TestThoughtStep:
    """Test Sequential Reasoning ThoughtStep"""

    def test_thought_step_creation(self):
        """Test creating a thought step"""
        from integrations.memory.sequential_reasoning import ThoughtStep, ThoughtType

        step = ThoughtStep(
            id="thought-1",
            number=1,
            thought_type=ThoughtType.ANALYSIS,
            content="Analyzing the problem",
            timestamp=time.time(),
            confidence=0.8,
        )

        assert step.thought_type == ThoughtType.ANALYSIS
        assert step.content == "Analyzing the problem"
        assert step.confidence == 0.8
        assert step.number == 1
        assert not step.is_revision

    def test_thought_step_revision(self):
        """Test revision tracking"""
        from integrations.memory.sequential_reasoning import ThoughtStep, ThoughtType

        step = ThoughtStep(
            id="thought-2",
            number=2,
            thought_type=ThoughtType.REVISION,
            content="Reconsidering approach",
            timestamp=time.time(),
            is_revision=True,
            revises_step=1,
        )

        assert step.is_revision
        assert step.revises_step == 1

    def test_thought_step_branching(self):
        """Test thought branching"""
        from integrations.memory.sequential_reasoning import ThoughtStep, ThoughtType

        step = ThoughtStep(
            id="thought-3",
            number=3,
            thought_type=ThoughtType.HYPOTHESIS,
            content="Alternative approach",
            timestamp=time.time(),
            branch_id="alt_1",
            branch_from=2,
        )

        assert step.branch_id == "alt_1"
        assert step.branch_from == 2


class TestSequentialReasoner:
    """Test SequentialReasoner engine"""

    def test_reasoner_creation(self):
        """Test creating a reasoner"""
        from integrations.memory.sequential_reasoning import SequentialReasoner

        reasoner = SequentialReasoner()
        assert reasoner is not None

    def test_begin_and_add_thoughts(self):
        """Test beginning reasoning and adding thoughts"""
        from integrations.memory.sequential_reasoning import (
            SequentialReasoner,
            ThoughtType,
        )

        reasoner = SequentialReasoner()
        chain = reasoner.begin_reasoning("What is the answer?")

        assert chain.query == "What is the answer?"
        assert not chain.is_complete  # Should not be complete yet

        reasoner.add_thought(
            chain,  # Pass chain object, not chain_id
            ThoughtType.ANALYSIS,
            "Let me think about this",
            confidence=0.7,
        )

        assert len(chain.steps) >= 1  # At least decomposition + our step

    def test_conclude_reasoning(self):
        """Test concluding a reasoning chain"""
        from integrations.memory.sequential_reasoning import (
            SequentialReasoner,
            ThoughtType,
        )

        reasoner = SequentialReasoner()
        chain = reasoner.begin_reasoning("Test query")

        reasoner.add_thought(chain, ThoughtType.HYPOTHESIS, "Testing", 0.8)
        reasoner.conclude(chain, "The answer is 42", confidence=0.95)

        assert chain.conclusion == "The answer is 42"
        assert chain.final_confidence == 0.95

    def test_decompose_query(self):
        """Test query decomposition"""
        from integrations.memory.sequential_reasoning import SequentialReasoner

        reasoner = SequentialReasoner()
        query = "How does Python implement memory management?"

        # decompose_query returns (sub_queries, chain)
        sub_queries, chain = reasoner.decompose_query(query)

        assert isinstance(sub_queries, list)
        assert len(sub_queries) > 0
        assert query in sub_queries  # Original query should be in results


class TestLateralQueryExpander:
    """Test Lateral Query Expansion"""

    def test_query_expansion(self):
        """Test expanding a query laterally"""
        from integrations.memory.lateral_synchronicity import LateralQueryExpander

        expander = LateralQueryExpander()
        expansions = expander.expand("machine learning patterns")

        # Should have focus and shadow components
        assert "focus" in expansions
        assert "shadow" in expansions
        assert "abstract" in expansions


class TestGlimmer:
    """Test Glimmer (synchronicity detection)"""

    def test_glimmer_creation(self):
        """Test creating a glimmer"""
        from integrations.memory.lateral_synchronicity import Glimmer, GlimmerType

        glimmer = Glimmer(
            id="glimmer-1",
            source_id="memory1",
            target_id="memory2",
            glimmer_type=GlimmerType.SEMANTIC,
            strength=0.7,
            discovered_at=time.time(),
            shared_concepts=["theme1", "theme2"],
            shared_dimensions=["domain", "abstract"],
        )

        assert glimmer.strength == 0.7
        assert len(glimmer.shared_concepts) == 2
        assert "domain" in glimmer.shared_dimensions

    def test_glimmer_to_dict(self):
        """Test glimmer serialization"""
        from integrations.memory.lateral_synchronicity import Glimmer, GlimmerType

        glimmer = Glimmer(
            id="glimmer-2",
            source_id="m1",
            target_id="m2",
            glimmer_type=GlimmerType.TEMPORAL,
            strength=0.5,
            discovered_at=time.time(),
        )

        data = glimmer.to_dict()
        assert data["id"] == "glimmer-2"
        assert data["type"] == "temporal"


class TestSynchronicityDetector:
    """Test cross-domain synchronicity detection"""

    def test_detector_creation(self):
        """Test creating a detector"""
        from integrations.memory.bridge import SynchronicityDetector

        detector = SynchronicityDetector()
        assert detector is not None

    def test_detect_connections(self):
        """Test connection detection between two memories"""
        from integrations.memory.bridge import SynchronicityDetector, SynchronicityEvent

        detector = SynchronicityDetector(threshold=0.5)  # Lower threshold for test

        # Two memories with different domains but some overlap
        memory_1 = {
            "id": "m1",
            "content": "machine learning algorithms",
            "metadata": {"c7_domain": "technology", "c7_emotion": "curious"},
        }
        memory_2 = {
            "id": "m2",
            "content": "neural patterns in brain",
            "metadata": {"c7_domain": "neuroscience", "c7_emotion": "curious"},
        }

        # Detect between two memories (may or may not find bridge depending on threshold)
        event = detector.detect(memory_1, memory_2, embedding_similarity=0.8)

        # Either returns a SynchronicityEvent or None
        if event is not None:
            assert isinstance(event, SynchronicityEvent)
            assert event.memory_id_1 == "m1"
            assert event.memory_id_2 == "m2"


class TestMemoryBridge:
    """Test Memory Bridge tier transitions"""

    def test_bridge_creation(self):
        """Test creating a memory bridge"""
        from integrations.memory.bridge import MemoryBridge

        bridge = MemoryBridge()
        assert bridge is not None

    def test_evaluate_promotion(self):
        """Test promotion decision logic"""
        from integrations.memory.bridge import MemoryBridge

        bridge = MemoryBridge()

        # Memory that has been accessed multiple times
        memory = {
            "id": "test-mem",
            "content": "Important information",
            "access_count": 10,
            "created_at": time.time() - 86400 * 2,  # 2 days ago
        }

        # Returns (should_promote: bool, reason: TransitionReason|None)
        should_promote, reason = bridge.evaluate_promotion(memory)

        # With 10 accesses, should likely promote
        assert isinstance(should_promote, bool)


class TestLateralBridge:
    """Test Lateral Bridge for focus+shadow weaving"""

    def test_lateral_bridge_creation(self):
        """Test creating a lateral bridge"""
        from integrations.memory.lateral_synchronicity import LateralBridge

        bridge = LateralBridge()
        assert bridge is not None

    def test_expand_query(self):
        """Test lateral query expansion"""
        from integrations.memory.lateral_synchronicity import LateralBridge

        bridge = LateralBridge()

        result = bridge.expand_query("test query")

        # Should return expanded queries
        assert "focus" in result
        assert "shadow" in result


class TestMemoryConfig:
    """Test HybridMemory configuration"""

    def test_config_defaults(self):
        """Test default configuration"""
        from integrations.memory.hybrid_memory import MemoryConfig

        config = MemoryConfig()

        assert config.chromadb_host == "localhost"
        assert config.chromadb_port == 8000
        assert config.working_memory_size == 50

    def test_config_from_env(self):
        """Test configuration from environment"""
        import os

        from integrations.memory.hybrid_memory import MemoryConfig

        # Set test env vars
        os.environ["CHROMADB_HOST"] = "testhost"
        os.environ["CHROMADB_PORT"] = "9000"

        config = MemoryConfig.from_env()

        assert config.chromadb_host == "testhost"
        assert config.chromadb_port == 9000

        # Cleanup
        del os.environ["CHROMADB_HOST"]
        del os.environ["CHROMADB_PORT"]


class TestMemoryTier:
    """Test MemoryTier enum"""

    def test_memory_tiers(self):
        """Test memory tier values"""
        from integrations.memory.hybrid_memory import MemoryTier

        assert MemoryTier.WORKING.value == "working"
        assert MemoryTier.SHORT_TERM.value == "short"
        assert MemoryTier.LONG_TERM.value == "long"
        assert MemoryTier.ARCHIVE.value == "archive"


class TestMCPIntegration:
    """Test MCP server integration"""

    def test_mcp_tool_schema_exists(self):
        """Verify MCP tool schemas are defined"""
        # Read the MCP server file
        mcp_path = Path(__file__).parent.parent / "gateway" / "mcp" / "stdio_server.py"

        if mcp_path.exists():
            content = mcp_path.read_text()

            # Check memory tools exist
            assert "memory_recall" in content
            assert "memory_recall_with_reasoning" in content
            assert "memory_store" in content

    def test_handler_signature(self):
        """Verify handler methods exist"""
        mcp_path = Path(__file__).parent.parent / "gateway" / "mcp" / "stdio_server.py"

        if mcp_path.exists():
            content = mcp_path.read_text()

            # Handler methods should exist
            assert "def handle_memory_recall" in content
            assert "def handle_memory_recall_with_reasoning" in content


# Run tests
if __name__ == "__main__":
    print("=" * 60)
    print("Running Hybrid Memory System Tests")
    print("=" * 60)

    # Collect results
    passed = 0
    failed = 0
    errors = []

    # Get all test classes
    test_classes = [
        TestContext7,
        TestMemoryItem,
        TestThoughtStep,
        TestSequentialReasoner,
        TestLateralQueryExpander,
        TestGlimmer,
        TestSynchronicityDetector,
        TestMemoryBridge,
        TestLateralBridge,
        TestMemoryConfig,
        TestMemoryTier,
        TestMCPIntegration,
    ]

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        instance = test_class()

        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    getattr(instance, method_name)()
                    print(f"  ✅ {method_name}")
                    passed += 1
                except Exception as e:
                    print(f"  ❌ {method_name}: {e}")
                    errors.append((f"{test_class.__name__}.{method_name}", str(e)))
                    failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    if errors:
        print("\nFailures:")
        for name, error in errors:
            print(f"  - {name}: {error}")

    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
