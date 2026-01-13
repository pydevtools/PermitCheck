"""
Example: Go Plugin for PermitCheck

This is a starter template for implementing Go (go.mod) support.
Complete the TODO sections to make it functional.
"""
import os
import re
import subprocess
from typing import Dict, Set, Optional, Tuple

import requests

from permitcheck.plugin import Plugin
from permitcheck.core.cache import LicenseCache
from permitcheck.core.matcher import LicenseMatcher
from permitcheck.utils import get_pwd


class GoPlugin(Plugin):
    """Plugin for Go module dependency license checking."""
    
    def __init__(self):
        """Initialize plugin with cache and matcher."""
        self.cache = LicenseCache()
        self.matcher: Optional[LicenseMatcher] = None
    
    def get_name(self) -> str:
        """Return the plugin name."""
        return "go"
    
    def run(self) -> Optional[Dict[str, Set[str]]]:
        """Discover Go modules and return license information."""
        # Step 1: Discover dependencies from go.mod
        modules = self._discover_modules()
        if not modules:
            print('No go.mod found or no dependencies listed')
            return None
        
        print(f"Found {len(modules)} modules to check...")
        
        # Step 2: Fetch license for each module
        result = {}
        for module in modules:
            licenses = self._get_module_license(module)
            result[module] = licenses
        
        return result
    
    def load_settings(self) -> Optional[Tuple[Set[str], Set[str], Set[str]]]:
        """Load PermitCheck settings from configuration."""
        # TODO: Implement config loading
        return None
    
    def _discover_modules(self) -> Set[str]:
        """Discover modules from go.mod.
        
        Returns:
            Set of module paths (e.g., 'github.com/user/repo')
        """
        modules = set()
        gomod = os.path.join(get_pwd(), 'go.mod')
        
        if not os.path.exists(gomod):
            return modules
        
        # Parse go.mod file
        with open(gomod, 'r') as f:
            content = f.read()
        
        # Pattern: require module_path v1.2.3
        require_pattern = re.compile(r'require\s+([^\s]+)\s+v[\d.]+')
        
        # Single requires
        for match in require_pattern.finditer(content):
            modules.add(match.group(1))
        
        # Require blocks: require ( ... )
        block_pattern = re.compile(r'require\s*\((.*?)\)', re.DOTALL)
        blocks = block_pattern.findall(content)
        for block in blocks:
            for line in block.split('\n'):
                line = line.strip()
                if line and not line.startswith('//'):
                    # Extract module path before version
                    parts = line.split()
                    if len(parts) >= 2:
                        modules.add(parts[0])
        
        return modules
    
    def _get_module_license(self, module_path: str) -> Set[str]:
        """Get license for a specific Go module.
        
        Args:
            module_path: Full module path (e.g., 'github.com/user/repo')
            
        Returns:
            Set of license identifiers
        """
        # Try cache first
        cached = self.cache.get(module_path)
        if cached:
            return cached
        
        # Fetch from source
        licenses = self._fetch_license_from_source(module_path)
        
        # Normalize licenses
        if licenses and self.matcher:
            licenses = self.matcher.normalize_license_set(licenses)
        
        # Cache result
        if licenses:
            self.cache.set(module_path, licenses)
        
        return licenses or {'Unknown'}
    
    def _fetch_license_from_source(self, module_path: str) -> Set[str]:
        """Fetch license for Go module.
        
        Strategy:
        1. Check pkg.go.dev API
        2. Try go list -json command
        3. Look for LICENSE file in $GOPATH/pkg/mod/
        
        Args:
            module_path: Full module path
            
        Returns:
            Set of license strings
        """
        try:
            # Method 1: pkg.go.dev API
            licenses = self._fetch_from_pkggodev(module_path)
            if licenses:
                return licenses
            
            # Method 2: go list command (if module is downloaded)
            licenses = self._fetch_from_golist(module_path)
            if licenses:
                return licenses
            
            # Method 3: Check LICENSE file in module cache
            licenses = self._fetch_from_license_file(module_path)
            if licenses:
                return licenses
            
        except Exception as e:
            print(f"Error fetching license for {module_path}: {e}")
        
        return {'Unknown'}
    
    def _fetch_from_pkggodev(self, module_path: str) -> Set[str]:
        """Fetch license from pkg.go.dev.
        
        Note: pkg.go.dev doesn't have a public API, so this uses web scraping.
        TODO: Implement proper scraping or use alternative API.
        """
        try:
            # This is a placeholder - pkg.go.dev doesn't have a JSON API
            # You could scrape the HTML or use GitHub API for GitHub-hosted modules
            
            if 'github.com' in module_path:
                return self._fetch_from_github(module_path)
            
        except Exception:
            pass
        
        return set()
    
    def _fetch_from_github(self, module_path: str) -> Set[str]:
        """Fetch license from GitHub API for GitHub-hosted modules.
        
        Args:
            module_path: Module path starting with 'github.com'
            
        Returns:
            Set of license strings
        """
        try:
            # Parse: github.com/user/repo/subpackage -> user/repo
            parts = module_path.split('/')
            if len(parts) >= 3:
                owner, repo = parts[1], parts[2]
                
                url = f"https://api.github.com/repos/{owner}/{repo}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'license' in data and data['license']:
                        license_info = data['license']
                        if 'spdx_id' in license_info:
                            spdx = license_info['spdx_id']
                            if spdx != 'NOASSERTION':
                                return {spdx}
        except Exception:
            pass
        
        return set()
    
    def _fetch_from_golist(self, module_path: str) -> Set[str]:
        """Fetch module info using 'go list -json'.
        
        Args:
            module_path: Module path
            
        Returns:
            Set of license strings
        """
        try:
            result = subprocess.run(
                ['go', 'list', '-json', module_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                # Go modules don't include license in 'go list' output
                # But we can get the module directory
                if 'Dir' in data:
                    return self._read_license_file(data['Dir'])
        except Exception:
            pass
        
        return set()
    
    def _fetch_from_license_file(self, module_path: str) -> Set[str]:
        """Find LICENSE file in $GOPATH/pkg/mod/.
        
        Args:
            module_path: Module path
            
        Returns:
            Set of license strings
        """
        try:
            # Get GOPATH
            result = subprocess.run(
                ['go', 'env', 'GOPATH'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                gopath = result.stdout.strip()
                # Module cache is at $GOPATH/pkg/mod/
                # Module path needs to be encoded (@ for version)
                # This is simplified - real implementation needs proper path encoding
                module_dir = os.path.join(gopath, 'pkg', 'mod', module_path)
                if os.path.exists(module_dir):
                    return self._read_license_file(module_dir)
        except Exception:
            pass
        
        return set()
    
    def _read_license_file(self, directory: str) -> Set[str]:
        """Read LICENSE file from directory and detect license type.
        
        Args:
            directory: Path to module directory
            
        Returns:
            Set of license strings
        """
        import glob
        
        license_files = glob.glob(os.path.join(directory, 'LICENSE*'))
        if not license_files:
            license_files = glob.glob(os.path.join(directory, 'COPYING*'))
        
        if license_files:
            try:
                with open(license_files[0], 'r') as f:
                    content = f.read()
                    # Use matcher to identify license from text
                    if self.matcher:
                        return self.matcher.match(content)
            except Exception:
                pass
        
        return set()


# Example usage
if __name__ == '__main__':
    plugin = GoPlugin()
    result = plugin.run()
    if result:
        for module, licenses in result.items():
            print(f"{module}: {', '.join(licenses)}")
