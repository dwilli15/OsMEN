"""
Comprehensive tests for OAuth Registry to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from integrations.oauth.oauth_registry import OAuthProviderRegistry, get_registry, register_provider, get_oauth_handler
from integrations.oauth.google_oauth import GoogleOAuthHandler
from integrations.oauth.oauth_handler import OAuthHandler


@pytest.fixture
def empty_registry():
    """Create empty OAuth registry."""
    return OAuthProviderRegistry()


@pytest.fixture
def populated_registry():
    """Create registry with providers."""
    registry = OAuthProviderRegistry()
    
    google_config = {
        'client_id': 'google_client_id',
        'client_secret': 'google_secret',
        'redirect_uri': 'http://localhost:8080/callback',
        'scopes': ['calendar', 'gmail']
    }
    
    github_config = {
        'client_id': 'github_client_id',
        'client_secret': 'github_secret',
        'redirect_uri': 'http://localhost:8080/callback',
        'scopes': ['user', 'repo']
    }
    
    registry.register('google', GoogleOAuthHandler, google_config)
    registry.register('github', GoogleOAuthHandler, github_config)  # Use GoogleOAuthHandler for both
    
    return registry


class TestOAuthProviderRegistry:
    """Test OAuth Provider Registry."""
    
    def test_initialization(self, empty_registry):
        """Test registry initialization."""
        assert empty_registry._providers == {}
        assert empty_registry._configs == {}
    
    def test_register_provider(self, empty_registry):
        """Test registering a provider."""
        config = {
            'client_id': 'test_id',
            'client_secret': 'test_secret',
            'redirect_uri': 'http://localhost',
            'scopes': []
        }
        
        empty_registry.register('test_provider', GoogleOAuthHandler, config)
        
        assert 'test_provider' in empty_registry._providers
        assert 'test_provider' in empty_registry._configs
        assert empty_registry._providers['test_provider'] == GoogleOAuthHandler
        assert empty_registry._configs['test_provider'] == config
    
    def test_register_without_config(self, empty_registry):
        """Test registering provider without config."""
        empty_registry.register('test_provider', GoogleOAuthHandler)
        
        assert 'test_provider' in empty_registry._providers
        assert 'test_provider' not in empty_registry._configs
    
    def test_register_duplicate_provider_overwrites(self, populated_registry):
        """Test that registering duplicate provider overwrites with warning."""
        config = {'client_id': 'new_id', 'client_secret': 'secret', 'redirect_uri': 'http://localhost', 'scopes': []}
        
        # Should overwrite without error
        populated_registry.register('google', GoogleOAuthHandler, config)
        
        assert populated_registry._configs['google']['client_id'] == 'new_id'
    
    def test_unregister_provider(self, populated_registry):
        """Test unregistering a provider."""
        populated_registry.unregister('google')
        
        assert 'google' not in populated_registry._providers
        assert 'google' not in populated_registry._configs
    
    def test_unregister_nonexistent_provider(self, empty_registry):
        """Test unregistering non-existent provider."""
        # Should not raise error, just logs warning
        empty_registry.unregister('nonexistent')
    
    def test_get_handler_with_config(self, populated_registry):
        """Test getting handler with default config."""
        handler = populated_registry.get_handler('google')
        
        assert isinstance(handler, GoogleOAuthHandler)
        assert handler.client_id == 'google_client_id'
    
    def test_get_handler_with_custom_config(self, populated_registry):
        """Test getting handler with custom config."""
        custom_config = {
            'client_id': 'custom_id',
            'client_secret': 'custom_secret',
            'redirect_uri': 'http://localhost:9000/callback',
            'scopes': ['drive']
        }
        
        handler = populated_registry.get_handler('google', custom_config)
        
        assert isinstance(handler, GoogleOAuthHandler)
        assert handler.client_id == 'custom_id'
    
    def test_get_handler_nonexistent(self, empty_registry):
        """Test getting handler for non-existent provider."""
        with pytest.raises(ValueError) as exc_info:
            empty_registry.get_handler('nonexistent')
        
        assert 'not found' in str(exc_info.value).lower()
    
    def test_get_handler_no_config(self, empty_registry):
        """Test getting handler without config."""
        empty_registry.register('test', GoogleOAuthHandler)
        
        with pytest.raises(ValueError) as exc_info:
            empty_registry.get_handler('test')
        
        assert 'no configuration' in str(exc_info.value).lower()
    
    def test_list_providers(self, populated_registry):
        """Test listing all providers."""
        providers = populated_registry.list_providers()
        
        assert 'google' in providers
        assert 'github' in providers
        assert len(providers) == 2
    
    def test_list_providers_empty(self, empty_registry):
        """Test listing providers when registry is empty."""
        providers = empty_registry.list_providers()
        
        assert providers == []
    
    def test_is_registered_true(self, populated_registry):
        """Test checking if provider is registered."""
        assert populated_registry.is_registered('google') is True
        assert populated_registry.is_registered('github') is True
    
    def test_is_registered_false(self, populated_registry):
        """Test checking if non-existent provider is registered."""
        assert populated_registry.is_registered('nonexistent2') is False
        assert populated_registry.is_registered('nonexistent') is False
    
    def test_get_provider_info(self, populated_registry):
        """Test getting provider information."""
        info = populated_registry.get_provider_info('google')
        
        assert info['name'] == 'google'
        assert info['handler_class'] == 'GoogleOAuthHandler'
        assert info['has_default_config'] is True
        assert 'module' in info
    
    def test_get_provider_info_nonexistent(self, empty_registry):
        """Test getting info for non-existent provider."""
        with pytest.raises(ValueError) as exc_info:
            empty_registry.get_provider_info('nonexistent')
        
        assert 'not found' in str(exc_info.value).lower()
    
    def test_register_with_invalid_handler_class(self, empty_registry):
        """Test registering with invalid handler class."""
        # Create a class that doesn't inherit from OAuthHandler
        class InvalidHandler:
            pass
        
        config = {'client_id': 'test', 'client_secret': 'secret', 'redirect_uri': 'http://localhost', 'scopes': []}
        
        with pytest.raises(ValueError) as exc_info:
            empty_registry.register('invalid', InvalidHandler, config)
        
        assert 'must be a subclass of OAuthHandler' in str(exc_info.value)
    
    def test_global_registry(self):
        """Test global registry singleton."""
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert registry1 is registry2
    
    def test_register_provider_global(self):
        """Test registering via global function."""
        config = {
            'client_id': 'test',
            'client_secret': 'secret',
            'redirect_uri': 'http://localhost',
            'scopes': []
        }
        
        register_provider('test_global', GoogleOAuthHandler, config)
        
        registry = get_registry()
        assert registry.is_registered('test_global')
        
        # Clean up
        registry.unregister('test_global')
    
    def test_get_oauth_handler_global(self):
        """Test getting handler via global function."""
        config = {
            'client_id': 'test',
            'client_secret': 'secret',
            'redirect_uri': 'http://localhost',
            'scopes': []
        }
        
        registry = get_registry()
        registry.register('test_handler', GoogleOAuthHandler, config)
        
        handler = get_oauth_handler('test_handler')
        
        assert isinstance(handler, GoogleOAuthHandler)
        
        # Clean up
        registry.unregister('test_handler')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

