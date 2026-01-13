"""
Example: Java Plugin for PermitCheck (Maven)

This is a starter template for implementing Java (Maven pom.xml) support.
Complete the TODO sections to make it functional.
"""
import os
import xml.etree.ElementTree as ET
from typing import Dict, Set, Optional, Tuple

import requests

from permitcheck.plugin import Plugin
from permitcheck.core.cache import LicenseCache
from permitcheck.core.matcher import LicenseMatcher
from permitcheck.utils import get_pwd


class JavaPlugin(Plugin):
    """Plugin for Java (Maven) dependency license checking."""
    
    def __init__(self):
        """Initialize plugin with cache and matcher."""
        self.cache = LicenseCache()
        self.matcher: Optional[LicenseMatcher] = None
        self.maven_ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
    
    def get_name(self) -> str:
        """Return the plugin name."""
        return "java"
    
    def run(self) -> Optional[Dict[str, Set[str]]]:
        """Discover Maven dependencies and return license information."""
        # Step 1: Discover dependencies from pom.xml
        dependencies = self._discover_dependencies()
        if not dependencies:
            print('No pom.xml found or no dependencies listed')
            return None
        
        print(f"Found {len(dependencies)} dependencies to check...")
        
        # Step 2: Fetch license for each dependency
        result = {}
        for dep in dependencies:
            licenses = self._get_dependency_license(dep)
            result[dep] = licenses
        
        return result
    
    def load_settings(self) -> Optional[Tuple[Set[str], Set[str], Set[str]]]:
        """Load PermitCheck settings from configuration."""
        # TODO: Implement config loading
        return None
    
    def _discover_dependencies(self) -> Set[str]:
        """Discover dependencies from pom.xml.
        
        Returns:
            Set of artifact coordinates (groupId:artifactId)
        """
        dependencies = set()
        pom_file = os.path.join(get_pwd(), 'pom.xml')
        
        if not os.path.exists(pom_file):
            return dependencies
        
        try:
            tree = ET.parse(pom_file)
            root = tree.getroot()
            
            # Find all <dependency> elements
            for dep in root.findall('.//m:dependency', self.maven_ns):
                group_id = dep.find('m:groupId', self.maven_ns)
                artifact_id = dep.find('m:artifactId', self.maven_ns)
                
                if group_id is not None and artifact_id is not None:
                    # Use groupId:artifactId as identifier
                    coord = f"{group_id.text}:{artifact_id.text}"
                    dependencies.add(coord)
        
        except ET.ParseError as e:
            print(f"Error parsing pom.xml: {e}")
        
        return dependencies
    
    def _get_dependency_license(self, coordinate: str) -> Set[str]:
        """Get license for a Maven dependency.
        
        Args:
            coordinate: Maven coordinate (groupId:artifactId)
            
        Returns:
            Set of license identifiers
        """
        # Try cache first
        cached = self.cache.get(coordinate)
        if cached:
            return cached
        
        # Fetch from Maven Central
        licenses = self._fetch_license_from_maven_central(coordinate)
        
        # Normalize licenses
        if licenses and self.matcher:
            licenses = self.matcher.normalize_license_set(licenses)
        
        # Cache result
        if licenses:
            self.cache.set(coordinate, licenses)
        
        return licenses or {'Unknown'}
    
    def _fetch_license_from_maven_central(self, coordinate: str) -> Set[str]:
        """Fetch license from Maven Central.
        
        Args:
            coordinate: Maven coordinate (groupId:artifactId)
            
        Returns:
            Set of license strings
        """
        try:
            group_id, artifact_id = coordinate.split(':')
            
            # Method 1: Search API to get latest version
            search_url = f"https://search.maven.org/solrsearch/select"
            params = {
                'q': f'g:"{group_id}" AND a:"{artifact_id}"',
                'rows': 1,
                'wt': 'json'
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                docs = data.get('response', {}).get('docs', [])
                
                if docs:
                    latest_version = docs[0].get('latestVersion')
                    if latest_version:
                        # Method 2: Fetch POM file for the artifact
                        return self._fetch_from_pom(group_id, artifact_id, latest_version)
        
        except requests.RequestException as e:
            print(f"Network error fetching license for {coordinate}: {e}")
        except Exception as e:
            print(f"Error fetching license for {coordinate}: {e}")
        
        return {'Unknown'}
    
    def _fetch_from_pom(self, group_id: str, artifact_id: str, version: str) -> Set[str]:
        """Fetch and parse POM file from Maven Central.
        
        Args:
            group_id: Maven groupId
            artifact_id: Maven artifactId
            version: Version number
            
        Returns:
            Set of license strings
        """
        try:
            # Construct POM URL
            group_path = group_id.replace('.', '/')
            pom_url = (
                f"https://repo1.maven.org/maven2/{group_path}/"
                f"{artifact_id}/{version}/{artifact_id}-{version}.pom"
            )
            
            response = requests.get(pom_url, timeout=10)
            if response.status_code == 200:
                # Parse POM XML
                root = ET.fromstring(response.text)
                
                # Find <licenses> section
                licenses_elem = root.find('.//m:licenses', self.maven_ns)
                if licenses_elem is not None:
                    licenses = set()
                    for license_elem in licenses_elem.findall('m:license', self.maven_ns):
                        name_elem = license_elem.find('m:name', self.maven_ns)
                        if name_elem is not None and name_elem.text:
                            licenses.add(name_elem.text)
                    
                    return licenses
        
        except Exception:
            pass
        
        return set()


# Alternative: Gradle support
class GradlePlugin(Plugin):
    """Plugin for Java (Gradle) dependency license checking.
    
    TODO: Implement Gradle support by parsing build.gradle or build.gradle.kts
    """
    
    def get_name(self) -> str:
        return "gradle"
    
    def run(self) -> Optional[Dict[str, Set[str]]]:
        """Discover Gradle dependencies."""
        # TODO: Implement parsing of build.gradle
        # Could use:
        # 1. Parse build.gradle directly (complex due to Groovy DSL)
        # 2. Run 'gradle dependencies' command and parse output
        # 3. Use Gradle Build Scan API
        print("Gradle support not yet implemented")
        return None
    
    def load_settings(self) -> Optional[Tuple[Set[str], Set[str], Set[str]]]:
        return None


# Example usage
if __name__ == '__main__':
    plugin = JavaPlugin()
    result = plugin.run()
    if result:
        for dep, licenses in result.items():
            print(f"{dep}: {', '.join(licenses)}")
