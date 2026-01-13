"""
Example: Ruby Plugin for PermitCheck

This is a starter template for implementing Ruby (Gemfile) support.
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


class RubyPlugin(Plugin):
    """Plugin for Ruby gem dependency license checking."""
    
    def __init__(self):
        """Initialize plugin with cache and matcher."""
        self.cache = LicenseCache()
        self.matcher: Optional[LicenseMatcher] = None
    
    def get_name(self) -> str:
        """Return the plugin name."""
        return "ruby"
    
    def run(self) -> Optional[Dict[str, Set[str]]]:
        """Discover Ruby gems and return license information."""
        # Step 1: Discover dependencies from Gemfile
        gems = self._discover_gems()
        if not gems:
            print('No Gemfile found or no gems listed')
            return None
        
        print(f"Found {len(gems)} gems to check...")
        
        # Step 2: Fetch license for each gem
        result = {}
        for gem in gems:
            licenses = self._get_gem_license(gem)
            result[gem] = licenses
        
        return result
    
    def load_settings(self) -> Optional[Tuple[Set[str], Set[str], Set[str]]]:
        """Load PermitCheck settings from configuration."""
        # TODO: Implement config loading from permitcheck.yaml or custom Ruby config
        # For now, return None to use global defaults
        return None
    
    def _discover_gems(self) -> Set[str]:
        """Discover gems from Gemfile.
        
        Returns:
            Set of gem names
        """
        gems = set()
        gemfile = os.path.join(get_pwd(), 'Gemfile')
        
        if not os.path.exists(gemfile):
            return gems
        
        # Parse Gemfile for gem declarations
        gem_pattern = re.compile(r"gem\s+['\"]([^'\"]+)['\"]")
        
        with open(gemfile, 'r') as f:
            for line in f:
                # Skip comments and blank lines
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Extract gem name
                match = gem_pattern.search(line)
                if match:
                    gems.add(match.group(1))
        
        return gems
    
    def _get_gem_license(self, gem_name: str) -> Set[str]:
        """Get license for a specific gem.
        
        Args:
            gem_name: Name of the gem
            
        Returns:
            Set of license identifiers
        """
        # Try cache first
        cached = self.cache.get(gem_name)
        if cached:
            return cached
        
        # Fetch from source
        licenses = self._fetch_license_from_rubygems(gem_name)
        
        # Normalize licenses
        if licenses and self.matcher:
            licenses = self.matcher.normalize_license_set(licenses)
        
        # Cache result
        if licenses:
            self.cache.set(gem_name, licenses)
        
        return licenses or {'Unknown'}
    
    def _fetch_license_from_rubygems(self, gem_name: str) -> Set[str]:
        """Fetch license from RubyGems.org API.
        
        Args:
            gem_name: Name of the gem
            
        Returns:
            Set of license strings
        """
        try:
            # Method 1: RubyGems.org API
            url = f"https://rubygems.org/api/v1/gems/{gem_name}.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check 'licenses' field (array)
                if 'licenses' in data and data['licenses']:
                    return set(data['licenses'])
                
                # Fallback: check 'license' field (string)
                if 'license' in data and data['license']:
                    return {data['license']}
            
            # Method 2: Try gem specification command (if gem is installed)
            licenses = self._fetch_from_gem_spec(gem_name)
            if licenses:
                return licenses
            
        except requests.RequestException as e:
            print(f"Network error fetching license for {gem_name}: {e}")
        except Exception as e:
            print(f"Error fetching license for {gem_name}: {e}")
        
        return {'Unknown'}
    
    def _fetch_from_gem_spec(self, gem_name: str) -> Set[str]:
        """Fetch license from local gem specification.
        
        Args:
            gem_name: Name of the gem
            
        Returns:
            Set of license strings
        """
        try:
            # Run: gem specification <gem> licenses
            result = subprocess.run(
                ['gem', 'specification', gem_name, 'licenses'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse output (typically YAML array format)
                import yaml
                licenses = yaml.safe_load(result.stdout)
                if isinstance(licenses, list):
                    return set(licenses)
                elif isinstance(licenses, str):
                    return {licenses}
        except Exception:
            pass  # Silently fail if gem not installed or command fails
        
        return set()


# Example usage
if __name__ == '__main__':
    plugin = RubyPlugin()
    result = plugin.run()
    if result:
        for gem, licenses in result.items():
            print(f"{gem}: {', '.join(licenses)}")
