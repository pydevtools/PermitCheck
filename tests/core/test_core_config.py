"""Tests for core.config module."""

import pytest
from pathlib import Path
from permitcheck.core.config import ConfigManager, LicensePolicy
from permitcheck.exceptions import ConfigurationError


def test_license_policy_initialization():
    """Test LicensePolicy initialization and base identifier expansion."""
    policy = LicensePolicy(
        allowed_licenses={'MIT', 'Apache-2.0'},
        trigger_error_licenses={'GPL-3.0'},
        skip_libraries={'test-lib'}
    )
    
    # Should add base identifiers
    assert 'MIT' in policy.allowed_licenses
    assert 'Apache-2.0' in policy.allowed_licenses
    assert 'Apache' in policy.allowed_licenses  # Base identifier
    assert 'GPL-3.0' in policy.trigger_error_licenses
    assert 'GPL' in policy.trigger_error_licenses  # Base identifier


def test_license_policy_conflict_detection():
    """Test that conflicting licenses raise ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Conflicting licenses"):
        policy = LicensePolicy(
            allowed_licenses={'MIT'},
            trigger_error_licenses={'MIT'}  # Conflict!
        )
        policy.validate()


def test_config_manager_from_settings():
    """Test loading policy from settings tuple."""
    manager = ConfigManager()
    allowed = {'MIT', 'BSD'}
    trigger_error = {'GPL'}
    skip = {'test-lib'}
    
    policy = manager.load_policy((allowed, trigger_error, skip))
    
    assert policy.allowed_licenses >= allowed
    assert policy.trigger_error_licenses >= trigger_error
    assert policy.skip_libraries == skip


def test_config_manager_missing_file():
    """Test that missing config file raises ConfigurationError."""
    manager = ConfigManager(Path('/nonexistent/path'))
    
    with pytest.raises(ConfigurationError, match="No configuration file found"):
        manager.load_policy()
