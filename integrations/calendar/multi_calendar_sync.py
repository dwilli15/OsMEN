#!/usr/bin/env python3
"""
Multi-Calendar Sync Manager

Synchronizes events across multiple calendar services.
Part of v1.4.0 - Syllabus Parser & Calendar Foundation.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import json

from google_calendar import GoogleCalendarIntegration
from outlook_calendar import OutlookCalendarIntegration


class MultiCalendarSync:
    """Manage synchronization across multiple calendars"""
    
    def __init__(self):
        self.calendars = {}
        self.sync_map = {}  # Maps events between calendars
    
    def add_calendar(self, name: str, calendar_integration) -> bool:
        """
        Add a calendar to sync
        
        Args:
            name: Calendar identifier
            calendar_integration: Calendar integration instance
        
        Returns:
            True if successful
        """
        self.calendars[name] = calendar_integration
        return True
    
    def sync_event(self, event_data: Dict[str, Any], source_calendar: str, 
                   target_calendars: List[str]) -> Dict[str, Any]:
        """
        Sync an event to multiple calendars
        
        Args:
            event_data: Event to sync
            source_calendar: Source calendar name
            target_calendars: List of target calendar names
        
        Returns:
            Sync result with created event IDs
        """
        results = {
            'source': source_calendar,
            'event': event_data.get('title'),
            'synced_to': {},
            'errors': {}
        }
        
        for target in target_calendars:
            if target not in self.calendars:
                results['errors'][target] = "Calendar not configured"
                continue
            
            try:
                calendar = self.calendars[target]
                created_event = calendar.create_event(event_data)
                
                if created_event:
                    results['synced_to'][target] = created_event.get('id')
                    
                    # Store mapping
                    event_id = event_data.get('id', 'unknown')
                    if event_id not in self.sync_map:
                        self.sync_map[event_id] = {}
                    self.sync_map[event_id][target] = created_event.get('id')
                else:
                    results['errors'][target] = "Failed to create event"
            
            except Exception as e:
                results['errors'][target] = str(e)
        
        return results
    
    def sync_all_events(self, events: List[Dict[str, Any]], 
                       target_calendars: List[str]) -> List[Dict[str, Any]]:
        """
        Sync multiple events to calendars
        
        Args:
            events: List of events to sync
            target_calendars: Target calendars
        
        Returns:
            List of sync results
        """
        results = []
        
        for event in events:
            result = self.sync_event(event, 'osmen', target_calendars)
            results.append(result)
        
        return results
    
    def update_synced_event(self, event_id: str, updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an event across all synced calendars
        
        Args:
            event_id: Original event ID
            updated_data: Updated event data
        
        Returns:
            Update results
        """
        results = {'updated': [], 'errors': {}}
        
        if event_id not in self.sync_map:
            results['errors']['general'] = "Event not found in sync map"
            return results
        
        # Update in all synced calendars
        for calendar_name, synced_id in self.sync_map[event_id].items():
            try:
                calendar = self.calendars[calendar_name]
                updated = calendar.update_event(synced_id, updated_data)
                
                if updated:
                    results['updated'].append(calendar_name)
                else:
                    results['errors'][calendar_name] = "Update failed"
            
            except Exception as e:
                results['errors'][calendar_name] = str(e)
        
        return results
    
    def delete_synced_event(self, event_id: str) -> Dict[str, Any]:
        """
        Delete an event from all synced calendars
        
        Args:
            event_id: Original event ID
        
        Returns:
            Delete results
        """
        results = {'deleted': [], 'errors': {}}
        
        if event_id not in self.sync_map:
            results['errors']['general'] = "Event not found in sync map"
            return results
        
        # Delete from all synced calendars
        for calendar_name, synced_id in self.sync_map[event_id].items():
            try:
                calendar = self.calendars[calendar_name]
                success = calendar.delete_event(synced_id)
                
                if success:
                    results['deleted'].append(calendar_name)
                else:
                    results['errors'][calendar_name] = "Delete failed"
            
            except Exception as e:
                results['errors'][calendar_name] = str(e)
        
        # Remove from sync map
        if event_id in self.sync_map:
            del self.sync_map[event_id]
        
        return results
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status"""
        return {
            'calendars_configured': list(self.calendars.keys()),
            'total_synced_events': len(self.sync_map),
            'sync_map': self.sync_map
        }


def main():
    """Test multi-calendar sync"""
    print("Multi-Calendar Sync Manager")
    print("=" * 50)
    
    sync_manager = MultiCalendarSync()
    
    # Example: Configure calendars (would need actual instances)
    print("✅ Multi-calendar sync infrastructure ready")
    print("\nFeatures:")
    print("- Sync events to multiple calendars")
    print("- Update synced events across all calendars")
    print("- Delete from all synced calendars")
    print("- Track sync mappings")


if __name__ == "__main__":
    main()
