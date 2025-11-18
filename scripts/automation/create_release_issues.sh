#!/bin/bash

# Script to create 15 GitHub issues for Public Release Readiness
# Based on issue #38: https://github.com/dwilli15/OsMEN/issues/38

set -e

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed."
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI."
    echo "Run: gh auth login"
    exit 1
fi

# Repository (adjust if needed)
REPO="dwilli15/OsMEN"

echo "Creating 15 GitHub issues for public release readiness..."
echo "Repository: $REPO"
echo ""

# Issue 1: Missing Security Policy
echo "Creating Issue 1: Add Security Policy and Vulnerability Reporting Guidelines"
gh issue create \
    --repo "$REPO" \
    --title "Add Security Policy and Vulnerability Reporting Guidelines" \
    --label "security,documentation,critical" \
    --body "## Description
Repository lacks a SECURITY.md file that explains how users should report security vulnerabilities. This is essential for responsible disclosure and maintaining trust with the community.

## Required Actions
- [ ] Create \`.github/SECURITY.md\` with vulnerability reporting process
- [ ] Include supported versions table
- [ ] Provide security contact email or secure reporting method (e.g., security@domain.com or GitHub Security Advisories)
- [ ] Add timeline expectations for security responses (e.g., 48 hours acknowledgment, 7-14 days for patches)

## Estimated Effort
2-3 hours

## Priority
CRITICAL - Required for public release

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 2: Missing Code of Conduct
echo "Creating Issue 2: Add Code of Conduct"
gh issue create \
    --repo "$REPO" \
    --title "Add Code of Conduct" \
    --label "community,documentation,critical" \
    --body "## Description
No CODE_OF_CONDUCT.md file exists to set community standards and expectations for behavior. This is required for a healthy open-source community and is expected by GitHub and most contributors.

## Required Actions
- [ ] Create CODE_OF_CONDUCT.md based on Contributor Covenant 2.1
- [ ] Define enforcement responsibilities and who to contact
- [ ] Provide contact information for reporting issues (e.g., conduct@domain.com)
- [ ] Add attribution to standard if using template

## Estimated Effort
1-2 hours

## Priority
CRITICAL - Required for public release

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 3: Hardcoded Credentials in Examples
echo "Creating Issue 3: Fix Hardcoded Credentials and Secrets in .env.example Files"
gh issue create \
    --repo "$REPO" \
    --title "Fix Hardcoded Credentials and Secrets in .env.example Files" \
    --label "security,critical" \
    --body "## Description
.env.example contains placeholder values that could be mistaken for real credentials or provide templates that users might use directly in production without changing.

## Current Issues
\`\`\`
# In .env.example - these look too real:
N8N_BASIC_AUTH_PASSWORD=changeme  # Should be: N8N_BASIC_AUTH_PASSWORD=your-secure-password-here
OPENAI_API_KEY=your_openai_api_key_here  # Already correct format
\`\`\`

## Required Actions
- [ ] Review all .env.example files for potentially confusing placeholders
- [ ] Add prominent warnings about not using example values in production
- [ ] Use obviously fake placeholders (e.g., \"your-api-key-here\", not \"sk-example123\")
- [ ] Add validation in setup scripts to detect and warn if example values are detected

## Estimated Effort
2-3 hours

## Priority
CRITICAL - Security risk

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 4: Missing Compatibility Documentation
echo "Creating Issue 4: Add Comprehensive Installation Testing and Compatibility Documentation"
gh issue create \
    --repo "$REPO" \
    --title "Add Comprehensive Installation Testing and Compatibility Documentation" \
    --label "documentation,high-priority" \
    --body "## Description
While 1stsetup.md exists, there's no documented matrix of tested platforms, versions, or known compatibility issues. Users need to know what's officially supported.

## Required Actions
- [ ] Create \`docs/COMPATIBILITY.md\` listing:
  - Tested operating systems (Windows 10/11, macOS 12+, Ubuntu 20.04+, etc.)
  - Required Docker versions (e.g., Docker 20.10+, Docker Compose 1.29+)
  - Python version compatibility matrix (3.12+)
  - Known issues with specific configurations
- [ ] Add troubleshooting for common installation failures
- [ ] Document resource requirements (minimum: 16GB RAM, recommended: 32GB RAM, etc.)

## Estimated Effort
4-6 hours

## Priority
HIGH - Users need to know if it will work on their system

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 5: Missing API Documentation
echo "Creating Issue 5: Add Comprehensive API Documentation for Gateway and MCP Server"
gh issue create \
    --repo "$REPO" \
    --title "Add Comprehensive API Documentation for Gateway and MCP Server" \
    --label "documentation,api,high-priority" \
    --body "## Description
gateway.py and mcp_server.py lack comprehensive API documentation for external integrations. Developers need to know how to integrate with these services.

## Required Actions
- [ ] Add OpenAPI/Swagger documentation for gateway endpoints
- [ ] Document MCP server protocol and endpoints
- [ ] Create API usage examples in docs/API_GUIDE.md
- [ ] Add rate limiting and authentication documentation
- [ ] Include error response codes and meanings

## Estimated Effort
6-8 hours

## Priority
HIGH - Critical for integrations

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 6: Missing License Compliance
echo "Creating Issue 6: Add Dependency License Compliance Check"
gh issue create \
    --repo "$REPO" \
    --title "Add Dependency License Compliance Check" \
    --label "legal,dependencies,high-priority" \
    --body "## Description
No automated check to ensure all dependencies have compatible licenses for public release. This could expose the project to legal issues.

## Required Actions
- [ ] Add license checker to CI/CD (e.g., \`pip-licenses\` or \`license-checker\`)
- [ ] Create \`THIRD_PARTY_LICENSES.md\` listing all dependencies and their licenses
- [ ] Verify no GPL/AGPL dependencies if incompatible with project license (Apache 2.0)
- [ ] Document license compatibility policy in CONTRIBUTING.md

## Estimated Effort
3-4 hours

## Priority
HIGH - Legal requirement for public release

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 7: Missing Backup/Recovery Documentation
echo "Creating Issue 7: Add Comprehensive Backup and Recovery Documentation"
gh issue create \
    --repo "$REPO" \
    --title "Add Comprehensive Backup and Recovery Documentation" \
    --label "documentation,operations,high-priority" \
    --body "## Description
While Makefile has a backup command, there's no documented backup/recovery procedure for production use. Users need to know how to protect their data.

## Required Actions
- [ ] Create \`docs/BACKUP_RECOVERY.md\` with:
  - What to backup (Postgres DB, Qdrant vectors, config files, n8n workflows, Langflow flows)
  - Backup frequency recommendations (daily for DB, hourly for configs)
  - Restoration procedures with step-by-step instructions
  - Disaster recovery planning
  - Testing backup validity
- [ ] Add automated backup validation scripts

## Estimated Effort
4-5 hours

## Priority
HIGH - Critical for production use

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 8: Missing Performance Benchmarks
echo "Creating Issue 8: Add Performance Benchmarks and Scaling Guidelines"
gh issue create \
    --repo "$REPO" \
    --title "Add Performance Benchmarks and Scaling Guidelines" \
    --label "documentation,performance,medium-priority" \
    --body "## Description
No documented performance characteristics, expected resource usage, or scaling guidelines for production deployments.

## Required Actions
- [ ] Create \`docs/PERFORMANCE.md\` documenting:
  - Expected resource usage per agent (CPU, RAM, disk)
  - Concurrent user limits
  - Response time benchmarks
  - Scaling strategies (horizontal/vertical)
  - Performance tuning guide
- [ ] Add performance testing scripts
- [ ] Document performance monitoring setup (Prometheus, Grafana)

## Estimated Effort
6-8 hours

## Priority
MEDIUM - Important for production planning

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 9: Missing Telemetry Disclosure
echo "Creating Issue 9: Add Telemetry and Analytics Disclosure Documentation"
gh issue create \
    --repo "$REPO" \
    --title "Add Telemetry and Analytics Disclosure Documentation" \
    --label "privacy,documentation,medium-priority" \
    --body "## Description
No clear documentation about what telemetry/analytics (if any) the system collects and how to disable it. This is important for user privacy and GDPR compliance.

## Required Actions
- [ ] Create \`docs/TELEMETRY.md\` documenting:
  - What data is collected (or explicit \"no telemetry\" statement)
  - Where data is sent (if applicable)
  - How to disable telemetry completely
  - Data retention policies
- [ ] Add opt-out mechanisms in configuration
- [ ] Ensure GDPR/CCPA compliance if applicable

## Estimated Effort
2-3 hours

## Priority
MEDIUM - Privacy compliance

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 10: Missing Accessibility Guidelines
echo "Creating Issue 10: Add Accessibility Guidelines and WCAG Compliance Documentation"
gh issue create \
    --repo "$REPO" \
    --title "Add Accessibility Guidelines and WCAG Compliance Documentation" \
    --label "accessibility,documentation,medium-priority" \
    --body "## Description
Web dashboard lacks documented accessibility features and WCAG compliance information.

## Required Actions
- [ ] Create \`docs/ACCESSIBILITY.md\` documenting:
  - WCAG compliance level (A, AA, or AAA)
  - Known accessibility issues
  - Keyboard navigation support
  - Screen reader compatibility
  - Color contrast compliance
- [ ] Add accessibility testing to CI (e.g., axe-core)
- [ ] Fix critical accessibility issues in web dashboard

## Estimated Effort
8-10 hours

## Priority
MEDIUM - Important for inclusive access

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 11: Missing Upgrade Documentation
echo "Creating Issue 11: Add Upgrade and Migration Path Documentation"
gh issue create \
    --repo "$REPO" \
    --title "Add Upgrade and Migration Path Documentation" \
    --label "documentation,operations,medium-priority" \
    --body "## Description
Missing documentation for upgrading between versions and migrating data. Users need clear upgrade paths.

## Required Actions
- [ ] Create \`docs/UPGRADING.md\` with:
  - Version upgrade procedures
  - Breaking changes between versions (maintain in CHANGELOG.md)
  - Data migration scripts
  - Rollback procedures
  - Version compatibility matrix
- [ ] Add migration testing to CI

## Estimated Effort
4-6 hours

## Priority
MEDIUM - Important for long-term maintenance

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 12: Missing Monitoring Documentation
echo "Creating Issue 12: Add Comprehensive Monitoring and Observability Documentation"
gh issue create \
    --repo "$REPO" \
    --title "Add Comprehensive Monitoring and Observability Documentation" \
    --label "documentation,operations,medium-priority" \
    --body "## Description
No comprehensive guide for production monitoring, alerting, and observability.

## Required Actions
- [ ] Create \`docs/MONITORING.md\` with:
  - Recommended monitoring tools (Prometheus, Grafana, etc.)
  - Key metrics to track (agent response times, error rates, resource usage)
  - Alert configurations
  - Log aggregation setup (ELK stack, Loki, etc.)
  - Distributed tracing setup (Jaeger, Zipkin)
  - Dashboard templates (Grafana examples)
- [ ] Provide example monitoring configurations

## Estimated Effort
6-8 hours

## Priority
MEDIUM - Important for production operations

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 13: Missing Release Process
echo "Creating Issue 13: Add Release Process and Versioning Documentation"
gh issue create \
    --repo "$REPO" \
    --title "Add Release Process and Versioning Documentation" \
    --label "documentation,process,medium-priority" \
    --body "## Description
No documented release process, versioning strategy, or changelog generation process.

## Required Actions
- [ ] Create \`docs/RELEASE_PROCESS.md\` documenting:
  - Versioning strategy (recommend Semantic Versioning)
  - Release branch strategy (e.g., gitflow)
  - Changelog generation process
  - Release testing checklist
  - Publication process (Docker Hub, PyPI, GitHub Releases)
- [ ] Automate release process where possible (GitHub Actions)

## Estimated Effort
4-6 hours

## Priority
MEDIUM - Important for maintainability

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 14: Missing i18n Documentation
echo "Creating Issue 14: Add Internationalization (i18n) Support Documentation"
gh issue create \
    --repo "$REPO" \
    --title "Add Internationalization (i18n) Support Documentation" \
    --label "documentation,enhancement,low-priority" \
    --body "## Description
No documentation on how to add translations or localization support.

## Required Actions
- [ ] Create \`docs/INTERNATIONALIZATION.md\` if i18n is supported
- [ ] Document translation process
- [ ] List supported languages
- [ ] OR clearly state \"English only\" in README if not supporting i18n

## Estimated Effort
2-3 hours (or 20+ hours if implementing i18n)

## Priority
LOW - Can be added post-release

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

# Issue 15: Missing Public Roadmap
echo "Creating Issue 15: Add Public Roadmap and Feature Request Process"
gh issue create \
    --repo "$REPO" \
    --title "Add Public Roadmap and Feature Request Process" \
    --label "community,documentation,low-priority" \
    --body "## Description
Missing public roadmap and unclear process for feature requests.

## Required Actions
- [ ] Create \`ROADMAP.md\` with planned features and timeline
- [ ] Enable GitHub Discussions for feature requests
- [ ] Document feature request process in CONTRIBUTING.md
- [ ] Add feature request issue template

## Estimated Effort
3-4 hours

## Priority
LOW - Can be added post-release

## Reference
See \`docs/PUBLIC_RELEASE_CHECKLIST.md\` for complete details."

echo ""
echo "✅ Successfully created 15 GitHub issues for public release readiness!"
echo ""
echo "View all issues at: https://github.com/$REPO/issues"
echo ""
echo "Next steps:"
echo "1. Review the created issues"
echo "2. Assign them to team members or milestones"
echo "3. Start working through them based on priority (Critical → High → Medium → Low)"
