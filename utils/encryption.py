"""
Encryption utility voor secure mapping storage.

Gebruikt Fernet (symmetric encryption) voor het encrypten van mapping.json files.
Elke session krijgt een unieke encryption key die automatisch wordt gegenereerd.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from cryptography.fernet import Fernet, InvalidToken


class SecureMappingStorage:
    """
    Secure storage voor anonymization mappings met encryption.

    Elke session krijgt een unieke encryption key die wordt opgeslagen in
    output/{session_id}/.encryption_key. Deze key wordt gebruikt om mapping.json
    te encrypten/decrypten.

    Usage:
        # Bij anonymization:
        storage = SecureMappingStorage(session_id)
        storage.save_mapping(mapping_dict, output_dir)

        # Bij reverse anonymization:
        storage = SecureMappingStorage(session_id)
        mapping = storage.load_mapping(output_dir)
    """

    def __init__(self, session_id: str):
        """
        Initialiseer secure storage voor een session.

        Args:
            session_id: UUID van de session
        """
        self.session_id = session_id
        self._key: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None

    def _get_key_path(self, output_dir: Path) -> Path:
        """
        Bepaal pad naar encryption key bestand.

        Args:
            output_dir: Output directory voor deze session

        Returns:
            Path naar .encryption_key bestand
        """
        return output_dir / '.encryption_key'

    def _load_or_generate_key(self, output_dir: Path) -> Fernet:
        """
        Laad bestaande key of genereer nieuwe key.

        Args:
            output_dir: Output directory voor deze session

        Returns:
            Fernet instance met geladen/gegenereerde key
        """
        if self._fernet is not None:
            return self._fernet

        key_path = self._get_key_path(output_dir)

        if key_path.exists():
            # Laad bestaande key
            with open(key_path, 'rb') as f:
                self._key = f.read()
        else:
            # Genereer nieuwe key
            self._key = Fernet.generate_key()

            # Sla key op (wordt auto-cleaned na 24u samen met session)
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(key_path, 'wb') as f:
                f.write(self._key)

        self._fernet = Fernet(self._key)
        return self._fernet

    def save_mapping(self, mapping: Dict, output_dir: Path, filename: str = 'mapping.json') -> None:
        """
        Encrypt en sla mapping op.

        Args:
            mapping: Dictionary met origineel → placeholder mappings
            output_dir: Output directory (bijv. output/{session_id}/)
            filename: Naam van mapping bestand (default: mapping.json)

        Raises:
            IOError: Als schrijven faalt
        """
        output_dir = Path(output_dir)
        fernet = self._load_or_generate_key(output_dir)

        # Converteer mapping naar JSON string
        mapping_json = json.dumps(mapping, indent=2, ensure_ascii=False)

        # Encrypt JSON
        encrypted_data = fernet.encrypt(mapping_json.encode('utf-8'))

        # Schrijf encrypted data
        mapping_path = output_dir / filename
        with open(mapping_path, 'wb') as f:
            f.write(encrypted_data)

    def load_mapping(self, output_dir: Path, filename: str = 'mapping.json') -> Dict:
        """
        Decrypt en laad mapping.

        Args:
            output_dir: Output directory (bijv. output/{session_id}/)
            filename: Naam van mapping bestand (default: mapping.json)

        Returns:
            Dictionary met origineel → placeholder mappings

        Raises:
            FileNotFoundError: Als mapping.json niet bestaat
            InvalidToken: Als decryption faalt (verkeerde key of corrupt bestand)
            json.JSONDecodeError: Als decrypted data geen valide JSON is
        """
        output_dir = Path(output_dir)
        mapping_path = output_dir / filename

        if not mapping_path.exists():
            raise FileNotFoundError(f"Mapping bestand niet gevonden: {mapping_path}")

        fernet = self._load_or_generate_key(output_dir)

        # Lees encrypted data
        with open(mapping_path, 'rb') as f:
            encrypted_data = f.read()

        # Decrypt
        try:
            decrypted_data = fernet.decrypt(encrypted_data)
        except InvalidToken:
            raise InvalidToken("Kan mapping niet decrypten. Key is mogelijk corrupt of verkeerd.")

        # Parse JSON
        mapping = json.loads(decrypted_data.decode('utf-8'))

        return mapping

    def mapping_exists(self, output_dir: Path, filename: str = 'mapping.json') -> bool:
        """
        Check of encrypted mapping bestand bestaat.

        Args:
            output_dir: Output directory
            filename: Naam van mapping bestand

        Returns:
            True als mapping bestand bestaat
        """
        output_dir = Path(output_dir)
        mapping_path = output_dir / filename
        return mapping_path.exists()


def load_plaintext_mapping(mapping_path: Path) -> Dict:
    """
    Backwards compatibility: laad plaintext mapping.json.

    Gebruikt voor oude (pre-encryption) mapping files.

    Args:
        mapping_path: Pad naar plaintext mapping.json

    Returns:
        Dictionary met mappings

    Raises:
        FileNotFoundError: Als bestand niet bestaat
        json.JSONDecodeError: Als bestand geen valide JSON is
    """
    with open(mapping_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_encrypted_mapping(mapping_path: Path) -> bool:
    """
    Detecteer of mapping bestand encrypted is.

    Encrypted bestanden zijn binary (niet UTF-8 decodable).
    Plaintext mappings zijn JSON (UTF-8 text).

    Args:
        mapping_path: Pad naar mapping bestand

    Returns:
        True als encrypted, False als plaintext
    """
    try:
        with open(mapping_path, 'rb') as f:
            data = f.read(100)  # Lees eerste 100 bytes

        # Probeer als UTF-8 te decoden
        try:
            data.decode('utf-8')
            # Als dit lukt, is het plaintext
            return False
        except UnicodeDecodeError:
            # Als dit faalt, is het binary (encrypted)
            return True

    except Exception:
        # Als bestand niet leesbaar is, assume encrypted
        return True
