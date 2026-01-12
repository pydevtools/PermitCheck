# PermitCheck

[![Tests](https://github.com/kirankotari/permitcheck/workflows/Tests/badge.svg)](https://github.com/kirankotari/permitcheck/actions)
[![PyPI version](https://badge.fury.io/py/permitcheck.svg)](https://badge.fury.io/py/permitcheck)
[![Python Versions](https://img.shields.io/pypi/pyversions/permitcheck.svg)](https://pypi.org/project/permitcheck/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> **A fast, modern license compliance checker for Python projects**

PermitCheck automatically scans your dependencies and validates them against your license policy. Built with performance in mind, it features parallel processing, smart caching, and multiple output formats for seamless integration into any workflow.

## ✨ Features

- 🚀 **Parallel Processing** - Fast dependency scanning with concurrent license lookups
- 💾 **Smart Caching** - Intelligent caching system to speed up repeated scans
- 🎯 **SPDX Expression Support** - Handles complex license expressions like `MIT OR Apache-2.0`
- 📊 **Multiple Output Formats** - Console, JSON, HTML, Markdown, CSV, and SARIF
- 🔍 **Enhanced Detection** - Extracts licenses from metadata, classifiers, LICENSE files, and READMEs
- ⚙️ **Flexible Configuration** - YAML or TOML-based policy configuration
- 🔌 **Plugin Architecture** - Extensible design for future language support
- 🤖 **CI/CD Ready** - Easy integration with GitHub Actions, GitLab CI, and more

## 📦 Installation

```bash
pip install permitcheck
```

Or using uv:

```bash
uv add permitcheck
```

## 🚀 Quick Start

### Basic Usage

Check Python dependencies with console output:

```bash
permitcheck -l python
```

### Output Formats

Generate reports in different formats:

```bash
# JSON output for CI/CD pipelines
permitcheck -l python --format json

# HTML report with charts and styling
permitcheck -l python --format html -o report.html

# Markdown for documentation
permitcheck -l python --format markdown -o compliance.md

# CSV for spreadsheet analysis
permitcheck -l python --format csv -o licenses.csv

# SARIF for security tools integration
permitcheck -l python --format sarif -o results.sarif
```

### Configuration

Create a `permitcheck.yaml` in your project root:

```yaml
allowed_licenses:
  - MIT
  - Apache-2.0
  - BSD-3-Clause
  - ISC

trigger_error_licenses:
  - GPL-3.0
  - AGPL-3.0
  - Proprietary
  - Unknown

skip_libraries:
  - internal-package
```

Or use `pyproject.toml`:

```toml
[licenses]
allowed = ["MIT", "Apache-2.0", "BSD-3-Clause"]
trigger_error = ["GPL-3.0", "AGPL-3.0", "Proprietary"]
skip_libraries = []
```

## 📖 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Output Formats](docs/output-formats.md)
- [CI/CD Integration](docs/ci-cd-integration.md)
- [API Reference](docs/api-reference.md)

## 🔧 CLI Options

```
Options:
  -l, --lang LANG         Languages to check: python, npm
  --format FORMAT         Output format: console, json, simple, html, markdown, csv, sarif
  -o, --output FILE       Write output to file instead of stdout
  -v, --version           Show version number
  -V, --verbose           Enable verbose output
  -q, --quiet             Suppress non-error output
  --clear-cache           Clear the license cache
  --no-cache              Disable caching for this run
  -h, --help              Show help message
```

## 💡 Examples

### CI/CD Integration

**GitHub Actions:**

```yaml
- name: Check License Compliance
  run: |
    pip install permitcheck
    permitcheck -l python --format sarif -o results.sarif
    
- name: Upload Results
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: results.sarif
```

**GitLab CI:**

```yaml
license-check:
  script:
    - pip install permitcheck
    - permitcheck -l python --format json
  artifacts:
    reports:
      license_scanning: license-report.json
```

### Advanced Usage

```bash
# Verbose output with detailed information
permitcheck -l python --verbose

# Quiet mode for CI (only errors)
permitcheck -l python --quiet

# Force fresh scan (bypass cache)
permitcheck -l python --no-cache

# Multiple output formats
permitcheck -l python --format html -o report.html
permitcheck -l python --format json -o results.json
```

## 🎯 Use Cases

- **Pre-commit Hooks** - Validate licenses before committing
- **CI/CD Pipelines** - Automated compliance checks on every build
- **Dependency Audits** - Regular license compliance reviews
- **Security Scanning** - Integrate with security tools via SARIF
- **Documentation** - Generate license reports for stakeholders

## 🛠️ Development

### Setup

```bash
git clone https://github.com/kirankotari/permitcheck.git
cd permitcheck
uv sync
```

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=permitcheck --cov-report=html

# Specific test suite
uv run pytest tests/test_integration.py -v
```

### Code Quality

```bash
# Format code
uv run black permitcheck tests

# Lint
uv run pylint permitcheck
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- SPDX for standardized license identifiers
- All contributors who have helped improve this project

## 📞 Support

- 📧 Email: kirankotari@live.com
- 🐛 Issues: [GitHub Issues](https://github.com/kirankotari/permitcheck/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/kirankotari/permitcheck/discussions)

---

**Made with ❤️ by [Kiran Kumar Kotari](https://github.com/kirankotari)**
