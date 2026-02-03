# Security Policy

## Our Commitment

Beacon is a mental health AI triage system for minors. Security is not just important—it's life-critical. We treat all security concerns with the highest priority.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**DO NOT** open a public GitHub issue for security vulnerabilities.

### How to Report

1. **Email**: security@beacon-project.org (or your designated security contact)
2. **Subject Line**: `[SECURITY] Brief description`
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact (especially on student safety/privacy)
   - Your contact information

### What to Expect

- **Acknowledgment**: Within 24 hours
- **Initial Assessment**: Within 72 hours
- **Regular Updates**: Every 7 days until resolved
- **Resolution Timeline**: Critical issues within 7 days, high priority within 30 days

### Severity Levels

#### CRITICAL (P0) - Immediate Response
- Student PII exposure
- Crisis detection bypass
- Unauthorized access to student data
- Data breach or exfiltration

#### HIGH (P1) - 7 Day Response
- Authentication bypass
- Privilege escalation
- SQL injection or XSS vulnerabilities
- Denial of service affecting crisis alerts

#### MEDIUM (P2) - 30 Day Response
- Information disclosure (non-PII)
- CSRF vulnerabilities
- Rate limiting bypass

#### LOW (P3) - 90 Day Response
- Minor configuration issues
- Non-exploitable information leaks

## Security Best Practices for Contributors

### Code Requirements

1. **Zero PII in Logs**
   ```python
   # ❌ NEVER
   logger.info(f"Student {student_id} logged in")
   
   # ✅ ALWAYS
   logger.info(f"Student {hash_pii(student_id)} logged in")
   ```

2. **Input Validation**
   - Validate all user inputs
   - Use parameterized queries (never string concatenation)
   - Sanitize outputs to prevent XSS

3. **Authentication & Authorization**
   - All endpoints require authentication
   - RBAC enforced at service layer
   - Session tokens expire after 24 hours

4. **Secrets Management**
   - Never commit secrets to git
   - Use environment variables
   - Rotate credentials quarterly

5. **Dependencies**
   - Keep dependencies updated
   - Review security advisories weekly
   - Pin versions in requirements.txt

### Testing Requirements

- 100% test coverage for safety-critical code
- Security tests for all authentication/authorization
- Penetration testing before major releases

### Compliance

All code must comply with:
- FERPA (Family Educational Rights and Privacy Act)
- COPPA (Children's Online Privacy Protection Act)
- SOC 2 Type II requirements
- HIPAA-ready architecture

## Security Features

### Data Protection

- **Encryption at Rest**: AES-256 for all databases
- **Encryption in Transit**: TLS 1.3 minimum
- **Field-Level Encryption**: For highly sensitive PII
- **Key Management**: AWS KMS

### Access Control

- **RBAC**: Role-based access control
- **Principle of Least Privilege**: Users get minimum necessary permissions
- **Audit Logging**: All data access logged immutably

### Privacy

- **PII Hashing**: All identifiers hashed before logging
- **K-Anonymity**: k≥5 for all aggregated reports
- **Data Retention**: Automated lifecycle policies
- **Right to Deletion**: Students can request data deletion

### Monitoring

- **Anomaly Detection**: Unusual access patterns flagged
- **Failed Login Tracking**: Rate limiting after 5 failures
- **Security Alerts**: Real-time notifications for suspicious activity

## Vulnerability Disclosure Policy

We follow responsible disclosure:

1. **Report received** → Acknowledge within 24 hours
2. **Vulnerability confirmed** → Work on fix
3. **Fix deployed** → Notify reporter
4. **90-day embargo** → Public disclosure (if appropriate)

### Recognition

We maintain a security hall of fame for responsible disclosure. With your permission, we'll credit you in our security acknowledgments.

## Security Incident Response

### Incident Classification

- **P0 (Critical)**: Active data breach, student safety at risk
- **P1 (High)**: Potential breach, vulnerability being exploited
- **P2 (Medium)**: Vulnerability discovered, no active exploitation
- **P3 (Low)**: Theoretical vulnerability, low exploitability

### Response Team

- **Security Lead**: Coordinates response
- **Engineering Lead**: Implements fixes
- **Legal Counsel**: Handles compliance/notification
- **Communications**: Manages stakeholder updates

### Breach Notification

If student data is compromised:
- **Schools notified**: Within 24 hours
- **Affected families notified**: Within 72 hours
- **Regulatory bodies notified**: Per FERPA/COPPA requirements

## Security Checklist for PRs

Before merging, verify:

- [ ] No PII in log statements
- [ ] All inputs validated
- [ ] No secrets in code
- [ ] SQL queries parameterized
- [ ] XSS prevention implemented
- [ ] Authentication required
- [ ] Authorization enforced
- [ ] Error messages don't leak sensitive info
- [ ] Security tests pass
- [ ] Dependencies scanned for vulnerabilities

## Contact

- **Security Team**: security@beacon-project.org
- **Emergency Hotline**: [Your emergency contact]
- **PGP Key**: [Link to public key if applicable]

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [FERPA Compliance Guide](https://www2.ed.gov/policy/gen/guid/fpco/ferpa/index.html)
- [COPPA Compliance Guide](https://www.ftc.gov/business-guidance/resources/childrens-online-privacy-protection-rule-six-step-compliance-plan-your-business)

---

**Remember**: The stakes are high. Mental health + minors = zero tolerance for security issues.
