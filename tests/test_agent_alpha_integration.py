#!/usr/bin/env python3
"""
Integration Tests for Agent Alpha Features

Tests the complete integration of:
- Calendar OAuth and management
- Syllabus upload and parsing
- Event preview and editing
- Schedule generation and optimization
- Reminder creation and management
- Health-based schedule adjustment
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("\n" + "=" * 70)
print("Agent Alpha Integration Test Suite")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)


def test_calendar_manager():
    """Test calendar manager integration"""
    print("\n" + "=" * 70)
    print("Testing Calendar Manager")
    print("=" * 70)
    
    try:
        sys.path.insert(0, str(project_root / "integrations" / "calendar"))
        from calendar_manager import CalendarManager
        
        manager = CalendarManager()
        status = manager.get_status()
        
        # Validate status structure
        required_keys = ['configured_providers', 'primary_provider', 'google_available', 'outlook_available']
        for key in required_keys:
            if key not in status:
                raise ValueError(f"Missing key in status: {key}")
        
        print(f"✅ Calendar Manager: PASS")
        print(f"Google API Available: {status['google_available']}")
        print(f"Outlook API Available: {status['outlook_available']}")
        print(f"Configured Providers: {status['configured_providers']}")
        return True
    
    except Exception as e:
        print(f"❌ Calendar Manager: FAIL - {e}")
        return False


def test_syllabus_parser():
    """Test syllabus parser"""
    print("\n" + "=" * 70)
    print("Testing Syllabus Parser")
    print("=" * 70)
    
    try:
        # Import from parsers.syllabus package
        from parsers.syllabus.syllabus_parser import SyllabusParser
        
        parser = SyllabusParser()
        
        # Test with simulated data
        test_data = {
            "course_info": {
                "course_code": "CS 101",
                "course_name": "Introduction to Computer Science",
                "instructor": "Dr. Smith",
                "semester": "Fall",
                "year": 2024
            },
            "events": [
                {
                    "type": "exam",
                    "title": "Midterm Exam",
                    "date": "2024-10-15",
                    "description": "Covers chapters 1-5"
                }
            ],
            "assignments": [
                {
                    "type": "assignment",
                    "title": "Homework 1",
                    "due_date": "2024-09-30",
                    "description": "Complete exercises"
                }
            ]
        }
        
        normalized = parser.normalize_data(test_data)
        
        # Validate structure
        required_keys = ['course', 'events', 'metadata']
        for key in required_keys:
            if key not in normalized:
                raise ValueError(f"Missing key in normalized data: {key}")
        
        if len(normalized['events']) != 2:
            raise ValueError(f"Expected 2 events, got {len(normalized['events'])}")
        
        print(f"✅ Syllabus Parser: PASS")
        print(f"Events parsed: {len(normalized['events'])}")
        print(f"Course: {normalized['course']['name']}")
        return True
    
    except Exception as e:
        print(f"❌ Syllabus Parser: FAIL - {e}")
        return False


def test_schedule_optimizer():
    """Test schedule optimizer"""
    print("\n" + "=" * 70)
    print("Testing Schedule Optimizer")
    print("=" * 70)
    
    try:
        from scheduling.schedule_optimizer import ScheduleOptimizer
        from scheduling.priority_ranker import PriorityRanker
        
        optimizer = ScheduleOptimizer()
        ranker = PriorityRanker()
        
        # Test with simulated tasks
        tasks = [
            {
                "id": "1",
                "title": "Important Exam",
                "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "type": "exam",
                "priority": "high",
                "priority_score": 90
            },
            {
                "id": "2",
                "title": "Homework Assignment",
                "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
                "type": "assignment",
                "priority": "medium",
                "priority_score": 60
            }
        ]
        
        # Generate schedule using the actual method
        start_date = datetime.now()
        end_date = datetime.now() + timedelta(days=7)
        schedule = optimizer.generate_schedule(tasks, start_date, end_date)
        
        if not isinstance(schedule, list):
            raise ValueError("Schedule should be a list")
        
        # Add buffer time
        buffered = optimizer.add_buffer_time(schedule)
        
        if not isinstance(buffered, list):
            raise ValueError("Buffered schedule should be a list")
        
        print(f"✅ Schedule Optimizer: PASS")
        print(f"Sessions generated: {len(schedule)}")
        print(f"With buffers: {len(buffered)}")
        return True
    
    except Exception as e:
        print(f"❌ Schedule Optimizer: FAIL - {e}")
        return False


def test_adaptive_reminders():
    """Test adaptive reminder system"""
    print("\n" + "=" * 70)
    print("Testing Adaptive Reminder System")
    print("=" * 70)
    
    try:
        sys.path.insert(0, str(project_root / "reminders"))
        from adaptive_reminders import AdaptiveReminderSystem
        
        reminder_system = AdaptiveReminderSystem()
        
        # Test reminder creation
        test_task = {
            "id": "test_task_1",
            "title": "Test Assignment",
            "date": (datetime.now() + timedelta(days=5)).isoformat(),
            "type": "assignment",
            "priority": "medium"
        }
        
        reminder = reminder_system.create_reminder(test_task)
        
        # Validate reminder structure
        required_keys = ['id', 'task_id', 'reminder_time', 'status', 'escalation_level']
        for key in required_keys:
            if key not in reminder:
                raise ValueError(f"Missing key in reminder: {key}")
        
        # Test snooze functionality
        success = reminder_system.snooze_reminder(reminder['id'], 24)
        if not success:
            raise ValueError("Snooze failed")
        
        print(f"✅ Adaptive Reminders: PASS")
        print(f"Reminder created: {reminder['id']}")
        print(f"Escalation level: {reminder['escalation_level']}")
        return True
    
    except Exception as e:
        print(f"❌ Adaptive Reminders: FAIL - {e}")
        return False


def test_health_integration():
    """Test health-based schedule adjustment"""
    print("\n" + "=" * 70)
    print("Testing Health Integration")
    print("=" * 70)
    
    try:
        sys.path.insert(0, str(project_root / "health_integration"))
        from schedule_adjuster import HealthBasedScheduleAdjuster
        
        adjuster = HealthBasedScheduleAdjuster()
        
        # Test with simulated schedule
        test_schedule = [
            {
                "id": "1",
                "title": "Study Session",
                "date": datetime.now().isoformat(),
                "type": "exam",
                "priority": "high"
            }
        ]
        
        adjusted_schedule = adjuster.adjust_schedule_for_health(test_schedule)
        
        if not isinstance(adjusted_schedule, list):
            raise ValueError("Adjusted schedule should be a list")
        
        if len(adjusted_schedule) == 0:
            raise ValueError("Adjusted schedule is empty")
        
        # Get health status
        status = adjuster.get_health_status_summary()
        
        required_keys = ['sleep', 'energy', 'overall_status', 'recommendations']
        for key in required_keys:
            if key not in status:
                raise ValueError(f"Missing key in health status: {key}")
        
        print(f"✅ Health Integration: PASS")
        print(f"Overall status: {status['overall_status']}")
        print(f"Recommendations: {len(status['recommendations'])}")
        return True
    
    except Exception as e:
        print(f"❌ Health Integration: FAIL - {e}")
        return False


def test_web_integration():
    """Test web dashboard integration (structure validation)"""
    print("\n" + "=" * 70)
    print("Testing Web Dashboard Integration")
    print("=" * 70)
    
    try:
        # Verify web templates exist
        web_dir = project_root / "web"
        templates_dir = web_dir / "templates"
        
        required_templates = [
            'base.html',
            'dashboard.html',
            'calendar_setup.html',
            'event_preview.html',
            'tasks.html',
            'health.html'
        ]
        
        for template in required_templates:
            template_path = templates_dir / template
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template}")
        
        # Verify main.py exists and has required endpoints
        main_py = web_dir / "main.py"
        if not main_py.exists():
            raise FileNotFoundError("web/main.py not found")
        
        with open(main_py, 'r') as f:
            content = f.read()
            
            required_endpoints = [
                '/calendar',
                '/api/calendar/google/oauth',
                '/api/calendar/outlook/oauth',
                '/api/syllabus/upload',
                '/api/schedule/generate',
                '/api/reminders/create',
                '/api/health/status'
            ]
            
            for endpoint in required_endpoints:
                if endpoint not in content:
                    raise ValueError(f"Endpoint not found in main.py: {endpoint}")
        
        print(f"✅ Web Integration: PASS")
        print(f"Templates verified: {len(required_templates)}")
        print(f"Endpoints verified: {len(required_endpoints)}")
        return True
    
    except Exception as e:
        print(f"❌ Web Integration: FAIL - {e}")
        return False


def run_all_tests():
    """Run all integration tests"""
    tests = [
        ("Calendar Manager", test_calendar_manager),
        ("Syllabus Parser", test_syllabus_parser),
        ("Schedule Optimizer", test_schedule_optimizer),
        ("Adaptive Reminders", test_adaptive_reminders),
        ("Health Integration", test_health_integration),
        ("Web Integration", test_web_integration)
    ]
    
    results = []
    for name, test_func in tests:
        results.append((name, test_func()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("Integration Test Summary")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<30} {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All integration tests passed!")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
