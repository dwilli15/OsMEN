#!/usr/bin/env python3
"""
OsMEN Agent Testing Script
Tests all agent implementations
"""

import sys
import json
from datetime import datetime

from parsers.syllabus.syllabus_parser import SyllabusParser
from scheduling.schedule_optimizer import ScheduleOptimizer


def _sample_parsed_syllabus():
    """Provide representative parsed syllabus data for parser/scheduler tests."""
    return {
        "course_info": {
            "course_code": "CS 401",
            "course_name": "Advanced Systems",
            "instructor": "Dr. Rivera",
            "semester": "Fall",
            "year": 2025,
        },
        "events": [
            {
                "type": "exam",
                "title": "Midterm Exam",
                "date": "2025-10-12",
                "description": "Comprehensive midterm covering units 1-5",
            },
            {
                "type": "lecture",
                "title": "Guest Lecture",
                "date": "2025-09-18",
                "description": "Industry expert session",
            },
        ],
        "assignments": [
            {
                "type": "assignment",
                "title": "Homework 1",
                "due_date": "2025-09-05",
                "description": "Problem set on distributed systems",
            },
            {
                "type": "project",
                "title": "Capstone Proposal",
                "due_date": "2025-09-25",
                "description": "Submit proposal for final project",
            },
        ],
    }


def test_boot_hardening():
    """Test Boot Hardening Agent"""
    print("\n" + "="*50)
    print("Testing Boot Hardening Agent")
    print("="*50)
    
    try:
        from agents.boot_hardening.boot_hardening_agent import BootHardeningAgent
        
        agent = BootHardeningAgent()
        report = agent.get_hardening_report()
        
        # Validate report structure
        required_keys = ['boot_integrity', 'startup_analysis', 'timestamp', 'overall_status']
        for key in required_keys:
            if key not in report:
                raise ValueError(f"Missing required key in report: {key}")
        
        # Validate boot_integrity structure
        if 'issues' not in report['boot_integrity']:
            raise ValueError("Missing 'issues' in boot_integrity")
        
        print("✅ Boot Hardening Agent: PASS")
        print(f"Status: {report['overall_status']}")
        print(f"Issues: {len(report['boot_integrity']['issues'])}")
        
        return True
    except Exception as e:
        print(f"❌ Boot Hardening Agent: FAIL - {e}")
        return False


def test_daily_brief():
    """Test Daily Brief Agent"""
    print("\n" + "="*50)
    print("Testing Daily Brief Agent")
    print("="*50)
    
    try:
        from agents.daily_brief.daily_brief_agent import DailyBriefAgent
        
        agent = DailyBriefAgent()
        brief = agent.generate_brief()
        
        # Validate brief structure
        required_keys = ['date', 'time', 'greeting', 'system_status', 'scheduled_tasks', 
                        'pending_updates', 'resource_analysis', 'recommendations']
        for key in required_keys:
            if key not in brief:
                raise ValueError(f"Missing required key in brief: {key}")
        
        # Validate scheduled_tasks is a list
        if not isinstance(brief['scheduled_tasks'], list):
            raise ValueError("scheduled_tasks should be a list")
        
        print("✅ Daily Brief Agent: PASS")
        print(f"Date: {brief['date']}")
        print(f"Tasks: {len(brief['scheduled_tasks'])}")
        
        return True
    except Exception as e:
        print(f"❌ Daily Brief Agent: FAIL - {e}")
        return False


def test_focus_guardrails():
    """Test Focus Guardrails Agent"""
    print("\n" + "="*50)
    print("Testing Focus Guardrails Agent")
    print("="*50)
    
    try:
        from agents.focus_guardrails.focus_guardrails_agent import FocusGuardrailsAgent
        
        agent = FocusGuardrailsAgent()
        session = agent.start_focus_session(25)
        
        # Validate session structure
        required_keys = ['start_time', 'duration_minutes', 'end_time', 'status']
        for key in required_keys:
            if key not in session:
                raise ValueError(f"Missing required key in session: {key}")
        
        # Validate status is 'active'
        if session['status'] != 'active':
            raise ValueError(f"Expected status 'active', got '{session['status']}'")
        
        # Get focus report
        report = agent.get_focus_report()
        
        # Validate report structure
        report_keys = ['total_sessions', 'completed_sessions', 'active_session', 'blocked_sites', 'timestamp']
        for key in report_keys:
            if key not in report:
                raise ValueError(f"Missing required key in report: {key}")
        
        # End the session
        end_result = agent.end_focus_session()
        
        # Validate end result
        if not end_result or 'status' not in end_result:
            raise ValueError("end_focus_session() returned invalid result")
        if end_result['status'] != 'completed':
            raise ValueError(f"Expected status 'completed' after ending session, got '{end_result.get('status')}'")
        
        print("✅ Focus Guardrails Agent: PASS")
        print(f"Session Status: {end_result['status']}")
        print(f"Duration: {session['duration_minutes']} minutes")
        
        return True
    except Exception as e:
        print(f"❌ Focus Guardrails Agent: FAIL - {e}")
        return False


def test_tool_integrations():
    """Test Tool Integrations"""
    print("\n" + "="*50)
    print("Testing Tool Integrations")
    print("="*50)
    
    results = []
    
    # Test Simplewall Integration
    try:
        from tools.simplewall.simplewall_integration import SimplewallIntegration
        simplewall = SimplewallIntegration()
        rules = simplewall.get_rules()
        
        # Validate rules structure
        if not isinstance(rules, list):
            raise ValueError("get_rules() should return a list")
        
        print("✅ Simplewall Integration: PASS")
        results.append(True)
    except Exception as e:
        print(f"❌ Simplewall Integration: FAIL - {e}")
        results.append(False)
    
    # Test Sysinternals Integration
    try:
        from tools.sysinternals.sysinternals_integration import SysinternalsIntegration
        sysinternals = SysinternalsIntegration()
        analysis = sysinternals.analyze_system_health()
        
        # Validate analysis structure
        if not isinstance(analysis, dict):
            raise ValueError("analyze_system_health() should return a dict")
        if 'autoruns' not in analysis:
            raise ValueError("Missing 'autoruns' in analysis")
        if 'timestamp' not in analysis:
            raise ValueError("Missing 'timestamp' in analysis")
        
        print("✅ Sysinternals Integration: PASS")
        results.append(True)
    except Exception as e:
        print(f"❌ Sysinternals Integration: FAIL - {e}")
        results.append(False)
    
    # Test FFmpeg Integration
    try:
        from tools.ffmpeg.ffmpeg_integration import FFmpegIntegration
        ffmpeg = FFmpegIntegration()
        info = ffmpeg.get_media_info('test.mp4')
        
        # Validate info structure
        if not isinstance(info, dict):
            raise ValueError("get_media_info() should return a dict")
        required_keys = ['file', 'format', 'duration', 'video_codec', 'audio_codec', 'resolution']
        for key in required_keys:
            if key not in info:
                raise ValueError(f"Missing required key in media info: {key}")
        
        print("✅ FFmpeg Integration: PASS")
        results.append(True)
    except Exception as e:
        print(f"❌ FFmpeg Integration: FAIL - {e}")
        results.append(False)
    
    return all(results)


def test_syllabus_parser_normalization_pipeline():
    """Validate parser normalization needed for Alpha A1.3/A1.4 flows."""
    print("\n" + "="*50)
    print("Testing Syllabus Parser Normalization")
    print("="*50)
    
    try:
        parser = SyllabusParser()
        normalized = parser.normalize_data(_sample_parsed_syllabus())
        events = normalized["events"]
        
        assert normalized["metadata"]["total_events"] == 4, "Expected all events to be counted"
        assert events[0]["title"] == "Homework 1", "Events should be chronological"
        
        midterm = next(event for event in events if event["title"] == "Midterm Exam")
        assert midterm["priority"] == "high", "Midterm should be high priority"
        assert midterm["reminder"]["advance_days"] == 7, "High priority reminder lead time mismatch"
        
        print("✅ Syllabus Parser Normalization: PASS")
        print(f"Total Normalized Events: {len(events)}")
        print(f"Top Event: {events[0]['title']} on {events[0]['date']}")
        return True
    except Exception as e:
        print(f"❌ Syllabus Parser Normalization: FAIL - {e}")
        return False


def test_schedule_optimizer_with_normalized_events():
    """Ensure normalized events convert into prioritized study sessions."""
    print("\n" + "="*50)
    print("Testing Schedule Optimizer Integration")
    print("="*50)
    
    try:
        parser = SyllabusParser()
        normalized = parser.normalize_data(_sample_parsed_syllabus())
        
        priority_scores = {"high": 100, "medium": 70, "low": 40}
        tasks = [
            {
                "id": idx,
                "title": event["title"],
                "priority_score": priority_scores.get(event["priority"], 40),
            }
            for idx, event in enumerate(normalized["events"])
        ]
        
        optimizer = ScheduleOptimizer()
        start_date = datetime(2025, 9, 1)
        schedule = optimizer.generate_schedule(tasks, start_date, start_date)
        
        assert schedule, "Schedule should not be empty"
        assert schedule[0]["task_title"] == "Midterm Exam", "Highest priority task should be scheduled first"
        
        buffered = optimizer.add_buffer_time(schedule)
        assert any(item["type"] == "buffer" for item in buffered[1:]), "Buffer blocks should be injected between sessions"
        
        print("✅ Schedule Optimizer Integration: PASS")
        print(f"Scheduled Blocks: {len(schedule)} | Buffered Blocks: {len(buffered)}")
        return True
    except Exception as e:
        print(f"❌ Schedule Optimizer Integration: FAIL - {e}")
        return False


def test_personal_assistant():
    """Test Personal Assistant Agent"""
    print("\n" + "="*50)
    print("Testing Personal Assistant Agent")
    print("="*50)
    
    try:
        from agents.personal_assistant.personal_assistant_agent import PersonalAssistantAgent
        
        agent = PersonalAssistantAgent()
        
        # Test task creation
        task = agent.create_task("Test task", priority="high")
        if "id" not in task or "title" not in task:
            raise ValueError("Task creation failed")
        
        # Test reminder setting
        reminder = agent.set_reminder("Test reminder", datetime.now().isoformat())
        if "id" not in reminder:
            raise ValueError("Reminder creation failed")
        
        # Generate report
        report = agent.generate_assistant_report()
        required_keys = ['timestamp', 'overall_status', 'statistics']
        for key in required_keys:
            if key not in report:
                raise ValueError(f"Missing required key in report: {key}")
        
        print("✅ Personal Assistant Agent: PASS")
        print(f"Status: {report['overall_status']}")
        print(f"Tasks: {report['statistics']['total_tasks']}")
        
        return True
    except Exception as e:
        print(f"❌ Personal Assistant Agent: FAIL - {e}")
        return False


def test_content_creator():
    """Test Content Creator Agent"""
    print("\n" + "="*50)
    print("Testing Content Creator Agent")
    print("="*50)
    
    try:
        from agents.content_creator.content_creator_agent import ContentCreatorAgent
        
        agent = ContentCreatorAgent()
        
        # Test image generation
        image = agent.generate_image("Test prompt", style="realistic")
        if "id" not in image or "type" not in image:
            raise ValueError("Image generation failed")
        
        # Generate report
        report = agent.generate_creator_report()
        required_keys = ['timestamp', 'overall_status', 'statistics']
        for key in required_keys:
            if key not in report:
                raise ValueError(f"Missing required key in report: {key}")
        
        print("✅ Content Creator Agent: PASS")
        print(f"Status: {report['overall_status']}")
        print(f"Content Created: {report['statistics']['total_content_created']}")
        
        return True
    except Exception as e:
        print(f"❌ Content Creator Agent: FAIL - {e}")
        return False


def test_email_manager():
    """Test Email Manager Agent"""
    print("\n" + "="*50)
    print("Testing Email Manager Agent")
    print("="*50)
    
    try:
        from agents.email_manager.email_manager_agent import EmailManagerAgent
        
        agent = EmailManagerAgent()
        
        # Test contact addition
        contact = agent.add_contact("Test User", "test@example.com")
        if "id" not in contact or "email" not in contact:
            raise ValueError("Contact creation failed")
        
        # Generate report
        report = agent.generate_email_report()
        required_keys = ['timestamp', 'overall_status', 'statistics']
        for key in required_keys:
            if key not in report:
                raise ValueError(f"Missing required key in report: {key}")
        
        print("✅ Email Manager Agent: PASS")
        print(f"Status: {report['overall_status']}")
        print(f"Contacts: {report['statistics']['total_contacts']}")
        
        return True
    except Exception as e:
        print(f"❌ Email Manager Agent: FAIL - {e}")
        return False


def test_live_caption():
    """Test Live Caption Agent"""
    print("\n" + "="*50)
    print("Testing Live Caption Agent")
    print("="*50)
    
    try:
        from agents.live_caption.live_caption_agent import LiveCaptionAgent
        
        agent = LiveCaptionAgent()
        
        # Test session start
        session = agent.start_caption_session("test-meeting", "Test Meeting")
        if "id" not in session or "status" not in session:
            raise ValueError("Session start failed")
        
        # Generate report
        report = agent.generate_caption_report()
        required_keys = ['timestamp', 'overall_status', 'statistics']
        for key in required_keys:
            if key not in report:
                raise ValueError(f"Missing required key in report: {key}")
        
        print("✅ Live Caption Agent: PASS")
        print(f"Status: {report['overall_status']}")
        print(f"Sessions: {report['statistics']['total_sessions']}")
        
        return True
    except Exception as e:
        print(f"❌ Live Caption Agent: FAIL - {e}")
        return False


def test_audiobook_creator():
    """Test Audiobook Creator Agent"""
    print("\n" + "="*50)
    print("Testing Audiobook Creator Agent")
    print("="*50)
    
    try:
        from agents.audiobook_creator.audiobook_creator_agent import AudiobookCreatorAgent
        
        agent = AudiobookCreatorAgent()
        
        # Test voice profile creation
        profile = agent.create_voice_profile("Test Voice", ["/sample.wav"])
        if "id" not in profile or "name" not in profile:
            raise ValueError("Voice profile creation failed")
        
        # Generate report
        report = agent.generate_audiobook_report()
        required_keys = ['timestamp', 'overall_status', 'statistics']
        for key in required_keys:
            if key not in report:
                raise ValueError(f"Missing required key in report: {key}")
        
        print("✅ Audiobook Creator Agent: PASS")
        print(f"Status: {report['overall_status']}")
        print(f"Voice Profiles: {report['statistics']['voice_profiles']}")
        
        return True
    except Exception as e:
        print(f"❌ Audiobook Creator Agent: FAIL - {e}")
        return False


def test_podcast_creator():
    """Test Podcast Creator Agent"""
    print("\n" + "="*50)
    print("Testing Podcast Creator Agent")
    print("="*50)
    
    try:
        from agents.podcast_creator.podcast_creator_agent import PodcastCreatorAgent
        
        agent = PodcastCreatorAgent()
        
        # Test series creation
        series = agent.create_podcast_series("Test Series", "Test Description")
        if "id" not in series or "title" not in series:
            raise ValueError("Series creation failed")
        
        # Generate report
        report = agent.generate_podcast_report()
        required_keys = ['timestamp', 'overall_status', 'statistics']
        for key in required_keys:
            if key not in report:
                raise ValueError(f"Missing required key in report: {key}")
        
        print("✅ Podcast Creator Agent: PASS")
        print(f"Status: {report['overall_status']}")
        print(f"Series: {report['statistics']['total_series']}")
        
        return True
    except Exception as e:
        print(f"❌ Podcast Creator Agent: FAIL - {e}")
        return False


def test_os_optimizer():
    """Test OS Optimizer Agent"""
    print("\n" + "="*50)
    print("Testing OS Optimizer Agent")
    print("="*50)
    
    try:
        from agents.os_optimizer.os_optimizer_agent import OSOptimizerAgent
        
        agent = OSOptimizerAgent()
        
        # Test performance analysis
        analysis = agent.analyze_system_performance()
        if "performance_score" not in analysis:
            raise ValueError("Performance analysis failed")
        
        # Generate report
        report = agent.generate_optimizer_report()
        required_keys = ['timestamp', 'overall_status', 'statistics']
        for key in required_keys:
            if key not in report:
                raise ValueError(f"Missing required key in report: {key}")
        
        print("✅ OS Optimizer Agent: PASS")
        print(f"Status: {report['overall_status']}")
        print(f"Optimizations: {report['statistics']['total_optimizations']}")
        
        return True
    except Exception as e:
        print(f"❌ OS Optimizer Agent: FAIL - {e}")
        return False


def test_security_ops():
    """Test Security Operations Agent"""
    print("\n" + "="*50)
    print("Testing Security Operations Agent")
    print("="*50)
    
    try:
        from agents.security_ops.security_ops_agent import SecurityOpsAgent
        
        agent = SecurityOpsAgent()
        
        # Test security scan
        scan = agent.run_security_scan("port", ["localhost"])
        if "id" not in scan or "type" not in scan:
            raise ValueError("Security scan failed")
        
        # Generate report
        report = agent.generate_security_report()
        required_keys = ['timestamp', 'overall_status', 'statistics']
        for key in required_keys:
            if key not in report:
                raise ValueError(f"Missing required key in report: {key}")
        
        print("✅ Security Operations Agent: PASS")
        print(f"Status: {report['overall_status']}")
        print(f"Scans: {report['statistics']['total_scans']}")
        
        return True
    except Exception as e:
        print(f"❌ Security Operations Agent: FAIL - {e}")
        return False


def test_cli_integrations():
    """Test Codex and Copilot CLI Integrations"""
    print("\n" + "="*50)
    print("Testing CLI Integrations")
    print("="*50)
    
    results = []
    
    # Test Codex CLI Integration
    try:
        from tools.codex_cli.codex_integration import CodexCLIIntegration
        codex = CodexCLIIntegration()
        status = codex.get_integration_status()
        
        if "integration" not in status or "capabilities" not in status:
            raise ValueError("Invalid status structure")
        
        print("✅ Codex CLI Integration: PASS")
        results.append(True)
    except Exception as e:
        print(f"❌ Codex CLI Integration: FAIL - {e}")
        results.append(False)
    
    # Test Copilot CLI Integration
    try:
        from tools.copilot_cli.copilot_integration import CopilotCLIIntegration
        copilot = CopilotCLIIntegration()
        status = copilot.get_integration_status()
        
        if "integration" not in status or "capabilities" not in status:
            raise ValueError("Invalid status structure")
        
        print("✅ Copilot CLI Integration: PASS")
        results.append(True)
    except Exception as e:
        print(f"❌ Copilot CLI Integration: FAIL - {e}")
        results.append(False)
    
    return all(results)


def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("OsMEN Agent Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    results = []
    
    # Run original MVP agent tests
    results.append(("Boot Hardening", test_boot_hardening()))
    results.append(("Daily Brief", test_daily_brief()))
    results.append(("Focus Guardrails", test_focus_guardrails()))
    results.append(("Tool Integrations", test_tool_integrations()))
    results.append(("Syllabus Parser Normalization", test_syllabus_parser_normalization_pipeline()))
    results.append(("Schedule Optimizer Integration", test_schedule_optimizer_with_normalized_events()))
    
    # Run new agent tests
    results.append(("Personal Assistant", test_personal_assistant()))
    results.append(("Content Creator", test_content_creator()))
    results.append(("Email Manager", test_email_manager()))
    results.append(("Live Caption", test_live_caption()))
    results.append(("Audiobook Creator", test_audiobook_creator()))
    results.append(("Podcast Creator", test_podcast_creator()))
    results.append(("OS Optimizer", test_os_optimizer()))
    results.append(("Security Operations", test_security_ops()))
    results.append(("CLI Integrations", test_cli_integrations()))
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:25} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
