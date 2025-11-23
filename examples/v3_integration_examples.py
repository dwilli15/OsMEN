#!/usr/bin/env python3
"""
v3.0 Integration Examples

Demonstrates how to use the v3 integration layer for common tasks.
All examples work with properly configured OAuth.

Run after setting up OAuth:
    python scripts/setup_oauth.py --provider google
    python scripts/complete_oauth.py --provider google --code <CODE>
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from integrations.v3_integration_layer import get_integration_layer


def example_1_check_status():
    """Example 1: Check integration status"""
    print("\n" + "=" * 70)
    print("Example 1: Check Integration Status")
    print("=" * 70)
    
    integration = get_integration_layer()
    status = integration.get_integration_status()
    
    import json
    print(json.dumps(status, indent=2))


def example_2_list_calendars():
    """Example 2: List Google Calendars"""
    print("\n" + "=" * 70)
    print("Example 2: List Google Calendars")
    print("=" * 70)
    
    integration = get_integration_layer()
    calendar = integration.get_google_calendar()
    
    if not calendar:
        print("❌ Google Calendar not configured")
        print("   Run: python scripts/setup_oauth.py --provider google")
        return
    
    try:
        calendars = calendar.list_calendars()
        print(f"\n✅ Found {len(calendars)} calendars:\n")
        
        for cal in calendars:
            print(f"  📅 {cal.get('summary', 'Unnamed')}")
            print(f"     ID: {cal.get('id')}")
            if cal.get('description'):
                print(f"     Description: {cal.get('description')}")
            print()
    
    except Exception as e:
        print(f"❌ Error listing calendars: {e}")


def example_3_create_event():
    """Example 3: Create a calendar event"""
    print("\n" + "=" * 70)
    print("Example 3: Create Calendar Event")
    print("=" * 70)
    
    integration = get_integration_layer()
    calendar = integration.get_google_calendar()
    
    if not calendar:
        print("❌ Google Calendar not configured")
        return
    
    # Create event for tomorrow at 2 PM
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)
    
    event_data = {
        'summary': '🤖 OsMEN Test Event',
        'description': 'Created by OsMEN v3.0 integration example',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'UTC'
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'UTC'
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 60},
                {'method': 'popup', 'minutes': 10}
            ]
        }
    }
    
    try:
        event = calendar.create_event('primary', event_data)
        print("\n✅ Event created successfully!")
        print(f"\n   Title: {event.get('summary')}")
        print(f"   Start: {event.get('start', {}).get('dateTime')}")
        print(f"   Link: {event.get('htmlLink')}")
    
    except Exception as e:
        print(f"❌ Error creating event: {e}")


def example_4_list_upcoming_events():
    """Example 4: List upcoming events"""
    print("\n" + "=" * 70)
    print("Example 4: List Upcoming Events")
    print("=" * 70)
    
    integration = get_integration_layer()
    calendar = integration.get_google_calendar()
    
    if not calendar:
        print("❌ Google Calendar not configured")
        return
    
    try:
        now = datetime.now()
        end_date = now + timedelta(days=7)
        
        events = calendar.list_events(
            calendar_id='primary',
            start_date=now,
            end_date=end_date,
            max_results=10
        )
        
        print(f"\n✅ Found {len(events)} upcoming events in next 7 days:\n")
        
        for event in events:
            summary = event.get('summary', 'No title')
            start = event.get('start', {})
            start_time = start.get('dateTime', start.get('date', 'Unknown'))
            
            print(f"  📅 {summary}")
            print(f"     When: {start_time}")
            if event.get('description'):
                print(f"     Description: {event.get('description')[:50]}...")
            print()
    
    except Exception as e:
        print(f"❌ Error listing events: {e}")


def example_5_send_email():
    """Example 5: Send an email via Gmail"""
    print("\n" + "=" * 70)
    print("Example 5: Send Email (Gmail)")
    print("=" * 70)
    
    integration = get_integration_layer()
    gmail = integration.get_google_gmail()
    
    if not gmail:
        print("❌ Gmail not configured")
        return
    
    print("\n⚠️  This will send a test email to yourself.")
    confirm = input("Continue? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Cancelled")
        return
    
    # Get user's email
    try:
        profile = gmail.get_profile()
        to_email = profile.get('emailAddress')
        
        message_data = {
            'to': to_email,
            'subject': '🤖 OsMEN v3.0 Test Email',
            'body': 'This is a test email sent from OsMEN v3.0 integration layer.\n\nIf you received this, Gmail integration is working! 🎉'
        }
        
        result = gmail.send_message(message_data)
        print(f"\n✅ Email sent successfully!")
        print(f"   Message ID: {result.get('id')}")
    
    except Exception as e:
        print(f"❌ Error sending email: {e}")


def example_6_unified_calendar():
    """Example 6: Use unified calendar manager"""
    print("\n" + "=" * 70)
    print("Example 6: Unified Calendar Manager")
    print("=" * 70)
    print("\n(Works with both Google and Microsoft calendars)")
    
    integration = get_integration_layer()
    calendar_manager = integration.get_calendar_manager()
    
    if not calendar_manager:
        print("❌ Calendar manager not available")
        return
    
    try:
        # This would list events from all configured providers
        print("\n✅ Calendar manager ready")
        print("   Supports: Google Calendar, Outlook Calendar")
        print("   Features: Unified interface, conflict detection, multi-provider sync")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print(" " * 20 + "OsMEN v3.0 Integration Examples")
    print("=" * 70)
    print()
    print("These examples demonstrate the v3 integration layer.")
    print("Make sure you've configured OAuth first:")
    print("  python scripts/setup_oauth.py --provider google")
    print()
    
    examples = [
        ("Check Integration Status", example_1_check_status),
        ("List Google Calendars", example_2_list_calendars),
        ("Create Calendar Event", example_3_create_event),
        ("List Upcoming Events", example_4_list_upcoming_events),
        ("Send Email via Gmail", example_5_send_email),
        ("Unified Calendar Manager", example_6_unified_calendar),
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print(f"  {len(examples) + 1}. Run All")
    print(f"  0. Exit")
    
    while True:
        choice = input(f"\nSelect example (0-{len(examples) + 1}): ").strip()
        
        if choice == '0':
            print("\n👋 Goodbye!")
            break
        
        try:
            choice_num = int(choice)
            if choice_num == len(examples) + 1:
                # Run all
                for name, func in examples:
                    func()
                    input("\nPress Enter to continue to next example...")
            elif 1 <= choice_num <= len(examples):
                examples[choice_num - 1][1]()
            else:
                print("❌ Invalid choice")
        except ValueError:
            print("❌ Please enter a number")
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted!")
            break
        except Exception as e:
            print(f"\n❌ Error running example: {e}")


if __name__ == "__main__":
    main()
