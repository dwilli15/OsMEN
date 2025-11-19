"""
OAuth Provider Registry.

Centralized registry for managing OAuth provider implementations.
Supports provider registration, discovery, and factory pattern for
creating OAuth handlers.
"""

from typing import Dict, Type, Optional, Any, List
from loguru import logger

from .oauth_handler import OAuthHandler


class OAuthProviderRegistry:
    """
    Registry for OAuth provider implementations.
    
    Manages registration and instantiation of OAuth handlers for
    different providers (Google, Microsoft, GitHub, etc.).
    """
    
    def __init__(self):
        """Initialize the OAuth provider registry."""
        self._providers: Dict[str, Type[OAuthHandler]] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        logger.info("OAuthProviderRegistry initialized")
    
    def register(self, provider_name: str, handler_class: Type[OAuthHandler],
                 config: Optional[Dict[str, Any]] = None) -> None:
        """
        Register an OAuth provider handler.
        
        Args:
            provider_name: Unique name for the provider (e.g., "google", "microsoft")
            handler_class: OAuthHandler subclass for this provider
            config: Optional default configuration for this provider
            
        Raises:
            ValueError: If provider is already registered or handler is invalid
        """
        if not issubclass(handler_class, OAuthHandler):
            raise ValueError(f"{handler_class} must be a subclass of OAuthHandler")
        
        if provider_name in self._providers:
            logger.warning(f"Provider '{provider_name}' already registered, overwriting")
        
        self._providers[provider_name] = handler_class
        
        if config:
            self._configs[provider_name] = config
        
        logger.info(f"Registered OAuth provider: {provider_name}")
    
    def unregister(self, provider_name: str) -> None:
        """
        Unregister an OAuth provider.
        
        Args:
            provider_name: Name of the provider to unregister
        """
        if provider_name in self._providers:
            del self._providers[provider_name]
            if provider_name in self._configs:
                del self._configs[provider_name]
            logger.info(f"Unregistered OAuth provider: {provider_name}")
        else:
            logger.warning(f"Provider '{provider_name}' not found in registry")
    
    def get_handler(self, provider_name: str, config: Optional[Dict[str, Any]] = None) -> OAuthHandler:
        """
        Get an OAuth handler instance for a provider.
        
        Args:
            provider_name: Name of the registered provider
            config: Configuration for the handler (uses default if not provided)
            
        Returns:
            Instantiated OAuthHandler for the provider
            
        Raises:
            ValueError: If provider not found or config missing
        """
        if provider_name not in self._providers:
            available = ', '.join(self._providers.keys())
            raise ValueError(
                f"Provider '{provider_name}' not found. "
                f"Available providers: {available or 'none'}"
            )
        
        handler_class = self._providers[provider_name]
        
        # Use provided config or default config
        handler_config = config if config is not None else self._configs.get(provider_name)
        
        if handler_config is None:
            raise ValueError(
                f"No configuration provided for provider '{provider_name}' "
                "and no default configuration found"
            )
        
        logger.info(f"Creating OAuth handler for provider: {provider_name}")
        return handler_class(handler_config)
    
    def list_providers(self) -> List[str]:
        """
        List all registered provider names.
        
        Returns:
            List of provider names
        """
        return list(self._providers.keys())
    
    def is_registered(self, provider_name: str) -> bool:
        """
        Check if a provider is registered.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            True if provider is registered, False otherwise
        """
        return provider_name in self._providers
    
    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """
        Get information about a registered provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Dictionary with provider information
            
        Raises:
            ValueError: If provider not found
        """
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        
        handler_class = self._providers[provider_name]
        has_config = provider_name in self._configs
        
        return {
            'name': provider_name,
            'handler_class': handler_class.__name__,
            'has_default_config': has_config,
            'module': handler_class.__module__
        }


# Global registry instance
_global_registry = OAuthProviderRegistry()


def get_registry() -> OAuthProviderRegistry:
    """
    Get the global OAuth provider registry.
    
    Returns:
        Global OAuthProviderRegistry instance
    """
    return _global_registry


def register_provider(provider_name: str, handler_class: Type[OAuthHandler],
                      config: Optional[Dict[str, Any]] = None) -> None:
    """
    Register a provider with the global registry.
    
    Args:
        provider_name: Unique name for the provider
        handler_class: OAuthHandler subclass
        config: Optional default configuration
    """
    _global_registry.register(provider_name, handler_class, config)


def get_oauth_handler(provider_name: str, config: Optional[Dict[str, Any]] = None) -> OAuthHandler:
    """
    Get an OAuth handler from the global registry.
    
    Args:
        provider_name: Name of the provider
        config: Configuration for the handler
        
    Returns:
        Instantiated OAuthHandler
    """
    return _global_registry.get_handler(provider_name, config)
