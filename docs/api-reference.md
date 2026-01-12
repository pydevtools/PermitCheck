# API Reference

PermitCheck provides a Python API for programmatic access.

## Core Modules

### permitcheck.lint

Legacy compatibility wrapper maintaining backward compatibility.

```python
from permitcheck.lint import PermitCheck, Settings

# Define dependencies
deps = {
    'pytest': {'MIT'},
    'requests': {'Apache-2.0'},
    'certifi': {'MPL-2.0'}
}

# Define settings (allowed, trigger_error, skip)
settings = (
    {'MIT', 'Apache-2.0', 'BSD-3-Clause'},  # allowed
    {'GPL-3.0', 'AGPL-3.0'},                # trigger_error
    set()                                    # skip
)

# Run validation
checker = PermitCheck(deps, settings, output_format='console')

# Access results
print(f"Allowed: {checker.allowed}")
print(f"Errors: {checker.errors}")
print(f"Warnings: {checker.warnings}")
```

### permitcheck.core.config

Configuration management.

```python
from pathlib import Path
from permitcheck.core.config import ConfigManager, LicensePolicy

# Load from file
config_manager = ConfigManager(base_dir=Path('.'))
policy = config_manager.load_policy()

# Create policy manually
policy = LicensePolicy(
    allowed_licenses={'MIT', 'Apache-2.0'},
    trigger_error_licenses={'GPL-3.0'},
    skip_libraries={'internal-pkg'}
)

# Validate policy
policy.validate()  # Raises ConfigurationError if invalid
```

### permitcheck.core.validator

License validation logic.

```python
from permitcheck.core.validator import LicenseValidator, ValidationResult
from permitcheck.core.config import LicensePolicy

# Create policy
policy = LicensePolicy(
    allowed_licenses={'MIT', 'Apache-2.0'},
    trigger_error_licenses={'GPL-3.0'},
    skip_libraries=set()
)

# Create validator
validator = LicenseValidator(policy)

# Validate dependencies
dependencies = {
    'pytest': {'MIT'},
    'requests': {'Apache-2.0'},
    'gpl-package': {'GPL-3.0'}
}

result = validator.validate(dependencies)

# Check results
print(f"Has errors: {result.has_errors}")
print(f"Has warnings: {result.has_warnings}")
print(f"Is success: {result.is_success}")
print(f"Allowed: {result.allowed}")
print(f"Errors: {result.errors}")
print(f"Warnings: {result.warnings}")
```

### permitcheck.core.reporter

Multi-format output generation.

```python
from permitcheck.core.reporter import Reporter, OutputFormat
from permitcheck.core.validator import ValidationResult

# Create result
result = ValidationResult(
    allowed={'pytest', 'requests'},
    errors={'gpl-package'},
    warnings={'unknown-pkg'},
    skipped=set()
)

dependencies = {
    'pytest': {'MIT'},
    'requests': {'Apache-2.0'},
    'gpl-package': {'GPL-3.0'},
    'unknown-pkg': {'Unknown'}
}

# Console output
reporter = Reporter(format=OutputFormat.CONSOLE)
reporter.report(result, dependencies, language='python')

# JSON output
reporter = Reporter(format=OutputFormat.JSON)
reporter.report(result, dependencies, language='python')

# HTML output to file
with open('report.html', 'w') as f:
    reporter = Reporter(format=OutputFormat.HTML)
    reporter.report(result, dependencies, language='python', output=f)
```

### permitcheck.core.matcher

License matching and normalization.

```python
from permitcheck.core.matcher import LicenseMatcher, SPDXExpressionParser

# Create matcher
spdx_licenses = {'MIT', 'Apache-2.0', 'BSD-3-Clause', 'GPL-2.0-or-later'}
matcher = LicenseMatcher(spdx_licenses, fuzzy_threshold=0.85)

# Match single license
matched = matcher.match('MIT License')
print(matched)  # {'MIT'}

# Match with fuzzy matching
matched = matcher.match('Apache 2.0')
print(matched)  # {'Apache-2.0'}

# Normalize license set
licenses = {'mit', 'Apache License 2.0', 'BSD'}
normalized = matcher.normalize_license_set(licenses)
print(normalized)  # {'MIT', 'Apache-2.0', 'BSD'}

# Parse SPDX expressions
parser = SPDXExpressionParser()
licenses = parser.parse('MIT OR Apache-2.0')
print(licenses)  # ['MIT', 'Apache-2.0']

licenses = parser.parse('GPL-2.0+')
print(licenses)  # ['GPL-2.0-or-later']
```

### permitcheck.core.cache

License caching system.

```python
from permitcheck.core.cache import LicenseCache

# Create cache
cache = LicenseCache()

# Set licenses for package
cache.set('pytest', {'MIT'})

# Get cached licenses
licenses = cache.get('pytest')
print(licenses)  # {'MIT'}

# Check cache statistics
stats = cache.stats()
print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Size: {stats['size']}")

# Clear cache
cache.clear()

# Clear expired entries only
cache.clear_expired()
```

### permitcheck.plugins.for_python

Python dependency scanning.

```python
from permitcheck.plugins.for_python import PythonPlugin, PythonLicense

# Use plugin
plugin = PythonPlugin()
dependencies = plugin.run()

# Get settings
settings = plugin.load_settings()

# Get license for specific package
py_license = PythonLicense()
licenses = py_license.get_package_license('pytest')
print(licenses)  # {'MIT'}
```

## Exception Classes

```python
from permitcheck.exceptions import (
    PermitCheckError,
    PermitCheckWarning,
    PermitCheckInfo,
    ConfigurationError
)

try:
    # Your code
    pass
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except PermitCheckError as e:
    print(f"Error: {e}")
```

## Complete Example

```python
#!/usr/bin/env python3
"""Complete example of using PermitCheck API."""

from pathlib import Path
from permitcheck.core.config import ConfigManager
from permitcheck.core.validator import LicenseValidator
from permitcheck.core.reporter import Reporter, OutputFormat
from permitcheck.plugins.for_python import PythonPlugin

def main():
    # 1. Load configuration
    config_manager = ConfigManager(base_dir=Path('.'))
    policy = config_manager.load_policy()
    
    # 2. Scan dependencies
    plugin = PythonPlugin()
    dependencies = plugin.run()
    
    if not dependencies:
        print("No dependencies found")
        return
    
    # 3. Validate against policy
    validator = LicenseValidator(policy)
    result = validator.validate(dependencies)
    
    # 4. Generate reports
    
    # Console output
    console_reporter = Reporter(format=OutputFormat.CONSOLE)
    console_reporter.report(result, dependencies, language='python')
    
    # HTML report
    with open('license-report.html', 'w') as f:
        html_reporter = Reporter(format=OutputFormat.HTML)
        html_reporter.report(result, dependencies, language='python', output=f)
    
    # JSON report
    with open('license-report.json', 'w') as f:
        json_reporter = Reporter(format=OutputFormat.JSON)
        json_reporter.report(result, dependencies, language='python', output=f)
    
    # 5. Exit with appropriate code
    if result.has_errors:
        exit(1)
    else:
        exit(0)

if __name__ == '__main__':
    main()
```

## Type Hints

PermitCheck is fully type-hinted. Use with mypy:

```python
from typing import Dict, Set
from permitcheck.core.validator import ValidationResult

def process_results(result: ValidationResult) -> Dict[str, Set[str]]:
    """Process validation results."""
    return {
        'allowed': result.allowed,
        'errors': result.errors,
        'warnings': result.warnings
    }
```

## Async Support

Currently, PermitCheck uses ThreadPoolExecutor for parallel processing. Async support is planned for future releases.

## Testing

Test your integration:

```python
import pytest
from permitcheck.core.config import LicensePolicy
from permitcheck.core.validator import LicenseValidator

def test_license_validation():
    policy = LicensePolicy(
        allowed_licenses={'MIT'},
        trigger_error_licenses={'GPL-3.0'},
        skip_libraries=set()
    )
    
    validator = LicenseValidator(policy)
    
    dependencies = {
        'pytest': {'MIT'},
        'bad-package': {'GPL-3.0'}
    }
    
    result = validator.validate(dependencies)
    
    assert 'pytest' in result.allowed
    assert 'bad-package' in result.errors
    assert result.has_errors
```

## Next Steps

- Review [Configuration](configuration.md)
- Explore [Output Formats](output-formats.md)
- Set up [CI/CD Integration](ci-cd-integration.md)
