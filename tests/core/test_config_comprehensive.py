"""Comprehensive tests for config.py to achieve 85%+ coverage."""

import os
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest
import tempfile

from permitcheck.core.config import LicensePolicy, ConfigManager
from permitcheck.exceptions import ConfigurationError


class TestLicensePolicyInit:
    """Test LicensePolicy initialization and post_init."""
    
    def test_post_init_adds_base_identifiers_allowed(self):
        """Test that base identifiers are added for allowed licenses."""
        policy = LicensePolicy(
            allowed_licenses={'Apache-2.0', 'GPL-3.0', 'MIT'}
        )
        
        # Should include both full and base identifiers
        assert 'Apache-2.0' in policy.allowed_licenses
        assert 'Apache' in policy.allowed_licenses
        assert 'GPL-3.0' in policy.allowed_licenses
        assert 'GPL' in policy.allowed_licenses
        assert 'MIT' in policy.allowed_licenses
    
    def test_post_init_adds_base_identifiers_trigger_error(self):
        """Test that base identifiers are added for trigger_error licenses."""
        policy = LicensePolicy(
            trigger_error_licenses={'AGPL-3.0', 'Commons-Clause'}
        )
        
        assert 'AGPL-3.0' in policy.trigger_error_licenses
        assert 'AGPL' in policy.trigger_error_licenses
        assert 'Commons-Clause' in policy.trigger_error_licenses
        assert 'Commons' in policy.trigger_error_licenses
    
    def test_post_init_single_word_licenses(self):
        """Test licenses without hyphens."""
        policy = LicensePolicy(
            allowed_licenses={'MIT', 'ISC', 'BSD'}
        )
        
        # Single word licenses should still be present
        assert 'MIT' in policy.allowed_licenses
        assert 'ISC' in policy.allowed_licenses
        assert 'BSD' in policy.allowed_licenses


class TestLicensePolicyValidation:
    """Test LicensePolicy validation."""
    
    def test_validate_no_conflicts(self):
        """Test validation passes with no conflicts."""
        policy = LicensePolicy(
            allowed_licenses={'MIT', 'Apache-2.0'},
            trigger_error_licenses={'GPL-3.0', 'AGPL-3.0'}
        )
        
        # Should not raise
        policy.validate()
    
    def test_validate_with_conflicts_exact(self):
        """Test validation fails when same license in both sets."""
        policy = LicensePolicy(
            allowed_licenses={'MIT', 'Apache-2.0'},
            trigger_error_licenses={'MIT', 'GPL-3.0'}
        )
        
        with pytest.raises(ConfigurationError) as exc_info:
            policy.validate()
        
        assert 'Conflicting licenses' in str(exc_info.value)
        assert 'MIT' in str(exc_info.value)
    
    def test_validate_with_base_identifier_conflicts(self):
        """Test validation catches conflicts via base identifiers."""
        policy = LicensePolicy(
            allowed_licenses={'Apache-2.0'},
            trigger_error_licenses={'Apache-1.0'}
        )
        
        # Both will have 'Apache' base identifier
        with pytest.raises(ConfigurationError) as exc_info:
            policy.validate()
        
        assert 'Conflicting licenses' in str(exc_info.value)
        assert 'Apache' in str(exc_info.value)
    
    def test_validate_empty_sets(self):
        """Test validation with empty sets."""
        policy = LicensePolicy()
        
        # Should not raise
        policy.validate()


class TestConfigManagerInit:
    """Test ConfigManager initialization."""
    
    def test_init_default_base_dir(self):
        """Test initialization with default base directory."""
        manager = ConfigManager()
        
        assert manager.base_dir == Path.cwd()
    
    def test_init_custom_base_dir(self):
        """Test initialization with custom base directory."""
        custom_dir = Path('/tmp/custom')
        manager = ConfigManager(base_dir=custom_dir)
        
        assert manager.base_dir == custom_dir
    
    def test_config_files_list(self):
        """Test CONFIG_FILES constant."""
        assert 'permitcheck.yaml' in ConfigManager.CONFIG_FILES
        assert '.permitcheck.yaml' in ConfigManager.CONFIG_FILES
        assert 'permitcheck.yml' in ConfigManager.CONFIG_FILES


class TestConfigManagerFindConfigFile:
    """Test _find_config_file method."""
    
    def test_find_first_existing_file(self):
        """Test finding the first existing config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create second config file
            config2 = tmp_path / '.permitcheck.yaml'
            config2.touch()
            
            manager = ConfigManager(base_dir=tmp_path)
            result = manager._find_config_file()
            
            # Should find second in list since first doesn't exist
            assert result == config2
    
    def test_find_no_config_file(self):
        """Test when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(base_dir=Path(tmpdir))
            result = manager._find_config_file()
            
            assert result is None
    
    def test_find_prioritizes_first_in_list(self):
        """Test that first file in CONFIG_FILES is prioritized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create all config files
            (tmp_path / 'permitcheck.yaml').touch()
            (tmp_path / '.permitcheck.yaml').touch()
            (tmp_path / 'permitcheck.yml').touch()
            
            manager = ConfigManager(base_dir=tmp_path)
            result = manager._find_config_file()
            
            # Should return first one
            assert result.name == 'permitcheck.yaml'


class TestConfigManagerLoadConfig:
    """Test _load_config method."""
    
    @patch('permitcheck.core.config.read_yaml')
    def test_load_yaml_config(self, mock_read_yaml):
        """Test loading YAML config."""
        mock_read_yaml.return_value = {'allowed_licenses': ['MIT']}
        
        manager = ConfigManager()
        config_path = Path('test.yaml')
        
        result = manager._load_config(config_path)
        
        assert result == {'allowed_licenses': ['MIT']}
        mock_read_yaml.assert_called_once_with(str(config_path))
    
    @patch('permitcheck.core.config.read_yaml')
    def test_load_yml_config(self, mock_read_yaml):
        """Test loading .yml config."""
        mock_read_yaml.return_value = {'allowed_licenses': ['MIT']}
        
        manager = ConfigManager()
        config_path = Path('test.yml')
        
        result = manager._load_config(config_path)
        
        assert result == {'allowed_licenses': ['MIT']}
    
    @patch('permitcheck.core.config.read_toml')
    def test_load_toml_config(self, mock_read_toml):
        """Test loading TOML config."""
        mock_read_toml.return_value = {'allowed_licenses': ['Apache-2.0']}
        
        manager = ConfigManager()
        config_path = Path('test.toml')
        
        result = manager._load_config(config_path)
        
        assert result == {'allowed_licenses': ['Apache-2.0']}
        mock_read_toml.assert_called_once_with(str(config_path))
    
    def test_load_unsupported_format(self):
        """Test loading unsupported config format."""
        manager = ConfigManager()
        config_path = Path('test.json')
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager._load_config(config_path)
        
        assert 'Unsupported config format' in str(exc_info.value)
        assert '.json' in str(exc_info.value)
    
    @patch('permitcheck.core.config.read_yaml')
    def test_load_config_read_error(self, mock_read_yaml):
        """Test handling read errors."""
        mock_read_yaml.side_effect = Exception("Read error")
        
        manager = ConfigManager()
        config_path = Path('test.yaml')
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager._load_config(config_path)
        
        assert 'Failed to load' in str(exc_info.value)
        assert 'Read error' in str(exc_info.value)


class TestConfigManagerParsePolicy:
    """Test _parse_policy method."""
    
    def test_parse_policy_complete(self):
        """Test parsing complete policy config."""
        config = {
            'allowed_licenses': ['MIT', 'Apache-2.0'],
            'trigger_error_licenses': ['GPL-3.0'],
            'skip_libraries': ['test-lib']
        }
        
        manager = ConfigManager()
        policy = manager._parse_policy(config)
        
        assert 'MIT' in policy.allowed_licenses
        assert 'Apache-2.0' in policy.allowed_licenses
        assert 'GPL-3.0' in policy.trigger_error_licenses
        assert 'test-lib' in policy.skip_libraries
    
    def test_parse_policy_minimal(self):
        """Test parsing minimal policy config."""
        config = {}
        
        manager = ConfigManager()
        policy = manager._parse_policy(config)
        
        assert policy.allowed_licenses == set()
        assert policy.trigger_error_licenses == set()
        assert policy.skip_libraries == set()
    
    def test_parse_policy_none_skip_libraries(self):
        """Test parsing when skip_libraries is None."""
        config = {
            'allowed_licenses': ['MIT'],
            'skip_libraries': None
        }
        
        manager = ConfigManager()
        policy = manager._parse_policy(config)
        
        assert policy.skip_libraries == set()
    
    def test_parse_policy_invalid_type(self):
        """Test parsing non-dictionary config."""
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager._parse_policy("not a dict")
        
        assert 'must be a dictionary' in str(exc_info.value)
    
    def test_parse_policy_with_conflicts(self):
        """Test parsing policy with conflicts triggers validation error."""
        config = {
            'allowed_licenses': ['MIT'],
            'trigger_error_licenses': ['MIT']
        }
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError):
            manager._parse_policy(config)


class TestConfigManagerLoadPolicy:
    """Test load_policy method."""
    
    def test_load_policy_from_settings_tuple(self):
        """Test loading policy from settings tuple."""
        settings = (
            {'MIT', 'Apache-2.0'},
            {'GPL-3.0'},
            {'skip-lib'}
        )
        
        manager = ConfigManager()
        policy = manager.load_policy(settings)
        
        assert 'MIT' in policy.allowed_licenses
        assert 'GPL-3.0' in policy.trigger_error_licenses
        assert 'skip-lib' in policy.skip_libraries
    
    def test_load_policy_from_settings_validates(self):
        """Test that loading from settings validates."""
        settings = (
            {'MIT'},
            {'MIT'},  # Conflict
            set()
        )
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError):
            manager.load_policy(settings)
    
    @patch.object(ConfigManager, '_find_config_file')
    @patch.object(ConfigManager, '_load_config')
    def test_load_policy_from_config_file(self, mock_load, mock_find):
        """Test loading policy from config file."""
        mock_find.return_value = Path('permitcheck.yaml')
        mock_load.return_value = {
            'allowed_licenses': ['MIT'],
            'trigger_error_licenses': [],
            'skip_libraries': []
        }
        
        manager = ConfigManager()
        policy = manager.load_policy()
        
        assert 'MIT' in policy.allowed_licenses
        mock_find.assert_called_once()
        mock_load.assert_called_once()
    
    @patch.object(ConfigManager, '_find_config_file')
    def test_load_policy_no_config_found(self, mock_find):
        """Test error when no config file found."""
        mock_find.return_value = None
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.load_policy()
        
        assert 'No configuration file found' in str(exc_info.value)
        assert 'permitcheck.yaml' in str(exc_info.value)


class TestConfigManagerLoadFromPyproject:
    """Test load_from_pyproject method."""
    
    @patch('permitcheck.core.config.read_toml')
    def test_load_from_pyproject_success(self, mock_read_toml):
        """Test loading from pyproject.toml with licenses section."""
        mock_read_toml.return_value = {
            'licenses': {
                'allowed': ['MIT', 'Apache-2.0'],
                'trigger_error': ['GPL-3.0'],
                'skip_libraries': ['test-lib']
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pyproject = tmp_path / 'pyproject.toml'
            pyproject.touch()
            
            manager = ConfigManager(base_dir=tmp_path)
            policy = manager.load_from_pyproject()
            
            assert policy is not None
            assert 'MIT' in policy.allowed_licenses
            assert 'GPL-3.0' in policy.trigger_error_licenses
            assert 'test-lib' in policy.skip_libraries
    
    def test_load_from_pyproject_no_file(self):
        """Test when pyproject.toml doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(base_dir=Path(tmpdir))
            result = manager.load_from_pyproject()
            
            assert result is None
    
    @patch('permitcheck.core.config.read_toml')
    def test_load_from_pyproject_no_licenses_section(self, mock_read_toml):
        """Test when pyproject.toml exists but has no licenses section."""
        mock_read_toml.return_value = {
            'project': {'name': 'test'}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pyproject = tmp_path / 'pyproject.toml'
            pyproject.touch()
            
            manager = ConfigManager(base_dir=tmp_path)
            result = manager.load_from_pyproject()
            
            assert result is None
    
    @patch('permitcheck.core.config.read_toml')
    def test_load_from_pyproject_read_error(self, mock_read_toml):
        """Test handling read errors from pyproject.toml."""
        mock_read_toml.side_effect = Exception("Parse error")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pyproject = tmp_path / 'pyproject.toml'
            pyproject.touch()
            
            manager = ConfigManager(base_dir=tmp_path)
            
            with pytest.raises(ConfigurationError) as exc_info:
                manager.load_from_pyproject()
            
            assert 'Failed to load from pyproject.toml' in str(exc_info.value)
            assert 'Parse error' in str(exc_info.value)
    
    @patch('permitcheck.core.config.read_toml')
    def test_load_from_pyproject_validation_error(self, mock_read_toml):
        """Test validation errors are raised."""
        mock_read_toml.return_value = {
            'licenses': {
                'allowed': ['MIT'],
                'trigger_error': ['MIT'],  # Conflict
                'skip_libraries': []
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pyproject = tmp_path / 'pyproject.toml'
            pyproject.touch()
            
            manager = ConfigManager(base_dir=tmp_path)
            
            with pytest.raises(ConfigurationError):
                manager.load_from_pyproject()


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""
    
    def test_full_workflow_yaml(self):
        """Test full workflow with YAML config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / 'permitcheck.yaml'
            
            # Write actual YAML content
            config_file.write_text("""
allowed_licenses:
  - MIT
  - Apache-2.0
trigger_error_licenses:
  - GPL-3.0
skip_libraries:
  - test-lib
""")
            
            manager = ConfigManager(base_dir=tmp_path)
            policy = manager.load_policy()
            
            assert 'MIT' in policy.allowed_licenses
            assert 'Apache' in policy.allowed_licenses  # Base identifier
            assert 'GPL-3.0' in policy.trigger_error_licenses
            assert 'test-lib' in policy.skip_libraries
    
    def test_multiple_config_files_precedence(self):
        """Test that first config file in list takes precedence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create multiple config files
            (tmp_path / 'permitcheck.yaml').write_text('allowed_licenses: [MIT]')
            (tmp_path / '.permitcheck.yaml').write_text('allowed_licenses: [Apache-2.0]')
            
            manager = ConfigManager(base_dir=tmp_path)
            policy = manager.load_policy()
            
            # Should load from first file
            assert 'MIT' in policy.allowed_licenses
            assert 'Apache-2.0' not in policy.allowed_licenses
