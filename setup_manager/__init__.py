"""
Setup Manager Module
Centralized initialization and configuration for OsMEN agents
"""

from .manager import SetupManager
from .config import ConfigManager

__all__ = ['SetupManager', 'ConfigManager']
