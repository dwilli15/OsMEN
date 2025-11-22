#!/usr/bin/env python3
"""
Unit tests for EncryptionManager

Tests encryption/decryption, key generation, and error handling.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.security.encryption_manager import EncryptionManager


def test_generate_key():
    """Test key generation."""
    key = EncryptionManager.generate_key()
    assert key is not None
    assert len(key) > 0
    assert isinstance(key, str)
    print("✅ test_generate_key passed")


def test_encryption_round_trip():
    """Test encryption and decryption round trip."""
    manager = EncryptionManager(EncryptionManager.generate_key())
    original = "test_access_token_12345"
    
    encrypted = manager.encrypt_token(original)
    decrypted = manager.decrypt_token(encrypted)
    
    assert decrypted == original
    assert encrypted != original  # Verify it was actually encrypted
    print("✅ test_encryption_round_trip passed")


def test_encrypt_empty_token():
    """Test that encrypting empty token raises error."""
    manager = EncryptionManager(EncryptionManager.generate_key())
    try:
        manager.encrypt_token("")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "empty token" in str(e).lower()
    print("✅ test_encrypt_empty_token passed")


def test_decrypt_empty_ciphertext():
    """Test that decrypting empty ciphertext raises error."""
    manager = EncryptionManager(EncryptionManager.generate_key())
    try:
        manager.decrypt_token("")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "empty" in str(e).lower()
    print("✅ test_decrypt_empty_ciphertext passed")


def test_decrypt_invalid_ciphertext():
    """Test that decrypting invalid ciphertext raises error."""
    manager = EncryptionManager(EncryptionManager.generate_key())
    try:
        manager.decrypt_token("invalid_ciphertext")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "decrypt" in str(e).lower()
    print("✅ test_decrypt_invalid_ciphertext passed")


def test_different_keys_different_encryption():
    """Test that different keys produce different encryption."""
    key1 = EncryptionManager.generate_key()
    key2 = EncryptionManager.generate_key()
    
    manager1 = EncryptionManager(key1)
    manager2 = EncryptionManager(key2)
    
    token = "test_token_123"
    
    encrypted1 = manager1.encrypt_token(token)
    encrypted2 = manager2.encrypt_token(token)
    
    # Same plaintext, different keys should produce different ciphertext
    assert encrypted1 != encrypted2
    print("✅ test_different_keys_different_encryption passed")


def test_wrong_key_cannot_decrypt():
    """Test that wrong key cannot decrypt."""
    key1 = EncryptionManager.generate_key()
    key2 = EncryptionManager.generate_key()
    
    manager1 = EncryptionManager(key1)
    manager2 = EncryptionManager(key2)
    
    token = "test_token_123"
    encrypted = manager1.encrypt_token(token)
    
    try:
        manager2.decrypt_token(encrypted)
        assert False, "Should not be able to decrypt with wrong key"
    except ValueError:
        pass  # Expected
    print("✅ test_wrong_key_cannot_decrypt passed")


def test_invalid_key_raises_error():
    """Test that invalid key raises error on initialization."""
    try:
        EncryptionManager("invalid_key")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "invalid" in str(e).lower() or "key" in str(e).lower()
    print("✅ test_invalid_key_raises_error passed")


def test_no_key_raises_error():
    """Test that missing key raises error."""
    import os
    # Temporarily remove env var if it exists
    old_key = os.environ.get('OAUTH_ENCRYPTION_KEY')
    if 'OAUTH_ENCRYPTION_KEY' in os.environ:
        del os.environ['OAUTH_ENCRYPTION_KEY']
    
    try:
        EncryptionManager()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "key" in str(e).lower()
    finally:
        # Restore env var
        if old_key:
            os.environ['OAUTH_ENCRYPTION_KEY'] = old_key
    print("✅ test_no_key_raises_error passed")


def test_unicode_token_encryption():
    """Test encryption of unicode tokens."""
    manager = EncryptionManager(EncryptionManager.generate_key())
    token = "test_token_with_unicode_🔐_symbols"
    
    encrypted = manager.encrypt_token(token)
    decrypted = manager.decrypt_token(encrypted)
    
    assert decrypted == token
    print("✅ test_unicode_token_encryption passed")


def run_all_tests():
    """Run all encryption tests."""
    print("\nRunning Encryption Manager Tests")
    print("=" * 60)
    
    tests = [
        test_generate_key,
        test_encryption_round_trip,
        test_encrypt_empty_token,
        test_decrypt_empty_ciphertext,
        test_decrypt_invalid_ciphertext,
        test_different_keys_different_encryption,
        test_wrong_key_cannot_decrypt,
        test_invalid_key_raises_error,
        test_no_key_raises_error,
        test_unicode_token_encryption,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)


def test_encryption_with_env_var():
    """Test initialization with environment variable."""
    import os
    key = EncryptionManager.generate_key()
    os.environ['OAUTH_ENCRYPTION_KEY'] = key
    
    try:
        manager = EncryptionManager()
        token = "test_token"
        encrypted = manager.encrypt_token(token)
        decrypted = manager.decrypt_token(encrypted)
        assert decrypted == token
        print("✅ test_encryption_with_env_var passed")
    finally:
        del os.environ['OAUTH_ENCRYPTION_KEY']


def test_encrypt_non_string_token():
    """Test encrypting non-string token."""
    manager = EncryptionManager(EncryptionManager.generate_key())
    try:
        manager.encrypt_token(12345)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must be a string" in str(e).lower()
    print("✅ test_encrypt_non_string_token passed")


def test_key_as_bytes():
    """Test initialization with bytes key."""
    key = EncryptionManager.generate_key()
    key_bytes = key.encode()
    manager = EncryptionManager(key_bytes)
    
    token = "test_token"
    encrypted = manager.encrypt_token(token)
    decrypted = manager.decrypt_token(encrypted)
    assert decrypted == token
    print("✅ test_key_as_bytes passed")


if __name__ == '__main__':
    test_generate_key()
    test_encryption_round_trip()
    test_encrypt_empty_token()
    test_decrypt_empty_ciphertext()
    test_decrypt_invalid_ciphertext()
    test_different_keys_different_encryption()
    test_wrong_key_cannot_decrypt()
    test_invalid_key_raises_error()
    test_no_key_raises_error()
    test_unicode_token_encryption()
    test_encryption_with_env_var()
    test_encrypt_non_string_token()
    test_key_as_bytes()
    print("\n✅ All encryption tests passed!")


def test_decrypt_non_string_ciphertext():
    """Test decrypting non-string ciphertext."""
    manager = EncryptionManager(EncryptionManager.generate_key())
    try:
        manager.decrypt_token(12345)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must be a string" in str(e).lower()
    print("✅ test_decrypt_non_string_ciphertext passed")


if __name__ == '__main__':
    test_generate_key()
    test_encryption_round_trip()
    test_encrypt_empty_token()
    test_decrypt_empty_ciphertext()
    test_decrypt_invalid_ciphertext()
    test_different_keys_different_encryption()
    test_wrong_key_cannot_decrypt()
    test_invalid_key_raises_error()
    test_no_key_raises_error()
    test_unicode_token_encryption()
    test_encryption_with_env_var()
    test_encrypt_non_string_token()
    test_key_as_bytes()
    test_decrypt_non_string_ciphertext()
    print("\n✅ All encryption tests passed!")
