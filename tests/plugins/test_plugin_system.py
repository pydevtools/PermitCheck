"""Comprehensive tests for plugin system with mocks."""
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import pytest

from permitcheck.plugin import Plugin, PluginManager
from permitcheck.exceptions import PluginLoadError


class MockPlugin(Plugin):
    """Mock plugin for testing."""
    
    def __init__(self, name="mock"):
        self.name = name
        self.settings_data = {}
        
    def get_name(self):
        return self.name
    
    def run(self):
        return {"package1": {"MIT"}, "package2": {"Apache-2.0"}}
    
    def load_settings(self):
        return self.settings_data


class TestPluginBase:
    """Test Plugin base class."""
    
    def test_plugin_has_abstract_methods(self):
        """Test Plugin has required abstract methods."""
        assert hasattr(Plugin, 'get_name')
        assert hasattr(Plugin, 'run')
        assert hasattr(Plugin, 'load_settings')
        
    def test_plugin_subclass(self):
        """Test creating a plugin subclass."""
        plugin = MockPlugin("test-plugin")
        assert plugin.get_name() == "test-plugin"
        assert isinstance(plugin.run(), dict)


class TestPluginManager:
    """Test PluginManager functionality."""
    
    def test_plugin_manager_initialization(self):
        """Test PluginManager can be initialized."""
        manager = PluginManager()
        assert manager is not None
        
    def test_load_plugins_python(self):
        """Test loading Python plugin."""
        manager = PluginManager()
        plugins = manager.load_plugins('python')
        
        assert plugins is not None
        assert isinstance(plugins, dict)
        
    @patch('permitcheck.plugin.PluginManager.load_plugins')
    def test_load_plugins_with_mock(self, mock_load):
        """Test load_plugins with mock."""
        mock_load.return_value = {'python': MockPlugin('python')}
        
        manager = PluginManager()
        plugins = manager.load_plugins('python')
        
        assert 'python' in plugins
        mock_load.assert_called_once_with('python')
        
    def test_run_plugin_python(self):
        """Test running Python plugin."""
        manager = PluginManager()
        manager.load_plugins('python')
        
        # Run plugin
        result = manager.run_plugin('python')
        
        assert result is not None
        assert isinstance(result, dict)
        
    @patch('permitcheck.plugins.for_python.PythonPlugin')
    def test_run_plugin_with_cache(self, mock_python_plugin):
        """Test running plugin with cache."""
        mock_instance = Mock()
        mock_instance.run.return_value = {"package": {"MIT"}}
        mock_python_plugin.return_value = mock_instance
        
        manager = PluginManager()
        manager.plugins = {'python': mock_instance}
        
        result = manager.run_plugin('python')
        
        assert result is not None
        mock_instance.run.assert_called_once()
        
    @patch('permitcheck.plugins.for_python.PythonPlugin')
    def test_run_plugin_without_cache(self, mock_python_plugin):
        """Test running plugin without cache."""
        mock_instance = Mock()
        mock_instance.run.return_value = {"package": {"MIT"}}
        mock_python_plugin.return_value = mock_instance
        
        manager = PluginManager()
        manager.plugins = {'python': mock_instance}
        
        result = manager.run_plugin('python')
        
        assert result is not None


class TestPluginLoadingEdgeCases:
    """Test edge cases in plugin loading."""
    
    def test_load_nonexistent_plugin(self):
        """Test loading non-existent plugin."""
        manager = PluginManager()
        
        # Loading with unrecognized plugin name loads all plugins
        result = manager.load_plugins('nonexistent')
        # Should return available plugins
        assert isinstance(result, dict)
            
    def test_load_plugins_all_languages(self):
        """Test loading plugins for all languages."""
        manager = PluginManager()
        
        # Should load without errors
        plugins = manager.load_plugins()
        assert isinstance(plugins, dict)
        
    def test_load_multiple_plugins(self):
        """Test loading multiple plugins."""
        manager = PluginManager()
        
        # Load Python
        plugins1 = manager.load_plugins('python')
        assert 'python' in plugins1
        
        # NPM might not be implemented yet, but test the pattern
        try:
            plugins2 = manager.load_plugins('npm')
            assert isinstance(plugins2, dict)
        except (PluginLoadError, NotImplementedError):
            # Expected if npm not implemented
            pass


class TestPluginManagerWithMocks:
    """Test PluginManager with comprehensive mocks."""
    
    @patch('permitcheck.plugins.for_python.PythonPlugin')
    def test_manager_with_mock_python_plugin(self, mock_plugin_class):
        """Test manager with mocked Python plugin."""
        mock_plugin = MockPlugin('python')
        mock_plugin_class.return_value = mock_plugin
        
        manager = PluginManager()
        plugins = manager.load_plugins('python')
        
        assert 'python' in plugins
        
    def test_plugin_settings_loading(self):
        """Test plugin settings loading."""
        manager = PluginManager()
        manager.load_plugins('python')
        
        # Get plugin and check if it has load_settings method
        if 'python' in manager.plugins:
            plugin = manager.plugins['python']
            settings = plugin.load_settings()
            assert settings is not None


class TestPluginErrorHandling:
    """Test plugin error handling."""
    
    @patch('permitcheck.plugins.for_python.PythonPlugin')
    def test_plugin_run_error(self, mock_plugin_class):
        """Test handling errors during plugin run."""
        mock_plugin = Mock()
        mock_plugin.run.side_effect = Exception("Plugin error")
        mock_plugin_class.return_value = mock_plugin
        
        manager = PluginManager()
        manager.plugins = {'python': mock_plugin}
        
        with pytest.raises(Exception) as exc_info:
            manager.run_plugin('python')
        
        assert "Plugin error" in str(exc_info.value)
        
    def test_run_unloaded_plugin(self):
        """Test running plugin that wasn't loaded."""
        manager = PluginManager()
        
        with pytest.raises(Exception):
            manager.run_plugin('nonexistent')


class TestPluginIntegration:
    """Integration tests for plugin system."""
    
    def test_full_plugin_workflow(self):
        """Test complete plugin workflow."""
        manager = PluginManager()
        
        # Load plugin
        plugins = manager.load_plugins('python')
        assert 'python' in plugins
        
        # Run plugin
        result = manager.run_plugin('python')
        assert isinstance(result, dict)
        
        # Load settings
        settings = plugins['python'].load_settings()
        assert settings is not None
        
    @patch('permitcheck.plugins.for_python.PythonPlugin')
    def test_plugin_lifecycle(self, mock_plugin_class):
        """Test plugin lifecycle management."""
        mock_plugin = MockPlugin('python')
        mock_plugin_class.return_value = mock_plugin
        
        manager = PluginManager()
        
        # Load
        plugins = manager.load_plugins('python')
        assert 'python' in plugins
        
        # Run multiple times
        result1 = manager.run_plugin('python')
        result2 = manager.run_plugin('python')
        
        assert result1 == result2
        
    def test_multiple_manager_instances(self):
        """Test multiple plugin manager instances."""
        manager1 = PluginManager()
        manager2 = PluginManager()
        
        # Both should work independently
        plugins1 = manager1.load_plugins('python')
        plugins2 = manager2.load_plugins('python')
        
        assert plugins1 is not None
        assert plugins2 is not None


class TestPluginCaching:
    """Test plugin caching behavior."""
    
    def test_plugin_cache_usage(self):
        """Test that plugins use cache appropriately."""
        manager = PluginManager()
        manager.load_plugins('python')
        
        # Run plugin multiple times
        result1 = manager.run_plugin('python')
        result2 = manager.run_plugin('python')
        
        # Both should return results
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)


class TestPluginSettings:
    """Test plugin settings functionality."""
    
    def test_default_settings(self):
        """Test plugin with default settings."""
        plugin = MockPlugin()
        settings = plugin.load_settings()
        
        assert settings is not None
        assert isinstance(settings, dict)
        
    def test_custom_settings(self):
        """Test plugin with custom settings."""
        plugin = MockPlugin()
        plugin.settings_data = {"allow": ["MIT", "Apache-2.0"]}
        
        settings = plugin.load_settings()
        assert "allow" in settings
        assert "MIT" in settings["allow"]
