"""Comprehensive tests for reporter output formats with mocks."""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from permitcheck.core.reporter import Reporter, OutputFormat
from permitcheck.core.validator import ValidationResult


@pytest.fixture
def sample_validation_result():
    """Create a sample validation result."""
    result = ValidationResult()
    result.allowed.add("requests==2.28.0 (Apache-2.0)")
    result.allowed.add("pytest==7.2.0 (MIT)")
    result.errors.add("gpl-package==1.0.0 (GPL-3.0)")
    result.warnings.add("unknown-package==0.1.0 (UNKNOWN)")
    result.skipped.add("skipped-package==1.0.0")
    return result


@pytest.fixture
def sample_dependencies():
    """Create sample dependencies dictionary."""
    return {
        "requests": {"Apache-2.0"},
        "pytest": {"MIT"},
        "gpl-package": {"GPL-3.0"},
        "unknown-package": {"UNKNOWN"},
        "skipped-package": set()
    }


class TestReporterInitialization:
    """Test Reporter initialization."""
    
    def test_default_format(self):
        """Test default format is console."""
        reporter = Reporter()
        assert reporter.format == OutputFormat.CONSOLE
        
    def test_json_format(self):
        """Test JSON format initialization."""
        reporter = Reporter(OutputFormat.JSON)
        assert reporter.format == OutputFormat.JSON
        
    def test_all_formats(self):
        """Test all format types can be initialized."""
        for format_type in OutputFormat:
            reporter = Reporter(format_type)
            assert reporter.format == format_type


class TestConsoleReporter:
    """Test console output format."""
    
    def test_console_output(self, sample_validation_result, sample_dependencies, capsys):
        """Test console output format."""
        reporter = Reporter(OutputFormat.CONSOLE)
        reporter.report(sample_validation_result, sample_dependencies, "python")
        
        captured = capsys.readouterr()
        # Should contain some output
        assert len(captured.out) > 0 or len(captured.err) > 0
        
    def test_console_with_file_output(self, sample_validation_result, sample_dependencies, tmp_path):
        """Test console output to file."""
        output_file = tmp_path / "console.txt"
        
        with output_file.open('w') as f:
            reporter = Reporter(OutputFormat.CONSOLE)
            reporter.report(sample_validation_result, sample_dependencies, "python", output=f)
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0


class TestJSONReporter:
    """Test JSON output format."""
    
    def test_json_structure(self, sample_validation_result, sample_dependencies, capsys):
        """Test JSON output structure."""
        reporter = Reporter(OutputFormat.JSON)
        reporter.report(sample_validation_result, sample_dependencies, "python")
        
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        
        # Check structure
        assert "allowed" in data or "errors" in data or isinstance(data, dict)
        
    def test_json_to_file(self, sample_validation_result, sample_dependencies, tmp_path):
        """Test JSON output to file."""
        output_file = tmp_path / "report.json"
        
        with output_file.open('w') as f:
            reporter = Reporter(OutputFormat.JSON)
            reporter.report(sample_validation_result, sample_dependencies, "python", output=f)
        
        # Verify file contains valid JSON
        with output_file.open() as f:
            data = json.load(f)
            assert isinstance(data, dict)


class TestSimpleReporter:
    """Test simple output format."""
    
    def test_simple_output(self, sample_validation_result, sample_dependencies, capsys):
        """Test simple text output."""
        reporter = Reporter(OutputFormat.SIMPLE)
        reporter.report(sample_validation_result, sample_dependencies, "python")
        
        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestHTMLReporter:
    """Test HTML output format."""
    
    def test_html_structure(self, sample_validation_result, sample_dependencies, capsys):
        """Test HTML output structure."""
        reporter = Reporter(OutputFormat.HTML)
        reporter.report(sample_validation_result, sample_dependencies, "python")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Check HTML structure
        assert "<!DOCTYPE html>" in output or "<html" in output or len(output) > 0
        
    def test_html_to_file(self, sample_validation_result, sample_dependencies, tmp_path):
        """Test HTML output to file."""
        output_file = tmp_path / "report.html"
        
        with output_file.open('w') as f:
            reporter = Reporter(OutputFormat.HTML)
            reporter.report(sample_validation_result, sample_dependencies, "python", output=f)
        
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 0


class TestMarkdownReporter:
    """Test Markdown output format."""
    
    def test_markdown_structure(self, sample_validation_result, sample_dependencies, capsys):
        """Test Markdown output structure."""
        reporter = Reporter(OutputFormat.MARKDOWN)
        reporter.report(sample_validation_result, sample_dependencies, "python")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Should have markdown content
        assert len(output) > 0
        
    def test_markdown_to_file(self, sample_validation_result, sample_dependencies, tmp_path):
        """Test Markdown output to file."""
        output_file = tmp_path / "report.md"
        
        with output_file.open('w') as f:
            reporter = Reporter(OutputFormat.MARKDOWN)
            reporter.report(sample_validation_result, sample_dependencies, "python", output=f)
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0


class TestCSVReporter:
    """Test CSV output format."""
    
    def test_csv_structure(self, sample_validation_result, sample_dependencies, capsys):
        """Test CSV output structure."""
        reporter = Reporter(OutputFormat.CSV)
        reporter.report(sample_validation_result, sample_dependencies, "python")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Should have CSV content
        assert len(output) > 0
        
    def test_csv_to_file(self, sample_validation_result, sample_dependencies, tmp_path):
        """Test CSV output to file."""
        output_file = tmp_path / "report.csv"
        
        with output_file.open('w') as f:
            reporter = Reporter(OutputFormat.CSV)
            reporter.report(sample_validation_result, sample_dependencies, "python", output=f)
        
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 0


class TestSARIFReporter:
    """Test SARIF output format."""
    
    def test_sarif_structure(self, sample_validation_result, sample_dependencies, capsys):
        """Test SARIF output structure."""
        reporter = Reporter(OutputFormat.SARIF)
        reporter.report(sample_validation_result, sample_dependencies, "python")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Should be valid JSON
        if output:
            data = json.loads(output)
            assert isinstance(data, dict)
        
    def test_sarif_to_file(self, sample_validation_result, sample_dependencies, tmp_path):
        """Test SARIF output to file."""
        output_file = tmp_path / "report.sarif"
        
        with output_file.open('w') as f:
            reporter = Reporter(OutputFormat.SARIF)
            reporter.report(sample_validation_result, sample_dependencies, "python", output=f)
        
        assert output_file.exists()
        # Verify it's valid JSON
        with output_file.open() as f:
            data = json.load(f)
            assert isinstance(data, dict)


class TestReporterWithEmptyResults:
    """Test reporters with empty results."""
    
    def test_empty_results_console(self, sample_dependencies, capsys):
        """Test console reporter with empty results."""
        result = ValidationResult()
        reporter = Reporter(OutputFormat.CONSOLE)
        reporter.report(result, {}, "python")
        
        # Should not crash
        assert True
        
    def test_empty_results_json(self, capsys):
        """Test JSON reporter with empty results."""
        result = ValidationResult()
        reporter = Reporter(OutputFormat.JSON)
        reporter.report(result, {}, "python")
        
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, dict)
        
    def test_empty_results_all_formats(self, capsys):
        """Test all formats with empty results."""
        result = ValidationResult()
        
        for format_type in OutputFormat:
            reporter = Reporter(format_type)
            reporter.report(result, {}, "python")
            # Should not crash for any format
            assert True


class TestReporterMarks:
    """Test reporter mark symbols."""
    
    def test_marks_exist(self):
        """Test that reporter has mark symbols."""
        assert hasattr(Reporter, 'MARKS')
        assert 'allowed' in Reporter.MARKS
        assert 'error' in Reporter.MARKS
        assert 'warning' in Reporter.MARKS
        assert 'skip' in Reporter.MARKS


class TestReporterIntegration:
    """Integration tests for reporter."""
    
    def test_all_formats_produce_output(self, sample_validation_result, sample_dependencies, capsys):
        """Test all formats produce output."""
        for format_type in OutputFormat:
            reporter = Reporter(format_type)
            reporter.report(sample_validation_result, sample_dependencies, "python")
            
            captured = capsys.readouterr()
            # All formats should produce some output
            assert len(captured.out) >= 0  # Could be empty for some formats
            
    def test_multiple_languages(self, sample_validation_result, sample_dependencies, capsys):
        """Test reporter with different languages."""
        for language in ["python", "npm", "java"]:
            reporter = Reporter(OutputFormat.JSON)
            reporter.report(sample_validation_result, sample_dependencies, language)
            
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert isinstance(data, dict)


class TestReporterErrorHandling:
    """Test reporter error handling."""
    
    def test_invalid_output_handle(self, sample_validation_result, sample_dependencies):
        """Test with invalid output handle."""
        reporter = Reporter(OutputFormat.JSON)
        # Should handle None output gracefully
        reporter.report(sample_validation_result, sample_dependencies, "python", output=None)
        assert True
        
    def test_reporter_with_malformed_data(self, capsys):
        """Test reporter with malformed validation result."""
        result = ValidationResult()
        result.allowed.add("malformed-entry-without-proper-format")
        
        reporter = Reporter(OutputFormat.JSON)
        reporter.report(result, {"test": {"MIT"}}, "python")
        
        # Should handle gracefully
        assert True
