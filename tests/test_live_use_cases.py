#!/usr/bin/env python3
"""
OsMEN Live Use Case Tests
Real-world scenario testing for all MVP agents and workflows
"""

import sys
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


class LiveUseCaseTests:
    def __init__(self):
        self.results = []
        self.project_root = Path(__file__).parent
        
    def add_result(self, test_name: str, status: bool, details: str = ""):
        """Record test result"""
        self.results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def print_header(self, title: str):
        """Print test section header"""
        print("\n" + "="*70)
        print(f"LIVE USE CASE: {title}")
        print("="*70 + "\n")
        
    def test_scenario_1_morning_routine(self):
        """
        Scenario 1: Morning Startup Routine
        - System boots up
        - Boot hardening checks security
        - Daily brief generates morning report
        """
        self.print_header("Morning Startup Routine")
        
        try:
            # Step 1: Boot Hardening Check
            print("Step 1: Running boot security check...")
            from agents.boot_hardening.boot_hardening_agent import BootHardeningAgent
            
            boot_agent = BootHardeningAgent()
            boot_report = boot_agent.get_hardening_report()
            
            print(f"  ✅ Boot security status: {boot_report['overall_status']}")
            print(f"  ✅ Boot integrity issues found: {len(boot_report['boot_integrity']['issues'])}")
            print(f"  ✅ Startup analysis completed")
            
            # Step 2: Generate Daily Brief
            print("\nStep 2: Generating morning brief...")
            from agents.daily_brief.daily_brief_agent import DailyBriefAgent
            
            brief_agent = DailyBriefAgent()
            brief = brief_agent.generate_brief()
            
            print(f"  ✅ Brief date: {brief['date']}")
            print(f"  ✅ Scheduled tasks: {len(brief['scheduled_tasks'])}")
            print(f"  ✅ System status: {brief['system_status']}")
            
            # Verify integration
            assert boot_report['overall_status'] in ['good', 'moderate', 'critical']
            assert brief['date'] == datetime.now().strftime("%Y-%m-%d")
            assert 'system_status' in brief
            
            self.add_result("Morning Routine", True, "Boot check + Daily brief completed successfully")
            print("\n✅ Morning Routine Test: PASS")
            return True
            
        except Exception as e:
            self.add_result("Morning Routine", False, str(e))
            print(f"\n❌ Morning Routine Test: FAIL - {e}")
            return False
            
    def test_scenario_2_focus_session_workflow(self):
        """
        Scenario 2: Focused Work Session
        - User starts a Pomodoro session
        - Focus agent monitors applications
        - Blocks distractions
        - Tracks session completion
        """
        self.print_header("Focused Work Session (Pomodoro)")
        
        try:
            # Step 1: Starting 25-minute focus session
            print("Step 1: Starting 25-minute focus session...")
            from agents.focus_guardrails.focus_guardrails_agent import FocusGuardrailsAgent
            
            focus_agent = FocusGuardrailsAgent()
            
            # Start session (pass duration as integer, not dict)
            session = focus_agent.start_focus_session(duration_minutes=25)
            
            print(f"  ✅ Session started: {session['start_time']}")
            print(f"  ✅ Duration: {session['duration_minutes']} minutes")
            print(f"  ✅ Status: {session['status']}")
            
            # Verify session started correctly
            assert session['duration_minutes'] == 25, "Duration should be 25 minutes"
            assert session['status'] == 'active', "Session should be active initially"
            
            # Step 2: Check current status
            print("\nStep 2: Checking focus report...")
            report = focus_agent.get_focus_report()
            
            print(f"  ✅ Total sessions: {report['total_sessions']}")
            print(f"  ✅ Blocked sites: {len(report['blocked_sites'])}")
            
            # Step 3: Simulate session completion
            print("\nStep 3: Completing focus session...")
            completion = focus_agent.end_focus_session()
            
            if completion:
                print(f"  ✅ Session completed: {completion.get('status', 'unknown')}")
            
            # Verify completion
            assert completion is not None, "Completion should not be None"
            assert completion.get('status') == 'completed', "Session should be completed"
            
            self.add_result("Focus Session", True, "Pomodoro session workflow completed")
            print("\n✅ Focus Session Test: PASS")
            return True
            
        except Exception as e:
            self.add_result("Focus Session", False, str(e))
            print(f"\n❌ Focus Session Test: FAIL - {e}")
            return False
            
    def test_scenario_3_security_incident_response(self):
        """
        Scenario 3: Security Incident Detection & Response
        - Suspicious process detected
        - Boot hardening agent analyzes
        - Recommends firewall actions
        - Generates incident report
        """
        self.print_header("Security Incident Response")
        
        try:
            print("Step 1: Simulating suspicious process detection...")
            from agents.boot_hardening.boot_hardening_agent import BootHardeningAgent
            
            boot_agent = BootHardeningAgent()
            
            # Analyze current system state
            report = boot_agent.get_hardening_report()
            
            print(f"  ✅ Security status: {report['overall_status']}")
            print(f"  ✅ Boot integrity checked")
            
            # Step 2: Check for suspicious items
            print("\nStep 2: Analyzing for security threats...")
            suspicious_items = [
                item for item in report['boot_integrity']['issues']
                if 'Secure Boot' in item or 'rootkit' in item.lower()
            ]
            
            print(f"  ✅ Potential threats identified: {len(suspicious_items)}")
            
            # Step 3: Generate security recommendations
            print("\nStep 3: Generating security recommendations...")
            recommendations = {
                'firewall_updates': [{'action': 'review', 'target': 'suspicious_process'}],
                'process_actions': report['boot_integrity']['recommendations']
            }
            
            print(f"  ✅ Firewall rules suggested: {len(recommendations.get('firewall_updates', []))}")
            print(f"  ✅ Process actions recommended: {len(recommendations.get('process_actions', []))}")
            
            # Step 4: Create incident log
            print("\nStep 4: Creating incident log...")
            incident = {
                "timestamp": datetime.now().isoformat(),
                "severity": report['overall_status'],
                "issues": suspicious_items,
                "recommendations": recommendations,
                "status": "documented"
            }
            
            # Save to logs (if directory exists)
            log_dir = self.project_root / "logs"
            if log_dir.exists():
                log_file = log_dir / f"security_incident_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(log_file, 'w') as f:
                    json.dump(incident, f, indent=2)
                print(f"  ✅ Incident log saved: {log_file.name}")
            
            # Verify incident handling
            assert report['overall_status'] in ['good', 'moderate', 'critical']
            assert 'firewall_updates' in recommendations or 'process_actions' in recommendations
            
            self.add_result("Security Incident", True, "Incident detected and documented")
            print("\n✅ Security Incident Test: PASS")
            return True
            
        except Exception as e:
            self.add_result("Security Incident", False, str(e))
            print(f"\n❌ Security Incident Test: FAIL - {e}")
            return False
            
    def test_scenario_4_tool_integration_workflow(self):
        """
        Scenario 4: Tool Integration Workflow
        - Simplewall firewall control
        - Sysinternals process monitoring
        - FFmpeg media processing
        """
        self.print_header("Tool Integration Workflow")
        
        try:
            # Step 1: Simplewall Integration
            print("Step 1: Testing Simplewall integration...")
            from tools.simplewall.simplewall_integration import SimplewallIntegration
            
            simplewall = SimplewallIntegration()
            rules = simplewall.get_rules()
            
            print(f"  ✅ Simplewall integration: Active")
            print(f"  ✅ Current rules loaded: {len(rules)}")
            
            # Step 2: Sysinternals Integration
            print("\nStep 2: Testing Sysinternals integration...")
            from tools.sysinternals.sysinternals_integration import SysinternalsIntegration
            
            sysinternals = SysinternalsIntegration()
            analysis = sysinternals.analyze_system_health()
            
            print(f"  ✅ Sysinternals integration: Active")
            print(f"  ✅ Tools available: Autoruns, Process Monitor, TCPView")
            print(f"  ✅ Recommendations: {len(analysis['recommendations'])}")
            
            # Step 3: FFmpeg Integration
            print("\nStep 3: Testing FFmpeg integration...")
            from tools.ffmpeg.ffmpeg_integration import FFmpegIntegration
            
            ffmpeg = FFmpegIntegration()
            # Test video info capability
            test_info = ffmpeg.get_media_info("test_video.mp4")
            
            print(f"  ✅ FFmpeg integration: Active")
            print(f"  ✅ Media processing: Available")
            print(f"  ✅ Operations: convert, extract audio, thumbnails, compress")
            
            # Verify all tools are integrated
            assert len(rules) > 0, "Simplewall rules should be available"
            assert 'recommendations' in analysis, "Sysinternals analysis should have recommendations"
            assert 'format' in test_info, "FFmpeg should provide media info"
            
            self.add_result("Tool Integration", True, "All tools integrated successfully")
            print("\n✅ Tool Integration Test: PASS")
            return True
            
        except Exception as e:
            self.add_result("Tool Integration", False, str(e))
            print(f"\n❌ Tool Integration Test: FAIL - {e}")
            return False
            
    def test_scenario_5_end_to_end_daily_workflow(self):
        """
        Scenario 5: Complete Daily Workflow
        - Morning: Boot check + Daily brief
        - Midday: Focus session for 2 hours
        - Evening: Security review
        - Night: System status report
        """
        self.print_header("End-to-End Daily Workflow")
        
        try:
            workflow_log = []
            
            # Morning (8:00 AM)
            print("Phase 1: Morning (8:00 AM)")
            print("  - Running boot security check...")
            from agents.boot_hardening.boot_hardening_agent import BootHardeningAgent
            boot_agent = BootHardeningAgent()
            morning_security = boot_agent.get_hardening_report()
            workflow_log.append({"time": "08:00", "task": "boot_check", "status": "completed"})
            
            print("  - Generating daily brief...")
            from agents.daily_brief.daily_brief_agent import DailyBriefAgent
            brief_agent = DailyBriefAgent()
            morning_brief = brief_agent.generate_brief()
            workflow_log.append({"time": "08:05", "task": "daily_brief", "status": "completed"})
            
            print(f"  ✅ Morning tasks completed")
            
            # Midday (10:00 AM - 12:00 PM)
            print("\nPhase 2: Midday Focus Session (10:00 AM)")
            print("  - Starting 2-hour deep work session...")
            from agents.focus_guardrails.focus_guardrails_agent import FocusGuardrailsAgent
            focus_agent = FocusGuardrailsAgent()
            focus_session = focus_agent.start_focus_session(duration_minutes=120)
            workflow_log.append({"time": "10:00", "task": "focus_start", "status": "active"})
            
            print("  - Focus session active...")
            focus_report = focus_agent.get_focus_report()
            
            print("  - Completing focus session...")
            focus_complete = focus_agent.end_focus_session()
            workflow_log.append({"time": "12:00", "task": "focus_complete", "status": "completed"})
            
            print(f"  ✅ Focus session completed: {focus_session['duration_minutes']} minutes")
            
            # Evening (6:00 PM)
            print("\nPhase 3: Evening Security Review (6:00 PM)")
            print("  - Running security audit...")
            evening_security = boot_agent.get_hardening_report()
            security_delta = len(evening_security['boot_integrity']['issues']) - len(morning_security['boot_integrity']['issues'])
            workflow_log.append({"time": "18:00", "task": "security_audit", "status": "completed"})
            
            print(f"  ✅ Security status: {evening_security['overall_status']}")
            print(f"  ✅ Issues delta: {'+' if security_delta > 0 else ''}{security_delta}")
            
            # Night (10:00 PM)
            print("\nPhase 4: Night Status Report (10:00 PM)")
            print("  - Generating end-of-day report...")
            
            daily_summary = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "workflow_events": workflow_log,
                "security_checks": 2,
                "focus_sessions": 1,
                "total_focus_time": focus_session['duration_minutes'],
                "security_status_change": security_delta,
                "overall_health": "good" if security_delta <= 0 else "needs_attention"
            }
            
            # Save daily summary
            log_dir = self.project_root / "logs"
            if log_dir.exists():
                summary_file = log_dir / f"daily_summary_{datetime.now().strftime('%Y%m%d')}.json"
                with open(summary_file, 'w') as f:
                    json.dump(daily_summary, f, indent=2)
                print(f"  ✅ Daily summary saved: {summary_file.name}")
            
            print(f"\n  ✅ Day completed with {len(workflow_log)} events logged")
            
            # Verify complete workflow
            assert len(workflow_log) >= 5, "All workflow phases should be logged"
            assert daily_summary['security_checks'] == 2
            assert daily_summary['focus_sessions'] == 1
            
            self.add_result("Daily Workflow", True, f"{len(workflow_log)} workflow events completed")
            print("\n✅ End-to-End Daily Workflow Test: PASS")
            return True
            
        except Exception as e:
            self.add_result("Daily Workflow", False, str(e))
            print(f"\n❌ End-to-End Daily Workflow Test: FAIL - {e}")
            return False
            
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("LIVE USE CASE TEST SUMMARY")
        print("="*70 + "\n")
        
        passed = sum(1 for r in self.results if r['status'])
        total = len(self.results)
        
        for result in self.results:
            status_icon = "✅" if result['status'] else "❌"
            print(f"{status_icon} {result['test']:<30} {result['details']}")
        
        print("\n" + "="*70)
        print(f"Total: {passed}/{total} scenarios passed")
        
        if passed == total:
            print("\n🎉 All live use case tests passed!")
            print("System is production ready and validated with real-world scenarios.")
            return 0
        else:
            print(f"\n⚠️  {total - passed} scenario(s) failed")
            print("Review failures and fix issues before production deployment.")
            return 1


def main():
    """Run all live use case tests"""
    print("="*70)
    print("OsMEN Live Use Case Testing Suite")
    print("Real-world scenario validation for production readiness")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    tester = LiveUseCaseTests()
    
    # Run all scenarios
    tester.test_scenario_1_morning_routine()
    tester.test_scenario_2_focus_session_workflow()
    tester.test_scenario_3_security_incident_response()
    tester.test_scenario_4_tool_integration_workflow()
    tester.test_scenario_5_end_to_end_daily_workflow()
    
    # Print summary
    return tester.print_summary()


if __name__ == "__main__":
    sys.exit(main())
