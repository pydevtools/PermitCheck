# PermitCheck Quick Reference

One-page quick reference for PermitCheck users and developers.

---

## 🚀 Installation

```bash
# Using uv (recommended)
uv add permitcheck

# Using pip
pip install permitcheck

# From source
git clone https://github.com/kirankotari/permitcheck.git
cd permitcheck && uv sync
```

---

## 📋 Basic Commands

```bash
# Check Python dependencies
permitcheck -l python

# Check with custom config
permitcheck -l python -c config.yaml

# Export to JSON
permitcheck -l python -f json -o report.json

# Export to HTML report
permitcheck -l python -f html -o report.html

# Clear cache
permitcheck --clear-cache

# Get package license info
permitcheck --info requests
```

---

## ⚙️ Configuration

### YAML Format (`permitcheck.yaml`)

```yaml
licenses:
  allowed:
    - MIT
    - Apache-2.0
    - BSD-3-Clause
  
  trigger_error:
    - GPL-3.0
    - AGPL-3.0
  
  skip_libraries:
    - internal-package
```

### TOML Format (`pyproject.toml`)

```toml
[tool.permitcheck]
allowed = ["MIT", "Apache-2.0", "BSD-3-Clause"]
trigger_error = ["GPL-3.0", "AGPL-3.0"]
skip_libraries = ["internal-package"]
```

---

## 📊 Output Formats

| Format | Usage | Best For |
|--------|-------|----------|
| `console` | `-f console` | Terminal/human reading |
| `json` | `-f json` | CI/CD, automation |
| `html` | `-f html` | Reports, stakeholders |
| `markdown` | `-f markdown` | Documentation |
| `csv` | `-f csv` | Spreadsheet analysis |
| `sarif` | `-f sarif` | Security scanning |
| `simple` | `-f simple` | Plain text logs |

---

## 🔌 Plugin Development (Quick)

### 1. Create Plugin File
```bash
touch permitcheck/plugins/for_<language>.py
```

### 2. Implement Plugin Class
```python
from permitcheck.plugin import Plugin

class LanguagePlugin(Plugin):
    def get_name(self) -> str:
        return "<language>"
    
    def run(self) -> Optional[Dict[str, Set[str]]]:
        # Discover dependencies
        # Return: {'package': {'MIT', 'Apache-2.0'}}
        pass
    
    def load_settings(self) -> Optional[Tuple[Set, Set, Set]]:
        # Return: (allowed, trigger_error, skip)
        return None
```

### 3. Key Methods to Implement
- `_discover_dependencies()` - Parse manifest files
- `_get_package_license()` - Fetch licenses
- `_fetch_license_from_source()` - Query APIs/files

---

## 🎯 Common Use Cases

### CI/CD Integration (GitHub Actions)
```yaml
- name: License Check
  run: |
    pip install permitcheck
    permitcheck -l python -f sarif -o results.sarif
```

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: permitcheck
        name: License Compliance
        entry: permitcheck -l python
        language: system
        pass_filenames: false
```

### Programmatic API
```python
from permitcheck.core.validator import LicenseValidator, LicensePolicy

policy = LicensePolicy(
    allowed={'MIT', 'Apache-2.0'},
    trigger_error={'GPL-3.0'},
    skip_libraries=set()
)

validator = LicenseValidator(policy)
result = validator.validate({'pkg': {'MIT'}})
```

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| Unknown licenses | Check package metadata, add to skip list |
| Cache stale | Run `permitcheck --clear-cache` |
| Config not found | Ensure file is named `permitcheck.yaml` |
| Slow performance | Cache is building (fast on second run) |

---

## 📚 Documentation Links

| Topic | Link |
|-------|------|
| **Complete Usage** | [usage-guide.md](./usage-guide.md) |
| **Architecture** | [architecture.md](./architecture.md) |
| **Plugin Development** | [adding-language-support.md](./adding-language-support.md) |
| **Contributing** | [CONTRIBUTING.md](./CONTRIBUTING.md) |
| **Examples** | [examples/](../examples/) |

---

## 🎨 Output Examples

### Console Output
```
✅ Allowed (45):
  ✓ requests (Apache-2.0)
  ✓ pytest (MIT)

❌ Violations (1):
  ✗ gpl-lib (GPL-3.0)

⚠️  Unknown (2):
  ? internal-lib (Unknown)
```

### JSON Output
```json
{
  "summary": {"total": 48, "allowed": 45, "violations": 1, "warnings": 2},
  "allowed": [{"package": "requests", "licenses": ["Apache-2.0"]}],
  "violations": [{"package": "gpl-lib", "licenses": ["GPL-3.0"]}]
}
```

---

## 🌐 Supported Languages

| Language | Status | Manifest Files |
|----------|--------|----------------|
| Python | ✅ Full | requirements.txt, pyproject.toml |
| npm | 🚧 In Dev | package.json |
| Ruby | 📋 Example | Gemfile |
| Go | 📋 Example | go.mod |
| Java | 📋 Example | pom.xml |

---

## 🚦 Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success (no violations) |
| `1` | Violations found or error |
| `130` | User interrupted (Ctrl+C) |

---

## 📊 Performance

| Scenario | Time | Cache |
|----------|------|-------|
| First run (50 deps) | 5-15s | Cold |
| Second run | 0.5-2s | Warm |
| **Speedup** | **10-50x** | - |

---

## 🔐 SPDX License Identifiers

Common SPDX identifiers to use in config:

```
Permissive:
  - MIT
  - Apache-2.0
  - BSD-2-Clause
  - BSD-3-Clause
  - ISC

Copyleft:
  - GPL-2.0
  - GPL-3.0
  - LGPL-2.1
  - LGPL-3.0
  - AGPL-3.0

Other:
  - MPL-2.0
  - CC-BY-4.0
  - Unlicense
```

Full list: https://spdx.org/licenses/

---

## 📦 Package Registry APIs

| Language | Registry | API Endpoint |
|----------|----------|--------------|
| Python | PyPI | `https://pypi.org/pypi/{package}/json` |
| npm | npm | `https://registry.npmjs.org/{package}` |
| Ruby | RubyGems | `https://rubygems.org/api/v1/gems/{gem}.json` |
| Java | Maven | `https://search.maven.org/solrsearch/select` |
| Go | GitHub | `https://api.github.com/repos/{owner}/{repo}` |

---

## 🛠️ Development Commands

```bash
# Run tests
uv run pytest

# With coverage
uv run pytest --cov=permitcheck

# Format code
uv run ruff format

# Type check
uv run mypy permitcheck

# Lint
uv run ruff check
```

---

## 💡 Pro Tips

1. **Use base identifiers**: `Apache` expands to all Apache variants
2. **Cache is your friend**: 10-50x speedup on subsequent runs
3. **SARIF for security**: Integrates with GitHub Security tab
4. **Skip internal packages**: Add to `skip_libraries` config
5. **Parallel processing**: Automatically used for dependencies

---

## 🤝 Get Help

- **Issues**: https://github.com/kirankotari/permitcheck/issues
- **Discussions**: https://github.com/kirankotari/permitcheck/discussions
- **Email**: kirankotari@live.com

---

## 📖 Further Reading

**New Users**:
1. [Installation](installation.md)
2. [Usage Guide](usage-guide.md)
3. [Configuration](configuration.md)

**Contributors**:
1. [Architecture](architecture.md)
2. [Plugin Dev Guide](adding-language-support.md)
3. [Examples](../examples/)

---

**Version**: 2.0.0  
**Last Updated**: 2024  
**License**: Apache 2.0
