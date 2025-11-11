#!/usr/bin/env python3
"""
Outlook Calendar Integration

Manages events in Microsoft Outlook Calendar via Microsoft Graph API.
Part of v1.4.0 - Syllabus Parser & Calendar Foundation.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import requests


class OutlookCalendarIntegration:
    """Integration with Outlook Calendar via Microsoft Graph API"""
    
    GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    
    def __init__(self, access_token: str = None):
        """
        Initialize Outlook Calendar integration
        
        Args:
            access_token: Microsoft Graph API access token
        """
        self.access_token = access_token or os.getenv('OUTLOOK_ACCESS_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def create_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new calendar event"""
        if not self.access_token:
            print("No access token provided")
            return None
        
        outlook_event = self._convert_to_outlook_format(event_data)
        
        try:
            response = requests.post(
                f'{self.GRAPH_API_ENDPOINT}/me/events',
                headers=self.headers,
                json=outlook_event
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                print(f"Error creating event: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing event"""
        if not self.access_token:
            return None
        
        outlook_event = self._convert_to_outlook_format(event_data)
        
        try:
            response = requests.patch(
                f'{self.GRAPH_API_ENDPOINT}/me/events/{event_id}',
                headers=self.headers,
                json=outlook_event
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        if not self.access_token:
            return False
        
        try:
            response = requests.delete(
                f'{self.GRAPH_API_ENDPOINT}/me/events/{event_id}',
                headers=self.headers
            )
            
            return response.status_code == 204
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def list_events(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """List upcoming events"""
        if not self.access_token:
            return []
        
        try:
            response = requests.get(
                f'{self.GRAPH_API_ENDPOINT}/me/events?$top={max_results}&$orderby=start/dateTime',
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json().get('value', [])
            else:
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def _convert_to_outlook_format(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert our event format to Outlook format"""
        outlook_event = {
            'subject': event_data.get('title', 'Untitled Event'),
            'body': {
                'contentType': 'text',
                'content': event_data.get('description', '')
            },
            'start': {},
            'end': {},
        }
        
        date_str = event_data.get('date')
        if date_str:
            if 'T' in date_str:
                outlook_event['start']['dateTime'] = date_str
                outlook_event['start']['timeZone'] = 'UTC'
                
                duration = event_data.get('duration_minutes', 60)
                start_dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                end_dt = start_dt + timedelta(minutes=duration)
                outlook_event['end']['dateTime'] = end_dt.isoformat()
                outlook_event['end']['timeZone'] = 'UTC'
            else:
                outlook_event['isAllDay'] = True
                outlook_event['start']['dateTime'] = f'{date_str}T00:00:00'
                outlook_event['start']['timeZone'] = 'UTC'
                outlook_event['end']['dateTime'] = f'{date_str}T23:59:59'
                outlook_event['end']['timeZone'] = 'UTC'
        
        if event_data.get('location'):
            outlook_event['location'] = {'displayName': event_data['location']}
        
        return outlook_event


def main():
    """Test Outlook Calendar integration"""
    print("Outlook Calendar Integration - Ready")
    print("Requires Microsoft Graph API access token")


if __name__ == "__main__":
    main()
