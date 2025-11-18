# Team 3: API Client Generation - Day 1 TODO List

**Day 1 Focus**: API Client Auto-Generation

**Team Focus**: Set up openapi-generator and auto-generate Python clients for all 3 Google APIs

**Timeline**: Day 1 - 8 hours

**Team Lead**: Automation Engineer

---

## 🎯 Primary Objectives

- [ ] Install and configure openapi-generator
- [ ] Generate Google Calendar API Python client
- [ ] Generate Gmail API Python client
- [ ] Generate Google Contacts/People API Python client
- [ ] Create unified API wrapper template
- [ ] Build retry/backoff decorator
- [ ] Add rate limiting handler
- [ ] Create API response normalizer

---

## 📋 Detailed Task List

### Hour 1-2: OpenAPI Generator Setup

#### Installation and Configuration
- [ ] Research and select openapi-generator installation method
  - [ ] Option 1: NPM (recommended for CI/CD)
    ```bash
    npm install -g @openapitools/openapi-generator-cli
    ```
  - [ ] Option 2: Homebrew (for Mac development)
    ```bash
    brew install openapi-generator
    ```
  - [ ] Option 3: Docker (for consistent environments)
    ```bash
    docker pull openapitools/openapi-generator-cli
    ```
- [ ] Install chosen method
- [ ] Verify installation
  ```bash
  openapi-generator-cli version  # or openapi-generator version
  ```
- [ ] Test with sample OpenAPI spec

#### Generator Configuration
- [ ] Create `scripts/automation/openapi_configs/` directory
- [ ] Create Python client configuration file
  - [ ] `python_client_config.yaml`
    ```yaml
    packageName: osmen_api_client
    projectName: osmen-api-client
    packageVersion: 1.0.0
    pythonVersion: 3.12
    library: urllib3
    generateSourceCodeOnly: false
    ```
- [ ] Create generator wrapper script
  - [ ] `scripts/automation/generate_api_client.sh`
    ```bash
    #!/bin/bash
    # Generate Python API client from OpenAPI spec
    # Usage: ./generate_api_client.sh <spec_url> <output_dir> <package_name>
    
    SPEC_URL=$1
    OUTPUT_DIR=$2
    PACKAGE_NAME=$3
    
    openapi-generator-cli generate \
      -i "$SPEC_URL" \
      -g python \
      -o "$OUTPUT_DIR" \
      -c scripts/automation/openapi_configs/python_client_config.yaml \
      --package-name "$PACKAGE_NAME"
    ```
- [ ] Make script executable
  ```bash
  chmod +x scripts/automation/generate_api_client.sh
  ```
- [ ] Test script with simple spec

#### Documentation
- [ ] Create `scripts/automation/README.md`
- [ ] Document how to use generator script
- [ ] Document how to regenerate clients
- [ ] Document configuration options
- [ ] Add troubleshooting section

---

### Hour 3-4: Google Calendar API Client Generation

#### Obtain OpenAPI Spec
- [ ] Research Google Calendar API v3 OpenAPI spec
  - [ ] Check Google API Discovery Service
    ```
    https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest
    ```
  - [ ] Convert Discovery Document to OpenAPI if needed
  - [ ] Or find pre-converted OpenAPI 3.0 spec
- [ ] Download and save spec
  - [ ] Create `specs/` directory
  - [ ] Save as `specs/google_calendar_v3.json` or `.yaml`
- [ ] Validate OpenAPI spec
  ```bash
  openapi-generator-cli validate -i specs/google_calendar_v3.json
  ```
- [ ] Fix any validation errors

#### Generate Calendar Client
- [ ] Run generator for Calendar API
  ```bash
  ./scripts/automation/generate_api_client.sh \
    specs/google_calendar_v3.json \
    integrations/google/calendar_client \
    osmen_google_calendar
  ```
- [ ] Review generated code structure
  ```
  integrations/google/calendar_client/
  ├── osmen_google_calendar/
  │   ├── __init__.py
  │   ├── api/
  │   ├── models/
  │   ├── api_client.py
  │   ├── configuration.py
  │   └── rest.py
  ├── setup.py
  ├── requirements.txt
  └── README.md
  ```
- [ ] Install generated client
  ```bash
  cd integrations/google/calendar_client
  pip install -e .
  ```
- [ ] Test import
  ```python
  from osmen_google_calendar import ApiClient, Configuration
  from osmen_google_calendar.api import EventsApi, CalendarsApi
  ```

#### Create Calendar API Wrapper
- [ ] Create `integrations/google/calendar_wrapper.py`
- [ ] Implement `CalendarAPIWrapper` class
  ```python
  from osmen_google_calendar import ApiClient, Configuration
  from osmen_google_calendar.api import EventsApi, CalendarsApi
  
  class CalendarAPIWrapper:
      """High-level wrapper for Google Calendar API."""
      
      def __init__(self, access_token: str):
          config = Configuration()
          config.access_token = access_token
          self.api_client = ApiClient(configuration=config)
          self.events_api = EventsApi(self.api_client)
          self.calendars_api = CalendarsApi(self.api_client)
  ```
- [ ] Implement convenience methods
  - [ ] `list_calendars()` - List all calendars
  - [ ] `list_events(calendar_id, start, end)` - List events in date range
  - [ ] `create_event(calendar_id, event)` - Create new event
  - [ ] `get_event(calendar_id, event_id)` - Get event details
  - [ ] `update_event(calendar_id, event_id, event)` - Update event
  - [ ] `delete_event(calendar_id, event_id)` - Delete event
- [ ] Add helper methods
  - [ ] `quick_add(calendar_id, text)` - Create event from natural language
  - [ ] `get_free_busy(calendar_ids, start, end)` - Check availability

---

### Hour 5-6: Gmail API Client Generation

#### Obtain OpenAPI Spec
- [ ] Research Gmail API v1 OpenAPI spec
  - [ ] Check Google API Discovery Service
    ```
    https://www.googleapis.com/discovery/v1/apis/gmail/v1/rest
    ```
  - [ ] Convert or find OpenAPI spec
- [ ] Download and save spec
  - [ ] Save as `specs/gmail_v1.json` or `.yaml`
- [ ] Validate spec
  ```bash
  openapi-generator-cli validate -i specs/gmail_v1.json
  ```

#### Generate Gmail Client
- [ ] Run generator for Gmail API
  ```bash
  ./scripts/automation/generate_api_client.sh \
    specs/gmail_v1.json \
    integrations/google/gmail_client \
    osmen_google_gmail
  ```
- [ ] Review generated code
- [ ] Install generated client
  ```bash
  cd integrations/google/gmail_client
  pip install -e .
  ```
- [ ] Test import

#### Create Gmail API Wrapper
- [ ] Create `integrations/google/gmail_wrapper.py`
- [ ] Implement `GmailAPIWrapper` class
  ```python
  from osmen_google_gmail import ApiClient, Configuration
  from osmen_google_gmail.api import UsersMessagesApi, UsersLabelsApi
  
  class GmailAPIWrapper:
      """High-level wrapper for Gmail API."""
      
      def __init__(self, access_token: str):
          config = Configuration()
          config.access_token = access_token
          self.api_client = ApiClient(configuration=config)
          self.messages_api = UsersMessagesApi(self.api_client)
          self.labels_api = UsersLabelsApi(self.api_client)
  ```
- [ ] Implement convenience methods
  - [ ] `list_messages(query, max_results)` - List/search messages
  - [ ] `get_message(message_id)` - Get full message
  - [ ] `send_message(to, subject, body, html=False)` - Send email
  - [ ] `send_message_with_attachment(to, subject, body, files)` - Send with attachments
  - [ ] `delete_message(message_id)` - Delete message
  - [ ] `trash_message(message_id)` - Move to trash
  - [ ] `modify_labels(message_id, add_labels, remove_labels)` - Manage labels
- [ ] Add helper methods
  - [ ] `create_draft(to, subject, body)` - Create draft
  - [ ] `send_draft(draft_id)` - Send existing draft
  - [ ] `search_messages(query)` - Gmail search syntax

---

### Hour 7-8: Google Contacts API and Unified Infrastructure

#### Obtain OpenAPI Spec (People API)
- [ ] Research Google People API v1 (Contacts)
  - [ ] Check Discovery Service
    ```
    https://www.googleapis.com/discovery/v1/apis/people/v1/rest
    ```
  - [ ] Find or convert OpenAPI spec
- [ ] Download and save spec
  - [ ] Save as `specs/google_people_v1.json` or `.yaml`
- [ ] Validate spec

#### Generate Contacts Client
- [ ] Run generator for People/Contacts API
  ```bash
  ./scripts/automation/generate_api_client.sh \
    specs/google_people_v1.json \
    integrations/google/contacts_client \
    osmen_google_contacts
  ```
- [ ] Install generated client
  ```bash
  cd integrations/google/contacts_client
  pip install -e .
  ```

#### Create Contacts API Wrapper
- [ ] Create `integrations/google/contacts_wrapper.py`
- [ ] Implement `ContactsAPIWrapper` class
  ```python
  from osmen_google_contacts import ApiClient, Configuration
  from osmen_google_contacts.api import PeopleApi, ContactGroupsApi
  
  class ContactsAPIWrapper:
      """High-level wrapper for Google People/Contacts API."""
      
      def __init__(self, access_token: str):
          config = Configuration()
          config.access_token = access_token
          self.api_client = ApiClient(configuration=config)
          self.people_api = PeopleApi(self.api_client)
          self.groups_api = ContactGroupsApi(self.api_client)
  ```
- [ ] Implement convenience methods
  - [ ] `list_contacts(page_size)` - List all contacts
  - [ ] `get_contact(resource_name)` - Get contact details
  - [ ] `create_contact(contact)` - Create new contact
  - [ ] `update_contact(resource_name, contact)` - Update contact
  - [ ] `delete_contact(resource_name)` - Delete contact
  - [ ] `search_contacts(query)` - Search contacts
  - [ ] `list_contact_groups()` - List groups
  - [ ] `create_contact_group(name)` - Create group

#### Unified API Infrastructure
- [ ] Create `integrations/google/base_wrapper.py`
- [ ] Implement `GoogleAPIWrapperBase` class
  ```python
  class GoogleAPIWrapperBase:
      """Base class for all Google API wrappers."""
      
      def __init__(self, access_token: str):
          self.access_token = access_token
          self._setup_client()
      
      @abstractmethod
      def _setup_client(self):
          """Set up the API client (implemented by subclasses)."""
          pass
  ```
- [ ] Add common functionality
  - [ ] Token injection
  - [ ] Error handling
  - [ ] Logging
  - [ ] Retry logic (see below)
  - [ ] Rate limiting (see below)

#### Retry/Backoff Decorator
- [ ] Create `integrations/utils/retry.py`
- [ ] Implement retry decorator with exponential backoff
  ```python
  import time
  from functools import wraps
  
  def retry_with_backoff(max_retries=3, base_delay=1, max_delay=60):
      """Retry with exponential backoff."""
      def decorator(func):
          @wraps(func)
          def wrapper(*args, **kwargs):
              retries = 0
              while retries < max_retries:
                  try:
                      return func(*args, **kwargs)
                  except Exception as e:
                      retries += 1
                      if retries >= max_retries:
                          raise
                      delay = min(base_delay * (2 ** retries), max_delay)
                      time.sleep(delay)
              return wrapper
      return decorator
  ```
- [ ] Configure retry for specific error codes
  - [ ] 429 (Rate Limit)
  - [ ] 500 (Internal Server Error)
  - [ ] 503 (Service Unavailable)
  - [ ] Network errors (timeout, connection)

#### Rate Limiting Handler
- [ ] Create `integrations/utils/rate_limit.py`
- [ ] Implement rate limiter using token bucket algorithm
  ```python
  import time
  from collections import defaultdict
  
  class RateLimiter:
      """Token bucket rate limiter."""
      
      def __init__(self, requests_per_second=10):
          self.rate = requests_per_second
          self.tokens = defaultdict(lambda: self.rate)
          self.last_update = defaultdict(time.time)
      
      def acquire(self, key='default'):
          """Acquire permission to make a request."""
          # Implement token bucket logic
  ```
- [ ] Add rate limit decorator
  ```python
  @rate_limit(requests_per_second=10)
  def api_call():
      pass
  ```

#### API Response Normalizer
- [ ] Create `integrations/utils/response_normalizer.py`
- [ ] Implement response normalization
  ```python
  def normalize_response(response, api_type='google'):
      """Normalize API responses to a common format."""
      return {
          'success': True,
          'data': response,
          'api_type': api_type,
          'timestamp': datetime.now().isoformat()
      }
  
  def normalize_error(error, api_type='google'):
      """Normalize API errors to a common format."""
      return {
          'success': False,
          'error': str(error),
          'error_code': getattr(error, 'code', None),
          'api_type': api_type,
          'timestamp': datetime.now().isoformat()
      }
  ```

---

## 🧪 Testing Requirements

### Unit Tests (15+ tests)
- [ ] Test Calendar wrapper initialization
- [ ] Test Calendar methods (list, create, update, delete)
- [ ] Test Gmail wrapper initialization
- [ ] Test Gmail methods (list, send, delete)
- [ ] Test Contacts wrapper initialization
- [ ] Test Contacts methods (list, create, update)
- [ ] Test retry decorator
  - [ ] Test successful retry
  - [ ] Test max retries exceeded
  - [ ] Test exponential backoff timing
- [ ] Test rate limiter
  - [ ] Test token bucket algorithm
  - [ ] Test rate enforcement
- [ ] Test response normalizer
  - [ ] Test success responses
  - [ ] Test error responses

### Integration Tests (with mocks)
- [ ] Test OAuth token injection into API clients
- [ ] Test error handling and retry
- [ ] Test rate limiting in action
- [ ] Test end-to-end API calls (mocked)

---

## 📦 Dependencies

### System Dependencies
```bash
# Choose one:
npm install -g @openapitools/openapi-generator-cli  # Option 1
brew install openapi-generator  # Option 2
docker pull openapitools/openapi-generator-cli  # Option 3
```

### Python Packages
```python
# Add to requirements.txt
requests>=2.31.0
urllib3>=2.0.0
python-dateutil>=2.8.2
pyyaml>=6.0
tenacity>=8.2.0  # Alternative retry library
pytest>=7.4.0
pytest-mock>=3.11.0
responses>=0.23.0
```

---

## 📊 Success Metrics

### End of Day 1 Deliverables
- [ ] openapi-generator configured and working
- [ ] Google Calendar API client generated
- [ ] Gmail API client generated
- [ ] Google Contacts/People API client generated
- [ ] Calendar wrapper with convenience methods
- [ ] Gmail wrapper with convenience methods
- [ ] Contacts wrapper with convenience methods
- [ ] Base wrapper class with common functionality
- [ ] Retry/backoff decorator functional
- [ ] Rate limiting handler implemented
- [ ] API response normalizer implemented
- [ ] 15+ unit tests passing
- [ ] Documentation complete
- [ ] Ready for Team 1 OAuth token injection
- [ ] Ready for Day 2 Microsoft API generation

---

## 🚀 Handoff to Other Teams

### For Team 1 (Google OAuth)
- API clients ready to receive OAuth tokens
- Token injection interface defined
- Example of how to initialize with tokens

### For Team 2 (Microsoft OAuth - Day 2)
- Generator framework ready for Microsoft Graph APIs
- Pattern established for API wrappers
- Utilities (retry, rate limit) ready to reuse

### For Team 4 (Testing)
- Generated clients ready for testing
- Wrappers ready for integration tests
- Mock patterns defined

### For Day 2 Teams
- Complete API client generation pipeline
- Reusable for Outlook APIs
- Documentation on regenerating clients

---

## 📝 Notes

- Don't modify generated code directly - use wrappers
- Keep generated code in separate directory
- Document regeneration process clearly
- Test wrappers, not generated code
- Use retry and rate limiting on all API calls
- Normalize responses for consistent handling
- Follow Google API best practices
- Implement pagination for list methods
- Handle OAuth token refresh in wrappers
- Log API calls (but not request/response bodies)

---

**Team Contact**: Automation Engineer  
**Status Updates**: Every 2 hours to Orchestration  
**Blockers**: Report immediately  
**Dependency**: Team 1 OAuth for token injection testing

---

## 🎯 Ready to Execute!

Automate ALL the things! Let the generator do the heavy lifting!

**LET'S BUILD! 🚀**
