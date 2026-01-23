"""
Download Routes - File Download Endpoints

Blueprint voor downloads van geanonimiseerde bestanden, mappings en ZIP archives.
"""

import zipfile
from io import BytesIO
from flask import Blueprint, jsonify, session, current_app, send_file
from utils.validators import validate_session_access

download_bp = Blueprint('download', __name__)


@download_bp.route('/download/<file_id>')
def download_file(file_id):
    """
    Download geanonimiseerd bestand
    """
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'Geen actieve sessie'}), 400

    output_dir = current_app.config['OUTPUT_FOLDER'] / session_id

    # Zoek bestand met deze ID
    for filepath in output_dir.glob(f"{file_id}_*"):
        # SEC-13: Validate session access (prevent path traversal)
        validate_session_access(filepath, session_id)

        # Verwijder file_id prefix
        # Formaat: {file_id}_{base_name}_anoniem_{timestamp}.{ext} -> {base_name}_anoniem_{timestamp}.{ext}
        clean_name = filepath.name.replace(f"{file_id}_", "")
        return send_file(
            filepath,
            as_attachment=True,
            download_name=clean_name
        )

    return jsonify({'error': 'Bestand niet gevonden'}), 404


@download_bp.route('/download-mapping/<mapping_id>')
def download_mapping(mapping_id):
    """
    Download mapping.json bestand voor reversible anonymization
    """
    session_id = session.get('session_id')
    if not session_id or session_id != mapping_id:
        return jsonify({'error': 'Geen toegang tot mapping'}), 403

    output_dir = current_app.config['OUTPUT_FOLDER'] / session_id
    mapping_file = output_dir / f"mapping_{session_id}.json"

    if not mapping_file.exists():
        return jsonify({'error': 'Mapping niet gevonden'}), 404

    # SEC-13: Validate session access
    validate_session_access(mapping_file, session_id)

    return send_file(
        mapping_file,
        mimetype='application/json',
        as_attachment=True,
        download_name='anonimisatie_mapping.json'
    )


@download_bp.route('/download-all')
def download_all():
    """
    Download alle geanonimiseerde bestanden als ZIP
    """
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'Geen actieve sessie'}), 400

    output_dir = current_app.config['OUTPUT_FOLDER'] / session_id
    if not output_dir.exists() or not any(output_dir.iterdir()):
        return jsonify({'error': 'Geen bestanden om te downloaden'}), 404

    # SEC-13: Validate session access to output directory
    # This prevents accessing other sessions' files via directory listing
    validate_session_access(output_dir, session_id)

    # Maak ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filepath in output_dir.iterdir():
            if filepath.is_file():
                filename = filepath.name

                # Skip hidden files like .encryption_key en .meta.json
                if filename.startswith('.') or filename.endswith('.meta.json'):
                    continue

                # Bepaal clean name voor in ZIP
                if filename.startswith('mapping_'):
                    # Mapping bestand: mapping_{session_id}.json -> anonimisatie_mapping.json
                    clean_name = 'anonimisatie_mapping.json'

                    # Include encryption key WITH mapping for encrypted mappings
                    # Key moet in zelfde ZIP voor reverse anonymization
                    encryption_key_path = output_dir / '.encryption_key'
                    if encryption_key_path.exists():
                        zip_file.write(encryption_key_path, arcname='.encryption_key')

                elif '_ann_' in filename:
                    # Geanonimiseerd bestand: {uuid}_{name}_ann_{HHMM}.{ext} -> {name}_ann_{HHMM}.{ext}
                    # Verwijder UUID prefix (eerste deel tot eerste underscore)
                    clean_name = filename.split('_', 1)[1]
                else:
                    # Fallback voor oude formaat of andere bestanden
                    # Verwijder UUID als die er is
                    parts = filename.split('_', 1)
                    if len(parts) == 2:
                        clean_name = parts[1]
                    else:
                        clean_name = filename

                zip_file.write(filepath, arcname=clean_name)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='geanonimiseerde_bestanden.zip'
    )
