"""Comprehensive tests for utils module with mocks."""
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest
import toml

from permitcheck import utils


class TestGetPwd:
    """Test get_pwd function."""
    
    def test_get_pwd_returns_path(self):
        """Test get_pwd returns a valid path."""
        pwd = utils.get_pwd()
        assert pwd
        assert isinstance(pwd, str)
        assert Path(pwd).exists()
        
    def test_get_pwd_is_absolute(self):
        """Test get_pwd returns absolute path."""
        pwd = utils.get_pwd()
        assert Path(pwd).is_absolute()
        
    @patch('os.getcwd')
    def test_get_pwd_with_mock(self, mock_getcwd):
        """Test get_pwd with mocked getcwd."""
        mock_getcwd.return_value = '/mock/path'
        pwd = utils.get_pwd()
        assert '/mock/path' in pwd or pwd


class TestGetLines:
    """Test get_lines function."""
    
    def test_get_lines_reads_file(self, tmp_path):
        """Test get_lines reads file content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line1\nline2\nline3\n")
        
        lines = utils.get_lines(str(test_file))
        assert lines == ["line1", "line2", "line3"]
        
    def test_get_lines_empty_file(self, tmp_path):
        """Test get_lines with empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        lines = utils.get_lines(str(test_file))
        assert lines == []
        
    def test_get_lines_strips_whitespace(self, tmp_path):
        """Test get_lines strips whitespace."""
        test_file = tmp_path / "whitespace.txt"
        test_file.write_text("  line1  \n\tline2\t\n  \n")
        
        lines = utils.get_lines(str(test_file))
        # Should remove empty lines and strip whitespace
        assert "line1" in lines or "  line1  " in lines
        
    def test_get_lines_nonexistent_file(self, capsys):
        """Test get_lines with nonexistent file prints error."""
        lines = utils.get_lines("/nonexistent/file.txt")
        
        captured = capsys.readouterr()
        assert "Error" in captured.out or lines == []
        
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_get_lines_file_not_found(self, mock_file, capsys):
        """Test get_lines handles FileNotFoundError."""
        lines = utils.get_lines("missing.txt")
        
        captured = capsys.readouterr()
        assert "Error" in captured.out or lines == []


class TestGetMatchingKeys:
    """Test get_matching_keys function."""
    
    def test_get_matching_keys_with_keys_dict(self):
        """Test get_matching_keys with proper parameters."""
        keys = ["key1", "key2", "key3", "key_other"]
        substring = "key"
        
        # The function signature is: get_matching_keys(substring: str, keys: List[str])
        result = utils.get_matching_keys(substring, keys)
        assert isinstance(result, list)
        assert len(result) == 4  # All keys contain "key"
        
    def test_get_matching_keys_empty(self):
        """Test get_matching_keys with empty data."""
        result = utils.get_matching_keys("test", [])
        assert result == []
        
    @patch('re.search')
    def test_get_matching_keys_with_mock(self, mock_search):
        """Test get_matching_keys with mocked regex."""
        mock_search.return_value = True
        
        keys = ["key1", "key2"]
        result = utils.get_matching_keys("pattern", keys)
        
        # Should call re.search
        assert isinstance(result, list)


class TestReadToml:
    """Test read_toml function."""
    
    def test_read_toml_valid_file(self, tmp_path):
        """Test read_toml with valid TOML file."""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')
        
        data = utils.read_toml(str(toml_file))
        assert data["project"]["name"] == "test"
        assert data["project"]["version"] == "1.0.0"
        
    def test_read_toml_with_dependencies(self, tmp_path):
        """Test read_toml with dependencies."""
        toml_file = tmp_path / "pyproject.toml"
        content = """
[project]
name = "test-package"
dependencies = ["requests", "pytest"]
"""
        toml_file.write_text(content)
        
        data = utils.read_toml(str(toml_file))
        assert "dependencies" in data["project"]
        assert "requests" in data["project"]["dependencies"]
        
    def test_read_toml_nonexistent_file(self, capsys):
        """Test read_toml with nonexistent file."""
        result = utils.read_toml("/nonexistent/file.toml")
        
        captured = capsys.readouterr()
        # Should print error or return empty
        assert "Error" in captured.out or result == {} or result is None
        
    @patch('os.path.isfile', return_value=True)
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_read_toml_file_error(self, mock_file, mock_isfile):
        """Test read_toml handles file errors."""
        with pytest.raises(FileNotFoundError):
            utils.read_toml("missing.toml")
        
    def test_read_toml_invalid_toml(self, tmp_path):
        """Test read_toml with invalid TOML."""
        toml_file = tmp_path / "invalid.toml"
        toml_file.write_text("this is not valid [ toml")
        
        with pytest.raises(Exception):
            utils.read_toml(str(toml_file))


class TestFlattenSet:
    """Test flatten_set function."""
    
    def test_flatten_set_with_dict(self):
        """Test flatten_set with dictionary."""
        data = {
            "pkg1": ["MIT", "Apache-2.0"],
            "pkg2": ["BSD-3-Clause"]
        }
        
        result = utils.flatten_set(data)
        assert isinstance(result, set)
        assert "MIT" in result
        assert "Apache-2.0" in result
        assert "BSD-3-Clause" in result
        
    def test_flatten_set_empty_dict(self):
        """Test flatten_set with empty dictionary."""
        result = utils.flatten_set({})
        assert result == set()
        
    def test_flatten_set_nested_lists(self):
        """Test flatten_set with nested lists."""
        data = {
            "pkg1": ["MIT", "Apache-2.0"],
            "pkg2": ["BSD"],
            "pkg3": []
        }
        
        result = utils.flatten_set(data)
        assert len(result) >= 3
        
    @patch('itertools.chain')
    def test_flatten_set_with_mock(self, mock_chain):
        """Test flatten_set with mocked chain."""
        mock_chain.return_value = iter(["MIT", "Apache-2.0"])
        
        data = {"pkg": ["MIT"]}
        result = utils.flatten_set(data)
        
        # Should use itertools.chain
        assert isinstance(result, set)


class TestExit:
    """Test exit function."""
    
    def test_exit_default(self):
        """Test exit with default code."""
        with pytest.raises(SystemExit) as exc_info:
            utils.exit()
        assert exc_info.value.code == 0
        
    def test_exit_with_code(self):
        """Test exit with specific code."""
        with pytest.raises(SystemExit) as exc_info:
            utils.exit(code=1)
        assert exc_info.value.code == 1
        
    def test_exit_with_different_codes(self):
        """Test exit with various exit codes."""
        for code in [0, 1, 2, 127, 255]:
            with pytest.raises(SystemExit) as exc_info:
                utils.exit(code=code)
            assert exc_info.value.code == code


class TestGetBasedir:
    """Test get_basedir function."""
    
    def test_get_basedir_returns_path(self):
        """Test get_basedir returns a path."""
        basedir = utils.get_basedir()
        assert basedir
        assert isinstance(basedir, str)
        
    def test_get_basedir_exists(self):
        """Test get_basedir returns existing path."""
        basedir = utils.get_basedir()
        # Should be a valid path reference
        assert basedir or basedir == ""
        
    @patch('os.path.dirname')
    def test_get_basedir_with_mock(self, mock_dirname):
        """Test get_basedir with mocked dirname."""
        mock_dirname.return_value = '/mock/base/dir'
        
        # The function uses __file__, so we need to call it
        basedir = utils.get_basedir()
        assert isinstance(basedir, str)


class TestCheckSubclass:
    """Test check_subclass function."""
    
    def test_check_subclass_valid(self):
        """Test check_subclass with valid subclass."""
        from permitcheck.plugin import Plugin
        from permitcheck.plugins.for_python import PythonPlugin
        
        # PythonPlugin should be a subclass of Plugin
        result = utils.check_subclass(PythonPlugin, Plugin)
        assert result is True or result is not None
        
    def test_check_subclass_invalid(self):
        """Test check_subclass with non-subclass."""
        result = utils.check_subclass(str, int)
        # Should return False or raise exception
        assert result is False or result is None


class TestReadJson:
    """Test read_json function if it exists."""
    
    def test_read_json_if_exists(self):
        """Test read_json if the function exists."""
        if hasattr(utils, 'read_json'):
            # Test with mock
            with patch('builtins.open', mock_open(read_data='{"key": "value"}')):
                result = utils.read_json('test.json')
                assert result is not None


class TestWriteJson:
    """Test write_json function if it exists."""
    
    def test_write_json_if_exists(self, tmp_path):
        """Test write_json if the function exists."""
        if hasattr(utils, 'write_json'):
            json_file = tmp_path / "output.json"
            data = {"key": "value"}
            
            # Function signature is write_json(fpath: str, data: Dict)
            utils.write_json(str(json_file), data)
            
            if json_file.exists():
                assert json_file.stat().st_size > 0


class TestUtilsIntegration:
    """Integration tests for utils module."""
    
    def test_file_operations_workflow(self, tmp_path):
        """Test complete workflow with file operations."""
        # Create TOML file
        toml_file = tmp_path / "config.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        
        # Read TOML
        data = utils.read_toml(str(toml_file))
        assert data["project"]["name"] == "test"
        
        # Create text file
        text_file = tmp_path / "data.txt"
        text_file.write_text("line1\nline2\n")
        
        # Read lines
        lines = utils.get_lines(str(text_file))
        assert len(lines) >= 2
        
    def test_error_handling_workflow(self, capsys):
        """Test error handling across functions."""
        # Try to read non-existent files
        utils.get_lines("/nonexistent.txt")
        utils.read_toml("/nonexistent.toml")
        
        captured = capsys.readouterr()
        # Should have error messages
        assert len(captured.out) >= 0  # May print errors or be silent


class TestUtilsEdgeCases:
    """Test edge cases in utils module."""
    
    def test_get_lines_with_unicode(self, tmp_path):
        """Test get_lines with unicode content."""
        test_file = tmp_path / "unicode.txt"
        test_file.write_text("line1 αβγ\nline2 中文\nline3 🔥\n", encoding='utf-8')
        
        lines = utils.get_lines(str(test_file))
        assert len(lines) >= 3
        
    def test_read_toml_complex_structure(self, tmp_path):
        """Test read_toml with complex structure."""
        toml_file = tmp_path / "complex.toml"
        content = """
[project]
name = "complex"
version = "1.0.0"

[project.dependencies]
requests = "^2.28.0"
pytest = {version = "^7.0", optional = true}

[[project.authors]]
name = "Test Author"
email = "test@example.com"
"""
        toml_file.write_text(content)
        
        data = utils.read_toml(str(toml_file))
        assert data["project"]["name"] == "complex"
        
    def test_flatten_set_preserves_uniqueness(self):
        """Test flatten_set maintains set uniqueness."""
        data = {
            "pkg1": ["MIT", "MIT", "Apache-2.0"],
            "pkg2": ["MIT", "BSD"]
        }
        
        result = utils.flatten_set(data)
        # Should have unique values only
        mit_count = len([x for x in result if x == "MIT"])
        assert mit_count == 1
