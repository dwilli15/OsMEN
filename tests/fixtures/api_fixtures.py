"""
API-specific test fixtures.
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime, timedelta


@pytest.fixture
def mock_calendar_api_response() -> Dict[str, Any]:
    """Mock Calendar API response."""
    return {
        'calendars': [
            {
                'id': 'primary',
                'summary': 'Test Calendar',
                'description': 'Primary test calendar',
                'timeZone': 'America/New_York',
            },
            {
                'id': 'work_calendar_123',
                'summary': 'Work Calendar',
                'description': 'Work events calendar',
                'timeZone': 'America/New_York',
            },
        ],
        'events': [
            {
                'id': 'event_001',
                'summary': 'Test Event 1',
                'description': 'First test event',
                'start': {
                    'dateTime': '2024-01-15T10:00:00-05:00',
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': '2024-01-15T11:00:00-05:00',
                    'timeZone': 'America/New_York',
                },
            },
            {
                'id': 'event_002',
                'summary': 'Test Event 2',
                'description': 'Second test event',
                'start': {
                    'dateTime': '2024-01-15T14:00:00-05:00',
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': '2024-01-15T15:00:00-05:00',
                    'timeZone': 'America/New_York',
                },
            },
        ],
    }


@pytest.fixture
def mock_gmail_api_response() -> Dict[str, Any]:
    """Mock Gmail API response."""
    return {
        'messages': [
            {
                'id': 'msg_001',
                'threadId': 'thread_001',
                'labelIds': ['INBOX', 'UNREAD'],
                'snippet': 'This is a test email message snippet...',
            },
            {
                'id': 'msg_002',
                'threadId': 'thread_001',
                'labelIds': ['INBOX'],
                'snippet': 'This is another test email...',
            },
        ],
        'message_detail': {
            'id': 'msg_001',
            'threadId': 'thread_001',
            'labelIds': ['INBOX', 'UNREAD'],
            'snippet': 'This is a test email message snippet...',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'To', 'value': 'recipient@example.com'},
                    {'name': 'Subject', 'value': 'Test Email Subject'},
                    {'name': 'Date', 'value': 'Mon, 15 Jan 2024 10:00:00 -0500'},
                ],
                'body': {
                    'data': 'VGhpcyBpcyB0aGUgZW1haWwgYm9keSBjb250ZW50',  # Base64 encoded
                },
            },
        },
    }


@pytest.fixture
def mock_contacts_api_response() -> Dict[str, Any]:
    """Mock Contacts API response."""
    return {
        'connections': [
            {
                'resourceName': 'people/c001',
                'etag': 'etag_001',
                'names': [
                    {
                        'displayName': 'John Doe',
                        'familyName': 'Doe',
                        'givenName': 'John',
                    },
                ],
                'emailAddresses': [
                    {
                        'value': 'john.doe@example.com',
                        'type': 'work',
                    },
                ],
                'phoneNumbers': [
                    {
                        'value': '+1-555-0101',
                        'type': 'mobile',
                    },
                ],
            },
            {
                'resourceName': 'people/c002',
                'etag': 'etag_002',
                'names': [
                    {
                        'displayName': 'Jane Smith',
                        'familyName': 'Smith',
                        'givenName': 'Jane',
                    },
                ],
                'emailAddresses': [
                    {
                        'value': 'jane.smith@example.com',
                        'type': 'personal',
                    },
                ],
            },
        ],
    }


@pytest.fixture
def mock_api_error_response() -> Dict[str, Any]:
    """Mock API error response."""
    return {
        'error': {
            'code': 401,
            'message': 'Invalid Credentials',
            'status': 'UNAUTHENTICATED',
        },
    }


@pytest.fixture
def mock_rate_limit_response() -> Dict[str, Any]:
    """Mock rate limit error response."""
    return {
        'error': {
            'code': 429,
            'message': 'Rate Limit Exceeded',
            'status': 'RESOURCE_EXHAUSTED',
        },
    }
