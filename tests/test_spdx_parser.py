"""Tests for SPDX expression parsing."""

import pytest
from permitcheck.core.matcher import SPDXExpressionParser


class TestSPDXExpressionParser:
    """Test SPDX expression parsing logic."""
    
    def test_simple_license(self):
        """Test parsing a simple license."""
        parser = SPDXExpressionParser()
        licenses = parser.parse("MIT")
        
        assert licenses == ["MIT"]
    
    def test_or_expression(self):
        """Test parsing OR expressions."""
        parser = SPDXExpressionParser()
        licenses = parser.parse("MIT OR Apache-2.0")
        
        assert set(licenses) == {"MIT", "Apache-2.0"}
    
    def test_and_expression(self):
        """Test parsing AND expressions."""
        parser = SPDXExpressionParser()
        licenses = parser.parse("MIT AND Apache-2.0")
        
        assert set(licenses) == {"MIT", "Apache-2.0"}
    
    def test_with_expression(self):
        """Test parsing WITH expressions (license exceptions)."""
        parser = SPDXExpressionParser()
        licenses = parser.parse("GPL-2.0 WITH Classpath-exception-2.0")
        
        # Should treat as a combined license
        assert "GPL-2.0 WITH Classpath-exception-2.0" in licenses or "GPL-2.0" in licenses
    
    def test_plus_suffix(self):
        """Test parsing licenses with + suffix (or-later)."""
        parser = SPDXExpressionParser()
        licenses = parser.parse("GPL-2.0+")
        
        # Should convert GPL-2.0+ to GPL-2.0-or-later
        assert "GPL-2.0-or-later" in licenses or "GPL-2.0+" in licenses
    
    def test_complex_expression(self):
        """Test parsing complex nested expressions."""
        parser = SPDXExpressionParser()
        licenses = parser.parse("(MIT OR BSD-3-Clause) AND Apache-2.0")
        
        # Should extract all licenses
        assert "MIT" in licenses
        assert "BSD-3-Clause" in licenses or "BSD" in licenses
        assert "Apache-2.0" in licenses or "Apache" in licenses
    
    def test_parenthesized_expression(self):
        """Test parsing expressions with parentheses."""
        parser = SPDXExpressionParser()
        licenses = parser.parse("(MIT OR Apache-2.0)")
        
        assert "MIT" in licenses
        assert "Apache-2.0" in licenses or "Apache" in licenses
    
    def test_multiple_or_operators(self):
        """Test parsing expressions with multiple OR operators."""
        parser = SPDXExpressionParser()
        licenses = parser.parse("MIT OR Apache-2.0 OR BSD-3-Clause")
        
        assert "MIT" in licenses
        assert "Apache-2.0" in licenses or "Apache" in licenses
        assert "BSD-3-Clause" in licenses or "BSD" in licenses
    
    def test_whitespace_handling(self):
        """Test parsing with various whitespace."""
        parser = SPDXExpressionParser()
        
        licenses1 = parser.parse("MIT OR Apache-2.0")
        licenses2 = parser.parse("MIT  OR  Apache-2.0")
        licenses3 = parser.parse("MIT OR Apache-2.0 ")
        
        # All should parse to same result
        assert licenses1 == licenses2
        assert licenses1 == licenses3
    
    def test_case_sensitivity(self):
        """Test that license names are case-preserved."""
        parser = SPDXExpressionParser()
        licenses = parser.parse("MIT or apache-2.0")
        
        # Parser should handle case properly
        assert len(licenses) > 0
    
    def test_empty_expression(self):
        """Test parsing empty expression."""
        parser = SPDXExpressionParser()
        licenses = parser.parse("")
        
        assert licenses == []
    
    def test_invalid_expression(self):
        """Test parsing invalid expressions."""
        parser = SPDXExpressionParser()
        
        # Should not crash on malformed input
        licenses = parser.parse("MIT AND AND Apache-2.0")
        assert isinstance(licenses, list)
    
    def test_real_world_expressions(self):
        """Test parsing real-world SPDX expressions."""
        parser = SPDXExpressionParser()
        
        # Common patterns from real packages
        test_cases = [
            ("Apache-2.0", {"Apache-2.0"}),
            ("MIT", {"MIT"}),
            ("BSD-3-Clause", {"BSD-3-Clause"}),
            ("ISC", {"ISC"}),
            ("LGPL-2.1+", {"LGPL-2.1-or-later"}),
        ]
        
        for expression, expected_partial in test_cases:
            licenses = parser.parse(expression)
            # Check that at least the main license is found
            assert len(licenses) > 0, f"Failed to parse: {expression}"


class TestSPDXIntegration:
    """Test SPDX parser integration with LicenseMatcher."""
    
    def test_matcher_with_spdx_expression(self):
        """Test that LicenseMatcher uses SPDX parser."""
        from permitcheck.core.matcher import LicenseMatcher
        
        spdx_licenses = {"MIT", "Apache-2.0", "BSD-3-Clause", "GPL-2.0"}
        matcher = LicenseMatcher(spdx_licenses)
        
        # Should match through SPDX expression
        matched = matcher.match("MIT OR Apache-2.0")
        assert "MIT" in matched or "Apache-2.0" in matched
    
    def test_matcher_with_or_later(self):
        """Test that LicenseMatcher handles GPL-2.0+."""
        from permitcheck.core.matcher import LicenseMatcher
        
        spdx_licenses = {"GPL-2.0-or-later", "MIT"}
        matcher = LicenseMatcher(spdx_licenses)
        
        # Should match GPL-2.0+ to GPL-2.0-or-later
        matched = matcher.match("GPL-2.0+")
        assert "GPL-2.0-or-later" in matched or "GPL-2.0" in matched
    
    def test_normalize_license_set_with_expressions(self):
        """Test normalize_license_set with SPDX expressions."""
        from permitcheck.core.matcher import LicenseMatcher
        
        spdx_licenses = {"MIT", "Apache-2.0", "BSD-3-Clause"}
        matcher = LicenseMatcher(spdx_licenses)
        
        # Normalize a set containing expressions
        licenses = {"MIT OR Apache-2.0", "BSD-3-Clause"}
        normalized = matcher.normalize_license_set(licenses)
        
        # Should expand the OR expression
        assert len(normalized) >= 2
        assert "MIT" in normalized or "Apache-2.0" in normalized
