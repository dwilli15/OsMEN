#!/usr/bin/env python3
"""
Team 5 Security Test Runner

Runs all Team 5 security component tests.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import test modules
from tests.unit.security.test_encryption import run_all_tests as run_encryption_tests
from tests.unit.security.test_token_manager import run_all_tests as run_token_manager_tests
from tests.unit.security.test_credential_validator import run_all_tests as run_credential_validator_tests
from tests.unit.security.test_oauth_errors import run_all_tests as run_oauth_errors_tests


def main():
    """Run all Team 5 security tests."""
    print("\n" + "=" * 80)
    print("TEAM 5 SECURITY - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    test_suites = [
        ("Encryption Manager", run_encryption_tests),
        ("Token Manager", run_token_manager_tests),
        ("Credential Validator", run_credential_validator_tests),
        ("OAuth Error Handling", run_oauth_errors_tests),
    ]
    
    total_passed = 0
    total_failed = 0
    
    for suite_name, run_tests in test_suites:
        print(f"\n{'=' * 80}")
        print(f"Running {suite_name} Tests")
        print("=" * 80)
        
        success = run_tests()
        
        if success:
            print(f"✅ {suite_name} - ALL TESTS PASSED")
            total_passed += 1
        else:
            print(f"❌ {suite_name} - SOME TESTS FAILED")
            total_failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Test Suites Passed: {total_passed}/{len(test_suites)}")
    print(f"Test Suites Failed: {total_failed}/{len(test_suites)}")
    
    if total_failed == 0:
        print("\n🎉 ALL TEAM 5 SECURITY TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n⚠️  {total_failed} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
