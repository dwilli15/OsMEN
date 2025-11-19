#!/usr/bin/env python3
"""
Security Logger for OAuth and Token Operations

Logs security-related events with proper privacy protection.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any
import hashlib
from pathlib import Path


class SecurityLogger:
    """Logs security-related events."""
    
    def __init__(self, log_file: str = '~/.osmen/security.log'):
        """Initialize security logger.
        
        Args:
            log_file: Path to security log file
        """
        self.log_file = os.path.expanduser(log_file)
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Set up security logger with file handler."""
        logger = logging.getLogger('osmen.security')
        logger.setLevel(logging.INFO)
        
        # Create log directory
        log_dir = os.path.dirname(self.log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log_oauth_event(self, event_type: str, provider: str, 
                       user_id: str, success: bool, details: Dict[str, Any] = None):
        """Log OAuth-related event.
        
        Args:
            event_type: Type of event (e.g., 'token_exchange', 'refresh')
            provider: OAuth provider
            user_id: User identifier
            success: Whether operation succeeded
            details: Additional event details
        """
        # Hash user_id for privacy
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'provider': provider,
            'user_hash': user_hash,
            'success': success,
            'details': details or {}
        }
        
        if success:
            self.logger.info(f"OAuth Event: {event}")
        else:
            self.logger.warning(f"OAuth Event Failed: {event}")
    
    def log_token_event(self, event_type: str, provider: str, user_id: str):
        """Log token-related event (creation, refresh, deletion).
        
        Args:
            event_type: Type of token event
            provider: OAuth provider
            user_id: User identifier
        """
        self.log_oauth_event(event_type, provider, user_id, True, 
                           {'event': 'token_operation'})
    
    def log_security_error(self, error_type: str, details: Dict[str, Any]):
        """Log security error.
        
        Args:
            error_type: Type of security error
            details: Error details
        """
        self.logger.error(f"Security Error - {error_type}: {details}")
