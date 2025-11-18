"""
Test data generators using factory pattern.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
import random
import string


class DataFactory:
    """Base factory for generating test data."""
    
    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate a random string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def random_email() -> str:
        """Generate a random email address."""
        username = DataFactory.random_string(8).lower()
        domain = random.choice(['example.com', 'test.com', 'demo.org'])
        return f"{username}@{domain}"
    
    @staticmethod
    def random_datetime(days_offset: int = 0) -> datetime:
        """Generate a random datetime."""
        base = datetime.now() + timedelta(days=days_offset)
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)
        return base.replace(hour=random_hours, minute=random_minutes, second=0, microsecond=0)


class EventFactory(DataFactory):
    """Factory for generating test calendar events."""
    
    @classmethod
    def create(cls, **kwargs) -> Dict[str, Any]:
        """Create a test calendar event."""
        event_id = kwargs.get('id', f'event_{cls.random_string(6)}')
        summary = kwargs.get('summary', f'Test Event {cls.random_string(4)}')
        
        start_time = kwargs.get('start_time', cls.random_datetime())
        duration_hours = kwargs.get('duration_hours', 1)
        end_time = start_time + timedelta(hours=duration_hours)
        
        return {
            'id': event_id,
            'summary': summary,
            'description': kwargs.get('description', f'Description for {summary}'),
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': kwargs.get('timezone', 'America/New_York'),
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': kwargs.get('timezone', 'America/New_York'),
            },
            'status': kwargs.get('status', 'confirmed'),
            'creator': {
                'email': kwargs.get('creator_email', cls.random_email()),
            },
        }
    
    @classmethod
    def create_batch(cls, count: int = 5, **kwargs) -> list:
        """Create multiple test events."""
        return [cls.create(**kwargs) for _ in range(count)]


class EmailFactory(DataFactory):
    """Factory for generating test emails."""
    
    @classmethod
    def create(cls, **kwargs) -> Dict[str, Any]:
        """Create a test email message."""
        msg_id = kwargs.get('id', f'msg_{cls.random_string(8)}')
        thread_id = kwargs.get('threadId', f'thread_{cls.random_string(8)}')
        
        subject = kwargs.get('subject', f'Test Email {cls.random_string(4)}')
        snippet = kwargs.get('snippet', f'This is a test email snippet {cls.random_string(10)}...')
        
        from_email = kwargs.get('from_email', cls.random_email())
        to_email = kwargs.get('to_email', cls.random_email())
        
        return {
            'id': msg_id,
            'threadId': thread_id,
            'labelIds': kwargs.get('labelIds', ['INBOX']),
            'snippet': snippet,
            'payload': {
                'headers': [
                    {'name': 'From', 'value': from_email},
                    {'name': 'To', 'value': to_email},
                    {'name': 'Subject', 'value': subject},
                    {'name': 'Date', 'value': datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')},
                ],
                'body': {
                    'data': kwargs.get('body', 'VGVzdCBlbWFpbCBib2R5'),  # Base64 encoded
                },
            },
        }
    
    @classmethod
    def create_batch(cls, count: int = 5, **kwargs) -> list:
        """Create multiple test emails."""
        return [cls.create(**kwargs) for _ in range(count)]


class ContactFactory(DataFactory):
    """Factory for generating test contacts."""
    
    _first_names = ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Diana', 'Eve', 'Frank']
    _last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
    
    @classmethod
    def create(cls, **kwargs) -> Dict[str, Any]:
        """Create a test contact."""
        resource_name = kwargs.get('resourceName', f'people/{cls.random_string(8)}')
        
        first_name = kwargs.get('givenName', random.choice(cls._first_names))
        last_name = kwargs.get('familyName', random.choice(cls._last_names))
        display_name = f"{first_name} {last_name}"
        
        email = kwargs.get('email', f"{first_name.lower()}.{last_name.lower()}@example.com")
        
        return {
            'resourceName': resource_name,
            'etag': kwargs.get('etag', cls.random_string(12)),
            'names': [
                {
                    'displayName': display_name,
                    'familyName': last_name,
                    'givenName': first_name,
                },
            ],
            'emailAddresses': [
                {
                    'value': email,
                    'type': kwargs.get('email_type', 'work'),
                },
            ],
            'phoneNumbers': kwargs.get('phoneNumbers', [
                {
                    'value': f'+1-555-{random.randint(1000, 9999)}',
                    'type': 'mobile',
                },
            ]) if kwargs.get('include_phone', True) else [],
        }
    
    @classmethod
    def create_batch(cls, count: int = 5, **kwargs) -> list:
        """Create multiple test contacts."""
        return [cls.create(**kwargs) for _ in range(count)]


class TokenFactory(DataFactory):
    """Factory for generating test OAuth tokens."""
    
    @classmethod
    def create(cls, provider: str = 'google', **kwargs) -> Dict[str, Any]:
        """Create a test OAuth token."""
        token = {
            'access_token': kwargs.get('access_token', f'{provider}_access_{cls.random_string(16)}'),
            'token_type': kwargs.get('token_type', 'Bearer'),
            'expires_in': kwargs.get('expires_in', 3600),
            'scope': kwargs.get('scope', 'test_scope'),
        }
        
        if kwargs.get('include_refresh', True):
            token['refresh_token'] = kwargs.get('refresh_token', f'{provider}_refresh_{cls.random_string(16)}')
        
        # Provider-specific fields
        if provider == 'microsoft':
            token['id_token'] = kwargs.get('id_token', f'id_token_{cls.random_string(16)}')
            token['ext_expires_in'] = kwargs.get('ext_expires_in', 3600)
        
        return token
    
    @classmethod
    def create_expired(cls, provider: str = 'google', **kwargs) -> Dict[str, Any]:
        """Create an expired test OAuth token."""
        kwargs['expires_in'] = -3600  # Expired 1 hour ago
        return cls.create(provider, **kwargs)


# Convenience functions

def create_test_event(**kwargs) -> Dict[str, Any]:
    """Create a single test event."""
    return EventFactory.create(**kwargs)


def create_test_events(count: int = 5, **kwargs) -> list:
    """Create multiple test events."""
    return EventFactory.create_batch(count, **kwargs)


def create_test_email(**kwargs) -> Dict[str, Any]:
    """Create a single test email."""
    return EmailFactory.create(**kwargs)


def create_test_emails(count: int = 5, **kwargs) -> list:
    """Create multiple test emails."""
    return EmailFactory.create_batch(count, **kwargs)


def create_test_contact(**kwargs) -> Dict[str, Any]:
    """Create a single test contact."""
    return ContactFactory.create(**kwargs)


def create_test_contacts(count: int = 5, **kwargs) -> list:
    """Create multiple test contacts."""
    return ContactFactory.create_batch(count, **kwargs)


def create_test_token(provider: str = 'google', **kwargs) -> Dict[str, Any]:
    """Create a test OAuth token."""
    return TokenFactory.create(provider, **kwargs)
