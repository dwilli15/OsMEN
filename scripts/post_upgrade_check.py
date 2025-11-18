#!/usr/bin/env python3
"""
Post-upgrade validation script for OsMEN.
Verifies system health after upgrading to a new version.
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"  Checking {description}...", end=' ')
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=30,
            check=False
        )
        if result.returncode == 0:
            print("✅")
            return True
        else:
            print("❌")
            return False
    except Exception as e:
        print(f"❌ ({e})")
        return False


def check_docker_services():
    """Check that all Docker services are running."""
    print("\n🐳 Checking Docker services...")
    
    services = [
        'postgres',
        'redis',
        'qdrant',
        'langflow',
        'n8n',
    ]
    
    all_running = True
    for service in services:
        running = run_command(
            f'docker ps | grep -q {service}',
            f'{service} container'
        )
        all_running = all_running and running
    
    return all_running


def check_python_imports():
    """Check that key Python modules can be imported."""
    print("\n🐍 Checking Python dependencies...")
    
    modules = [
        'fastapi',
        'pydantic',
        'langchain',
        'qdrant_client',
    ]
    
    all_imported = True
    for module in modules:
        imported = run_command(
            f'python3 -c "import {module}"',
            f'{module} module'
        )
        all_imported = all_imported and imported
    
    return all_imported


def check_database_connection():
    """Check database connection."""
    print("\n💾 Checking database connection...")
    
    return run_command(
        'docker exec osmen-postgres psql -U postgres -c "SELECT 1" > /dev/null 2>&1',
        'PostgreSQL connection'
    )


def check_agent_files():
    """Check that agent files exist."""
    print("\n🤖 Checking agent files...")
    
    agents_dir = Path('agents')
    if not agents_dir.exists():
        print("  ❌ agents/ directory not found")
        return False
    
    agent_dirs = [d for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if len(agent_dirs) == 0:
        print("  ❌ No agent directories found")
        return False
    
    print(f"  ✅ Found {len(agent_dirs)} agent directories")
    return True


def check_configuration():
    """Check critical configuration files."""
    print("\n⚙️  Checking configuration...")
    
    critical_files = [
        '.env',
        'docker-compose.yml',
    ]
    
    all_exist = True
    for file in critical_files:
        exists = Path(file).exists()
        print(f"  Checking {file}...", end=' ')
        if exists:
            print("✅")
        else:
            print("❌")
            all_exist = False
    
    return all_exist


def run_agent_tests():
    """Run basic agent tests."""
    print("\n🧪 Running agent tests...")
    
    test_file = Path('test_agents.py')
    if not test_file.exists():
        print("  ⚠️  test_agents.py not found, skipping")
        return True
    
    return run_command(
        'python3 test_agents.py',
        'agent tests'
    )


def main():
    """Main entry point."""
    print("🔍 OsMEN Post-Upgrade Validation")
    print("=" * 60)
    
    # Determine if --full flag is present
    full_check = '--full' in sys.argv
    
    if full_check:
        print("\n📋 Running FULL validation suite")
    else:
        print("\n📋 Running standard validation")
        print("   (use --full for comprehensive checks)")
    
    # Run checks
    results = {}
    
    results['docker'] = check_docker_services()
    results['python'] = check_python_imports()
    results['database'] = check_database_connection()
    results['agents'] = check_agent_files()
    results['config'] = check_configuration()
    
    if full_check:
        results['tests'] = run_agent_tests()
    
    # Summary
    print("\n" + "=" * 60)
    print("\n📊 Validation Summary:\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {check.capitalize()}: {status}")
    
    print(f"\n  Total: {passed}/{total} checks passed")
    print("\n" + "=" * 60)
    
    if passed == total:
        print("\n✅ All validation checks passed!")
        print("\nYour OsMEN installation appears to be working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some validation checks failed")
        print("\nRecommended actions:")
        print("1. Review failed checks above")
        print("2. Check Docker logs: docker-compose logs")
        print("3. Verify configuration in .env")
        print("4. Consult docs/UPGRADING.md for troubleshooting")
        sys.exit(1)


if __name__ == '__main__':
    main()
