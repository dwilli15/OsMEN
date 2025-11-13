#!/usr/bin/env python3
"""
Location Context Integration

Integrates location data to optimize scheduling based on context.
Part of v1.6.0 - Adaptive Reminders & Health Integration.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from pathlib import Path


class LocationContextManager:
    """Manage location-based scheduling context"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.location_data_path = self.repo_root / ".copilot" / "location_context.json"
        self.location_data = self._load_location_data()
        
        # Common locations
        self.location_types = [
            "home", "campus", "library", "cafe", "gym", "commute"
        ]
    
    def _load_location_data(self) -> Dict[str, Any]:
        """Load location context data"""
        if self.location_data_path.exists():
            with open(self.location_data_path, 'r') as f:
                return json.load(f)
        
        return {
            "location_history": [],
            "productivity_by_location": {},
            "location_patterns": {}
        }
    
    def _save_location_data(self):
        """Save location data"""
        self.location_data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.location_data_path, 'w') as f:
            json.dump(self.location_data, f, indent=2)
    
    def record_location(self, location_type: str, timestamp: datetime = None):
        """Record current location"""
        if timestamp is None:
            timestamp = datetime.now()
        
        record = {
            "location_type": location_type,
            "timestamp": timestamp.isoformat(),
            "day_of_week": timestamp.strftime("%A"),
            "hour": timestamp.hour
        }
        
        self.location_data.setdefault("location_history", []).append(record)
        self._save_location_data()
    
    def record_productivity_at_location(self, location_type: str,
                                       task_type: str, productivity_score: float):
        """Record productivity at a location for task type"""
        key = f"{location_type}_{task_type}"
        
        if key not in self.location_data.get("productivity_by_location", {}):
            self.location_data.setdefault("productivity_by_location", {})[key] = []
        
        self.location_data["productivity_by_location"][key].append({
            "timestamp": datetime.now().isoformat(),
            "score": productivity_score
        })
        
        self._save_location_data()
    
    def get_best_location_for_task(self, task_type: str) -> str:
        """Get best location for task type based on history"""
        productivity_data = self.location_data.get("productivity_by_location", {})
        
        # Calculate average productivity for each location
        location_scores = {}
        for key, records in productivity_data.items():
            if task_type in key:
                location = key.split('_')[0]
                avg_score = sum(r['score'] for r in records) / len(records)
                location_scores[location] = avg_score
        
        if location_scores:
            return max(location_scores, key=location_scores.get)
        
        # Default recommendations
        defaults = {
            "exam": "library",
            "project": "library",
            "homework": "home",
            "reading": "cafe",
            "review": "home"
        }
        
        return defaults.get(task_type, "library")
    
    def predict_current_location(self) -> str:
        """Predict current location based on patterns"""
        now = datetime.now()
        hour = now.hour
        day_of_week = now.strftime("%A")
        
        # Analyze recent patterns for this time
        history = self.location_data.get("location_history", [])
        recent = [
            r for r in history[-100:]  # Last 100 records
            if r.get("day_of_week") == day_of_week and
            abs(r.get("hour", 0) - hour) <= 1
        ]
        
        if recent:
            # Most common location at this time/day
            locations = [r["location_type"] for r in recent]
            return max(set(locations), key=locations.count)
        
        # Default based on time of day
        if 8 <= hour < 17:
            return "campus"
        elif 17 <= hour < 22:
            return "home"
        else:
            return "home"
    
    def get_location_recommendations(self, task: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get location recommendations for task"""
        task_type = task.get('type', 'homework')
        best_location = self.get_best_location_for_task(task_type)
        
        recommendations = [
            {
                "location": best_location,
                "reason": "Best productivity history",
                "recommended": True
            }
        ]
        
        # Add alternative locations
        if best_location != "library":
            recommendations.append({
                "location": "library",
                "reason": "Quiet study environment",
                "recommended": False
            })
        
        if best_location != "home":
            recommendations.append({
                "location": "home",
                "reason": "Convenient and comfortable",
                "recommended": False
            })
        
        return recommendations


def main():
    print("Location Context Manager - Ready")


if __name__ == "__main__":
    main()
