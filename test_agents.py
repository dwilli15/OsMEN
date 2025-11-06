#!/usr/bin/env python3
"""
OsMEN Agent Testing Script
Tests all agent implementations
"""

import sys
import json
from datetime import datetime


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
        if end_result.get('status') != 'completed':
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


def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("OsMEN Agent Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    results = []
    
    # Run MVP agent tests
    results.append(("Boot Hardening", test_boot_hardening()))
    results.append(("Daily Brief", test_daily_brief()))
    results.append(("Focus Guardrails", test_focus_guardrails()))
    results.append(("Tool Integrations", test_tool_integrations()))
    
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
