"""
Tests for file size warnings and limits (SEC-11)

Tests according to PITFALLS.md requirements:
- 5MB - 50MB: Warning message about processing time
- >50MB: Reject with 413 error
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestFileSizeWarnings:
    """Test file size warning thresholds"""

    def test_small_file_no_warning(self, client, tmp_path):
        """Test that small files (<5MB) have no warnings"""
        # Create 1MB file
        small_file = tmp_path / "small.txt"
        small_file.write_text("x" * (1 * 1024 * 1024))  # 1MB

        with open(small_file, 'rb') as f:
            response = client.post('/api/upload', data={
                'files[]': (f, 'small.txt')
            }, content_type='multipart/form-data')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['files']) == 1

        # Should not have warnings
        file_info = data['files'][0]
        assert 'warnings' not in file_info or len(file_info.get('warnings', [])) == 0

    def test_medium_file_warning(self, client, tmp_path):
        """Test that medium files (5-50MB) show warning"""
        # Create 6MB file
        medium_file = tmp_path / "medium.txt"
        medium_file.write_text("x" * (6 * 1024 * 1024))  # 6MB

        with open(medium_file, 'rb') as f:
            response = client.post('/api/upload', data={
                'files[]': (f, 'medium.txt')
            }, content_type='multipart/form-data')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # Should have size warning
        file_info = data['files'][0]
        assert 'warnings' in file_info
        assert len(file_info['warnings']) > 0

        # Check warning mentions size and time
        warning_text = ' '.join(file_info['warnings'])
        assert 'groot bestand' in warning_text.lower() or 'mb' in warning_text.lower()
        assert any(time_word in warning_text.lower() for time_word in ['seconden', 'duren', 'tijd'])

    def test_large_file_rejected(self, client, tmp_path):
        """Test that large files (>50MB) are rejected"""
        # Create 51MB file
        large_file = tmp_path / "large.txt"
        # Write in chunks to avoid memory issues
        with open(large_file, 'wb') as f:
            chunk = b"x" * (1024 * 1024)  # 1MB chunk
            for _ in range(51):
                f.write(chunk)

        with open(large_file, 'rb') as f:
            response = client.post('/api/upload', data={
                'files[]': (f, 'large.txt')
            }, content_type='multipart/form-data')

        # File should be rejected
        data = response.get_json()

        # Should have errors
        assert 'errors' in data or not data.get('success')

        if 'errors' in data:
            error_text = str(data['errors'])
            assert '50' in error_text or 'groot' in error_text.lower()

    def test_warning_threshold_boundary(self, client, tmp_path):
        """Test exactly at warning threshold (5MB)"""
        # Create exactly 5MB file
        threshold_file = tmp_path / "threshold.txt"
        threshold_file.write_text("x" * (5 * 1024 * 1024))  # Exactly 5MB

        with open(threshold_file, 'rb') as f:
            response = client.post('/api/upload', data={
                'files[]': (f, 'threshold.txt')
            }, content_type='multipart/form-data')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # At exact threshold - implementation may or may not warn
        # Either is acceptable

    def test_hard_limit_boundary(self, client, tmp_path):
        """Test exactly at hard limit (50MB)"""
        # Create exactly 50MB file
        limit_file = tmp_path / "limit.txt"
        with open(limit_file, 'wb') as f:
            chunk = b"x" * (1024 * 1024)
            for _ in range(50):
                f.write(chunk)

        with open(limit_file, 'rb') as f:
            response = client.post('/api/upload', data={
                'files[]': (f, 'limit.txt')
            }, content_type='multipart/form-data')

        # At exact 50MB - should be accepted (limit is >50MB)
        data = response.get_json()
        assert response.status_code == 200


class TestErrorMessages:
    """Test that error messages for size limits are clear"""

    def test_size_error_mentions_limit(self, client, tmp_path):
        """Test that size error mentions the 50MB limit"""
        # Create 51MB file
        large_file = tmp_path / "toolarge.txt"
        with open(large_file, 'wb') as f:
            chunk = b"x" * (1024 * 1024)
            for _ in range(51):
                f.write(chunk)

        with open(large_file, 'rb') as f:
            response = client.post('/api/upload', data={
                'files[]': (f, 'toolarge.txt')
            }, content_type='multipart/form-data')

        data = response.get_json()

        # Error should mention 50MB limit
        error_text = str(data.get('errors', ''))
        assert '50' in error_text

    def test_size_error_actionable(self, client, tmp_path):
        """Test that size error suggests solution"""
        # Create 51MB file
        large_file = tmp_path / "huge.txt"
        with open(large_file, 'wb') as f:
            chunk = b"x" * (1024 * 1024)
            for _ in range(51):
                f.write(chunk)

        with open(large_file, 'rb') as f:
            response = client.post('/api/upload', data={
                'files[]': (f, 'huge.txt')
            }, content_type='multipart/form-data')

        data = response.get_json()

        # Error should suggest action (split or contact)
        error_text = str(data.get('errors', '')).lower()
        assert 'split' in error_text or 'contact' in error_text or 'neem contact' in error_text


class TestWarningFormat:
    """Test warning message format and content"""

    def test_warning_shows_actual_size(self, client, tmp_path):
        """Test that warning shows the actual file size"""
        # Create 10MB file
        file_10mb = tmp_path / "file10.txt"
        file_10mb.write_text("x" * (10 * 1024 * 1024))

        with open(file_10mb, 'rb') as f:
            response = client.post('/api/upload', data={
                'files[]': (f, 'file10.txt')
            }, content_type='multipart/form-data')

        data = response.get_json()
        file_info = data['files'][0]

        if 'warnings' in file_info and file_info['warnings']:
            warning = ' '.join(file_info['warnings'])
            # Should mention size around 10MB
            assert '10' in warning or '9.' in warning  # Might be 9.x MB due to rounding

    def test_warning_estimates_time(self, client, tmp_path):
        """Test that warning estimates processing time"""
        # Create 15MB file
        file_15mb = tmp_path / "file15.txt"
        file_15mb.write_text("x" * (15 * 1024 * 1024))

        with open(file_15mb, 'rb') as f:
            response = client.post('/api/upload', data={
                'files[]': (f, 'file15.txt')
            }, content_type='multipart/form-data')

        data = response.get_json()
        file_info = data['files'][0]

        if 'warnings' in file_info and file_info['warnings']:
            warning = ' '.join(file_info['warnings']).lower()
            # Should mention time estimate
            assert 'seconden' in warning or 'duren' in warning


class TestMultipleFiles:
    """Test size warnings with multiple files"""

    def test_multiple_files_individual_warnings(self, client, tmp_path):
        """Test that each file gets its own size warning"""
        # Create small and large file
        small = tmp_path / "small.txt"
        large = tmp_path / "large.txt"
        small.write_text("x" * (1 * 1024 * 1024))  # 1MB
        large.write_text("x" * (10 * 1024 * 1024))  # 10MB

        with open(small, 'rb') as f1, open(large, 'rb') as f2:
            response = client.post('/api/upload', data={
                'files[]': [(f1, 'small.txt'), (f2, 'large.txt')]
            }, content_type='multipart/form-data')

        data = response.get_json()
        assert len(data['files']) == 2

        # Small file should not have warning
        small_file = next(f for f in data['files'] if f['originalName'] == 'small.txt')
        assert 'warnings' not in small_file or len(small_file.get('warnings', [])) == 0

        # Large file should have warning
        large_file = next(f for f in data['files'] if f['originalName'] == 'large.txt')
        assert 'warnings' in large_file and len(large_file['warnings']) > 0

    def test_mixed_valid_invalid_sizes(self, client, tmp_path):
        """Test mix of valid and oversized files"""
        valid = tmp_path / "valid.txt"
        invalid = tmp_path / "invalid.txt"

        valid.write_text("x" * (5 * 1024 * 1024))  # 5MB - OK

        # Create 51MB oversized file
        with open(invalid, 'wb') as f:
            chunk = b"x" * (1024 * 1024)
            for _ in range(51):
                f.write(chunk)

        with open(valid, 'rb') as f1, open(invalid, 'rb') as f2:
            response = client.post('/api/upload', data={
                'files[]': [(f1, 'valid.txt'), (f2, 'invalid.txt')]
            }, content_type='multipart/form-data')

        data = response.get_json()

        # Should be partial success
        assert 'files' in data
        assert 'errors' in data

        # Valid file should be uploaded
        assert len(data['files']) == 1
        assert data['files'][0]['originalName'] == 'valid.txt'

        # Invalid file should be in errors
        assert len(data['errors']) == 1
        assert 'invalid.txt' in str(data['errors'])
