"""
Comprehensive tests for Google API Wrappers to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from integrations.google.wrappers.calendar_wrapper import GoogleCalendarWrapper
from integrations.google.wrappers.gmail_wrapper import GoogleGmailWrapper
from integrations.google.wrappers.contacts_wrapper import GoogleContactsWrapper


@pytest.fixture
def mock_oauth_handler():
    """Create mock OAuth handler."""
    handler = Mock()
    handler.get_token = Mock(return_value={
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'expires_in': 3600
    })
    return handler


class TestGoogleCalendarWrapper:
    """Test Google Calendar Wrapper for 100% coverage."""
    
    def test_initialization_with_oauth(self, mock_oauth_handler):
        """Test wrapper initialization with OAuth handler."""
        wrapper = GoogleCalendarWrapper(oauth_handler=mock_oauth_handler)
        assert wrapper.oauth_handler == mock_oauth_handler
        assert wrapper.base_url == 'https://www.googleapis.com/calendar/v3'
    
    def test_initialization_without_oauth(self):
        """Test wrapper initialization without OAuth handler."""
        wrapper = GoogleCalendarWrapper()
        assert wrapper.oauth_handler is None
        assert wrapper._access_token is None
    
    def test_get_access_token_from_handler(self, mock_oauth_handler):
        """Test getting access token from OAuth handler."""
        wrapper = GoogleCalendarWrapper(oauth_handler=mock_oauth_handler)
        token = wrapper._get_access_token()
        assert token == 'test_access_token'
    
    def test_get_access_token_direct(self):
        """Test getting access token directly."""
        wrapper = GoogleCalendarWrapper()
        wrapper._access_token = 'direct_token'
        token = wrapper._get_access_token()
        assert token == 'direct_token'
    
    def test_get_headers(self, mock_oauth_handler):
        """Test getting request headers."""
        wrapper = GoogleCalendarWrapper(oauth_handler=mock_oauth_handler)
        headers = wrapper._get_headers()
        assert 'Authorization' in headers
        assert 'Bearer' in headers['Authorization']
        assert 'Content-Type' in headers
    
    @patch('requests.get')
    def test_list_calendars(self, mock_get, mock_oauth_handler):
        """Test listing calendars."""
        mock_response = Mock()
        mock_response.json.return_value = {'items': [{'id': 'primary', 'summary': 'Primary'}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = GoogleCalendarWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.list_calendars()
        
        mock_get.assert_called_once()
        assert isinstance(result, list)
    
    @patch('requests.get')
    def test_list_events(self, mock_get, mock_oauth_handler):
        """Test listing events."""
        mock_response = Mock()
        mock_response.json.return_value = {'items': [{'id': 'event1', 'summary': 'Meeting'}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = GoogleCalendarWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.list_events('primary')
        
        mock_get.assert_called_once()
        assert isinstance(result, list)
    
    @patch('requests.post')
    def test_create_event(self, mock_post, mock_oauth_handler):
        """Test creating an event."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'event1', 'summary': 'New Event'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        wrapper = GoogleCalendarWrapper(oauth_handler=mock_oauth_handler)
        event_data = {'summary': 'New Event', 'start': {'dateTime': '2024-01-01T10:00:00Z'}}
        result = wrapper.create_event('primary', event_data)
        
        mock_post.assert_called_once()
        assert result is not None
    
    @patch('requests.get')
    def test_get_event(self, mock_get, mock_oauth_handler):
        """Test getting single event."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'event1', 'summary': 'Meeting'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = GoogleCalendarWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.get_event('primary', 'event1')
        
        mock_get.assert_called_once()
    
    @patch('requests.put')
    def test_update_event(self, mock_put, mock_oauth_handler):
        """Test updating an event."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'event1', 'summary': 'Updated'}
        mock_response.raise_for_status = Mock()
        mock_put.return_value = mock_response
        
        wrapper = GoogleCalendarWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.update_event('primary', 'event1', {'summary': 'Updated'})
        
        mock_put.assert_called_once()
    
    @patch('requests.delete')
    def test_delete_event(self, mock_delete, mock_oauth_handler):
        """Test deleting an event."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_delete.return_value = mock_response
        
        wrapper = GoogleCalendarWrapper(oauth_handler=mock_oauth_handler)
        wrapper.delete_event('primary', 'event1')
        
        mock_delete.assert_called_once()


class TestGoogleGmailWrapper:
    """Test Google Gmail Wrapper for 100% coverage."""
    
    def test_initialization_with_oauth(self, mock_oauth_handler):
        """Test wrapper initialization with OAuth handler."""
        wrapper = GoogleGmailWrapper(oauth_handler=mock_oauth_handler)
        assert wrapper.oauth_handler == mock_oauth_handler
        assert wrapper.base_url == 'https://gmail.googleapis.com/gmail/v1'
    
    def test_initialization_without_oauth(self):
        """Test wrapper initialization without OAuth handler."""
        wrapper = GoogleGmailWrapper()
        assert wrapper.oauth_handler is None
    
    def test_get_headers(self, mock_oauth_handler):
        """Test getting request headers."""
        wrapper = GoogleGmailWrapper(oauth_handler=mock_oauth_handler)
        headers = wrapper._get_headers()
        assert 'Authorization' in headers
        assert 'Content-Type' in headers
    
    @patch('requests.post')
    def test_send_email(self, mock_post, mock_oauth_handler):
        """Test sending email."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'msg1'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        wrapper = GoogleGmailWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.send_email('to@example.com', 'Subject', 'Body')
        
        mock_post.assert_called_once()
        assert result is not None
    
    @patch('requests.post')
    def test_send_email_html(self, mock_post, mock_oauth_handler):
        """Test sending HTML email."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'msg1'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        wrapper = GoogleGmailWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.send_email('to@example.com', 'Subject', '<p>HTML Body</p>', html=True)
        
        mock_post.assert_called_once()
    
    @patch('requests.get')
    def test_list_messages(self, mock_get, mock_oauth_handler):
        """Test listing messages."""
        mock_response = Mock()
        mock_response.json.return_value = {'messages': [{'id': 'msg1'}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = GoogleGmailWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.list_messages()
        
        mock_get.assert_called_once()
        assert isinstance(result, list)
    
    @patch('requests.get')
    def test_list_messages_with_query(self, mock_get, mock_oauth_handler):
        """Test listing messages with query."""
        mock_response = Mock()
        mock_response.json.return_value = {'messages': [{'id': 'msg1'}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = GoogleGmailWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.list_messages(query='is:unread')
        
        mock_get.assert_called_once()


class TestGoogleContactsWrapper:
    """Test Google Contacts Wrapper for 100% coverage."""
    
    def test_initialization_with_oauth(self, mock_oauth_handler):
        """Test wrapper initialization with OAuth handler."""
        wrapper = GoogleContactsWrapper(oauth_handler=mock_oauth_handler)
        assert wrapper.oauth_handler == mock_oauth_handler
        assert wrapper.base_url == 'https://people.googleapis.com/v1'
    
    def test_initialization_without_oauth(self):
        """Test wrapper initialization without OAuth handler."""
        wrapper = GoogleContactsWrapper()
        assert wrapper.oauth_handler is None
    
    def test_get_headers(self, mock_oauth_handler):
        """Test getting request headers."""
        wrapper = GoogleContactsWrapper(oauth_handler=mock_oauth_handler)
        headers = wrapper._get_headers()
        assert 'Authorization' in headers
        assert 'Content-Type' in headers
    
    @patch('requests.get')
    def test_list_contacts(self, mock_get, mock_oauth_handler):
        """Test listing contacts."""
        mock_response = Mock()
        mock_response.json.return_value = {'connections': [{'resourceName': 'people/1'}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = GoogleContactsWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.list_contacts()
        
        mock_get.assert_called_once()
        assert isinstance(result, list)
    
    @patch('requests.get')
    def test_list_contacts_with_page_size(self, mock_get, mock_oauth_handler):
        """Test listing contacts with custom page size."""
        mock_response = Mock()
        mock_response.json.return_value = {'connections': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = GoogleContactsWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.list_contacts(page_size=50)
        
        mock_get.assert_called_once()
    
    @patch('requests.post')
    def test_create_contact(self, mock_post, mock_oauth_handler):
        """Test creating a contact."""
        mock_response = Mock()
        mock_response.json.return_value = {'resourceName': 'people/1'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        wrapper = GoogleContactsWrapper(oauth_handler=mock_oauth_handler)
        contact_data = {'names': [{'givenName': 'John', 'familyName': 'Doe'}]}
        result = wrapper.create_contact(contact_data)
        
        mock_post.assert_called_once()
        assert result is not None
    
    @patch('requests.get')
    def test_search_contacts(self, mock_get, mock_oauth_handler):
        """Test searching contacts."""
        mock_response = Mock()
        mock_response.json.return_value = {'results': [{'person': {'resourceName': 'people/1'}}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = GoogleContactsWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.search_contacts('john@example.com')
        
        mock_get.assert_called_once()
        assert isinstance(result, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
