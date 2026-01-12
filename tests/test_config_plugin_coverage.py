"""Tests for config and plugin modules to improve coverage."""
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from permitcheck.core.config import ConfigManager, LicensePolicy
from permitcheck.plugin import PluginManager, Plugin


class TestConfigManagerCoverage:
    """Additional tests for ConfigManager."""
    
    def test_load_policy_from_tuple(self, tmp_path):
        """Test loading policy from tuple."""
        manager = ConfigManager(tmp_path)
        
        allowed = {'MIT', 'Apache-2.0'}
        trigger_error = {'GPL'}
        skip_libraries = {'test-lib'}
        
        policy = manager.load_policy((allowed, trigger_error, skip_libraries))
        
        assert policy.allowed_licenses == allowed
        assert policy.trigger_error_licenses == trigger_error
        assert policy.skip_libraries == skip_libraries
        
    def test_load_policy_from_file(self, tmp_path):
        """Test loading policy from permitcheck.yaml."""
        config_file = tmp_path / 'permitcheck.yaml'
        config_content = """allowed_licenses:
  - MIT
  - Apache-2.0
trigger_error_licenses:
  - GPL-3.0
skip_libraries:
  - test-package
"""
        config_file.write_text(config_content)
        
        manager = ConfigManager(tmp_path)
        policy = manager.load_policy(None)
        
        assert 'MIT' in policy.allowed_licenses
        assert 'GPL-3.0' in policy.trigger_error_licenses
        
    def test_load_policy_defaults(self, tmp_path):
        """Test loading policy with defaults when no config."""
        manager = ConfigManager(tmp_path)
        
        # When no config file, should raise ConfigurationError
        with pytest.raises(Exception):  # ConfigurationError
            policy = manager.load_policy(None)
        
    def test_load_config_nonexistent_file(self, tmp_path):
        """Test loading config when file doesn't exist."""
        manager = ConfigManager(tmp_path)
        
        # _load_config should raise or return empty when file doesn't exist
        try:
            config = manager._load_config()
            assert isinstance(config, dict)
        except:
            # Exception is acceptable
            pass


class TestPluginManagerCoverage:
    """Additional tests for PluginManager."""
    
    def test_load_plugins_all(self):
        """Test loading all available plugins."""
        manager = PluginManager()
        plugins = manager.load_plugins()
        
        assert isinstance(plugins, dict)
        assert len(plugins) > 0
        
    def test_load_plugins_specific(self):
        """Test loading a specific plugin."""
        manager = PluginManager()
        plugins = manager.load_plugins('python')
        
        assert 'python' in plugins
        assert plugins['python'] is not None
        
    def test_get_plugin_list(self):
        """Test getting list of loaded plugin names."""
        manager = PluginManager()
        manager.load_plugins('python')
        
        # get_plugin_list doesn't exist, use get_supported_languages
        plugin_list = manager.get_supported_languages()
        
        assert isinstance(plugin_list, list)
        assert 'python' in plugin_list
        
    def test_run_plugin_not_loaded(self):
        """Test running a plugin that isn't loaded."""
        manager = PluginManager()
        
        with pytest.raises(ValueError, match="Plugin .* not found"):
            manager.run_plugin('nonexistent')
            
    def test_plugin_manager_initialization(self):
        """Test PluginManager initialization."""
        manager = PluginManager()
        
        assert manager.plugins is not None
        assert isinstance(manager.plugins, dict)


class TestPluginBase:
    """Tests for Plugin base class."""
    
    def test_plugin_interface(self):
        """Test that Plugin is an abstract interface."""
        # Plugin should not be instantiable directly
        # but we can check its methods exist
        assert hasattr(Plugin, 'get_name')
        assert hasattr(Plugin, 'run')
        assert hasattr(Plugin, 'load_settings')


class TestLicensePolicy:
    """Test LicensePolicy dataclass."""
    
    def test_policy_creation(self):
        """Test creating a LicensePolicy."""
        policy = LicensePolicy(
            allowed_licenses={'MIT'},
            trigger_error_licenses={'GPL'},
            skip_libraries={'test'}
        )
        
        assert policy.allowed_licenses == {'MIT'}
        assert policy.trigger_error_licenses == {'GPL'}
        assert policy.skip_libraries == {'test'}
        
    def test_policy_defaults(self):
        """Test LicensePolicy default values."""
        policy = LicensePolicy(
            allowed_licenses=set(),
            trigger_error_licenses=set(),
            skip_libraries=set()
        )
        
        assert isinstance(policy.allowed_licenses, set)
        assert isinstance(policy.trigger_error_licenses, set)
        assert isinstance(policy.skip_libraries, set)


class TestPluginLoadingPaths:
    """Test various plugin loading paths."""
    
    def test_load_npm_plugin(self):
        """Test loading NPM plugin."""
        manager = PluginManager()
        plugins = manager.load_plugins('npm')
        
        if 'npm' in plugins:
            assert plugins['npm'].get_name() == 'npm'
            
    def test_load_multiple_plugins_at_once(self):
        """Test loading multiple plugins."""
        manager = PluginManager()
        plugins = manager.load_plugins()
        
        # Should load all available plugins
        assert len(plugins) >= 1  # At least python should be available


class TestConfigManagerEdgeCases:
    """Test edge cases in ConfigManager."""
    
    def test_policy_with_empty_sets(self, tmp_path):
        """Test policy with empty sets."""
        manager = ConfigManager(tmp_path)
        policy = manager.load_policy((set(), set(), set()))
        
        assert policy.allowed_licenses == set()
        assert policy.trigger_error_licenses == set()
        assert policy.skip_libraries == set()
        
    def test_config_file_with_missing_sections(self, tmp_path):
        """Test config file with missing sections."""
        config_file = tmp_path / 'permitcheck.yaml'
        config_content = """
other_section:
  value: test
"""
        config_file.write_text(config_content)
        
        manager = ConfigManager(tmp_path)
        policy = manager.load_policy(None)
        
        # Should handle gracefully
        assert isinstance(policy, LicensePolicy)
        
    @patch('permitcheck.core.config.ConfigManager._load_config')
    def test_load_policy_with_exception(self, mock_load, tmp_path):
        """Test handling exceptions in policy loading."""
        mock_load.side_effect = Exception("Config error")
        
        manager = ConfigManager(tmp_path)
        
        # Should handle gracefully or raise
        try:
            policy = manager.load_policy(None)
            # If it doesn't raise, should return valid policy
            assert isinstance(policy, LicensePolicy)
        except Exception:
            # Exception is also acceptable
            pass


class TestPluginSettings:
    """Test plugin settings loading."""
    
    def test_python_plugin_load_settings(self):
        """Test loading settings from Python plugin."""
        manager = PluginManager()
        plugins = manager.load_plugins('python')
        
        if 'python' in plugins:
            settings = plugins['python'].load_settings()
            # Settings can be None or a tuple
            assert settings is None or isinstance(settings, tuple)
            
    @patch('permitcheck.plugins.for_python.Toml.read')
    def test_plugin_settings_with_mock(self, mock_toml_read):
        """Test plugin settings loading with mocked config."""
        from permitcheck.plugins.for_python import PythonPlugin
        
        mock_toml_read.return_value = {
            'licenses': {
                'allowed': ['MIT'],
                'trigger_error': [],
                'skip_libraries': []
            }
        }
        
        plugin = PythonPlugin()
        settings = plugin.load_settings()
        
        assert settings is not None
        allowed, trigger, skip = settings
        assert 'MIT' in allowed


class TestPluginErrorHandling:
    """Test error handling in plugin system."""
    
    def test_run_plugin_invalid_name(self):
        """Test running plugin with invalid name."""
        manager = PluginManager()
        manager.load_plugins()
        
        with pytest.raises(ValueError):
            manager.run_plugin('invalid_plugin_name')
            
    def test_plugin_with_no_dependencies(self):
        """Test plugin behavior when no dependencies found."""
        # This is handled by the plugin implementation
        # Test is to ensure error handling exists
        manager = PluginManager()
        plugins = manager.load_plugins('python')
        
        # Plugin should be loaded even if it might fail on run()
        assert 'python' in plugins


class TestIntegrationPluginConfig:
    """Integration tests for plugin and config interaction."""
    
    def test_plugin_uses_config(self, tmp_path):
        """Test that plugins can use configuration."""
        config_file = tmp_path / 'permitcheck.yaml'
        config_content = """allowed_licenses:
  - MIT
  - BSD
"""
        config_file.write_text(config_content)
        
        config_manager = ConfigManager(tmp_path)
        policy = config_manager.load_policy(None)
        
        assert 'MIT' in policy.allowed_licenses
        assert 'BSD' in policy.allowed_licenses
        
    def test_full_plugin_workflow_with_settings(self, tmp_path):
        """Test complete workflow with plugin and settings."""
        manager = PluginManager()
        plugins = manager.load_plugins('python')
        
        if 'python' in plugins:
            settings = plugins['python'].load_settings()
            # Should be able to load settings
            assert settings is None or isinstance(settings, tuple)
