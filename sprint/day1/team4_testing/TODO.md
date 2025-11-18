# Team 4: Testing Infrastructure - Day 1 TODO List

**Day 1 Focus**: Testing Automation

**Team Focus**: Set up comprehensive testing framework, create OAuth and API tests, enhance CI/CD pipeline

**Timeline**: Day 1 - 8 hours

**Team Lead**: QA Engineer

---

## 🎯 Primary Objectives

- [ ] Set up pytest with auto-discovery and coverage tracking
- [ ] Create OAuth flow test fixtures
- [ ] Build mock OAuth server for testing
- [ ] Add API integration test framework
- [ ] Create test data generators
- [ ] Configure GitHub Actions for CI/CD
- [ ] Add automated code quality checks
- [ ] Create performance benchmarking tests
- [ ] Achieve 50+ automated tests passing
- [ ] Reach 90%+ code coverage target

---

## 📋 Detailed Task List

### Hour 1-2: Test Automation Framework Design

#### Test Directory Structure
- [ ] Create comprehensive test directory
  ```
  tests/
  ├── __init__.py
  ├── conftest.py          # Shared fixtures
  ├── unit/                # Unit tests
  │   ├── __init__.py
  │   ├── oauth/
  │   │   ├── test_oauth_handler.py
  │   │   ├── test_google_oauth.py
  │   │   └── test_microsoft_oauth.py
  │   ├── api_clients/
  │   │   ├── test_calendar_wrapper.py
  │   │   ├── test_gmail_wrapper.py
  │   │   └── test_contacts_wrapper.py
  │   └── utils/
  │       ├── test_retry.py
  │       ├── test_rate_limit.py
  │       └── test_encryption.py
  ├── integration/         # Integration tests
  │   ├── __init__.py
  │   ├── test_oauth_flow.py
  │   ├── test_api_integration.py
  │   └── test_end_to_end.py
  ├── fixtures/            # Test data and fixtures
  │   ├── __init__.py
  │   ├── oauth_fixtures.py
  │   ├── api_fixtures.py
  │   └── mock_data.py
  └── mocks/               # Mock servers and services
      ├── __init__.py
      ├── mock_oauth_server.py
      ├── mock_google_api.py
      └── mock_microsoft_api.py
  ```

#### pytest Configuration
- [ ] Create `pytest.ini` in project root
  ```ini
  [pytest]
  testpaths = tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  
  markers =
      unit: Unit tests (fast, no external dependencies)
      integration: Integration tests (slower, may use mocks)
      slow: Slow running tests
      oauth: OAuth related tests
      api: API client tests
      security: Security related tests
  
  addopts =
      --verbose
      --strict-markers
      --tb=short
      --cov=integrations
      --cov=agents
      --cov-report=html:htmlcov
      --cov-report=term-missing
      --cov-report=xml
      --cov-fail-under=90
  ```

- [ ] Create `.coveragerc` for coverage configuration
  ```ini
  [run]
  source = integrations, agents
  omit =
      */tests/*
      */test_*.py
      */__pycache__/*
      */venv/*
      */virtualenv/*
      */.tox/*
  
  [report]
  exclude_lines =
      pragma: no cover
      def __repr__
      raise AssertionError
      raise NotImplementedError
      if __name__ == .__main__.:
      if TYPE_CHECKING:
      @abstractmethod
  ```

#### Install Testing Dependencies
- [ ] Install pytest and plugins
  ```bash
  pip install pytest pytest-cov pytest-mock pytest-asyncio pytest-xdist pytest-timeout pytest-html
  ```
- [ ] Add to requirements.txt
  ```
  pytest>=7.4.0
  pytest-cov>=4.1.0
  pytest-mock>=3.11.0
  pytest-asyncio>=0.21.0
  pytest-xdist>=3.3.0
  pytest-timeout>=2.1.0
  pytest-html>=3.2.0
  coverage>=7.3.0
  faker>=19.0.0
  responses>=0.23.0
  factory-boy>=3.3.0
  ```

---

### Hour 3-4: OAuth Flow Tests

#### Mock OAuth Server
- [ ] Create `tests/mocks/mock_oauth_server.py`
- [ ] Implement mock server using `responses` library
  ```python
  import responses
  from urllib.parse import urlparse, parse_qs
  
  class MockOAuthServer:
      """Mock OAuth server for testing."""
      
      def __init__(self):
          self.auth_codes = {}
          self.tokens = {}
          self.refresh_tokens = {}
      
      @responses.activate
      def mock_authorization_endpoint(self, provider='google'):
          """Mock the authorization endpoint."""
          # Returns authorization URL
          
      @responses.activate
      def mock_token_endpoint(self, provider='google'):
          """Mock the token exchange endpoint."""
          # Returns access and refresh tokens
          
      @responses.activate
      def mock_refresh_endpoint(self, provider='google'):
          """Mock the token refresh endpoint."""
          # Returns new access token
  ```

- [ ] Implement Google OAuth endpoints
  ```python
  @responses.activate
  def mock_google_token_exchange(code):
      responses.add(
          responses.POST,
          'https://oauth2.googleapis.com/token',
          json={
              'access_token': 'mock_access_token_123',
              'expires_in': 3600,
              'refresh_token': 'mock_refresh_token_456',
              'scope': 'calendar gmail contacts',
              'token_type': 'Bearer'
          },
          status=200
      )
  ```

- [ ] Implement Microsoft OAuth endpoints
  ```python
  @responses.activate
  def mock_microsoft_token_exchange(code):
      responses.add(
          responses.POST,
          'https://login.microsoftonline.com/common/oauth2/v2.0/token',
          json={
              'token_type': 'Bearer',
              'scope': 'Calendars.ReadWrite Mail.ReadWrite',
              'expires_in': 3600,
              'access_token': 'mock_access_token_789',
              'refresh_token': 'mock_refresh_token_012',
              'id_token': 'mock_id_token_345'
          },
          status=200
      )
  ```

- [ ] Implement error scenarios
  - [ ] Invalid authorization code
  - [ ] Expired refresh token
  - [ ] Network errors
  - [ ] Rate limit errors

#### OAuth Test Fixtures
- [ ] Create `tests/fixtures/oauth_fixtures.py`
  ```python
  import pytest
  
  @pytest.fixture
  def mock_google_oauth_config():
      return {
          'provider': 'google',
          'client_id': 'test_client_id',
          'client_secret': 'test_client_secret',
          'redirect_uri': 'http://localhost:8080/callback',
          'scopes': [
              'https://www.googleapis.com/auth/calendar',
              'https://www.googleapis.com/auth/gmail.modify'
          ]
      }
  
  @pytest.fixture
  def mock_microsoft_oauth_config():
      return {
          'provider': 'microsoft',
          'client_id': 'test_client_id_ms',
          'client_secret': 'test_client_secret_ms',
          'redirect_uri': 'http://localhost:8080/callback',
          'tenant': 'common',
          'scopes': [
              'https://graph.microsoft.com/Calendars.ReadWrite',
              'offline_access'
          ]
      }
  
  @pytest.fixture
  def mock_token_response():
      return {
          'access_token': 'test_access_token',
          'token_type': 'Bearer',
          'expires_in': 3600,
          'refresh_token': 'test_refresh_token',
          'scope': 'calendar gmail'
      }
  ```

#### OAuth Unit Tests
- [ ] Create `tests/unit/oauth/test_google_oauth.py`
  ```python
  import pytest
  from integrations.oauth.google_oauth import GoogleOAuthHandler
  
  def test_google_authorization_url_generation(mock_google_oauth_config):
      handler = GoogleOAuthHandler(mock_google_oauth_config)
      url = handler.get_authorization_url()
      
      assert 'accounts.google.com' in url
      assert 'client_id=' in url
      assert 'redirect_uri=' in url
      assert 'scope=' in url
      assert 'state=' in url
      assert 'access_type=offline' in url
  
  @responses.activate
  def test_google_token_exchange(mock_google_oauth_config):
      # Mock the token endpoint
      mock_google_token_exchange('test_code')
      
      handler = GoogleOAuthHandler(mock_google_oauth_config)
      tokens = handler.exchange_code_for_token('test_code')
      
      assert tokens['access_token'] == 'mock_access_token_123'
      assert tokens['refresh_token'] == 'mock_refresh_token_456'
      assert 'expires_in' in tokens
  
  # Add 8-10 more tests for Google OAuth
  ```

- [ ] Create `tests/unit/oauth/test_microsoft_oauth.py`
  - [ ] Test authorization URL generation
  - [ ] Test token exchange
  - [ ] Test token refresh
  - [ ] Test id_token parsing
  - [ ] Test tenant handling
  - [ ] Test error handling
  - [ ] Add 8-10 tests total

#### OAuth Integration Tests
- [ ] Create `tests/integration/test_oauth_flow.py`
  ```python
  @responses.activate
  def test_complete_google_oauth_flow():
      """Test complete OAuth flow from auth to token."""
      # 1. Generate authorization URL
      # 2. Simulate user authorization (get code)
      # 3. Exchange code for token
      # 4. Validate token structure
      # 5. Test token storage
  
  @responses.activate
  def test_google_token_refresh_flow():
      """Test token refresh workflow."""
      # 1. Use existing refresh token
      # 2. Request new access token
      # 3. Validate new token
      # 4. Verify token updated in storage
  
  # Add similar tests for Microsoft
  ```

---

### Hour 5-6: API Client and CI/CD Setup

#### API Client Test Fixtures
- [ ] Create `tests/fixtures/api_fixtures.py`
  ```python
  @pytest.fixture
  def mock_calendar_api():
      """Mock Calendar API responses."""
      return {
          'calendars': [
              {'id': 'primary', 'summary': 'Test Calendar'},
              {'id': 'work', 'summary': 'Work Calendar'}
          ],
          'events': [
              {
                  'id': 'event1',
                  'summary': 'Test Event',
                  'start': {'dateTime': '2024-01-01T10:00:00Z'},
                  'end': {'dateTime': '2024-01-01T11:00:00Z'}
              }
          ]
      }
  
  @pytest.fixture
  def mock_gmail_api():
      """Mock Gmail API responses."""
      return {
          'messages': [
              {
                  'id': 'msg1',
                  'threadId': 'thread1',
                  'snippet': 'Test email snippet'
              }
          ]
      }
  ```

#### API Client Tests
- [ ] Create `tests/unit/api_clients/test_calendar_wrapper.py`
  ```python
  @responses.activate
  def test_calendar_list_calendars(mock_calendar_api):
      # Mock the Calendar API list endpoint
      responses.add(
          responses.GET,
          'https://www.googleapis.com/calendar/v3/users/me/calendarList',
          json=mock_calendar_api['calendars'],
          status=200
      )
      
      wrapper = CalendarAPIWrapper('test_token')
      calendars = wrapper.list_calendars()
      
      assert len(calendars) == 2
      assert calendars[0]['summary'] == 'Test Calendar'
  
  # Add 10+ tests for Calendar API operations
  ```

- [ ] Create `tests/unit/api_clients/test_gmail_wrapper.py`
  - [ ] Test list messages
  - [ ] Test send message
  - [ ] Test get message
  - [ ] Test delete message
  - [ ] Add 10+ tests

- [ ] Create `tests/unit/api_clients/test_contacts_wrapper.py`
  - [ ] Test list contacts
  - [ ] Test create contact
  - [ ] Test search contacts
  - [ ] Add 10+ tests

#### GitHub Actions CI/CD
- [ ] Create `.github/workflows/test.yml`
  ```yaml
  name: Test Suite
  
  on:
    push:
      branches: [ main, develop ]
    pull_request:
      branches: [ main, develop ]
  
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
            pip install pytest pytest-cov
        
        - name: Run tests with coverage
          run: |
            pytest --cov --cov-report=xml --cov-report=term-missing
        
        - name: Upload coverage to Codecov
          uses: codecov/codecov-action@v3
          with:
            file: ./coverage.xml
            fail_ci_if_error: true
  ```

- [ ] Create `.github/workflows/lint.yml`
  ```yaml
  name: Code Quality
  
  on: [push, pull_request]
  
  jobs:
    lint:
      runs-on: ubuntu-latest
      
      steps:
        - uses: actions/checkout@v3
        
        - name: Set up Python
          uses: actions/setup-python@v4
          with:
            python-version: '3.12'
        
        - name: Install linters
          run: |
            pip install black flake8 isort mypy pylint
        
        - name: Run Black
          run: black --check --diff .
        
        - name: Run isort
          run: isort --check --diff .
        
        - name: Run Flake8
          run: flake8 integrations/ agents/ --max-line-length=100
        
        - name: Run Pylint
          run: pylint integrations/ agents/ --fail-under=8.0
  ```

---

### Hour 7-8: Test Data Generators and Performance Tests

#### Test Data Generators
- [ ] Create `tests/fixtures/mock_data.py`
  ```python
  from faker import Faker
  import factory
  from datetime import datetime, timedelta
  
  fake = Faker()
  
  class EventFactory(factory.Factory):
      """Factory for generating test calendar events."""
      class Meta:
          model = dict
      
      id = factory.Sequence(lambda n: f'event_{n}')
      summary = factory.LazyAttribute(lambda _: fake.sentence())
      start = factory.LazyAttribute(
          lambda _: {
              'dateTime': datetime.now().isoformat(),
              'timeZone': 'UTC'
          }
      )
      end = factory.LazyAttribute(
          lambda obj: {
              'dateTime': (datetime.fromisoformat(
                  obj['start']['dateTime']
              ) + timedelta(hours=1)).isoformat(),
              'timeZone': 'UTC'
          }
      )
  
  class EmailFactory(factory.Factory):
      """Factory for generating test emails."""
      class Meta:
          model = dict
      
      id = factory.Sequence(lambda n: f'msg_{n}')
      threadId = factory.Sequence(lambda n: f'thread_{n}')
      snippet = factory.LazyAttribute(lambda _: fake.text(max_nb_chars=100))
      subject = factory.LazyAttribute(lambda _: fake.sentence())
      from_email = factory.LazyAttribute(lambda _: fake.email())
      to_email = factory.LazyAttribute(lambda _: fake.email())
  
  class ContactFactory(factory.Factory):
      """Factory for generating test contacts."""
      class Meta:
          model = dict
      
      resourceName = factory.Sequence(lambda n: f'people/{n}')
      names = factory.LazyAttribute(
          lambda _: [{
              'givenName': fake.first_name(),
              'familyName': fake.last_name()
          }]
      )
      emailAddresses = factory.LazyAttribute(
          lambda _: [{'value': fake.email()}]
      )
  ```

#### Performance Benchmarking Tests
- [ ] Install pytest-benchmark
  ```bash
  pip install pytest-benchmark
  ```

- [ ] Create `tests/unit/test_performance.py`
  ```python
  import pytest
  
  def test_token_encryption_performance(benchmark):
      """Benchmark token encryption/decryption."""
      from integrations.security.encryption_manager import EncryptionManager
      
      encryptor = EncryptionManager()
      token = 'test_token_value_1234567890'
      
      def encrypt_decrypt():
          encrypted = encryptor.encrypt_token(token)
          decrypted = encryptor.decrypt_token(encrypted)
          assert decrypted == token
      
      result = benchmark(encrypt_decrypt)
      assert result is None  # Just timing
  
  def test_oauth_url_generation_performance(benchmark):
      """Benchmark OAuth URL generation."""
      from integrations.oauth.google_oauth import GoogleOAuthHandler
      
      config = {
          'client_id': 'test',
          'client_secret': 'test',
          'redirect_uri': 'http://localhost',
          'scopes': ['calendar', 'gmail']
      }
      handler = GoogleOAuthHandler(config)
      
      url = benchmark(handler.get_authorization_url)
      assert 'accounts.google.com' in url
  
  # Add more performance tests
  ```

#### Integration Test Scaffolding
- [ ] Create comprehensive conftest.py
  ```python
  import pytest
  from tests.mocks.mock_oauth_server import MockOAuthServer
  
  @pytest.fixture(scope='session')
  def mock_oauth_server():
      """Session-scoped mock OAuth server."""
      return MockOAuthServer()
  
  @pytest.fixture
  def temp_database(tmp_path):
      """Temporary database for testing."""
      db_path = tmp_path / "test.db"
      # Set up test database
      yield db_path
      # Teardown
  
  @pytest.fixture
  def clean_environment(monkeypatch):
      """Clean environment for testing."""
      monkeypatch.delenv('GOOGLE_CLIENT_ID', raising=False)
      monkeypatch.delenv('MICROSOFT_CLIENT_ID', raising=False)
      yield
  ```

#### Test Result Reporting
- [ ] Configure HTML test reports
  ```bash
  pytest --html=report.html --self-contained-html
  ```

- [ ] Set up test result tracking
  - [ ] Track test count
  - [ ] Track coverage percentage
  - [ ] Track test execution time
  - [ ] Track flaky tests

---

## 🧪 Testing Requirements

### Target Metrics
- [ ] **50+ automated tests** passing
- [ ] **90%+ code coverage** on new code
- [ ] **< 2 minutes** total test suite runtime
- [ ] **Zero flaky tests**

### Test Breakdown
- [ ] Unit tests: 30+
  - [ ] OAuth tests: 12
  - [ ] API client tests: 12
  - [ ] Utility tests: 6
- [ ] Integration tests: 15+
  - [ ] OAuth flow tests: 6
  - [ ] API integration tests: 6
  - [ ] End-to-end tests: 3
- [ ] Performance tests: 5+

---

## 📦 Dependencies

```
# Add to requirements.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-asyncio>=0.21.0
pytest-xdist>=3.3.0
pytest-timeout>=2.1.0
pytest-html>=3.2.0
pytest-benchmark>=4.0.0
coverage>=7.3.0
faker>=19.0.0
responses>=0.23.0
factory-boy>=3.3.0
```

---

## 📊 Success Metrics

### End of Day 1 Deliverables
- [ ] pytest framework fully configured
- [ ] 50+ automated tests passing
- [ ] Code coverage > 90%
- [ ] Mock OAuth server functional
- [ ] Mock API servers functional
- [ ] CI/CD pipeline running on GitHub Actions
- [ ] Test data generators created
- [ ] Performance benchmarks established
- [ ] HTML test reports generated
- [ ] Coverage reports generated
- [ ] Documentation complete

---

## 🚀 Handoff to Other Teams

### For All Teams
- Test framework ready for all code
- Mock servers for testing without real APIs
- Test fixtures and factories to use
- CI/CD pipeline validates all PRs

### For Team 5 (Security)
- Security test patterns
- Encryption test examples
- Validation test structure

---

## 📝 Notes

- Write tests as code is developed (TDD)
- Keep tests fast (use mocks)
- One assertion per test (when reasonable)
- Test both success and failure paths
- Use descriptive test names
- Clean up test resources
- Don't test implementation details
- Focus on behavior and contracts
- Keep test data minimal
- Use factories for complex objects

---

**Team Contact**: QA Engineer  
**Status Updates**: Every 2 hours to Orchestration  
**Blockers**: Report immediately  
**Dependency**: Needs code from Teams 1, 2, 3, 5 to test

---

## 🎯 Ready to Execute!

Quality is built in, not bolted on!

**LET'S TEST! ✅**
