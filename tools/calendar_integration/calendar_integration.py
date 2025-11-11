#!/usr/bin/env python3
"""
Calendar Integration
Integrates with Google Calendar and Outlook Calendar for event management
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalendarEvent:
    """Represents a calendar event"""
    
    def __init__(self, title: str, start: datetime, end: datetime,
                 description: str = "", location: str = "", 
                 calendar_id: str = "primary", event_id: str = None):
        self.title = title
        self.start = start
        self.end = end
        self.description = description
        self.location = location
        self.calendar_id = calendar_id
        self.event_id = event_id
    
    def to_google_format(self) -> Dict[str, Any]:
        """Convert to Google Calendar API format"""
        return {
            "summary": self.title,
            "description": self.description,
            "location": self.location,
            "start": {
                "dateTime": self.start.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": self.end.isoformat(),
                "timeZone": "UTC"
            }
        }
    
    def to_outlook_format(self) -> Dict[str, Any]:
        """Convert to Outlook/Microsoft Graph API format"""
        return {
            "subject": self.title,
            "body": {
                "contentType": "HTML",
                "content": self.description
            },
            "start": {
                "dateTime": self.start.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": self.end.isoformat(),
                "timeZone": "UTC"
            },
            "location": {
                "displayName": self.location
            }
        }


class GoogleCalendarIntegration:
    """Google Calendar integration"""
    
    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path
        self.service = None
        self._authenticated = False
    
    def authenticate(self):
        """Authenticate with Google Calendar API using OAuth 2.0"""
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/calendar']
            
            creds = None
            token_path = 'token.json'
            
            # Load existing credentials
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.credentials_path or not os.path.exists(self.credentials_path):
                        raise FileNotFoundError(
                            "Google Calendar credentials not found. "
                            "Download from Google Cloud Console and set credentials_path"
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=creds)
            self._authenticated = True
            logger.info("Google Calendar authentication successful")
            
        except ImportError:
            raise RuntimeError(
                "Google Calendar libraries not installed. "
                "Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
    
    def create_event(self, event: CalendarEvent) -> str:
        """Create calendar event"""
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first")
        
        event_data = event.to_google_format()
        
        created_event = self.service.events().insert(
            calendarId=event.calendar_id,
            body=event_data
        ).execute()
        
        logger.info(f"Created event: {created_event.get('id')}")
        return created_event.get('id')
    
    def update_event(self, event: CalendarEvent) -> bool:
        """Update existing event"""
        if not self._authenticated or not event.event_id:
            return False
        
        event_data = event.to_google_format()
        
        self.service.events().update(
            calendarId=event.calendar_id,
            eventId=event.event_id,
            body=event_data
        ).execute()
        
        logger.info(f"Updated event: {event.event_id}")
        return True
    
    def delete_event(self, event_id: str, calendar_id: str = "primary") -> bool:
        """Delete event"""
        if not self._authenticated:
            return False
        
        self.service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        logger.info(f"Deleted event: {event_id}")
        return True
    
    def list_events(self, days_ahead: int = 30, calendar_id: str = "primary") -> List[Dict]:
        """List upcoming events"""
        if not self._authenticated:
            return []
        
        now = datetime.utcnow().isoformat() + 'Z'
        end = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            timeMax=end,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    
    def batch_create_events(self, events: List[CalendarEvent]) -> List[str]:
        """Create multiple events in batch"""
        event_ids = []
        
        for event in events:
            try:
                event_id = self.create_event(event)
                event_ids.append(event_id)
            except Exception as e:
                logger.error(f"Error creating event {event.title}: {e}")
                event_ids.append(None)
        
        return event_ids


class OutlookCalendarIntegration:
    """Outlook/Microsoft Graph Calendar integration"""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.getenv("OUTLOOK_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("OUTLOOK_CLIENT_SECRET")
        self.access_token = None
        self._authenticated = False
    
    def authenticate(self):
        """Authenticate with Microsoft Graph API"""
        try:
            import msal
            import requests
            
            # Create MSAL app
            authority = "https://login.microsoftonline.com/common"
            scopes = ["https://graph.microsoft.com/Calendars.ReadWrite"]
            
            app = msal.PublicClientApplication(
                self.client_id,
                authority=authority
            )
            
            # Get token interactively
            result = app.acquire_token_interactive(scopes=scopes)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self._authenticated = True
                logger.info("Outlook Calendar authentication successful")
            else:
                raise RuntimeError(f"Authentication failed: {result.get('error_description')}")
        
        except ImportError:
            raise RuntimeError(
                "Microsoft Graph libraries not installed. "
                "Run: pip install msal requests"
            )
    
    def create_event(self, event: CalendarEvent) -> str:
        """Create calendar event"""
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first")
        
        import requests
        
        endpoint = "https://graph.microsoft.com/v1.0/me/events"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        event_data = event.to_outlook_format()
        
        response = requests.post(endpoint, headers=headers, json=event_data)
        response.raise_for_status()
        
        created_event = response.json()
        logger.info(f"Created Outlook event: {created_event.get('id')}")
        return created_event.get('id')
    
    def update_event(self, event: CalendarEvent) -> bool:
        """Update existing event"""
        if not self._authenticated or not event.event_id:
            return False
        
        import requests
        
        endpoint = f"https://graph.microsoft.com/v1.0/me/events/{event.event_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        event_data = event.to_outlook_format()
        
        response = requests.patch(endpoint, headers=headers, json=event_data)
        response.raise_for_status()
        
        logger.info(f"Updated Outlook event: {event.event_id}")
        return True
    
    def delete_event(self, event_id: str) -> bool:
        """Delete event"""
        if not self._authenticated:
            return False
        
        import requests
        
        endpoint = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        response = requests.delete(endpoint, headers=headers)
        response.raise_for_status()
        
        logger.info(f"Deleted Outlook event: {event_id}")
        return True
    
    def list_events(self, days_ahead: int = 30) -> List[Dict]:
        """List upcoming events"""
        if not self._authenticated:
            return []
        
        import requests
        
        start = datetime.utcnow().isoformat() + 'Z'
        end = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        endpoint = f"https://graph.microsoft.com/v1.0/me/calendarview?startdatetime={start}&enddatetime={end}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        return response.json().get('value', [])


class ConflictDetector:
    """Detects conflicts in calendar events"""
    
    @staticmethod
    def check_time_overlap(event1: CalendarEvent, event2: CalendarEvent) -> bool:
        """Check if two events overlap in time"""
        return (event1.start < event2.end and event1.end > event2.start)
    
    @staticmethod
    def find_conflicts(events: List[CalendarEvent]) -> List[Dict[str, Any]]:
        """Find all conflicting events"""
        conflicts = []
        
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                if ConflictDetector.check_time_overlap(event1, event2):
                    conflicts.append({
                        "event1": {
                            "title": event1.title,
                            "start": event1.start.isoformat(),
                            "end": event1.end.isoformat()
                        },
                        "event2": {
                            "title": event2.title,
                            "start": event2.start.isoformat(),
                            "end": event2.end.isoformat()
                        },
                        "type": "time_overlap"
                    })
        
        return conflicts
    
    @staticmethod
    def suggest_resolution(conflict: Dict[str, Any]) -> List[str]:
        """Suggest resolutions for a conflict"""
        suggestions = []
        
        # Suggest moving one event
        suggestions.append("Move one event to a different time")
        
        # Suggest shortening overlap
        suggestions.append("Shorten one or both events to eliminate overlap")
        
        # Suggest canceling if low priority
        suggestions.append("Cancel the lower priority event")
        
        return suggestions


def test_calendar_integration():
    """Test calendar integration (without actual API calls)"""
    print("Testing Calendar Integration...")
    
    # Create test event
    event = CalendarEvent(
        title="Test Event",
        start=datetime.now(),
        end=datetime.now() + timedelta(hours=1),
        description="This is a test event",
        location="Test Location"
    )
    
    # Test format conversion
    google_format = event.to_google_format()
    outlook_format = event.to_outlook_format()
    
    print(f"✅ Google format: {google_format['summary']}")
    print(f"✅ Outlook format: {outlook_format['subject']}")
    
    # Test conflict detection
    event1 = CalendarEvent("Event 1", datetime.now(), datetime.now() + timedelta(hours=1))
    event2 = CalendarEvent("Event 2", datetime.now() + timedelta(minutes=30), datetime.now() + timedelta(hours=2))
    
    has_conflict = ConflictDetector.check_time_overlap(event1, event2)
    print(f"✅ Conflict detection: {'Conflict found' if has_conflict else 'No conflict'}")
    
    conflicts = ConflictDetector.find_conflicts([event1, event2])
    print(f"✅ Found {len(conflicts)} conflicts")
    
    if conflicts:
        suggestions = ConflictDetector.suggest_resolution(conflicts[0])
        print(f"✅ Suggestions: {len(suggestions)} resolutions")
    
    return True


if __name__ == "__main__":
    success = test_calendar_integration()
    print(f"\n{'✅ Test passed' if success else '❌ Test failed'}")
