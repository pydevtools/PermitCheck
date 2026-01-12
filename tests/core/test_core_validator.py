"""Tests for core.validator module."""

import pytest
from permitcheck.core.validator import LicenseValidator, ValidationResult, Classification
from permitcheck.core.config import LicensePolicy


def test_validation_result_properties():
    """Test ValidationResult computed properties."""
    result = ValidationResult(
        allowed={'pkg1', 'pkg2'},
        errors={'pkg3'},
        warnings={'pkg4'}
    )
    
    assert result.has_errors is True
    assert result.has_warnings is True
    assert result.is_success is False
    assert result.total_checked == 4


def test_validation_result_success():
    """Test ValidationResult when all packages allowed."""
    result = ValidationResult(allowed={'pkg1', 'pkg2'})
    
    assert result.is_success is True
    assert result.has_errors is False
    assert result.has_warnings is False


def test_validator_classify_allowed():
    """Test that allowed licenses are classified correctly."""
    policy = LicensePolicy(
        allowed_licenses={'MIT', 'BSD'},
        trigger_error_licenses={'GPL'}
    )
    validator = LicenseValidator(policy)
    
    classification = validator.get_classification('test-pkg', {'MIT'})
    assert classification == Classification.ALLOWED


def test_validator_classify_error():
    """Test that trigger error licenses are classified correctly."""
    policy = LicensePolicy(
        allowed_licenses={'MIT'},
        trigger_error_licenses={'GPL'}
    )
    validator = LicenseValidator(policy)
    
    classification = validator.get_classification('test-pkg', {'GPL', 'LGPL'})
    assert classification == Classification.ERROR


def test_validator_classify_warning():
    """Test that unknown licenses are classified as warnings."""
    policy = LicensePolicy(
        allowed_licenses={'MIT'},
        trigger_error_licenses={'GPL'}
    )
    validator = LicenseValidator(policy)
    
    classification = validator.get_classification('test-pkg', {'Unknown'})
    assert classification == Classification.WARNING


def test_validator_classify_skip():
    """Test that skipped libraries are classified correctly."""
    policy = LicensePolicy(
        allowed_licenses={'MIT'},
        skip_libraries={'skip-me'}
    )
    validator = LicenseValidator(policy)
    
    classification = validator.get_classification('skip-me', {'GPL'})
    assert classification == Classification.SKIP


def test_validator_full_validation():
    """Test full validation of multiple dependencies."""
    policy = LicensePolicy(
        allowed_licenses={'MIT', 'BSD'},
        trigger_error_licenses={'GPL'},
        skip_libraries={'skip-pkg'}
    )
    validator = LicenseValidator(policy)
    
    deps = {
        'pkg1': {'MIT'},
        'pkg2': {'GPL'},
        'pkg3': {'Unknown'},
        'skip-pkg': {'GPL'},  # Should be skipped despite GPL
    }
    
    result = validator.validate(deps)
    
    assert 'pkg1' in result.allowed
    assert 'pkg2' in result.errors
    assert 'pkg3' in result.warnings
    assert 'skip-pkg' in result.skipped


def test_validator_warnings_become_errors_when_no_trigger_error():
    """Test that warnings become errors when no trigger_error_licenses configured."""
    policy = LicensePolicy(
        allowed_licenses={'MIT'},
        # No trigger_error_licenses
    )
    validator = LicenseValidator(policy)
    
    deps = {
        'pkg1': {'MIT'},
        'pkg2': {'Unknown'},
    }
    
    result = validator.validate(deps)
    
    assert 'pkg2' in result.errors
    assert len(result.warnings) == 0
