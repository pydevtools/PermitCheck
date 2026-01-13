# PermitCheck Usage Guide

Complete guide to using PermitCheck for license compliance checking.

## Table of Contents
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CLI Usage](#cli-usage)
- [Programmatic API](#programmatic-api)
- [Output Formats](#output-formats)
- [CI/CD Integration](#cicd-integration)
- [Advanced Usage](#advanced-usage)

---

> **Note**: Need to install PermitCheck first? See [Installation Guide](installation.md).

---

## Quick Start

### Basic Usage

Check Python dependencies in current directory:
```bash
permitcheck -l python
```

Check with custom config:
```bash
permitcheck -l python -c my-config.yaml
```

Check multiple languages:
```bash
permitcheck -l python npm
```

### Expected Output

```
🔍 Checking Python dependencies...

✅ Allowed (45):
  ✓ requests (Apache-2.0)
  ✓ pytest (MIT)
  ✓ click (BSD-3-Clause)
  ...

⚠️  Unknown Licenses (2):
  ? internal-lib (Unknown)
  ? custom-package (Unknown)

❌ Violations (1):
  ✗ gpl-package (GPL-3.0) - Denied by policy

Summary: 1 error(s), 2 warning(s)
```

---

## Configuration

> **Detailed Configuration**: See [Configuration Guide](configuration.md) for full details on policy setup, license identifiers, and advanced options.

### Quick Configuration Example

**YAML** (`permitcheck.yaml`):
```yaml
licenses:
  allowed: [MIT, Apache-2.0, BSD-3-Clause]
  trigger_error: [GPL-3.0, AGPL-3.0]
  skip_libraries: [internal-package]
```

**TOML** (`pyproject.toml`):
```toml
[tool.permitcheck]
allowed = ["MIT", "Apache-2.0", "BSD-3-Clause"]
trigger_error = ["GPL-3.0", "AGPL-3.0"]
skip_libraries = ["internal-package"]
```

**Using custom config**:
```bash
permitcheck -l python -c my-config.yaml
```

For configuration file discovery order, base identifiers, and advanced features, see [Configuration Guide](configuration.md).

---

## CLI Usage

### Command Line Options

```bash
permitcheck [OPTIONS]
```

| Option | Description | Example |
|--------|-------------|---------|
| `-l, --lang` | Languages to check | `-l python npm` |
| `-c, --config` | Custom config file | `-c my-config.yaml` |
| `-f, --format` | Output format | `-f json` |
| `-o, --output` | Output file | `-o report.html` |
| `--clear-cache` | Clear license cache | `--clear-cache` |
| `--info <package>` | Show license info | `--info requests` |
| `--version` | Show version | `--version` |
| `-h, --help` | Show help | `-h` |

### Examples

**Check specific languages**:
```bash
permitcheck -l python
permitcheck -l python npm
```

**Use custom config**:
```bash
permitcheck -l python -c strict-policy.yaml
```

**Export to JSON**:
```bash
permitcheck -l python -f json -o report.json
```

**Export to HTML**:
```bash
permitcheck -l python -f html -o report.html
```

**Export to SARIF (for security scanning)**:
```bash
permitcheck -l python -f sarif -o results.sarif
```

**Clear cache and re-check**:
```bash
permitcheck --clear-cache
permitcheck -l python
```

**Get license info for a package**:
```bash
permitcheck --info requests
# Output: requests: Apache-2.0
```

---

## Programmatic API

### Basic API Usage

```python
from permitcheck.core.config import ConfigManager, LicensePolicy
from permitcheck.core.validator import LicenseValidator
from permitcheck.core.reporter import Reporter, OutputFormat

# Load configuration
config_manager = ConfigManager()
policy = config_manager.load_policy()

# Or create policy programmatically
policy = LicensePolicy(
    allowed={'MIT', 'Apache-2.0', 'BSD-3-Clause'},
    trigger_error={'GPL-3.0', 'AGPL-3.0'},
    skip_libraries=set()
)

# Validate dependencies
validator = LicenseValidator(policy)
dependencies = {
    'requests': {'Apache-2.0'},
    'pytest': {'MIT'},
    'gpl-lib': {'GPL-3.0'}
}

result = validator.validate(dependencies)

# Generate report
reporter = Reporter(output_format=OutputFormat.CONSOLE)
report = reporter.format(result, language='python', file_handle=None)
print(report)
```

### Plugin API Usage

```python
from permitcheck.plugin import PluginManager

# Load all plugins
manager = PluginManager()
manager.load_plugins()

# Get plugin by language
python_plugin = manager.get_plugins_by_language('python')[0]

# Run plugin to discover dependencies
dependencies = python_plugin.run()
# Returns: {'requests': {'Apache-2.0'}, ...}

# Load plugin-specific settings
settings = python_plugin.load_settings()
# Returns: (allowed_set, trigger_error_set, skip_set)
```

### License Matcher API

```python
from permitcheck.core.matcher import LicenseMatcher

matcher = LicenseMatcher(known_licenses={'MIT', 'Apache-2.0', 'BSD-3-Clause'})

# Match license string
licenses = matcher.match('MIT or Apache-2.0')
# Returns: {'MIT', 'Apache-2.0'}

# Normalize license variations
licenses = matcher.normalize_license_set({'apache 2', 'mit license'})
# Returns: {'Apache-2.0', 'MIT'}

# Match from text (LICENSE file content)
content = open('LICENSE').read()
licenses = matcher.match(content)
# Returns: {'Apache-2.0'} (if content matches Apache)
```

### Cache API

```python
from permitcheck.core.cache import LicenseCache

cache = LicenseCache(ttl_seconds=86400)  # 24 hours

# Get cached license
licenses = cache.get('requests')
# Returns: {'Apache-2.0'} or None if not cached

# Set cache entry
cache.set('requests', {'Apache-2.0'})

# Clear entire cache
cache.clear()

# Clear specific entry
cache.delete('requests')
```

---

## Output Formats

> **Detailed Format Reference**: See [Output Formats Guide](output-formats.md) for complete format documentation, examples, and CI/CD integration.

### Available Formats

| Format | Usage | Best For |
|--------|-------|----------|
| `console` | `-f console` (default) | Terminal/human reading |
| `json` | `-f json` | CI/CD, automation |
| `html` | `-f html` | Reports, stakeholders |
| `markdown` | `-f markdown` | Documentation |
| `csv` | `-f csv` | Spreadsheet analysis |
| `sarif` | `-f sarif` | Security scanning |

### Quick Examples

```bash
# JSON for CI/CD
permitcheck -l python -f json -o report.json

# HTML for reports
permitcheck -l python -f html -o report.html

# SARIF for GitHub Security
permitcheck -l python -f sarif -o results.sarif
```

See [Output Formats Guide](output-formats.md) for complete format specifications and examples.

---

## CI/CD Integration

> **Detailed CI/CD Setup**: See [CI/CD Integration Guide](ci-cd-integration.md) for complete examples and best practices.

### Quick CI/CD Example (GitHub Actions)

```yaml
name: License Check
on: [push, pull_request]
jobs:
  license-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install permitcheck
      - run: permitcheck -l python
```

For GitLab CI, Jenkins, CircleCI, and other platforms, see [CI/CD Integration Guide](ci-cd-integration.md).

---

## Advanced Usage

### Custom Reporter

Create custom output format:

```python
from permitcheck.core.reporter import Reporter, OutputFormat
from permitcheck.core.validator import ValidationResult

class CustomReporter(Reporter):
    def _format_custom(self, result: ValidationResult, language: str) -> str:
        """Custom format implementation."""
        output = f"=== {language.upper()} LICENSE REPORT ===\n\n"
        
        if result.errors:
            output += "VIOLATIONS:\n"
            for pkg, licenses in result.errors:
                output += f"  - {pkg}: {', '.join(licenses)}\n"
        
        return output

# Use custom reporter
reporter = CustomReporter(output_format=OutputFormat.CONSOLE)
report = reporter._format_custom(result, 'python')
```

### Custom License Matcher

Extend matcher for custom licenses:

```python
from permitcheck.core.matcher import LicenseMatcher

class CustomMatcher(LicenseMatcher):
    def __init__(self):
        super().__init__(known_licenses)
        # Add custom aliases
        self.custom_aliases = {
            'my-proprietary': 'Company Proprietary License',
            'internal': 'Internal Use Only'
        }
    
    def match(self, license_string: str) -> Set[str]:
        # Check custom aliases first
        lower = license_string.lower()
        if lower in self.custom_aliases:
            return {self.custom_aliases[lower]}
        
        # Fall back to parent implementation
        return super().match(license_string)
```

### Parallel Processing

Process multiple projects concurrently:

```python
from concurrent.futures import ThreadPoolExecutor
from permitcheck.plugin import PluginManager

def check_project(project_dir):
    os.chdir(project_dir)
    manager = PluginManager()
    manager.load_plugins()
    # ... run checks
    return result

projects = ['project1', 'project2', 'project3']

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(check_project, projects))
```

### Programmatic Policy Creation

Build policy dynamically:

```python
from permitcheck.core.config import LicensePolicy

def build_policy_for_environment(env: str) -> LicensePolicy:
    if env == 'production':
        return LicensePolicy(
            allowed={'MIT', 'Apache-2.0', 'BSD-3-Clause'},
            trigger_error={'GPL-3.0', 'AGPL-3.0'},
            skip_libraries=set()
        )
    elif env == 'development':
        return LicensePolicy(
            allowed={'MIT', 'Apache-2.0', 'BSD-3-Clause', 'GPL-3.0'},
            trigger_error={'AGPL-3.0'},
            skip_libraries=set()
        )

policy = build_policy_for_environment('production')
```

---

## Troubleshooting

### Cache Issues

If seeing stale data:
```bash
permitcheck --clear-cache
```

### Unknown Licenses

If packages show "Unknown" license:
1. Check if package has LICENSE file
2. Verify package metadata (`pip show <package>`)
3. Manually add to skip list if internal package

### Performance

For large projects:
1. Cache is automatically used (10-50x speedup)
2. Dependencies are checked in parallel
3. Use `--clear-cache` only when needed

### Configuration Not Found

Ensure config file:
- Is named `permitcheck.yaml` or `pyproject.toml`
- Is in current or parent directory
- Has correct syntax (valid YAML/TOML)
- Has `[tool.permitcheck]` section (for pyproject.toml)

---

## Examples

### Example 1: Strict Production Policy

```yaml
# permitcheck.yaml
licenses:
  allowed:
    - MIT
    - Apache-2.0
    - BSD-3-Clause
  
  trigger_error:
    - GPL
    - AGPL
    - LGPL
    - Proprietary
    - Unknown
```

### Example 2: Permissive Development Policy

```yaml
licenses:
  allowed:
    - MIT
    - Apache
    - BSD
    - GPL
    - LGPL
  
  trigger_error:
    - Proprietary
  
  skip_libraries:
    - internal-lib
    - test-fixtures
```

### Example 3: Multi-Language Project

```bash
# Check all languages
permitcheck -l python npm

# Separate reports per language
permitcheck -l python -f json -o python-licenses.json
permitcheck -l npm -f json -o npm-licenses.json
```

---

## Best Practices

1. **Use configuration files**: Don't rely on defaults
2. **Include in CI/CD**: Catch violations early
3. **Review unknown licenses**: Investigate "Unknown" packages
4. **Keep cache fresh**: Clear cache periodically (weekly)
5. **Document policy**: Explain why licenses are allowed/denied
6. **Use SARIF format**: Integrate with security scanning tools
7. **Version your config**: Track policy changes over time

---

## Getting Help

- **Documentation**: https://github.com/kirankotari/permitcheck/tree/main/docs
- **Issues**: https://github.com/kirankotari/permitcheck/issues
- **Discussions**: https://github.com/kirankotari/permitcheck/discussions
- **Contributing**: See [CONTRIBUTING.md](./CONTRIBUTING.md)

---

## Related Documentation

- [Architecture Overview](./architecture.md)
- [Adding Language Support](./adding-language-support.md)
- [API Reference](./api-reference.md)
- [Configuration Guide](./configuration.md)
