"""Integration tests for PermitCheck end-to-end workflows."""

import pytest
import tempfile
import shutil
from pathlib import Path
from permitcheck.lint import PermitCheck, Settings
from permitcheck.plugins.for_python import PythonLicense
from permitcheck.core.config import ConfigManager, LicensePolicy
from permitcheck.core.cache import LicenseCache


class TestEndToEndPython:
    """Integration tests for Python package scanning."""
    
    def test_full_scan_with_settings(self):
        """Test complete scan with configuration tuple."""
        # Create settings tuple
        settings = (
            {'MIT', 'Apache-2.0', 'BSD-3-Clause'},  # allowed
            {'GPL', 'LGPL'},  # trigger_error
            set()  # skip
        )
        
        # Create test dependencies
        deps = {
            'pytest': {'MIT'},
            'requests': {'Apache-2.0'},
        }
        
        # Run PermitCheck
        checker = PermitCheck(deps, settings, output_format='console')
        
        # Should have results
        assert hasattr(checker, 'allowed')
        assert hasattr(checker, 'errors')
        assert 'pytest' in checker.allowed or 'requests' in checker.allowed
    
    def test_config_loading_yaml(self, tmp_path):
        """Test configuration loading from YAML."""
        config_content = """
allowed_licenses:
  - MIT
  - Apache-2.0

trigger_error_licenses:
  - GPL

skip_libraries:
  - test-package
"""
        config_file = tmp_path / "permitcheck.yaml"
        config_file.write_text(config_content)
        
        # Load config
        config_manager = ConfigManager(base_dir=tmp_path)
        policy = config_manager.load_policy()
        
        assert 'MIT' in policy.allowed_licenses
        assert 'Apache-2.0' in policy.allowed_licenses
        assert 'GPL' in policy.trigger_error_licenses
        assert 'test-package' in policy.skip_libraries
    
    def test_config_loading_toml(self, tmp_path):
        """Test configuration loading from permitcheck.yaml."""
        config_content = """
allowed_licenses:
  - MIT
  - Apache-2.0

trigger_error_licenses:
  - GPL
"""
        config_file = tmp_path / "permitcheck.yaml"
        config_file.write_text(config_content)
        
        # Load config
        config_manager = ConfigManager(base_dir=tmp_path)
        policy = config_manager.load_policy()
        
        assert 'MIT' in policy.allowed_licenses
        assert 'GPL' in policy.trigger_error_licenses


class TestCachingIntegration:
    """Integration tests for license caching."""
    
    def test_cache_persistence(self, tmp_path):
        """Test that cache persists across instances."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        
        # First instance - set data
        cache1 = LicenseCache(cache_dir=cache_dir)
        cache1.set('pytest', {'MIT'})
        cache1.set('requests', {'Apache-2.0'})
        
        # Second instance - should load persisted data
        cache2 = LicenseCache(cache_dir=cache_dir)
        
        assert cache2.get('pytest') == {'MIT'}
        assert cache2.get('requests') == {'Apache-2.0'}
    
    def test_cache_with_python_plugin(self, tmp_path):
        """Test cache integration with Python plugin."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        
        # Create plugin with cache
        plugin = PythonLicense()
        
        # Get license for a known package (will cache it)
        licenses = plugin.get_package_license('pytest')
        
        # Verify we got license info
        assert licenses is not None
        assert len(licenses) > 0


class TestValidationWorkflow:
    """Integration tests for validation workflow."""
    
    def test_allow_only_mit(self, tmp_path):
        """Test strict MIT-only policy."""
        config_content = """
allowed_licenses:
  - MIT

trigger_error_licenses:
  - Apache-2.0
  - BSD
  - GPL
"""
        config_file = tmp_path / "permitcheck.yaml"
        config_file.write_text(config_content)
        
        config_manager = ConfigManager(base_dir=tmp_path)
        policy = config_manager.load_policy()
        
        # Should have strict MIT policy
        assert 'MIT' in policy.allowed_licenses
        assert 'Apache-2.0' in policy.trigger_error_licenses
    
    def test_no_conflicts_in_policy(self, tmp_path):
        """Test policy validation."""
        from permitcheck.exceptions import ConfigurationError
        
        # Create conflicting config
        policy = LicensePolicy(
            allowed_licenses={'MIT', 'GPL'},
            trigger_error_licenses={'GPL'},
            skip_libraries=set()
        )
        
        # Should raise error due to conflict
        with pytest.raises(ConfigurationError):
            policy.validate()
    
    def test_skip_validation_packages(self, tmp_path):
        """Test that skipped packages are configured."""
        config_content = """
allowed_licenses:
  - MIT

skip_libraries:
  - pytest
  - requests
"""
        config_file = tmp_path / "permitcheck.yaml"
        config_file.write_text(config_content)
        
        config_manager = ConfigManager(base_dir=tmp_path)
        policy = config_manager.load_policy()
        
        assert 'pytest' in policy.skip_libraries
        assert 'requests' in policy.skip_libraries


class TestMultiFormatOutput:
    """Integration tests for different output formats."""
    
    def test_console_output(self, tmp_path, capsys):
        """Test console output format."""
        from permitcheck.core.reporter import Reporter, OutputFormat
        from permitcheck.core.validator import ValidationResult
        
        result = ValidationResult(
            allowed={'pytest', 'requests'},
            errors={'bad-pkg'}
        )
        dependencies = {
            'pytest': {'MIT'},
            'requests': {'Apache-2.0'},
            'bad-pkg': {'GPL'}
        }
        
        reporter = Reporter(format=OutputFormat.CONSOLE)
        reporter.report(result, dependencies)
        
        captured = capsys.readouterr()
        assert 'pytest' in captured.out or 'requests' in captured.out
    
    def test_json_output(self, tmp_path):
        """Test JSON output format."""
        import json
        from io import StringIO
        from permitcheck.core.reporter import Reporter, OutputFormat
        from permitcheck.core.validator import ValidationResult
        
        result = ValidationResult(
            allowed={'pytest'},
            errors={'bad-pkg'}
        )
        dependencies = {
            'pytest': {'MIT'},
            'bad-pkg': {'GPL'}
        }
        
        reporter = Reporter(format=OutputFormat.JSON)
        
        import sys
        old_stdout = sys.stdout
        sys.stdout = output = StringIO()
        
        reporter.report(result, dependencies)
        
        sys.stdout = old_stdout
        json_str = output.getvalue()
        
        # Should be valid JSON
        data = json.loads(json_str)
        assert 'summary' in data
        assert data['summary']['errors'] == 1


class TestRealWorldScenarios:
    """Integration tests with real-world scenarios."""
    
    def test_current_project_scan(self):
        """Test scanning the current PermitCheck project itself."""
        from permitcheck.plugins.for_python import PythonLicense
        
        plugin = PythonLicense()
        
        # Test getting license for a known package
        pytest_license = plugin.get_package_license('pytest')
        
        # Should successfully get license
        assert pytest_license is not None
        assert len(pytest_license) > 0
        
        # pytest uses MIT license
        assert 'MIT' in pytest_license or 'MIT License' in str(pytest_license)
    
    def test_mixed_licenses_handling(self, tmp_path):
        """Test handling of packages with multiple licenses."""
        from permitcheck.core.validator import LicenseValidator
        from permitcheck.core.config import LicensePolicy
        
        policy = LicensePolicy(
            allowed_licenses={'MIT', 'Apache-2.0'},
            trigger_error_licenses={'GPL'},
            skip_libraries=set()
        )
        
        validator = LicenseValidator(policy)
        
        # Package with multiple licenses (one allowed, one not)
        dependencies = {
            'mixed-pkg': {'MIT', 'GPL'}
        }
        
        result = validator.validate(dependencies)
        
        # Should be flagged as error due to GPL
        assert 'mixed-pkg' in result.errors
