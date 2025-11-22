#!/usr/bin/env python3
"""
Tests for Token Refresher
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from integrations.security.token_refresher import TokenRefresher, TokenRefreshScheduler
from integrations.security.token_manager import TokenManager
from integrations.security.encryption_manager import EncryptionManager


@pytest.fixture
def encryption_manager():
    """Create encryption manager with test key."""
    return EncryptionManager(EncryptionManager.generate_key())


@pytest.fixture
def token_manager(encryption_manager, tmp_path):
    """Create token manager with temp database."""
    db_path = tmp_path / "test_tokens.db"
    # Get the encryption key from the encryption manager
    key = EncryptionManager.generate_key()
    return TokenManager(
        db_path=str(db_path),
        encryption_key=key
    )


@pytest.fixture
def mock_oauth_handler():
    """Create mock OAuth handler."""
    handler = Mock()
    handler.refresh_token = Mock(return_value={
        'access_token': 'new_access_token',
        'expires_in': 3600,
        'refresh_token': 'new_refresh_token',
        'scopes': ['calendar', 'gmail']
    })
    return handler


@pytest.fixture
def oauth_registry(mock_oauth_handler):
    """Create mock OAuth registry."""
    registry = Mock()
    registry.get_handler = Mock(return_value=mock_oauth_handler)
    return registry


@pytest.fixture
def token_refresher(token_manager, oauth_registry):
    """Create token refresher."""
    return TokenRefresher(token_manager, oauth_registry)


class TestTokenRefresher:
    """Test TokenRefresher class."""
    
    def test_initialization(self, token_refresher):
        """Test TokenRefresher initialization."""
        assert token_refresher.token_manager is not None
        assert token_refresher.oauth_registry is not None
    
    def test_is_expiring_soon_true(self, token_refresher):
        """Test _is_expiring_soon returns True for soon-to-expire token."""
        # Token expires in 2 minutes
        expires_at = datetime.now() + timedelta(minutes=2)
        assert token_refresher._is_expiring_soon(expires_at, minutes=5) is True
    
    def test_is_expiring_soon_false(self, token_refresher):
        """Test _is_expiring_soon returns False for valid token."""
        # Token expires in 10 minutes
        expires_at = datetime.now() + timedelta(minutes=10)
        assert token_refresher._is_expiring_soon(expires_at, minutes=5) is False
    
    def test_is_expiring_soon_already_expired(self, token_refresher):
        """Test _is_expiring_soon returns True for already expired token."""
        # Token expired 1 minute ago
        expires_at = datetime.now() - timedelta(minutes=1)
        assert token_refresher._is_expiring_soon(expires_at, minutes=5) is True
    
    def test_check_and_refresh_no_token(self, token_refresher):
        """Test check_and_refresh_token with non-existent token."""
        result = token_refresher.check_and_refresh_token('google', 'user1')
        assert result is False
    
    def test_check_and_refresh_valid_token(self, token_refresher, token_manager):
        """Test check_and_refresh_token with valid token."""
        # Store token that expires in 10 minutes (not expiring soon)
        token_manager.save_token('google', 'user1', {
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
            'expires_in': 600,  # 10 minutes
            'scopes': ['calendar']
        })
        
        result = token_refresher.check_and_refresh_token('google', 'user1')
        assert result is True
    
    def test_check_and_refresh_expiring_token(self, token_refresher, token_manager, oauth_registry):
        """Test check_and_refresh_token with expiring token."""
        # Store token that expires in 2 minutes (expiring soon)
        token_manager.save_token('google', 'user1', {
            'access_token': 'old_token',
            'refresh_token': 'old_refresh',
            'expires_in': 120,  # 2 minutes
            'scopes': ['calendar']
        })
        
        result = token_refresher.check_and_refresh_token('google', 'user1')
        assert result is True
        
        # Verify refresh was called
        oauth_registry.get_handler.assert_called_once_with('google')
    
    def test_refresh_token_success(self, token_refresher, token_manager, mock_oauth_handler):
        """Test _refresh_token success."""
        # Store initial token
        token_manager.save_token('google', 'user1', {
            'access_token': 'old_token',
            'refresh_token': 'old_refresh',
            'expires_in': 120,
            'scopes': ['calendar']
        })
        
        token = token_manager.get_token('google', 'user1')
        result = token_refresher._refresh_token('google', 'user1', token)
        
        assert result is True
        
        # Verify new token was saved
        updated_token = token_manager.get_token('google', 'user1')
        assert updated_token['access_token'] == 'new_access_token'
    
    def test_refresh_token_no_refresh_token(self, token_refresher):
        """Test _refresh_token with no refresh token."""
        token = {
            'access_token': 'test_token',
            'expires_at': datetime.now() - timedelta(minutes=1)
        }
        
        result = token_refresher._refresh_token('google', 'user1', token)
        assert result is False
    
    def test_refresh_token_handler_error(self, token_refresher, token_manager, oauth_registry):
        """Test _refresh_token when handler raises error."""
        # Store token with refresh token
        token_manager.save_token('google', 'user1', {
            'access_token': 'old_token',
            'refresh_token': 'old_refresh',
            'expires_in': 120,
            'scopes': ['calendar']
        })
        
        # Make handler raise error
        handler = Mock()
        handler.refresh_token = Mock(side_effect=Exception("Refresh failed"))
        oauth_registry.get_handler = Mock(return_value=handler)
        
        token = token_manager.get_token('google', 'user1')
        result = token_refresher._refresh_token('google', 'user1', token)
        
        assert result is False


class TestTokenRefreshScheduler:
    """Test TokenRefreshScheduler class."""
    
    def test_initialization(self, token_refresher):
        """Test TokenRefreshScheduler initialization."""
        scheduler = TokenRefreshScheduler(token_refresher, check_interval=60)
        assert scheduler.refresher == token_refresher
        assert scheduler.check_interval == 60
        assert scheduler.running is False
        assert scheduler.thread is None
    
    def test_start_stop(self, token_refresher):
        """Test starting and stopping scheduler."""
        scheduler = TokenRefreshScheduler(token_refresher, check_interval=1)
        
        scheduler.start()
        assert scheduler.running is True
        assert scheduler.thread is not None
        assert scheduler.thread.is_alive()
        
        scheduler.stop()
        assert scheduler.running is False
    
    def test_start_already_running(self, token_refresher):
        """Test starting scheduler when already running."""
        scheduler = TokenRefreshScheduler(token_refresher, check_interval=1)
        
        scheduler.start()
        thread1 = scheduler.thread
        
        # Try starting again
        scheduler.start()
        thread2 = scheduler.thread
        
        # Should be the same thread
        assert thread1 == thread2
        
        scheduler.stop()
    
    @patch('time.sleep', return_value=None)  # Don't actually sleep
    def test_refresh_loop(self, mock_sleep, token_refresher, token_manager):
        """Test refresh loop processes tokens."""
        # Store some tokens
        token_manager.save_token('google', 'user1', {
            'access_token': 'token1',
            'refresh_token': 'refresh1',
            'expires_in': 600,
            'scopes': ['calendar']
        })
        
        scheduler = TokenRefreshScheduler(token_refresher, check_interval=1)
        
        # Mock check_and_refresh_token to track calls
        original_check = token_refresher.check_and_refresh_token
        call_count = {'count': 0}
        
        def mock_check(provider, user_id):
            call_count['count'] += 1
            # Stop after first call to prevent infinite loop
            scheduler.running = False
            return original_check(provider, user_id)
        
        token_refresher.check_and_refresh_token = mock_check
        
        scheduler.start()
        # Wait a bit for the thread to process
        import time
        time.sleep(0.5)
        scheduler.stop()
        
        # Should have processed at least one token
        assert call_count['count'] >= 1
    
    def test_scheduler_with_error_in_loop(self, token_refresher, token_manager):
        """Test scheduler handles errors in refresh loop."""
        scheduler = TokenRefreshScheduler(token_refresher, check_interval=0.1)
        
        # Make list_tokens raise error
        original_list = token_manager.list_tokens
        error_count = {'count': 0}
        
        def mock_list():
            error_count['count'] += 1
            if error_count['count'] == 1:
                raise Exception("List error")
            else:
                scheduler.running = False
                return original_list()
        
        token_manager.list_tokens = mock_list
        
        scheduler.start()
        import time
        time.sleep(0.5)
        scheduler.stop()
        
        # Should have tried at least once
        assert error_count['count'] >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
