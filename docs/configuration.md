# Configuration Guide

PermitCheck supports two configuration formats: YAML and TOML.

## Configuration Files

PermitCheck looks for configuration in the following locations (in order):

1. `permitcheck.yaml`
2. `.permitcheck.yaml`
3. `permitcheck.yml`
4. `pyproject.toml` (in `[licenses]` section)

## YAML Configuration

Create a `permitcheck.yaml` in your project root:

```yaml
allowed_licenses:
  - MIT
  - Apache-2.0
  - BSD-3-Clause
  - ISC
  - BSD-2-Clause

trigger_error_licenses:
  - GPL-3.0
  - GPL-2.0
  - AGPL-3.0
  - Proprietary
  - Unknown

skip_libraries:
  - my-internal-package
  - legacy-dependency
```

## TOML Configuration

Add to your `pyproject.toml`:

```toml
[licenses]
allowed = [
    "MIT",
    "Apache-2.0",
    "BSD-3-Clause",
    "ISC",
]

trigger_error = [
    "GPL-3.0",
    "AGPL-3.0",
    "Proprietary",
    "Unknown",
]

skip_libraries = [
    "internal-package",
]
```

## Configuration Options

### allowed_licenses

List of licenses that are approved for use in your project.

**Examples:**
- `MIT`
- `Apache-2.0`
- `BSD-3-Clause`
- `ISC`
- `PSF-2.0` (Python Software Foundation)

**SPDX Support:**
PermitCheck recognizes SPDX license identifiers and handles complex expressions:
- `MIT OR Apache-2.0` - Either license is acceptable
- `GPL-2.0+` - GPL 2.0 or later versions
- `Apache-2.0 WITH LLVM-exception` - License with exceptions

### trigger_error_licenses

Licenses that will cause the validation to fail.

**Common Restrictive Licenses:**
- `GPL-3.0` - GNU General Public License v3
- `GPL-2.0` - GNU General Public License v2
- `AGPL-3.0` - GNU Affero General Public License
- `Proprietary` - Proprietary/commercial licenses
- `Unknown` - Unidentified licenses

**Why Trigger Errors?**
- Legal compliance requirements
- Incompatibility with your project's license
- Corporate policy restrictions
- Distribution limitations

### skip_libraries

Dependencies to skip during license checking.

**Use Cases:**
- Internal/private packages
- Development-only tools
- Legacy dependencies under review
- Packages with complex licensing

**Example:**
```yaml
skip_libraries:
  - my-company-internal
  - legacy-package-under-review
  - test-utility
```

## Policy Validation

PermitCheck validates your configuration and will warn about:

- **Conflicts**: A license in both `allowed` and `trigger_error`
- **Empty Policy**: No licenses defined
- **Invalid SPDX**: Malformed license expressions

## Common Configurations

### Permissive Open Source

For projects that accept most permissive licenses:

```yaml
allowed_licenses:
  - MIT
  - Apache-2.0
  - BSD-3-Clause
  - BSD-2-Clause
  - ISC
  - 0BSD
  - Unlicense

trigger_error_licenses:
  - GPL-3.0
  - GPL-2.0
  - AGPL-3.0
  - LGPL-3.0
  - LGPL-2.1
```

### Strict Commercial

For commercial projects with strict requirements:

```yaml
allowed_licenses:
  - MIT
  - Apache-2.0
  - BSD-3-Clause

trigger_error_licenses:
  - GPL-3.0
  - GPL-2.0
  - AGPL-3.0
  - LGPL-3.0
  - LGPL-2.1
  - MPL-2.0
  - EPL-2.0
  - CDDL-1.0
  - Proprietary
  - Unknown
```

### GPL-Compatible

For GPL-licensed projects:

```yaml
allowed_licenses:
  - GPL-3.0
  - GPL-2.0
  - LGPL-3.0
  - LGPL-2.1
  - MIT
  - Apache-2.0
  - BSD-3-Clause
  - BSD-2-Clause

trigger_error_licenses:
  - Proprietary
  - Unknown
```

## Environment-Specific Configuration

You can use different configurations for different environments:

```bash
# Development (more permissive)
permitcheck -l python --config permitcheck-dev.yaml

# Production (strict)
permitcheck -l python --config permitcheck-prod.yaml
```

## Cache Configuration

PermitCheck caches license information to speed up scans:

```bash
# Clear cache
permitcheck --clear-cache

# Disable cache for single run
permitcheck -l python --no-cache
```

**Cache Location:**
- Linux/macOS: `~/.permitcheck/cache/`
- Windows: `%USERPROFILE%\.permitcheck\cache\`

## Tips

1. **Start Permissive**: Begin with a broader set of allowed licenses and narrow down based on requirements
2. **Regular Reviews**: Update your policy as dependencies change
3. **Document Exceptions**: Comment why certain libraries are skipped
4. **Version Control**: Commit your configuration to track policy changes
5. **Team Alignment**: Ensure all team members understand the license policy

## Next Steps

- Explore [Output Formats](output-formats.md)
- Set up [CI/CD Integration](ci-cd-integration.md)
- Read [API Reference](api-reference.md)
