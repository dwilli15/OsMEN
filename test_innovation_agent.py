#!/usr/bin/env python3
"""
Test suite for Innovation Agent
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.innovation_agent.innovation_agent import InnovationAgent, InnovationMonitor


async def test_innovation_agent():
    """Test innovation agent functionality"""
    print("\n" + "="*50)
    print("Testing Innovation Agent")
    print("="*50)
    
    try:
        # Initialize agent
        agent = InnovationAgent()
        
        # Test monitor initialization
        monitor = InnovationMonitor()
        assert monitor.cache is not None, "Cache should be initialized"
        assert monitor.watch_list is not None, "Watch list should be loaded"
        
        print("✅ Innovation Agent initialized")
        
        # Test GitHub scanning (with limited repos to avoid rate limits)
        print("\nTesting GitHub release scanning...")
        github_innovations = await monitor.scan_github_releases(["langflow-ai/langflow"])
        print(f"Found {len(github_innovations)} GitHub innovations")
        
        # Test RSS feed scanning (with one feed)
        print("\nTesting RSS feed scanning...")
        rss_innovations = await monitor.scan_rss_feeds(["https://news.ycombinator.com/rss"])
        print(f"Found {len(rss_innovations)} RSS innovations")
        
        # Test digest generation
        print("\nTesting digest generation...")
        all_innovations = github_innovations + rss_innovations
        digest = await agent.generate_weekly_digest(all_innovations)
        assert digest, "Digest should be generated"
        assert "Weekly Innovation Digest" in digest, "Digest should have header"
        print(f"Generated digest ({len(digest)} chars)")
        
        print("\n✅ All tests passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_innovation_agent())
    sys.exit(0 if success else 1)
