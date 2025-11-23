#!/usr/bin/env python3
"""
Tests for Security Logger
"""

import pytest
import os
import logging
import hashlib
from pathlib import Path
from integrations.security.security_logger import SecurityLogger


@pytest.fixture
def log_file(tmp_path):
    """Create temporary log file path."""
    return str(tmp_path / "test_security.log")


@pytest.fixture
def security_logger(log_file):
    """Create security logger with temporary log file."""
    return SecurityLogger(log_file=log_file)


class TestSecurityLogger:
    """Test SecurityLogger class."""
    
    def test_initialization(self, security_logger, log_file):
        """Test SecurityLogger initialization."""
        assert security_logger.logger is not None
        assert security_logger.log_file == log_file
        assert os.path.exists(os.path.dirname(log_file))
    
    def test_log_file_creation(self, log_file):
        """Test log file is created."""
        logger = SecurityLogger(log_file=log_file)
        logger.log_oauth_event('test', 'google', 'user1', True)
        assert os.path.exists(log_file)
    
    def test_log_oauth_event_success(self, security_logger, log_file):
        """Test logging successful OAuth event."""
        security_logger.log_oauth_event(
            'token_exchange',
            'google',
            'test_user',
            True,
            {'code_length': 40}
        )
        
        # Check log file contains the event
        with open(log_file, 'r') as f:
            content = f.read()
            assert 'OAuth Event' in content
            assert 'token_exchange' in content
            assert 'google' in content
            # Should NOT contain actual user_id
            assert 'test_user' not in content
            # Should contain hashed user_id
            user_hash = hashlib.sha256('test_user'.encode()).hexdigest()[:16]
            assert user_hash in content
    
    def test_log_oauth_event_failure(self, security_logger, log_file):
        """Test logging failed OAuth event."""
        security_logger.log_oauth_event(
            'token_exchange',
            'microsoft',
            'test_user',
            False,
            {'error': 'invalid_code'}
        )
        
        with open(log_file, 'r') as f:
            content = f.read()
            assert 'OAuth Event Failed' in content
            assert 'microsoft' in content
            assert 'invalid_code' in content
    
    def test_log_token_event(self, security_logger, log_file):
        """Test logging token event."""
        security_logger.log_token_event('token_created', 'google', 'user123')
        
        with open(log_file, 'r') as f:
            content = f.read()
            assert 'token_created' in content
            assert 'google' in content
            assert 'token_operation' in content
    
    def test_log_security_error(self, security_logger, log_file):
        """Test logging security error."""
        security_logger.log_security_error(
            'encryption_failed',
            {'reason': 'Invalid key', 'timestamp': '2024-01-01'}
        )
        
        with open(log_file, 'r') as f:
            content = f.read()
            assert 'Security Error' in content
            assert 'encryption_failed' in content
            assert 'Invalid key' in content
    
    def test_user_id_hashing(self, security_logger):
        """Test that user_id is properly hashed."""
        user_id = 'sensitive_user@example.com'
        expected_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        
        # Log event
        security_logger.log_oauth_event('test', 'google', user_id, True)
        
        # Check log file
        with open(security_logger.log_file, 'r') as f:
            content = f.read()
            # Original user_id should NOT be in log
            assert user_id not in content
            # Hash should be in log
            assert expected_hash in content
    
    def test_log_rotation_setup(self, log_file):
        """Test that log rotation is configured."""
        logger = SecurityLogger(log_file=log_file)
        
        # Check that handler is RotatingFileHandler
        handlers = logger.logger.handlers
        assert len(handlers) > 0
        
        # Find RotatingFileHandler
        rotating_handler = None
        for handler in handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                rotating_handler = handler
                break
        
        assert rotating_handler is not None
        assert rotating_handler.maxBytes == 10*1024*1024  # 10MB
        assert rotating_handler.backupCount == 5
    
    def test_log_level(self, security_logger):
        """Test logger level is set correctly."""
        assert security_logger.logger.level == logging.INFO
    
    def test_log_format(self, security_logger, log_file):
        """Test log message format."""
        security_logger.log_oauth_event('test', 'google', 'user1', True)
        
        with open(log_file, 'r') as f:
            content = f.read()
            # Should contain timestamp, logger name, level, and message
            assert 'osmen.security' in content
            assert 'INFO' in content or 'WARNING' in content
    
    def test_multiple_events(self, security_logger, log_file):
        """Test logging multiple events."""
        security_logger.log_oauth_event('event1', 'google', 'user1', True)
        security_logger.log_oauth_event('event2', 'microsoft', 'user2', False)
        security_logger.log_token_event('token_refresh', 'google', 'user1')
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) >= 3
    
    def test_log_directory_creation(self, tmp_path):
        """Test that log directory is created if it doesn't exist."""
        nested_log = str(tmp_path / "nested" / "dir" / "security.log")
        logger = SecurityLogger(log_file=nested_log)
        
        logger.log_oauth_event('test', 'google', 'user1', True)
        
        assert os.path.exists(nested_log)
        assert os.path.exists(os.path.dirname(nested_log))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
