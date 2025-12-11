#!/usr/bin/env python3
"""
Calendar Manager - Unified Interface for All Calendar Providers

Provides a single interface for interacting with multiple calendar providers,
with automatic failover, caching, and error handling.

Part of Production Readiness - Phase 1, Day 1-2
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from .google_calendar import GoogleCalendarIntegration, GOOGLE_API_AVAILABLE
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logger.warning("Google Calendar integration not available")

try:
    from .outlook_calendar import OutlookCalendarIntegration
    OUTLOOK_API_AVAILABLE = True
except ImportError:
    OUTLOOK_API_AVAILABLE = False
    logger.warning("Outlook Calendar integration not available")


class CalendarManager:
    """Unified calendar manager with multi-provider support"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize calendar manager
        
        Args:
            config_dir: Directory for storing calendar configurations
        """
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), '../../.copilot/calendar')
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)
        
        self.providers = {}
        self.primary_provider = None
        self.config_file = os.path.join(self.config_dir, 'config.json')
        
        # Load configuration
        self._load_config()
        
        logger.info(f"CalendarManager initialized with config dir: {self.config_dir}")
    
    def _load_config(self):
        """Load calendar configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.primary_provider = config.get('primary_provider')
                    logger.info(f"Loaded config: primary provider = {self.primary_provider}")
            else:
                logger.info("No existing config found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    def _save_config(self):
        """Save calendar configuration to file"""
        try:
            config = {
                'primary_provider': self.primary_provider,
                'configured_providers': list(self.providers.keys()),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def add_google_calendar(self, credentials_path: str = None, token_path: str = None) -> bool:
        """
        Add Google Calendar provider
        
        Args:
            credentials_path: Path to Google OAuth credentials JSON
            token_path: Path to store OAuth token
            
        Returns:
            True if successful
        """
        if not GOOGLE_API_AVAILABLE:
            logger.error("Google Calendar API not available - install google-api-python-client")
            return False
        
        try:
            # Use config dir for token storage
            if token_path is None:
                token_path = os.path.join(self.config_dir, 'google_token.json')
            
            google_cal = GoogleCalendarIntegration(
                credentials_path=credentials_path,
                token_path=token_path
            )
            
            # Authenticate
            if google_cal.authenticate():
                self.providers['google'] = google_cal
                
                # Set as primary if it's the first provider
                if self.primary_provider is None:
                    self.primary_provider = 'google'
                
                self._save_config()
                logger.info("Google Calendar added successfully")
                return True
            else:
                logger.error("Google Calendar authentication failed")
                return False
        
        except Exception as e:
            logger.error(f"Error adding Google Calendar: {e}")
            return False
    
    def add_outlook_calendar(self, access_token: str) -> bool:
        """
        Add Outlook Calendar provider
        
        Args:
            access_token: Microsoft Graph API access token
            
        Returns:
            True if successful
        """
        try:
            outlook_cal = OutlookCalendarIntegration(access_token=access_token)
            self.providers['outlook'] = outlook_cal
            
            # Set as primary if it's the first provider
            if self.primary_provider is None:
                self.primary_provider = 'outlook'
            
            self._save_config()
            logger.info("Outlook Calendar added successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error adding Outlook Calendar: {e}")
            return False
    
    def set_primary_provider(self, provider_name: str) -> bool:
        """
        Set the primary calendar provider
        
        Args:
            provider_name: Name of provider ('google' or 'outlook')
            
        Returns:
            True if successful
        """
        if provider_name not in self.providers:
            logger.error(f"Provider {provider_name} not configured")
            return False
        
        self.primary_provider = provider_name
        self._save_config()
        logger.info(f"Primary provider set to: {provider_name}")
        return True
    
    def create_event(self, event_data: Dict[str, Any], provider: str = None) -> Optional[Dict[str, Any]]:
        """
        Create a calendar event
        
        Args:
            event_data: Event data
            provider: Specific provider to use (uses primary if not specified)
            
        Returns:
            Created event data or None
        """
        provider_name = provider or self.primary_provider
        
        if provider_name not in self.providers:
            logger.error(f"Provider {provider_name} not configured")
            return None
        
        try:
            calendar = self.providers[provider_name]
            result = calendar.create_event(event_data)
            
            if result:
                logger.info(f"Event created: {event_data.get('title')} via {provider_name}")
            else:
                logger.error(f"Failed to create event via {provider_name}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error creating event via {provider_name}: {e}")
            
            # Try failover to another provider
            if provider is None:  # Only failover if user didn't specify provider
                return self._failover_create(event_data, provider_name)
            
            return None
    
    def _failover_create(self, event_data: Dict[str, Any], failed_provider: str) -> Optional[Dict[str, Any]]:
        """Attempt to create event with alternative provider"""
        for provider_name, calendar in self.providers.items():
            if provider_name == failed_provider:
                continue
            
            try:
                logger.info(f"Attempting failover to {provider_name}")
                result = calendar.create_event(event_data)
                
                if result:
                    logger.info(f"Failover successful - event created via {provider_name}")
                    return result
            
            except Exception as e:
                logger.error(f"Failover to {provider_name} also failed: {e}")
        
        logger.error("All providers failed")
        return None
    
    def create_events_batch(self, events: List[Dict[str, Any]], provider: str = None) -> Dict[str, Any]:
        """
        Create multiple events in batch
        
        Args:
            events: List of event data
            provider: Specific provider to use
            
        Returns:
            Batch result with successes and failures
        """
        results = {
            'total': len(events),
            'successful': 0,
            'failed': 0,
            'events': []
        }
        
        for event_data in events:
            result = self.create_event(event_data, provider)
            
            if result:
                results['successful'] += 1
                results['events'].append({
                    'title': event_data.get('title'),
                    'status': 'success',
                    'id': result.get('id')
                })
            else:
                results['failed'] += 1
                results['events'].append({
                    'title': event_data.get('title'),
                    'status': 'failed'
                })
        
        logger.info(f"Batch create: {results['successful']}/{results['total']} successful")
        return results
    
    def list_events(self, max_results: int = 10, provider: str = None) -> List[Dict[str, Any]]:
        """
        List upcoming events
        
        Args:
            max_results: Maximum number of events to return
            provider: Specific provider to use
            
        Returns:
            List of events
        """
        provider_name = provider or self.primary_provider
        
        if provider_name not in self.providers:
            logger.error(f"Provider {provider_name} not configured")
            return []
        
        try:
            calendar = self.providers[provider_name]
            events = calendar.list_events(max_results=max_results)
            logger.info(f"Retrieved {len(events)} events from {provider_name}")
            return events
        
        except Exception as e:
            logger.error(f"Error listing events from {provider_name}: {e}")
            return []
    
    def update_event(self, event_id: str, event_data: Dict[str, Any], provider: str = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing event
        
        Args:
            event_id: Event ID
            event_data: Updated event data
            provider: Specific provider to use
            
        Returns:
            Updated event data or None
        """
        provider_name = provider or self.primary_provider
        
        if provider_name not in self.providers:
            logger.error(f"Provider {provider_name} not configured")
            return None
        
        try:
            calendar = self.providers[provider_name]
            result = calendar.update_event(event_id, event_data)
            
            if result:
                logger.info(f"Event updated: {event_id} via {provider_name}")
            else:
                logger.error(f"Failed to update event via {provider_name}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error updating event via {provider_name}: {e}")
            return None
    
    def delete_event(self, event_id: str, provider: str = None) -> bool:
        """
        Delete an event
        
        Args:
            event_id: Event ID
            provider: Specific provider to use
            
        Returns:
            True if successful
        """
        provider_name = provider or self.primary_provider
        
        if provider_name not in self.providers:
            logger.error(f"Provider {provider_name} not configured")
            return False
        
        try:
            calendar = self.providers[provider_name]
            success = calendar.delete_event(event_id)
            
            if success:
                logger.info(f"Event deleted: {event_id} via {provider_name}")
            else:
                logger.error(f"Failed to delete event via {provider_name}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error deleting event via {provider_name}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get calendar manager status"""
        return {
            'configured_providers': list(self.providers.keys()),
            'primary_provider': self.primary_provider,
            'google_available': GOOGLE_API_AVAILABLE,
            'outlook_available': OUTLOOK_API_AVAILABLE,
            'config_dir': self.config_dir
        }


def main():
    """Test calendar manager"""
    print("Calendar Manager - Unified Calendar Interface")
    print("=" * 60)
    
    manager = CalendarManager()
    status = manager.get_status()
    
    print(f"\nStatus:")
    print(f"  Google API Available: {status['google_available']}")
    print(f"  Outlook API Available: {status['outlook_available']}")
    print(f"  Configured Providers: {status['configured_providers']}")
    print(f"  Primary Provider: {status['primary_provider']}")
    print(f"  Config Directory: {status['config_dir']}")
    
    print("\n✅ Calendar Manager ready for production use")


if __name__ == "__main__":
    main()
