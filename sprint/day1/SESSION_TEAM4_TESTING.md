# Team 4: Testing Infrastructure - Task Session

**Agent**: @day1-team4-testing  
**Session Started**: 2025-11-19  
**Status**: 🟢 ACTIVE - Independent Track  
**Orchestrator**: @day1-orchestrator

---

## 🎯 Your Mission

Build comprehensive automated testing infrastructure with 90%+ code coverage. Create mock servers, test fixtures, and CI/CD pipeline.

**Your Agent**: `sprint/day1/team4_testing/team4_agent.py` can execute autonomously!

---

## 🚀 Execute Your Agent

```bash
cd sprint/day1/team4_testing
python3 team4_agent.py
```

---

## 📋 Hour 1-2: Testing Framework Setup

### Install Testing Dependencies

```bash
pip install pytest pytest-cov pytest-mock responses faker hypothesis
```

### Create Test Directory Structure

```bash
mkdir -p tests/{unit,integration,fixtures}
mkdir -p tests/unit/{oauth,api,security}
```

### Configure pytest

**File**: `pytest.ini` (if not exists)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=integrations
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
```

### Create conftest.py

**File**: `tests/conftest.py`

```python
import pytest
from faker import Faker

@pytest.fixture
def fake():
    """Faker instance for test data generation"""
    return Faker()

@pytest.fixture
def mock_oauth_tokens():
    """Mock OAuth tokens"""
    return {
        'access_token': 'mock_access_token_12345',
        'refresh_token': 'mock_refresh_token_67890',
        'expires_in': 3600,
        'token_type': 'Bearer'
    }

@pytest.fixture
def mock_google_event():
    """Mock Google Calendar event"""
    return {
        'id': 'event123',
        'summary': 'Test Event',
        'description': 'Test Description',
        'start': {'dateTime': '2025-11-20T10:00:00Z'},
        'end': {'dateTime': '2025-11-20T11:00:00Z'}
    }
```

---

## 📋 Hour 3-4: OAuth Flow Testing

### Create OAuth Fixtures

**File**: `tests/fixtures/oauth_fixtures.py`

```python
import pytest
import responses


@pytest.fixture
def mock_google_oauth_server():
    """Mock Google OAuth server"""
    @responses.activate
    def _mock():
        # Mock authorization endpoint
        responses.add(
            responses.POST,
            'https://oauth2.googleapis.com/token',
            json={
                'access_token': 'mock_access_token',
                'refresh_token': 'mock_refresh_token',
                'expires_in': 3600,
                'token_type': 'Bearer'
            },
            status=200
        )
        return responses
    return _mock


@pytest.fixture
def mock_microsoft_oauth_server():
    """Mock Microsoft OAuth server"""
    @responses.activate
    def _mock():
        responses.add(
            responses.POST,
            'https://login.microsoftonline.com/common/oauth2/v2.0/token',
            json={
                'access_token': 'mock_access_token',
                'refresh_token': 'mock_refresh_token',
                'id_token': 'mock.id.token',
                'expires_in': 3600
            },
            status=200
        )
        return responses
    return _mock
```

### Create OAuth Tests

**File**: `tests/unit/oauth/test_google_oauth.py`

```python
import pytest
import responses
from integrations.oauth.google_oauth import GoogleOAuthHandler


@responses.activate
def test_get_authorization_url():
    """Test Google OAuth authorization URL generation"""
    handler = GoogleOAuthHandler()
    url = handler.get_authorization_url(state='test_state')
    
    assert 'https://accounts.google.com/o/oauth2/v2/auth' in url
    assert 'client_id=' in url
    assert 'state=test_state' in url
    assert 'scope=' in url


@responses.activate
def test_exchange_code_for_token():
    """Test authorization code exchange"""
    responses.add(
        responses.POST,
        'https://oauth2.googleapis.com/token',
        json={
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 3600
        },
        status=200
    )
    
    handler = GoogleOAuthHandler()
    tokens = handler.exchange_code_for_token('test_code')
    
    assert tokens['access_token'] == 'test_access_token'
    assert tokens['refresh_token'] == 'test_refresh_token'


@responses.activate
def test_refresh_token():
    """Test token refresh"""
    responses.add(
        responses.POST,
        'https://oauth2.googleapis.com/token',
        json={
            'access_token': 'new_access_token',
            'expires_in': 3600
        },
        status=200
    )
    
    handler = GoogleOAuthHandler()
    tokens = handler.refresh_token('old_refresh_token')
    
    assert tokens['access_token'] == 'new_access_token'


def test_revoke_token():
    """Test token revocation"""
    # Add test
    pass


def test_validate_token():
    """Test token validation"""
    # Add test
    pass
```

Create similar tests for Microsoft OAuth (15+ tests total).

---

## 📋 Hour 5-6: API Integration Testing

### Create Mock API Servers

**File**: `tests/fixtures/api_fixtures.py`

```python
import pytest
import responses
from faker import Faker


@pytest.fixture
def mock_google_calendar_api():
    """Mock Google Calendar API"""
    @responses.activate
    def _mock():
        # List calendars
        responses.add(
            responses.GET,
            'https://www.googleapis.com/calendar/v3/users/me/calendarList',
            json={'items': []},
            status=200
        )
        
        # Create event
        responses.add(
            responses.POST,
            'https://www.googleapis.com/calendar/v3/calendars/primary/events',
            json={'id': 'event123'},
            status=201
        )
        
        return responses
    return _mock


@pytest.fixture
def generate_calendar_events():
    """Generate fake calendar events"""
    fake = Faker()
    
    def _generate(count=5):
        events = []
        for _ in range(count):
            events.append({
                'id': fake.uuid4(),
                'summary': fake.sentence(nb_words=3),
                'description': fake.text(),
                'start': {'dateTime': fake.future_datetime().isoformat()},
                'end': {'dateTime': fake.future_datetime().isoformat()}
            })
        return events
    return _generate
```

### Create API Tests

**File**: `tests/unit/api/test_calendar_client.py`

```python
import pytest
import responses
from integrations.google.wrappers.calendar_wrapper import GoogleCalendarWrapper


@responses.activate
def test_list_calendars(mock_google_calendar_api):
    """Test listing calendars"""
    # Implementation
    pass


@responses.activate
def test_create_event(mock_google_calendar_api):
    """Test creating event"""
    # Implementation
    pass


@responses.activate
def test_retry_on_failure():
    """Test retry logic with exponential backoff"""
    # Mock API failure then success
    responses.add(
        responses.POST,
        'https://www.googleapis.com/calendar/v3/calendars/primary/events',
        status=500
    )
    responses.add(
        responses.POST,
        'https://www.googleapis.com/calendar/v3/calendars/primary/events',
        json={'id': 'event123'},
        status=201
    )
    
    # Should retry and succeed
    # Implementation
    pass


def test_rate_limiting():
    """Test rate limiting enforcement"""
    # Implementation
    pass


def test_pagination_handling():
    """Test automatic pagination"""
    # Implementation
    pass
```

Create similar tests for Gmail and Contacts (30+ tests total).

---

## 📋 Hour 7-8: CI/CD Pipeline

### Create GitHub Actions Workflow

**File**: `.github/workflows/day1-tests.yml`

```yaml
name: Day 1 Testing Pipeline

on:
  push:
    branches: [ main, copilot/reactivate-custom-agents ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-mock responses faker
      
      - name: Run linting
        run: |
          pip install flake8 black
          flake8 integrations tests --max-line-length=100
          black --check integrations tests
      
      - name: Run tests
        run: |
          pytest tests/ --cov=integrations --cov-report=xml --cov-report=term-missing -v
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

### Add Code Quality Checks

```bash
# Run locally
flake8 integrations tests --max-line-length=100
black integrations tests
pytest --cov=integrations --cov-report=term-missing
```

---

## 📊 Progress Checklist

- [ ] pytest framework configured
- [ ] Test directory structure created
- [ ] conftest.py with fixtures
- [ ] Mock OAuth servers (Google, Microsoft)
- [ ] 20+ OAuth flow tests passing
- [ ] Mock API servers (Calendar, Gmail, Contacts)
- [ ] 30+ API integration tests passing
- [ ] Test data generators with Faker
- [ ] 90%+ code coverage on critical paths
- [ ] GitHub Actions CI/CD pipeline
- [ ] Code quality checks (flake8, black)

---

## 🔄 Communication

```python
orchestrator.receive_message(
    team_id='team4',
    message=f'52 tests passing, 92% coverage achieved',
    priority=TaskPriority.MEDIUM
)
```

---

## 🎯 Success Criteria

- ✅ 50+ tests passing
- ✅ 90%+ coverage on OAuth and API code
- ✅ Mock servers for all external APIs
- ✅ CI/CD pipeline operational
- ✅ Code quality checks passing

**Let's build that safety net! 🚀**
