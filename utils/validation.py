"""
Security Validation Module

Bevat functies voor input validatie, file upload security en session management.
"""

import re
import uuid
from pathlib import Path
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage

# python-magic is optioneel
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


# Allowed MIME types mapping
ALLOWED_MIME_TYPES = {
    'text/plain': ['txt', 'md'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['xlsx'],
    'text/csv': ['csv'],
    'application/pdf': ['pdf']
}

# Maximum file sizes per type (in bytes)
# SEC-11: Global 50MB hard limit for all file types
MAX_FILE_SIZES = {
    'txt': 50 * 1024 * 1024,   # 50MB
    'md': 50 * 1024 * 1024,    # 50MB
    'docx': 50 * 1024 * 1024,  # 50MB
    'xlsx': 50 * 1024 * 1024,  # 50MB (was 100MB, reduced for safety)
    'csv': 50 * 1024 * 1024,   # 50MB (was 100MB, reduced for safety)
    'pdf': 50 * 1024 * 1024    # 50MB
}


def validate_file_upload(file: FileStorage, check_mime: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Valideer uploaded file op extensie, MIME type en grootte.

    Args:
        file: Werkzeug FileStorage object
        check_mime: Of MIME type gevalideerd moet worden (vereist python-magic)

    Returns:
        Tuple van (is_valid: bool, error_message: Optional[str])
    """
    if not file or not file.filename:
        return False, "Geen bestand gevonden"

    filename = file.filename

    # Check extensie
    if '.' not in filename:
        return False, "Bestand heeft geen extensie"

    extension = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = {'txt', 'docx', 'xlsx', 'csv', 'pdf', 'md'}

    if extension not in allowed_extensions:
        return False, f"Bestandstype .{extension} niet toegestaan"

    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to start

    max_size = MAX_FILE_SIZES.get(extension, 50 * 1024 * 1024)
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        file_mb = file_size / (1024 * 1024)
        return False, f"Bestand te groot ({file_mb:.1f}MB). Maximum toegestaan is {max_mb:.0f}MB. Split bestand of neem contact op."

    if file_size == 0:
        return False, "Bestand is leeg"

    # Optional: MIME type validation (requires python-magic)
    if check_mime and MAGIC_AVAILABLE:
        try:
            file.seek(0)
            mime = magic.from_buffer(file.read(2048), mime=True)
            file.seek(0)

            # Check if MIME type matches extension
            if mime not in ALLOWED_MIME_TYPES:
                return False, f"MIME type {mime} niet toegestaan"

            if extension not in ALLOWED_MIME_TYPES[mime]:
                return False, f"Extensie .{extension} komt niet overeen met MIME type {mime}"

        except Exception as e:
            # Error during MIME check - skip
            pass

    return True, None


def validate_session_id(session_id: str) -> bool:
    """
    Valideer session ID is een geldige UUID.

    Args:
        session_id: Session ID string

    Returns:
        True als geldig UUID, anders False
    """
    if not session_id:
        return False

    try:
        uuid_obj = uuid.UUID(session_id)
        return str(uuid_obj) == session_id
    except (ValueError, AttributeError):
        return False


def validate_file_id(file_id: str) -> bool:
    """
    Valideer file ID is een geldige UUID.

    Args:
        file_id: File ID string

    Returns:
        True als geldig UUID, anders False
    """
    return validate_session_id(file_id)  # Same validation


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename door gevaarlijke karakters te verwijderen.

    Args:
        filename: Originele filename
        max_length: Maximum lengte van filename

    Returns:
        Gesanitized filename
    """
    from werkzeug.utils import secure_filename

    # Gebruik werkzeug's secure_filename
    safe_name = secure_filename(filename)

    # Extra: verwijder dubbele extensies
    # "malicious.php.txt" -> "malicious_php.txt"
    if safe_name.count('.') > 1:
        parts = safe_name.split('.')
        # Laatste deel is de extensie, rest replace dots met underscores
        name_part = '_'.join(parts[:-1])
        extension = parts[-1]
        safe_name = f"{name_part}.{extension}"

    # Truncate als te lang
    if len(safe_name) > max_length:
        # Behoud extensie
        if '.' in safe_name:
            name, ext = safe_name.rsplit('.', 1)
            name = name[:max_length - len(ext) - 1]
            safe_name = f"{name}.{ext}"
        else:
            safe_name = safe_name[:max_length]

    return safe_name


def validate_path_traversal(path: Path, base_path: Path) -> bool:
    """
    Check of path binnen base_path blijft (geen path traversal).

    Args:
        path: Path om te valideren
        base_path: Base directory

    Returns:
        True als path veilig is, anders False
    """
    try:
        # Resolve beide paths (resolves .., symlinks, etc.)
        resolved_path = path.resolve()
        resolved_base = base_path.resolve()

        # Check of resolved path binnen base path valt
        return resolved_path.is_relative_to(resolved_base)
    except (ValueError, OSError):
        return False


def validate_regex_pattern(pattern: str, max_length: int = 1000) -> Tuple[bool, Optional[str]]:
    """
    Valideer regex pattern op veiligheid (geen ReDoS).

    Args:
        pattern: Regex pattern string
        max_length: Maximum lengte van pattern

    Returns:
        Tuple van (is_valid: bool, error_message: Optional[str])
    """
    if len(pattern) > max_length:
        return False, f"Pattern te lang (max {max_length} karakters)"

    # Check for dangerous regex patterns that can cause ReDoS
    # (Deze check is basis - voor echte productie gebruik een library zoals 'rxxr2')

    dangerous_patterns = [
        r'\(\?.*\)\+\+',  # Nested quantifiers
        r'\(\?.*\)\*\*',
        r'\(\?.*\){.*,.*}',  # Large repetitions
    ]

    for dangerous in dangerous_patterns:
        if re.search(dangerous, pattern):
            return False, "Mogelijk gevaarlijk regex pattern gedetecteerd"

    # Probeer te compileren
    try:
        re.compile(pattern)
        return True, None
    except re.error as e:
        return False, f"Ongeldig regex pattern: {str(e)}"


def validate_json_input(data: dict, required_fields: list, max_depth: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Valideer JSON input op required fields en max depth.

    Args:
        data: JSON data als dict
        required_fields: Lijst van required field names
        max_depth: Maximum nesting depth

    Returns:
        Tuple van (is_valid: bool, error_message: Optional[str])
    """
    if not isinstance(data, dict):
        return False, "Data moet een object zijn"

    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Required field '{field}' ontbreekt"

    # Check depth (tegen JSON bombs)
    def get_depth(obj, current_depth=0):
        if current_depth > max_depth:
            raise ValueError("Max depth exceeded")

        if isinstance(obj, dict):
            if obj:
                return 1 + max(get_depth(v, current_depth + 1) for v in obj.values())
            return 1
        elif isinstance(obj, list):
            if obj:
                return 1 + max(get_depth(item, current_depth + 1) for item in obj)
            return 1
        return 0

    try:
        depth = get_depth(data)
        if depth > max_depth:
            return False, f"JSON te diep genest (max {max_depth} levels)"
    except ValueError:
        return False, f"JSON te diep genest (max {max_depth} levels)"

    return True, None
