#!/usr/bin/env python3
"""
Weekly Innovation Digest Generator

Compiles discoveries into a weekly digest for user review.
Part of v1.3.0 Innovation Agent Framework.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from scoring import InnovationScorer


class DigestGenerator:
    """Generate weekly innovation digest"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent
        self.cache_path = self.repo_root / ".copilot" / "innovation_cache.json"
        self.backlog_path = self.repo_root / "docs" / "INNOVATION_BACKLOG.md"
        self.scorer = InnovationScorer()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load innovation cache"""
        if self.cache_path.exists():
            with open(self.cache_path, 'r') as f:
                return json.load(f)
        return {"seen_items": {}, "last_scan": None}
    
    def _get_week_range(self) -> tuple:
        """Get date range for current week"""
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday
        return week_start, week_end
    
    def generate_digest(self, discoveries: List[Dict[str, Any]]) -> str:
        """Generate markdown digest"""
        week_start, week_end = self._get_week_range()
        
        digest = f"# Weekly Innovation Digest\n\n"
        digest += f"**Week of:** {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}\n"
        digest += f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        digest += "---\n\n"
        
        if not discoveries:
            digest += "## Summary\n\nNo new discoveries this week.\n\n"
            digest += "The innovation monitoring system is active and scanning regularly.\n"
            return digest
        
        # Categorize discoveries
        approved = [d for d in discoveries if d.get('recommendation') == 'approve']
        research = [d for d in discoveries if d.get('recommendation') == 'research_more']
        rejected = [d for d in discoveries if d.get('recommendation') == 'reject']
        
        # Summary
        digest += f"## Summary\n\n"
        digest += f"- **Total Discoveries:** {len(discoveries)}\n"
        digest += f"- **Recommended for Approval:** {len(approved)}\n"
        digest += f"- **Requires More Research:** {len(research)}\n"
        digest += f"- **Not Recommended:** {len(rejected)}\n\n"
        digest += "---\n\n"
        
        # Recommended for Approval
        if approved:
            digest += "## 🟢 Recommended for Approval\n\n"
            digest += "These discoveries meet all criteria and are ready for implementation consideration.\n\n"
            
            for i, item in enumerate(approved, 1):
                digest += self._format_discovery(item, i)
            
            digest += "---\n\n"
        
        # Requires Research
        if research:
            digest += "## 🟡 Requires More Research\n\n"
            digest += "These discoveries show promise but need additional evaluation.\n\n"
            
            for i, item in enumerate(research, 1):
                digest += self._format_discovery(item, i, brief=True)
            
            digest += "---\n\n"
        
        # Not Recommended
        if rejected:
            digest += "## 🔴 Not Recommended\n\n"
            digest += "These discoveries do not meet criteria for OsMEN at this time.\n\n"
            
            for i, item in enumerate(rejected, 1):
                digest += f"{i}. **{item['title']}** - Relevance: {item.get('relevance_score', 'N/A')}/10\n"
            
            digest += "\n---\n\n"
        
        # Next Steps
        digest += "## Next Steps\n\n"
        digest += "1. Review recommended items above\n"
        digest += "2. Approve/reject/defer each recommendation\n"
        digest += "3. For approved items, add to implementation queue\n"
        digest += "4. Update `.copilot/pre_approved_tasks.json` if needed\n\n"
        
        digest += "**Review Deadline:** Sunday 6 PM (per innovation guidelines)\n"
        
        return digest
    
    def _format_discovery(self, item: Dict[str, Any], index: int, brief: bool = False) -> str:
        """Format a single discovery"""
        output = f"### {index}. {item['title']}\n\n"
        output += f"**Source:** {item.get('source', 'Unknown')}\n"
        output += f"**Link:** {item.get('link', 'N/A')}\n\n"
        
        # Scores
        output += "**Evaluation:**\n"
        output += f"- Relevance: {item.get('relevance_score', 'N/A')}/10\n"
        output += f"- Complexity: {item.get('complexity_score', 'N/A')}/10\n"
        output += f"- Impact: {item.get('impact_score', 'N/A')}/10\n"
        output += f"- Risk: {item.get('risk_level', 'N/A')}\n"
        output += f"- No-Code Compatible: {item.get('no_code_compatible', 'Unknown')}\n\n"
        
        if not brief:
            # Summary
            summary = item.get('summary', 'No summary available')
            if len(summary) > 300:
                summary = summary[:300] + "..."
            output += f"**Summary:**\n{summary}\n\n"
            
            # Recommendation rationale
            output += f"**Recommendation:** {item.get('recommendation', 'pending').upper()}\n"
            output += self._get_recommendation_rationale(item) + "\n\n"
        
        output += "---\n\n"
        return output
    
    def _get_recommendation_rationale(self, item: Dict[str, Any]) -> str:
        """Get rationale for recommendation"""
        recommendation = item.get('recommendation', 'pending')
        
        if recommendation == 'approve':
            return "Meets all criteria for implementation."
        elif recommendation == 'research_more':
            reasons = []
            if item.get('complexity_score', 0) > 6:
                reasons.append("high complexity")
            if item.get('impact_score', 0) < 6:
                reasons.append("unclear impact")
            if item.get('risk_level') == 'high':
                reasons.append("high risk")
            if not item.get('no_code_compatible'):
                reasons.append("no-code compatibility unclear")
            
            if reasons:
                return f"Needs investigation: {', '.join(reasons)}."
            return "Requires additional evaluation."
        else:
            return "Does not meet minimum relevance threshold."
    
    def update_backlog(self, digest: str):
        """Update INNOVATION_BACKLOG.md with new discoveries"""
        if not self.backlog_path.exists():
            print(f"Warning: {self.backlog_path} does not exist")
            return
        
        # Read current backlog
        content = self.backlog_path.read_text()
        
        # Find insertion point (after "## Current Week Discoveries")
        lines = content.split('\n')
        insert_idx = None
        
        for i, line in enumerate(lines):
            if line.startswith("## Current Week Discoveries"):
                insert_idx = i + 1
                break
        
        if insert_idx is None:
            print("Warning: Could not find insertion point in backlog")
            return
        
        # Insert digest
        week_start, _ = self._get_week_range()
        week_header = f"\n### Week of {week_start.strftime('%Y-%m-%d')}\n\n"
        
        # Clear old "No new discoveries" text if present
        new_lines = []
        skip_until_section = False
        for i, line in enumerate(lines):
            if i == insert_idx:
                new_lines.append(line)
                # Skip old content until next section
                skip_until_section = True
            elif skip_until_section and line.startswith("##"):
                skip_until_section = False
                new_lines.append(line)
            elif not skip_until_section:
                new_lines.append(line)
        
        # Insert new content
        new_lines.insert(insert_idx + 1, week_header + digest)
        
        # Write back
        self.backlog_path.write_text('\n'.join(new_lines))
        print(f"✅ Updated {self.backlog_path}")


def main():
    """Main execution"""
    print("📊 Generating Weekly Innovation Digest\n")
    
    generator = DigestGenerator()
    
    # For now, generate empty digest (will be populated by monitor_feeds.py)
    discoveries = []
    
    digest = generator.generate_digest(discoveries)
    
    # Save digest
    digest_path = Path(".copilot/weekly_digest_latest.md")
    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(digest)
    
    print(f"✅ Digest generated: {digest_path}")
    
    # Update backlog
    generator.update_backlog(digest)
    
    print("\n📧 Digest ready for user review")


if __name__ == "__main__":
    main()
