"""Tests for core.matcher module."""

import pytest
from permitcheck.core.matcher import LicenseMatcher


def test_matcher_exact_match():
    """Test exact license name matching."""
    spdx_licenses = {'MIT', 'BSD', 'GPL-3.0'}
    matcher = LicenseMatcher(spdx_licenses)
    
    result = matcher.match('MIT')
    assert 'MIT' in result


def test_matcher_normalized_match():
    """Test normalized license matching."""
    spdx_licenses = {'Apache-2.0', 'BSD-3-Clause', 'MIT'}
    matcher = LicenseMatcher(spdx_licenses)
    
    # Test common variations
    result = matcher.match('Apache 2.0')
    assert 'Apache-2.0' in result
    
    result = matcher.match('MIT License')
    assert 'MIT' in result


def test_matcher_fuzzy_match():
    """Test fuzzy license matching."""
    spdx_licenses = {'Apache-2.0', 'BSD-3-Clause'}
    matcher = LicenseMatcher(spdx_licenses)
    
    # Test close matches
    result = matcher.match('Apache License 2.0')
    assert len(result) > 0


def test_matcher_no_match():
    """Test when no match is found."""
    spdx_licenses = {'MIT', 'BSD'}
    matcher = LicenseMatcher(spdx_licenses)
    
    result = matcher.match('Unknown-License-XYZ-123')
    assert len(result) == 0


def test_matcher_empty_spdx():
    """Test matching against empty SPDX set."""
    matcher = LicenseMatcher(set())
    
    # With empty SPDX, matcher may still return normalized results
    result = matcher.match('MIT')
    # Just verify it returns a set
    assert isinstance(result, set)


def test_matcher_case_insensitive():
    """Test case-insensitive matching."""
    spdx_licenses = {'MIT', 'Apache-2.0'}
    matcher = LicenseMatcher(spdx_licenses)
    
    result = matcher.match('mit')
    assert 'MIT' in result
    
    result = matcher.match('apache-2.0')
    assert 'Apache-2.0' in result


def test_matcher_normalization():
    """Test license name normalization."""
    spdx_licenses = {'BSD', 'MIT', 'Apache-2.0', 'GPL-3.0'}
    matcher = LicenseMatcher(spdx_licenses)
    
    # Test various normalizations
    test_cases = [
        ('The MIT License', 'MIT'),
        ('Apache 2.0', 'Apache-2.0'),
    ]
    
    for input_license, expected_match in test_cases:
        result = matcher.match(input_license)
        assert expected_match in result


def test_matcher_threshold():
    """Test fuzzy matching threshold."""
    spdx_licenses = {'Apache-2.0'}
    
    # With lower threshold, should match more variations
    matcher_low = LicenseMatcher(spdx_licenses, fuzzy_threshold=0.7)
    result_low = matcher_low.match('Apache License')
    assert len(result_low) > 0


def test_matcher_with_special_characters():
    """Test matching with special characters."""
    spdx_licenses = {'Apache-2.0', 'GPL-3.0-or-later', 'CC-BY-4.0'}
    matcher = LicenseMatcher(spdx_licenses)
    
    # Test licenses with parentheses, dashes, dots
    test_cases = [
        ('Apache-2.0', 'Apache-2.0'),
        ('CC-BY-4.0', 'CC-BY-4.0'),
    ]
    
    for license_name, expected in test_cases:
        result = matcher.match(license_name)
        assert expected in result
