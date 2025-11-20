"""API response normalizer for consistent error handling"""
from datetime import datetime
from typing import Dict, Any, Optional

def normalize_response(
    response: Any,
    api_type: str = 'generic',
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Normalize API response to common format.
    
    Args:
        response: Raw API response
        api_type: Type of API (google, microsoft, etc.)
        metadata: Additional metadata
    
    Returns:
        Normalized response dictionary
    """
    return {
        'success': True,
        'data': response,
        'api_type': api_type,
        'timestamp': datetime.now().isoformat(),
        'metadata': metadata or {}
    }

def normalize_error(
    error: Exception,
    api_type: str = 'generic',
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Normalize API error to common format.
    
    Args:
        error: Exception object
        api_type: Type of API
        context: Additional error context
    
    Returns:
        Normalized error dictionary
    """
    return {
        'success': False,
        'error': str(error),
        'error_type': type(error).__name__,
        'error_code': getattr(error, 'code', None),
        'api_type': api_type,
        'timestamp': datetime.now().isoformat(),
        'context': context or {}
    }
