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

### validate_env.py
**Purpose:** Validate .env file for placeholder and insecure values.

**Usage:**
```bash
python3 scripts/automation/validate_env.py
```

**What it checks:**
- Detects placeholder patterns (your-*-here, changeme, example, etc.)
- Identifies insecure defaults (admin, password, postgres)
- Validates critical keys (PASSWORD, SECRET, API_KEY, TOKEN)
- Returns exit code 1 for critical issues (suitable for CI/CD)

### check_licenses.py
**Purpose:** Check Python package licenses for Apache 2.0 compatibility.

**Usage:**
```bash
python3 scripts/automation/check_licenses.py
```

**What it does:**
- Scans all installed Python packages
- Identifies compatible licenses (MIT, BSD, Apache 2.0, etc.)
- Flags incompatible licenses (GPL, AGPL)
- Marks licenses requiring manual review (LGPL, Fair Code)
- Generates compliance reports

**Prerequisites:**
- Install pip-licenses for better detection: `pip install pip-licenses`

### validate_backup.py
**Purpose:** Validate backup file integrity and completeness.

**Usage:**
```bash
python3 scripts/automation/validate_backup.py <backup-file>
```

**Example:**
```bash
python3 scripts/automation/validate_backup.py backups/osmen_backup_20241118_120000.tar.gz
```

**What it checks:**
- File integrity (valid tar.gz format)
- Required components (postgres, config)
- Recommended components (qdrant, n8n, langflow)
- Manifest.json validity
- Calculates and displays SHA256 checksum

### test_performance.py
**Purpose:** Run performance tests on OsMEN agents.

**Usage:**
```bash
python3 scripts/automation/test_performance.py
```

**What it tests:**
- Agent response times (min, max, mean, median)
- Success rates
- Performance statistics (standard deviation)
- Provides optimization recommendations

### analyze_repo.py
**Purpose:** Deep analysis to identify gaps between documentation and implementation.

**Usage:**
```bash
python3 scripts/automation/analyze_repo.py
```

**What it analyzes:**
- Documented scripts vs. actual files
- Documented API endpoints vs. implementations
- Configuration options coverage
- Documented features vs. actual code
- Makefile targets documentation
- Docker services documentation

**Output:**
- Categorized gaps (Critical, High, Medium, Low priority)
- Actionable recommendations
- Prioritized fix list

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
