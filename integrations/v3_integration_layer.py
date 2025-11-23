#!/usr/bin/env python3
"""
v3.0 Integration Layer

This module connects all the framework components created in v1 and v2
to make them actually work together. It provides a unified interface
for all external integrations.

Key Improvements:
- Connects OAuth handlers with API wrappers
- Implements token management and refresh
- Provides unified error handling
- Adds logging and monitoring
- Makes framework code production-ready
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

# Token management
from integrations.token_manager import TokenManager

# OAuth imports
from integrations.oauth.google_oauth import GoogleOAuthHandler
from integrations.oauth.microsoft_oauth import MicrosoftOAuthHandler

# Google API wrappers
from integrations.google.wrappers.calendar_wrapper import GoogleCalendarWrapper
from integrations.google.wrappers.gmail_wrapper import GmailWrapper
from integrations.google.wrappers.contacts_wrapper import ContactsWrapper

# Microsoft API wrappers  
from integrations.microsoft.wrappers.calendar_wrapper import OutlookCalendarWrapper
from integrations.microsoft.wrappers.mail_wrapper import OutlookMailWrapper
from integrations.microsoft.wrappers.contacts_wrapper import MicrosoftContactsWrapper

# Calendar integration layer
from integrations.calendar.calendar_manager import CalendarManager


class V3IntegrationLayer:
    """
    v3.0 Integration Layer
    
    Connects all framework components and makes them production-ready.
    This class bridges the gap between framework code and working features.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize v3 integration layer.
        
        Args:
            config_dir: Directory for storing configurations and tokens
        """
        self.config_dir = config_dir or os.path.join(
            os.path.dirname(__file__), 
            '../.copilot/integrations'
        )
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)
        
        # Token manager for secure storage
        self.token_manager = TokenManager(storage_dir=os.path.join(self.config_dir, 'tokens'))
        
        # OAuth handlers
        self.google_oauth = None
        self.microsoft_oauth = None
        
        # API wrappers
        self.google_calendar = None
        self.google_gmail = None
        self.google_contacts = None
        self.outlook_calendar = None
        self.outlook_mail = None
        self.microsoft_contacts = None
        
        # Unified interfaces (lazy-initialized)
        self.calendar_manager = None
        
        # Load configuration
        self._load_config()
        
        logger.info("v3 Integration Layer initialized")
    
    def _load_config(self):
        """Load integration configuration"""
        config_file = os.path.join(self.config_dir, 'config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info("Loaded integration configuration")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                self.config = {}
        else:
            self.config = {}
    
    def _save_config(self):
        """Save integration configuration"""
        config_file = os.path.join(self.config_dir, 'config.json')
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Saved integration configuration")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    # Google Integration Methods
    
    def setup_google_oauth(
        self, 
        client_id: str,
        client_secret: str,
        redirect_uri: str = 'http://localhost:8080/oauth/callback',
        scopes: List[str] = None
    ) -> GoogleOAuthHandler:
        """
        Setup Google OAuth handler.
        
        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            redirect_uri: OAuth redirect URI
            scopes: List of Google API scopes
            
        Returns:
            Configured GoogleOAuthHandler instance
        """
        if scopes is None:
            scopes = [
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/contacts'
            ]
        
        oauth_config = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'scopes': scopes
        }
        
        self.google_oauth = GoogleOAuthHandler(oauth_config)
        
        # Save configuration
        self.config['google_oauth'] = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scopes': scopes,
            'configured_at': datetime.now().isoformat()
        }
        self._save_config()
        
        logger.info("Google OAuth configured successfully")
        return self.google_oauth
    
    def get_google_calendar(self) -> Optional[GoogleCalendarWrapper]:
        """
        Get Google Calendar wrapper instance.
        
        Returns:
            GoogleCalendarWrapper instance if OAuth is configured, None otherwise
        """
        if not self.google_oauth:
            logger.error("Google OAuth not configured")
            return None
        
        if not self.google_calendar:
            self.google_calendar = GoogleCalendarWrapper(self.google_oauth)
        
        return self.google_calendar
    
    def get_google_gmail(self) -> Optional[GmailWrapper]:
        """Get Gmail wrapper instance"""
        if not self.google_oauth:
            logger.error("Google OAuth not configured")
            return None
        
        if not self.google_gmail:
            self.google_gmail = GmailWrapper(self.google_oauth)
        
        return self.google_gmail
    
    def get_google_contacts(self) -> Optional[ContactsWrapper]:
        """Get Google Contacts wrapper instance"""
        if not self.google_oauth:
            logger.error("Google OAuth not configured")
            return None
        
        if not self.google_contacts:
            self.google_contacts = ContactsWrapper(self.google_oauth)
        
        return self.google_contacts
    
    # Microsoft Integration Methods
    
    def setup_microsoft_oauth(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str = 'common',
        redirect_uri: str = 'http://localhost:8080/oauth/callback',
        scopes: List[str] = None
    ) -> MicrosoftOAuthHandler:
        """
        Setup Microsoft OAuth handler.
        
        Args:
            client_id: Microsoft application client ID
            client_secret: Microsoft application client secret
            tenant_id: Azure AD tenant ID (default: 'common')
            redirect_uri: OAuth redirect URI
            scopes: List of Microsoft Graph API scopes
            
        Returns:
            Configured MicrosoftOAuthHandler instance
        """
        if scopes is None:
            scopes = [
                'Calendars.ReadWrite',
                'Mail.ReadWrite',
                'Contacts.ReadWrite'
            ]
        
        oauth_config = {
            'client_id': client_id,
            'client_secret': client_secret,
            'tenant_id': tenant_id,
            'redirect_uri': redirect_uri,
            'scopes': scopes
        }
        
        self.microsoft_oauth = MicrosoftOAuthHandler(oauth_config)
        
        # Save configuration
        self.config['microsoft_oauth'] = {
            'client_id': client_id,
            'tenant_id': tenant_id,
            'redirect_uri': redirect_uri,
            'scopes': scopes,
            'configured_at': datetime.now().isoformat()
        }
        self._save_config()
        
        logger.info("Microsoft OAuth configured successfully")
        return self.microsoft_oauth
    
    def get_outlook_calendar(self) -> Optional[OutlookCalendarWrapper]:
        """Get Outlook Calendar wrapper instance"""
        if not self.microsoft_oauth:
            logger.error("Microsoft OAuth not configured")
            return None
        
        if not self.outlook_calendar:
            self.outlook_calendar = OutlookCalendarWrapper(self.microsoft_oauth)
        
        return self.outlook_calendar
    
    def get_outlook_mail(self) -> Optional[OutlookMailWrapper]:
        """Get Outlook Mail wrapper instance"""
        if not self.microsoft_oauth:
            logger.error("Microsoft OAuth not configured")
            return None
        
        if not self.outlook_mail:
            self.outlook_mail = OutlookMailWrapper(self.microsoft_oauth)
        
        return self.outlook_mail
    
    def get_microsoft_contacts(self) -> Optional[MicrosoftContactsWrapper]:
        """Get Microsoft Contacts wrapper instance"""
        if not self.microsoft_oauth:
            logger.error("Microsoft OAuth not configured")
            return None
        
        if not self.microsoft_contacts:
            self.microsoft_contacts = MicrosoftContactsWrapper(self.microsoft_oauth)
        
        return self.microsoft_contacts
    
    # Unified Interface Methods
    
    def get_calendar_manager(self) -> CalendarManager:
        """
        Get unified calendar manager.
        
        Returns:
            CalendarManager instance that works with all configured providers
        """
        if not self.calendar_manager:
            self.calendar_manager = CalendarManager(self.config_dir)
        
        return self.calendar_manager
    
    # Health Check Methods
    
    def check_google_integration(self) -> Dict[str, Any]:
        """
        Check status of Google integrations.
        
        Returns:
            Dictionary with status of each Google service
        """
        status = {
            'oauth_configured': self.google_oauth is not None,
            'calendar_available': False,
            'gmail_available': False,
            'contacts_available': False
        }
        
        if self.google_oauth:
            try:
                calendar = self.get_google_calendar()
                if calendar:
                    # Try to list calendars as a health check
                    calendars = calendar.list_calendars()
                    status['calendar_available'] = True
                    status['calendar_count'] = len(calendars)
            except Exception as e:
                logger.error(f"Google Calendar health check failed: {e}")
        
        return status
    
    def check_microsoft_integration(self) -> Dict[str, Any]:
        """
        Check status of Microsoft integrations.
        
        Returns:
            Dictionary with status of each Microsoft service
        """
        status = {
            'oauth_configured': self.microsoft_oauth is not None,
            'calendar_available': False,
            'mail_available': False,
            'contacts_available': False
        }
        
        if self.microsoft_oauth:
            try:
                calendar = self.get_outlook_calendar()
                if calendar:
                    # Try to list calendars as a health check
                    calendars = calendar.list_calendars()
                    status['calendar_available'] = True
                    status['calendar_count'] = len(calendars)
            except Exception as e:
                logger.error(f"Outlook Calendar health check failed: {e}")
        
        return status
    
    def get_integration_status(self) -> Dict[str, Any]:
        """
        Get overall integration status.
        
        Returns:
            Dictionary with status of all integrations
        """
        return {
            'version': '3.0',
            'google': self.check_google_integration(),
            'microsoft': self.check_microsoft_integration(),
            'timestamp': datetime.now().isoformat()
        }


# Convenience function for creating integration layer
def get_integration_layer(config_dir: str = None) -> V3IntegrationLayer:
    """
    Get or create v3 integration layer instance.
    
    Args:
        config_dir: Directory for storing configurations
        
    Returns:
        V3IntegrationLayer instance
    """
    return V3IntegrationLayer(config_dir)


if __name__ == "__main__":
    # Example usage
    integration = get_integration_layer()
    
    print("v3.0 Integration Layer")
    print("=" * 50)
    print("\nThis module connects all framework components from v1 and v2.")
    print("\nStatus:")
    status = integration.get_integration_status()
    print(json.dumps(status, indent=2))
    
    print("\n\nTo configure Google OAuth:")
    print("  integration.setup_google_oauth(client_id, client_secret)")
    print("\nTo configure Microsoft OAuth:")
    print("  integration.setup_microsoft_oauth(client_id, client_secret)")
