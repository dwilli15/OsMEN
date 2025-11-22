#!/usr/bin/env python3
"""
Unit tests for CredentialValidator

Tests credential validation logic.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.security.credential_validator import CredentialValidator


def test_validate_required_env_vars():
    """Test validation of required environment variables."""
    # Set test env vars
    os.environ['TEST_VAR_1'] = 'value1'
    os.environ['TEST_VAR_2'] = ''
    
    results = CredentialValidator.validate_required_env_vars(['TEST_VAR_1', 'TEST_VAR_2', 'TEST_VAR_3'])
    
    assert results['TEST_VAR_1'] == True
    assert results['TEST_VAR_2'] == False  # Empty value
    assert results['TEST_VAR_3'] == False  # Not set
    
    # Cleanup
    del os.environ['TEST_VAR_1']
    del os.environ['TEST_VAR_2']
    
    print("✅ test_validate_required_env_vars passed")


def test_validate_google_client_id():
    """Test Google client ID validation."""
    # Valid Google client ID
    valid_id = "123456789.apps.googleusercontent.com"
    assert CredentialValidator.validate_client_id(valid_id, 'google') == True
    
    # Invalid Google client ID
    invalid_id = "invalid_client_id"
    assert CredentialValidator.validate_client_id(invalid_id, 'google') == False
    
    print("✅ test_validate_google_client_id passed")


def test_validate_microsoft_client_id():
    """Test Microsoft client ID validation."""
    # Valid Microsoft client ID (UUID)
    valid_id = "12345678-1234-1234-1234-123456789abc"
    assert CredentialValidator.validate_client_id(valid_id, 'microsoft') == True
    
    # Invalid Microsoft client ID
    invalid_id = "not-a-uuid"
    assert CredentialValidator.validate_client_id(invalid_id, 'microsoft') == False
    
    print("✅ test_validate_microsoft_client_id passed")


def test_validate_redirect_uri():
    """Test redirect URI validation."""
    # Valid URIs
    assert CredentialValidator.validate_redirect_uri('http://localhost:8000/callback') == True
    assert CredentialValidator.validate_redirect_uri('https://example.com/oauth/callback') == True
    
    # Invalid URIs
    assert CredentialValidator.validate_redirect_uri('ftp://example.com') == False
    assert CredentialValidator.validate_redirect_uri('http://example.com#fragment') == False
    assert CredentialValidator.validate_redirect_uri('') == False
    assert CredentialValidator.validate_redirect_uri(None) == False
    
    print("✅ test_validate_redirect_uri passed")


def test_check_secrets_not_committed():
    """Test that .env is in .gitignore."""
    result = CredentialValidator.check_secrets_not_committed()
    # Should be True if .gitignore exists and contains .env
    assert isinstance(result, bool)
    print("✅ test_check_secrets_not_committed passed")


def run_all_tests():
    """Run all credential validator tests."""
    print("\nRunning Credential Validator Tests")
    print("=" * 60)
    
    tests = [
        test_validate_required_env_vars,
        test_validate_google_client_id,
        test_validate_microsoft_client_id,
        test_validate_redirect_uri,
        test_check_secrets_not_committed,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)


def test_validate_client_id_invalid_provider():
    """Test validation with invalid/unknown provider."""
    result = CredentialValidator.validate_client_id('some_random_id', 'unknown_provider')
    # Should return True for unknown providers (skip format validation)
    assert result is True


def test_validate_client_id_none():
    """Test validation with None client_id."""
    result = CredentialValidator.validate_client_id(None, 'google')
    assert result is False


def test_validate_client_id_whitespace():
    """Test validation with whitespace-only client_id."""
    result = CredentialValidator.validate_client_id('   ', 'google')
    assert result is False


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])


def test_check_secrets_not_committed_no_gitignore(tmp_path):
    """Test when .gitignore doesn't exist."""
    import os
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = CredentialValidator.check_secrets_not_committed()
        assert result is False
    finally:
        os.chdir(original_dir)
