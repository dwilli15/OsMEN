#!/usr/bin/env python3
"""
Daily Innovation Digest

Generates daily summary of innovation activity.
Part of v1.3.0 Innovation Agent Framework.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from validation import InnovationValidator, InnovationLogger


class DailyDigest:
    """Generate daily innovation digest"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent
        self.validator = InnovationValidator()
        self.logger = InnovationLogger()
        self.digest_dir = self.repo_root / ".copilot" / "daily_digests"
        self.digest_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_digest(self, date: datetime = None) -> str:
        """
        Generate daily digest
        
        Args:
            date: Date to generate for (defaults to yesterday)
        
        Returns:
            Markdown digest
        """
        if date is None:
            date = datetime.now(timezone.utc) - timedelta(days=1)
        
        date_str = date.strftime('%Y-%m-%d')
        
        # Get audit trail for the day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        audit_entries = self.validator.get_audit_trail(limit=1000)
        
        # Filter to this day
        day_entries = []
        for entry in audit_entries:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if start_of_day <= entry_time < end_of_day:
                day_entries.append(entry)
        
        # Generate digest
        digest = f"# Daily Innovation Digest\n\n"
        digest += f"**Date:** {date_str}\n"
        digest += f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        digest += "---\n\n"
        
        if not day_entries:
            digest += "## Summary\n\nNo innovation activity today.\n\n"
            digest += "The innovation monitoring system runs weekly on Sundays.\n"
            return digest
        
        # Count by action type
        action_counts = {}
        for entry in day_entries:
            action = entry["action_type"]
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Summary
        digest += f"## Summary\n\n"
        digest += f"- **Total Actions:** {len(day_entries)}\n"
        for action, count in sorted(action_counts.items()):
            digest += f"- **{action.capitalize()}:** {count}\n"
        digest += "\n---\n\n"
        
        # Activity timeline
        digest += "## Activity Timeline\n\n"
        for entry in day_entries:
            timestamp = entry["timestamp"][11:19]  # HH:MM:SS
            action = entry["action_type"]
            user = entry.get("user", "system")
            
            digest += f"**{timestamp}** - {action} by {user}\n"
            
            # Add details
            data = entry.get("data", {})
            if "title" in data:
                digest += f"  - {data['title']}\n"
            
            digest += "\n"
        
        digest += "---\n\n"
        
        # Status summary
        digest += "## System Status\n\n"
        digest += "- Innovation monitoring: ✅ Active\n"
        digest += "- Next weekly scan: Sunday 6 PM UTC\n"
        digest += "- Audit trail: ✅ Recording\n"
        digest += "\n"
        
        return digest
    
    def save_digest(self, digest: str, date: datetime = None) -> Path:
        """
        Save digest to file
        
        Args:
            digest: Digest content
            date: Date for filename
        
        Returns:
            Path to saved file
        """
        if date is None:
            date = datetime.now(timezone.utc) - timedelta(days=1)
        
        filename = f"digest_{date.strftime('%Y-%m-%d')}.md"
        filepath = self.digest_dir / filename
        
        filepath.write_text(digest)
        
        return filepath
    
    def get_recent_digests(self, days: int = 7) -> List[Path]:
        """Get paths to recent digest files"""
        if not self.digest_dir.exists():
            return []
        
        all_digests = sorted(self.digest_dir.glob("digest_*.md"), reverse=True)
        return all_digests[:days]


def main():
    """Generate daily digest"""
    print("📊 Generating Daily Innovation Digest\n")
    
    digest_gen = DailyDigest()
    
    # Generate for yesterday
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    digest = digest_gen.generate_digest(yesterday)
    
    # Save digest
    filepath = digest_gen.save_digest(digest, yesterday)
    
    print(f"✅ Daily digest generated: {filepath}")
    print(f"\n--- Preview ---")
    print(digest[:500])
    
    # Show recent digests
    recent = digest_gen.get_recent_digests(days=7)
    print(f"\n📁 Recent digests: {len(recent)} files")


if __name__ == "__main__":
    main()
