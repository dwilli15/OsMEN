# Day 1 Quick Start Guide

**Welcome to Day 1 of the 6-Day Blitz!**

This guide will help you get started quickly.

---

## 🚀 Getting Started

### 1. Choose Your Team

Pick your team based on your expertise:

- **Backend/OAuth Expert?** → [Team 1 (Google OAuth)](team1_google_oauth/TODO.md) or [Team 2 (Microsoft OAuth)](team2_microsoft_oauth/TODO.md)
- **Automation/DevOps?** → [Team 3 (API Clients)](team3_api_clients/TODO.md)
- **QA/Testing?** → [Team 4 (Testing)](team4_testing/TODO.md)
- **Security Expert?** → [Team 5 (Token Security)](team5_token_security/TODO.md)
- **Project Manager?** → [Orchestration Team](orchestration/TODO.md)

### 2. Read Your Team's TODO

Each TODO list is organized by hour with detailed tasks:

```
Hour 1-2: Foundation setup
Hour 3-4: Core implementation
Hour 5-6: Advanced features
Hour 7-8: Integration & testing
```

### 3. Set Up Your Environment

```bash
# Navigate to the OsMEN repository
cd /path/to/OsMEN

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Generate encryption key (for Team 5 or all teams)
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
# Add the output to .env as OAUTH_ENCRYPTION_KEY
```

### 4. Run Existing Tests

Ensure everything works before starting:

```bash
python3 test_agents.py
# All tests should pass ✅
```

---

## 📋 Team Coordination

### Communication Channels

Set up these channels (Slack/Discord/Teams):
- `#day1-team1-google-oauth`
- `#day1-team2-microsoft-oauth`
- `#day1-team3-api-clients`
- `#day1-team4-testing`
- `#day1-team5-token-security`
- `#day1-orchestration` (all teams)

### Status Update Format

Post every 2 hours:

```
Team [X] - Hour [Y] Update
✅ Done: [what you completed]
🏗️ In Progress: [what you're working on]
🚫 Blocked: [any blockers]
⏭️ Next: [what's coming next]
```

### Blocker Escalation

If you're blocked:
1. Try to resolve it yourself (15 minutes)
2. Ask your team lead
3. Escalate to #day1-orchestration
4. Get help from other teams if needed

---

## 🎯 Day 1 Goals

By end of day (8 hours), we should have:

✅ **OAuth Working**
- Google OAuth 2.0 flows complete
- Microsoft OAuth 2.0 flows complete
- Token storage with encryption
- Automatic token refresh

✅ **API Clients Generated**
- Google Calendar API client
- Gmail API client
- Google Contacts API client
- Retry logic and rate limiting

✅ **Testing Infrastructure**
- 50+ automated tests passing
- 90%+ code coverage
- Mock servers for testing
- CI/CD pipeline running

✅ **Security Hardened**
- All tokens encrypted at rest
- Secure credential management
- Security logging in place

---

## ⏱️ Hourly Schedule

| Hour | Checkpoint | Focus |
|------|------------|-------|
| 0 | Kickoff | Team assignments, setup |
| 2 | Stand-up #1 | Foundation complete? |
| 4 | Stand-up #2 | Core features done? |
| 6 | Stand-up #3 | Integration working? |
| 8 | Final Demo | All deliverables complete? |

---

## 📚 Key Resources

### For Team 1 (Google OAuth)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google API Console](https://console.cloud.google.com/)

### For Team 2 (Microsoft OAuth)
- [Microsoft Identity Platform](https://learn.microsoft.com/en-us/azure/active-directory/develop/)
- [Azure Portal](https://portal.azure.com/)

### For Team 3 (API Clients)
- [openapi-generator Documentation](https://openapi-generator.tech/)
- [Google API Discovery Service](https://developers.google.com/discovery)

### For Team 4 (Testing)
- [pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

### For Team 5 (Security)
- [cryptography Library](https://cryptography.io/)
- [OWASP OAuth Security](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)

---

## 🔧 Useful Commands

### Run Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/unit/oauth/test_google_oauth.py

# With coverage
pytest --cov=integrations --cov-report=html

# Only OAuth tests
pytest -m oauth
```

### Generate API Client
```bash
./scripts/automation/generate_api_client.sh \
  specs/google_calendar_v3.json \
  integrations/google/calendar_client \
  osmen_google_calendar
```

### Generate Encryption Key
```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

### Format Code
```bash
black integrations/ agents/
isort integrations/ agents/
```

### Lint Code
```bash
flake8 integrations/ agents/
pylint integrations/ agents/
```

---

## 🚨 Common Issues

### Issue: openapi-generator not found
**Solution**: Install via npm, homebrew, or use Docker
```bash
npm install -g @openapitools/openapi-generator-cli
```

### Issue: Import errors
**Solution**: Install package in development mode
```bash
cd integrations/google/calendar_client
pip install -e .
```

### Issue: Tests failing
**Solution**: Check you have all dependencies
```bash
pip install -r requirements.txt
```

### Issue: Encryption key error
**Solution**: Generate and add to .env
```bash
python scripts/generate_encryption_key.py
# Add output to .env file
```

---

## ✅ Pre-Flight Checklist

Before starting your team's work:

- [ ] Read your team's TODO list completely
- [ ] Understand your hour-by-hour tasks
- [ ] Know your dependencies on other teams
- [ ] Have development environment set up
- [ ] Can run existing tests successfully
- [ ] Have communication channels set up
- [ ] Know who your team lead is
- [ ] Understand the overall Day 1 goals

---

## 🎯 Success Metrics

Track your progress:

- [ ] **Tests**: 50+ passing (team contribution: ~10 each)
- [ ] **Coverage**: 90%+ on your code
- [ ] **Documentation**: Updated as you code
- [ ] **Integration**: Your code works with other teams
- [ ] **Quality**: No critical bugs, clean code

---

## 📞 Need Help?

1. **Check your TODO** - Most answers are there
2. **Ask your team** - Use your team channel
3. **Check orchestration** - Post in #day1-orchestration
4. **Escalate quickly** - Don't stay blocked

---

## 🏁 Let's Go!

**This is Day 1 - The Foundation**

Everything we build today sets us up for Days 2-6.

**Let's make it count! 🚀**

---

## Quick Links

- [📋 Master Overview](README.md)
- [👥 Team 1 - Google OAuth](team1_google_oauth/TODO.md)
- [👥 Team 2 - Microsoft OAuth](team2_microsoft_oauth/TODO.md)
- [👥 Team 3 - API Clients](team3_api_clients/TODO.md)
- [👥 Team 4 - Testing](team4_testing/TODO.md)
- [👥 Team 5 - Token Security](team5_token_security/TODO.md)
- [🎯 Orchestration](orchestration/TODO.md)

---

**Last Updated**: 2024-11-18
**Status**: Ready to Execute
**Let's Build! 🚀**
