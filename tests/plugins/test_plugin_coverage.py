"""Additional tests for plugin.py to improve coverage to 90%+."""
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import pytest

from permitcheck.plugin import Plugin, PluginManager
from permitcheck.exceptions import PluginLoadError


class ConcretePlugin(Plugin):
    """Concrete implementation for testing abstract methods."""
    
    def get_name(self):
        return "concrete"
    
    def run(self):
        return {"test": {"MIT"}}
    
    def load_settings(self):
        return ({"MIT"}, set(), set())


class TestPluginAbstractMethods:
    """Test abstract method enforcement."""
    
    def test_cannot_instantiate_abstract_plugin(self):
        """Test that Plugin cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Plugin()
    
    def test_plugin_get_name_not_implemented(self):
        """Test get_name raises NotImplementedError if not overridden."""
        # Create a class that doesn't implement get_name properly
        class IncompletePlugin(Plugin):
            def run(self):
                return {}
            def load_settings(self):
                return None
        
        with pytest.raises(TypeError):
            IncompletePlugin()
    
    def test_plugin_run_not_implemented(self):
        """Test run raises NotImplementedError if not overridden."""
        class IncompletePlugin(Plugin):
            def get_name(self):
                return "incomplete"
            def load_settings(self):
                return None
        
        with pytest.raises(TypeError):
            IncompletePlugin()
    
    def test_plugin_load_settings_not_implemented(self):
        """Test load_settings raises NotImplementedError if not overridden."""
        class IncompletePlugin(Plugin):
            def get_name(self):
                return "incomplete"
            def run(self):
                return {}
        
        with pytest.raises(TypeError):
            IncompletePlugin()
    
    def test_concrete_plugin_can_be_instantiated(self):
        """Test that concrete implementations work."""
        plugin = ConcretePlugin()
        assert plugin.get_name() == "concrete"
        assert plugin.run() == {"test": {"MIT"}}
        assert plugin.load_settings() == ({"MIT"}, set(), set())


class TestPluginManagerEnvironmentVariables:
    """Test PERMITCHECK_PLUGINPATH environment variable handling."""
    
    @patch.dict(os.environ, {'PERMITCHECK_PLUGINPATH': '/custom/path1:/custom/path2'}, clear=False)
    @patch('os.listdir')
    def test_load_plugins_with_env_var(self, mock_listdir):
        """Test loading plugins with PERMITCHECK_PLUGINPATH set."""
        mock_listdir.return_value = []
        
        manager = PluginManager()
        manager.load_plugins()
        
        # Should include paths from environment variable
        assert '/custom/path1' in manager.plugindirs
        assert '/custom/path2' in manager.plugindirs
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('os.listdir')
    def test_load_plugins_without_env_var(self, mock_listdir):
        """Test loading plugins without PERMITCHECK_PLUGINPATH."""
        mock_listdir.return_value = []
        
        manager = PluginManager()
        manager.load_plugins()
        
        # Should only have default plugin directory
        assert len([d for d in manager.plugindirs if 'plugins' in d]) >= 1
    
    @patch.dict(os.environ, {'PERMITCHECK_PLUGINPATH': '/path/a' + os.pathsep + '/path/b'}, clear=False)
    @patch('os.listdir')
    def test_multiple_paths_in_env_var(self, mock_listdir):
        """Test multiple paths in PERMITCHECK_PLUGINPATH."""
        mock_listdir.return_value = []
        
        manager = PluginManager()
        manager.load_plugins()
        
        assert '/path/a' in manager.plugindirs
        assert '/path/b' in manager.plugindirs


class TestPluginManagerFileHandling:
    """Test plugin file discovery and loading."""
    
    @patch('os.listdir')
    def test_skip_hidden_files(self, mock_listdir):
        """Test that hidden files starting with .# are skipped."""
        mock_listdir.return_value = ['.#temp.py', '__init__.py']
        
        manager = PluginManager()
        manager.load_plugins()
        
        # Should not try to load hidden files (no PluginLoadError raised)
        # Only properly formatted plugin files should be attempted
    
    @patch('os.listdir')
    def test_skip_dunder_files(self, mock_listdir):
        """Test that __init__.py and similar files are skipped."""
        mock_listdir.return_value = ['__init__.py', '__pycache__']
        
        manager = PluginManager()
        manager.load_plugins()
        
        # Should skip __init__.py and __pycache__ (no errors raised)
        assert manager.plugins is not None
    
    @patch('os.listdir')
    def test_skip_non_for_files(self, mock_listdir):
        """Test that files not starting with 'for_' are skipped."""
        mock_listdir.return_value = ['test.py', 'helper.py']
        
        manager = PluginManager()
        manager.load_plugins()
        
        # Should skip files not starting with 'for_'
        assert manager.plugins is not None
    
    @patch('os.listdir')
    @patch.object(PluginManager, '_load_plugin')
    def test_load_py_files(self, mock_load_plugin, mock_listdir):
        """Test loading .py plugin files."""
        mock_listdir.return_value = ['for_python.py', 'for_npm.py']
        
        manager = PluginManager()
        manager.load_plugins()
        
        # Should call _load_plugin for both files
        calls = mock_load_plugin.call_args_list
        assert any('python' in str(call) for call in calls)
    
    @patch('os.listdir')
    @patch.object(PluginManager, '_load_plugin')
    def test_load_pyc_files(self, mock_load_plugin, mock_listdir):
        """Test loading .pyc plugin files."""
        mock_listdir.return_value = ['for_rust.pyc', 'for_go.pyc']
        
        manager = PluginManager()
        manager.load_plugins()
        
        # Should call _load_plugin for .pyc files
        assert mock_load_plugin.call_count >= 2


class TestPluginLoadingErrors:
    """Test error handling in plugin loading."""
    
    @patch('os.listdir')
    def test_import_error_raises_plugin_load_error(self, mock_listdir):
        """Test ImportError is caught and wrapped in PluginLoadError."""
        mock_listdir.return_value = ['for_missing.py']
        
        manager = PluginManager()
        
        with pytest.raises(PluginLoadError) as exc_info:
            with patch('builtins.__import__', side_effect=ImportError("Module not found")):
                manager.load_plugins()
        
        assert "Failed to load plugin" in str(exc_info.value)
        assert "missing" in str(exc_info.value)
    
    @patch('os.listdir')
    def test_other_exception_raises_plugin_load_error(self, mock_listdir):
        """Test other exceptions are caught and wrapped."""
        mock_listdir.return_value = ['for_broken.py']
        
        manager = PluginManager()
        
        with pytest.raises(PluginLoadError) as exc_info:
            with patch('builtins.__import__', side_effect=RuntimeError("Something broke")):
                manager.load_plugins()
        
        assert "Error initializing plugin" in str(exc_info.value)
    
    @patch('os.listdir')
    @patch('builtins.__import__')
    def test_module_without_plugin_class(self, mock_import, mock_listdir):
        """Test module that doesn't contain a Plugin subclass."""
        mock_listdir.return_value = ['for_empty.py']
        
        # Create a mock module with no Plugin subclass
        mock_module = Mock(spec=[])
        # Add some attributes that are not Plugin classes
        type(mock_module).some_function = Mock()
        type(mock_module).CONSTANT = 42
        mock_import.return_value = mock_module
        
        # Mock dir() to return our attributes
        with patch('builtins.dir', return_value=['some_function', 'CONSTANT']):
            manager = PluginManager()
            manager.load_plugins()
        
        # Should handle gracefully - no plugin loaded for 'empty'
        assert 'empty' not in manager.plugins


class TestGetPluginsByLanguage:
    """Test get_plugins_by_language method."""
    
    def test_get_existing_plugin(self):
        """Test getting a plugin that exists."""
        manager = PluginManager()
        manager.plugins = {'python': ConcretePlugin()}
        
        plugin = manager.get_plugins_by_language('python')
        assert plugin is not None
        assert plugin.get_name() == "concrete"
    
    def test_get_nonexistent_plugin(self, capsys):
        """Test getting a plugin that doesn't exist."""
        manager = PluginManager()
        manager.plugins = {'python': ConcretePlugin()}
        
        plugin = manager.get_plugins_by_language('rust')
        
        # Should return None and print message
        assert plugin is None
        
        captured = capsys.readouterr()
        assert "Plugin for 'rust' is not loaded" in captured.out
        assert "Available plugins: python" in captured.out
    
    def test_get_plugin_no_plugins_loaded(self, capsys):
        """Test getting plugin when no plugins are loaded."""
        manager = PluginManager()
        manager.plugins = {}
        
        plugin = manager.get_plugins_by_language('any')
        
        assert plugin is None
        captured = capsys.readouterr()
        assert "Available plugins: none" in captured.out


class TestGetSupportedLanguages:
    """Test get_supported_languages method."""
    
    def test_get_supported_languages_empty(self):
        """Test with no plugins loaded."""
        manager = PluginManager()
        manager.plugins = {}
        
        languages = manager.get_supported_languages()
        assert languages == []
    
    def test_get_supported_languages_multiple(self):
        """Test with multiple plugins loaded."""
        manager = PluginManager()
        manager.plugins = {
            'python': ConcretePlugin(),
            'npm': ConcretePlugin(),
            'rust': ConcretePlugin()
        }
        
        languages = manager.get_supported_languages()
        assert len(languages) == 3
        assert 'python' in languages
        assert 'npm' in languages
        assert 'rust' in languages


class TestRunPlugin:
    """Test run_plugin method."""
    
    def test_run_existing_plugin(self):
        """Test running an existing plugin."""
        manager = PluginManager()
        manager.plugins = {'python': ConcretePlugin()}
        
        result = manager.run_plugin('python')
        assert result == {"test": {"MIT"}}
    
    def test_run_nonexistent_plugin(self):
        """Test running a non-existent plugin raises ValueError."""
        manager = PluginManager()
        manager.plugins = {'python': ConcretePlugin()}
        
        with pytest.raises(ValueError) as exc_info:
            manager.run_plugin('nonexistent')
        
        assert "Plugin 'nonexistent' not found" in str(exc_info.value)


class TestPluginManagerCustomDirs:
    """Test PluginManager with custom plugin directories."""
    
    @patch('os.listdir')
    def test_custom_plugin_dirs(self, mock_listdir):
        """Test initializing with custom plugin directories."""
        mock_listdir.return_value = []
        
        custom_dirs = ['/custom/plugins', '/another/path']
        manager = PluginManager(plugindirs=custom_dirs)
        
        assert '/custom/plugins' in manager.plugindirs
        assert '/another/path' in manager.plugindirs
    
    @patch('os.listdir')
    def test_none_plugin_dirs(self, mock_listdir):
        """Test initializing with None plugin directories."""
        mock_listdir.return_value = []
        
        manager = PluginManager(plugindirs=None)
        
        # Should have empty list initially
        assert manager.plugindirs == []
