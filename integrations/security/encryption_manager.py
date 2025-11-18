#!/usr/bin/env python3
"""
Encryption Manager for OAuth Token Security

Provides secure encryption and decryption of OAuth tokens using Fernet
symmetric encryption from the cryptography library.
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet


class EncryptionManager:
    """Manages encryption/decryption of sensitive data (tokens).
    
    Uses Fernet symmetric encryption which provides:
    - Authentication (prevents tampering)
    - Encryption (prevents reading)
    - Time-based expiration support
    
    Example:
        >>> manager = EncryptionManager()
        >>> encrypted = manager.encrypt_token("my_access_token")
        >>> decrypted = manager.decrypt_token(encrypted)
        >>> assert decrypted == "my_access_token"
    """
    
    def __init__(self, key_source: Optional[str] = None):
        """Initialize with encryption key from environment or parameter.
        
        Args:
            key_source: Base64-encoded Fernet key. If None, reads from
                       OAUTH_ENCRYPTION_KEY environment variable.
        
        Raises:
            ValueError: If no key is provided or key is invalid
        """
        if key_source is None:
            key_source = os.getenv('OAUTH_ENCRYPTION_KEY')
        
        if not key_source:
            raise ValueError(
                "Encryption key must be provided via OAUTH_ENCRYPTION_KEY "
                "environment variable or key_source parameter. "
                "Generate a key with: EncryptionManager.generate_key()"
            )
        
        try:
            # Ensure key is bytes
            if isinstance(key_source, str):
                key_bytes = key_source.encode()
            else:
                key_bytes = key_source
            
            self.cipher = Fernet(key_bytes)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")
    
    def encrypt_token(self, plaintext: str) -> str:
        """Encrypt a token.
        
        Args:
            plaintext: The token to encrypt
        
        Returns:
            Base64-encoded encrypted token
        
        Raises:
            ValueError: If plaintext is empty or None
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty token")
        
        if not isinstance(plaintext, str):
            raise ValueError("Token must be a string")
        
        # Encrypt the plaintext
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        
        # Return as base64-encoded string for easy storage
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    
    def decrypt_token(self, ciphertext: str) -> str:
        """Decrypt a token.
        
        Args:
            ciphertext: The encrypted token (base64-encoded)
        
        Returns:
            Decrypted plaintext token
        
        Raises:
            ValueError: If ciphertext is empty, None, or decryption fails
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty ciphertext")
        
        if not isinstance(ciphertext, str):
            raise ValueError("Ciphertext must be a string")
        
        try:
            # Decode from base64
            decoded = base64.urlsafe_b64decode(ciphertext.encode())
            
            # Decrypt
            decrypted_bytes = self.cipher.decrypt(decoded)
            
            return decrypted_bytes.decode()
        
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key.
        
        Returns:
            Base64-encoded Fernet key suitable for encryption
        
        Example:
            >>> key = EncryptionManager.generate_key()
            >>> manager = EncryptionManager(key)
        """
        return Fernet.generate_key().decode()
