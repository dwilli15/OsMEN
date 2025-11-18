#!/usr/bin/env python3
"""
Unit tests for TokenManager

Tests token storage, retrieval, and management.
"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.security.token_manager import TokenManager
from integrations.security.encryption_manager import EncryptionManager


def test_token_manager_initialization():
    """Test TokenManager initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_tokens.db')
        key = EncryptionManager.generate_key()
        
        manager = TokenManager(db_path=db_path, encryption_key=key)
        assert os.path.exists(db_path)
        
        # Check file permissions (600)
        stat_info = os.stat(db_path)
        permissions = oct(stat_info.st_mode)[-3:]
        assert permissions == '600', f"Expected 600, got {permissions}"
    
    print("✅ test_token_manager_initialization passed")


def test_save_and_get_token():
    """Test saving and retrieving a token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_tokens.db')
        key = EncryptionManager.generate_key()
        manager = TokenManager(db_path=db_path, encryption_key=key)
        
        token_data = {
            'access_token': 'test_access_token_123',
            'refresh_token': 'test_refresh_token_456',
            'expires_in': 3600,
            'scopes': ['email', 'profile']
        }
        
        manager.save_token('google', 'user@example.com', token_data)
        
        retrieved = manager.get_token('google', 'user@example.com')
        assert retrieved is not None
        assert retrieved['access_token'] == token_data['access_token']
        assert retrieved['refresh_token'] == token_data['refresh_token']
        assert retrieved['scopes'] == token_data['scopes']
    
    print("✅ test_save_and_get_token passed")


def test_get_nonexistent_token():
    """Test retrieving a token that doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_tokens.db')
        key = EncryptionManager.generate_key()
        manager = TokenManager(db_path=db_path, encryption_key=key)
        
        retrieved = manager.get_token('google', 'nonexistent@example.com')
        assert retrieved is None
    
    print("✅ test_get_nonexistent_token passed")


def test_delete_token():
    """Test deleting a token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_tokens.db')
        key = EncryptionManager.generate_key()
        manager = TokenManager(db_path=db_path, encryption_key=key)
        
        token_data = {
            'access_token': 'test_token',
            'expires_in': 3600
        }
        
        manager.save_token('google', 'user@example.com', token_data)
        assert manager.get_token('google', 'user@example.com') is not None
        
        manager.delete_token('google', 'user@example.com')
        assert manager.get_token('google', 'user@example.com') is None
    
    print("✅ test_delete_token passed")


def test_list_tokens():
    """Test listing all tokens."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_tokens.db')
        key = EncryptionManager.generate_key()
        manager = TokenManager(db_path=db_path, encryption_key=key)
        
        # Save multiple tokens
        for i, provider in enumerate(['google', 'microsoft']):
            token_data = {
                'access_token': f'token_{i}',
                'expires_in': 3600
            }
            manager.save_token(provider, f'user{i}@example.com', token_data)
        
        tokens = manager.list_tokens()
        assert len(tokens) == 2
        assert any(t['provider'] == 'google' for t in tokens)
        assert any(t['provider'] == 'microsoft' for t in tokens)
    
    print("✅ test_list_tokens passed")


def run_all_tests():
    """Run all token manager tests."""
    print("\nRunning Token Manager Tests")
    print("=" * 60)
    
    tests = [
        test_token_manager_initialization,
        test_save_and_get_token,
        test_get_nonexistent_token,
        test_delete_token,
        test_list_tokens,
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
