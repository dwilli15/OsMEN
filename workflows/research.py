"""
Research Workflow for OsMEN

Deep research workflow using OpenDeepResearch and LocalDeepResearcher patterns.
Performs multi-source synthesis with citation tracking.

Usage:
    from workflows.research import ResearchWorkflow
    
    workflow = ResearchWorkflow()
    result = await workflow.run(
        topic="AI Agent Frameworks",
        depth="deep",  # quick, standard, deep
        sources=["web", "papers", "docs"]
    )
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class ResearchDepth(str, Enum):
    """Research depth levels"""
    QUICK = "quick"      # 1-2 sources, no follow-up
    STANDARD = "standard"  # 3-5 sources, basic analysis
    DEEP = "deep"        # 5-10 sources, multi-step analysis


class SourceType(str, Enum):
    """Source types for research"""
    WEB = "web"
    PAPERS = "papers"
    DOCS = "docs"
    NEWS = "news"
    CODE = "code"
    FORUMS = "forums"


@dataclass
class Citation:
    """A citation/reference"""
    id: str
    title: str
    url: Optional[str]
    source_type: SourceType
    author: Optional[str] = None
    date: Optional[str] = None
    snippet: Optional[str] = None
    relevance_score: float = 0.0


@dataclass
class ResearchSection:
    """A section of the research report"""
    title: str
    content: str
    citations: List[Citation] = field(default_factory=list)
    subsections: List["ResearchSection"] = field(default_factory=list)


@dataclass
class ResearchResult:
    """Complete research result"""
    topic: str
    summary: str
    sections: List[ResearchSection]
    citations: List[Citation]
    metadata: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_markdown(self) -> str:
        """Convert to markdown format"""
        lines = [
            f"# Research Report: {self.topic}",
            "",
            f"*Generated: {self.created_at.strftime('%Y-%m-%d %H:%M')}*",
            "",
            "## Executive Summary",
            "",
            self.summary,
            ""
        ]
        
        for section in self.sections:
            lines.extend(self._section_to_markdown(section, level=2))
        
        if self.citations:
            lines.extend([
                "## References",
                ""
            ])
            for i, cite in enumerate(self.citations, 1):
                cite_line = f"{i}. **{cite.title}**"
                if cite.author:
                    cite_line += f" - {cite.author}"
                if cite.date:
                    cite_line += f" ({cite.date})"
                if cite.url:
                    cite_line += f" [[link]({cite.url})]"
                lines.append(cite_line)
            lines.append("")
        
        return "\n".join(lines)
    
    def _section_to_markdown(self, section: ResearchSection, level: int) -> List[str]:
        """Convert section to markdown"""
        prefix = "#" * level
        lines = [
            f"{prefix} {section.title}",
            "",
            section.content,
            ""
        ]
        
        for subsection in section.subsections:
            lines.extend(self._section_to_markdown(subsection, level + 1))
        
        return lines


class ResearchAgent:
    """
    Agent that performs research on a specific source type.
    
    Can search web, academic papers, documentation, news, and forums.
    """
    
    def __init__(self, source_type: SourceType, llm_provider=None):
        """
        Initialize research agent.
        
        Args:
            source_type: Type of source to search
            llm_provider: LLM provider for analysis
        """
        self.source_type = source_type
        self.llm = llm_provider
        self._search_results: List[Dict[str, Any]] = []
    
    async def search(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for information on the topic.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of search results
        """
        # In production, this would use actual search APIs
        # For now, generate mock results based on source type
        
        logger.info(f"Searching {self.source_type.value} for: {query}")
        
        results = []
        
        if self.source_type == SourceType.WEB:
            results = self._mock_web_search(query, max_results)
        elif self.source_type == SourceType.PAPERS:
            results = self._mock_paper_search(query, max_results)
        elif self.source_type == SourceType.DOCS:
            results = self._mock_docs_search(query, max_results)
        elif self.source_type == SourceType.NEWS:
            results = self._mock_news_search(query, max_results)
        elif self.source_type == SourceType.CODE:
            results = self._mock_code_search(query, max_results)
        elif self.source_type == SourceType.FORUMS:
            results = self._mock_forum_search(query, max_results)
        
        self._search_results = results
        return results
    
    def _mock_web_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Generate mock web search results"""
        base_results = [
            {
                "title": f"Comprehensive Guide to {query}",
                "url": f"https://example.com/guide/{query.replace(' ', '-').lower()}",
                "snippet": f"A detailed overview of {query}, covering key concepts and best practices...",
                "date": "2024-11-15"
            },
            {
                "title": f"{query}: What You Need to Know in 2024",
                "url": f"https://techblog.com/{query.replace(' ', '-').lower()}",
                "snippet": f"The latest developments in {query}, including recent trends and innovations...",
                "date": "2024-11-20"
            },
            {
                "title": f"Understanding {query} for Beginners",
                "url": f"https://learn.dev/{query.replace(' ', '-').lower()}-101",
                "snippet": f"Start your journey learning about {query} with this beginner-friendly guide...",
                "date": "2024-10-05"
            }
        ]
        return base_results[:max_results]
    
    def _mock_paper_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Generate mock academic paper results"""
        base_results = [
            {
                "title": f"A Survey of {query}: Methods and Applications",
                "url": f"https://arxiv.org/abs/2411.{uuid4().hex[:5]}",
                "authors": ["J. Smith", "A. Johnson", "M. Williams"],
                "snippet": f"We present a comprehensive survey of {query}, analyzing 150+ papers...",
                "date": "2024-11-10",
                "citations": 45
            },
            {
                "title": f"Advances in {query}: A Systematic Review",
                "url": f"https://arxiv.org/abs/2410.{uuid4().hex[:5]}",
                "authors": ["R. Chen", "S. Kumar"],
                "snippet": f"This systematic review examines recent advances in {query}...",
                "date": "2024-10-22",
                "citations": 23
            }
        ]
        return base_results[:max_results]
    
    def _mock_docs_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Generate mock documentation results"""
        base_results = [
            {
                "title": f"Official Documentation: {query}",
                "url": f"https://docs.example.com/{query.replace(' ', '-').lower()}",
                "snippet": f"Official documentation for {query}, including API reference and examples...",
                "date": "2024-11-01"
            },
            {
                "title": f"{query} - Getting Started Guide",
                "url": f"https://docs.example.com/{query.replace(' ', '-').lower()}/quickstart",
                "snippet": f"Get started with {query} in 5 minutes with this quickstart guide...",
                "date": "2024-10-15"
            }
        ]
        return base_results[:max_results]
    
    def _mock_news_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Generate mock news results"""
        return [
            {
                "title": f"Breaking: Major Advancement in {query}",
                "url": f"https://technews.com/2024/11/{query.replace(' ', '-').lower()}",
                "snippet": f"Industry leaders announce breakthrough in {query}...",
                "date": "2024-11-25",
                "source": "TechNews"
            }
        ][:max_results]
    
    def _mock_code_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Generate mock code repository results"""
        return [
            {
                "title": f"{query.replace(' ', '-')}-implementation",
                "url": f"https://github.com/example/{query.replace(' ', '-').lower()}",
                "snippet": f"Reference implementation of {query} in Python...",
                "stars": 1250,
                "language": "Python"
            }
        ][:max_results]
    
    def _mock_forum_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Generate mock forum/discussion results"""
        return [
            {
                "title": f"Discussion: Best practices for {query}?",
                "url": f"https://forum.dev/t/{query.replace(' ', '-').lower()}-best-practices",
                "snippet": f"Community discussion on {query} best practices...",
                "replies": 42,
                "date": "2024-11-18"
            }
        ][:max_results]
    
    async def analyze(
        self,
        results: List[Dict[str, Any]],
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze search results and extract key insights.
        
        Args:
            results: Search results to analyze
            focus_areas: Optional areas to focus on
            
        Returns:
            Analysis with key findings
        """
        if not results:
            return {
                "findings": [],
                "themes": [],
                "gaps": ["No results found"]
            }
        
        # Extract key findings
        findings = []
        for r in results[:5]:
            findings.append({
                "source": r.get("title", "Unknown"),
                "insight": r.get("snippet", ""),
                "relevance": 0.8 + (len(findings) * -0.1)
            })
        
        # Identify themes
        themes = self._extract_themes(results)
        
        return {
            "findings": findings,
            "themes": themes,
            "source_count": len(results),
            "source_type": self.source_type.value
        }
    
    def _extract_themes(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract common themes from results"""
        # Simple theme extraction
        all_text = " ".join(r.get("title", "") + " " + r.get("snippet", "") for r in results)
        words = re.findall(r'\b[A-Z][a-z]+\b', all_text)
        
        # Count word frequency
        word_counts = {}
        for word in words:
            if len(word) > 3:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return top themes
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:5]]
    
    def get_citations(self) -> List[Citation]:
        """Convert search results to citations"""
        citations = []
        for r in self._search_results:
            citations.append(Citation(
                id=str(uuid4()),
                title=r.get("title", "Unknown"),
                url=r.get("url"),
                source_type=self.source_type,
                author=", ".join(r.get("authors", [])) if r.get("authors") else r.get("source"),
                date=r.get("date"),
                snippet=r.get("snippet"),
                relevance_score=0.8
            ))
        return citations


class SynthesisAgent:
    """
    Agent that synthesizes findings from multiple research agents.
    
    Creates cohesive analysis from diverse sources.
    """
    
    def __init__(self, llm_provider=None):
        """
        Initialize synthesis agent.
        
        Args:
            llm_provider: LLM provider for synthesis
        """
        self.llm = llm_provider
    
    async def synthesize(
        self,
        topic: str,
        analyses: List[Dict[str, Any]],
        depth: ResearchDepth
    ) -> ResearchResult:
        """
        Synthesize multiple analyses into a research result.
        
        Args:
            topic: Research topic
            analyses: List of analyses from research agents
            depth: Research depth level
            
        Returns:
            Complete research result
        """
        # Collect all findings
        all_findings = []
        all_themes = []
        all_citations = []
        
        for analysis in analyses:
            all_findings.extend(analysis.get("findings", []))
            all_themes.extend(analysis.get("themes", []))
        
        # Deduplicate themes
        unique_themes = list(dict.fromkeys(all_themes))[:5]
        
        # Generate summary
        summary = self._generate_summary(topic, all_findings, unique_themes)
        
        # Generate sections based on themes
        sections = []
        for theme in unique_themes:
            relevant_findings = [f for f in all_findings if theme.lower() in f.get("insight", "").lower()]
            section = ResearchSection(
                title=theme,
                content=self._generate_section_content(theme, relevant_findings),
                citations=[]  # Would link relevant citations
            )
            sections.append(section)
        
        # Add methodology section
        sections.append(ResearchSection(
            title="Methodology",
            content=f"This research was conducted at {depth.value} depth, analyzing {len(all_findings)} findings from {len(analyses)} source types."
        ))
        
        # Collect all citations
        for analysis in analyses:
            agent_citations = analysis.get("citations", [])
            all_citations.extend(agent_citations)
        
        return ResearchResult(
            topic=topic,
            summary=summary,
            sections=sections,
            citations=all_citations,
            metadata={
                "depth": depth.value,
                "source_count": len(analyses),
                "finding_count": len(all_findings),
                "theme_count": len(unique_themes)
            }
        )
    
    def _generate_summary(
        self,
        topic: str,
        findings: List[Dict[str, Any]],
        themes: List[str]
    ) -> str:
        """Generate executive summary"""
        theme_text = ", ".join(themes[:3]) if themes else "various aspects"
        
        return f"""This research report provides a comprehensive analysis of **{topic}**. 

The investigation covered {len(findings)} key findings across multiple sources, identifying major themes including {theme_text}.

Key insights include:
- Analysis of current state and recent developments
- Identification of best practices and common patterns
- Review of challenges and opportunities in the field

The following sections provide detailed analysis of each major theme."""
    
    def _generate_section_content(
        self,
        theme: str,
        findings: List[Dict[str, Any]]
    ) -> str:
        """Generate section content from findings"""
        if not findings:
            return f"Further research is needed on {theme}."
        
        content_parts = [f"Analysis of {theme} reveals several important insights:"]
        
        for finding in findings[:3]:
            content_parts.append(f"\n- {finding.get('insight', '')}")
        
        return "\n".join(content_parts)


class ResearchWorkflow:
    """
    Complete research workflow orchestrating multiple agents.
    
    Supports quick, standard, and deep research with multi-source synthesis.
    """
    
    def __init__(self, llm_provider=None):
        """
        Initialize research workflow.
        
        Args:
            llm_provider: LLM provider for agents
        """
        self.llm = llm_provider
        self.synthesis_agent = SynthesisAgent(llm_provider)
        
        # Import streaming mixin if available
        try:
            from gateway.streaming import StreamingWorkflowMixin
            self._streaming_mixin = StreamingWorkflowMixin
        except ImportError:
            self._streaming_mixin = None
    
    async def run(
        self,
        topic: str,
        depth: str = "standard",
        sources: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None,
        max_results_per_source: int = 5
    ) -> ResearchResult:
        """
        Run the research workflow.
        
        Args:
            topic: Research topic
            depth: Research depth (quick, standard, deep)
            sources: Source types to search
            focus_areas: Specific areas to focus on
            max_results_per_source: Max results per source
            
        Returns:
            Complete research result
        """
        depth_enum = ResearchDepth(depth)
        
        # Determine sources based on depth
        if sources is None:
            if depth_enum == ResearchDepth.QUICK:
                sources = ["web"]
            elif depth_enum == ResearchDepth.STANDARD:
                sources = ["web", "papers", "docs"]
            else:
                sources = ["web", "papers", "docs", "news", "code"]
        
        # Adjust max results based on depth
        if depth_enum == ResearchDepth.QUICK:
            max_results_per_source = min(max_results_per_source, 3)
        elif depth_enum == ResearchDepth.DEEP:
            max_results_per_source = max(max_results_per_source, 10)
        
        logger.info(f"Starting {depth} research on: {topic}")
        logger.info(f"Sources: {sources}, Max results: {max_results_per_source}")
        
        # Create research agents
        agents = []
        for source in sources:
            try:
                source_type = SourceType(source)
                agents.append(ResearchAgent(source_type, self.llm))
            except ValueError:
                logger.warning(f"Unknown source type: {source}")
        
        # Search all sources in parallel
        search_tasks = []
        for agent in agents:
            task = agent.search(topic, max_results_per_source)
            search_tasks.append(task)
        
        search_results = await asyncio.gather(*search_tasks)
        
        # Analyze results in parallel
        analyze_tasks = []
        for agent, results in zip(agents, search_results):
            task = agent.analyze(results, focus_areas)
            analyze_tasks.append(task)
        
        analyses = await asyncio.gather(*analyze_tasks)
        
        # Add citations to analyses
        for agent, analysis in zip(agents, analyses):
            analysis["citations"] = agent.get_citations()
        
        # Synthesize findings
        result = await self.synthesis_agent.synthesize(topic, analyses, depth_enum)
        
        logger.info(f"Research complete: {len(result.sections)} sections, {len(result.citations)} citations")
        
        return result


# CLI interface
async def main():
    """CLI entry point for research workflow"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OsMEN Research Workflow")
    parser.add_argument("topic", help="Research topic")
    parser.add_argument("--depth", choices=["quick", "standard", "deep"], default="standard")
    parser.add_argument("--sources", nargs="+", help="Source types")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    workflow = ResearchWorkflow()
    result = await workflow.run(
        topic=args.topic,
        depth=args.depth,
        sources=args.sources
    )
    
    markdown = result.to_markdown()
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(markdown)
        print(f"Research saved to: {args.output}")
    else:
        print(markdown)


if __name__ == "__main__":
    asyncio.run(main())
