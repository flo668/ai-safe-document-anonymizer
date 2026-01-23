"""
Upload Routes - File Upload en Session Cleanup

Blueprint voor file upload en sessie cleanup endpoints.
"""

import json
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename

try:
    from utils.validation import validate_file_upload, validate_session_id, sanitize_filename, validate_path_traversal
    from utils.validators import validate_file
except ImportError:
    # Fallback als utils nog niet in path zit
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.validation import validate_file_upload, validate_session_id, sanitize_filename, validate_path_traversal
    from utils.validators import validate_file

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/upload', methods=['POST'])
def upload_files():
    """
    File upload endpoint
    Accepts: multipart/form-data met files[]
    Returns: JSON met file IDs en metadata
    """
    if 'files[]' not in request.files:
        return jsonify({'error': 'Geen bestanden gevonden'}), 400

    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        return jsonify({'error': 'Geen bestanden geselecteerd'}), 400

    # Create session directory
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id

    session_dir = current_app.config['UPLOAD_FOLDER'] / session_id
    session_dir.mkdir(exist_ok=True)

    uploaded_files = []
    errors = []

    for file in files:
        # Validate file upload (security check)
        is_valid, error_msg = validate_file_upload(file, check_mime=False)
        if not is_valid:
            errors.append({'filename': file.filename, 'error': error_msg})
            continue

        # Sanitize filename
        filename = sanitize_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_ext = filename.rsplit('.', 1)[1].lower()

        # Save file
        filepath = session_dir / f"{file_id}.{file_ext}"
        file.save(filepath)

        # Validate file (check for corruption, password protection, etc.)
        validation_result = validate_file(filepath)

        if not validation_result["valid"]:
            # Remove invalid file
            filepath.unlink()
            errors.append({
                'filename': filename,
                'error': validation_result["error"]
            })
            continue

        # Add file size warning if file is large (5MB - 50MB)
        file_size = filepath.stat().st_size
        size_warning_threshold = current_app.config.get('FILE_SIZE_WARNING_THRESHOLD', 5 * 1024 * 1024)
        if file_size > size_warning_threshold:
            size_mb = file_size / (1024 * 1024)
            estimated_time = "10-30 seconden" if file_size < 20 * 1024 * 1024 else "30-60 seconden"
            validation_result.setdefault("warnings", []).append(
                f"Groot bestand ({size_mb:.1f}MB) - verwerking kan {estimated_time} duren"
            )

        # Sla originele bestandsnaam op in metadata bestand
        metadata_file = session_dir / f"{file_id}.meta.json"
        metadata = {
            'originalName': filename
        }

        # Add warnings if any
        if validation_result.get("warnings"):
            metadata['warnings'] = validation_result["warnings"]

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f)

        file_info = {
            'id': file_id,
            'originalName': filename,
            'fileType': _get_file_type(file_ext),
            'size': filepath.stat().st_size,
            'status': 'uploaded'
        }

        # Include warnings in response
        if validation_result.get("warnings"):
            file_info['warnings'] = validation_result["warnings"]

        uploaded_files.append(file_info)

    response = {
        'success': True,
        'files': uploaded_files,
        'sessionId': session_id
    }

    # Include errors if any
    if errors:
        response['errors'] = errors
        response['partialSuccess'] = len(uploaded_files) > 0

    return jsonify(response)


@upload_bp.route('/cleanup', methods=['POST'])
def cleanup_session():
    """
    Cleanup sessie bestanden
    """
    session_id = session.get('session_id')
    if session_id:
        _cleanup_session_files(session_id)
        session.pop('session_id', None)

    return jsonify({'success': True})


# Helper functies (tijdelijk - zullen later naar utils verplaatst worden)

def _allowed_file(filename):
    """Check of bestand toegestaan is"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'txt', 'docx', 'xlsx', 'csv', 'pdf', 'md'}


def _get_file_type(extension):
    """Bepaal file type van extensie"""
    ext_map = {
        'txt': 'txt',
        'md': 'txt',  # Markdown behandelen als platte tekst
        'docx': 'docx',
        'xlsx': 'xlsx',
        'csv': 'xlsx',  # CSV behandelen als Excel
        'pdf': 'pdf'
    }
    return ext_map.get(extension, 'unknown')


def _cleanup_session_files(session_id):
    """Verwijder alle bestanden voor een sessie"""
    import shutil

    # Validate session ID to prevent path traversal
    if not validate_session_id(session_id):
        return  # Silently fail on invalid session ID

    session_dir = current_app.config['UPLOAD_FOLDER'] / session_id
    output_dir = current_app.config['OUTPUT_FOLDER'] / session_id

    # Extra check: ensure paths are within allowed directories
    if not validate_path_traversal(session_dir, current_app.config['UPLOAD_FOLDER']):
        return

    if not validate_path_traversal(output_dir, current_app.config['OUTPUT_FOLDER']):
        return

    if session_dir.exists():
        shutil.rmtree(session_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
