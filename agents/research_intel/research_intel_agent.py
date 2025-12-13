#!/usr/bin/env python3
"""
Research Intelligence Agent - Real Implementation
Provides research, information gathering, and intelligence analysis.

This agent integrates with:
- Librarian RAG for semantic search and lateral thinking
- LLM providers for analysis and synthesis
- Document processing for file analysis

Usage:
    from agents.research_intel.research_intel_agent import ResearchIntelAgent

    agent = ResearchIntelAgent()

    # Research with RAG
    research = await agent.research_topic_async("therapeutic alliance", depth="deep")

    # Document analysis
    analysis = agent.analyze_document("/path/to/document.md")

    # Knowledge graph
    graph = agent.create_knowledge_graph("psychology")
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import research memory type for hints
try:
    from agents.research_intel.research_memory import ResearchMemoryIntegration
except ImportError:
    ResearchMemoryIntegration = None  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TRUNCATE_LENGTH = 100  # Length for content truncation in key points
MAX_DOCUMENTS = 5  # Maximum documents to process for key points

# Try to import research memory for persistence
RESEARCH_MEMORY_AVAILABLE = False
try:
    from .research_memory import ResearchMemoryIntegration, get_research_memory

    RESEARCH_MEMORY_AVAILABLE = True
    logger.info("Research memory integration available")
except ImportError as e:
    logger.warning(f"Research memory not available: {e}")

# Try to import librarian for RAG
LIBRARIAN_AVAILABLE = False
try:
    from agents.librarian.librarian_agent import LibrarianAgent, LibrarianConfig

    LIBRARIAN_AVAILABLE = True
    logger.info("Librarian RAG integration available")
except ImportError as e:
    logger.warning(f"Librarian not available: {e}")

# Try to import LLM providers
LLM_AVAILABLE = False
try:
    from integrations.llm_providers import LLMConfig, get_llm_provider

    LLM_AVAILABLE = True
    logger.info("LLM providers available")
except ImportError as e:
    logger.warning(f"LLM providers not available: {e}")


class ResearchIntelAgent:
    """
    Agent for research and intelligence gathering.

    Real implementation that:
    - Uses Librarian RAG for semantic search
    - Integrates with LLM for analysis
    - Processes actual documents
    - Builds knowledge graphs

    Attributes:
        librarian: LibrarianAgent for RAG functionality
        llm_provider: LLM provider for synthesis
        use_rag: Whether RAG is available
        use_llm: Whether LLM is available
    """

    def __init__(self, llm_provider: str = "ollama"):
        """
        Initialize the Research Intelligence Agent.

        Args:
            llm_provider: LLM to use (ollama, openai, anthropic)
        """
        self.sources = []
        self.findings = []
        self.llm_provider_name = llm_provider

        # Initialize research memory for persistence
        self.research_memory: Optional[ResearchMemoryIntegration] = None
        if RESEARCH_MEMORY_AVAILABLE:
            try:
                self.research_memory = get_research_memory()
                logger.info("Research memory integration enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize research memory: {e}")

        # Initialize Librarian for RAG
        self.librarian = None
        self.use_rag = False
        if LIBRARIAN_AVAILABLE:
            try:
                self.librarian = LibrarianAgent()
                self.librarian.initialize()
                self.use_rag = True
                logger.info("Research Intel Agent: Librarian RAG initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Librarian: {e}")

        # LLM will be initialized on first use (async)
        self.llm = None
        self.use_llm = LLM_AVAILABLE

        logger.info(
            f"ResearchIntelAgent initialized (RAG={self.use_rag}, LLM={self.use_llm}, Memory={bool(self.research_memory)})"
        )

    async def _get_llm(self):
        """Get LLM provider (lazy initialization)."""
        if self.llm is None and LLM_AVAILABLE:
            try:
                self.llm = await get_llm_provider(self.llm_provider_name)
            except Exception as e:
                logger.warning(f"Failed to get LLM provider: {e}")
        return self.llm

    async def research_topic_async(
        self, topic: str, depth: str = "medium", mode: str = "lateral"
    ) -> Dict[str, Any]:
        """
        Research a topic using RAG and LLM (async version).

        Args:
            topic: Topic to research
            depth: Research depth (shallow, medium, deep)
            mode: Retrieval mode (foundation, lateral, factcheck)

        Returns:
            Dictionary with research results
        """
        research = {
            "topic": topic,
            "depth": depth,
            "mode": mode,
            "sources": [],
            "summary": "",
            "key_points": [],
            "lateral_connections": [],
            "timestamp": datetime.now().isoformat(),
            "rag_used": False,
            "llm_used": False,
            "memory_used": False,
            "prior_research": [],
        }

        # Check for relevant past research
        if self.research_memory and self.research_memory.enabled:
            try:
                context = self.research_memory.get_research_context(
                    topic, max_context_items=3
                )
                research["prior_research"] = context.get("similar_research", [])
                research["memory_used"] = len(context["similar_research"]) > 0

                # Adjust depth based on past research
                if context.get("recommended_depth"):
                    if depth == "shallow" and context["recommended_depth"] == "deep":
                        logger.info(
                            f"Upgrading research depth to {context['recommended_depth']} based on prior research"
                        )
                        depth = context["recommended_depth"]
                        research["depth"] = depth

            except Exception as e:
                logger.warning(f"Failed to get research context: {e}")

        # Determine top_k based on depth
        depth_to_k = {"shallow": 3, "medium": 5, "deep": 10}
        top_k = depth_to_k.get(depth, 5)

        # Use Librarian RAG for retrieval
        if self.use_rag and self.librarian:
            try:
                result = self.librarian.query(topic, mode=mode, top_k=top_k)

                research["rag_used"] = True
                research["sources"] = [
                    {
                        "content": (
                            doc.content[:200] + "..."
                            if len(doc.content) > 200
                            else doc.content
                        ),
                        "metadata": doc.metadata,
                        "score": doc.score,
                    }
                    for doc in result.documents
                ]
                research["key_points"] = self._extract_key_points(result.documents)
                research["rag_confidence"] = result.confidence

                # Get lateral connections if in lateral mode
                if mode == "lateral":
                    connections = self.librarian.find_connections(topic)
                    research["lateral_connections"] = connections.get(
                        "domains_touched", []
                    )

            except Exception as e:
                logger.error(f"RAG retrieval failed: {e}")
                research["rag_error"] = str(e)

        # Use LLM for synthesis
        llm = await self._get_llm()
        if llm:
            try:
                # Build context from sources
                context = "\n\n".join(
                    [
                        f"Source {i+1}: {s.get('content', '')}"
                        for i, s in enumerate(research["sources"][:5])
                    ]
                )

                prompt = f"""Based on the following research context, provide a comprehensive summary about "{topic}".

{context if context else "No sources available - provide general knowledge."}

Provide:
1. A clear summary (2-3 paragraphs)
2. 5 key points
3. Potential areas for deeper research
"""

                response = await llm.chat(
                    [
                        {
                            "role": "system",
                            "content": "You are a research analyst providing thorough, evidence-based summaries.",
                        },
                        {"role": "user", "content": prompt},
                    ]
                )

                research["summary"] = response.content
                research["llm_used"] = True
                research["llm_model"] = response.model

            except Exception as e:
                logger.error(f"LLM synthesis failed: {e}")
                research["llm_error"] = str(e)

        # Fallback if no services available
        if not research["summary"]:
            research["summary"] = (
                f"Research summary for {topic} (generated without LLM)"
            )
            if not research["key_points"]:
                research["key_points"] = [f"Key information about {topic}"]

        # Store research findings in memory for future recall
        if self.research_memory and self.research_memory.enabled:
            try:
                memory_id = self.research_memory.store_research(
                    topic=topic,
                    summary=research["summary"],
                    key_points=research["key_points"],
                    sources=research["sources"],
                    depth=depth,
                    mode=mode,
                    lateral_connections=research.get("lateral_connections", []),
                )
                if memory_id:
                    research["memory_stored"] = True
                    research["memory_id"] = memory_id
                    logger.info(f"Research on '{topic}' stored in memory: {memory_id}")
            except Exception as e:
                logger.warning(f"Failed to store research in memory: {e}")

        return research

    def research_topic(self, topic: str, depth: str = "medium") -> Dict[str, Any]:
        """
        Research a topic (synchronous version with RAG support).

        Args:
            topic: Topic to research
            depth: Research depth (shallow, medium, deep)

        Returns:
            Dictionary with research results
        """
        research = {
            "topic": topic,
            "depth": depth,
            "sources": [],
            "summary": "",
            "key_points": [],
            "timestamp": datetime.now().isoformat(),
            "rag_used": False,
            "memory_used": False,
        }

        depth_to_k = {"shallow": 3, "medium": 5, "deep": 10}
        top_k = depth_to_k.get(depth, 5)

        # Use Librarian RAG
        if self.use_rag and self.librarian:
            try:
                result = self.librarian.query(topic, mode="foundation", top_k=top_k)
                research["rag_used"] = True
                research["sources"] = [
                    {"content": doc.content[:200], "score": doc.score}
                    for doc in result.documents
                ]
                research["key_points"] = self._extract_key_points(result.documents)
                research["summary"] = result.answer
            except Exception as e:
                logger.error(f"RAG retrieval failed: {e}")

        # Fallback
        if not research["key_points"]:
            research["key_points"].append(f"Key information about {topic}")
        if not research["summary"]:
            research["summary"] = f"Research summary for {topic}"

        # Store research in memory
        if self.research_memory and self.research_memory.enabled:
            try:
                memory_id = self.research_memory.store_research(
                    topic=topic,
                    summary=research["summary"],
                    key_points=research["key_points"],
                    sources=research["sources"],
                    depth=depth,
                    mode="foundation",
                )
                if memory_id:
                    research["memory_stored"] = True
            except Exception as e:
                logger.warning(f"Failed to store research: {e}")

        return research

    def _extract_key_points(self, documents: List) -> List[str]:
        """Extract key points from retrieved documents."""
        key_points = []
        for doc in documents[:MAX_DOCUMENTS]:
            # Extract first sentence or truncate
            content = doc.content
            if ". " in content:
                first_sentence = content.split(". ")[0] + "."
            else:
                first_sentence = (
                    content[:TRUNCATE_LENGTH] + "..."
                    if len(content) > TRUNCATE_LENGTH
                    else content
                )
            key_points.append(first_sentence)
        return key_points

    def analyze_document(self, document_path: str) -> Dict[str, Any]:
        """
        Analyze a document and extract key information.

        Actually reads and processes the document if it exists.

        Args:
            document_path: Path to document to analyze

        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "document": document_path,
            "summary": "",
            "key_topics": [],
            "entities": [],
            "word_count": 0,
            "sentiment": "neutral",
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
        }

        path = Path(document_path)

        if not path.exists():
            analysis["status"] = "error"
            analysis["error"] = f"File not found: {document_path}"
            return analysis

        try:
            # Read document
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            analysis["word_count"] = len(content.split())
            analysis["char_count"] = len(content)
            analysis["status"] = "analyzed"

            # Basic topic extraction (find headers in markdown)
            if path.suffix in [".md", ".markdown"]:
                headers = [
                    line.strip("# ").strip()
                    for line in content.split("\n")
                    if line.startswith("#")
                ]
                analysis["key_topics"] = headers[:10]

            # Simple summary (first paragraph)
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            if paragraphs:
                first_para = paragraphs[0]
                analysis["summary"] = (
                    first_para[:300] + "..." if len(first_para) > 300 else first_para
                )

            # Ingest to librarian if available
            if self.use_rag and self.librarian:
                try:
                    ingest_result = self.librarian.ingest_documents(
                        str(path), recursive=False
                    )
                    analysis["indexed"] = ingest_result.get("status") == "success"
                except Exception as e:
                    analysis["indexing_error"] = str(e)

        except Exception as e:
            analysis["status"] = "error"
            analysis["error"] = str(e)

        return analysis

    async def gather_intelligence_async(self, queries: List[str]) -> Dict[str, Any]:
        """
        Gather intelligence from multiple queries using RAG (async).

        Args:
            queries: List of queries to research

        Returns:
            Dictionary with aggregated intelligence
        """
        intelligence = {
            "queries": queries,
            "findings": [],
            "synthesis": "",
            "confidence": "medium",
            "timestamp": datetime.now().isoformat(),
        }

        # Research each query
        for query in queries:
            result = await self.research_topic_async(query, depth="medium")

            finding = {
                "query": query,
                "results": result.get("sources", []),
                "summary": result.get("summary", ""),
                "relevance": "high" if result.get("rag_used") else "medium",
            }
            intelligence["findings"].append(finding)

        # Synthesize findings with LLM
        llm = await self._get_llm()
        if llm and intelligence["findings"]:
            try:
                findings_text = "\n\n".join(
                    [
                        f"Query: {f['query']}\nSummary: {f['summary']}"
                        for f in intelligence["findings"]
                    ]
                )

                response = await llm.chat(
                    [
                        {
                            "role": "system",
                            "content": "You are an intelligence analyst synthesizing multiple research findings.",
                        },
                        {
                            "role": "user",
                            "content": f"Synthesize the following research findings into a coherent intelligence report:\n\n{findings_text}",
                        },
                    ]
                )

                intelligence["synthesis"] = response.content
                intelligence["confidence"] = "high"
            except Exception as e:
                logger.error(f"Synthesis failed: {e}")

        return intelligence

    def gather_intelligence(self, queries: List[str]) -> Dict[str, Any]:
        """
        Gather intelligence from multiple queries (sync version).

        Args:
            queries: List of queries to research

        Returns:
            Dictionary with aggregated intelligence
        """
        intelligence = {
            "queries": queries,
            "findings": [],
            "synthesis": "",
            "confidence": "medium",
            "timestamp": datetime.now().isoformat(),
        }

        for query in queries:
            result = self.research_topic(query)
            finding = {
                "query": query,
                "results": result.get("sources", []),
                "summary": result.get("summary", ""),
                "relevance": "high" if result.get("rag_used") else "medium",
            }
            intelligence["findings"].append(finding)

        return intelligence

    def create_knowledge_graph(self, topic: str) -> Dict[str, Any]:
        """
        Create a knowledge graph for a topic.

        Uses librarian lateral thinking to find connections.

        Args:
            topic: Central topic for the graph

        Returns:
            Dictionary with graph structure
        """
        graph = {
            "topic": topic,
            "nodes": [],
            "edges": [],
            "metadata": {"created": datetime.now().isoformat(), "rag_used": False},
        }

        # Add central node
        graph["nodes"].append(
            {"id": topic, "label": topic, "type": "topic", "central": True}
        )

        # Use librarian for lateral connections
        if self.use_rag and self.librarian:
            try:
                connections = self.librarian.find_connections(topic)
                graph["metadata"]["rag_used"] = True

                # Add domain nodes
                for domain in connections.get("domains_touched", []):
                    node_id = f"domain_{domain}"
                    graph["nodes"].append(
                        {"id": node_id, "label": domain, "type": "domain"}
                    )
                    graph["edges"].append(
                        {"source": topic, "target": node_id, "relation": "connected_to"}
                    )

                # Query for related concepts
                result = self.librarian.query(topic, mode="lateral", top_k=10)

                for i, doc in enumerate(result.documents[:5]):
                    source = doc.metadata.get("source", f"concept_{i}")
                    node_id = f"concept_{i}"
                    graph["nodes"].append(
                        {
                            "id": node_id,
                            "label": source,
                            "type": "concept",
                            "score": doc.score,
                        }
                    )
                    graph["edges"].append(
                        {
                            "source": topic,
                            "target": node_id,
                            "relation": "related_to",
                            "weight": doc.score,
                        }
                    )

            except Exception as e:
                logger.error(f"Knowledge graph creation failed: {e}")
                graph["error"] = str(e)

        return graph

    def track_sources(self, source_urls: List[str]) -> Dict[str, Any]:
        """
        Track and monitor information sources.

        Args:
            source_urls: List of URLs to track

        Returns:
            Dictionary with tracking status
        """
        tracking = {
            "sources": [],
            "updates": [],
            "status": "tracking",
            "timestamp": datetime.now().isoformat(),
        }

        for url in source_urls:
            source_entry = {
                "url": url,
                "last_checked": datetime.now().isoformat(),
                "status": "active",
                "reachable": False,
            }

            # Try to check if URL is reachable
            try:
                import urllib.request

                urllib.request.urlopen(url, timeout=5)
                source_entry["reachable"] = True
            except Exception:
                source_entry["status"] = "unreachable"

            tracking["sources"].append(source_entry)
            self.sources.append(url)

        return tracking

    async def generate_report_async(self, topic: str) -> str:
        """
        Generate a comprehensive research report using LLM (async).

        Args:
            topic: Topic for the report

        Returns:
            Formatted report string
        """
        # Gather research
        research = await self.research_topic_async(topic, depth="deep")

        # Build report
        report_lines = [
            f"# Research Report: {topic}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"RAG: {'✅' if research.get('rag_used') else '❌'} | LLM: {'✅' if research.get('llm_used') else '❌'}",
            "",
            "## Executive Summary",
            "",
            research.get("summary", "No summary available."),
            "",
            "## Key Findings",
            "",
        ]

        for i, point in enumerate(research.get("key_points", []), 1):
            report_lines.append(f"{i}. {point}")

        if research.get("lateral_connections"):
            report_lines.extend(["", "## Lateral Connections", ""])
            for conn in research["lateral_connections"]:
                report_lines.append(f"- {conn}")

        report_lines.extend(["", "## Sources", ""])

        for i, source in enumerate(research.get("sources", []), 1):
            score = source.get("score", 0)
            report_lines.append(f"{i}. Score: {score:.2f}")

        return "\n".join(report_lines)

    def generate_report(self, topic: str) -> str:
        """
        Generate a research report (sync version).

        Args:
            topic: Topic for the report

        Returns:
            Formatted report string
        """
        research = self.research_topic(topic, depth="deep")

        report = f"""
# Research Report: {topic}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
RAG: {'✅' if research.get('rag_used') else '❌'}

## Executive Summary

{research.get('summary', 'No summary available.')}

## Key Findings

"""
        for i, point in enumerate(research.get("key_points", []), 1):
            report += f"{i}. {point}\n"

        report += """
## Sources

"""
        for i, source in enumerate(research.get("sources", []), 1):
            report += f"{i}. Score: {source.get('score', 0):.2f}\n"

        return report


def main():
    """Main entry point for the agent"""
    agent = ResearchIntelAgent()

    print("=" * 60)
    print("RESEARCH INTEL AGENT - Real Implementation")
    print("=" * 60)
    print(f"RAG Available: {agent.use_rag}")
    print(f"LLM Available: {agent.use_llm}")
    print()

    # Test research
    research = agent.research_topic("AI agent orchestration", depth="medium")
    print(f"Research Topic: {research['topic']}")
    print(f"RAG Used: {research.get('rag_used')}")
    print(f"Key Points: {len(research.get('key_points', []))}")
    print()

    # Test report
    print("Generated Report:")
    print(agent.generate_report("AI agent orchestration"))


if __name__ == "__main__":
    main()
