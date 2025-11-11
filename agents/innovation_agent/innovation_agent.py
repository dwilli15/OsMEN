#!/usr/bin/env python3
"""
OsMEN Innovation Agent
Monitors frameworks, tools, and automation patterns for improvements
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Innovation:
    """Represents a discovered innovation"""
    id: str
    name: str
    category: str  # framework, tool, pattern
    source: str
    url: str
    discovered_date: str
    summary: str
    relevance_score: int  # 1-10
    complexity_score: int  # 1-10
    impact_score: int  # 1-10
    risk_level: str  # low, medium, high
    no_code_compatible: bool
    recommendation: str  # implement, hold, research_more, reject
    details: Dict[str, Any]


class InnovationMonitor:
    """Monitors various sources for innovations"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent / "config"
        self.config_path.mkdir(exist_ok=True)
        self.cache_path = self.config_path / "cache.json"
        self.cache = self._load_cache()
        
        # Load watch list from memory.json
        memory_path = Path(__file__).parent.parent.parent / ".copilot" / "memory.json"
        with open(memory_path) as f:
            memory = json.load(f)
        self.watch_list = memory.get("innovation_agent", {}).get("watch_list", [])
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache of previously seen items"""
        if self.cache_path.exists():
            with open(self.cache_path) as f:
                return json.load(f)
        return {"seen_urls": [], "last_scan": None}
    
    def _save_cache(self):
        """Save cache"""
        with open(self.cache_path, "w") as f:
            json.dump(self.cache, f, indent=2)
    
    async def scan_github_releases(self, repos: List[str]) -> List[Innovation]:
        """Scan GitHub repositories for new releases"""
        innovations = []
        
        for repo in repos:
            try:
                # GitHub API doesn't require auth for public repos
                url = f"https://api.github.com/repos/{repo}/releases/latest"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    release = response.json()
                    release_url = release.get("html_url", "")
                    
                    if release_url not in self.cache["seen_urls"]:
                        innovation = self._evaluate_github_release(repo, release)
                        if innovation:
                            innovations.append(innovation)
                            self.cache["seen_urls"].append(release_url)
                
            except Exception as e:
                logger.warning(f"Error scanning {repo}: {e}")
        
        return innovations
    
    def _evaluate_github_release(self, repo: str, release: Dict) -> Optional[Innovation]:
        """Evaluate a GitHub release"""
        tag_name = release.get("tag_name", "")
        name = release.get("name", tag_name)
        body = release.get("body", "")
        url = release.get("html_url", "")
        published = release.get("published_at", "")
        
        # Simple scoring based on repo name matching watch list
        repo_name = repo.split("/")[-1].lower()
        relevance = 5
        for watch_item in self.watch_list:
            if watch_item.lower() in repo_name or watch_item.lower() in name.lower():
                relevance = 8
                break
        
        # Skip if relevance too low
        if relevance < 7:
            return None
        
        return Innovation(
            id=f"github_{repo.replace('/', '_')}_{tag_name}",
            name=f"{repo} {tag_name}",
            category="framework",
            source="GitHub Releases",
            url=url,
            discovered_date=published or datetime.now(timezone.utc).isoformat(),
            summary=body[:500] if body else f"New release {tag_name}",
            relevance_score=relevance,
            complexity_score=6,
            impact_score=7,
            risk_level="medium",
            no_code_compatible=True,
            recommendation="research_more",
            details={
                "repo": repo,
                "tag": tag_name,
                "release_notes": body
            }
        )
    
    async def scan_rss_feeds(self, feeds: List[str]) -> List[Innovation]:
        """Scan RSS feeds for innovations"""
        innovations = []
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]:  # Top 5 entries
                    entry_url = entry.get("link", "")
                    
                    if entry_url not in self.cache["seen_urls"]:
                        innovation = self._evaluate_rss_entry(entry)
                        if innovation:
                            innovations.append(innovation)
                            self.cache["seen_urls"].append(entry_url)
                
            except Exception as e:
                logger.warning(f"Error scanning feed {feed_url}: {e}")
        
        return innovations
    
    def _evaluate_rss_entry(self, entry: Any) -> Optional[Innovation]:
        """Evaluate an RSS feed entry"""
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        url = entry.get("link", "")
        published = entry.get("published", "")
        
        # Check relevance to watch list
        relevance = 5
        text = f"{title} {summary}".lower()
        for watch_item in self.watch_list:
            if watch_item.lower() in text:
                relevance = 7
                break
        
        if relevance < 7:
            return None
        
        return Innovation(
            id=f"rss_{hash(url)}",
            name=title,
            category="pattern",
            source="RSS Feed",
            url=url,
            discovered_date=published or datetime.now(timezone.utc).isoformat(),
            summary=summary[:500],
            relevance_score=relevance,
            complexity_score=5,
            impact_score=6,
            risk_level="low",
            no_code_compatible=True,
            recommendation="research_more",
            details={"feed_entry": entry}
        )
    
    async def scan_arxiv(self, queries: List[str]) -> List[Innovation]:
        """Scan ArXiv for academic papers"""
        innovations = []
        
        for query in queries:
            try:
                # ArXiv API
                url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results=5"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    # Parse XML response
                    soup = BeautifulSoup(response.content, "xml")
                    entries = soup.find_all("entry")
                    
                    for entry in entries:
                        paper_url = entry.find("id").text
                        
                        if paper_url not in self.cache["seen_urls"]:
                            innovation = self._evaluate_arxiv_paper(entry)
                            if innovation:
                                innovations.append(innovation)
                                self.cache["seen_urls"].append(paper_url)
                
            except Exception as e:
                logger.warning(f"Error scanning ArXiv for {query}: {e}")
        
        return innovations
    
    def _evaluate_arxiv_paper(self, entry: Any) -> Optional[Innovation]:
        """Evaluate an ArXiv paper"""
        title = entry.find("title").text.strip()
        summary = entry.find("summary").text.strip()
        url = entry.find("id").text
        published = entry.find("published").text
        
        # Academic papers need high relevance
        relevance = 5
        text = f"{title} {summary}".lower()
        for watch_item in self.watch_list:
            if watch_item.lower() in text:
                relevance = 8
                break
        
        if relevance < 8:
            return None
        
        return Innovation(
            id=f"arxiv_{hash(url)}",
            name=title,
            category="pattern",
            source="ArXiv",
            url=url,
            discovered_date=published,
            summary=summary[:500],
            relevance_score=relevance,
            complexity_score=8,
            impact_score=7,
            risk_level="low",
            no_code_compatible=False,
            recommendation="research_more",
            details={"paper": {"title": title, "abstract": summary}}
        )


class InnovationAgent:
    """Main innovation agent"""
    
    def __init__(self):
        self.monitor = InnovationMonitor()
        self.backlog_path = Path(__file__).parent.parent.parent / "docs" / "INNOVATION_BACKLOG.md"
        self.backlog_path.parent.mkdir(exist_ok=True)
    
    async def weekly_scan(self) -> List[Innovation]:
        """Perform weekly scan of all sources"""
        logger.info("Starting weekly innovation scan...")
        
        all_innovations = []
        
        # GitHub repositories to watch
        github_repos = [
            "microsoft/autogen",
            "microsoft/semantic-kernel",
            "langchain-ai/langgraph",
            "joaomdmoura/crewAI",
            "run-llama/llama_index",
            "langflow-ai/langflow",
            "n8n-io/n8n"
        ]
        
        # RSS feeds
        rss_feeds = [
            "https://news.ycombinator.com/rss",
            "https://www.reddit.com/r/MachineLearning/.rss",
            "https://www.reddit.com/r/LocalLLaMA/.rss"
        ]
        
        # ArXiv queries
        arxiv_queries = [
            "autonomous+agents",
            "llm+orchestration",
            "agentic+workflows"
        ]
        
        # Scan all sources
        github_innovations = await self.monitor.scan_github_releases(github_repos)
        all_innovations.extend(github_innovations)
        
        rss_innovations = await self.monitor.scan_rss_feeds(rss_feeds)
        all_innovations.extend(rss_innovations)
        
        arxiv_innovations = await self.monitor.scan_arxiv(arxiv_queries)
        all_innovations.extend(arxiv_innovations)
        
        # Save cache
        self.monitor.cache["last_scan"] = datetime.now(timezone.utc).isoformat()
        self.monitor._save_cache()
        
        # Update backlog
        self._update_backlog(all_innovations)
        
        logger.info(f"Scan complete. Found {len(all_innovations)} new innovations.")
        return all_innovations
    
    def _update_backlog(self, innovations: List[Innovation]):
        """Update innovation backlog document"""
        # Read existing backlog
        existing_content = ""
        if self.backlog_path.exists():
            with open(self.backlog_path) as f:
                existing_content = f.read()
        
        # Generate new discoveries section
        new_section = f"\n\n## New Discoveries ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})\n\n"
        
        for innovation in innovations:
            new_section += f"### {innovation.name}\n\n"
            new_section += f"**Category:** {innovation.category}\n"
            new_section += f"**Source:** {innovation.source}\n"
            new_section += f"**URL:** {innovation.url}\n"
            new_section += f"**Date:** {innovation.discovered_date}\n\n"
            new_section += f"**Summary:**\n{innovation.summary}\n\n"
            new_section += f"**Evaluation:**\n"
            new_section += f"- Relevance: {innovation.relevance_score}/10\n"
            new_section += f"- Complexity: {innovation.complexity_score}/10\n"
            new_section += f"- Impact: {innovation.impact_score}/10\n"
            new_section += f"- Risk: {innovation.risk_level}\n"
            new_section += f"- No-Code Compatible: {'Yes' if innovation.no_code_compatible else 'No'}\n\n"
            new_section += f"**Recommendation:** {innovation.recommendation}\n\n"
            new_section += "---\n\n"
        
        # Prepend to existing content
        if "# Innovation Backlog" in existing_content:
            # Insert after header
            parts = existing_content.split("\n", 2)
            updated_content = parts[0] + "\n" + (parts[1] if len(parts) > 1 else "") + new_section + (parts[2] if len(parts) > 2 else "")
        else:
            updated_content = f"# Innovation Backlog\n\n{new_section}{existing_content}"
        
        # Write updated backlog
        with open(self.backlog_path, "w") as f:
            f.write(updated_content)
        
        logger.info(f"Updated backlog at {self.backlog_path}")
    
    async def generate_weekly_digest(self, innovations: List[Innovation]) -> str:
        """Generate weekly digest for user review"""
        digest = "# Weekly Innovation Digest\n\n"
        digest += f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n"
        digest += f"**New Discoveries:** {len(innovations)}\n\n"
        
        if not innovations:
            digest += "No new innovations discovered this week.\n"
            return digest
        
        # Group by recommendation
        recommend_impl = [i for i in innovations if i.recommendation == "implement"]
        recommend_research = [i for i in innovations if i.recommendation == "research_more"]
        others = [i for i in innovations if i.recommendation not in ["implement", "research_more"]]
        
        if recommend_impl:
            digest += "## Recommended for Implementation\n\n"
            for innovation in recommend_impl:
                digest += f"- **{innovation.name}** ({innovation.category})\n"
                digest += f"  - Scores: R:{innovation.relevance_score}/10, I:{innovation.impact_score}/10, C:{innovation.complexity_score}/10\n"
                digest += f"  - {innovation.url}\n\n"
        
        if recommend_research:
            digest += "## Needs Further Research\n\n"
            for innovation in recommend_research:
                digest += f"- **{innovation.name}** ({innovation.category})\n"
                digest += f"  - Scores: R:{innovation.relevance_score}/10, I:{innovation.impact_score}/10\n"
                digest += f"  - {innovation.url}\n\n"
        
        if others:
            digest += "## Other Discoveries\n\n"
            for innovation in others:
                digest += f"- **{innovation.name}** - {innovation.recommendation}\n"
        
        return digest


async def main():
    """Main entry point"""
    agent = InnovationAgent()
    innovations = await agent.weekly_scan()
    
    # Generate digest
    digest = await agent.generate_weekly_digest(innovations)
    print("\n" + digest)
    
    return {
        "status": "success",
        "innovations_found": len(innovations),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(json.dumps(result, indent=2))
