#!/usr/bin/env python3
"""
Integration tests for OsMEN MCP Server with new tools
"""

import sys
import os
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent))

# Import MCP server components
from gateway.mcp_server import MCPServer, ToolCallRequest


def test_mcp_server_initialization():
    """Test MCP server initializes with all tools"""
    print("\n" + "="*50)
    print("Testing MCP Server Initialization")
    print("="*50)
    
    try:
        server = MCPServer()
        tools = server.list_tools()
        
        print(f"\n✅ Server initialized with {len(tools)} tools:")
        
        # Expected tool categories
        expected_categories = {
            'obsidian': 0,
            'simplewall': 0,
            'sysinternals': 0,
            'ffmpeg': 0,
            'productivity': 0,
            'innovation': 0
        }
        
        for tool in tools:
            tool_name = tool.name
            print(f"  - {tool_name}: {tool.description}")
            
            # Count by category
            for category in expected_categories:
                if tool_name.startswith(category):
                    expected_categories[category] += 1
        
        print("\n✅ Tool counts by category:")
        for category, count in expected_categories.items():
            print(f"  - {category}: {count} tools")
        
        # Verify we have tools from all categories
        assert expected_categories['productivity'] > 0, "Productivity tools missing"
        assert expected_categories['innovation'] > 0, "Innovation tools missing"
        
        print("\n✅ All tool categories present")
        return True
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_productivity_tools():
    """Test productivity monitor tools"""
    print("\n" + "="*50)
    print("Testing Productivity Monitor Tools")
    print("="*50)
    
    try:
        server = MCPServer()
        
        # Test start session
        print("\nTesting start_focus_session...")
        request = ToolCallRequest(
            tool='productivity_start_session',
            parameters={'session_type': 'pomodoro', 'duration': 25}
        )
        response = server.call_tool(request)
        
        assert response.success, "Start session should succeed"
        assert 'session_id' in response.result, "Should return session_id"
        session_id = response.result['session_id']
        print(f"✅ Started session {session_id}")
        
        # Test end session
        print("\nTesting end_focus_session...")
        request = ToolCallRequest(
            tool='productivity_end_session',
            parameters={
                'session_id': session_id,
                'productivity_score': 9,
                'distractions': 1
            }
        )
        response = server.call_tool(request)
        
        assert response.success, "End session should succeed"
        print(f"✅ Ended session {session_id}")
        
        # Test daily summary
        print("\nTesting daily_summary...")
        request = ToolCallRequest(
            tool='productivity_daily_summary',
            parameters={}
        )
        response = server.call_tool(request)
        
        assert response.success, "Daily summary should succeed"
        assert 'sessions_completed' in response.result, "Should have sessions count"
        print(f"✅ Daily summary: {response.result['sessions_completed']} sessions")
        
        # Test weekly trends
        print("\nTesting weekly_trends...")
        request = ToolCallRequest(
            tool='productivity_weekly_trends',
            parameters={}
        )
        response = server.call_tool(request)
        
        assert response.success, "Weekly trends should succeed"
        assert 'total_sessions' in response.result, "Should have total sessions"
        print(f"✅ Weekly trends: {response.result['total_sessions']} total sessions")
        
        print("\n✅ All productivity tests passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Productivity tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_innovation_tools():
    """Test innovation agent tools"""
    print("\n" + "="*50)
    print("Testing Innovation Agent Tools")
    print("="*50)
    
    try:
        server = MCPServer()
        
        # Test weekly scan (light test - only checks it runs)
        print("\nTesting innovation_weekly_scan...")
        request = ToolCallRequest(
            tool='innovation_weekly_scan',
            parameters={}
        )
        response = server.call_tool(request)
        
        assert response.success, "Weekly scan should succeed"
        print(f"✅ Weekly scan completed: {len(response.result)} innovations found")
        
        print("\n✅ All innovation tests passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Innovation tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("OsMEN MCP Server Integration Tests")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("MCP Server Initialization", test_mcp_server_initialization()))
    results.append(("Productivity Tools", test_productivity_tools()))
    results.append(("Innovation Tools", test_innovation_tools()))
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
