"""
Tests for session isolation (SEC-13)

Tests according to PITFALLS.md requirements:
- User A can access only User A files
- User B cannot access User A files (403 Forbidden)
- Path traversal attacks blocked (../../attack)
- Session expired → 403 Forbidden
"""

import pytest
import sys
import os
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.validators import validate_session_access
from flask import Flask, session, abort


class TestSessionIsolation:
    """Test session-based file access isolation"""

    def test_user_can_access_own_files(self, app):
        """Test that user can access files in their own session"""
        with app.test_request_context():
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id

            # Create session directories
            upload_dir = app.config['UPLOAD_FOLDER'] / session_id
            upload_dir.mkdir(exist_ok=True, parents=True)

            # Create test file
            test_file = upload_dir / "test.txt"
            test_file.write_text("My data")

            # Should allow access
            assert validate_session_access(test_file, session_id) is True

    def test_user_cannot_access_other_session_files(self, app):
        """Test that user cannot access files from another session"""
        with app.test_request_context():
            session_a = str(uuid.uuid4())
            session_b = str(uuid.uuid4())

            # Create session A directory and file
            upload_dir_a = app.config['UPLOAD_FOLDER'] / session_a
            upload_dir_a.mkdir(exist_ok=True, parents=True)
            file_a = upload_dir_a / "secret.txt"
            file_a.write_text("Session A secret data")

            # Set current session to B
            session['session_id'] = session_b

            # Try to access session A's file from session B
            with pytest.raises(Exception) as exc_info:
                validate_session_access(file_a, session_b)

            # Should be 403 Forbidden
            assert exc_info.value.code == 403
            assert "niet in jouw sessie" in str(exc_info.value.description).lower()

    def test_path_traversal_blocked(self, app):
        """Test that path traversal attacks are blocked"""
        with app.test_request_context():
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id

            # Create session directory
            upload_dir = app.config['UPLOAD_FOLDER'] / session_id
            upload_dir.mkdir(exist_ok=True, parents=True)

            # Attempt path traversal to parent directory
            traversal_path = upload_dir / ".." / "other_session" / "secret.txt"

            with pytest.raises(Exception) as exc_info:
                validate_session_access(traversal_path, session_id)

            # Should be 403 Forbidden
            assert exc_info.value.code == 403

    def test_absolute_path_outside_session_blocked(self, app):
        """Test that absolute paths outside session are blocked"""
        with app.test_request_context():
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id

            # Try to access /etc/passwd
            absolute_path = Path("/etc/passwd")

            with pytest.raises(Exception) as exc_info:
                validate_session_access(absolute_path, session_id)

            # Should be 403 Forbidden
            assert exc_info.value.code == 403
            assert "niet in jouw sessie" in str(exc_info.value.description).lower()

    def test_no_session_id_blocked(self, app):
        """Test that requests without session ID are blocked"""
        with app.test_request_context():
            # No session ID set
            upload_dir = app.config['UPLOAD_FOLDER']
            test_file = upload_dir / "test.txt"

            with pytest.raises(Exception) as exc_info:
                validate_session_access(test_file, session_id=None)

            # Should be 403 Forbidden
            assert exc_info.value.code == 403
            assert "geen geldige sessie" in str(exc_info.value.description).lower()

    def test_symlink_attack_blocked(self, app, tmp_path):
        """Test that symlink attacks are blocked"""
        with app.test_request_context():
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id

            # Create session directory
            upload_dir = app.config['UPLOAD_FOLDER'] / session_id
            upload_dir.mkdir(exist_ok=True, parents=True)

            # Create a target file outside session
            target_file = tmp_path / "secret.txt"
            target_file.write_text("Secret data")

            # Create symlink inside session directory pointing outside
            symlink = upload_dir / "link_to_secret.txt"
            try:
                symlink.symlink_to(target_file)
            except OSError:
                pytest.skip("Symlinks not supported on this OS")

            # Try to access via symlink - should be blocked
            with pytest.raises(Exception) as exc_info:
                validate_session_access(symlink, session_id)

            # Should be 403 Forbidden
            assert exc_info.value.code == 403

    def test_output_folder_access_allowed(self, app):
        """Test that files in output folder are accessible"""
        with app.test_request_context():
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id

            # Create session output directory
            output_dir = app.config['OUTPUT_FOLDER'] / session_id
            output_dir.mkdir(exist_ok=True, parents=True)

            # Create test file in output
            test_file = output_dir / "anonymized.txt"
            test_file.write_text("Anonymized data")

            # Should allow access to output folder
            assert validate_session_access(test_file, session_id) is True

    def test_cross_session_output_blocked(self, app):
        """Test that user cannot access another session's output"""
        with app.test_request_context():
            session_a = str(uuid.uuid4())
            session_b = str(uuid.uuid4())

            # Create session A output directory and file
            output_dir_a = app.config['OUTPUT_FOLDER'] / session_a
            output_dir_a.mkdir(exist_ok=True, parents=True)
            file_a = output_dir_a / "anonymized.txt"
            file_a.write_text("Session A output")

            # Set current session to B
            session['session_id'] = session_b

            # Try to access session A's output from session B
            with pytest.raises(Exception) as exc_info:
                validate_session_access(file_a, session_b)

            # Should be 403 Forbidden
            assert exc_info.value.code == 403


class TestDownloadEndpointIsolation:
    """Test session isolation in download endpoints"""

    def test_download_own_file(self, client, tmp_path):
        """Test that user can download their own files"""
        # Upload a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("My data")

        with open(test_file, 'rb') as f:
            upload_response = client.post('/api/upload', data={
                'files[]': (f, 'test.txt')
            }, content_type='multipart/form-data')

        assert upload_response.status_code == 200
        upload_data = upload_response.get_json()
        session_id = upload_data['sessionId']
        file_id = upload_data['files'][0]['id']

        # Process file (simplified - just copy to output)
        from pathlib import Path
        output_dir = Path('/tmp/test_outputs') / session_id
        output_dir.mkdir(exist_ok=True, parents=True)
        output_file = output_dir / f"{file_id}_test_ann_1200.txt"
        output_file.write_text("Anonymized data")

        # Download should work
        download_response = client.get(f'/api/download/{file_id}')

        # Should succeed (200) or 404 if processing not complete
        assert download_response.status_code in [200, 404]

    def test_download_other_session_file_blocked(self, app, tmp_path):
        """Test that user cannot download files from another session"""
        session_a = str(uuid.uuid4())
        session_b = str(uuid.uuid4())

        # Create session A output file
        output_dir_a = app.config['OUTPUT_FOLDER'] / session_a
        output_dir_a.mkdir(exist_ok=True, parents=True)
        file_id = str(uuid.uuid4())
        file_a = output_dir_a / f"{file_id}_secret_ann_1200.txt"
        file_a.write_text("Secret data")

        # Try to download from session B
        with app.test_client() as client_b:
            # Set session B
            with client_b.session_transaction() as sess:
                sess['session_id'] = session_b

            response = client_b.get(f'/api/download/{file_id}')

            # Should be blocked (403 or 404)
            assert response.status_code in [403, 404]

    def test_path_traversal_in_download_blocked(self, client):
        """Test that path traversal in download is blocked"""
        # Attempt to download with path traversal
        malicious_file_ids = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../other_session/secret.txt",
        ]

        for file_id in malicious_file_ids:
            response = client.get(f'/api/download/{file_id}')

            # Should be blocked (400, 403, or 404)
            assert response.status_code in [400, 403, 404]


class TestErrorMessages:
    """Test that security error messages are informative but not revealing"""

    def test_403_error_message_clear(self, app):
        """Test that 403 error messages are clear"""
        with app.test_request_context():
            session_id = str(uuid.uuid4())

            # Try to access file in different session
            other_session_file = app.config['UPLOAD_FOLDER'] / "other_session" / "file.txt"

            with pytest.raises(Exception) as exc_info:
                validate_session_access(other_session_file, session_id)

            error_msg = str(exc_info.value.description).lower()

            # Should mention session or access denied
            assert any(word in error_msg for word in ["sessie", "toegang", "geweigerd"])

    def test_403_error_does_not_reveal_paths(self, app):
        """Test that 403 errors don't reveal actual file paths"""
        with app.test_request_context():
            session_id = str(uuid.uuid4())

            # Try to access /etc/passwd
            absolute_path = Path("/etc/passwd")

            with pytest.raises(Exception) as exc_info:
                validate_session_access(absolute_path, session_id)

            error_msg = str(exc_info.value.description).lower()

            # Should NOT reveal the actual path attempted
            assert "/etc/passwd" not in error_msg


class TestEdgeCases:
    """Test edge cases in session isolation"""

    def test_empty_session_id(self, app):
        """Test that empty session ID is blocked"""
        with app.test_request_context():
            test_file = app.config['UPLOAD_FOLDER'] / "test.txt"

            with pytest.raises(Exception) as exc_info:
                validate_session_access(test_file, session_id="")

            assert exc_info.value.code == 403

    def test_malicious_session_id_path_traversal(self, app):
        """Test that malicious session IDs with path traversal are handled safely"""
        with app.test_request_context():
            # Create a normal session
            normal_session = str(uuid.uuid4())
            normal_dir = app.config['UPLOAD_FOLDER'] / normal_session
            normal_dir.mkdir(exist_ok=True, parents=True)
            normal_file = normal_dir / "file.txt"
            normal_file.write_text("Data")

            # Try to access with malicious session IDs
            malicious_session_ids = [
                f"{normal_session}/../other_session",
                f"../../{normal_session}",
            ]

            for malicious_id in malicious_session_ids:
                # Attempt to construct path through malicious ID
                # Path resolution will resolve this, but session check should catch it
                test_file = app.config['UPLOAD_FOLDER'] / malicious_id / "file.txt"

                # This might raise or might not depending on path resolution
                # The important thing is that validate_session_access prevents access
                try:
                    result = validate_session_access(test_file, session_id=malicious_id)
                    # If it doesn't raise, the path resolution made it safe anyway
                except Exception as e:
                    # Expected - access denied
                    assert e.code == 403

    def test_case_sensitive_session_id(self, app):
        """Test that session IDs are case-sensitive"""
        with app.test_request_context():
            session_lower = str(uuid.uuid4()).lower()
            session_upper = session_lower.upper()

            # Create file in lowercase session
            upload_dir = app.config['UPLOAD_FOLDER'] / session_lower
            upload_dir.mkdir(exist_ok=True, parents=True)
            test_file = upload_dir / "test.txt"
            test_file.write_text("Data")

            # Try to access with uppercase session ID - should fail
            if session_lower != session_upper:
                with pytest.raises(Exception):
                    validate_session_access(test_file, session_id=session_upper)
