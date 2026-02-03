# Pull Request

## Description

**What does this PR do?**

Brief summary of changes.

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Security fix
- [ ] Compliance update

## Related Issues

Fixes #(issue number)
Relates to #(issue number)

## Motivation and Context

**Why is this change needed?**

What problem does it solve?

## Changes Made

**Detailed list of changes:**

- Changed X to Y
- Added Z functionality
- Removed deprecated W

## Testing

**How has this been tested?**

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] Golden test set validated (if crisis detection changes)
- [ ] Property-based tests added (if applicable)

**Test coverage:**
- Coverage before: __%
- Coverage after: __%

**Test scenarios:**
1. Scenario 1: Expected result
2. Scenario 2: Expected result

## Safety & Security Checklist

**Critical for safety-critical code:**

- [ ] No PII in log statements (used `hash_pii()`)
- [ ] All inputs validated
- [ ] No secrets in code
- [ ] SQL queries parameterized (no string concatenation)
- [ ] XSS prevention implemented
- [ ] Authentication required for new endpoints
- [ ] Authorization enforced (RBAC)
- [ ] Error messages don't leak sensitive info
- [ ] No bare `except:` clauses
- [ ] Explicit exception handling with context

## Compliance Checklist

- [ ] FERPA compliant (student data privacy)
- [ ] COPPA compliant (parental consent for <13)
- [ ] Audit logging added for sensitive operations
- [ ] Data retention policies followed
- [ ] K-anonymity maintained (k≥5) for reports

## Code Quality Checklist

- [ ] Type hints added for all functions
- [ ] Docstrings added/updated
- [ ] Code follows project tenets (see `.kiro/steering/00-project-tenets.md`)
- [ ] Passes 60-second litmus test (new engineer can understand in 60s)
- [ ] No "clever" code - explicit and traceable
- [ ] Enums used for fixed values
- [ ] Immutable data structures where appropriate

## Performance Impact

**Does this change affect performance?**

- [ ] No performance impact
- [ ] Improves performance (describe):
- [ ] May impact performance (describe):

**Benchmarks (if applicable):**
- Before: X ms
- After: Y ms

## Breaking Changes

**Does this PR introduce breaking changes?**

- [ ] No
- [ ] Yes (describe migration path):

## Deployment Notes

**Special deployment considerations:**

- [ ] Database migration required
- [ ] Configuration changes required
- [ ] Environment variables added/changed
- [ ] Dependencies added/updated
- [ ] Infrastructure changes needed
- [ ] Requires feature flag
- [ ] Requires gradual rollout (canary)

**Rollback plan:**
Describe how to rollback if issues arise.

## Documentation

- [ ] README updated
- [ ] API documentation updated
- [ ] Architecture diagrams updated
- [ ] DECISION_LOG.md updated (if architectural decision)
- [ ] Compliance documentation updated
- [ ] User-facing documentation updated

## Screenshots/Videos

If applicable, add screenshots or videos demonstrating the changes.

## Reviewer Guidance

**What should reviewers focus on?**

- Specific areas of concern:
- Questions for reviewers:

## Checklist Before Merge

- [ ] All tests pass
- [ ] Code reviewed by at least 2 people
- [ ] Security review completed (if security-related)
- [ ] Compliance review completed (if compliance-related)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts
- [ ] CI/CD pipeline passes

## Post-Merge Tasks

- [ ] Monitor error rates for 24 hours
- [ ] Verify metrics dashboards
- [ ] Update project board
- [ ] Notify stakeholders (if user-facing change)

---

## For Reviewers

### Safety-Critical Code Review

If this PR touches crisis detection, notification, or data handling:

1. **Trace the flow**: Can you follow the logic in 60 seconds?
2. **Check error handling**: Are all failures logged and handled?
3. **Verify PII protection**: No PII in logs or unencrypted storage?
4. **Test coverage**: 100% coverage for safety-critical paths?
5. **Compliance**: FERPA/COPPA requirements met?

### Code Review Checklist

- [ ] Code is clear and maintainable
- [ ] No obvious bugs or edge cases missed
- [ ] Error handling is appropriate
- [ ] Tests are comprehensive
- [ ] Documentation is clear
- [ ] Performance is acceptable
- [ ] Security best practices followed
- [ ] Aligns with project tenets

### Review Comments

**Approval criteria:**
- ✅ **LGTM**: Looks good to me, approved
- 🔄 **Request Changes**: Issues must be addressed before merge
- 💬 **Comment**: Suggestions for improvement (non-blocking)

---

**Remember**: The stakes are high. Mental health + minors = zero tolerance for bugs.
