#!/usr/bin/env python3
"""
Health-Based Schedule Adjuster

Adjusts schedules based on health data and energy patterns.
Part of v1.6.0 - Adaptive Reminders & Health Integration.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from health_integration.health_data import HealthDataIntegrator, SleepPatternAnalyzer
from health_integration.energy_correlation import EnergyLevelCorrelator
from health_integration.location_context import LocationContextManager


class HealthBasedScheduleAdjuster:
    """Adjust schedules based on comprehensive health data"""
    
    def __init__(self):
        self.health = HealthDataIntegrator()
        self.sleep_analyzer = SleepPatternAnalyzer(self.health)
        self.energy_correlator = EnergyLevelCorrelator()
        self.location_manager = LocationContextManager()
    
    def adjust_schedule_for_health(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Adjust schedule based on health data
        
        Args:
            schedule: List of scheduled tasks
        
        Returns:
            Adjusted schedule
        """
        adjusted_schedule = []
        
        # Get health insights
        sleep_analysis = self.sleep_analyzer.analyze_sleep_impact()
        energy_patterns = self.energy_correlator.analyze_energy_patterns()
        
        for task in schedule:
            adjusted_task = task.copy()
            
            # Adjust based on sleep quality
            if sleep_analysis["productivity_impact"] == "negative":
                adjusted_task["adjustment_reason"] = "Low sleep - task rescheduled"
                adjusted_task = self._adjust_for_low_sleep(adjusted_task)
            
            # Adjust based on energy patterns
            if energy_patterns.get("status") == "analyzed":
                optimal_time = self._get_optimal_time_for_task(
                    adjusted_task,
                    energy_patterns
                )
                if optimal_time:
                    adjusted_task["recommended_time"] = optimal_time
            
            # Adjust based on location
            location_recs = self.location_manager.get_location_recommendations(adjusted_task)
            if location_recs:
                adjusted_task["recommended_location"] = location_recs[0]["location"]
            
            adjusted_schedule.append(adjusted_task)
        
        return adjusted_schedule
    
    def _adjust_for_low_sleep(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust task for low sleep conditions"""
        task_type = task.get('type', 'homework')
        
        # High-intensity tasks should be rescheduled
        if task_type in ['exam', 'project']:
            # Suggest rescheduling to when sleep improves
            task["health_recommendation"] = "Reschedule to well-rested day"
            task["priority_adjustment"] = "defer"
        else:
            # Lower-intensity tasks can proceed with breaks
            task["health_recommendation"] = "Add extra breaks"
            task["break_frequency_minutes"] = 30  # Break every 30 min
        
        return task
    
    def _get_optimal_time_for_task(self, task: Dict[str, Any],
                                   energy_patterns: Dict[str, Any]) -> Optional[str]:
        """Get optimal time based on energy patterns"""
        task_type = task.get('type', 'homework')
        peak_time = energy_patterns.get("peak_energy_time")
        
        # High-intensity tasks at peak energy
        if task_type in ['exam', 'project'] and peak_time:
            return peak_time
        
        # Use energy correlator
        return self.energy_correlator.get_optimal_time_for_task_type(task_type)
    
    def get_health_status_summary(self) -> Dict[str, Any]:
        """Get overall health status summary"""
        sleep_analysis = self.sleep_analyzer.analyze_sleep_impact()
        energy_patterns = self.energy_correlator.analyze_energy_patterns()
        
        return {
            "sleep": sleep_analysis,
            "energy": energy_patterns,
            "overall_status": self._calculate_overall_status(sleep_analysis, energy_patterns),
            "recommendations": self._generate_recommendations(sleep_analysis, energy_patterns)
        }
    
    def _calculate_overall_status(self, sleep_analysis: Dict[str, Any],
                                 energy_patterns: Dict[str, Any]) -> str:
        """Calculate overall health status"""
        sleep_status = sleep_analysis.get("sleep_status", "adequate")
        
        if sleep_status == "optimal":
            return "excellent"
        elif sleep_status == "adequate":
            return "good"
        else:
            return "needs_attention"
    
    def _generate_recommendations(self, sleep_analysis: Dict[str, Any],
                                 energy_patterns: Dict[str, Any]) -> List[str]:
        """Generate health-based recommendations"""
        recommendations = []
        
        # Sleep recommendations
        recommendations.extend(sleep_analysis.get("recommendations", []))
        
        # Energy recommendations
        if energy_patterns.get("status") == "analyzed":
            peak_time = energy_patterns.get("peak_energy_time")
            recommendations.append(
                f"Schedule important tasks during {peak_time} (your peak energy time)"
            )
        
        # General recommendations
        if not recommendations:
            recommendations.append("Continue tracking health data for personalized insights")
        
        return recommendations
    
    def should_schedule_task_now(self, task: Dict[str, Any]) -> bool:
        """Determine if task should be scheduled now based on health"""
        sleep_analysis = self.sleep_analyzer.analyze_sleep_impact()
        
        # Don't schedule high-intensity tasks when sleep-deprived
        if sleep_analysis["productivity_impact"] == "negative":
            if task.get('type') in ['exam', 'project']:
                return False
        
        return True


def main():
    print("Health-Based Schedule Adjuster - Ready")


if __name__ == "__main__":
    main()
