"""
Reverse Routes - De-Anonymization

Blueprint voor het terugdraaien van anonimisatie met mapping.json bestanden.
"""

import uuid
import shutil
from flask import Blueprint, request, jsonify, current_app, send_file
from anonymizer.reverse_anonymizer import AnonymizationMapping, ReverseAnonymizer
from utils.encryption import SecureMappingStorage, is_encrypted_mapping, load_plaintext_mapping
from utils.audit import AuditLogger
from cryptography.fernet import InvalidToken

reverse_bp = Blueprint('reverse', __name__)


@reverse_bp.route('/reverse', methods=['POST'])
def reverse_anonymization():
    """
    De-anonimiseer een bestand met een mapping.json
    Accepteert: anonymized_file en mapping_file
    """
    if 'anonymized_file' not in request.files or 'mapping_file' not in request.files:
        return jsonify({'error': 'Beide bestanden zijn vereist'}), 400

    anonymized_file = request.files['anonymized_file']
    mapping_file = request.files['mapping_file']

    if not anonymized_file.filename or not mapping_file.filename:
        return jsonify({'error': 'Bestandsnamen zijn leeg'}), 400

    # Valideer mapping file
    if not mapping_file.filename.endswith('.json'):
        return jsonify({'error': 'Mapping bestand moet een .json bestand zijn'}), 400

    # Maak tijdelijke directory voor deze operatie
    temp_id = str(uuid.uuid4())[:8]
    temp_dir = current_app.config['UPLOAD_FOLDER'] / f"reverse_{temp_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Initialiseer audit logger
    audit_logger = AuditLogger(temp_id, temp_dir)

    try:
        # Sla bestanden op
        anonymized_path = temp_dir / anonymized_file.filename
        mapping_path = temp_dir / mapping_file.filename

        anonymized_file.save(anonymized_path)
        mapping_file.save(mapping_path)

        # Log start van reverse operation
        file_ext = anonymized_path.suffix.lower().lstrip('.')
        audit_logger.log_reverse_start(anonymized_file.filename, file_ext)

        # Laad mapping - detect encrypted vs plaintext
        mapping_encrypted = is_encrypted_mapping(mapping_path)

        if mapping_encrypted:
            # Encrypted mapping - gebruik SecureMappingStorage
            try:
                # Check if encryption key was also uploaded
                # (Should be in same directory as mapping when user uploads ZIP)
                encryption_key_path = temp_dir / '.encryption_key'

                # If user uploaded from original ZIP, key is included
                # If user uploads mapping separately, key might be in request.files
                if 'encryption_key' in request.files:
                    key_file = request.files['encryption_key']
                    key_file.save(encryption_key_path)

                # Check if key exists
                if not encryption_key_path.exists():
                    return jsonify({
                        'error': 'Encrypted mapping vereist .encryption_key bestand. '
                                'Upload de volledige ZIP met mapping + key, of upload key apart.'
                    }), 400

                # Voor encrypted mappings hebben we session_id nodig
                # Probeer dit uit de filename te halen (mapping_{session_id}.json)
                if mapping_file.filename.startswith('mapping_') and mapping_file.filename.endswith('.json'):
                    session_id_from_file = mapping_file.filename[8:-5]  # Extract session_id
                else:
                    session_id_from_file = temp_id  # Fallback naar temp_id

                secure_storage = SecureMappingStorage(session_id_from_file)
                mapping_dict = secure_storage.load_mapping(mapping_path.parent, filename=mapping_path.name)
                mapping = AnonymizationMapping.from_dict(mapping_dict)

                # Log successful encrypted load
                audit_logger.log_mapping_loaded(len(mapping.mappings), encrypted=True)

            except InvalidToken:
                return jsonify({
                    'error': 'Kan encrypted mapping niet decrypten. Encryption key is incorrect of corrupt.'
                }), 400
            except Exception as e:
                # Fallback to plaintext if decryption fails
                try:
                    mapping_dict = load_plaintext_mapping(mapping_path)
                    mapping = AnonymizationMapping.from_dict(mapping_dict)
                    audit_logger.log_mapping_loaded(len(mapping.mappings), encrypted=False)
                except Exception:
                    raise e  # Re-raise original error
        else:
            # Plaintext mapping (backwards compatibility)
            mapping = AnonymizationMapping.from_file(mapping_path)
            audit_logger.log_mapping_loaded(len(mapping.mappings), encrypted=False)

        # Bepaal output path
        output_filename = f"deanon_{anonymized_file.filename}"
        output_path = temp_dir / output_filename

        # De-anonimiseer op basis van bestandstype
        if file_ext == '.txt':
            ReverseAnonymizer.deanonymize_txt_file(anonymized_path, output_path, mapping)
        elif file_ext == '.docx':
            ReverseAnonymizer.deanonymize_docx_file(anonymized_path, output_path, mapping)
        elif file_ext == '.xlsx':
            ReverseAnonymizer.deanonymize_excel_file(anonymized_path, output_path, mapping)
        elif file_ext == '.csv':
            ReverseAnonymizer.deanonymize_csv_file(anonymized_path, output_path, mapping)
        else:
            audit_logger.log_reverse_error(anonymized_file.filename, f'Unsupported file type: {file_ext}')
            return jsonify({'error': f'Bestandstype {file_ext} wordt niet ondersteund'}), 400

        # Log successful completion
        audit_logger.log_reverse_complete(output_filename, mappings_applied=len(mapping.mappings))

        # Return het de-geanonimiseerde bestand
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        # Log error
        audit_logger.log_reverse_error(anonymized_file.filename, str(e))
        return jsonify({'error': f'Fout bij de-anonimiseren: {str(e)}'}), 500

    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
