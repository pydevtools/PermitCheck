# Contributing to PermitCheck

Thank you for your interest in contributing to PermitCheck! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [GitHub Issues](https://github.com/kirankotari/permitcheck/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Relevant logs or screenshots

### Suggesting Features

1. Check existing [GitHub Issues](https://github.com/kirankotari/permitcheck/issues) and [Discussions](https://github.com/kirankotari/permitcheck/discussions)
2. Create a new discussion with:
   - Use case description
   - Proposed solution
   - Alternative approaches considered
   - Examples

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests
5. Run the test suite
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.10 or higher
- uv package manager

### Setup

```bash
# Clone repository
git clone https://github.com/kirankotari/permitcheck.git
cd permitcheck

# Install dependencies
uv sync

# Verify installation
uv run pytest
```

## Development Workflow

### Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_core_validator.py

# With coverage
uv run pytest --cov=permitcheck --cov-report=html

# Verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x
```

### Code Formatting

```bash
# Format code
uv run black permitcheck tests

# Check formatting
uv run black --check permitcheck tests
```

### Linting

```bash
# Run pylint
uv run pylint permitcheck --disable=C0114,C0115,C0116 --max-line-length=100
```

### Type Checking

```bash
# Run mypy (if installed)
mypy permitcheck
```

## Project Structure

```
permitcheck/
├── permitcheck/           # Main package
│   ├── core/             # Core functionality
│   │   ├── cache.py      # Caching system
│   │   ├── config.py     # Configuration
│   │   ├── matcher.py    # License matching
│   │   ├── reporter.py   # Output formats
│   │   └── validator.py  # Validation logic
│   ├── plugins/          # Language plugins
│   │   ├── for_python.py # Python support
│   │   └── for_npm.py    # NPM support (WIP)
│   ├── scripts/          # CLI tools
│   │   └── permitcheck_tool.py
│   ├── license/          # License data
│   └── exceptions.py     # Custom exceptions
├── tests/                # Test suite
│   ├── test_core_*.py    # Core tests
│   ├── test_integration.py
│   └── test_spdx_parser.py
├── docs/                 # Documentation
└── .github/workflows/    # CI/CD
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for all public functions/classes

### Example

```python
from typing import Dict, Set

def validate_licenses(
    dependencies: Dict[str, Set[str]],
    allowed: Set[str]
) -> bool:
    """Validate dependencies against allowed licenses.
    
    Args:
        dependencies: Mapping of package names to license sets
        allowed: Set of allowed license identifiers
        
    Returns:
        True if all licenses are allowed, False otherwise
    """
    for pkg_name, licenses in dependencies.items():
        if not licenses.issubset(allowed):
            return False
    return True
```

### Commit Messages

Follow conventional commits:

```
feat: Add CSV output format
fix: Correct SPDX expression parsing
docs: Update installation guide
test: Add integration tests for caching
refactor: Simplify license matching logic
perf: Optimize parallel processing
chore: Update dependencies
```

### Branch Naming

```
feature/add-npm-support
fix/cache-invalidation
docs/api-reference
test/integration-tests
```

## Testing Guidelines

### Unit Tests

- Test individual functions/methods
- Mock external dependencies
- Use pytest fixtures
- Aim for high coverage

```python
import pytest
from permitcheck.core.validator import LicenseValidator

@pytest.fixture
def validator():
    policy = LicensePolicy(
        allowed_licenses={'MIT'},
        trigger_error_licenses={'GPL-3.0'},
        skip_libraries=set()
    )
    return LicenseValidator(policy)

def test_validate_allowed(validator):
    deps = {'pytest': {'MIT'}}
    result = validator.validate(deps)
    assert 'pytest' in result.allowed
    assert not result.has_errors
```

### Integration Tests

- Test complete workflows
- Use real dependencies where possible
- Test edge cases

### Test Coverage

- Aim for >80% coverage
- Focus on critical paths
- Test error conditions

## Documentation

### Docstrings

Use Google style docstrings:

```python
def match(self, license_str: str) -> Set[str]:
    """Match license string against SPDX licenses.
    
    Tries exact match, normalized match, SPDX expression parsing,
    and fuzzy matching in order.
    
    Args:
        license_str: License string to match
        
    Returns:
        Set of matched SPDX license identifiers
        
    Examples:
        >>> matcher.match('MIT License')
        {'MIT'}
        >>> matcher.match('MIT OR Apache-2.0')
        {'MIT', 'Apache-2.0'}
    """
```

### README Updates

Update README.md when adding:
- New features
- Configuration options
- Examples
- Breaking changes

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release notes
4. Tag release: `git tag v2.0.0`
5. Push tag: `git push origin v2.0.0`
6. GitHub Actions will automatically publish to PyPI

## Areas Needing Help

### High Priority

- NPM/JavaScript support implementation
- Performance optimizations
- Additional output formats

### Medium Priority

- More language plugins (Ruby, Go, Rust)
- Enhanced README detection
- Better error messages

### Low Priority

- Additional SPDX expression features
- Performance benchmarks
- Video tutorials

## Questions?

- Open a [Discussion](https://github.com/kirankotari/permitcheck/discussions)
- Create an [Issue](https://github.com/kirankotari/permitcheck/issues)
- Email: kirankotari@live.com

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to PermitCheck! 🎉
