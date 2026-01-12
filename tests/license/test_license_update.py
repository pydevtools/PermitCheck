"""Comprehensive tests for license/update.py to improve coverage."""
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import xml.etree.ElementTree as ET

import pytest
import requests

from permitcheck.license.update import XML, JSON, License, main
from permitcheck import utils


class TestXMLSave:
    """Test XML.save functionality."""
    
    def test_save_single_license(self, tmp_path):
        """Test saving a single license to XML."""
        licenses_iter = [
            [{'MIT': 'MIT License'}]
        ]
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            XML.save(licenses_iter, 'test_licenses.xml')
        
        xml_file = tmp_path / 'test_licenses.xml'
        assert xml_file.exists()
        
        # Parse and verify
        tree = ET.parse(xml_file)
        root = tree.getroot()
        assert root.tag == 'licenses'
        
    def test_save_multiple_licenses(self, tmp_path):
        """Test saving multiple licenses to XML."""
        licenses_iter = [
            [
                {'MIT': 'MIT License'},
                {'Apache-2.0': 'Apache License 2.0'}
            ]
        ]
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            XML.save(licenses_iter, 'multi_licenses.xml')
        
        xml_file = tmp_path / 'multi_licenses.xml'
        assert xml_file.exists()
        
        # Parse and verify
        tree = ET.parse(xml_file)
        root = tree.getroot()
        licenses = root.findall('license')
        assert len(licenses) == 2
        
    def test_save_duplicate_licenses(self, tmp_path):
        """Test that duplicate licenses are not saved twice."""
        licenses_iter = [
            [
                {'MIT': 'MIT License'},
                {'MIT': 'MIT License'}  # Duplicate
            ]
        ]
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            XML.save(licenses_iter, 'dedup_licenses.xml')
        
        xml_file = tmp_path / 'dedup_licenses.xml'
        tree = ET.parse(xml_file)
        root = tree.getroot()
        licenses = root.findall('license')
        # Should only have one MIT license
        assert len(licenses) == 1
        
    def test_save_sorted_licenses(self, tmp_path):
        """Test that licenses are saved in sorted order."""
        licenses_iter = [
            [
                {'Zlib': 'zlib License'},
                {'Apache-2.0': 'Apache License 2.0'},
                {'MIT': 'MIT License'}
            ]
        ]
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            XML.save(licenses_iter, 'sorted_licenses.xml')
        
        xml_file = tmp_path / 'sorted_licenses.xml'
        tree = ET.parse(xml_file)
        root = tree.getroot()
        license_ids = [lic.find('id').text for lic in root.findall('license')]
        
        # Should be sorted alphabetically
        assert license_ids == sorted(license_ids)
        
    def test_save_multiple_batches(self, tmp_path):
        """Test saving licenses from multiple batches."""
        licenses_iter = [
            [{'MIT': 'MIT License'}],
            [{'Apache-2.0': 'Apache License 2.0'}],
            [{'GPL-3.0': 'GNU General Public License v3.0'}]
        ]
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            XML.save(licenses_iter, 'batch_licenses.xml')
        
        xml_file = tmp_path / 'batch_licenses.xml'
        tree = ET.parse(xml_file)
        root = tree.getroot()
        assert len(root.findall('license')) == 3


class TestJSONSave:
    """Test JSON.save functionality."""
    
    def test_save_single_license(self, tmp_path):
        """Test saving a single license to JSON."""
        licenses_iter = [
            [{'MIT': 'MIT License'}]
        ]
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            JSON.save(licenses_iter, 'test_licenses.json')
        
        json_file = tmp_path / 'test_licenses.json'
        assert json_file.exists()
        
        with open(json_file) as f:
            data = json.load(f)
        
        assert 'MIT' in data
        assert data['MIT'] == 'MIT License'
        
    def test_save_multiple_licenses(self, tmp_path):
        """Test saving multiple licenses to JSON."""
        licenses_iter = [
            [
                {'MIT': 'MIT License'},
                {'Apache-2.0': 'Apache License 2.0'}
            ]
        ]
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            JSON.save(licenses_iter, 'multi_licenses.json')
        
        json_file = tmp_path / 'multi_licenses.json'
        with open(json_file) as f:
            data = json.load(f)
        
        assert len(data) == 2
        assert 'MIT' in data
        assert 'Apache-2.0' in data
        
    def test_save_default_filename(self, tmp_path):
        """Test saving with default filename."""
        licenses_iter = [
            [{'MIT': 'MIT License'}]
        ]
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            JSON.save(licenses_iter)
        
        # Should use default filename
        json_file = tmp_path / JSON.fname
        assert json_file.exists()
        
    def test_save_merge_batches(self, tmp_path):
        """Test that licenses from multiple batches are merged."""
        licenses_iter = [
            [{'MIT': 'MIT License'}],
            [{'Apache-2.0': 'Apache License 2.0'}]
        ]
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            JSON.save(licenses_iter, 'merged.json')
        
        json_file = tmp_path / 'merged.json'
        with open(json_file) as f:
            data = json.load(f)
        
        assert len(data) == 2


class TestLicenseFetch:
    """Test License.fetch functionality."""
    
    @patch('permitcheck.utils.get_lines')
    @patch('permitcheck.license.update.requests.get')
    def test_fetch_spdx_format(self, mock_get, mock_get_lines):
        """Test fetching licenses in SPDX format."""
        mock_get_lines.return_value = ['https://example.com/licenses']
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'licenses': [
                {'licenseId': 'MIT', 'name': 'MIT License'},
                {'licenseId': 'Apache-2.0', 'name': 'Apache License 2.0'}
            ]
        }
        mock_get.return_value = mock_response
        
        result = list(License.fetch())
        
        assert len(result) == 1
        assert len(result[0]) == 2
        assert {'MIT': 'MIT License'} in result[0]
        
    @patch('permitcheck.utils.get_lines')
    @patch('permitcheck.license.update.requests.get')
    def test_fetch_github_format(self, mock_get, mock_get_lines):
        """Test fetching licenses in GitHub format."""
        mock_get_lines.return_value = ['https://api.github.com/licenses']
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'key': 'mit', 'name': 'MIT License'},
            {'key': 'apache-2.0', 'name': 'Apache License 2.0'}
        ]
        mock_get.return_value = mock_response
        
        result = list(License.fetch())
        
        assert len(result) == 1
        assert len(result[0]) == 2
        
    @patch('permitcheck.utils.get_lines')
    @patch('permitcheck.license.update.requests.get')
    def test_fetch_id_format(self, mock_get, mock_get_lines):
        """Test fetching licenses with id/name format."""
        mock_get_lines.return_value = ['https://example.com/licenses']
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 'MIT', 'name': 'MIT License'},
            {'id': 'BSD-3', 'name': 'BSD 3-Clause'}
        ]
        mock_get.return_value = mock_response
        
        result = list(License.fetch())
        
        assert len(result) == 1
        assert len(result[0]) == 2
        
    @patch('permitcheck.utils.get_lines')
    @patch('permitcheck.license.update.requests.get')
    def test_fetch_error_response(self, mock_get, mock_get_lines, capsys):
        """Test handling of error responses."""
        mock_get_lines.return_value = ['https://example.com/licenses']
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = list(License.fetch())
        
        # Should handle error gracefully
        captured = capsys.readouterr()
        assert 'Failed to fetch licenses: 404' in captured.out
        
    @patch('permitcheck.utils.get_lines')
    @patch('permitcheck.license.update.requests.get')
    def test_fetch_empty_response(self, mock_get, mock_get_lines):
        """Test handling empty response."""
        mock_get_lines.return_value = ['https://example.com/licenses']
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        result = list(License.fetch())
        
        assert len(result) == 1
        assert result[0] == []


class TestLicenseGet:
    """Test License.get functionality."""
    
    @patch('permitcheck.license.update.read_json')
    @patch('permitcheck.license.update.os.path.isfile')
    def test_get_existing_file(self, mock_isfile, mock_read_json):
        """Test getting licenses from existing file."""
        mock_isfile.return_value = True
        mock_read_json.return_value = {
            'MIT': 'MIT License',
            'Apache-2.0': 'Apache License 2.0'
        }
        
        result = License.get(is_print=False)
        
        assert isinstance(result, set)
        assert 'MIT' in result
        
    @patch('permitcheck.license.update.main')
    @patch('permitcheck.license.update.os.path.isfile')
    def test_get_nonexistent_file(self, mock_isfile, mock_main):
        """Test getting licenses when file doesn't exist."""
        mock_isfile.return_value = False
        
        # Should call main() to create the file
        try:
            License.get(is_print=False)
        except:
            pass
        
        mock_main.assert_called_once()
        
    @patch('permitcheck.license.update.read_json')
    @patch('permitcheck.license.update.os.path.isfile')
    def test_get_with_print(self, mock_isfile, mock_read_json, capsys):
        """Test getting licenses with print output."""
        mock_isfile.return_value = True
        mock_read_json.return_value = {
            'MIT': 'MIT License',
            'Apache-2.0': 'Apache License 2.0',
            'GPL-3.0': 'GNU GPL v3.0'
        }
        
        License.get(is_print=True)
        
        captured = capsys.readouterr()
        assert 'MIT' in captured.out
        assert 'SPDX Code' in captured.out
        
    @patch('permitcheck.license.update.read_json')
    @patch('permitcheck.license.update.os.path.isfile')
    def test_get_custom_file(self, mock_isfile, mock_read_json):
        """Test getting licenses from custom file."""
        mock_isfile.return_value = True
        mock_read_json.return_value = {'MIT': 'MIT License'}
        
        result = License.get(license_file='/custom/path.json', is_print=False)
        
        mock_read_json.assert_called_with('/custom/path.json')
        assert isinstance(result, set)


class TestLicenseCreateSpdxSet:
    """Test License._create_spdx_set functionality."""
    
    @patch('permitcheck.license.update.read_json')
    @patch('permitcheck.license.update.os.path.isfile')
    def test_create_spdx_set_simple(self, mock_isfile, mock_read_json):
        """Test creating SPDX set with simple licenses."""
        mock_isfile.return_value = True
        mock_read_json.return_value = {
            'MIT': 'MIT License',
            'Apache-2.0': 'Apache License 2.0'
        }
        
        result = License.get(is_print=False)
        
        # Should contain license IDs and their prefixes
        assert 'MIT' in result
        assert 'Apache' in result
        assert 'Apache-2.0' in result


class TestMain:
    """Test main function."""
    
    @patch('permitcheck.license.update.JSON.save')
    @patch('permitcheck.license.update.License.fetch')
    def test_main_execution(self, mock_fetch, mock_save):
        """Test main function execution."""
        mock_fetch.return_value = iter([
            [{'MIT': 'MIT License'}]
        ])
        
        main()
        
        mock_fetch.assert_called_once()
        mock_save.assert_called_once()
        
    @patch('permitcheck.license.update.JSON.save')
    @patch('permitcheck.license.update.License.fetch')
    def test_main_saves_fetched_licenses(self, mock_fetch, mock_save):
        """Test that main saves fetched licenses."""
        licenses_data = iter([
            [
                {'MIT': 'MIT License'},
                {'Apache-2.0': 'Apache License 2.0'}
            ]
        ])
        mock_fetch.return_value = licenses_data
        
        main()
        
        # JSON.save should be called with the fetched licenses
        assert mock_save.call_count == 1


class TestXMLEdgeCases:
    """Test edge cases for XML functionality."""
    
    def test_save_empty_licenses(self, tmp_path):
        """Test saving empty license list."""
        licenses_iter = []
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            XML.save(licenses_iter, 'empty.xml')
        
        xml_file = tmp_path / 'empty.xml'
        assert xml_file.exists()
        
    def test_save_nested_empty(self, tmp_path):
        """Test saving with nested empty lists."""
        licenses_iter = [[]]
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            XML.save(licenses_iter, 'nested_empty.xml')
        
        xml_file = tmp_path / 'nested_empty.xml'
        assert xml_file.exists()


class TestJSONEdgeCases:
    """Test edge cases for JSON functionality."""
    
    def test_save_empty_licenses(self, tmp_path):
        """Test saving empty license list."""
        licenses_iter = []
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            JSON.save(licenses_iter, 'empty.json')
        
        json_file = tmp_path / 'empty.json'
        assert json_file.exists()
        
        with open(json_file) as f:
            data = json.load(f)
        
        assert data == {}
        
    def test_save_overwrite_existing(self, tmp_path):
        """Test that saving overwrites existing file."""
        licenses_iter1 = [[{'MIT': 'MIT License'}]]
        licenses_iter2 = [[{'Apache-2.0': 'Apache License 2.0'}]]
        
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            JSON.save(licenses_iter1, 'overwrite.json')
            JSON.save(licenses_iter2, 'overwrite.json')
        
        json_file = tmp_path / 'overwrite.json'
        with open(json_file) as f:
            data = json.load(f)
        
        # Should only have second license
        assert 'Apache-2.0' in data
        assert 'MIT' not in data


class TestLicenseFetchEdgeCases:
    """Test edge cases for License.fetch."""
    
    @patch('permitcheck.utils.get_lines')
    @patch('permitcheck.license.update.requests.get')
    def test_fetch_connection_error(self, mock_get, mock_get_lines):
        """Test handling connection errors."""
        mock_get_lines.return_value = ['https://example.com/licenses']
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        # Should handle exception
        try:
            result = list(License.fetch())
        except requests.exceptions.ConnectionError:
            pass


class TestIntegration:
    """Integration tests for update module."""
    
    @patch('permitcheck.utils.get_lines')
    @patch('permitcheck.license.update.requests.get')
    def test_full_workflow(self, mock_get, mock_get_lines, tmp_path):
        """Test complete workflow from fetch to save."""
        mock_get_lines.return_value = ['https://example.com/licenses']
        utils
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'licenses': [
                {'licenseId': 'MIT', 'name': 'MIT License'},
                {'licenseId': 'Apache-2.0', 'name': 'Apache License 2.0'}
            ]
        }
        mock_get.return_value = mock_response
        
        # Fetch licenses
        licenses = License.fetch()
        
        # Save to JSON
        with patch('permitcheck.license.update.os.path.dirname', return_value=str(tmp_path)):
            JSON.save(licenses, 'integration.json')
        
        # Verify file
        json_file = tmp_path / 'integration.json'
        assert json_file.exists()
        
        with open(json_file) as f:
            data = json.load(f)
        
        assert 'MIT' in data
        assert 'Apache-2.0' in data
