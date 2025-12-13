#!/usr/bin/env python3
"""
DeepAgents Integration for OsMEN v3.0

Integrates LangChain's deepagents framework into OsMEN, providing:
- Long-horizon task planning and execution
- Sub-agent delegation
- Computer access (shell/filesystem)
- Extensible tool library
- Integration with existing OsMEN agents

Based on: https://github.com/langchain-ai/deepagents
"""

import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from deepagents import create_deep_agent
    from langchain.chat_models import init_chat_model

    DEEPAGENTS_AVAILABLE = True
except ImportError:
    DEEPAGENTS_AVAILABLE = False
    logger.warning("deepagents not installed. Install with: pip install deepagents")


class DeepAgentsIntegration:
    """
    Integration layer for LangChain DeepAgents in OsMEN.

    Provides:
    - Long-horizon task planning and execution
    - Sub-agent delegation for isolated task execution
    - Computer access (shell and filesystem tools)
    - Custom tool integration with OsMEN services
    - Template-based agent creation
    """

    def __init__(self, config_dir: str = None):
        """
        Initialize DeepAgents integration.

        Args:
            config_dir: Directory for agent configurations and state
        """
        if not DEEPAGENTS_AVAILABLE:
            raise ImportError("deepagents package not installed")

        self.config_dir = config_dir or os.path.join(
            os.path.dirname(__file__), "../.copilot/deepagents"
        )
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)

        # Default model (can be customized)
        self.default_model = "anthropic/claude-sonnet-4.5"

        # Agent registry
        self.agents = {}

        # Tool registry
        self.custom_tools = []

        logger.info("DeepAgents integration initialized")

    def create_agent(
        self,
        name: str,
        system_prompt: str,
        tools: List[Callable] = None,
        model: str = None,
        **kwargs,
    ) -> Any:
        """
        Create a deep agent with custom configuration.

        Args:
            name: Agent identifier
            system_prompt: Custom instructions for the agent
            tools: List of custom tool functions
            model: Model to use (default: claude-sonnet-4.5)
            **kwargs: Additional parameters for create_deep_agent

        Returns:
            Configured deep agent (LangGraph StateGraph)
        """
        # Initialize model
        model_name = model or self.default_model
        chat_model = init_chat_model(model_name)

        # Combine custom tools with built-in OsMEN tools
        all_tools = (tools or []) + self.custom_tools

        # Create agent
        agent = create_deep_agent(
            model=chat_model, system_prompt=system_prompt, tools=all_tools, **kwargs
        )

        # Register agent
        self.agents[name] = {
            "agent": agent,
            "model": model_name,
            "system_prompt": system_prompt,
            "tools": [t.__name__ for t in all_tools] if all_tools else [],
        }

        logger.info(f"Created deep agent: {name} with {len(all_tools)} tools")
        return agent

    def register_tool(self, tool_func: Callable):
        """
        Register a custom tool for use across all agents.

        Args:
            tool_func: Function with docstring describing the tool
        """
        self.custom_tools.append(tool_func)
        logger.info(f"Registered tool: {tool_func.__name__}")

    def get_agent(self, name: str) -> Optional[Any]:
        """Get a registered agent by name"""
        return self.agents.get(name, {}).get("agent")

    def list_agents(self) -> List[str]:
        """List all registered agents"""
        return list(self.agents.keys())

    def invoke_agent(self, name: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        Invoke a registered agent with a message.

        Args:
            name: Agent identifier
            message: User message/task
            **kwargs: Additional invocation parameters

        Returns:
            Agent response
        """
        agent = self.get_agent(name)
        if not agent:
            raise ValueError(f"Agent '{name}' not found")

        result = agent.invoke(
            {"messages": [{"role": "user", "content": message}]}, **kwargs
        )

        logger.info(f"Agent '{name}' completed task")
        return result


class AgentTemplateLibrary:
    """
    Library of pre-configured agent templates for common workflows.

    Templates include:
    - Research agents
    - Code generation agents
    - Data analysis agents
    - System automation agents
    - Calendar/scheduling agents
    - Knowledge management agents
    """

    @staticmethod
    def create_research_agent(integration: DeepAgentsIntegration) -> Any:
        """
        Create a research agent specialized in deep research tasks.

        Capabilities:
        - Web search and information gathering
        - Source evaluation and synthesis
        - Report generation
        - Citation management
        """
        system_prompt = """You are a research specialist. Your role is to:

1. PLANNING: Break down research questions into sub-tasks
2. GATHERING: Search for information from multiple sources
3. EVALUATION: Assess source credibility and relevance
4. SYNTHESIS: Combine information into coherent insights
5. REPORTING: Create polished, well-cited reports

Best Practices:
- Batch similar searches together for efficiency
- Cross-reference facts across multiple sources
- Track sources for proper citation
- Organize findings hierarchically
- Identify knowledge gaps early

Output Format:
- Executive summary
- Detailed findings with citations
- Recommendations or conclusions
- Areas requiring further investigation
"""

        # Register web search tool if available
        try:
            from tavily import TavilyClient

            tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

            def internet_search(query: str, max_results: int = 5) -> str:
                """Search the web for information"""
                return tavily.search(query, max_results=max_results)

            tools = [internet_search]
        except ImportError:
            logger.warning(
                "Tavily not installed - research agent will have limited search"
            )
            tools = []

        return integration.create_agent(
            name="research_specialist", system_prompt=system_prompt, tools=tools
        )

    @staticmethod
    def create_code_generation_agent(integration: DeepAgentsIntegration) -> Any:
        """
        Create a code generation agent for software development tasks.

        Capabilities:
        - Code generation with best practices
        - Testing and validation
        - Documentation generation
        - Refactoring suggestions
        """
        system_prompt = """You are a senior software engineer. Your role is to:

1. ANALYSIS: Understand requirements and constraints
2. DESIGN: Plan code structure and architecture
3. IMPLEMENTATION: Write clean, tested code
4. VALIDATION: Test edge cases and error handling
5. DOCUMENTATION: Add clear comments and docs

Code Quality Standards:
- Follow language-specific best practices
- Write comprehensive tests (unit, integration)
- Handle errors gracefully
- Use meaningful variable/function names
- Add docstrings for all public APIs
- Consider performance and security

Development Workflow:
- Start with high-level design
- Implement incrementally
- Test each component
- Refactor for clarity
- Document thoroughly
"""

        return integration.create_agent(
            name="code_generator", system_prompt=system_prompt
        )

    @staticmethod
    def create_data_analysis_agent(integration: DeepAgentsIntegration) -> Any:
        """
        Create a data analysis agent for analytics tasks.

        Capabilities:
        - Data exploration and profiling
        - Statistical analysis
        - Visualization recommendations
        - Insight generation
        """
        system_prompt = """You are a data analyst. Your role is to:

1. EXPLORATION: Profile data and identify patterns
2. CLEANING: Handle missing values and outliers
3. ANALYSIS: Apply statistical methods
4. VISUALIZATION: Create informative charts
5. INSIGHTS: Extract actionable findings

Analysis Workflow:
- Start with descriptive statistics
- Check data quality and completeness
- Identify correlations and trends
- Test hypotheses rigorously
- Visualize results effectively

Best Practices:
- Document assumptions clearly
- Validate findings with multiple methods
- Consider alternative explanations
- Communicate uncertainty appropriately
- Provide actionable recommendations
"""

        return integration.create_agent(
            name="data_analyst", system_prompt=system_prompt
        )

    @staticmethod
    def create_calendar_agent(integration: DeepAgentsIntegration) -> Any:
        """
        Create a calendar management agent.

        Capabilities:
        - Event scheduling and conflict resolution
        - Meeting optimization
        - Calendar analysis
        - Automated reminders
        """
        system_prompt = """You are a calendar management specialist. Your role is to:

1. SCHEDULING: Find optimal meeting times
2. CONFLICTS: Detect and resolve scheduling conflicts
3. OPTIMIZATION: Minimize meeting overhead
4. REMINDERS: Set up appropriate notifications
5. ANALYSIS: Identify scheduling patterns

Scheduling Principles:
- Respect working hours and time zones
- Batch similar meetings together
- Leave buffer time between meetings
- Prioritize focus time blocks
- Consider participant availability

Best Practices:
- Check all calendars before scheduling
- Suggest alternative times for conflicts
- Add detailed event descriptions
- Set reminders based on importance
- Minimize meeting duration when possible
"""

        return integration.create_agent(
            name="calendar_manager", system_prompt=system_prompt
        )


class RetrievalStrategyLibrary:
    """
    Library of retrieval strategies for RAG (Retrieval-Augmented Generation).

    Implements efficient retrieval patterns including:
    - Semantic search with embeddings
    - Hybrid search (semantic + keyword)
    - Hierarchical retrieval
    - Quantum-inspired retrieval (ambiguity-aware)

    These methods integrate with OsMEN's HybridMemory and EnhancedRAGPipeline.
    """

    _rag_pipeline = None
    _memory = None

    @classmethod
    def _get_rag_pipeline(cls):
        """Lazy-load RAG pipeline"""
        if cls._rag_pipeline is None:
            try:
                from integrations.rag_pipeline import EnhancedRAGPipeline, RAGConfig

                cls._rag_pipeline = EnhancedRAGPipeline(RAGConfig())
                logger.info("RAG pipeline loaded for DeepAgents retrieval")
            except Exception as e:
                logger.warning(f"Could not load RAG pipeline: {e}")
        return cls._rag_pipeline

    @classmethod
    def _get_memory(cls):
        """Lazy-load HybridMemory"""
        if cls._memory is None:
            try:
                from integrations.memory import HybridMemory, MemoryConfig

                cls._memory = HybridMemory(MemoryConfig.from_env())
                logger.info("HybridMemory loaded for DeepAgents retrieval")
            except Exception as e:
                logger.warning(f"Could not load HybridMemory: {e}")
        return cls._memory

    @staticmethod
    def semantic_retrieval(
        query: str,
        documents: List[str] = None,
        top_k: int = 5,
        embedding_model: str = "text-embedding-3-small",
    ) -> List[Dict[str, Any]]:
        """
        Semantic retrieval using embeddings via HybridMemory.

        Args:
            query: Search query
            documents: Optional document corpus (if None, searches memory)
            top_k: Number of results to return
            embedding_model: Model for embeddings (used if documents provided)

        Returns:
            Top-k most relevant documents with scores
        """
        logger.info(f"Semantic retrieval for: {query[:50]}...")

        memory = RetrievalStrategyLibrary._get_memory()
        if memory is None:
            logger.warning("HybridMemory not available for semantic retrieval")
            return []

        try:
            # Use HybridMemory's recall with foundation mode (semantic search)
            results = memory.recall(
                query=query, n_results=top_k, mode="foundation"  # Pure semantic search
            )

            # Convert to standard format
            return [
                {
                    "content": item.content,
                    "score": 1.0 - (i * 0.1),  # Approximate score from rank
                    "source": item.source,
                    "metadata": item.context,
                    "id": item.id,
                }
                for i, item in enumerate(results)
            ]
        except Exception as e:
            logger.error(f"Semantic retrieval failed: {e}")
            return []

    @staticmethod
    def hybrid_retrieval(
        query: str,
        documents: List[str] = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining semantic and keyword search.

        Uses EnhancedRAGPipeline's BM25 + semantic hybrid search.

        Args:
            query: Search query
            documents: Optional document corpus (if None, searches memory)
            semantic_weight: Weight for semantic similarity
            keyword_weight: Weight for keyword matching
            top_k: Number of results

        Returns:
            Top-k results with combined scoring
        """
        logger.info(f"Hybrid retrieval for: {query[:50]}...")

        rag = RetrievalStrategyLibrary._get_rag_pipeline()
        memory = RetrievalStrategyLibrary._get_memory()

        results = []

        # Try RAG pipeline first (has true hybrid BM25 + semantic)
        if rag is not None:
            try:
                rag_results = rag.query(
                    query=query, n_results=top_k, use_reranking=True
                )
                for r in rag_results:
                    results.append(
                        {
                            "content": r.content,
                            "score": r.combined_score,
                            "source": r.source,
                            "metadata": r.metadata,
                            "retrieval_method": "rag_hybrid",
                        }
                    )
            except Exception as e:
                logger.warning(f"RAG hybrid search failed: {e}")

        # Also search memory for personal context
        if memory is not None and len(results) < top_k:
            try:
                memory_results = memory.recall(
                    query=query, n_results=top_k - len(results), mode="foundation"
                )
                for item in memory_results:
                    results.append(
                        {
                            "content": item.content,
                            "score": 0.8,  # Memory results are contextually relevant
                            "source": item.source,
                            "metadata": item.context,
                            "retrieval_method": "memory_semantic",
                        }
                    )
            except Exception as e:
                logger.warning(f"Memory search failed: {e}")

        # Sort by score and return top_k
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:top_k]

    @staticmethod
    def quantum_inspired_retrieval(
        query: str,
        documents: List[str] = None,
        ambiguity_threshold: float = 0.3,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Quantum-inspired retrieval that embraces ambiguity.

        Uses LateralBridge to explore multiple interpretations
        and Context7 dimensions for multi-faceted relevance.

        Principles:
        - Ambiguity as feature, not bug
        - Multiple interpretation paths
        - Probabilistic relevance scoring
        - Context-dependent collapse

        Args:
            query: Search query (may be ambiguous)
            documents: Document corpus (optional)
            ambiguity_threshold: Threshold for ambiguity detection
            top_k: Number of results

        Returns:
            Results with interpretation probabilities
        """
        logger.info(f"Quantum-inspired retrieval for: {query[:50]}...")

        memory = RetrievalStrategyLibrary._get_memory()
        if memory is None:
            logger.warning("HybridMemory not available for quantum retrieval")
            return []

        try:
            # Use lateral mode which explores multiple interpretation paths
            results = memory.recall(
                query=query,
                n_results=top_k * 2,  # Get more for filtering
                mode="lateral",  # Enables cross-domain discovery
            )

            # Detect ambiguity by checking result diversity
            if len(results) >= 2:
                # Simple ambiguity detection: high variance in domains
                domains = [r.domain for r in results if r.domain]
                unique_domains = len(set(domains))
                ambiguity_score = unique_domains / max(len(domains), 1)
            else:
                ambiguity_score = 0.0

            # Build results with interpretation probabilities
            output = []
            for i, item in enumerate(results[:top_k]):
                # Calculate interpretation probability based on rank and ambiguity
                base_prob = 1.0 / (i + 1)  # Rank-based
                adjusted_prob = base_prob * (1.0 + ambiguity_score * 0.5)

                output.append(
                    {
                        "content": item.content,
                        "score": adjusted_prob,
                        "interpretation_probability": min(adjusted_prob, 1.0),
                        "source": item.source,
                        "domain": item.domain,
                        "abstract": item.abstract,
                        "metadata": item.context,
                        "ambiguity_score": ambiguity_score,
                        "retrieval_method": "quantum_lateral",
                    }
                )

            return output

        except Exception as e:
            logger.error(f"Quantum-inspired retrieval failed: {e}")
            return []


# Convenience function
def get_deepagents_integration(config_dir: str = None) -> DeepAgentsIntegration:
    """Get or create DeepAgents integration instance"""
    return DeepAgentsIntegration(config_dir)


if __name__ == "__main__":
    print("DeepAgents Integration for OsMEN v3.0")
    print("=" * 70)

    if not DEEPAGENTS_AVAILABLE:
        print("\n❌ deepagents not installed")
        print("Install with: pip install deepagents langchain-anthropic")
        print()
        sys.exit(1)

    print("\n✅ DeepAgents available")
    print("\nFeatures:")
    print("  - Long-horizon task planning")
    print("  - Sub-agent delegation")
    print("  - Computer access (shell/filesystem)")
    print("  - Extensible tool library")
    print("  - Template-based agent creation")
    print()
    print("Usage:")
    print(
        "  from integrations.deepagents_integration import get_deepagents_integration"
    )
    print("  integration = get_deepagents_integration()")
    print("  agent = integration.create_agent('my_agent', 'Custom prompt')")
    print()
