#!/usr/bin/env python3
"""
Microsoft Contacts API Wrapper (Microsoft Graph API)

High-level wrapper for Outlook Contacts operations with retry logic and error handling.
"""

from typing import Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
from loguru import logger
import requests


class MicrosoftContactsWrapper:
    """
    Unified wrapper for Microsoft Contacts (Outlook) via Microsoft Graph API.
    
    Provides high-level methods for contact operations with:
    - Automatic retry with exponential backoff
    - Rate limiting
    - Error handling and logging
    - Full CRUD operations
    """
    
    GRAPH_API_BASE = 'https://graph.microsoft.com/v1.0'
    
    def __init__(self, oauth_handler=None):
        """
        Initialize Microsoft Contacts wrapper.
        
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
    def list_contacts(self, max_results: int = 100) -> List[Dict]:
        """
        List all contacts.
        
        Args:
            max_results: Maximum number of results
            
        Returns:
            List of contact objects
        """
        url = f"{self.GRAPH_API_BASE}/me/contacts"
        params = {'$top': max_results}
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        
        data = response.json()
        contacts = data.get('value', [])
        
        logger.info(f"Listed {len(contacts)} contacts")
        return contacts
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def create_contact(self, contact_data: Dict) -> Dict:
        """
        Create a new contact.
        
        Args:
            contact_data: Contact information dict with fields like:
                - givenName: First name
                - surname: Last name
                - emailAddresses: List of email dicts
                - businessPhones: List of phone numbers
                - etc.
            
        Returns:
            Created contact object
        """
        url = f"{self.GRAPH_API_BASE}/me/contacts"
        
        response = requests.post(url, json=contact_data, headers=self._get_headers())
        response.raise_for_status()
        
        contact = response.json()
        logger.info(f"Created contact: {contact.get('displayName')}")
        return contact
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def get_contact(self, contact_id: str) -> Dict:
        """
        Get a specific contact by ID.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            Contact object
        """
        url = f"{self.GRAPH_API_BASE}/me/contacts/{contact_id}"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        
        contact = response.json()
        logger.info(f"Retrieved contact: {contact_id}")
        return contact
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def update_contact(self, contact_id: str, contact_data: Dict) -> Dict:
        """
        Update an existing contact.
        
        Args:
            contact_id: Contact ID to update
            contact_data: Updated contact information
            
        Returns:
            Updated contact object
        """
        url = f"{self.GRAPH_API_BASE}/me/contacts/{contact_id}"
        
        response = requests.patch(url, json=contact_data, headers=self._get_headers())
        response.raise_for_status()
        
        contact = response.json()
        logger.info(f"Updated contact: {contact_id}")
        return contact
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def delete_contact(self, contact_id: str) -> bool:
        """
        Delete a contact.
        
        Args:
            contact_id: Contact ID to delete
            
        Returns:
            True if successful
        """
        url = f"{self.GRAPH_API_BASE}/me/contacts/{contact_id}"
        response = requests.delete(url, headers=self._get_headers())
        response.raise_for_status()
        
        logger.info(f"Deleted contact: {contact_id}")
        return True
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def search_contacts(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Search contacts by name or email.
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            
        Returns:
            List of matching contacts
        """
        url = f"{self.GRAPH_API_BASE}/me/contacts"
        params = {
            '$search': f'"{query}"',
            '$top': max_results
        }
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        
        data = response.json()
        contacts = data.get('value', [])
        
        logger.info(f"Found {len(contacts)} contacts for query: {query}")
        return contacts
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def list_contact_folders(self) -> List[Dict]:
        """
        List all contact folders.
        
        Returns:
            List of contact folder objects
        """
        url = f"{self.GRAPH_API_BASE}/me/contactFolders"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        
        data = response.json()
        folders = data.get('value', [])
        
        logger.info(f"Listed {len(folders)} contact folders")
        return folders
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def create_contact_folder(self, folder_name: str, parent_folder_id: str = None) -> Dict:
        """
        Create a new contact folder.
        
        Args:
            folder_name: Name of folder to create
            parent_folder_id: Parent folder ID (optional)
            
        Returns:
            Created folder object
        """
        if parent_folder_id:
            url = f"{self.GRAPH_API_BASE}/me/contactFolders/{parent_folder_id}/childFolders"
        else:
            url = f"{self.GRAPH_API_BASE}/me/contactFolders"
        
        folder_data = {'displayName': folder_name}
        
        response = requests.post(url, json=folder_data, headers=self._get_headers())
        response.raise_for_status()
        
        folder = response.json()
        logger.info(f"Created contact folder: {folder_name}")
        return folder
    
    def convert_from_google_format(self, google_contact: Dict) -> Dict:
        """
        Convert Google Contacts format to Microsoft Graph format.
        
        Args:
            google_contact: Contact in Google People API format
            
        Returns:
            Contact in Microsoft Graph format
        """
        microsoft_contact = {}
        
        # Name fields
        if 'names' in google_contact and google_contact['names']:
            name = google_contact['names'][0]
            microsoft_contact['givenName'] = name.get('givenName', '')
            microsoft_contact['surname'] = name.get('familyName', '')
            microsoft_contact['displayName'] = name.get('displayName', '')
        
        # Email addresses
        if 'emailAddresses' in google_contact:
            microsoft_contact['emailAddresses'] = [
                {'address': email['value'], 'name': email.get('type', 'other')}
                for email in google_contact['emailAddresses']
            ]
        
        # Phone numbers
        if 'phoneNumbers' in google_contact:
            business_phones = []
            home_phones = []
            mobile_phone = None
            
            for phone in google_contact['phoneNumbers']:
                value = phone.get('value', '')
                phone_type = phone.get('type', '').lower()
                
                if 'work' in phone_type or 'business' in phone_type:
                    business_phones.append(value)
                elif 'home' in phone_type:
                    home_phones.append(value)
                elif 'mobile' in phone_type:
                    mobile_phone = value
                else:
                    business_phones.append(value)
            
            if business_phones:
                microsoft_contact['businessPhones'] = business_phones
            if home_phones:
                microsoft_contact['homePhones'] = home_phones
            if mobile_phone:
                microsoft_contact['mobilePhone'] = mobile_phone
        
        return microsoft_contact
