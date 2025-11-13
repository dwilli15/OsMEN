#!/usr/bin/env python3
"""
Google Calendar Integration

Manages events in Google Calendar.
Part of v1.4.0 - Syllabus Parser & Calendar Foundation.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


class GoogleCalendarIntegration:
    """Integration with Google Calendar API"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_path: str = None, token_path: str = None):
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API libraries not installed")
        
        self.credentials_path = credentials_path or os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        self.token_path = token_path or os.getenv('GOOGLE_TOKEN_PATH', 'token.json')
        self.service = None
        self.calendar_id = 'primary'
    
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API"""
        creds = None
        
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
        return True
    
    def create_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new calendar event"""
        if not self.service:
            return None
        
        google_event = self._convert_to_google_format(event_data)
        
        try:
            event = self.service.events().insert(calendarId=self.calendar_id, body=google_event).execute()
            return event
        except Exception as e:
            print(f"Error creating event: {e}")
            return None
    
    def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing event"""
        if not self.service:
            return None
        
        google_event = self._convert_to_google_format(event_data)
        
        try:
            event = self.service.events().update(calendarId=self.calendar_id, eventId=event_id, body=google_event).execute()
            return event
        except Exception as e:
            print(f"Error updating event: {e}")
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        if not self.service:
            return False
        
        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting event: {e}")
            return False
    
    def list_events(self, max_results: int = 10, time_min: datetime = None) -> List[Dict[str, Any]]:
        """List upcoming events"""
        if not self.service:
            return []
        
        if time_min is None:
            time_min = datetime.utcnow()
        
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        except Exception as e:
            print(f"Error listing events: {e}")
            return []
    
    def _convert_to_google_format(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert our event format to Google Calendar format"""
        google_event = {
            'summary': event_data.get('title', 'Untitled Event'),
            'description': event_data.get('description', ''),
            'start': {},
            'end': {},
        }
        
        date_str = event_data.get('date')
        if date_str:
            if 'T' in date_str:
                google_event['start']['dateTime'] = date_str
                duration = event_data.get('duration_minutes', 60)
                start_dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                end_dt = start_dt + timedelta(minutes=duration)
                google_event['end']['dateTime'] = end_dt.isoformat()
            else:
                google_event['start']['date'] = date_str
                google_event['end']['date'] = date_str
        
        if event_data.get('location'):
            google_event['location'] = event_data['location']
        
        if event_data.get('reminder', {}).get('enabled'):
            advance_days = event_data['reminder'].get('advance_days', 1)
            google_event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': advance_days * 24 * 60},
                    {'method': 'popup', 'minutes': advance_days * 24 * 60},
                ],
            }
        
        return google_event


def main():
    """Test Google Calendar integration"""
    print("Google Calendar Integration - Ready")
    print("Install with: pip install google-api-python-client google-auth-oauthlib")


if __name__ == "__main__":
    main()
