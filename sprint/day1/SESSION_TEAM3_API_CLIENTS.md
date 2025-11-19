# Team 3: API Client Generation - Task Session

**Agent**: @day1-team3-api-clients  
**Session Started**: 2025-11-19  
**Status**: 🟢 ACTIVE - Independent Track  
**Orchestrator**: @day1-orchestrator

---

## 🎯 Your Mission

Set up automated API client generation infrastructure and create production-ready Python clients for Google Calendar, Gmail, and Contacts APIs.

**Your Agent**: `sprint/day1/team3_api_clients/team3_agent.py` can execute autonomously!

---

## 🚀 Execute Your Agent

```bash
cd sprint/day1/team3_api_clients
python3 team3_agent.py
```

Your agent will handle much of the implementation. Monitor and guide as needed.

---

## 📋 Hour 1-2: OpenAPI Generator Setup

### Install OpenAPI Generator

**Option 1: NPM (Recommended)**
```bash
npm install -g @openapitools/openapi-generator-cli
```

**Option 2: Docker**
```bash
docker pull openapitools/openapi-generator-cli
```

**Option 3: Python**
```bash
pip install openapi-generator-cli
```

### Create Directory Structure

```bash
mkdir -p integrations/google/generated/{calendar,gmail,contacts}
mkdir -p integrations/google/wrappers
```

### Test Generation

```bash
# Test with simple example
openapi-generator-cli generate \
  -i https://petstore3.swagger.io/api/v3/openapi.json \
  -g python \
  -o /tmp/test-client

# Verify it works
ls /tmp/test-client
```

---

## 📋 Hour 3-4: Google Calendar API Client

### Download Calendar API Spec

```bash
# Google Discovery API
curl -o /tmp/calendar-api.json \
  'https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest'
```

### Generate Client

```bash
openapi-generator-cli generate \
  -i /tmp/calendar-api.json \
  -g python \
  -o integrations/google/generated/calendar \
  --additional-properties=packageName=google_calendar_client,projectName=google-calendar-client
```

### Create Wrapper

**File**: `integrations/google/wrappers/calendar_wrapper.py`

```python
#!/usr/bin/env python3
"""
Google Calendar API Wrapper
High-level wrapper with retry logic and rate limiting
"""

from typing import Dict, List, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry


class GoogleCalendarWrapper:
    """Unified wrapper for Google Calendar API"""
    
    def __init__(self, oauth_handler):
        """Initialize with OAuth handler"""
        self.oauth = oauth_handler
        # TODO: Initialize generated client
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)  # 10 calls per second
    def list_calendars(self) -> List[Dict]:
        """List all calendars for authenticated user"""
        # Implementation
        pass
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def create_event(self, calendar_id: str, event_data: Dict) -> Dict:
        """Create a new calendar event"""
        # Implementation
        pass
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def get_event(self, calendar_id: str, event_id: str) -> Dict:
        """Get a specific event"""
        # Implementation
        pass
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def update_event(self, calendar_id: str, event_id: str, event_data: Dict) -> Dict:
        """Update an existing event"""
        # Implementation
        pass
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete an event"""
        # Implementation
        pass
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    @sleep_and_retry
    @limits(calls=10, period=1)
    def list_events(self, calendar_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """List events in date range"""
        # Implementation with pagination
        pass
```

### Install Dependencies

```bash
pip install tenacity ratelimit
```

---

## 📋 Hour 5-6: Gmail API Client

### Generate Gmail Client

```bash
curl -o /tmp/gmail-api.json \
  'https://www.googleapis.com/discovery/v1/apis/gmail/v1/rest'

openapi-generator-cli generate \
  -i /tmp/gmail-api.json \
  -g python \
  -o integrations/google/generated/gmail \
  --additional-properties=packageName=google_gmail_client
```

### Create Wrapper

**File**: `integrations/google/wrappers/gmail_wrapper.py`

```python
class GoogleGmailWrapper:
    """Unified wrapper for Gmail API"""
    
    def __init__(self, oauth_handler):
        self.oauth = oauth_handler
    
    @retry_and_rate_limit
    def send_email(self, to: str, subject: str, body: str, html: bool = False) -> Dict:
        """Send an email"""
        pass
    
    @retry_and_rate_limit
    def send_email_with_attachment(self, to: str, subject: str, body: str, 
                                   attachments: List[str]) -> Dict:
        """Send email with attachments"""
        pass
    
    @retry_and_rate_limit
    def list_messages(self, query: Optional[str] = None, max_results: int = 100) -> List[Dict]:
        """List messages (with pagination)"""
        pass
    
    @retry_and_rate_limit
    def get_message(self, message_id: str) -> Dict:
        """Get a specific message"""
        pass
    
    @retry_and_rate_limit
    def search_messages(self, query: str) -> List[Dict]:
        """Search messages"""
        pass
    
    @retry_and_rate_limit
    def create_label(self, name: str) -> Dict:
        """Create a label"""
        pass
    
    @retry_and_rate_limit
    def apply_label(self, message_id: str, label_id: str) -> Dict:
        """Apply label to message"""
        pass
```

---

## 📋 Hour 7-8: Google Contacts API Client

### Generate Contacts Client

```bash
curl -o /tmp/contacts-api.json \
  'https://www.googleapis.com/discovery/v1/apis/people/v1/rest'

openapi-generator-cli generate \
  -i /tmp/contacts-api.json \
  -g python \
  -o integrations/google/generated/contacts \
  --additional-properties=packageName=google_contacts_client
```

### Create Wrapper

**File**: `integrations/google/wrappers/contacts_wrapper.py`

```python
class GoogleContactsWrapper:
    """Unified wrapper for Google Contacts (People) API"""
    
    def __init__(self, oauth_handler):
        self.oauth = oauth_handler
    
    @retry_and_rate_limit
    def list_contacts(self) -> List[Dict]:
        """List all contacts"""
        pass
    
    @retry_and_rate_limit
    def create_contact(self, contact_data: Dict) -> Dict:
        """Create a new contact"""
        pass
    
    @retry_and_rate_limit
    def get_contact(self, resource_name: str) -> Dict:
        """Get a specific contact"""
        pass
    
    @retry_and_rate_limit
    def update_contact(self, resource_name: str, contact_data: Dict) -> Dict:
        """Update a contact"""
        pass
    
    @retry_and_rate_limit
    def delete_contact(self, resource_name: str) -> bool:
        """Delete a contact"""
        pass
    
    @retry_and_rate_limit
    def search_contacts(self, query: str) -> List[Dict]:
        """Search contacts"""
        pass
```

---

## 📊 Progress Checklist

- [ ] openapi-generator-cli installed and tested
- [ ] Calendar API client generated
- [ ] Calendar wrapper with retry/rate limiting
- [ ] Gmail API client generated
- [ ] Gmail wrapper with retry/rate limiting
- [ ] Contacts API client generated
- [ ] Contacts wrapper with retry/rate limiting
- [ ] Dependencies installed (tenacity, ratelimit)
- [ ] 30+ API tests written and passing
- [ ] Code committed

---

## 🔄 Communication

```python
from sprint.day1.orchestration.orchestration_agent import OrchestrationAgent

orchestrator = OrchestrationAgent()

# After each client
orchestrator.receive_message(
    team_id='team3',
    message='Calendar API client generated and wrapped',
    priority=TaskPriority.MEDIUM
)
```

---

## 🎯 Success Criteria

- ✅ 3 API clients generated (Calendar, Gmail, Contacts)
- ✅ 3 wrappers with retry logic and rate limiting
- ✅ Response normalization working
- ✅ Pagination handled automatically
- ✅ 30+ API integration tests passing
- ✅ Integration with Team 1 OAuth tokens

**Let's auto-generate those API clients! 🚀**
