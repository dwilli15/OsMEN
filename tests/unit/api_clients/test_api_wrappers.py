"""
Unit tests for API client wrappers.

These tests use mocks and fixtures to test API operations without real API calls.
"""

import pytest
from tests.fixtures.api_fixtures import *
from tests.fixtures.mock_data import create_test_events, create_test_emails, create_test_contacts


class TestCalendarAPIWrapper:
    """Test Calendar API wrapper functionality."""
    
    def test_mock_calendar_response_structure(self, mock_calendar_api_response):
        """Test that mock calendar response has expected structure."""
        response = mock_calendar_api_response
        
        assert 'calendars' in response
        assert 'events' in response
        assert isinstance(response['calendars'], list)
        assert isinstance(response['events'], list)
        assert len(response['calendars']) > 0
        assert len(response['events']) > 0
    
    def test_calendar_list_parsing(self, mock_calendar_api_response):
        """Test parsing calendar list response."""
        calendars = mock_calendar_api_response['calendars']
        
        for calendar in calendars:
            assert 'id' in calendar
            assert 'summary' in calendar
            assert 'timeZone' in calendar
    
    def test_event_list_parsing(self, mock_calendar_api_response):
        """Test parsing event list response."""
        events = mock_calendar_api_response['events']
        
        for event in events:
            assert 'id' in event
            assert 'summary' in event
            assert 'start' in event
            assert 'end' in event
            assert 'dateTime' in event['start']
            assert 'timeZone' in event['start']
    
    def test_create_test_events(self):
        """Test creating test events using factory."""
        events = create_test_events(count=5)
        
        assert len(events) == 5
        
        for event in events:
            assert 'id' in event
            assert 'summary' in event
            assert 'description' in event
            assert 'start' in event
            assert 'end' in event
    
    def test_create_custom_test_event(self):
        """Test creating a custom test event."""
        from tests.fixtures.mock_data import create_test_event
        
        event = create_test_event(
            summary='Custom Test Event',
            description='This is a custom description',
            duration_hours=2
        )
        
        assert event['summary'] == 'Custom Test Event'
        assert event['description'] == 'This is a custom description'
        assert 'start' in event
        assert 'end' in event


class TestGmailAPIWrapper:
    """Test Gmail API wrapper functionality."""
    
    def test_mock_gmail_response_structure(self, mock_gmail_api_response):
        """Test that mock Gmail response has expected structure."""
        response = mock_gmail_api_response
        
        assert 'messages' in response
        assert 'message_detail' in response
        assert isinstance(response['messages'], list)
        assert len(response['messages']) > 0
    
    def test_message_list_parsing(self, mock_gmail_api_response):
        """Test parsing message list response."""
        messages = mock_gmail_api_response['messages']
        
        for message in messages:
            assert 'id' in message
            assert 'threadId' in message
            assert 'labelIds' in message
            assert 'snippet' in message
    
    def test_message_detail_parsing(self, mock_gmail_api_response):
        """Test parsing message detail response."""
        message = mock_gmail_api_response['message_detail']
        
        assert 'id' in message
        assert 'payload' in message
        assert 'headers' in message['payload']
        assert 'body' in message['payload']
        
        # Verify headers
        headers = {h['name']: h['value'] for h in message['payload']['headers']}
        assert 'From' in headers
        assert 'To' in headers
        assert 'Subject' in headers
        assert 'Date' in headers
    
    def test_create_test_emails(self):
        """Test creating test emails using factory."""
        emails = create_test_emails(count=5)
        
        assert len(emails) == 5
        
        for email in emails:
            assert 'id' in email
            assert 'threadId' in email
            assert 'snippet' in email
            assert 'payload' in email
            assert 'headers' in email['payload']
    
    def test_create_custom_test_email(self):
        """Test creating a custom test email."""
        from tests.fixtures.mock_data import create_test_email
        
        email = create_test_email(
            subject='Custom Test Subject',
            from_email='sender@test.com',
            to_email='recipient@test.com',
            snippet='This is a custom test email'
        )
        
        headers = {h['name']: h['value'] for h in email['payload']['headers']}
        assert headers['Subject'] == 'Custom Test Subject'
        assert headers['From'] == 'sender@test.com'
        assert headers['To'] == 'recipient@test.com'
        assert email['snippet'] == 'This is a custom test email'


class TestContactsAPIWrapper:
    """Test Contacts API wrapper functionality."""
    
    def test_mock_contacts_response_structure(self, mock_contacts_api_response):
        """Test that mock contacts response has expected structure."""
        response = mock_contacts_api_response
        
        assert 'connections' in response
        assert isinstance(response['connections'], list)
        assert len(response['connections']) > 0
    
    def test_contact_parsing(self, mock_contacts_api_response):
        """Test parsing contact response."""
        contacts = mock_contacts_api_response['connections']
        
        for contact in contacts:
            assert 'resourceName' in contact
            assert 'names' in contact
            assert 'emailAddresses' in contact
            
            # Verify names
            assert len(contact['names']) > 0
            name = contact['names'][0]
            assert 'displayName' in name
            
            # Verify emails
            assert len(contact['emailAddresses']) > 0
            email = contact['emailAddresses'][0]
            assert 'value' in email
    
    def test_create_test_contacts(self):
        """Test creating test contacts using factory."""
        contacts = create_test_contacts(count=5)
        
        assert len(contacts) == 5
        
        for contact in contacts:
            assert 'resourceName' in contact
            assert 'names' in contact
            assert 'emailAddresses' in contact
    
    def test_create_custom_test_contact(self):
        """Test creating a custom test contact."""
        from tests.fixtures.mock_data import create_test_contact
        
        contact = create_test_contact(
            givenName='John',
            familyName='Doe',
            email='john.doe@example.com',
            email_type='personal'
        )
        
        assert contact['names'][0]['givenName'] == 'John'
        assert contact['names'][0]['familyName'] == 'Doe'
        assert contact['emailAddresses'][0]['value'] == 'john.doe@example.com'
        assert contact['emailAddresses'][0]['type'] == 'personal'


class TestAPIErrorHandling:
    """Test API error handling."""
    
    def test_mock_api_error_response(self, mock_api_error_response):
        """Test that mock API error response has expected structure."""
        error = mock_api_error_response
        
        assert 'error' in error
        assert 'code' in error['error']
        assert 'message' in error['error']
        assert error['error']['code'] == 401
    
    def test_mock_rate_limit_response(self, mock_rate_limit_response):
        """Test that mock rate limit response has expected structure."""
        error = mock_rate_limit_response
        
        assert 'error' in error
        assert 'code' in error['error']
        assert 'message' in error['error']
        assert error['error']['code'] == 429


class TestDataFactories:
    """Test data factory functionality."""
    
    def test_event_factory_creates_unique_ids(self):
        """Test that event factory creates unique IDs."""
        events = create_test_events(count=10)
        
        event_ids = [e['id'] for e in events]
        assert len(event_ids) == len(set(event_ids))  # All IDs are unique
    
    def test_email_factory_creates_unique_ids(self):
        """Test that email factory creates unique IDs."""
        emails = create_test_emails(count=10)
        
        email_ids = [e['id'] for e in emails]
        assert len(email_ids) == len(set(email_ids))  # All IDs are unique
    
    def test_contact_factory_creates_unique_resource_names(self):
        """Test that contact factory creates unique resource names."""
        contacts = create_test_contacts(count=10)
        
        resource_names = [c['resourceName'] for c in contacts]
        assert len(resource_names) == len(set(resource_names))  # All resource names are unique
    
    def test_token_factory_google(self):
        """Test creating Google OAuth tokens."""
        from tests.fixtures.mock_data import create_test_token
        
        token = create_test_token(provider='google')
        
        assert 'access_token' in token
        assert 'refresh_token' in token
        assert token['token_type'] == 'Bearer'
        assert 'id_token' not in token  # Google doesn't include this in standard flow
    
    def test_token_factory_microsoft(self):
        """Test creating Microsoft OAuth tokens."""
        from tests.fixtures.mock_data import create_test_token
        
        token = create_test_token(provider='microsoft')
        
        assert 'access_token' in token
        assert 'refresh_token' in token
        assert 'id_token' in token  # Microsoft includes this
        assert token['token_type'] == 'Bearer'
