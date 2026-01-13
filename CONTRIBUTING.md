# Contributing to PermitCheck

Thank you for your interest in contributing to PermitCheck! We welcome contributions from the community.

## 🚀 Quick Start for Contributors

1. **[Fork and clone](https://github.com/kirankotari/permitcheck/fork)** the repository
2. **Install development dependencies**: See [Installation Guide](docs/installation.md#from-source)
3. **Make your changes** and test them
4. **Submit a pull request**

## 📖 Documentation for Contributors

Before contributing, please review:

| Document | Purpose |
|----------|---------|
| **[Architecture](docs/architecture.md)** | Understand system design and workflow |
| **[Adding Languages](docs/adding-language-support.md)** | Create language plugins |
| **[Usage Guide](docs/usage-guide.md)** | API usage and examples |
| **[Roadmap](docs/ROADMAP.md)** | Future plans |

---

## 🎯 Types of Contributions

### 1. Bug Reports

**Found a bug?** Open an [issue](https://github.com/kirankotari/permitcheck/issues) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Version info (`permitcheck --version`)
- OS and Python version

### 2. Feature Requests

**Have an idea?** Start a [discussion](https://github.com/kirankotari/permitcheck/discussions):
- Describe the feature
- Explain the use case
- Check [Roadmap](docs/ROADMAP.md) first

### 3. Documentation Improvements

**Docs need fixing?**
- Fix typos or unclear sections
- Add examples
- Improve explanations
- All docs should be in `docs/` folder

### 4. Code Contributions

**Want to contribute code?**
- Check [existing issues](https://github.com/kirankotari/permitcheck/issues)
- Follow development setup below
- Write tests for new features
- Update documentation

### 5. Language Support (Plugins)

**Add support for new language?**
- Read [Adding Language Support](docs/adding-language-support.md)
- Check [example plugins](examples/)
- Follow plugin development guide
- Add tests

---

## 🛠️ Development Setup

### Prerequisites

- Python 3.10 or higher
- `uv` package manager (recommended)
- Git

### Setup Steps

```bash
# Clone repository
git clone https://github.com/kirankotari/permitcheck.git
cd permitcheck

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run with your changes
uv run permitcheck -l python
```

For detailed installation instructions, see [Installation Guide](docs/installation.md#from-source).

---

## 🧪 Testing

### Run All Tests

```bash
uv run pytest
```

### Run Specific Tests

```bash
# Test specific file
uv run pytest tests/test_python/

# Test with coverage
uv run pytest --cov=permitcheck --cov-report=html
```

### Writing Tests

- Add tests for new features in `tests/`
- Follow existing test structure
- Use pytest fixtures
- Aim for high coverage

---

## 📝 Code Style

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Document public APIs
- Keep functions small and focused

### Example

```python
def check_license(package: str, licenses: set[str]) -> bool:
    """
    Check if package license is allowed.
    
    Args:
        package: Package name
        licenses: Set of allowed licenses
        
    Returns:
        True if allowed, False otherwise
    """
    # Implementation
    pass
```

### Formatting

```bash
# Format code (when available)
black permitcheck/

# Sort imports
isort permitcheck/

# Type checking
mypy permitcheck/
```

---

## 🔌 Adding Language Support

To add support for a new language:

1. **Read the guide**: [Adding Language Support](docs/adding-language-support.md)
2. **Check examples**: See [examples/](examples/) for Ruby, Go, Java templates
3. **Create plugin**: Inherit from `Plugin` base class
4. **Implement methods**: `run()`, `load_settings()`
5. **Add tests**: Create test files in `tests/`
6. **Update docs**: Add language to [Roadmap](docs/ROADMAP.md)

### Plugin Template

```python
from permitcheck.plugin import Plugin

class ForNewLang(Plugin):
    """Plugin for NewLang language."""
    
    def __init__(self):
        super().__init__()
        self.language = 'newlang'
        self.file_patterns = ['package.json']  # Files to look for
    
    def run(self) -> dict[str, set[str]]:
        """Discover dependencies and their licenses."""
        # Implementation
        return {'package-name': {'MIT'}}
    
    def load_settings(self) -> tuple[set, set, set]:
        """Load policy settings."""
        # Implementation
        return (allowed_set, trigger_error_set, skip_set)
```

For complete guide, see [Adding Language Support](docs/adding-language-support.md).

---

## 🚀 Pull Request Process

### Before Submitting

- [ ] Tests pass locally (`uv run pytest`)
- [ ] Code follows style guidelines
- [ ] Documentation updated (if needed)
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Guidelines

1. **Create a feature branch**: `git checkout -b feature/your-feature`
2. **Make your changes**: Keep commits focused and atomic
3. **Write good commit messages**:
   ```
   Add Ruby plugin support
   
   - Implement ForRuby plugin class
   - Add Gemfile.lock parser
   - Add tests for Ruby dependencies
   - Update documentation
   ```
4. **Push and create PR**: Describe changes clearly
5. **Respond to feedback**: Be open to suggestions

### PR Title Format

```
[Type] Brief description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- test: Test additions/changes
- refactor: Code refactoring
- chore: Maintenance tasks
```

### Examples

- `feat: Add Ruby language support`
- `fix: Handle missing pyproject.toml gracefully`
- `docs: Update installation guide with uv instructions`

---

## 📋 Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

### Examples

```
feat(plugin): add support for Ruby language

Implement ForRuby plugin to parse Gemfile.lock and detect
Ruby gem licenses. Includes tests and documentation updates.

Closes #123
```

```
fix(cache): handle corrupted cache files gracefully

Previously, corrupted cache files would crash the application.
Now they are detected and cleared automatically.

Fixes #456
```

---

## 🐛 Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Run with Verbose Output

```bash
permitcheck -l python --debug  # If --debug flag exists
```

### Common Issues

- **Import errors**: Check `uv sync` ran successfully
- **Test failures**: Ensure dependencies are up to date
- **Plugin not loading**: Check file naming and class name

---

## 📚 Documentation Guidelines

### Documentation Structure

All documentation lives in `docs/`:

```
docs/
├── README.md                    # Documentation index
├── installation.md              # Installation guide
├── usage-guide.md               # Complete usage with API
├── configuration.md             # Configuration reference
├── architecture.md              # System design and workflow
├── adding-language-support.md   # Plugin development
├── output-formats.md            # Output formats
├── ci-cd-integration.md         # CI/CD setup
├── ROADMAP.md                   # Future plans
└── QUICK_REFERENCE.md           # Command cheat sheet
```

### Documentation Principles

1. **No Duplication**: Link to other docs instead of copying content
2. **User-Focused**: Write for the reader's perspective
3. **Example-Rich**: Show code examples for concepts
4. **Keep Updated**: Update docs with code changes

### Adding Documentation

When adding documentation:
- Place in `docs/` folder
- Add link in `docs/README.md`
- Cross-reference related docs
- Include code examples
- Use proper markdown formatting

---

## 🤝 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

**Positive behavior**:
- Using welcoming language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

**Unacceptable behavior**:
- Harassment or discriminatory language
- Trolling or insulting comments
- Public or private harassment
- Publishing others' private information

### Enforcement

Violations can be reported to kirankotari@live.com. All complaints will be reviewed and investigated.

---

## 📞 Getting Help

### Questions?

- **GitHub Discussions**: [Start a discussion](https://github.com/kirankotari/permitcheck/discussions)
- **Email**: kirankotari@live.com
- **Issues**: For bug reports only

### Resources

- [Architecture Guide](docs/architecture.md) - Understand the codebase
- [Usage Guide](docs/usage-guide.md) - API usage and examples
- [Examples](examples/) - Plugin code examples

---

## 📜 License

By contributing to PermitCheck, you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).

---

## 🎉 Recognition

Contributors are recognized in:
- [GitHub Contributors](https://github.com/kirankotari/permitcheck/graphs/contributors)
- Release notes
- README acknowledgments

**Thank you for contributing to PermitCheck!** 🚀
