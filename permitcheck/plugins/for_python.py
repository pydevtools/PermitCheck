"""
PermitCheck python locates 3rd party libraries used and returns name and metadata
"""
import os
import re
from importlib.metadata import distributions
from typing import Dict, Set, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from permitcheck.plugin import Plugin
from permitcheck.license.update import License
from permitcheck.utils import get_pwd, get_lines, get_matching_keys, read_toml, flatten_set, exit
from permitcheck.core.cache import LicenseCache
from permitcheck.core.matcher import LicenseMatcher


class PythonPlugin(Plugin):
    def __init__(self):
        """Initialize plugin with cache and matcher."""
        self.cache = LicenseCache()
        self.matcher: Optional[LicenseMatcher] = None
    
    def get_name(self) -> str:
        return "python"

    def run(self) -> Optional[Dict[str, Set[str]]]:
        """Discover dependencies and return license information with parallel processing."""
        deps = self._extracted_from(Toml) or self._extracted_from(Requirements)
        if not deps:
            print('no dependencies found in this directory')
            exit()

        Expand.map_dependencies_by_package()
        deps = Expand.get_dependencies(deps)
        deps = deps - Expand.not_installed
        
        pylic = PythonLicense()
        
        # Parallel license fetching
        result = {}
        with ThreadPoolExecutor(max_workers=min(10, len(deps))) as executor:
            future_to_dep = {
                executor.submit(pylic.get_package_license, dep): dep 
                for dep in deps
            }
            
            for future in as_completed(future_to_dep):
                dep = future_to_dep[future]
                try:
                    licenses = future.result()
                    result[dep] = licenses
                except Exception as e:
                    print(f"Error fetching license for {dep}: {e}")
                    result[dep] = pylic.unknown
        
        return result


    def _extracted_from(self, cls) -> Optional[Set[str]]:
        cls.get_dependencies()
        return cls.to_set()

    def load_settings(self) -> Optional[Tuple[Set[str], Set[str], Set[str]]]:
        config = Toml.read()
        if 'licenses' not in config:
            return None
        config = config['licenses']
        allowed_licenses = set(config.get('allowed') or [])
        trigger_error_licenses = set(config.get('trigger_error') or [])
        skip_libraries = set(config.get('skip_libraries') or [])
        return (allowed_licenses, trigger_error_licenses, skip_libraries)


class PythonLicense(License):
    unknown: Set[str] = {'Unknown'}
    
    def __init__(self) -> None:
        super().__init__()
        self.spdx_set: Set[str] = super().get(is_print=False)
        # Initialize matcher with SPDX licenses
        self.matcher = LicenseMatcher(self.spdx_set, fuzzy_threshold=0.85)
        # Initialize cache
        self.cache = LicenseCache()

    def set_to_string(self, value_set: Set[str]) -> str:
        return next(iter(value_set)) if len(value_set) == 1 else str(value_set)

    def get_package_license(self, pkg_name: str) -> Set[str]:
        """Get licenses for a package from various metadata sources with caching."""
        # Try cache first
        cached = self.cache.get(pkg_name)
        if cached:
            return cached
        
        try:
            dist = next(d for d in distributions() if d.metadata['Name'].lower() == pkg_name.lower())

            # Try different metadata sources in order of preference with confidence tracking
            pkg_licenses = (
                self._get_license_from_metadata(dist, 'License') or
                self._get_license_from_metadata(dist, 'License-Expression') or
                self._get_license_from_classifiers(dist) or
                self._get_license_from_files(dist, 'LICENSE') or
                self._get_license_from_files(dist, 'LICENSE.txt') or
                self._get_license_from_files(dist, 'LICENSE.md') or
                self._get_license_from_files(dist, 'COPYING') or
                self._get_license_from_readme(dist)
            )
            
            if pkg_licenses and len(pkg_licenses) < 3:
                # Normalize licenses using matcher
                normalized = self.matcher.normalize_license_set(pkg_licenses)
                # Cache the result
                self.cache.set(pkg_name, normalized)
                return normalized

        except StopIteration:
            print(f"Package '{pkg_name}' not found.")
            return self.unknown

        return self.unknown

    # Helper function to retrieve license from metadata fields
    def _get_license_from_metadata(self, dist, field_name):
        """Extract license from metadata field."""
        pkg_licenses = set()
        license_content = dist.metadata.get(field_name, '').strip()
        pkg_licenses |= self._validate_license(license_content)
        return pkg_licenses

    # Helper function to check classifiers for licenses
    def _get_license_from_classifiers(self, dist):
        """Extract license from package classifiers."""
        classifiers = dist.metadata.get_all('Classifier', [])
        pkg_licenses = set()
        for line in classifiers:
            if 'license' not in line.lower():
                continue
            pkg_licenses |= self._validate_license(line)
        return pkg_licenses


    # Helper function to check LICENSE files in the distribution
    def _get_license_from_files(self, dist, filename='LICENSE'):
        """Extract license from LICENSE files in package."""
        pkg_licenses = set()
        try:
            for each in dist.files or []:
                if filename.upper() in each.name.upper():
                    try:
                        license_content = each.read_text()
                        pkg_licenses |= self._validate_license(license_content)
                        if pkg_licenses:
                            return pkg_licenses
                    except Exception:
                        pass
        except Exception:
            pass
        return pkg_licenses
    
    def _find_readme_file(self, dist):
        """Find README file in distribution."""
        readme_patterns = ['README', 'README.md', 'README.rst', 'README.txt']
        try:
            for file in dist.files or []:
                if any(pattern in file.name.upper() for pattern in readme_patterns):
                    return file
        except Exception:
            pass
        return None
    
    def _get_license_patterns(self):
        """Return regex patterns for finding licenses in README."""
        return [
            r'##?\s*License\s*\n\s*([A-Za-z0-9\-\.\s]+)',
            r'License:\s*([A-Za-z0-9\-\.\s]+)',
            r'Licensed under\s+(?:the\s+)?([A-Za-z0-9\-\.\s]+)',
            r'\*\*License\*\*:\s*([A-Za-z0-9\-\.\s]+)',
        ]
    
    def _extract_licenses_from_text(self, content):
        """Extract licenses from README text using regex patterns."""
        pkg_licenses = set()
        for pattern in self._get_license_patterns():
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                pkg_licenses |= self._validate_license(match.strip())
                if pkg_licenses:
                    return pkg_licenses
        return pkg_licenses
    
    def _get_license_from_readme(self, dist):
        """Extract license from README files."""
        readme_file = self._find_readme_file(dist)
        if not readme_file:
            return set()
        
        try:
            content = readme_file.read_text()
            return self._extract_licenses_from_text(content)
        except Exception:
            return set()
    
    def _validate_license(self, license_content):
        """Validate and extract known licenses from content using matcher."""
        # Use the matcher to find licenses in content
        if hasattr(self, 'matcher') and self.matcher:
            return self.matcher.match(license_content)
        
        # Fallback to simple string matching
        found_licenses = {
            lic_name for lic_name in self.spdx_set 
            if lic_name in license_content
        }
        return found_licenses if found_licenses else set()


class Expand:
    dep_map = {}
    visited, not_installed = set(), set()

    dep_pattern = re.compile(r"([a-zA-Z0-9\-_]+)")

    @classmethod
    def get_dependencies(cls, pkgs_set):
        """
        Recursively get all dependencies (including dependencies of dependencies).
        """
        dependencies = set()

        for pkg_name in pkgs_set:
            if pkg_name in cls.visited:
                continue
            cls.visited.add(pkg_name)

            if pkg_name.lower() not in cls.dep_map:
                cls.not_installed.add(pkg_name)
                continue

            direct_deps = cls.dep_map.get(pkg_name, set())
            dependencies |= direct_deps

            # Recursively find dependencies for each direct dependency
            for dep in direct_deps:
                dependencies |= cls.get_dependencies({dep})

        dependencies |= pkgs_set
        return dependencies

    @classmethod
    def map_dependencies_by_package(cls):
        """
        Maps each package to its direct dependencies.
        """

        for dist in distributions():
            dist_name = dist.metadata.get('Name').lower()
            if dist.requires:
                cls.dep_map[dist_name] = {cls.dep_pattern.match(dep).group(1) for dep in dist.requires}
            else:
                cls.dep_map[dist_name] = set()  # No dependencies


class Toml:
    basedir = get_pwd()
    file = 'pyproject.toml'
    config = None
    dependencies = {}

    @classmethod
    def read(cls, fpath=None):
        if not fpath:
            fpath = f"{cls.basedir}/{cls.file}"
        # print(fpath)
        cls.config = read_toml(fpath)
        return cls.config

    @classmethod
    def get_dependencies(cls, fpath=None):
        """Extract dependencies from pyproject.toml file."""
        if not cls.config:
            cls.read(fpath)

        cls._extract_poetry_dependencies()
        cls._extract_setuptools_dependencies()
        
        return cls.dependencies

    @classmethod
    def _extract_poetry_dependencies(cls):
        """Extract Poetry dependencies from config."""
        if 'tool' not in cls.config or 'poetry' not in cls.config['tool']:
            return
        
        poetry = cls.config['tool']['poetry']
        
        # Extract main and dev dependencies
        for matched_key in get_matching_keys('dependencies', list(poetry.keys())):
            deps = poetry[matched_key].copy()
            # Remove Python version requirement
            deps.pop('python', None)
            cls.dependencies[matched_key] = list(deps.keys())
        
        # Extract dependency groups
        if 'group' in poetry:
            for group, group_deps in poetry['group'].items():
                if 'dependencies' in group_deps:
                    cls.dependencies[group] = list(group_deps['dependencies'].keys())

    @classmethod
    def _extract_setuptools_dependencies(cls):
        """Extract Setuptools dependencies from config."""
        if 'project' not in cls.config or 'dependencies' not in cls.config['project']:
            return
        
        cls.dependencies['setuptools'] = [
            cls._clean_version_specifier(dep)
            for dep in cls.config['project']['dependencies']
        ]
    
    @classmethod
    def _clean_version_specifier(cls, dep_string):
        """Remove version specifiers from dependency string."""
        # Remove parenthesized version specs (e.g., "package (>=1.0,<2.0)")
        if '(' in dep_string:
            return dep_string.split('(')[0].strip()
        
        # Handle inline version specs (e.g., "package>=1.0")
        for separator in ['>=', '==', '<=', '~=', '!=', '<', '>']:
            if separator in dep_string:
                return dep_string.split(separator)[0].strip()
        return dep_string.strip()

    @classmethod
    def to_set(cls, deps:dict=None):
        return flatten_set(cls.dependencies) if not deps and cls.dependencies else deps

class Requirements:
    basedir = get_pwd()
    dependencies = {}

    @classmethod
    def clean_line(cls, line):
        # Check if the line starts with a comment (ignoring leading whitespace)
        if re.match(r'^\s*#', line):
            return None
        if line := line.split('#')[0].strip():
            # Remove any conditions (e.g., version specifiers like >=, <=, ==)
            return line.split('>=')[0].split('<=')[0].split('==')[0].strip()
        return None

    @classmethod
    def get_dependencies(cls):
        # List all files in the current working directory
        for filename in os.listdir(cls.basedir):
            # Check if the file contains 'req' or 'dep' and has a .txt extension
            if (('req' in filename or 'dep' in filename) and filename.endswith('.txt')):
                filepath = f"{cls.basedir}/{filename}"
                # Read the contents of the file and store in the dictionary
                deps = set()
                for line in get_lines(filepath):
                    if cleaned := cls.clean_line(line):
                        deps.add(cleaned)
                cls.dependencies[filename] = deps
        return cls.dependencies

    @classmethod
    def to_set(cls, deps:dict=None):
        return flatten_set(cls.dependencies) if not deps and cls.dependencies else deps


if __name__ == "__main__":
    Toml.get_dependencies()
    deps = Toml.to_set()
    print(deps)
    deps = Expand.get_dependencies(deps)
    print(deps)

