"""
Shared pytest fixtures and configuration for all tests.
"""

import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope='session')
def project_root_path():
    """Return the project root path."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary configuration directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def temp_database(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    yield db_path
    # Cleanup happens automatically with tmp_path


@pytest.fixture
def clean_environment(monkeypatch):
    """Clean environment variables for testing."""
    # Remove OAuth credentials if present
    env_vars_to_remove = [
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
        'MICROSOFT_CLIENT_ID',
        'MICROSOFT_CLIENT_SECRET',
        'OPENAI_API_KEY',
        'GITHUB_TOKEN',
    ]
    
    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)
    
    yield
    # Cleanup happens automatically


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    test_vars = {
        'GOOGLE_CLIENT_ID': 'test_google_client_id',
        'GOOGLE_CLIENT_SECRET': 'test_google_client_secret',
        'MICROSOFT_CLIENT_ID': 'test_microsoft_client_id',
        'MICROSOFT_CLIENT_SECRET': 'test_microsoft_client_secret',
    }
    
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    
    yield test_vars


@pytest.fixture
def sample_oauth_config() -> Dict[str, Any]:
    """Provide a sample OAuth configuration for testing."""
    return {
        'provider': 'test_provider',
        'client_id': 'test_client_123',
        'client_secret': 'test_secret_456',
        'redirect_uri': 'http://localhost:8080/callback',
        'scopes': ['scope1', 'scope2'],
    }


@pytest.fixture
def sample_token_response() -> Dict[str, Any]:
    """Provide a sample token response for testing."""
    return {
        'access_token': 'test_access_token_123',
        'token_type': 'Bearer',
        'expires_in': 3600,
        'refresh_token': 'test_refresh_token_456',
        'scope': 'scope1 scope2',
    }


# Pytest configuration hooks

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "oauth: mark test as OAuth-related"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API-related"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security-related"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-add markers based on test path
        test_path = str(item.fspath)
        
        if '/unit/' in test_path:
            item.add_marker(pytest.mark.unit)
        
        if '/integration/' in test_path:
            item.add_marker(pytest.mark.integration)
        
        if 'oauth' in test_path.lower() or 'oauth' in item.name.lower():
            item.add_marker(pytest.mark.oauth)
        
        if 'api' in test_path.lower() or 'api' in item.name.lower():
            item.add_marker(pytest.mark.api)
        
        if 'security' in test_path.lower() or 'security' in item.name.lower():
            item.add_marker(pytest.mark.security)
