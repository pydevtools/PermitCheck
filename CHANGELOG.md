# Changelog

All notable changes to PermitCheck will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-12

### Added
- **Parallel Processing**: Fast dependency scanning with concurrent license lookups using ThreadPoolExecutor
- **Enhanced License Detection**: Multiple fallback methods including:
  - LICENSE file parsing (LICENSE, LICENSE.txt, LICENSE.md, COPYING)
  - README.md license section extraction with regex patterns
  - Improved metadata and classifier detection
- **New Output Formats**:
  - Markdown format for documentation
  - CSV format for spreadsheet analysis
  - SARIF format for security tools integration (GitHub Security, VS Code)
- **SPDX Expression Support**: Parse and handle complex license expressions
  - OR operator: `MIT OR Apache-2.0`
  - AND operator: `MIT AND Apache-2.0`
  - WITH operator: `GPL-2.0 WITH Classpath-exception-2.0`
  - Plus suffix: `GPL-2.0+` → `GPL-2.0-or-later`
- **HTML Report Format**: Rich HTML reports with:
  - Responsive design with inline CSS
  - Gradient headers and status badges
  - Color-coded status indicators
  - Summary cards with metrics
  - Sortable dependency tables
- **CI/CD Pipeline**: Automated testing and releases via GitHub Actions
  - Multi-OS testing (Ubuntu, macOS, Windows)
  - Multi-Python version support (3.10, 3.11, 3.12)
  - Code coverage integration with Codecov
  - Black formatting checks
  - Pylint code quality checks
  - Automated PyPI publishing on version tags
- **Enhanced CLI**:
  - `--verbose/-V` flag for detailed output
  - `--quiet/-q` flag for minimal output
  - `-o/--output FILE` flag for file output
  - Better help text and usage examples
  - Emoji indicators for better readability
- **Smart Caching**: Improved caching system with:
  - Faster cache lookups
  - Version-aware caching
  - Cache statistics
  - Expiration handling

### Changed
- **Build System**: Migrated from Poetry to uv with hatchling backend
- **Python Version**: Minimum version increased from 3.9 to 3.10
- **Core Architecture**: Refactored into modular components:
  - `core.cache`: License caching system
  - `core.config`: Configuration management
  - `core.matcher`: License matching and normalization
  - `core.reporter`: Multi-format output generation
  - `core.validator`: License validation logic
- **Dependency Parsing**: Fixed version specifier handling for parenthesized formats
- **License Matching**: Enhanced fuzzy matching with configurable threshold

### Fixed
- Fixed dependency parsing for packages with parenthesized version specs (e.g., `requests (>=2.32.3,<3.0.0)`)
- Fixed wildcard imports in license/update.py
- Fixed output file redirection for HTML and other formats
- Fixed YAML configuration key names (allowed_licenses, trigger_error_licenses)
- Fixed integration test API signatures

### Testing
- **68 Total Tests** covering all functionality:
  - 39 core tests (cache, config, matcher, reporter, validator)
  - 12 integration tests (end-to-end workflows)
  - 16 SPDX parser tests
  - 1 legacy test
- All tests passing with 100% success rate
- Comprehensive test coverage for new features

### Documentation
- New comprehensive README with feature highlights
- Installation guide
- Configuration guide
- Output format examples
- CI/CD integration examples
- API reference

## [1.0.0] - Previous Release

### Initial Release
- Basic license checking for Python packages
- Console and JSON output formats
- YAML and TOML configuration support
- Simple license validation
- Basic caching mechanism

---

## Upgrade Guide

### From 1.x to 2.0

**Python Version Requirement:**
- Update to Python 3.10 or higher

**Build System:**
If you're building from source, install `uv`:
```bash
pip install uv
uv sync
```

**Configuration:**
No breaking changes to configuration format. Existing `permitcheck.yaml` and `pyproject.toml` files work as-is.

**CLI:**
All existing commands work identically. New options are additive only.

**Output Formats:**
- Old formats (console, json, simple) unchanged
- New formats (html, markdown, csv, sarif) available via `--format` flag

**API:**
Internal API has been refactored but maintains backward compatibility for public interfaces.
