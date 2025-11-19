#!/usr/bin/env python3
from typing import Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
import requests

class GoogleGmailWrapper:
    def __init__(self, oauth_handler=None):
        self.oauth_handler = oauth_handler
        self.base_url = 'https://gmail.googleapis.com/gmail/v1'
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
    def send_email(self, to: str, subject: str, body: str, html: bool = False) -> Dict:
        """Send email"""
        import base64
        from email.mime.text import MIMEText
        message = MIMEText(body, 'html' if html else 'plain')
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        url = f"{self.base_url}/users/me/messages/send"
        response = requests.post(url, json={'raw': raw}, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def list_messages(self, query: str = None, max_results: int = 100) -> List[Dict]:
        """List messages"""
        url = f"{self.base_url}/users/me/messages"
        params = {'maxResults': min(max_results, 500)}
        if query:
            params['q'] = query
        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json().get('messages', [])
