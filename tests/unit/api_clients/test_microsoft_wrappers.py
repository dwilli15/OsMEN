"""
Comprehensive tests for Microsoft API Wrappers to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch
import requests
from integrations.microsoft.wrappers.calendar_wrapper import MicrosoftCalendarWrapper
from integrations.microsoft.wrappers.mail_wrapper import MicrosoftMailWrapper
from integrations.microsoft.wrappers.contacts_wrapper import MicrosoftContactsWrapper


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


class TestMicrosoftCalendarWrapper:
    """Test Microsoft Calendar Wrapper for 100% coverage."""
    
    def test_initialization_with_oauth(self, mock_oauth_handler):
        """Test wrapper initialization with OAuth handler."""
        wrapper = MicrosoftCalendarWrapper(oauth_handler=mock_oauth_handler)
        assert wrapper.oauth_handler == mock_oauth_handler
        assert 'graph.microsoft.com' in wrapper.base_url
    
    def test_initialization_without_oauth(self):
        """Test wrapper initialization without OAuth handler."""
        wrapper = MicrosoftCalendarWrapper()
        assert wrapper.oauth_handler is None
        assert wrapper._access_token is None
    
    def test_get_access_token_from_handler(self, mock_oauth_handler):
        """Test getting access token from OAuth handler."""
        wrapper = MicrosoftCalendarWrapper(oauth_handler=mock_oauth_handler)
        token = wrapper._get_access_token()
        assert token == 'test_access_token'
    
    def test_get_access_token_direct(self):
        """Test getting access token directly."""
        wrapper = MicrosoftCalendarWrapper()
        wrapper._access_token = 'direct_token'
        token = wrapper._get_access_token()
        assert token == 'direct_token'
    
    def test_get_headers(self, mock_oauth_handler):
        """Test getting request headers."""
        wrapper = MicrosoftCalendarWrapper(oauth_handler=mock_oauth_handler)
        headers = wrapper._get_headers()
        assert 'Authorization' in headers
        assert 'Bearer' in headers['Authorization']
    
    @patch('requests.get')
    def test_list_events(self, mock_get, mock_oauth_handler):
        """Test listing events."""
        mock_response = Mock()
        mock_response.json.return_value = {'value': [{'id': '1', 'subject': 'Meeting'}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = MicrosoftCalendarWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.list_events()
        
        mock_get.assert_called_once()
        assert isinstance(result, list)
    
    @patch('requests.post')
    def test_create_event(self, mock_post, mock_oauth_handler):
        """Test creating an event."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': '1', 'subject': 'New Meeting'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        wrapper = MicrosoftCalendarWrapper(oauth_handler=mock_oauth_handler)
        event_data = {'subject': 'New Meeting'}
        result = wrapper.create_event(event_data)
        
        mock_post.assert_called_once()
        assert result is not None
    
    @patch('requests.get')
    def test_get_event(self, mock_get, mock_oauth_handler):
        """Test getting single event."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': '1', 'subject': 'Meeting'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = MicrosoftCalendarWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.get_event('event1')
        
        mock_get.assert_called_once()
    
    @patch('requests.patch')
    def test_update_event(self, mock_patch, mock_oauth_handler):
        """Test updating an event."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': '1', 'subject': 'Updated'}
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response
        
        wrapper = MicrosoftCalendarWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.update_event('event1', {'subject': 'Updated'})
        
        mock_patch.assert_called_once()
    
    @patch('requests.delete')
    def test_delete_event(self, mock_delete, mock_oauth_handler):
        """Test deleting an event."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_delete.return_value = mock_response
        
        wrapper = MicrosoftCalendarWrapper(oauth_handler=mock_oauth_handler)
        wrapper.delete_event('event1')
        
        mock_delete.assert_called_once()


class TestMicrosoftMailWrapper:
    """Test Microsoft Mail Wrapper for 100% coverage."""
    
    def test_initialization_with_oauth(self, mock_oauth_handler):
        """Test wrapper initialization with OAuth handler."""
        wrapper = MicrosoftMailWrapper(oauth_handler=mock_oauth_handler)
        assert wrapper.oauth_handler == mock_oauth_handler
        assert 'graph.microsoft.com' in wrapper.GRAPH_API_BASE
    
    def test_initialization_without_oauth(self):
        """Test wrapper initialization without OAuth handler."""
        wrapper = MicrosoftMailWrapper()
        assert wrapper.oauth_handler is None
    
    def test_get_headers(self, mock_oauth_handler):
        """Test getting request headers."""
        wrapper = MicrosoftMailWrapper(oauth_handler=mock_oauth_handler)
        headers = wrapper._get_headers()
        assert 'Authorization' in headers
    
    @patch('requests.get')
    def test_list_messages(self, mock_get, mock_oauth_handler):
        """Test listing messages."""
        mock_response = Mock()
        mock_response.json.return_value = {'value': [{'id': '1', 'subject': 'Email'}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = MicrosoftMailWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.list_messages()
        
        mock_get.assert_called_once()
        assert isinstance(result, list)
    
    @patch('requests.post')
    def test_send_mail(self, mock_post, mock_oauth_handler):
        """Test sending mail."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        wrapper = MicrosoftMailWrapper(oauth_handler=mock_oauth_handler)
        wrapper.send_email(['to@example.com'], 'Subject', 'Body')
        
        mock_post.assert_called_once()
    
    @patch('requests.get')
    def test_get_message(self, mock_get, mock_oauth_handler):
        """Test getting single message."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': '1', 'subject': 'Email'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = MicrosoftMailWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.get_message('msg1')
        
        mock_get.assert_called_once()
    
    @patch('requests.delete')
    def test_delete_message(self, mock_delete, mock_oauth_handler):
        """Test deleting a message."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_delete.return_value = mock_response
        
        wrapper = MicrosoftMailWrapper(oauth_handler=mock_oauth_handler)
        wrapper.delete_message('msg1')
        
        mock_delete.assert_called_once()


class TestMicrosoftContactsWrapper:
    """Test Microsoft Contacts Wrapper for 100% coverage."""
    
    def test_initialization_with_oauth(self, mock_oauth_handler):
        """Test wrapper initialization with OAuth handler."""
        wrapper = MicrosoftContactsWrapper(oauth_handler=mock_oauth_handler)
        assert wrapper.oauth_handler == mock_oauth_handler
        assert 'graph.microsoft.com' in wrapper.GRAPH_API_BASE
    
    def test_initialization_without_oauth(self):
        """Test wrapper initialization without OAuth handler."""
        wrapper = MicrosoftContactsWrapper()
        assert wrapper.oauth_handler is None
    
    def test_get_headers(self, mock_oauth_handler):
        """Test getting request headers."""
        wrapper = MicrosoftContactsWrapper(oauth_handler=mock_oauth_handler)
        headers = wrapper._get_headers()
        assert 'Authorization' in headers
    
    @patch('requests.get')
    def test_list_contacts(self, mock_get, mock_oauth_handler):
        """Test listing contacts."""
        mock_response = Mock()
        mock_response.json.return_value = {'value': [{'id': '1', 'displayName': 'John Doe'}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = MicrosoftContactsWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.list_contacts()
        
        mock_get.assert_called_once()
        assert isinstance(result, list)
    
    @patch('requests.post')
    def test_create_contact(self, mock_post, mock_oauth_handler):
        """Test creating a contact."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': '1', 'displayName': 'John Doe'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        wrapper = MicrosoftContactsWrapper(oauth_handler=mock_oauth_handler)
        contact_data = {'givenName': 'John', 'surname': 'Doe'}
        result = wrapper.create_contact(contact_data)
        
        mock_post.assert_called_once()
        assert result is not None
    
    @patch('requests.get')
    def test_get_contact(self, mock_get, mock_oauth_handler):
        """Test getting single contact."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': '1', 'displayName': 'John Doe'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        wrapper = MicrosoftContactsWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.get_contact('contact1')
        
        mock_get.assert_called_once()
    
    @patch('requests.patch')
    def test_update_contact(self, mock_patch, mock_oauth_handler):
        """Test updating a contact."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': '1', 'displayName': 'Jane Doe'}
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response
        
        wrapper = MicrosoftContactsWrapper(oauth_handler=mock_oauth_handler)
        result = wrapper.update_contact('contact1', {'givenName': 'Jane'})
        
        mock_patch.assert_called_once()
    
    @patch('requests.delete')
    def test_delete_contact(self, mock_delete, mock_oauth_handler):
        """Test deleting a contact."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_delete.return_value = mock_response
        
        wrapper = MicrosoftContactsWrapper(oauth_handler=mock_oauth_handler)
        wrapper.delete_contact('contact1')
        
        mock_delete.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
