#!/usr/bin/env python3
"""
Innovation Monitoring - RSS Feed Scanner

Monitors RSS feeds from key sources for relevant AI/agent framework updates.
Part of v1.3.0 Innovation Agent Framework.
"""

import json
import feedparser
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any
import hashlib


class FeedMonitor:
    """Monitor RSS feeds for innovation opportunities"""
    
    def __init__(self, config_path: str = ".copilot/innovation_guidelines.md"):
        self.repo_root = Path(__file__).parent.parent.parent
        self.config_path = self.repo_root / config_path
        self.cache_path = self.repo_root / ".copilot" / "innovation_cache.json"
        self.feeds = self._load_feeds()
        self.cache = self._load_cache()
    
    def _load_feeds(self) -> Dict[str, str]:
        """Load RSS feed URLs to monitor"""
        return {
            "github_langchain": "https://github.com/langchain-ai/langchain/releases.atom",
            "github_autogen": "https://github.com/microsoft/autogen/releases.atom",
            "github_crewai": "https://github.com/joaomdmoura/crewAI/releases.atom",
            "github_semantic_kernel": "https://github.com/microsoft/semantic-kernel/releases.atom",
            "github_llamaindex": "https://github.com/run-llama/llama_index/releases.atom",
            "arxiv_agents": "http://export.arxiv.org/rss/cs.AI",
            "arxiv_nlp": "http://export.arxiv.org/rss/cs.CL",
        }
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache of previously seen items"""
        if self.cache_path.exists():
            with open(self.cache_path, 'r') as f:
                return json.load(f)
        return {"seen_items": {}, "last_scan": None}
    
    def _save_cache(self):
        """Save cache to disk"""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _get_item_hash(self, item: Dict[str, Any]) -> str:
        """Generate unique hash for feed item"""
        key = f"{item.get('link', '')}:{item.get('title', '')}:{item.get('published', '')}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _is_relevant(self, item: Dict[str, Any]) -> bool:
        """Check if item is relevant to OsMEN"""
        # Keywords that indicate relevance
        relevant_keywords = [
            "agent", "autonomous", "multi-agent", "orchestration",
            "llm", "language model", "rag", "retrieval",
            "framework", "workflow", "automation", "memory",
            "context", "planning", "scheduling", "calendar"
        ]
        
        title = item.get('title', '').lower()
        summary = item.get('summary', '').lower()
        content = f"{title} {summary}"
        
        return any(keyword in content for keyword in relevant_keywords)
    
    def _score_relevance(self, item: Dict[str, Any]) -> int:
        """Score item relevance (1-10)"""
        # High-priority keywords
        high_priority = ["agent framework", "autonomous", "multi-agent", "no-code", "workflow"]
        medium_priority = ["llm", "orchestration", "rag", "memory", "planning"]
        
        title = item.get('title', '').lower()
        summary = item.get('summary', '').lower()
        content = f"{title} {summary}"
        
        score = 5  # Base score
        
        for keyword in high_priority:
            if keyword in content:
                score += 2
        
        for keyword in medium_priority:
            if keyword in content:
                score += 1
        
        return min(score, 10)
    
    def scan_feeds(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Scan all feeds for new items"""
        discoveries = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        for feed_name, feed_url in self.feeds.items():
            try:
                print(f"📡 Scanning {feed_name}...")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:20]:  # Limit to recent 20 items
                    item_hash = self._get_item_hash(entry)
                    
                    # Skip if already seen
                    if item_hash in self.cache["seen_items"]:
                        continue
                    
                    # Parse publish date
                    published = None
                    if hasattr(entry, 'published_parsed'):
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    
                    # Skip if too old
                    if published and published < cutoff_date:
                        continue
                    
                    # Check relevance
                    if not self._is_relevant(entry):
                        continue
                    
                    # Score and add to discoveries
                    relevance_score = self._score_relevance(entry)
                    
                    if relevance_score >= 6:  # Threshold from guidelines
                        discovery = {
                            "id": item_hash,
                            "source": feed_name,
                            "title": entry.get('title', 'No title'),
                            "link": entry.get('link', ''),
                            "summary": entry.get('summary', '')[:500],  # Truncate
                            "published": published.isoformat() if published else None,
                            "discovered": datetime.now(timezone.utc).isoformat(),
                            "relevance_score": relevance_score,
                            "complexity_score": None,  # Needs manual assessment
                            "impact_score": None,  # Needs manual assessment
                            "risk_level": None,  # Needs manual assessment
                            "no_code_compatible": None,  # Needs manual assessment
                        }
                        
                        discoveries.append(discovery)
                        self.cache["seen_items"][item_hash] = {
                            "title": discovery["title"],
                            "discovered": discovery["discovered"]
                        }
                
            except Exception as e:
                print(f"❌ Error scanning {feed_name}: {e}")
        
        # Update cache
        self.cache["last_scan"] = datetime.now(timezone.utc).isoformat()
        self._save_cache()
        
        return discoveries
    
    def generate_report(self, discoveries: List[Dict[str, Any]]) -> str:
        """Generate markdown report of discoveries"""
        if not discoveries:
            return "No new discoveries this week."
        
        # Sort by relevance score
        discoveries.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        report = f"# Innovation Scan Report\n\n"
        report += f"**Scan Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n"
        report += f"**New Discoveries:** {len(discoveries)}\n\n"
        report += "---\n\n"
        
        for i, item in enumerate(discoveries, 1):
            report += f"## {i}. {item['title']}\n\n"
            report += f"**Source:** {item['source']}\n"
            report += f"**Link:** {item['link']}\n"
            report += f"**Published:** {item['published'] or 'Unknown'}\n"
            report += f"**Relevance Score:** {item['relevance_score']}/10\n\n"
            report += f"**Summary:**\n{item['summary']}\n\n"
            report += "**Status:** 🔍 Requires manual evaluation\n\n"
            report += "---\n\n"
        
        return report


def main():
    """Main execution"""
    print("🚀 Starting Innovation Feed Monitor\n")
    
    monitor = FeedMonitor()
    discoveries = monitor.scan_feeds(days_back=7)
    
    print(f"\n✅ Scan complete. Found {len(discoveries)} relevant items.\n")
    
    if discoveries:
        report = monitor.generate_report(discoveries)
        
        # Save report
        report_path = Path(".copilot/innovation_scan_latest.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report)
        
        print(f"📄 Report saved to: {report_path}")
        print(f"\nTop discovery: {discoveries[0]['title']}")
    else:
        print("No new discoveries to report.")


if __name__ == "__main__":
    main()
