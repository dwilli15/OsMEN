#!/usr/bin/env python3
"""
Microsoft Mail API Wrapper (Microsoft Graph API)

High-level wrapper for Outlook Mail operations with retry logic and error handling.
"""

from typing import Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
from loguru import logger
import requests
import base64


class MicrosoftMailWrapper:
    """
    Unified wrapper for Microsoft Mail (Outlook) via Microsoft Graph API.
    
    Provides high-level methods for email operations with:
    - Automatic retry with exponential backoff
    - Rate limiting
    - Error handling and logging
    - Attachment support
    """
    
    GRAPH_API_BASE = 'https://graph.microsoft.com/v1.0'
    
    def __init__(self, oauth_handler=None):
        """
        Initialize Microsoft Mail wrapper.
        
        Args:
            oauth_handler: OAuth handler for authentication (MicrosoftOAuthHandler)
        """
        self.oauth_handler = oauth_handler
        self._access_token = None
    
    def _get_access_token(self) -> str:
        """Get current access token from OAuth handler"""
        if self.oauth_handler:
            token_data = self.oauth_handler.get_token()
            return token_data.get('access_token')
        return self._access_token
    
    def _get_headers(self) -> Dict:
        """Get request headers with authentication"""
        token = self._get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def send_email(self, 
                   to: List[str], 
                   subject: str, 
                   body: str,
                   cc: List[str] = None,
                   bcc: List[str] = None,
                   is_html: bool = False) -> Dict:
        """
        Send an email.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            cc: List of CC recipients
            bcc: List of BCC recipients
            is_html: Whether body is HTML
            
        Returns:
            Response data
        """
        message = {
            'message': {
                'subject': subject,
                'body': {
                    'contentType': 'HTML' if is_html else 'Text',
                    'content': body
                },
                'toRecipients': [{'emailAddress': {'address': addr}} for addr in to]
            }
        }
        
        if cc:
            message['message']['ccRecipients'] = [
                {'emailAddress': {'address': addr}} for addr in cc
            ]
        
        if bcc:
            message['message']['bccRecipients'] = [
                {'emailAddress': {'address': addr}} for addr in bcc
            ]
        
        url = f"{self.GRAPH_API_BASE}/me/sendMail"
        response = requests.post(url, json=message, headers=self._get_headers())
        response.raise_for_status()
        
        logger.info(f"Sent email to {len(to)} recipients: {subject}")
        return {'status': 'sent'}
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def send_email_with_attachment(self,
                                   to: List[str],
                                   subject: str,
                                   body: str,
                                   attachments: List[Dict],
                                   is_html: bool = False) -> Dict:
        """
        Send an email with attachments.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body
            attachments: List of attachment dicts with 'name' and 'content' (base64)
            is_html: Whether body is HTML
            
        Returns:
            Response data
        """
        message = {
            'subject': subject,
            'body': {
                'contentType': 'HTML' if is_html else 'Text',
                'content': body
            },
            'toRecipients': [{'emailAddress': {'address': addr}} for addr in to],
            'attachments': [
                {
                    '@odata.type': '#microsoft.graph.fileAttachment',
                    'name': att['name'],
                    'contentBytes': att['content']
                }
                for att in attachments
            ]
        }
        
        # Create draft first, then send
        url = f"{self.GRAPH_API_BASE}/me/messages"
        response = requests.post(url, json=message, headers=self._get_headers())
        response.raise_for_status()
        
        message_id = response.json()['id']
        
        # Send the draft
        send_url = f"{self.GRAPH_API_BASE}/me/messages/{message_id}/send"
        send_response = requests.post(send_url, headers=self._get_headers())
        send_response.raise_for_status()
        
        logger.info(f"Sent email with {len(attachments)} attachments")
        return {'status': 'sent', 'message_id': message_id}
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def list_messages(self, 
                     folder: str = 'inbox',
                     max_results: int = 50,
                     filter_query: str = None) -> List[Dict]:
        """
        List messages from a mail folder.
        
        Args:
            folder: Folder name (inbox, sentitems, drafts, etc.)
            max_results: Maximum number of results
            filter_query: OData filter query
            
        Returns:
            List of message objects
        """
        url = f"{self.GRAPH_API_BASE}/me/mailFolders/{folder}/messages"
        
        params = {'$top': max_results, '$orderby': 'receivedDateTime DESC'}
        if filter_query:
            params['$filter'] = filter_query
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        
        data = response.json()
        messages = data.get('value', [])
        
        logger.info(f"Listed {len(messages)} messages from {folder}")
        return messages
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def get_message(self, message_id: str) -> Dict:
        """
        Get a specific message by ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            Message object
        """
        url = f"{self.GRAPH_API_BASE}/me/messages/{message_id}"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        
        message = response.json()
        logger.info(f"Retrieved message: {message_id}")
        return message
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def search_messages(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Search messages using keyword query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            
        Returns:
            List of matching messages
        """
        url = f"{self.GRAPH_API_BASE}/me/messages"
        params = {
            '$search': f'"{query}"',
            '$top': max_results
        }
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        
        data = response.json()
        messages = data.get('value', [])
        
        logger.info(f"Found {len(messages)} messages for query: {query}")
        return messages
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message.
        
        Args:
            message_id: Message ID to delete
            
        Returns:
            True if successful
        """
        url = f"{self.GRAPH_API_BASE}/me/messages/{message_id}"
        response = requests.delete(url, headers=self._get_headers())
        response.raise_for_status()
        
        logger.info(f"Deleted message: {message_id}")
        return True
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> Dict:
        """
        Create a new mail folder.
        
        Args:
            folder_name: Name of folder to create
            parent_folder_id: Parent folder ID (optional)
            
        Returns:
            Created folder object
        """
        if parent_folder_id:
            url = f"{self.GRAPH_API_BASE}/me/mailFolders/{parent_folder_id}/childFolders"
        else:
            url = f"{self.GRAPH_API_BASE}/me/mailFolders"
        
        folder_data = {'displayName': folder_name}
        
        response = requests.post(url, json=folder_data, headers=self._get_headers())
        response.raise_for_status()
        
        folder = response.json()
        logger.info(f"Created folder: {folder_name}")
        return folder
