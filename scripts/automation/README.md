# OsMEN Automation Scripts

This directory contains automation scripts for managing and maintaining the OsMEN system.

## Available Scripts

### create_release_issues.sh
**Purpose:** Creates 15 GitHub issues for public release readiness tracking.

**Usage:**
```bash
# Ensure you're authenticated with GitHub CLI
gh auth login

# Run the script
./scripts/automation/create_release_issues.sh
```

**What it does:**
- Creates 15 individual GitHub issues based on the PUBLIC_RELEASE_CHECKLIST.md
- Issues are categorized by priority: Critical (3), High (4), Medium (6), Low (2)
- Each issue includes:
  - Detailed description
  - Required action items as checklists
  - Estimated effort
  - Priority level
  - Appropriate labels

**Prerequisites:**
- [GitHub CLI (gh)](https://cli.github.com/) must be installed
- You must be authenticated with GitHub CLI (`gh auth login`)
- You must have write access to the repository

**Issues created:**

**Critical Priority:**
1. Add Security Policy and Vulnerability Reporting Guidelines
2. Add Code of Conduct
3. Fix Hardcoded Credentials and Secrets in .env.example Files

**High Priority:**
4. Add Comprehensive Installation Testing and Compatibility Documentation
5. Add Comprehensive API Documentation for Gateway and MCP Server
6. Add Dependency License Compliance Check
7. Add Comprehensive Backup and Recovery Documentation

**Medium Priority:**
8. Add Performance Benchmarks and Scaling Guidelines
9. Add Telemetry and Analytics Disclosure Documentation
10. Add Accessibility Guidelines and WCAG Compliance Documentation
11. Add Upgrade and Migration Path Documentation
12. Add Comprehensive Monitoring and Observability Documentation
13. Add Release Process and Versioning Documentation

**Low Priority:**
14. Add Internationalization (i18n) Support Documentation
15. Add Public Roadmap and Feature Request Process

### install_llm_tools.py
**Purpose:** Install and configure LLM tools and dependencies.

### setup_first_team.py
**Purpose:** Set up the initial agent team configuration.

### setup_wizard.py
**Purpose:** Interactive setup wizard for initial OsMEN configuration.

### test_llm_providers.py
**Purpose:** Test connectivity and functionality of configured LLM providers.

### validate_production_ready.py
**Purpose:** Validate that the system is ready for production deployment.

### validate_security.py
**Purpose:** Run security validation checks on the configuration.

**Usage:**
```bash
python3 scripts/automation/validate_security.py
```

## General Guidelines

1. **Run from repository root:** Most scripts should be run from the repository root directory
2. **Check requirements:** Ensure all dependencies are installed (`pip install -r requirements.txt`)
3. **Review output:** Always review the output of automation scripts before proceeding
4. **Backup first:** For production systems, always backup before running automation scripts

## Contributing

When adding new automation scripts:
1. Add proper error handling
2. Include usage documentation in this README
3. Add comments explaining complex logic
4. Test thoroughly before committing
5. Follow the existing script structure and naming conventions
