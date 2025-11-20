#!/usr/bin/env python3
"""
Day 2 Integration Tests

Tests for all API integrations completed in Day 2:
- Google API wrappers
- Microsoft OAuth and Graph API
- Notion & Todoist clients
"""

import pytest
from unittest.mock import Mock, patch


class TestGoogleAPIWrappers:
    """Test Google API wrapper implementations"""
    
    def test_calendar_wrapper_import(self):
        """Test Google Calendar wrapper can be imported"""
        from integrations.google.wrappers.calendar_wrapper import GoogleCalendarWrapper
        assert GoogleCalendarWrapper is not None
    
    def test_gmail_wrapper_import(self):
        """Test Gmail wrapper can be imported"""
        from integrations.google.wrappers.gmail_wrapper import GoogleGmailWrapper
        assert GoogleGmailWrapper is not None
    
    def test_contacts_wrapper_import(self):
        """Test Contacts wrapper can be imported"""
        from integrations.google.wrappers.contacts_wrapper import GoogleContactsWrapper
        assert GoogleContactsWrapper is not None


class TestMicrosoftOAuth:
    """Test Microsoft OAuth implementation"""
    
    def test_microsoft_oauth_import(self):
        """Test Microsoft OAuth handler can be imported"""
        from integrations.oauth.microsoft_oauth import MicrosoftOAuthHandler
        assert MicrosoftOAuthHandler is not None
    
    @patch.dict('os.environ', {
        'MICROSOFT_CLIENT_ID': 'test_id',
        'MICROSOFT_CLIENT_SECRET': 'test_secret'
    })
    def test_microsoft_oauth_initialization(self):
        """Test Microsoft OAuth handler initializes"""
        from integrations.oauth.microsoft_oauth import MicrosoftOAuthHandler
        handler = MicrosoftOAuthHandler()
        assert handler.client_id == 'test_id'


class TestKnowledgeIntegrations:
    """Test Notion and Todoist integrations"""
    
    def test_notion_client_import(self):
        """Test Notion client can be imported"""
        from integrations.knowledge.notion_client import NotionClient
        assert NotionClient is not None
    
    def test_todoist_client_import(self):
        """Test Todoist client can be imported"""
        from integrations.knowledge.todoist_client import TodoistClient
        assert TodoistClient is not None
    
    def test_notion_client_initialization(self):
        """Test Notion client initializes without token"""
        from integrations.knowledge.notion_client import NotionClient
        client = NotionClient()
        assert client is not None
    
    def test_todoist_client_initialization(self):
        """Test Todoist client initializes without token"""
        from integrations.knowledge.todoist_client import TodoistClient
        client = TodoistClient()
        assert client is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
