# Adding Language Support

This guide walks you through adding support for a new programming language to PermitCheck.

## Overview

Adding language support involves:
1. Creating a new plugin
2. Implementing dependency discovery
3. Implementing license extraction
4. Adding configuration support
5. Writing tests
6. Updating documentation

**Estimated Time**: 4-8 hours for basic support, more for advanced features

---

## Step 1: Create Plugin File

Create a new file in `permitcheck/plugins/`:

```bash
touch permitcheck/plugins/for_<language>.py
```

**Naming Convention**: Always use `for_<language>.py` format (e.g., `for_java.py`, `for_ruby.py`)

---

## Step 2: Implement Plugin Class

### Basic Template

```python
"""
PermitCheck <Language> plugin - discovers and checks licenses for <Language> dependencies
"""
import os
from typing import Dict, Set, Optional, Tuple

from permitcheck.plugin import Plugin
from permitcheck.license.update import License
from permitcheck.utils import get_pwd, read_toml, exit
from permitcheck.core.cache import LicenseCache
from permitcheck.core.matcher import LicenseMatcher


class LanguagePlugin(Plugin):
    """Plugin for <Language> dependency license checking."""
    
    def __init__(self):
        """Initialize plugin with cache and matcher."""
        self.cache = LicenseCache()
        self.matcher: Optional[LicenseMatcher] = None
    
    def get_name(self) -> str:
        """Return the plugin name/language identifier."""
        return "<language>"  # lowercase: python, java, ruby, go, etc.
    
    def run(self) -> Optional[Dict[str, Set[str]]]:
        """Discover dependencies and return license information.
        
        Returns:
            Dict mapping package names to sets of license identifiers
            Example: {'package-name': {'MIT', 'Apache-2.0'}}
        """
        # Step 1: Discover dependencies
        deps = self._discover_dependencies()
        if not deps:
            print('No dependencies found in this directory')
            exit()
        
        # Step 2: For each dependency, fetch license info
        result = {}
        for dep in deps:
            licenses = self._get_package_license(dep)
            result[dep] = licenses
        
        return result
    
    def load_settings(self) -> Optional[Tuple[Set[str], Set[str], Set[str]]]:
        """Load PermitCheck settings from configuration.
        
        Returns:
            Tuple of (allowed_licenses, trigger_error_licenses, skip_libraries)
        """
        # Try to load from configuration file
        # This can be language-specific or use the global permitcheck config
        return None  # Returns None if no config found
    
    def _discover_dependencies(self) -> Set[str]:
        """Discover project dependencies.
        
        This is language-specific and should parse:
        - Manifest files (package.json, Gemfile, go.mod, pom.xml, etc.)
        - Lock files for exact versions
        - Build tool outputs
        
        Returns:
            Set of package names
        """
        raise NotImplementedError("Implement dependency discovery")
    
    def _get_package_license(self, package_name: str) -> Set[str]:
        """Get license(s) for a specific package.
        
        Args:
            package_name: Name of the package
            
        Returns:
            Set of license identifiers (SPDX preferred)
        """
        # Try cache first
        cached = self.cache.get(package_name)
        if cached:
            return cached
        
        # Fetch from package metadata/registry
        licenses = self._fetch_license_from_source(package_name)
        
        # Normalize using matcher
        if licenses and self.matcher:
            licenses = self.matcher.normalize_license_set(licenses)
        
        # Cache for future use
        if licenses:
            self.cache.set(package_name, licenses)
        
        return licenses or {'Unknown'}
    
    def _fetch_license_from_source(self, package_name: str) -> Set[str]:
        """Fetch license from package source/registry.
        
        This is where you implement language-specific logic:
        - Query package registry API (npm, RubyGems, Maven Central, etc.)
        - Parse package metadata files
        - Read LICENSE files from installed packages
        - Parse README files
        
        Args:
            package_name: Name of the package
            
        Returns:
            Set of raw license strings (before normalization)
        """
        raise NotImplementedError("Implement license fetching")
```

---

## Step 3: Implement Dependency Discovery

### Python Example (requirements.txt)

```python
def _discover_dependencies(self) -> Set[str]:
    """Discover dependencies from requirements.txt."""
    deps = set()
    req_file = os.path.join(get_pwd(), 'requirements.txt')
    
    if not os.path.exists(req_file):
        return deps
    
    with open(req_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Parse package name (remove version specifiers)
            pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0]
            deps.add(pkg_name.strip())
    
    return deps
```

### Java Example (pom.xml)

```python
import xml.etree.ElementTree as ET

def _discover_dependencies(self) -> Set[str]:
    """Discover dependencies from Maven pom.xml."""
    deps = set()
    pom_file = os.path.join(get_pwd(), 'pom.xml')
    
    if not os.path.exists(pom_file):
        return deps
    
    tree = ET.parse(pom_file)
    root = tree.getroot()
    
    # Maven uses XML namespaces
    ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
    
    for dep in root.findall('.//m:dependency', ns):
        group_id = dep.find('m:groupId', ns)
        artifact_id = dep.find('m:artifactId', ns)
        if group_id is not None and artifact_id is not None:
            # Maven packages are identified by groupId:artifactId
            pkg_name = f"{group_id.text}:{artifact_id.text}"
            deps.add(pkg_name)
    
    return deps
```

### Ruby Example (Gemfile)

```python
def _discover_dependencies(self) -> Set[str]:
    """Discover dependencies from Gemfile."""
    deps = set()
    gemfile = os.path.join(get_pwd(), 'Gemfile')
    
    if not os.path.exists(gemfile):
        return deps
    
    import re
    gem_pattern = re.compile(r"gem\s+['\"]([^'\"]+)['\"]")
    
    with open(gemfile, 'r') as f:
        for line in f:
            match = gem_pattern.search(line)
            if match:
                deps.add(match.group(1))
    
    return deps
```

### Go Example (go.mod)

```python
def _discover_dependencies(self) -> Set[str]:
    """Discover dependencies from go.mod."""
    deps = set()
    gomod = os.path.join(get_pwd(), 'go.mod')
    
    if not os.path.exists(gomod):
        return deps
    
    import re
    require_pattern = re.compile(r'require\s+([^\s]+)\s+v')
    
    with open(gomod, 'r') as f:
        content = f.read()
        # Find all requires
        for match in require_pattern.finditer(content):
            deps.add(match.group(1))
    
    return deps
```

---

## Step 4: Implement License Extraction

### Strategy 1: API Query

Most package registries have APIs:

```python
import requests

def _fetch_license_from_source(self, package_name: str) -> Set[str]:
    """Fetch license from npm registry."""
    try:
        url = f"https://registry.npmjs.org/{package_name}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            license_info = data.get('license', 'Unknown')
            return {license_info}
    except Exception as e:
        print(f"Error fetching license for {package_name}: {e}")
    
    return {'Unknown'}
```

### Strategy 2: Local Metadata

For installed packages:

```python
def _fetch_license_from_source(self, package_name: str) -> Set[str]:
    """Fetch license from installed gem metadata."""
    try:
        # Run gem specification command
        import subprocess
        result = subprocess.run(
            ['gem', 'specification', package_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse YAML output
            import yaml
            spec = yaml.safe_load(result.stdout)
            if 'licenses' in spec:
                return set(spec['licenses'])
    except Exception as e:
        print(f"Error reading gem spec for {package_name}: {e}")
    
    return {'Unknown'}
```

### Strategy 3: File Parsing

Read LICENSE files from package installation:

```python
import glob

def _fetch_license_from_source(self, package_name: str) -> Set[str]:
    """Find LICENSE file in package directory."""
    # Typical locations vary by language
    possible_locations = [
        f"/usr/local/lib/<language>/site-packages/{package_name}",
        f"./vendor/{package_name}",
        f"./node_modules/{package_name}"
    ]
    
    for location in possible_locations:
        license_files = glob.glob(f"{location}/LICENSE*")
        if license_files:
            with open(license_files[0], 'r') as f:
                content = f.read()
                # Use matcher to identify license from text
                if self.matcher:
                    return self.matcher.match(content)
    
    return {'Unknown'}
```

---

## Step 5: Add Configuration Support

### Option A: Reuse Global Config

```python
def load_settings(self) -> Optional[Tuple[Set[str], Set[str], Set[str]]]:
    """Load from permitcheck.yaml or pyproject.toml."""
    from permitcheck.core.config import ConfigManager
    
    config_manager = ConfigManager()
    policy = config_manager.load_policy()
    
    if policy:
        return (
            policy.allowed,
            policy.trigger_error,
            policy.skip_libraries
        )
    return None
```

### Option B: Language-Specific Config

```python
def load_settings(self) -> Optional[Tuple[Set[str], Set[str], Set[str]]]:
    """Load from language-specific config file."""
    config_file = os.path.join(get_pwd(), '<language>-license-config.yaml')
    
    if not os.path.exists(config_file):
        return None
    
    import yaml
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        return (
            set(config.get('allowed', [])),
            set(config.get('trigger_error', [])),
            set(config.get('skip_libraries', []))
        )
```

---

## Step 6: Write Tests

Create `tests/plugins/test_for_<language>.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from permitcheck.plugins.for_<language> import LanguagePlugin


class TestLanguagePlugin:
    """Test <Language> plugin functionality."""
    
    def test_get_name(self):
        """Test plugin returns correct name."""
        plugin = LanguagePlugin()
        assert plugin.get_name() == "<language>"
    
    @patch('os.path.exists')
    @patch('builtins.open', create=True)
    def test_discover_dependencies(self, mock_open, mock_exists):
        """Test dependency discovery from manifest file."""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = """
        # Sample manifest file content
        dependency-1
        dependency-2
        """
        
        plugin = LanguagePlugin()
        deps = plugin._discover_dependencies()
        
        assert 'dependency-1' in deps
        assert 'dependency-2' in deps
    
    @patch('requests.get')
    def test_fetch_license_from_api(self, mock_get):
        """Test license fetching from package registry."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'license': 'MIT'}
        mock_get.return_value = mock_response
        
        plugin = LanguagePlugin()
        licenses = plugin._fetch_license_from_source('test-package')
        
        assert 'MIT' in licenses
    
    def test_run_returns_dict(self):
        """Test run() returns proper format."""
        plugin = LanguagePlugin()
        
        with patch.object(plugin, '_discover_dependencies', return_value={'pkg1'}):
            with patch.object(plugin, '_get_package_license', return_value={'MIT'}):
                result = plugin.run()
                
                assert isinstance(result, dict)
                assert 'pkg1' in result
                assert 'MIT' in result['pkg1']
```

Run tests:
```bash
pytest tests/plugins/test_for_<language>.py -v
```

---

## Step 7: Update CLI Tool

Add your language to the CLI choices in `permitcheck/scripts/permitcheck_tool.py`:

```python
parser.add_argument(
    '-l', '--lang',
    choices=['python', 'npm', '<language>'],  # Add your language here
    nargs='+',
    metavar='LANG',
    help='Languages to check: python, npm, <language>'
)
```

---

## Step 8: Test End-to-End

Create a sample project with dependencies:

```bash
# Create test directory
mkdir test_<language>_project
cd test_<language>_project

# Create manifest file with dependencies
# (language-specific: requirements.txt, package.json, Gemfile, etc.)

# Run permitcheck
permitcheck -l <language>
```

---

## Step 9: Documentation

Update documentation:

1. **README.md**: Add language to supported languages list
2. **docs/api-reference.md**: Add plugin API documentation
3. **docs/configuration.md**: Add language-specific config examples
4. **CHANGELOG.md**: Add entry for new language support

---

## Best Practices

### Performance

- **Use caching**: Always cache license lookups
- **Parallel processing**: Use ThreadPoolExecutor for multiple packages
- **Lazy loading**: Don't fetch data until needed
- **Timeout requests**: Set reasonable timeouts for network calls

### Error Handling

```python
def _fetch_license_from_source(self, package_name: str) -> Set[str]:
    """Fetch with proper error handling."""
    try:
        # Your implementation
        return licenses
    except requests.RequestException as e:
        print(f"Network error fetching {package_name}: {e}")
        return {'Unknown'}
    except Exception as e:
        print(f"Error processing {package_name}: {e}")
        return {'Unknown'}
```

### License Normalization

Always use SPDX identifiers when possible:

```python
# Good
return {'Apache-2.0', 'MIT'}

# Bad
return {'Apache License 2.0', 'MIT License'}
```

Use the `LicenseMatcher` to normalize:

```python
raw_licenses = {'apache 2', 'mit license'}
normalized = self.matcher.normalize_license_set(raw_licenses)
# Returns: {'Apache-2.0', 'MIT'}
```

---

## Language-Specific Resources

### Package Registries & APIs

- **Python**: PyPI API - https://pypi.org/pypi/{package}/json
- **JavaScript/Node**: npm Registry - https://registry.npmjs.org/{package}
- **Ruby**: RubyGems API - https://rubygems.org/api/v1/gems/{gem}.json
- **Java**: Maven Central - https://search.maven.org/solrsearch/select?q=a:{artifact}
- **Go**: Go Packages - https://pkg.go.dev/{package}
- **Rust**: crates.io API - https://crates.io/api/v1/crates/{crate}
- **PHP**: Packagist API - https://packagist.org/packages/{vendor}/{package}.json

### Manifest Files

- **Python**: requirements.txt, pyproject.toml, Pipfile
- **JavaScript**: package.json, package-lock.json, yarn.lock
- **Ruby**: Gemfile, Gemfile.lock
- **Java**: pom.xml (Maven), build.gradle (Gradle)
- **Go**: go.mod, go.sum
- **Rust**: Cargo.toml, Cargo.lock
- **PHP**: composer.json, composer.lock

---

## Example: Complete Ruby Plugin

See `examples/for_ruby.py` (if available) for a complete, working example.

---

## Common Pitfalls

1. **Not handling missing files**: Always check if manifest files exist
2. **Ignoring versions**: Some APIs require version numbers
3. **Hardcoded paths**: Use `get_pwd()` for current directory
4. **No timeout on network calls**: Always set timeouts
5. **Not normalizing licenses**: Use LicenseMatcher for consistency
6. **Forgetting to cache**: Cache expensive operations

---

## Getting Help

- Open a discussion: https://github.com/kirankotari/permitcheck/discussions
- Check existing plugins: `permitcheck/plugins/for_python.py`
- Ask in issues: https://github.com/kirankotari/permitcheck/issues

---

## Checklist

Before submitting your plugin:

- [ ] Plugin file created in `permitcheck/plugins/for_<language>.py`
- [ ] Implements all three abstract methods (get_name, run, load_settings)
- [ ] Dependency discovery works for common manifest files
- [ ] License extraction handles multiple sources
- [ ] Uses caching for performance
- [ ] Error handling for network/file errors
- [ ] Tests written with >80% coverage
- [ ] CLI updated with new language choice
- [ ] Documentation updated
- [ ] End-to-end tested with real project
- [ ] Code follows style guide (ruff/black compliant)

---

## Next Steps

After implementing basic support:

1. **Add advanced features**:
   - Lock file parsing for exact versions
   - Transitive dependency resolution
   - Multiple manifest file support
   
2. **Optimize performance**:
   - Batch API requests
   - Parallel processing
   - Better caching strategies

3. **Enhance detection**:
   - Multiple license sources
   - README parsing
   - LICENSE file scanning

Good luck building your plugin! 🚀
