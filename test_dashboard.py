#!/usr/bin/env python3
"""
Test suite for OsMEN Dashboard
"""

import sys
import asyncio
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent))

from dashboard.dashboard_server import app, DashboardService


def test_dashboard_initialization():
    """Test dashboard service initialization"""
    print("\n" + "="*50)
    print("Testing Dashboard Initialization")
    print("="*50)
    
    try:
        service = DashboardService()
        assert service.productivity is not None, "Productivity monitor should be initialized"
        assert service.innovation is not None, "Innovation agent should be initialized"
        print("✅ Dashboard service initialized")
        
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test dashboard API endpoints (simplified)"""
    print("\n" + "="*50)
    print("Testing Dashboard API Endpoints")
    print("="*50)
    
    try:
        service = DashboardService()
        
        # Test status data
        print("\nTesting system status data...")
        status = service.get_system_status()
        assert status["status"] == "operational", "System should be operational"
        assert "agents" in status, "Should have agents"
        assert "services" in status, "Should have services"
        assert "timestamp" in status, "Should have timestamp"
        print(f"✅ System status: {status['status']} ({len(status['agents'])} agents)")
        
        # Test productivity data
        print("\nTesting productivity metrics data...")
        metrics = service.get_productivity_metrics()
        assert "status" in metrics, "Should have status"
        assert metrics["status"] in ["success", "error"], "Status should be valid"
        print(f"✅ Productivity metrics: {metrics['status']}")
        
        # Test innovation backlog data
        print("\nTesting innovation backlog data...")
        backlog = service.get_innovation_backlog()
        assert "status" in backlog, "Should have status"
        assert backlog["status"] in ["success", "error"], "Status should be valid"
        if backlog["status"] == "success":
            assert "innovations" in backlog, "Should have innovations"
            assert "total" in backlog, "Should have total count"
            print(f"✅ Innovation backlog: {backlog['total']} items")
        
        # Test agent logs
        print("\nTesting agent logs data...")
        logs = service.get_agent_logs("innovation_agent", 10)
        assert isinstance(logs, list), "Logs should be a list"
        print(f"✅ Agent logs: {len(logs)} entries")
        
        print("\n✅ All API endpoint data tests passed")
        return True
        
    except Exception as e:
        print(f"\n❌ API tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dashboard_components():
    """Test dashboard data aggregation"""
    print("\n" + "="*50)
    print("Testing Dashboard Components")
    print("="*50)
    
    try:
        service = DashboardService()
        
        # Test system status
        print("\nTesting get_system_status...")
        status = service.get_system_status()
        assert status["status"] == "operational", "System should be operational"
        assert "agents" in status, "Should have agents"
        assert "services" in status, "Should have services"
        print(f"✅ System status: {status['status']}")
        
        # Test productivity metrics
        print("\nTesting get_productivity_metrics...")
        metrics = service.get_productivity_metrics()
        assert "status" in metrics, "Should have status"
        print(f"✅ Productivity metrics retrieved")
        
        # Test innovation backlog
        print("\nTesting get_innovation_backlog...")
        backlog = service.get_innovation_backlog()
        assert "status" in backlog, "Should have status"
        print(f"✅ Innovation backlog: {backlog.get('total', 0)} items")
        
        print("\n✅ All component tests passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Component tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all dashboard tests"""
    print("\n" + "="*70)
    print("OsMEN Dashboard Test Suite")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Dashboard Initialization", test_dashboard_initialization()))
    results.append(("Dashboard Components", test_dashboard_components()))
    results.append(("API Endpoints", test_api_endpoints()))
    
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
        print("\n🎉 All dashboard tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
