"""Tests for additional reporter output formats (HTML, Markdown, CSV, SARIF)."""
import json
import tempfile
from pathlib import Path

import pytest

from permitcheck.core.reporter import Reporter, OutputFormat
from permitcheck.core.validator import ValidationResult


@pytest.fixture
def sample_validation_result():
    """Create a sample validation result for testing."""
    result = ValidationResult()
    result.allowed.add("test-package==1.0.0 (MIT, Apache-2.0)")
    return result


@pytest.fixture
def sample_results():
    """Create sample results list."""
    result = ValidationResult()
    result.allowed.add("test-package==1.0.0 (MIT)")
    result.errors.add("bad-package==2.0.0 (GPL-3.0)")
    result.warnings.add("warning-package==3.0.0 (UNKNOWN)")
    return result


class TestHTMLReporter:
    """Test HTML output format."""
    
    def test_html_format(self, sample_results):
        """Test HTML report generation."""
        reporter = Reporter(sample_results, OutputFormat.HTML)
        output = reporter.report()
        
        # Check HTML structure
        assert "<!DOCTYPE html>" in output
        assert "<html>" in output
        assert "</html>" in output
        
    def test_html_with_empty_results(self):
        """Test HTML report with no results."""
        result = ValidationResult()
        reporter = Reporter(result, OutputFormat.HTML)
        output = reporter.report()
        
        assert "<!DOCTYPE html>" in output
        
    def test_html_styling(self, sample_results):
        """Test HTML includes styling."""
        reporter = Reporter(sample_results, OutputFormat.HTML)
        output = reporter.report()
        
        assert "<style>" in output or "table" in output


class TestMarkdownReporter:
    """Test Markdown output format."""
    
    def test_markdown_format(self, sample_results):
        """Test Markdown report generation."""
        reporter = Reporter(sample_results, OutputFormat.MARKDOWN)
        output = reporter.report()
        
        # Check Markdown structure
        assert "# PermitCheck License Report" in output or "Summary" in output
        
    def test_markdown_with_empty_results(self):
        """Test Markdown report with no results."""
        result = ValidationResult()
        reporter = Reporter(result, OutputFormat.MARKDOWN)
        output = reporter.report()
        
        assert output
        assert len(output) > 0


class TestCSVReporter:
    """Test CSV output format."""
    
    def test_csv_format(self, sample_results):
        """Test CSV report generation."""
        reporter = Reporter(sample_results, OutputFormat.CSV)
        output = reporter.report()
        
        # Check CSV has content
        assert output
        lines = output.strip().split('\n')
        assert len(lines) >= 1
        
    def test_csv_with_empty_results(self):
        """Test CSV report with no results."""
        result = ValidationResult()
        reporter = Reporter(result, OutputFormat.CSV)
        output = reporter.report()
        
        assert output


class TestSARIFReporter:
    """Test SARIF output format."""
    
    def test_sarif_format(self, sample_results):
        """Test SARIF report generation."""
        reporter = Reporter(sample_results, OutputFormat.SARIF)
        output = reporter.report()
        
        # Parse JSON
        sarif = json.loads(output)
        
        # Check SARIF structure
        assert sarif["version"] == "2.1.0"
        assert "$schema" in sarif
        assert "runs" in sarif
        
    def test_sarif_with_empty_results(self):
        """Test SARIF report with no results."""
        result = ValidationResult()
        reporter = Reporter(result, OutputFormat.SARIF)
        output = reporter.report()
        
        sarif = json.loads(output)
        assert "runs" in sarif
        
    def test_sarif_schema(self, sample_results):
        """Test SARIF includes correct schema."""
        reporter = Reporter(sample_results, OutputFormat.SARIF)
        output = reporter.report()
        
        sarif = json.loads(output)
        assert "sarif-schema" in sarif["$schema"]
        assert "2.1.0" in sarif["$schema"]


class TestReporterToFile:
    """Test writing reports to files."""
    
    def test_write_to_file(self, sample_results):
        """Test writing report to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "report.json"
            reporter = Reporter(sample_results, OutputFormat.JSON, output_file=str(output_file))
            reporter.report()
            
            assert output_file.exists()
            content = output_file.read_text()
            data = json.loads(content)
            assert data
            
    def test_write_html_to_file(self, sample_results):
        """Test writing HTML report to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "report.html"
            reporter = Reporter(sample_results, OutputFormat.HTML, output_file=str(output_file))
            reporter.report()
            
            assert output_file.exists()
            content = output_file.read_text()
            assert "<!DOCTYPE html>" in content
            
    def test_write_markdown_to_file(self, sample_results):
        """Test writing Markdown report to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "report.md"
            reporter = Reporter(sample_results, OutputFormat.MARKDOWN, output_file=str(output_file))
            reporter.report()
            
            assert output_file.exists()


class TestReporterIntegration:
    """Integration tests for reporter."""
    
    def test_all_formats_produce_output(self, sample_results):
        """Test all formats produce non-empty output."""
        for format_type in OutputFormat:
            reporter = Reporter(sample_results, format_type)
            output = reporter.report()
            assert output
            assert len(output) > 0
