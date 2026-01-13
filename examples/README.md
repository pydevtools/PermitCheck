# Example Plugin Implementations

This directory contains example plugin implementations for various programming languages that are not yet fully supported in PermitCheck.

## Available Examples

### 1. Ruby Plugin (`for_ruby.py`)
- **Status**: ~80% complete, needs testing
- **Features**:
  - Parses `Gemfile` for dependencies
  - Fetches licenses from RubyGems.org API
  - Fallback to `gem specification` command
- **Usage**: Copy to `permitcheck/plugins/` and test with a Ruby project

### 2. Go Plugin (`for_go.py`)
- **Status**: ~70% complete, needs additional work
- **Features**:
  - Parses `go.mod` for module dependencies
  - GitHub API integration for GitHub-hosted modules
  - LICENSE file detection in module cache
- **Challenges**: No unified Go package registry API, requires multiple strategies

### 3. Java Plugin (`for_java.py`)
- **Status**: ~75% complete for Maven, Gradle stubbed out
- **Features**:
  - Parses Maven `pom.xml` files
  - Fetches licenses from Maven Central
  - Downloads and parses artifact POM files
- **TODO**: Gradle support (build.gradle parsing)

## How to Use These Examples

### Testing an Example Plugin

1. **Copy to plugins directory**:
```bash
cp examples/for_ruby.py permitcheck/plugins/
```

2. **Update CLI tool** to include new language in `permitcheck/scripts/permitcheck_tool.py`:
```python
parser.add_argument(
    '-l', '--lang',
    choices=['python', 'npm', 'ruby'],  # Add your language
    # ...
)
```

3. **Test with sample project**:
```bash
# Create test project
mkdir test_ruby_project
cd test_ruby_project

# Create Gemfile
cat > Gemfile << EOF
source 'https://rubygems.org'
gem 'rails'
gem 'rspec'
EOF

# Run PermitCheck
permitcheck -l ruby
```

### Customizing for Your Needs

Each plugin can be customized by modifying:

1. **Dependency Discovery**: Update `_discover_*()` method to parse your manifest format
2. **License Fetching**: Update `_fetch_license_from_*()` to query your package registry
3. **Configuration**: Implement `load_settings()` for language-specific config

## Implementation Checklist

When adapting these examples:

- [ ] Test dependency discovery with real projects
- [ ] Verify license fetching works for common packages
- [ ] Add error handling for edge cases
- [ ] Write unit tests (see `tests/plugins/test_for_python.py`)
- [ ] Add integration tests
- [ ] Update documentation
- [ ] Submit PR with your enhancements!

## Package Registry APIs

Here are the official APIs for major package registries:

| Language | Registry | API Documentation |
|----------|----------|-------------------|
| Ruby | RubyGems | https://guides.rubygems.org/rubygems-org-api/ |
| Go | pkg.go.dev | No official API (use GitHub API for GitHub repos) |
| Java | Maven Central | https://search.maven.org/classic/#api |
| Rust | crates.io | https://crates.io/data-access |
| PHP | Packagist | https://packagist.org/apidoc |
| C# | NuGet | https://docs.microsoft.com/nuget/api/overview |

## Common Patterns

### Pattern 1: API Query
Most registries provide JSON APIs:
```python
response = requests.get(f"{API_URL}/{package_name}")
data = response.json()
license = data.get('license')
```

### Pattern 2: CLI Tool Integration
Use existing package manager tools:
```python
result = subprocess.run(['gem', 'specification', package], 
                       capture_output=True)
# Parse result.stdout
```

### Pattern 3: LICENSE File Parsing
Read LICENSE files from installed packages:
```python
license_files = glob.glob(f"{package_dir}/LICENSE*")
content = open(license_files[0]).read()
licenses = self.matcher.match(content)  # Use fuzzy matching
```

## Contributing Your Plugin

Once your plugin works well:

1. **Polish the code**:
   - Add comprehensive docstrings
   - Handle edge cases
   - Add type hints
   - Follow code style (run `ruff format`)

2. **Write tests**:
   - Unit tests for each method
   - Mock external API calls
   - Test error conditions

3. **Update docs**:
   - Add to README.md supported languages
   - Document any special requirements
   - Add usage examples

4. **Submit PR**:
   - Follow [CONTRIBUTING.md](../docs/CONTRIBUTING.md)
   - Include test results
   - Describe what works and what doesn't

## Questions?

- Open a discussion: https://github.com/kirankotari/permitcheck/discussions
- Check existing issues: https://github.com/kirankotari/permitcheck/issues
- Read the guide: [docs/adding-language-support.md](../docs/adding-language-support.md)

Happy plugin development! 🚀
