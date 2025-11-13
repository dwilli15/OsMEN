#!/usr/bin/env python3
"""
Innovation Implementation Queue Manager

Manages the queue of approved innovations awaiting implementation.
Part of v1.3.0 Innovation Agent Framework.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


class ImplementationQueue:
    """Manage innovation implementation queue"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent
        self.queue_path = self.repo_root / ".copilot" / "implementation_queue.json"
        self.queue = self._load_queue()
    
    def _load_queue(self) -> Dict[str, Any]:
        """Load implementation queue from disk"""
        if self.queue_path.exists():
            with open(self.queue_path, 'r') as f:
                return json.load(f)
        
        return {
            "version": "1.0.0",
            "last_updated": None,
            "queued_items": [],
            "in_progress": [],
            "completed": [],
            "statistics": {
                "total_queued": 0,
                "total_completed": 0,
                "avg_implementation_days": 0
            }
        }
    
    def _save_queue(self):
        """Save queue to disk"""
        self.queue["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.queue_path, 'w') as f:
            json.dump(self.queue, f, indent=2)
    
    def add_to_queue(self, innovation: Dict[str, Any], priority: str = "medium") -> str:
        """
        Add approved innovation to implementation queue
        
        Args:
            innovation: Innovation discovery dict
            priority: "low", "medium", "high", or "critical"
        
        Returns:
            Queue item ID
        """
        item_id = f"impl_{len(self.queue['queued_items']) + 1:04d}"
        
        queue_item = {
            "id": item_id,
            "innovation": innovation,
            "priority": priority,
            "status": "queued",
            "queued_date": datetime.now(timezone.utc).isoformat(),
            "target_version": None,
            "assigned_to": None,
            "estimated_effort_hours": None,
            "notes": []
        }
        
        self.queue["queued_items"].append(queue_item)
        self.queue["statistics"]["total_queued"] += 1
        self._save_queue()
        
        return item_id
    
    def start_implementation(self, item_id: str, assigned_to: str = "copilot", 
                            target_version: str = None) -> bool:
        """
        Move item from queue to in-progress
        
        Args:
            item_id: Queue item ID
            assigned_to: Who is implementing (default: "copilot")
            target_version: Target version for release
        
        Returns:
            True if successful
        """
        # Find item in queue
        item = None
        for i, queued_item in enumerate(self.queue["queued_items"]):
            if queued_item["id"] == item_id:
                item = self.queue["queued_items"].pop(i)
                break
        
        if not item:
            return False
        
        # Update item
        item["status"] = "in_progress"
        item["assigned_to"] = assigned_to
        item["target_version"] = target_version
        item["started_date"] = datetime.now(timezone.utc).isoformat()
        
        self.queue["in_progress"].append(item)
        self._save_queue()
        
        return True
    
    def complete_implementation(self, item_id: str, implemented_in_version: str = None,
                               pull_request_url: str = None) -> bool:
        """
        Mark implementation as complete
        
        Args:
            item_id: Queue item ID
            implemented_in_version: Version where implemented
            pull_request_url: PR URL
        
        Returns:
            True if successful
        """
        # Find item in in_progress
        item = None
        for i, in_progress_item in enumerate(self.queue["in_progress"]):
            if in_progress_item["id"] == item_id:
                item = self.queue["in_progress"].pop(i)
                break
        
        if not item:
            return False
        
        # Calculate implementation time
        started = datetime.fromisoformat(item["started_date"])
        completed = datetime.now(timezone.utc)
        days = (completed - started).days
        
        # Update item
        item["status"] = "completed"
        item["completed_date"] = completed.isoformat()
        item["implementation_days"] = days
        item["implemented_in_version"] = implemented_in_version
        item["pull_request_url"] = pull_request_url
        
        self.queue["completed"].append(item)
        self.queue["statistics"]["total_completed"] += 1
        
        # Update average implementation time
        total_days = sum(item.get("implementation_days", 0) for item in self.queue["completed"])
        self.queue["statistics"]["avg_implementation_days"] = total_days / len(self.queue["completed"])
        
        self._save_queue()
        
        return True
    
    def add_note(self, item_id: str, note: str) -> bool:
        """Add note to any item"""
        # Search in all lists
        for item_list in [self.queue["queued_items"], self.queue["in_progress"], self.queue["completed"]]:
            for item in item_list:
                if item["id"] == item_id:
                    item["notes"].append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "note": note
                    })
                    self._save_queue()
                    return True
        
        return False
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item by ID"""
        for item_list in [self.queue["queued_items"], self.queue["in_progress"], self.queue["completed"]]:
            for item in item_list:
                if item["id"] == item_id:
                    return item
        return None
    
    def get_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """Get all queued items with given priority"""
        return [item for item in self.queue["queued_items"] if item["priority"] == priority]
    
    def get_next_item(self) -> Optional[Dict[str, Any]]:
        """Get next highest priority item from queue"""
        priority_order = ["critical", "high", "medium", "low"]
        
        for priority in priority_order:
            items = self.get_by_priority(priority)
            if items:
                return items[0]
        
        return None
    
    def generate_status_report(self) -> str:
        """Generate markdown status report"""
        report = "# Implementation Queue Status\n\n"
        report += f"**Last Updated:** {self.queue['last_updated'] or 'Never'}\n\n"
        
        # Statistics
        stats = self.queue["statistics"]
        report += "## Statistics\n\n"
        report += f"- **Total Queued:** {len(self.queue['queued_items'])}\n"
        report += f"- **In Progress:** {len(self.queue['in_progress'])}\n"
        report += f"- **Completed:** {stats['total_completed']}\n"
        report += f"- **Average Implementation Time:** {stats['avg_implementation_days']:.1f} days\n\n"
        
        # Queued items
        if self.queue["queued_items"]:
            report += "## Queued for Implementation\n\n"
            
            for priority in ["critical", "high", "medium", "low"]:
                items = self.get_by_priority(priority)
                if items:
                    report += f"### {priority.capitalize()} Priority\n\n"
                    for item in items:
                        title = item["innovation"].get("title", "Untitled")
                        report += f"- **{item['id']}**: {title}\n"
                        report += f"  - Queued: {item['queued_date'][:10]}\n"
                        if item.get("target_version"):
                            report += f"  - Target: {item['target_version']}\n"
                    report += "\n"
        
        # In progress
        if self.queue["in_progress"]:
            report += "## In Progress\n\n"
            for item in self.queue["in_progress"]:
                title = item["innovation"].get("title", "Untitled")
                report += f"- **{item['id']}**: {title}\n"
                report += f"  - Assigned: {item.get('assigned_to', 'Unassigned')}\n"
                report += f"  - Started: {item['started_date'][:10]}\n"
                report += f"  - Target: {item.get('target_version', 'TBD')}\n"
            report += "\n"
        
        # Recent completions (last 5)
        if self.queue["completed"]:
            report += "## Recently Completed\n\n"
            recent = sorted(self.queue["completed"], 
                          key=lambda x: x['completed_date'], 
                          reverse=True)[:5]
            
            for item in recent:
                title = item["innovation"].get("title", "Untitled")
                report += f"- **{item['id']}**: {title}\n"
                report += f"  - Completed: {item['completed_date'][:10]}\n"
                report += f"  - Version: {item.get('implemented_in_version', 'Unknown')}\n"
                report += f"  - Duration: {item.get('implementation_days', 0)} days\n"
            report += "\n"
        
        return report


def main():
    """Test implementation queue"""
    queue = ImplementationQueue()
    
    # Example: Add a test innovation
    test_innovation = {
        "id": "test_001",
        "title": "Test Innovation",
        "relevance_score": 8,
        "complexity_score": 4,
        "impact_score": 7
    }
    
    item_id = queue.add_to_queue(test_innovation, priority="high")
    print(f"✅ Added to queue: {item_id}")
    
    # Generate report
    report = queue.generate_status_report()
    print("\n" + report)


if __name__ == "__main__":
    main()
