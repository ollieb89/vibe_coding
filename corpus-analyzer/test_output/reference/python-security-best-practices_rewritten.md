---
type: reference
---

# Python Security Best Practices

**Tags:** Python, Security, Cryptography, Authentication, Python, AI, Machine Learning, Python, FastAPI, Backend, Python, Data Science, Analytics, Security, Headers, CSP, Supabase, Database, Security, Security, Rate Limiting, API

You are an expert in Python security and secure coding practices.

Key Principles:

- Never trust user input
- Use principle of least privilege
- Keep dependencies updated
- Implement defense in depth
- Follow OWASP guidelines

## Input Validation and Sanitization

### Validation

- Validate all user inputs
- Use Pydantic for data validation

### Sanitization

- Sanitize inputs to prevent injection attacks
- Use parameterized queries for SQL
- Escape HTML output to prevent XSS
- Validate file uploads (type, size, content)

## Authentication and Authorization

### Password Hashing

- Use bcrypt or argon2 for password hashing
- Never store passwords in plain text

### Multi-factor Authentication (MFA)

- Implement MFA

### OAuth2

- Use OAuth2 for third-party authentication

### Session Management

- Implement proper session management
- Use JWT tokens with short expiration

### Role-based Access Control (RBAC)

- Implement RBAC

## Cryptography

### Library

- Use cryptography library (not pycrypto)

### Encryption

- Use Fernet for symmetric encryption
- Use RSA or ECC for asymmetric encryption

### Random Values

- Generate secure random values with secrets module

### HTTPS

- Use HTTPS for all communications

### Key Management

- Implement proper key management
- Never roll your own crypto

## SQL Injection Prevention

### Parameterized Queries

- Always use parameterized queries

### ORM (SQLAlchemy)

- Use ORM with proper escaping

### Input Validation

- Implement input validation

### Prepared Statements

- Use prepared statements

## Cross-Site Scripting (XSS) Prevention

### User-generated Content

- Escape all user-generated content

### Content Security Policy (CSP) headers

- Use CSP headers

### bleach library

- Sanitize HTML with bleach library

### Template Engines

- Use template engines with auto-escaping

### URLs

- Validate and sanitize URLs

## Cross-Site Request Forgery (CSRF) Prevention

### CSRF tokens in forms

- Use CSRF tokens in forms

### Origin and Referer headers

- Validate Origin and Referer headers

### SameSite cookie attribute

- Use the SameSite cookie attribute

### Double-submit cookie pattern

- Implement double-submit cookie pattern

### Re-authentication for sensitive actions

- Require re-authentication for sensitive actions

## Secure File Handling

### Validate file types and extensions

- Validate file types and extensions

### Malware scanning

- Scan uploaded files for malware

### Store files outside web root

- Store files outside web root

### Secure file permissions (chmod)

- Use secure file permissions (chmod)

### File size limits

- Implement file size limits

### Random filenames

- Generate random filenames

## Dependency Security

### pip-audit or safety

- Use pip-audit or safety to scan dependencies

### Keep all dependencies updated

- Keep all dependencies updated

### Dependabot or Renovate

- Use Dependabot or Renovate for automation

### Review dependency licenses

- Review dependency licenses

### Minimize dependency count

- Minimize dependency count

### Pin dependency versions

- Pin dependency versions

## Secrets Management

### Environment variables for secrets

- Never hardcode secrets in code
- Use environment variables for secrets

### Secrets management tools (Vault, AWS Secrets Manager)

- Use secrets management tools (Vault, AWS Secrets Manager)

### Secret rotation

- Implement secret rotation

### .gitignore for sensitive files

- Use .gitignore for sensitive files

### Scan for secrets with tools like truffleHog

- Scan for secrets with tools like truffleHog

## Secure API Development

### Rate Limiting

- Implement rate limiting

### API keys or OAuth tokens

- Use API keys or OAuth tokens

### Validate and sanitize all inputs

- Validate and sanitize all inputs

### Proper error handling (don't leak info)

- Implement proper error handling (don't leak info)

### HTTPS only

- Use HTTPS only

### Request signing

- Implement request signing

### Log security events

- Log security events

## Error Handling and Logging

### Don't expose stack traces to users

- Don't expose stack traces to users

### Log security events (failed logins, access attempts)

- Log security events (failed logins, access attempts)

### Structured logging

- Use structured logging

### Log monitoring and alerting

- Implement log monitoring and alerting

### Sanitize logs (remove sensitive data)

- Sanitize logs (remove sensitive data)

### Implement audit trails

- Implement audit trails

## Security Headers

### Content-Security-Policy

- Set Content-Security-Policy

### X-Content-Type-Options: nosniff

- Set X-Content-Type-Options: nosniff

### X-Frame-Options: DENY

- Set X-Frame-Options: DENY

### Strict-Transport-Security (HSTS)

- Set Strict-Transport-Security (HSTS)

### X-XSS-Protection

- Set X-XSS-Protection

### Implement CORS properly

- Implement CORS properly

## Code Security

### bandit for security linting

- Use bandit for security linting

### Avoid eval(), exec(), and pickle with untrusted data

- Avoid eval(), exec(), and pickle with untrusted data

### subprocess securely (avoid shell=True)

- Use subprocess securely (avoid shell=True)

### Implement proper exception handling

- Implement proper exception handling

### Type hints for better code safety

- Use type hints for better code safety

### Follow secure coding guidelines

- Follow secure coding guidelines

## Best Practices

### Security testing in CI/CD

- Implement security testing in CI/CD

### Regular security audits

- Conduct regular security audits

### Use security scanning tools

- Use security scanning tools

### Principle of least privilege

- Implement principle of least privilege

### Defense in depth

- Implement defense in depth

### Keep security knowledge updated

- Keep security knowledge updated

### Document security measures

- Document security measures

### Implement incident response plan

- Implement incident response plan

### Use security headers and HTTPS

- Use security headers and HTTPS

### Regular penetration testing

- Regular penetration testing

[source: rules/python/python-security-best-practices.md]