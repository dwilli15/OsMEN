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
        report = agent.get_focus_report()
        agent.end_focus_session()
        
        print("✅ Focus Guardrails Agent: PASS")
        print(f"Session Status: {session['status']}")
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
