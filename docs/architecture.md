# Architecture Overview

## Table of Contents
- [System Architecture](#system-architecture)
- [Core Components](#core-components)
- [Plugin System](#plugin-system)
- [Data Flow](#data-flow)
- [Caching Strategy](#caching-strategy)
- [Extension Points](#extension-points)

---

## System Architecture

PermitCheck follows a modular, plugin-based architecture that separates concerns and enables easy extension for new programming languages.

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│  (permitcheck_tool.py - User Interface & Orchestration)     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Core Layer                                │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │  Config   │  │ Validator│  │ Reporter │  │  Matcher  │ │
│  │  Manager  │  │          │  │          │  │           │ │
│  └───────────┘  └──────────┘  └──────────┘  └───────────┘ │
│                                                              │
│  ┌───────────┐                                              │
│  │   Cache   │  (License lookup optimization)              │
│  └───────────┘                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Plugin System                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         PluginManager (Discovery & Loading)          │  │
│  └───────────────┬──────────────────────────────────────┘  │
│                  │                                           │
│  ┌───────────────▼───────────┬──────────────┬─────────────┐│
│  │   PythonPlugin            │  NpmPlugin   │  [Future]   ││
│  │   - Requirements parser   │  - package.  │  - Java     ││
│  │   - pyproject.toml        │    json      │  - Ruby     ││
│  │   - pip metadata          │  - lock file │  - Go       ││
│  └───────────────────────────┴──────────────┴─────────────┘│
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│               External Resources                             │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │ Package       │  │ SPDX License│  │ File System      │  │
│  │ Metadata      │  │ Database    │  │ (LICENSE files)  │  │
│  └───────────────┘  └─────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Configuration Manager (`core/config.py`)

**Responsibility**: Load and parse license policies from configuration files.

**Key Classes**:
- `LicensePolicy`: Dataclass holding allowed/denied/skip license sets
- `ConfigManager`: Discovers and loads configuration from YAML/TOML files

**Features**:
- Multi-format support (YAML, pyproject.toml)
- Hierarchical config discovery (current dir → parent dirs → home)
- Base identifier expansion (e.g., `Apache` → all Apache variants)
- Validation (conflict detection, empty set warnings)

**Usage**:
```python
from permitcheck.core.config import ConfigManager

manager = ConfigManager()
policy = manager.load_policy()
# Returns: LicensePolicy(allowed={...}, trigger_error={...}, skip_libraries={...})
```

---

### 2. License Validator (`core/validator.py`)

**Responsibility**: Validate dependencies against license policy.

**Key Classes**:
- `ValidationResult`: Result container with errors/warnings/allowed lists
- `LicenseValidator`: Core validation engine

**Validation Logic**:
1. Check if library should be skipped
2. Check for trigger_error licenses → add to errors
3. Check for allowed licenses → add to allowed
4. Unknown licenses → add to warnings

**Usage**:
```python
from permitcheck.core.validator import LicenseValidator, LicensePolicy

policy = LicensePolicy(
    allowed={'MIT', 'Apache-2.0'},
    trigger_error={'GPL-3.0'},
    skip_libraries=set()
)

validator = LicenseValidator(policy)
result = validator.validate(dependencies={'pkg': {'MIT'}})
# Returns: ValidationResult with errors/warnings/allowed
```

---

### 3. License Matcher (`core/matcher.py`)

**Responsibility**: Match and normalize license strings using fuzzy matching.

**Key Features**:
- Fuzzy string matching (Levenshtein distance)
- SPDX expression parsing (`MIT OR Apache-2.0`)
- Common license alias mapping
- Version normalization (`GPL-2.0+` → `GPL-2.0-or-later`)

**Algorithm**:
1. Exact match check
2. Alias lookup (e.g., "apache 2" → "Apache-2.0")
3. SPDX expression parsing
4. Fuzzy matching with configurable threshold (default 85%)

**Usage**:
```python
from permitcheck.core.matcher import LicenseMatcher

matcher = LicenseMatcher(known_licenses={'MIT', 'Apache-2.0'})
licenses = matcher.match('MIT or Apache')
# Returns: {'MIT', 'Apache-2.0'}
```

---

### 4. Reporter (`core/reporter.py`)

**Responsibility**: Format and output validation results in multiple formats.

**Supported Formats**:
- **Console**: Color-coded terminal output with emojis
- **JSON**: Machine-readable structured data
- **HTML**: Rich, styled web reports with CSS
- **Markdown**: Documentation-friendly format
- **CSV**: Spreadsheet-compatible export
- **SARIF**: Static Analysis Results Interchange Format (for CI/CD)
- **Simple**: Plain text summary

**Architecture**:
```python
class Reporter:
    def __init__(self, output_format: OutputFormat = OutputFormat.CONSOLE):
        self.format_handlers = {
            OutputFormat.JSON: self._format_json,
            OutputFormat.HTML: self._format_html,
            # ... other formats
        }
```

---

### 5. License Cache (`core/cache.py`)

**Responsibility**: Cache license lookups to improve performance.

**Cache Strategy**:
- **Storage**: JSON file at `~/.permitcheck/license_cache.json`
- **TTL**: 24 hours (configurable)
- **Eviction**: Time-based, on-read cleanup
- **Size**: ~1-5KB per 100 packages

**Performance Impact**:
- Cache hit: ~1-2ms
- Cache miss (with README parsing): ~50-500ms
- **Speedup**: 10-50x for cached packages

**Usage**:
```python
from permitcheck.core.cache import LicenseCache

cache = LicenseCache(ttl_seconds=86400)
licenses = cache.get('requests')  # Try cache
if not licenses:
    licenses = fetch_from_metadata()
    cache.set('requests', licenses)  # Store for next time
```

---

## Plugin System

### Plugin Architecture

The plugin system enables language-specific dependency detection without modifying core code.

**Base Contract** (`Plugin` abstract class):
```python
class Plugin(abc.ABC):
    @abc.abstractmethod
    def get_name(self) -> str:
        """Return language identifier (e.g., 'python', 'npm')"""
        
    @abc.abstractmethod
    def run(self) -> Optional[Dict[str, Set[str]]]:
        """Discover dependencies and return {package: {licenses}}"""
        
    @abc.abstractmethod
    def load_settings(self) -> Optional[Tuple[Set[str], Set[str], Set[str]]]:
        """Load language-specific config (allowed, errors, skip)"""
```

### Plugin Discovery

**PluginManager** automatically discovers plugins:

1. **Directory Scanning**: Scans `permitcheck/plugins/` for `for_*.py` files
2. **Environment Variable**: Respects `PERMITCHECK_PLUGINPATH` for custom locations
3. **Dynamic Loading**: Uses importlib to load plugin modules
4. **Validation**: Checks plugin classes inherit from `Plugin` base class

**Discovery Flow**:
```
1. Scan permitcheck/plugins/
2. Check PERMITCHECK_PLUGINPATH env var
3. For each for_*.py file:
   a. Import module
   b. Find Plugin subclass
   c. Instantiate plugin
   d. Register in plugins dict
```

### Existing Plugins

#### 1. Python Plugin (`plugins/for_python.py`)

**Capabilities**:
- Parse `requirements.txt` and `requirements-*.txt` files
- Parse `pyproject.toml` (Poetry/Hatch/PDM)
- Extract licenses from package metadata
- Read LICENSE files from installed packages
- Parse README files for license info
- Use pip to resolve dependency tree

**License Detection Hierarchy**:
1. Package metadata (`License` field)
2. SPDX License-Expression
3. Classifiers (`License :: OSI Approved :: MIT`)
4. LICENSE files (LICENSE, LICENSE.txt, LICENSE.md)
5. README parsing (regex patterns)

**Example**:
```python
from permitcheck.plugins.for_python import PythonPlugin

plugin = PythonPlugin()
deps = plugin.run()
# Returns: {'requests': {'Apache-2.0'}, 'pytest': {'MIT'}}
```

#### 2. NPM Plugin (`plugins/for_npm.py`)

**Current Status**: Stub implementation (not yet functional)

**Planned Capabilities**:
- Parse `package.json` dependencies
- Parse `package-lock.json` for exact versions
- Query npm registry for license info
- Support yarn.lock and pnpm-lock.yaml

---

## Data Flow

### End-to-End Flow

```
1. CLI Entry Point (permitcheck_tool.py)
   ↓
2. Parse Arguments
   ↓
3. PluginManager.load_plugins()
   ↓
4. For each language plugin:
   a. plugin.run() → discover dependencies
   b. plugin.load_settings() → get policy
   ↓
5. LicenseCache.get() for each package
   ↓ (if miss)
6. Plugin fetches license from metadata
   ↓
7. LicenseMatcher.normalize()
   ↓
8. LicenseCache.set()
   ↓
9. LicenseValidator.validate()
   ↓
10. Reporter.format()
    ↓
11. Output to console/file
```

### Data Structures

**Dependencies Map**:
```python
Dict[str, Set[str]]
# Example:
{
    'requests': {'Apache-2.0'},
    'pytest': {'MIT'},
    'django': {'BSD-3-Clause'}
}
```

**LicensePolicy**:
```python
@dataclass
class LicensePolicy:
    allowed: Set[str]           # MIT, Apache-2.0, etc.
    trigger_error: Set[str]     # GPL-3.0, Proprietary
    skip_libraries: Set[str]    # internal-lib, etc.
```

**ValidationResult**:
```python
@dataclass
class ValidationResult:
    errors: List[Tuple[str, Set[str]]]      # Failed packages
    warnings: List[Tuple[str, Set[str]]]    # Unknown licenses
    allowed: List[Tuple[str, Set[str]]]     # Passed packages
    has_errors: bool
    has_warnings: bool
```

---

## Caching Strategy

### Cache Architecture

**Three-Tier Lookup**:
1. **Memory Cache**: In-process dict (fastest, session-only)
2. **Disk Cache**: JSON file (persistent, 24hr TTL)
3. **Source Fetch**: Metadata/README parsing (slowest)

### Cache Invalidation

**Triggers**:
- Time-based: 24 hours (configurable)
- Manual: `permitcheck --clear-cache`
- Automatic: On corrupt cache file

**Strategy**: Lazy eviction (check on read, not background)

### Cache Key Design

**Key Format**: `package_name` (lowercase, normalized)

**Rationale**:
- No version in key (licenses rarely change per version)
- Simple string key for fast lookup
- Lowercase for case-insensitive matching

---

## Extension Points

### Adding a New Language Plugin

See [Contributing Guide - Adding Language Support](./CONTRIBUTING.md#adding-language-support) for detailed steps.

**Quick Overview**:

1. **Create Plugin File**: `permitcheck/plugins/for_<language>.py`
2. **Implement Plugin Class**:
```python
from permitcheck.plugin import Plugin

class LanguagePlugin(Plugin):
    def get_name(self) -> str:
        return "language"
    
    def run(self) -> Optional[Dict[str, Set[str]]]:
        # Discover dependencies
        # Extract licenses
        return {'package': {'MIT'}}
    
    def load_settings(self) -> Optional[Tuple[Set[str], Set[str], Set[str]]]:
        # Load from config file
        return (allowed, trigger_error, skip)
```

3. **Add Tests**: `tests/plugins/test_for_<language>.py`
4. **Update CLI**: Add language to choices in `permitcheck_tool.py`

### Custom Reporters

**Adding New Output Format**:

1. Add format to `OutputFormat` enum in `core/reporter.py`
2. Implement format handler method `_format_<format>()`
3. Register in format_handlers dict
4. Update CLI choices

**Example**:
```python
class OutputFormat(Enum):
    XML = "xml"

class Reporter:
    def _format_xml(self) -> str:
        # Generate XML output
        return xml_string
```

### Custom License Matchers

Extend `LicenseMatcher` for domain-specific matching:

```python
from permitcheck.core.matcher import LicenseMatcher

class CustomMatcher(LicenseMatcher):
    def __init__(self):
        super().__init__(known_licenses)
        self.custom_aliases = {
            'proprietary': 'Commercial',
            'internal': 'Private'
        }
```

---

## Testing Architecture

### Test Organization

```
tests/
├── core/           # Core component tests
├── plugins/        # Plugin-specific tests
├── scripts/        # CLI tool tests
├── license/        # License database tests
└── integration/    # End-to-end tests
```

### Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interaction
- **Plugin Tests**: Mock file systems and package metadata
- **CLI Tests**: Mock sys.argv and capture output

**Coverage Target**: 90%+ (currently at 89%)

---

## Performance Considerations

### Optimization Strategies

1. **Parallel Processing**: ThreadPoolExecutor for concurrent license lookups
2. **Smart Caching**: Avoid repeated metadata parsing
3. **Lazy Loading**: Load plugins only when needed
4. **Regex Compilation**: Pre-compile license patterns

### Benchmarks

**Typical Project (50 dependencies)**:
- First run (cold cache): 5-15 seconds
- Subsequent runs (warm cache): 0.5-2 seconds
- Speedup: 10-30x

**Bottlenecks**:
- README parsing: ~50-200ms per package
- Network requests (npm registry): ~100-500ms per package
- File I/O: ~10-50ms per package

---

## Security Considerations

### SARIF Integration

PermitCheck supports SARIF format for security scanning integration:

```bash
permitcheck -l python --format sarif > results.sarif
```

**Use Cases**:
- GitHub Security scanning
- VS Code Security panel
- CI/CD security gates

### Vulnerability Detection

**Future Enhancement**: Integrate with vulnerability databases (OSV, CVE)

---

## Error Handling Philosophy

### Error Categories

1. **Configuration Errors**: Invalid config, missing fields
2. **Plugin Errors**: Failed to load, missing dependencies
3. **Validation Errors**: License policy violations
4. **Runtime Errors**: Unexpected exceptions

### Error Propagation

```
Exception → Handler → User-friendly message → Exit code
```

**Exit Codes**:
- 0: Success
- 1: Validation errors or runtime errors
- 130: Keyboard interrupt (Ctrl+C)

---

## Future Architecture Plans

### Planned Enhancements

1. **Async Plugin System**: Support async/await for I/O-bound operations
2. **GraphQL API**: Expose validation as a service
3. **Web Dashboard**: Real-time monitoring of project licenses
4. **AI-Powered Matching**: ML model for license detection
5. **Blockchain Integration**: Immutable license verification

### Scalability

**Current Limitations**:
- Single-threaded CLI (mitigated by parallelism)
- No distributed caching
- No batch processing API

**Future Solutions**:
- Redis cache backend
- REST API with queue processing
- Kubernetes operator for CI/CD

---

## Conclusion

PermitCheck's architecture prioritizes:
- ✅ **Modularity**: Plugin system for easy extension
- ✅ **Performance**: Caching and parallel processing
- ✅ **Reliability**: Comprehensive error handling
- ✅ **Extensibility**: Multiple output formats and validators
- ✅ **Developer Experience**: Type hints, clear APIs, good docs

For implementation details, see source code and inline documentation.
