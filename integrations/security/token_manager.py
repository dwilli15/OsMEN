#!/usr/bin/env python3
"""
Token Manager for Secure OAuth Token Storage

Provides secure storage and retrieval of OAuth tokens using SQLite
with encryption via EncryptionManager.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
from integrations.security.encryption_manager import EncryptionManager


class TokenManager:
    """Manages secure storage and retrieval of OAuth tokens.
    
    Features:
    - Encrypted token storage in SQLite
    - Secure file permissions (600)
    - Support for access and refresh tokens
    - Token expiration tracking
    - Scope management
    """
    
    def __init__(self, db_path: str = '~/.osmen/tokens.db', encryption_key: Optional[str] = None):
        """Initialize TokenManager.
        
        Args:
            db_path: Path to SQLite database file
            encryption_key: Encryption key (uses env var if None)
        """
        self.db_path = os.path.expanduser(db_path)
        self.encryptor = EncryptionManager(encryption_key)
        self._init_database()
    
    def _init_database(self):
        """Initialize the token database with secure permissions."""
        # Create directory
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        # Create database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    access_token_encrypted TEXT NOT NULL,
                    refresh_token_encrypted TEXT,
                    expires_at TIMESTAMP NOT NULL,
                    scopes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(provider, user_id)
                )
            ''')
            conn.commit()
        
        # Set secure file permissions (600)
        os.chmod(self.db_path, 0o600)
    
    def save_token(self, provider: str, user_id: str, token_data: Dict) -> bool:
        """Save or update a token.
        
        Args:
            provider: OAuth provider (e.g., 'google', 'microsoft')
            user_id: User identifier
            token_data: Token data dict with:
                - access_token: Access token
                - refresh_token: Refresh token (optional)
                - expires_in: Seconds until expiration
                - scopes: List of scopes (optional)
        
        Returns:
            True if successful
        """
        encrypted_access = self.encryptor.encrypt_token(token_data['access_token'])
        encrypted_refresh = None
        if token_data.get('refresh_token'):
            encrypted_refresh = self.encryptor.encrypt_token(token_data['refresh_token'])
        
        expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
        scopes = ' '.join(token_data.get('scopes', []))
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO tokens 
                (provider, user_id, access_token_encrypted, refresh_token_encrypted, 
                 expires_at, scopes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (provider, user_id, encrypted_access, encrypted_refresh, expires_at, scopes))
            conn.commit()
        
        return True
    
    def get_token(self, provider: str, user_id: str) -> Optional[Dict]:
        """Retrieve and decrypt a token.
        
        Args:
            provider: OAuth provider
            user_id: User identifier
        
        Returns:
            Token dict or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM tokens WHERE provider = ? AND user_id = ?
            ''', (provider, user_id))
            row = cursor.fetchone()
        
        if not row:
            return None
        
        token = {
            'access_token': self.encryptor.decrypt_token(row['access_token_encrypted']),
            'expires_at': datetime.fromisoformat(row['expires_at']),
            'scopes': row['scopes'].split() if row['scopes'] else []
        }
        
        if row['refresh_token_encrypted']:
            token['refresh_token'] = self.encryptor.decrypt_token(row['refresh_token_encrypted'])
        
        return token
    
    def delete_token(self, provider: str, user_id: str) -> bool:
        """Delete a token.
        
        Args:
            provider: OAuth provider
            user_id: User identifier
        
        Returns:
            True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM tokens WHERE provider = ? AND user_id = ?', 
                        (provider, user_id))
            conn.commit()
        return True
    
    def list_tokens(self) -> List[Dict]:
        """List all stored tokens (without decrypting).
        
        Returns:
            List of token metadata dicts
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT provider, user_id, expires_at, scopes, created_at, updated_at
                FROM tokens
            ''')
            return [dict(row) for row in cursor.fetchall()]
