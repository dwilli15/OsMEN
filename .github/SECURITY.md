# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

We take the security of OsMEN seriously. If you have discovered a security vulnerability, we appreciate your help in disclosing it to us in a responsible manner.

### How to Report

Please report security vulnerabilities by emailing:

**security@osmen.dev** (or create a private security advisory using [GitHub Security Advisories](https://github.com/dwilli15/OsMEN/security/advisories/new))

### What to Include

When reporting a vulnerability, please include:

1. **Description**: Detailed description of the vulnerability
2. **Impact**: What could an attacker accomplish by exploiting this?
3. **Steps to Reproduce**: Clear step-by-step instructions
4. **Affected Components**: Which parts of OsMEN are affected?
5. **Suggested Fix**: If you have ideas on how to fix it (optional)
6. **Your Environment**: OS, Docker version, OsMEN version, etc.

### Example Report

```
Subject: [SECURITY] SQL Injection in API Gateway

Description: The /api/agents endpoint is vulnerable to SQL injection...
Impact: An attacker could read/modify database contents...
Steps to Reproduce:
1. Send POST request to /api/agents
2. Include payload: {"name": "test'; DROP TABLE users--"}
3. Observe database modification

Affected Components: gateway/gateway.py, line 234
Suggested Fix: Use parameterized queries instead of string concatenation
Environment: Ubuntu 22.04, Docker 24.0.5, OsMEN v2.0.0
```

## Response Timeline

We are committed to addressing security issues promptly:

- **Acknowledgment**: Within 48 hours of report
- **Initial Assessment**: Within 5 business days
- **Status Update**: Every 7 days until resolved
- **Patch Release**: Within 14 days for critical issues, 30 days for others

## Security Update Process

1. **Triage**: We assess the severity and impact
2. **Fix Development**: We develop and test a patch
3. **Coordinated Disclosure**: We coordinate release timing with you
4. **Release**: We release the patch and security advisory
5. **Credit**: We credit you in the advisory (if desired)

## Severity Levels

We use the following severity classifications:

### Critical
- Remote code execution
- Authentication bypass
- Data exfiltration of sensitive information
- Complete system compromise

### High
- Privilege escalation
- Unauthorized access to resources
- Exposure of credentials or API keys
- Denial of service affecting availability

### Medium
- Information disclosure of non-sensitive data
- Cross-site scripting (XSS)
- Cross-site request forgery (CSRF)
- Insecure defaults

### Low
- Security best practice violations
- Missing security headers
- Weak cryptographic algorithms (with mitigations)

## Security Best Practices for Users

### Deployment Security

1. **Change Default Credentials**: Always change default passwords in `.env`
   ```bash
   # DO NOT use these defaults in production:
   N8N_BASIC_AUTH_PASSWORD=changeme  # CHANGE THIS!
   POSTGRES_PASSWORD=postgres        # CHANGE THIS!
   ```

2. **API Key Security**:
   - Never commit `.env` files to git
   - Rotate API keys regularly
   - Use different keys for dev/staging/production

3. **Network Security**:
   - Use firewall rules to restrict access
   - Enable HTTPS in production (`ENFORCE_HTTPS=true`)
   - Restrict database access to localhost or VPN

4. **Update Regularly**:
   ```bash
   # Check for updates
   git fetch origin
   git log --oneline HEAD..origin/main
   
   # Read CHANGELOG.md for breaking changes
   cat CHANGELOG.md
   ```

5. **Run Security Validation**:
   ```bash
   python3 scripts/automation/validate_security.py
   ```

### Container Security

1. **Docker Security**:
   - Don't run containers as root
   - Use Docker secrets for sensitive data
   - Keep Docker updated
   - Scan images: `docker scan osmen-web`

2. **Volume Permissions**:
   - Ensure proper permissions on mounted volumes
   - Don't mount sensitive host directories

### Monitoring

1. **Enable Logging**: Set appropriate log levels in `.env`
2. **Monitor Logs**: Review logs for suspicious activity
   ```bash
   make logs | grep -i "error\|unauthorized\|failed"
   ```

3. **Health Checks**: Run operational checks regularly
   ```bash
   python3 check_operational.py
   ```

## Known Security Considerations

### Local LLM Privacy

OsMEN supports local LLM options (Ollama, LM Studio) for privacy-conscious users:
- Local models keep all data on your infrastructure
- No data sent to external APIs
- Trade-off: May have lower performance than cloud models

### Tool Integrations

Some integrations require cloud APIs:
- **Zoom**: Requires Zoom account and API credentials
- **Email**: Gmail/Outlook OAuth requires internet access
- **Content Creation**: Audiblez, Vibevoice are cloud services

Review the [TELEMETRY.md](../docs/TELEMETRY.md) for complete data flow documentation.

## Security Scanning

We use the following security tools:

- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability scanner
- **CodeQL**: Static analysis for code vulnerabilities
- **Docker Scan**: Container image scanning

Run scans locally:
```bash
# Install tools
pip install bandit safety

# Run scans
bandit -r agents/ gateway/ web/
safety check -r requirements.txt
```

## Responsible Disclosure

We ask that you:

1. **Give us reasonable time** to fix the issue before public disclosure
2. **Avoid degrading** user experience or data integrity
3. **Don't access** data that doesn't belong to you
4. **Don't perform DoS attacks** or intensive automated scanning

## Public Disclosure

After we've patched a vulnerability:

1. We publish a **Security Advisory** on GitHub
2. We release a **patch version** with the fix
3. We update **CHANGELOG.md** with security notes
4. We credit the reporter (if authorized)

## Hall of Fame

We appreciate security researchers who help us:

<!-- Security researchers who have responsibly disclosed vulnerabilities will be listed here -->

*No vulnerabilities have been reported yet.*

## Contact

- **Security Issues**: security@osmen.dev or [GitHub Security Advisories](https://github.com/dwilli15/OsMEN/security/advisories/new)
- **General Questions**: Open a [GitHub Discussion](https://github.com/dwilli15/OsMEN/discussions)
- **Project Maintainer**: [@dwilli15](https://github.com/dwilli15)

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

---

**Last Updated**: 2024-11-18  
**Version**: 1.0
