#!/usr/bin/env python3
"""
Token Management Service - v3.0

Provides secure token storage, automatic refresh, and lifecycle management.

Features:
- Encrypted token storage using Fernet (symmetric encryption)
- Automatic token refresh before expiry
- Background refresh daemon (optional)
- Token lifecycle events and logging
- Secure file permissions
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
from threading import Thread, Event
from loguru import logger

try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    logger.warning("cryptography not installed - using unencrypted storage")


class TokenManager:
    """
    Secure token storage and management.
    
    Handles:
    - Encrypted storage of OAuth tokens
    - Automatic token refresh
    - Token expiry monitoring
    - Secure file permissions
    """
    
    def __init__(self, storage_dir: str = None, encryption_key: str = None):
        """
        Initialize token manager.
        
        Args:
            storage_dir: Directory for storing tokens
            encryption_key: Fernet encryption key (auto-generated if not provided)
        """
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(__file__),
            '../.copilot/integrations/tokens'
        )
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions on storage directory
        os.chmod(self.storage_dir, 0o700)
        
        # Encryption key
        self.encryption_key = encryption_key
        if ENCRYPTION_AVAILABLE and not self.encryption_key:
            self.encryption_key = self._load_or_generate_key()
        
        self.cipher = None
        if ENCRYPTION_AVAILABLE and self.encryption_key:
            self.cipher = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
        
        # Callbacks for token events
        self.on_token_refreshed: Optional[Callable] = None
        self.on_token_expired: Optional[Callable] = None
        
        logger.info(f"TokenManager initialized (encryption: {'enabled' if self.cipher else 'disabled'})")
    
    def _load_or_generate_key(self) -> bytes:
        """Load or generate encryption key"""
        key_file = os.path.join(self.storage_dir, '.encryption_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                key = f.read()
            logger.info("Loaded encryption key")
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            logger.info("Generated new encryption key")
        
        return key
    
    def save_token(self, provider: str, token_data: Dict) -> bool:
        """
        Save token data securely.
        
        Args:
            provider: Provider name (google, microsoft, etc.)
            token_data: Token dictionary from OAuth flow
            
        Returns:
            True if successful
        """
        try:
            # Add metadata
            token_data['stored_at'] = datetime.now().isoformat()
            token_data['provider'] = provider
            
            # Calculate expiry time if not present
            if 'expires_in' in token_data and 'expires_at' not in token_data:
                expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
                token_data['expires_at'] = expires_at.isoformat()
            
            # Serialize
            token_json = json.dumps(token_data)
            
            # Encrypt if available
            if self.cipher:
                token_bytes = self.cipher.encrypt(token_json.encode())
                file_ext = '.encrypted'
            else:
                token_bytes = token_json.encode()
                file_ext = '.json'
            
            # Save to file
            token_file = os.path.join(self.storage_dir, f'{provider}_tokens{file_ext}')
            with open(token_file, 'wb') as f:
                f.write(token_bytes)
            
            # Set secure permissions
            os.chmod(token_file, 0o600)
            
            logger.info(f"Saved token for {provider} (encrypted: {self.cipher is not None})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving token for {provider}: {e}")
            return False
    
    def load_token(self, provider: str) -> Optional[Dict]:
        """
        Load token data for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Token dictionary or None if not found
        """
        try:
            # Try encrypted first, then plaintext
            for ext in ['.encrypted', '.json']:
                token_file = os.path.join(self.storage_dir, f'{provider}_tokens{ext}')
                if os.path.exists(token_file):
                    with open(token_file, 'rb') as f:
                        token_bytes = f.read()
                    
                    # Decrypt if needed
                    if ext == '.encrypted' and self.cipher:
                        token_json = self.cipher.decrypt(token_bytes).decode()
                    else:
                        token_json = token_bytes.decode()
                    
                    token_data = json.loads(token_json)
                    logger.debug(f"Loaded token for {provider}")
                    return token_data
            
            logger.warning(f"No token found for {provider}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading token for {provider}: {e}")
            return None
    
    def delete_token(self, provider: str) -> bool:
        """Delete token for provider"""
        try:
            for ext in ['.encrypted', '.json']:
                token_file = os.path.join(self.storage_dir, f'{provider}_tokens{ext}')
                if os.path.exists(token_file):
                    os.remove(token_file)
                    logger.info(f"Deleted token for {provider}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error deleting token for {provider}: {e}")
            return False
    
    def is_token_expired(self, provider: str) -> bool:
        """Check if token is expired or will expire soon"""
        token_data = self.load_token(provider)
        if not token_data:
            return True
        
        expires_at = token_data.get('expires_at')
        if not expires_at:
            return False  # No expiry info, assume valid
        
        try:
            expiry_time = datetime.fromisoformat(expires_at)
            # Consider expired if less than 5 minutes remaining
            buffer = timedelta(minutes=5)
            return datetime.now() + buffer >= expiry_time
        except Exception as e:
            logger.error(f"Error checking expiry for {provider}: {e}")
            return False
    
    def get_access_token(self, provider: str) -> Optional[str]:
        """Get valid access token (returns None if expired)"""
        if self.is_token_expired(provider):
            logger.warning(f"Token for {provider} is expired")
            if self.on_token_expired:
                self.on_token_expired(provider)
            return None
        
        token_data = self.load_token(provider)
        return token_data.get('access_token') if token_data else None
    
    def list_providers(self) -> list:
        """List all providers with stored tokens"""
        providers = set()
        try:
            for file in os.listdir(self.storage_dir):
                if file.endswith(('.encrypted', '.json')) and '_tokens' in file:
                    provider = file.replace('_tokens.encrypted', '').replace('_tokens.json', '')
                    providers.add(provider)
        except Exception as e:
            logger.error(f"Error listing providers: {e}")
        return sorted(list(providers))
    
    def get_token_status(self, provider: str) -> Dict:
        """Get detailed token status"""
        token_data = self.load_token(provider)
        if not token_data:
            return {
                'provider': provider,
                'exists': False,
                'expired': True
            }
        
        status = {
            'provider': provider,
            'exists': True,
            'expired': self.is_token_expired(provider),
            'has_refresh_token': 'refresh_token' in token_data,
            'stored_at': token_data.get('stored_at'),
            'expires_at': token_data.get('expires_at')
        }
        
        if status['expires_at']:
            try:
                expiry = datetime.fromisoformat(status['expires_at'])
                remaining = expiry - datetime.now()
                status['expires_in_seconds'] = max(0, int(remaining.total_seconds()))
            except:
                pass
        
        return status


class TokenRefreshDaemon:
    """
    Background daemon that automatically refreshes tokens before expiry.
    
    Usage:
        def refresh_callback(provider):
            # Your refresh logic
            oauth_handler = get_oauth_handler(provider)
            new_tokens = oauth_handler.refresh_token(old_refresh_token)
            return new_tokens
        
        daemon = TokenRefreshDaemon(token_manager, refresh_callback)
        daemon.start()
        # ... application runs ...
        daemon.stop()
    """
    
    def __init__(
        self, 
        token_manager: TokenManager,
        refresh_callback: Callable[[str], Optional[Dict]],
        check_interval: int = 300  # 5 minutes
    ):
        """
        Initialize refresh daemon.
        
        Args:
            token_manager: TokenManager instance
            refresh_callback: Function to refresh token, takes provider name, returns new token data
            check_interval: How often to check for expiring tokens (seconds)
        """
        self.token_manager = token_manager
        self.refresh_callback = refresh_callback
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.stop_event = Event()
        
        # Track refresh attempts
        self.refresh_attempts = {}
        self.max_retries = 3
        
        logger.info(f"TokenRefreshDaemon initialized (check interval: {check_interval}s)")
    
    def start(self):
        """Start the refresh daemon"""
        if self.running:
            logger.warning("Refresh daemon already running")
            return
        
        self.running = True
        self.stop_event.clear()
        self.thread = Thread(target=self._run, daemon=True, name="TokenRefreshDaemon")
        self.thread.start()
        logger.info("Token refresh daemon started")
    
    def stop(self):
        """Stop the refresh daemon"""
        if not self.running:
            return
        
        logger.info("Stopping token refresh daemon...")
        self.running = False
        self.stop_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
            if self.thread.is_alive():
                logger.warning("Daemon thread did not stop gracefully")
        
        logger.info("Token refresh daemon stopped")
    
    def _run(self):
        """Main daemon loop"""
        logger.info("Token refresh daemon loop starting")
        
        while self.running:
            try:
                self._check_and_refresh_tokens()
            except Exception as e:
                logger.error(f"Error in refresh daemon: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Wait for check_interval or stop event
            self.stop_event.wait(self.check_interval)
        
        logger.info("Token refresh daemon loop exited")
    
    def _check_and_refresh_tokens(self):
        """Check all tokens and refresh if needed"""
        providers = self.token_manager.list_providers()
        
        if not providers:
            logger.debug("No providers configured, skipping refresh check")
            return
        
        logger.debug(f"Checking {len(providers)} providers for token expiry")
        
        for provider in providers:
            try:
                if self.token_manager.is_token_expired(provider):
                    self._refresh_provider_token(provider)
            except Exception as e:
                logger.error(f"Error checking/refreshing token for {provider}: {e}")
    
    def _refresh_provider_token(self, provider: str):
        """Refresh token for a specific provider"""
        # Check retry count
        attempts = self.refresh_attempts.get(provider, 0)
        if attempts >= self.max_retries:
            logger.error(
                f"Max refresh retries ({self.max_retries}) reached for {provider}. "
                f"Manual intervention required."
            )
            return
        
        logger.info(f"Token for {provider} expiring soon, initiating refresh...")
        
        try:
            # Get current token data
            current_token = self.token_manager.load_token(provider)
            if not current_token:
                logger.error(f"No token found for {provider}")
                return
            
            # Call refresh callback
            new_token_data = self.refresh_callback(provider)
            
            if new_token_data:
                # Save new token
                self.token_manager.save_token(provider, new_token_data)
                logger.info(f"✅ Successfully refreshed token for {provider}")
                
                # Reset retry counter on success
                self.refresh_attempts[provider] = 0
            else:
                logger.error(f"Failed to refresh token for {provider}: callback returned None")
                self.refresh_attempts[provider] = attempts + 1
                
        except Exception as e:
            logger.error(f"Error refreshing token for {provider}: {e}")
            self.refresh_attempts[provider] = attempts + 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get daemon status"""
        return {
            'running': self.running,
            'check_interval': self.check_interval,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'providers_monitored': len(self.token_manager.list_providers()),
            'refresh_attempts': self.refresh_attempts.copy()
        }


if __name__ == "__main__":
    # Example usage
    print("Token Management Service - v3.0")
    print("=" * 70)
    
    if not ENCRYPTION_AVAILABLE:
        print("\n⚠️  WARNING: cryptography package not installed")
        print("Install with: pip install cryptography")
        print("Tokens will be stored UNENCRYPTED\n")
    
    token_manager = TokenManager()
    
    print(f"\nStorage directory: {token_manager.storage_dir}")
    print(f"Encryption: {'Enabled ✅' if token_manager.cipher else 'Disabled ❌'}")
    
    # List providers
    providers = token_manager.list_providers()
    print(f"\nConfigured providers: {len(providers)}")
    for provider in providers:
        status = token_manager.get_token_status(provider)
        print(f"  - {provider}: {'Expired ❌' if status['expired'] else 'Valid ✅'}")
        if status.get('expires_in_seconds'):
            hours = status['expires_in_seconds'] // 3600
            minutes = (status['expires_in_seconds'] % 3600) // 60
            print(f"    Expires in: {hours}h {minutes}m")
    
    print("\nUsage:")
    print("  from integrations.token_manager import TokenManager")
    print("  token_manager = TokenManager()")
    print("  token = token_manager.get_access_token('google')")
