#!/usr/bin/env python3
"""
Energy Level Correlation

Correlates energy levels with productivity and task completion.
Part of v1.6.0 - Adaptive Reminders & Health Integration.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
from pathlib import Path


class EnergyLevelCorrelator:
    """Correlate energy levels with task performance"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.correlation_path = self.repo_root / ".copilot" / "energy_correlation.json"
        self.correlation_data = self._load_correlation_data()
    
    def _load_correlation_data(self) -> Dict[str, Any]:
        """Load correlation data"""
        if self.correlation_path.exists():
            with open(self.correlation_path, 'r') as f:
                return json.load(f)
        
        return {
            "energy_by_time": {
                "morning": [],
                "afternoon": [],
                "evening": [],
                "night": []
            },
            "productivity_by_energy": [],
            "optimal_times": {}
        }
    
    def _save_correlation_data(self):
        """Save correlation data"""
        self.correlation_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.correlation_path, 'w') as f:
            json.dump(self.correlation_data, f, indent=2)
    
    def record_energy_productivity(self, time_of_day: str, energy_level: int,
                                   tasks_completed: int, quality_score: float):
        """Record energy and productivity correlation"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "time_of_day": time_of_day,
            "energy_level": energy_level,
            "tasks_completed": tasks_completed,
            "quality_score": quality_score
        }
        
        self.correlation_data["productivity_by_energy"].append(record)
        self._save_correlation_data()
    
    def get_optimal_time_for_task_type(self, task_type: str) -> str:
        """Get optimal time of day for task type based on energy correlation"""
        # Check if we have learned optimal times
        optimal = self.correlation_data.get("optimal_times", {}).get(task_type)
        if optimal:
            return optimal
        
        # Default recommendations based on task type
        defaults = {
            "exam": "morning",  # High focus needed
            "project": "morning",  # Creative work
            "homework": "afternoon",  # Standard work
            "reading": "evening",  # Lower intensity
            "review": "evening"  # Lighter work
        }
        
        return defaults.get(task_type, "afternoon")
    
    def analyze_energy_patterns(self) -> Dict[str, Any]:
        """Analyze energy level patterns"""
        records = self.correlation_data.get("productivity_by_energy", [])
        
        if len(records) < 5:
            return {
                "status": "insufficient_data",
                "message": "Need more data to analyze patterns"
            }
        
        # Calculate average energy by time of day
        time_averages = {}
        time_counts = {}
        
        for record in records[-30:]:  # Last 30 records
            time = record.get("time_of_day", "afternoon")
            energy = record.get("energy_level", 5)
            
            time_averages[time] = time_averages.get(time, 0) + energy
            time_counts[time] = time_counts.get(time, 0) + 1
        
        for time in time_averages:
            time_averages[time] = time_averages[time] / time_counts[time]
        
        # Find peak energy time
        peak_time = max(time_averages, key=time_averages.get) if time_averages else "morning"
        
        return {
            "status": "analyzed",
            "peak_energy_time": peak_time,
            "energy_by_time": {k: round(v, 1) for k, v in time_averages.items()},
            "total_records": len(records)
        }


def main():
    print("Energy Level Correlator - Ready")


if __name__ == "__main__":
    main()
