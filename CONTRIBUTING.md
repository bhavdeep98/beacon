# Contributing to Beacon

Thank you for your interest in contributing to Beacon, an AI-powered mental health triage system for students. This is a **safety-critical system** where bugs can have serious real-world consequences. We appreciate your help in making mental health support more accessible while maintaining the highest standards of safety, privacy, and compliance.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Safety-Critical Guidelines](#safety-critical-guidelines)
- [Documentation](#documentation)
- [Community](#community)

---

## Code of Conduct

This project adheres to a strict [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

**Key Points:**
- Professional and respectful communication
- Zero tolerance for privacy violations or safety bypasses
- Sensitivity required when discussing mental health topics
- Never share or reference actual student data

---

## Getting Started

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Git** for version control
- **Basic understanding** of mental health terminology (see [Glossary](.kiro/steering/01-glossary.md))

### Initial Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/beacon.git
   cd beacon
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL-OWNER/beacon.git
   ```

4. **Install dependencies**:
   ```bash
   ./setup.sh
   ```

5. **Run tests** to verify setup:
   ```bash
   ./run_tests.sh
   ```

6. **Read the project tenets**:
   - [Project Tenets](.kiro/steering/00-project-tenets.md) - 15 foundational principles
   - [Coding Standards](.kiro/steering/03-coding-standards.md) - Safety-critical code requirements
   - [Design Patterns](.kiro/steering/04-design-patterns.md) - Architectural patterns

---

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

#### 🐛 Bug Reports
- Use the bug report template
- Include steps to reproduce
- Specify expected vs actual behavior
- For safety-critical bugs, email security@beacon-project.org privately

#### 💡 Feature Requests
- Use the feature request template
- Explain the use case and benefit
- Consider safety and compliance implications
- Discuss in issues before implementing

#### 📝 Documentation
- Fix typos, clarify explanations
- Add examples or tutorials
- Improve API documentation
- Update outdated information

#### 🧪 Test Coverage
- Add tests for untested code paths
- Create golden test cases from real scenarios
- Improve test data quality
- Add property-based tests

#### 🔧 Code Contributions
- Bug fixes
- Performance improvements
- New detection strategies
- UI/UX enhancements

### What NOT to Contribute

❌ **Do not submit:**
- Code that bypasses safety guardrails
- Changes that log or expose PII
- Features without tests (especially safety-critical)
- Code that violates FERPA/COPPA compliance
- Clever abstractions that reduce traceability
- Changes to crisis detection without clinical review

---

## Development Workflow

### 1. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions/improvements
- `refactor/` - Code refactoring

### 2. Make Changes

Follow the [60-second litmus test](.kiro/steering/00-project-tenets.md#the-litmus-test):

Every file must answer in 60 seconds:
1. What does this file do?
2. What happens if this fails?
3. Where would I add a log statement to debug this?

**If no → Refactor immediately.**

### 3. Write Tests

```bash
# Run tests frequently during development
pytest tests/test_your_module.py -v

# Run all tests before committing
./run_tests.sh

# Check coverage (100% required for safety-critical code)
./run_tests.sh --coverage
```

### 4. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: Add semantic detection for coded language

- Implement embedding similarity for obfuscated phrases
- Add tests for leetspeak and coded crisis expressions
- Update crisis_patterns.yaml with new patterns
- Achieves 95% recall on adversarial test set

Closes #123"
```

**Commit message format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Test additions
- `refactor:` - Code refactoring
- `perf:` - Performance improvement
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

---

## Coding Standards

### Python (Backend)

**Required:**
- ✅ Type hints on all function signatures
- ✅ Docstrings for all public functions/classes
- ✅ Black formatting (line length: 100)
- ✅ Ruff + mypy linting (strict mode)
- ✅ No bare `except:` clauses

**Example:**
```python
from typing import Optional
from models import RiskAssessment

def assess_risk(
    student_id: str,
    message: str,
    history: Optional[list[str]] = None
) -> RiskAssessment:
    """
    Assess crisis risk for a student message.
    
    Args:
        student_id: Hashed student identifier
        message: Student's message content
        history: Optional conversation history
        
    Returns:
        RiskAssessment with score and evidence
        
    Raises:
        SafetyServiceError: If risk assessment fails
    """
    # Implementation
    pass
```

### TypeScript (Frontend)

**Required:**
- ✅ TypeScript strict mode
- ✅ ESLint compliance
- ✅ Prettier formatting
- ✅ React hooks best practices
- ✅ Accessibility (WCAG 2.1 AA)

### Privacy Requirements

**CRITICAL: Zero PII in logs**

```python
# ❌ NEVER DO THIS
logger.info(f"Student {student_id} logged in")

# ✅ ALWAYS DO THIS
from utils.privacy import hash_pii
logger.info(f"Student {hash_pii(student_id)} logged in")
```

### Error Handling

```python
# ❌ NEVER DO THIS
try:
    result = risky_operation()
except:
    pass

# ✅ ALWAYS DO THIS
from exceptions import SafetyServiceError

try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise SafetyServiceError(
        "Failed to analyze message",
        original_error=e,
        context={"session_id": hash_pii(session_id)}
    )
```

See [Coding Standards](.kiro/steering/03-coding-standards.md) for complete requirements.

---

## Testing Requirements

### Coverage Requirements

| Code Type | Coverage Required |
|-----------|-------------------|
| **Safety-critical** (crisis detection) | 100% |
| **Core services** | ≥95% |
| **Utilities** | ≥90% |
| **UI components** | ≥80% |

### Test Types

#### Unit Tests
```python
def test_crisis_detection_explicit_suicidal_ideation():
    """Test detection of explicit suicidal ideation."""
    message = "I want to end my life"
    result = safety_service.analyze(message)
    
    assert result.risk_level == RiskLevel.CRISIS
    assert result.confidence >= 0.90
    assert "suicidal_ideation" in result.matched_patterns
```

#### Integration Tests
```python
@pytest.mark.integration
async def test_end_to_end_crisis_flow():
    """Test complete crisis detection and notification flow."""
    response = await chat_service.send_message(
        session_id=test_session_id,
        message="I'm going to hurt myself tonight"
    )
    
    assert response.is_crisis_override is True
    assert "crisis resources" in response.message.lower()
```

#### Golden Tests
- Use curated test sets (MentalChat16K, Hard Crisis)
- Maintain custom crisis test set
- Test adversarial patterns (coded language, leetspeak)

### Running Tests

```bash
# Run all tests
./run_tests.sh

# Run specific test file
pytest tests/test_safety_service.py -v

# Run with coverage
./run_tests.sh --coverage

# Run fast tests only (skip benchmarks)
./run_tests.sh --fast

# Run specific test class
pytest tests/test_safety_service.py::TestExplicitCrisisDetection -v
```

---

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code passes all tests (`./run_tests.sh`)
- [ ] Safety-critical code has 100% test coverage
- [ ] All functions have type hints and docstrings
- [ ] No PII in log statements (use `hash_pii()`)
- [ ] No bare `except:` clauses
- [ ] Code passes 60-second litmus test
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Passes linting (Black, Ruff, mypy, ESLint)

### PR Template

Use this template for your pull request:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Safety Impact
- [ ] No safety impact
- [ ] Affects crisis detection (requires clinical review)
- [ ] Affects data privacy (requires security review)
- [ ] Affects compliance (requires legal review)

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Golden tests updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project coding standards
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] Safety-critical code has 100% coverage

## Related Issues
Closes #(issue number)

## Screenshots (if applicable)
Add screenshots for UI changes
```

### Review Process

1. **Automated Checks**: CI/CD runs tests, linting, coverage
2. **Code Review**: At least one maintainer reviews
3. **Safety Review**: Safety-critical changes require additional review
4. **Approval**: Maintainer approves and merges

**Review criteria:**
- Code quality and readability
- Test coverage and quality
- Safety and compliance adherence
- Documentation completeness
- Performance impact

### Addressing Feedback

```bash
# Make requested changes
git add .
git commit -m "Address review feedback: improve error handling"
git push origin feature/your-feature-name
```

---

## Safety-Critical Guidelines

### Crisis Detection Changes

**STOP**: Changes to crisis detection require:
1. Clinical review by mental health professional
2. Testing on golden test sets
3. Validation against MentalChat16K dataset
4. Documentation of recall/precision impact
5. Approval from project lead

### Adding Crisis Patterns

Edit `config/crisis_patterns.yaml`:

```yaml
crisis_keywords:
  new_category:
    patterns:
      - "phrase 1"
      - "phrase 2"
    confidence: 0.90
    clinical_basis: "Maps to C-SSRS item 4 (intent with plan)"
```

Then:
1. Add tests in `tests/test_safety_service.py`
2. Run full test suite
3. Document clinical rationale in PR

### Privacy Requirements

**Never log PII:**
- Student names, emails, IDs
- Full message content
- IP addresses (hash them)
- Session identifiers (hash them)

**Always:**
- Use `hash_pii()` for all identifiers
- Encrypt sensitive data at rest
- Use parameterized queries (prevent SQL injection)
- Validate all user inputs

### Compliance Checklist

- [ ] FERPA compliant (student education records)
- [ ] COPPA compliant (children under 13)
- [ ] No PII in application logs
- [ ] Audit trail for sensitive operations
- [ ] k-anonymity (k≥5) for aggregated reports
- [ ] Data retention policies followed

---

## Documentation

### What to Document

**Code Documentation:**
- Docstrings for all public functions/classes
- Inline comments for complex logic
- Type hints for all parameters/returns

**Project Documentation:**
- Update README.md for new features
- Add entries to CHANGELOG.md
- Update relevant docs/ files
- Add examples for new APIs

### Documentation Style

```python
def analyze_message(message: str, context: dict) -> RiskAssessment:
    """
    Analyze student message for crisis markers.
    
    This function runs multi-layer detection (regex, semantic, sarcasm)
    and returns a risk assessment with evidence. It's designed to be
    fast (<50ms) and deterministic for safety-critical use.
    
    Args:
        message: Student's message text (will be hashed for logging)
        context: Conversation context including history and metadata
        
    Returns:
        RiskAssessment containing:
            - risk_level: CRISIS, CAUTION, or SAFE
            - confidence: 0.0-1.0 confidence score
            - matched_patterns: List of triggered patterns
            - evidence: Human-readable explanation
            
    Raises:
        SafetyServiceError: If analysis fails
        
    Example:
        >>> result = analyze_message("I want to die", {})
        >>> result.risk_level
        RiskLevel.CRISIS
        >>> result.confidence
        0.95
    """
    pass
```

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Pull Requests**: Code review and collaboration
- **Email**: security@beacon-project.org (security issues only)

### Getting Help

**Before asking:**
1. Check existing documentation
2. Search closed issues
3. Review [Project Summary](docs/PROJECT_SUMMARY.md)
4. Read [Quick Reference](docs/QUICK_REFERENCE.md)

**When asking:**
- Provide context and what you've tried
- Include error messages and logs (no PII!)
- Specify your environment (OS, Python version, etc.)
- Be patient and respectful

### Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Significant contributions may be highlighted in:
- Blog posts
- Conference presentations
- Academic publications

---

## Development Tips

### Useful Commands

```bash
# Format code
black src/ tests/ --line-length 100

# Run linting
ruff check src/ tests/
mypy src/ --strict

# Run specific test with verbose output
pytest tests/test_safety_service.py::test_crisis_detection -vv

# Run tests with debugging
pytest tests/test_safety_service.py --pdb

# Generate coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Run benchmarks
python evaluation/benchmark_runner.py --dataset hard_crisis
```

### Debugging

```python
# Add structured logging
import structlog
logger = structlog.get_logger()

logger.info(
    "crisis_detected",
    session_id=hash_pii(session_id),
    risk_score=0.95,
    matched_patterns=["suicidal_ideation"]
)
```

### Performance Profiling

```bash
# Profile code
python -m cProfile -o profile.stats your_script.py

# View results
python -m pstats profile.stats
```

---

## License

By contributing to Beacon, you agree that your contributions will be licensed under the project's proprietary license. See [LICENSE](LICENSE) for details.

---

## Questions?

- Read the [FAQ](docs/FAQ.md) (if available)
- Check [GitHub Discussions](https://github.com/OWNER/beacon/discussions)
- Review [Project Documentation](docs/)
- Contact maintainers (see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md))

---

## Thank You!

Your contributions help make mental health support more accessible to students who need it. Every line of code you write, every bug you fix, and every test you add makes the system safer and more reliable.

**Remember**: The stakes are high. Mental health + minors = zero tolerance for bugs.

---

<div align="center">

**[⬆ Back to Top](#contributing-to-beacon)**

Made with 💙 for students who need support

</div>
