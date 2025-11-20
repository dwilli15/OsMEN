#!/usr/bin/env python3
from typing import Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
import requests

class GoogleContactsWrapper:
    def __init__(self, oauth_handler=None):
        self.oauth_handler = oauth_handler
        self.base_url = 'https://people.googleapis.com/v1'
        self._access_token = None
    
    def _get_headers(self) -> Dict:
        token = self._access_token
        if self.oauth_handler:
            token_data = self.oauth_handler.get_token()
            token = token_data.get('access_token')
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def list_contacts(self, page_size: int = 100) -> List[Dict]:
        """List contacts"""
        url = f"{self.base_url}/people/me/connections"
        params = {'personFields': 'names,emailAddresses,phoneNumbers', 'pageSize': page_size}
        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json().get('connections', [])
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def create_contact(self, contact_data: Dict) -> Dict:
        """Create contact"""
        url = f"{self.base_url}/people:createContact"
        response = requests.post(url, json=contact_data, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def search_contacts(self, query: str) -> List[Dict]:
        """Search contacts"""
        url = f"{self.base_url}/people:searchContacts"
        params = {'query': query, 'pageSize': 50, 'readMask': 'names,emailAddresses,phoneNumbers'}
        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        results = response.json().get('results', [])
        return [r.get('person') for r in results if 'person' in r]
