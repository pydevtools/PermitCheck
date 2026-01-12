"""Tests for core.reporter module."""

import pytest
import json
from io import StringIO
from permitcheck.core.reporter import Reporter, OutputFormat
from permitcheck.core.validator import ValidationResult


@pytest.fixture
def sample_validation_result():
    """Create a sample validation result for testing."""
    return ValidationResult(
        allowed={'requests', 'pytest'},
        errors={'evil-pkg'},
        warnings={'uncertain-pkg'},
        skipped={'internal-pkg'}
    )


def test_reporter_console_format(sample_validation_result, capsys):
    """Test console output format."""
    dependencies = {
        'requests': {'Apache-2.0'},
        'pytest': {'MIT'},
        'evil-pkg': {'Proprietary'},
        'uncertain-pkg': {'Unknown'},
        'internal-pkg': {'Internal'}
    }
    
    reporter = Reporter(format=OutputFormat.CONSOLE)
    reporter.report(sample_validation_result, dependencies)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Check output contains package names
    assert 'requests' in output or 'pytest' in output


def test_reporter_json_format(sample_validation_result):
    """Test JSON output format."""
    dependencies = {
        'requests': {'Apache-2.0'},
        'pytest': {'MIT'},
        'evil-pkg': {'Proprietary'},
        'uncertain-pkg': {'Unknown'}
        # internal-pkg not in dependencies, so it won't be counted
    }
    
    reporter = Reporter(format=OutputFormat.JSON)
    
    # Capture JSON output
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    reporter.report(sample_validation_result, dependencies)
    
    sys.stdout = old_stdout
    json_output = captured_output.getvalue()
    
    # Parse and validate JSON
    data = json.loads(json_output)
    
    assert 'summary' in data
    assert data['summary']['total'] == 4


def test_reporter_simple_format(sample_validation_result, capsys):
    """Test simple text output format."""
    dependencies = {
        'requests': {'Apache-2.0'},
        'evil-pkg': {'Proprietary'}
    }
    
    reporter = Reporter(format=OutputFormat.SIMPLE)
    reporter.report(sample_validation_result, dependencies)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Simple format should show some output
    assert len(output) > 0


def test_reporter_with_empty_result(capsys):
    """Test reporter with empty validation result."""
    result = ValidationResult()
    
    reporter = Reporter(format=OutputFormat.CONSOLE)
    reporter.report(result, {})
    
    captured = capsys.readouterr()
    # Should handle empty results gracefully


def test_reporter_success_status():
    """Test reporter determines correct success status."""
    # Success case - no errors
    success_result = ValidationResult(
        allowed={'pkg1'}
    )
    
    reporter = Reporter(format=OutputFormat.JSON)
    
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    reporter.report(success_result, {'pkg1': {'MIT'}})
    
    sys.stdout = old_stdout
    json_output = captured_output.getvalue()
    data = json.loads(json_output)
    
    assert data['summary']['status'] == 'passed'


def test_reporter_failure_status():
    """Test reporter determines correct failure status."""
    # Failure case - has errors
    failure_result = ValidationResult(
        errors={'bad-pkg'}
    )
    
    reporter = Reporter(format=OutputFormat.JSON)
    
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    reporter.report(failure_result, {'bad-pkg': {'Evil'}})
    
    sys.stdout = old_stdout
    json_output = captured_output.getvalue()
    data = json.loads(json_output)
    
    assert data['summary']['status'] == 'failed'


def test_reporter_format_enum():
    """Test reporter accepts OutputFormat enum."""
    reporter = Reporter(format=OutputFormat.CONSOLE)
    assert reporter.format == OutputFormat.CONSOLE
    
    reporter_json = Reporter(format=OutputFormat.JSON)
    assert reporter_json.format == OutputFormat.JSON


def test_reporter_format_enum():
    """Test reporter accepts OutputFormat enum."""
    reporter = Reporter(format=OutputFormat.CONSOLE)
    assert reporter.format == OutputFormat.CONSOLE
    
    reporter_json = Reporter(format=OutputFormat.JSON)
    assert reporter_json.format == OutputFormat.JSON


def test_reporter_json_structure():
    """Test JSON output has correct structure."""
    result = ValidationResult(
        allowed={'requests'},
        errors={'evil-pkg'}
    )
    dependencies = {
        'requests': {'Apache-2.0'},
        'evil-pkg': {'Proprietary'}
    }
    
    reporter = Reporter(format=OutputFormat.JSON)
    
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    reporter.report(result, dependencies)
    
    sys.stdout = old_stdout
    json_output = captured_output.getvalue()
    data = json.loads(json_output)
    
    # Verify top-level keys
    assert 'summary' in data
    assert 'dependencies' in data


def test_reporter_summary_calculations():
    """Test summary statistics are calculated correctly."""
    result = ValidationResult(
        allowed={'pkg1', 'pkg2'},
        errors={'pkg3'},
        warnings={'pkg4'}
    )
    dependencies = {
        'pkg1': {'MIT'},
        'pkg2': {'Apache-2.0'},
        'pkg3': {'Bad'},
        'pkg4': {'Unknown'}
    }
    
    reporter = Reporter(format=OutputFormat.JSON)
    
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    reporter.report(result, dependencies)
    
    sys.stdout = old_stdout
    json_output = captured_output.getvalue()
    data = json.loads(json_output)
    
    summary = data['summary']
    
    # Verify counts match
    assert summary['allowed'] == 2
    assert summary['errors'] == 1
    assert summary['warnings'] == 1
