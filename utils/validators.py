"""
Security Validators Module

Bevat functies voor ReDoS protection, formula injection escaping, file validation,
session isolation en andere security validatie.
"""

import re
import signal
import zipfile
from pathlib import Path
from typing import List, Optional, Dict
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from flask import session, abort, current_app


class TimeoutError(Exception):
    """Raised when regex execution times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for regex timeout."""
    raise TimeoutError("Regex timeout")


def safe_regex_findall(pattern: str, text: str, timeout: int = 1) -> List[str]:
    """
    Regex findall met timeout protection tegen ReDoS.

    Args:
        pattern: Regex pattern
        text: Text to search
        timeout: Max seconds (default 1)

    Returns:
        List of matches

    Raises:
        TimeoutError: Als regex >timeout seconden duurt
        re.error: Als pattern invalid is
    """
    # Set alarm signal
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        compiled = re.compile(pattern)
        matches = compiled.findall(text)
        signal.alarm(0)  # Cancel alarm
        return matches
    except TimeoutError:
        signal.alarm(0)
        raise TimeoutError(f"Regex pattern '{pattern}' timeout na {timeout}s - mogelijk ReDoS vulnerability")
    except re.error as e:
        signal.alarm(0)
        raise re.error(f"Invalid regex pattern '{pattern}': {e}")


def safe_regex_sub(pattern: str, replacement: str, text: str, timeout: int = 1) -> str:
    """
    Regex substitution met timeout protection tegen ReDoS.

    Args:
        pattern: Regex pattern
        replacement: Replacement string
        text: Text to search and replace
        timeout: Max seconds (default 1)

    Returns:
        Text with replacements

    Raises:
        TimeoutError: Als regex >timeout seconden duurt
        re.error: Als pattern invalid is
    """
    # Set alarm signal
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        compiled = re.compile(pattern)
        result = compiled.sub(replacement, text)
        signal.alarm(0)  # Cancel alarm
        return result
    except TimeoutError:
        signal.alarm(0)
        raise TimeoutError(f"Regex pattern '{pattern}' timeout na {timeout}s - mogelijk ReDoS vulnerability")
    except re.error as e:
        signal.alarm(0)
        raise re.error(f"Invalid regex pattern '{pattern}': {e}")


def escape_formula(value: str) -> str:
    """
    Escape Excel formulas door prefixen met single quote.

    Voorkomt formula injection attacks waarbij cellen die beginnen met
    =, +, -, @ worden uitgevoerd als formulas in Excel.

    Args:
        value: Cell value (string)

    Returns:
        Escaped value met single quote prefix indien nodig
    """
    if isinstance(value, str) and len(value) > 0:
        if value[0] in ('=', '+', '-', '@'):
            return "'" + value  # Single quote escapes formula
    return value


def validate_file(file_path: Path) -> Dict[str, any]:
    """
    Valideer uploaded bestand op corruption en password protection.

    Deze functie detecteert vroeg:
    - Corrupt/ongeldig bestanden
    - Password-protected bestanden
    - Lege/onleesbare bestanden

    Args:
        file_path: Path naar uploaded bestand

    Returns:
        dict: {"valid": bool, "error": str|None, "warnings": list}
    """
    ext = file_path.suffix.lower()
    result = {"valid": True, "error": None, "warnings": []}

    try:
        if ext in ['.xlsx', '.xls']:
            # Test if Excel file is readable
            try:
                wb = load_workbook(file_path, read_only=True, data_only=True)
                wb.close()
            except InvalidFileException:
                result["valid"] = False
                result["error"] = "Excel bestand is corrupt of ongeldig formaat"
            except zipfile.BadZipFile:
                result["valid"] = False
                result["error"] = "Excel bestand is corrupt (geen valide ZIP)"
            except Exception as e:
                error_msg = str(e).lower()
                if "password" in error_msg or "encrypted" in error_msg:
                    result["valid"] = False
                    result["error"] = "Excel bestand is wachtwoord-beveiligd. Verwijder wachtwoord eerst."
                else:
                    result["valid"] = False
                    result["error"] = f"Excel kan niet worden gelezen: {str(e)}"

        elif ext == '.docx':
            # Test if Word file is readable
            try:
                from docx import Document
                doc = Document(file_path)
                # Try to access paragraphs to verify it's readable
                _ = len(doc.paragraphs)
            except Exception as e:
                error_msg = str(e).lower()
                if "password" in error_msg or "encrypted" in error_msg:
                    result["valid"] = False
                    result["error"] = "Word document is wachtwoord-beveiligd. Verwijder wachtwoord eerst."
                else:
                    result["valid"] = False
                    result["error"] = f"Word document kan niet worden gelezen: {str(e)}"

        elif ext == '.pdf':
            # Test if PDF is readable
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    if len(pdf.pages) == 0:
                        result["valid"] = False
                        result["error"] = "PDF bevat geen pagina's"
                    # Check if it's a scanned PDF (no text)
                    elif len(pdf.pages) > 0:
                        first_page_text = pdf.pages[0].extract_text() or ""
                        if len(first_page_text.strip()) < 10:
                            result["warnings"].append(
                                "PDF lijkt gescand te zijn (weinig tekst). OCR is vereist voor anonimisatie."
                            )
            except Exception as e:
                error_msg = str(e).lower()
                if "password" in error_msg or "encrypted" in error_msg:
                    result["valid"] = False
                    result["error"] = "PDF is wachtwoord-beveiligd. Verwijder wachtwoord eerst."
                else:
                    result["valid"] = False
                    result["error"] = f"PDF kan niet worden gelezen: {str(e)}"

        elif ext in ['.txt', '.csv', '.md']:
            # Test if text file is readable
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(100)  # Read first 100 chars to verify
            except UnicodeDecodeError:
                # Try different encodings
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        f.read(100)
                    result["warnings"].append(
                        "Bestand gebruikt niet-UTF-8 encoding. Dit kan leiden tot encoding problemen."
                    )
                except Exception:
                    result["valid"] = False
                    result["error"] = "Tekstbestand kan niet worden gelezen (encoding probleem)"
            except Exception as e:
                result["valid"] = False
                result["error"] = f"Tekstbestand kan niet worden gelezen: {str(e)}"

        return result

    except Exception as e:
        result["valid"] = False
        result["error"] = f"Onverwachte fout bij validatie: {str(e)}"
        return result


def validate_bsn(bsn_str: str) -> bool:
    """
    Valideer BSN met 11-proef checksum algorithm.

    Weights: 9, 8, 7, 6, 5, 4, 3, 2, -1
    Checksum: sum(digit * weight) % 11 == 0

    Args:
        bsn_str: BSN string (9 digits, mag streepjes/punten bevatten)

    Returns:
        True als checksum valid, False anders

    Examples:
        validate_bsn("123456782") → True
        validate_bsn("123456783") → False
        validate_bsn("000000000") → False (deny list)
    """
    # Remove formatting
    digits = re.sub(r'[^0-9]', '', bsn_str)

    if len(digits) != 9:
        return False

    # Deny list: known invalid BSNs
    if digits in ('000000000', '111111111', '222222222', '333333333',
                   '444444444', '555555555', '666666666', '777777777',
                   '888888888', '999999999'):
        return False

    # 11-proef checksum
    weights = [9, 8, 7, 6, 5, 4, 3, 2, -1]
    checksum = sum(int(digit) * weight for digit, weight in zip(digits, weights))

    return checksum % 11 == 0


def validate_iban(iban_str: str) -> bool:
    """
    Valideer IBAN met mod-97 checksum algorithm.

    Algorithm:
    1. Move first 4 chars to end
    2. Replace letters with numbers (A=10, B=11, ..., Z=35)
    3. Calculate mod 97
    4. Valid if result == 1

    Args:
        iban_str: IBAN string (mag spaties bevatten)

    Returns:
        True als checksum valid

    Examples:
        validate_iban("NL91ABNA0417164300") → True
        validate_iban("NL00FAKE0000000000") → False
    """
    # Remove whitespace and convert to uppercase
    iban = re.sub(r'\s', '', iban_str).upper()

    # Check length (NL=18, DE=22, BE=16, FR=27)
    valid_lengths = {'NL': 18, 'DE': 22, 'BE': 16, 'FR': 27}
    country = iban[:2]
    if country not in valid_lengths or len(iban) != valid_lengths[country]:
        return False

    # Move first 4 chars to end
    rearranged = iban[4:] + iban[:4]

    # Replace letters with numbers (A=10, B=11, ..., Z=35)
    numeric = ''
    for char in rearranged:
        if char.isdigit():
            numeric += char
        else:
            numeric += str(ord(char) - ord('A') + 10)

    # Check mod-97
    return int(numeric) % 97 == 1


def validate_postal_code_nl(postal_str: str) -> bool:
    """
    Valideer Dutch postal code format en letter restrictions.

    Valid: 1012JS, 1234AB
    Invalid: 1234SA (reserved for PO boxes)

    Args:
        postal_str: Postal code string (4 digits + 2 letters)

    Returns:
        True als valid format en letters
    """
    # Normalize
    postal = re.sub(r'\s', '', postal_str).upper()

    if len(postal) != 6 or not postal[:4].isdigit() or not postal[4:].isalpha():
        return False

    # Check letter restrictions (reserved combinations)
    letters = postal[4:]
    invalid_combinations = ['SA', 'SD', 'SS']

    return letters not in invalid_combinations


def validate_session_access(file_path: Path, session_id: Optional[str] = None) -> bool:
    """
    Verify user can only access files in their own session directory.

    Prevents path traversal attacks like:
    - ../../other_session/sensitive.xlsx
    - /absolute/path/to/file

    Args:
        file_path: Path to file being accessed
        session_id: Session ID (defaults to current session)

    Returns:
        True if access is valid

    Raises:
        403 Forbidden: If file is outside session directory or session invalid
    """
    # Get session ID from Flask session if not provided
    if session_id is None:
        session_id = session.get('session_id')

    if not session_id:
        abort(403, "Geen geldige sessie")

    # Get session directory
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    output_folder = current_app.config.get('OUTPUT_FOLDER')

    if not upload_folder or not output_folder:
        abort(500, "Server configuratie fout")

    session_upload_dir = Path(upload_folder) / session_id
    session_output_dir = Path(output_folder) / session_id

    # Resolve paths to absolute (handles .., symlinks, etc.)
    try:
        resolved_file = file_path.resolve()
        resolved_upload = session_upload_dir.resolve()
        resolved_output = session_output_dir.resolve()
    except (ValueError, OSError) as e:
        abort(403, f"Ongeldige bestandspad: {str(e)}")

    # Check if file is within session upload or output directory
    try:
        # Try to make file_path relative to session directories
        is_in_upload = resolved_file.is_relative_to(resolved_upload)
    except ValueError:
        is_in_upload = False

    try:
        is_in_output = resolved_file.is_relative_to(resolved_output)
    except ValueError:
        is_in_output = False

    if not (is_in_upload or is_in_output):
        # File is outside both session directories - path traversal attack
        abort(403, "Toegang geweigerd - bestand niet in jouw sessie")

    return True
