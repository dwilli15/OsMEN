#!/usr/bin/env python3
"""
Token Refresher for Automatic OAuth Token Refresh

Automatically refreshes expiring OAuth tokens using refresh tokens.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from integrations.security.token_manager import TokenManager

logger = logging.getLogger(__name__)


class TokenRefresher:
    """Automatically refreshes expiring tokens."""
    
    def __init__(self, token_manager: TokenManager, oauth_registry):
        """Initialize TokenRefresher.
        
        Args:
            token_manager: TokenManager instance
            oauth_registry: OAuth provider registry (from Team 1)
        """
        self.token_manager = token_manager
        self.oauth_registry = oauth_registry
    
    def check_and_refresh_token(self, provider: str, user_id: str) -> bool:
        """Check if token needs refresh and refresh if necessary.
        
        Args:
            provider: OAuth provider
            user_id: User identifier
        
        Returns:
            True if token is valid or successfully refreshed
        """
        token = self.token_manager.get_token(provider, user_id)
        
        if not token:
            logger.warning(f"No token found for {provider}/{user_id}")
            return False
        
        # Refresh if expiring within 5 minutes
        if self._is_expiring_soon(token['expires_at'], minutes=5):
            logger.info(f"Token expiring soon for {provider}/{user_id}, refreshing...")
            return self._refresh_token(provider, user_id, token)
        
        return True  # Token is still valid
    
    def _is_expiring_soon(self, expires_at: datetime, minutes: int = 5) -> bool:
        """Check if token expires within specified minutes.
        
        Args:
            expires_at: Token expiration datetime
            minutes: Minutes threshold
        
        Returns:
            True if expiring soon
        """
        return datetime.now() + timedelta(minutes=minutes) >= expires_at
    
    def _refresh_token(self, provider: str, user_id: str, token: Dict) -> bool:
        """Refresh an expiring token.
        
        Args:
            provider: OAuth provider
            user_id: User identifier
            token: Current token data
        
        Returns:
            True if refresh successful
        """
        if 'refresh_token' not in token:
            logger.error(f"No refresh token available for {provider}/{user_id}")
            return False
        
        try:
            # Get OAuth handler for provider
            handler = self.oauth_registry.get_handler(provider)
            
            # Refresh the token
            new_token = handler.refresh_token(token['refresh_token'])
            
            # Save updated token
            self.token_manager.save_token(provider, user_id, new_token)
            
            logger.info(f"Successfully refreshed token for {provider}/{user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh token for {provider}/{user_id}: {e}")
            return False


import time
import threading


class TokenRefreshScheduler:
    """Background scheduler for token refresh."""
    
    def __init__(self, token_refresher: TokenRefresher, check_interval: int = 300):
        """Initialize with 5-minute default check interval.
        
        Args:
            token_refresher: TokenRefresher instance
            check_interval: Check interval in seconds (default 300 = 5 min)
        """
        self.refresher = token_refresher
        self.check_interval = check_interval
        self.running = False
        self.thread = None
    
    def start(self):
        """Start background refresh checking."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self.thread.start()
        logger.info("Token refresh scheduler started")
    
    def stop(self):
        """Stop background refresh checking."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Token refresh scheduler stopped")
    
    def _refresh_loop(self):
        """Background loop to check and refresh tokens."""
        while self.running:
            try:
                tokens = self.refresher.token_manager.list_tokens()
                for token_info in tokens:
                    self.refresher.check_and_refresh_token(
                        token_info['provider'],
                        token_info['user_id']
                    )
            except Exception as e:
                logger.error(f"Error in refresh loop: {e}")
            
            time.sleep(self.check_interval)
