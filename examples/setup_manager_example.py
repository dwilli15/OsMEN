#!/usr/bin/env python3
"""
Example: Using Setup Manager to Initialize Agents

This example demonstrates how to use the new Setup Manager
to initialize and manage OsMEN agents.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from setup_manager import SetupManager


def main():
    print("\n" + "="*80)
    print("Example: Setup Manager Agent Initialization")
    print("="*80)
    
    # Initialize Setup Manager
    print("\n1. Initializing Setup Manager...")
    manager = SetupManager()
    
    # Validate environment
    print("\n2. Validating environment...")
    validations = manager.validate_environment()
    for check, status in validations.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {check}")
    
    # Connect to services
    print("\n3. Connecting to services...")
    services = manager.initialize_services()
    for service, status in services.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {service}")
    
    # Initialize a specific agent
    print("\n4. Initializing Daily Brief agent...")
    try:
        daily_brief = manager.initialize_agent('daily_brief')
        print("   ✅ Daily Brief agent initialized")
        
        # Use the agent
        print("\n5. Generating daily brief...")
        brief = daily_brief.generate_brief()
        print(f"   Generated brief for: {brief.get('date')}")
        print(f"   Scheduled tasks: {len(brief.get('scheduled_tasks', []))}")
        
    except Exception as e:
        print(f"   ❌ Failed to initialize agent: {e}")
    
    # Get system status
    print("\n6. System Status:")
    status = manager.get_system_status()
    print(f"   Initialized agents: {len(status['initialized_agents'])}")
    print(f"   Connected services: {len(status['service_connections'])}")
    print(f"   Environment valid: {status['environment_valid']}")
    
    # Shutdown gracefully
    print("\n7. Shutting down...")
    manager.shutdown()
    print("   ✅ Shutdown complete")
    
    print("\n" + "="*80)
    print("Example complete!")
    print("="*80 + "\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
