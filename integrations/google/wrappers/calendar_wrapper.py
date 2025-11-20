#!/usr/bin/env python3
"""
Google Calendar API Wrapper
High-level wrapper with retry logic, rate limiting, and error handling
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
from loguru import logger
import requests


class GoogleCalendarWrapper:
    """
    Unified wrapper for Google Calendar API.
    
    Provides high-level methods for calendar operations with:
    - Automatic retry with exponential backoff
    - Rate limiting (10 calls per second per user)
    - Error handling and logging
    - Response normalization
    """
    
    def __init__(self, oauth_handler=None):
        """
        Initialize Google Calendar wrapper.
        
        Args:
            oauth_handler: OAuth handler for authentication (GoogleOAuthHandler)
        """
        self.oauth_handler = oauth_handler
        self.base_url = 'https://www.googleapis.com/calendar/v3'
        self._access_token = None
    
    def _get_access_token(self) -> str:
        """Get current access token from OAuth handler"""
        if self.oauth_handler:
            # Get token from OAuth handler
            token_data = self.oauth_handler.get_token()
            return token_data.get('access_token')
        return self._access_token
    
    def _get_headers(self) -> Dict:
        """Get request headers with authentication"""
        token = self._get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)  # 10 calls per second
    def list_calendars(self) -> List[Dict]:
        """
        List all calendars for authenticated user.
        
        Returns:
            List of calendar objects with id, summary, description, etc.
        """
        url = f"{self.base_url}/users/me/calendarList"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        
        data = response.json()
        calendars = data.get('items', [])
        
        logger.info(f"Listed {len(calendars)} calendars")
        return calendars
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def create_event(self, calendar_id: str, event_data: Dict) -> Dict:
        """
        Create a new calendar event.
        
        Args:
            calendar_id: Calendar ID (use 'primary' for main calendar)
            event_data: Event data dict
            
        Returns:
            Created event object with id, htmlLink, etc.
        """
        url = f"{self.base_url}/calendars/{calendar_id}/events"
        response = requests.post(url, json=event_data, headers=self._get_headers())
        response.raise_for_status()
        
        event = response.json()
        logger.info(f"Created event: {event.get('id')} - {event.get('summary')}")
        return event
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def get_event(self, calendar_id: str, event_id: str) -> Dict:
        """Get a specific event."""
        url = f"{self.base_url}/calendars/{calendar_id}/events/{event_id}"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def update_event(self, calendar_id: str, event_id: str, event_data: Dict) -> Dict:
        """Update an existing event."""
        url = f"{self.base_url}/calendars/{calendar_id}/events/{event_id}"
        response = requests.put(url, json=event_data, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete an event."""
        url = f"{self.base_url}/calendars/{calendar_id}/events/{event_id}"
        response = requests.delete(url, headers=self._get_headers())
        response.raise_for_status()
        logger.info(f"Deleted event: {event_id}")
        return True
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def list_events(self, calendar_id: str, start_date: datetime = None, 
                   end_date: datetime = None, max_results: int = 100) -> List[Dict]:
        """List events in date range with automatic pagination."""
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        url = f"{self.base_url}/calendars/{calendar_id}/events"
        params = {
            'timeMin': start_date.isoformat() + 'Z',
            'timeMax': end_date.isoformat() + 'Z',
            'maxResults': max_results,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        
        all_events = []
        page_token = None
        
        while True:
            if page_token:
                params['pageToken'] = page_token
            
            response = requests.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            events = data.get('items', [])
            all_events.extend(events)
            
            page_token = data.get('nextPageToken')
            if not page_token or len(all_events) >= max_results:
                break
        
        logger.info(f"Listed {len(all_events)} events")
        return all_events[:max_results]
