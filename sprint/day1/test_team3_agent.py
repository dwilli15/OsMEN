#!/usr/bin/env python3
"""
Tests for Team 3 Agent and Orchestration Agent
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

# Also add sprint directory to allow absolute imports
sprint_dir = Path(__file__).parent.parent
sys.path.insert(0, str(sprint_dir))


def test_orchestration_agent():
    """Test Orchestration Agent"""
    print("\n" + "="*60)
    print("Testing Orchestration Agent")
    print("="*60)
    
    try:
        from day1.orchestration.orchestration_agent import OrchestrationAgent, TeamStatus, TaskPriority
        
        agent = OrchestrationAgent()
        
        # Test message reception
        response = agent.receive_message('team3', 'Test message', TaskPriority.MEDIUM)
        assert response['acknowledged'] == True
        assert response['team_id'] == 'team3'
        
        # Test status update
        status = agent.update_team_status('team3', TeamStatus.IN_PROGRESS, 50)
        assert status['team_id'] == 'team3'
        assert status['progress'] == 50
        
        # Test blocker reporting
        blocker = agent.report_blocker('team3', 'Test blocker', 'medium')
        assert blocker['acknowledged'] == True
        assert 'blocker_id' in blocker
        
        # Test secret request
        secret_req = agent.request_secret('team3', 'TEST_SECRET', 'Testing')
        assert 'request_id' in secret_req
        assert secret_req['status'] == 'pending'
        
        # Test PR request
        pr_req = agent.request_pull_request('team3', 'test-branch', 'Test PR')
        assert 'request_id' in pr_req
        assert pr_req['branch_name'] == 'test-branch'
        
        # Test overall status
        overall = agent.get_overall_status()
        assert 'teams' in overall
        assert 'team3' in overall['teams']
        
        # Test status report
        report = agent.generate_status_report()
        assert 'ORCHESTRATION STATUS REPORT' in report
        
        print("✅ Orchestration Agent: PASS")
        print(f"  - Message handling: ✓")
        print(f"  - Status updates: ✓")
        print(f"  - Blocker tracking: ✓")
        print(f"  - Secret requests: ✓")
        print(f"  - PR requests: ✓")
        print(f"  - Status reporting: ✓")
        
        return True
    except Exception as e:
        print(f"❌ Orchestration Agent: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_team3_agent():
    """Test Team 3 Agent"""
    print("\n" + "="*60)
    print("Testing Team 3 Agent")
    print("="*60)
    
    try:
        from day1.orchestration.orchestration_agent import OrchestrationAgent
        from day1.team3_api_clients.team3_agent import Team3Agent, TaskStatus
        
        # Create orchestration agent
        orchestration = OrchestrationAgent()
        
        # Create Team 3 agent
        agent = Team3Agent(orchestration_agent=orchestration)
        
        # Verify initialization
        assert agent.team_id == 'team3'
        assert agent.team_name == 'API Clients'
        assert len(agent.tasks) == 15  # Should have 15 tasks
        
        # Test status retrieval
        status = agent.get_status()
        assert 'team_id' in status
        assert status['team_id'] == 'team3'
        assert status['total_tasks'] == 15
        
        # Test status report generation
        report = agent.generate_status_report()
        assert 'TEAM 3' in report
        assert 'API Clients' in report
        
        # Test individual task execution (non-blocking task)
        task = next(t for t in agent.tasks if t['id'] == 'task_11')  # Retry decorator
        result = agent.execute_task(task)
        assert result == True
        assert task['status'] == TaskStatus.COMPLETED
        
        print("✅ Team 3 Agent: PASS")
        print(f"  - Initialization: ✓")
        print(f"  - Task tracking: ✓ ({len(agent.tasks)} tasks)")
        print(f"  - Status reporting: ✓")
        print(f"  - Task execution: ✓")
        print(f"  - Orchestration integration: ✓")
        
        return True
    except Exception as e:
        print(f"❌ Team 3 Agent: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_integration():
    """Test integration between agents"""
    print("\n" + "="*60)
    print("Testing Agent Integration")
    print("="*60)
    
    try:
        from day1.orchestration.orchestration_agent import OrchestrationAgent, TeamStatus
        from day1.team3_api_clients.team3_agent import Team3Agent
        
        # Create agents
        orchestration = OrchestrationAgent()
        team3 = Team3Agent(orchestration_agent=orchestration)
        
        # Verify team3 can communicate with orchestration
        initial_msg_count = len(orchestration.messages)
        team3._notify_orchestration("Integration test message")
        assert len(orchestration.messages) > initial_msg_count
        
        # Verify status updates propagate
        team3._update_progress()
        overall_status = orchestration.get_overall_status()
        assert 'team3' in overall_status['teams']
        
        # Test secret request flow
        initial_secret_count = len(orchestration.secret_requests)
        team3._request_secret('TEST_KEY', 'Integration test')
        assert len(orchestration.secret_requests) > initial_secret_count
        
        print("✅ Agent Integration: PASS")
        print(f"  - Message passing: ✓")
        print(f"  - Status synchronization: ✓")
        print(f"  - Secret request flow: ✓")
        
        return True
    except Exception as e:
        print(f"❌ Agent Integration: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TEAM 3 AGENT TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Orchestration Agent", test_orchestration_agent()))
    results.append(("Team 3 Agent", test_team3_agent()))
    results.append(("Agent Integration", test_agent_integration()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
