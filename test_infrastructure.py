#!/usr/bin/env python3
"""
Test Suite for Setup Manager and CLI Bridge
Validates new infrastructure components
"""

import sys
import os
from pathlib import Path


def test_setup_manager_import():
    """Test Setup Manager can be imported"""
    print("\n" + "="*50)
    print("Testing Setup Manager Import")
    print("="*50)
    
    try:
        from setup_manager import SetupManager, ConfigManager
        print("✅ Setup Manager Import: PASS")
        return True
    except Exception as e:
        print(f"❌ Setup Manager Import: FAIL - {e}")
        return False


def test_config_manager():
    """Test Config Manager functionality"""
    print("\n" + "="*50)
    print("Testing Config Manager")
    print("="*50)
    
    try:
        from setup_manager import ConfigManager
        
        config = ConfigManager()
        
        # Test get/set
        config.set('TEST_KEY', 'test_value')
        value = config.get('TEST_KEY')
        
        if value != 'test_value':
            raise ValueError("Config get/set failed")
        
        # Test enabled agents
        agents = config.get_enabled_agents()
        if not isinstance(agents, list):
            raise ValueError("get_enabled_agents should return a list")
        
        # Test LLM config
        llm_config = config.get_llm_config()
        if not isinstance(llm_config, dict):
            raise ValueError("get_llm_config should return a dict")
        
        # Test service URLs
        service_urls = config.get_service_urls()
        if not isinstance(service_urls, dict):
            raise ValueError("get_service_urls should return a dict")
        
        print("✅ Config Manager: PASS")
        return True
    except Exception as e:
        print(f"❌ Config Manager: FAIL - {e}")
        return False


def test_setup_manager():
    """Test Setup Manager functionality"""
    print("\n" + "="*50)
    print("Testing Setup Manager")
    print("="*50)
    
    try:
        from setup_manager import SetupManager
        
        manager = SetupManager()
        
        # Test environment validation
        validations = manager.validate_environment()
        if not isinstance(validations, dict):
            raise ValueError("validate_environment should return a dict")
        
        # Test system status
        status = manager.get_system_status()
        if not isinstance(status, dict):
            raise ValueError("get_system_status should return a dict")
        
        required_status_keys = ['timestamp', 'initialized_agents', 'service_connections']
        for key in required_status_keys:
            if key not in status:
                raise ValueError(f"Missing key in status: {key}")
        
        print("✅ Setup Manager: PASS")
        print(f"   Environment checks: {len(validations)}")
        print(f"   Status keys: {len(status)}")
        return True
    except Exception as e:
        print(f"❌ Setup Manager: FAIL - {e}")
        return False


def test_cli_bridge_import():
    """Test CLI Bridge can be imported"""
    print("\n" + "="*50)
    print("Testing CLI Bridge Import")
    print("="*50)
    
    try:
        from cli_bridge import CodexBridge, CopilotBridge, CLIBridgeManager
        print("✅ CLI Bridge Import: PASS")
        return True
    except Exception as e:
        print(f"❌ CLI Bridge Import: FAIL - {e}")
        return False


def test_codex_bridge():
    """Test Codex Bridge functionality"""
    print("\n" + "="*50)
    print("Testing Codex Bridge")
    print("="*50)
    
    try:
        from cli_bridge import CodexBridge
        
        bridge = CodexBridge()
        
        # Test status
        status = bridge.get_status()
        if not isinstance(status, dict):
            raise ValueError("get_status should return a dict")
        
        required_keys = ['cli_available', 'api_key_configured', 'operational']
        for key in required_keys:
            if key not in status:
                raise ValueError(f"Missing key in status: {key}")
        
        print("✅ Codex Bridge: PASS")
        print(f"   Operational: {status['operational']}")
        return True
    except Exception as e:
        print(f"❌ Codex Bridge: FAIL - {e}")
        return False


def test_copilot_bridge():
    """Test Copilot Bridge functionality"""
    print("\n" + "="*50)
    print("Testing Copilot Bridge")
    print("="*50)
    
    try:
        from cli_bridge import CopilotBridge
        
        bridge = CopilotBridge()
        
        # Test status
        status = bridge.get_status()
        if not isinstance(status, dict):
            raise ValueError("get_status should return a dict")
        
        required_keys = ['cli_available', 'token_configured', 'operational']
        for key in required_keys:
            if key not in status:
                raise ValueError(f"Missing key in status: {key}")
        
        print("✅ Copilot Bridge: PASS")
        print(f"   Operational: {status['operational']}")
        return True
    except Exception as e:
        print(f"❌ Copilot Bridge: FAIL - {e}")
        return False


def test_cli_bridge_manager():
    """Test CLI Bridge Manager functionality"""
    print("\n" + "="*50)
    print("Testing CLI Bridge Manager")
    print("="*50)
    
    try:
        from cli_bridge import CLIBridgeManager
        
        manager = CLIBridgeManager()
        
        # Test status
        status = manager.get_status()
        if not isinstance(status, dict):
            raise ValueError("get_status should return a dict")
        
        required_keys = ['codex', 'copilot', 'operational']
        for key in required_keys:
            if key not in status:
                raise ValueError(f"Missing key in status: {key}")
        
        print("✅ CLI Bridge Manager: PASS")
        print(f"   Overall Operational: {status['operational']}")
        return True
    except Exception as e:
        print(f"❌ CLI Bridge Manager: FAIL - {e}")
        return False


def test_integration():
    """Test integration between Setup Manager and CLI Bridge"""
    print("\n" + "="*50)
    print("Testing Integration")
    print("="*50)
    
    try:
        from setup_manager import SetupManager
        from cli_bridge import CLIBridgeManager
        
        # Initialize both
        setup_mgr = SetupManager()
        cli_mgr = CLIBridgeManager()
        
        # Get statuses
        setup_status = setup_mgr.get_system_status()
        cli_status = cli_mgr.get_status()
        
        # Verify they can coexist
        if not isinstance(setup_status, dict) or not isinstance(cli_status, dict):
            raise ValueError("Status retrieval failed")
        
        print("✅ Integration: PASS")
        print(f"   Setup Manager initialized: {len(setup_status.get('initialized_agents', []))} agents")
        print(f"   CLI Bridge operational: {cli_status['operational']}")
        return True
    except Exception as e:
        print(f"❌ Integration: FAIL - {e}")
        return False


def main():
    """Run all infrastructure tests"""
    print("\n" + "="*80)
    print("OsMEN Infrastructure Test Suite")
    print("Testing Setup Manager and CLI Bridge")
    print("="*80)
    
    tests = [
        test_setup_manager_import,
        test_config_manager,
        test_setup_manager,
        test_cli_bridge_import,
        test_codex_bridge,
        test_copilot_bridge,
        test_cli_bridge_manager,
        test_integration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    
    test_names = [
        "Setup Manager Import",
        "Config Manager",
        "Setup Manager",
        "CLI Bridge Import",
        "Codex Bridge",
        "Copilot Bridge",
        "CLI Bridge Manager",
        "Integration"
    ]
    
    for name, result in zip(test_names, results):
        icon = "✅" if result else "❌"
        print(f"{icon} {name}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All infrastructure tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
