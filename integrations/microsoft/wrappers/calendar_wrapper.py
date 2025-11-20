#!/usr/bin/env python3
"""
Microsoft Calendar API Wrapper (Microsoft Graph API)

High-level wrapper with retry logic, rate limiting, and error handling.
Compatible with existing OutlookCalendarIntegration but using Microsoft Graph API v1.0.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
from loguru import logger
import requests


class MicrosoftCalendarWrapper:
    """
    Unified wrapper for Microsoft Calendar (Outlook) via Microsoft Graph API.
    
    Provides high-level methods for calendar operations with:
    - Automatic retry with exponential backoff
    - Rate limiting (10 calls per second per user)
    - Error handling and logging
    - Response normalization
    """
    
    GRAPH_API_BASE = 'https://graph.microsoft.com/v1.0'
    
    def __init__(self, oauth_handler=None):
        """
        Initialize Microsoft Calendar wrapper.
        
        Args:
            oauth_handler: OAuth handler for authentication (MicrosoftOAuthHandler)
        """
        self.oauth_handler = oauth_handler
        self.base_url = f"{self.GRAPH_API_BASE}/me/calendar"
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
            'Content-Type': 'application/json',
            'Prefer': 'outlook.timezone="UTC"'
        }
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)  # 10 calls per second
    def list_calendars(self) -> List[Dict]:
        """
        List all calendars for authenticated user.
        
        Returns:
            List of calendar objects with id, name, etc.
        """
        url = f"{self.GRAPH_API_BASE}/me/calendars"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        
        data = response.json()
        calendars = data.get('value', [])
        
        logger.info(f"Listed {len(calendars)} calendars")
        return calendars
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def create_event(self, calendar_id: str = None, event_data: Dict = None) -> Dict:
        """
        Create a new calendar event.
        
        Args:
            calendar_id: Calendar ID (optional, uses default if not provided)
            event_data: Event data dict in Microsoft Graph format
            
        Returns:
            Created event object
        """
        if calendar_id:
            url = f"{self.GRAPH_API_BASE}/me/calendars/{calendar_id}/events"
        else:
            url = f"{self.GRAPH_API_BASE}/me/events"
        
        response = requests.post(url, json=event_data, headers=self._get_headers())
        response.raise_for_status()
        
        event = response.json()
        logger.info(f"Created event: {event.get('id')} - {event.get('subject')}")
        return event
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def list_events(self, 
                   calendar_id: str = None,
                   start_time: datetime = None, 
                   end_time: datetime = None,
                   max_results: int = 100) -> List[Dict]:
        """
        List events from calendar.
        
        Args:
            calendar_id: Calendar ID (optional)
            start_time: Start of time range
            end_time: End of time range
            max_results: Maximum number of results
            
        Returns:
            List of event objects
        """
        if calendar_id:
            url = f"{self.GRAPH_API_BASE}/me/calendars/{calendar_id}/events"
        else:
            url = f"{self.GRAPH_API_BASE}/me/events"
        
        params = {'$top': max_results}
        
        if start_time and end_time:
            # Use Graph API filter format
            start_str = start_time.isoformat()
            end_str = end_time.isoformat()
            params['$filter'] = f"start/dateTime ge '{start_str}' and end/dateTime le '{end_str}'"
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        
        data = response.json()
        events = data.get('value', [])
        
        logger.info(f"Listed {len(events)} events")
        return events
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def get_event(self, event_id: str) -> Dict:
        """
        Get a specific event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event object
        """
        url = f"{self.GRAPH_API_BASE}/me/events/{event_id}"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        
        event = response.json()
        logger.info(f"Retrieved event: {event.get('id')}")
        return event
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def update_event(self, event_id: str, event_data: Dict) -> Dict:
        """
        Update an existing event.
        
        Args:
            event_id: Event ID to update
            event_data: Updated event data
            
        Returns:
            Updated event object
        """
        url = f"{self.GRAPH_API_BASE}/me/events/{event_id}"
        response = requests.patch(url, json=event_data, headers=self._get_headers())
        response.raise_for_status()
        
        event = response.json()
        logger.info(f"Updated event: {event.get('id')}")
        return event
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event.
        
        Args:
            event_id: Event ID to delete
            
        Returns:
            True if successful
        """
        url = f"{self.GRAPH_API_BASE}/me/events/{event_id}"
        response = requests.delete(url, headers=self._get_headers())
        response.raise_for_status()
        
        logger.info(f"Deleted event: {event_id}")
        return True
    
    def convert_from_google_format(self, google_event: Dict) -> Dict:
        """
        Convert Google Calendar event format to Microsoft Graph format.
        
        Args:
            google_event: Event in Google Calendar format
            
        Returns:
            Event in Microsoft Graph format
        """
        microsoft_event = {
            'subject': google_event.get('summary', ''),
            'body': {
                'contentType': 'HTML',
                'content': google_event.get('description', '')
            },
            'start': {
                'dateTime': google_event['start'].get('dateTime'),
                'timeZone': google_event['start'].get('timeZone', 'UTC')
            },
            'end': {
                'dateTime': google_event['end'].get('dateTime'),
                'timeZone': google_event['end'].get('timeZone', 'UTC')
            }
        }
        
        # Add location if present
        if google_event.get('location'):
            microsoft_event['location'] = {
                'displayName': google_event['location']
            }
        
        # Add attendees if present
        if google_event.get('attendees'):
            microsoft_event['attendees'] = [
                {
                    'emailAddress': {'address': attendee.get('email')},
                    'type': 'required'
                }
                for attendee in google_event['attendees']
            ]
        
        return microsoft_event
