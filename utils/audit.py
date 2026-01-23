"""
Audit logging utility voor GDPR-compliant tracking van anonymization operaties.

Logt alle anonymization acties naar session-specific audit.log bestanden.
Volgens GDPR Article 32 vereisten voor processing accountability.
"""

import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


class AuditLogger:
    """
    GDPR-compliant audit trail logger voor anonymization operaties.

    Logt naar output/{session_id}/audit.log met:
    - ISO 8601 timestamps (UTC)
    - Session ID
    - Action type
    - Filename
    - Transformation details

    Usage:
        logger = AuditLogger(session_id, output_dir)
        logger.log_anonymize_start("data.xlsx", "excel")
        logger.log_mapping_saved(15, encrypted=True)
        logger.log_anonymize_complete("data_anonymized.xlsx")
    """

    # Action types
    ACTION_ANONYMIZE_START = "ANONYMIZE_START"
    ACTION_ANONYMIZE_COMPLETE = "ANONYMIZE_COMPLETE"
    ACTION_ANONYMIZE_ERROR = "ANONYMIZE_ERROR"
    ACTION_REVERSE_START = "REVERSE_START"
    ACTION_REVERSE_COMPLETE = "REVERSE_COMPLETE"
    ACTION_REVERSE_ERROR = "REVERSE_ERROR"
    ACTION_MAPPING_SAVED = "MAPPING_SAVED"
    ACTION_MAPPING_LOADED = "MAPPING_LOADED"

    def __init__(self, session_id: str, output_dir: Path):
        """
        Initialiseer audit logger voor een session.

        Args:
            session_id: UUID van de session
            output_dir: Output directory voor deze session (bijv. output/{session_id}/)
        """
        self.session_id = session_id
        self.output_dir = Path(output_dir)
        self.audit_log_path = self.output_dir / 'audit.log'

        # Setup Python logger
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        Setup Python logging naar audit.log.

        Returns:
            Configured Logger instance
        """
        # Create logger met unieke naam per session
        logger = logging.getLogger(f'audit_{self.session_id}')
        logger.setLevel(logging.INFO)

        # Verwijder bestaande handlers (avoid duplicates bij multiple instanties)
        logger.handlers.clear()

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # File handler naar audit.log
        file_handler = logging.FileHandler(self.audit_log_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Format: ISO timestamp [SESSION:id] ACTION key=value key=value
        formatter = logging.Formatter(
            '%(asctime)s [SESSION:%(session_id)s] %(action)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S.%fZ'
        )
        formatter.converter = lambda *args: datetime.now(timezone.utc).timetuple()
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        # Don't propagate to root logger (avoid duplicate logs)
        logger.propagate = False

        return logger

    def _log(self, action: str, **kwargs) -> None:
        """
        Internal: schrijf log entry.

        Args:
            action: Action type (bijv. ANONYMIZE_START)
            **kwargs: Key-value pairs voor log message
        """
        # Build message from kwargs
        message_parts = []
        for key, value in kwargs.items():
            message_parts.append(f"{key}={value}")

        message = ' '.join(message_parts)

        # Log met extra context
        self.logger.info(
            message,
            extra={'session_id': self.session_id, 'action': action}
        )

    def log_anonymize_start(self, filename: str, file_type: str) -> None:
        """
        Log start van anonymization operatie.

        Args:
            filename: Naam van input bestand
            file_type: Type bestand (text, docx, excel, pdf)
        """
        self._log(
            self.ACTION_ANONYMIZE_START,
            file=filename,
            type=file_type
        )

    def log_anonymize_complete(self, filename: str, rules_applied: Optional[int] = None) -> None:
        """
        Log succesvolle completion van anonymization.

        Args:
            filename: Naam van output bestand
            rules_applied: Aantal toegepaste regels (optioneel)
        """
        kwargs = {'file': filename}
        if rules_applied is not None:
            kwargs['rules_applied'] = rules_applied

        self._log(self.ACTION_ANONYMIZE_COMPLETE, **kwargs)

    def log_anonymize_error(self, filename: str, error: str) -> None:
        """
        Log error tijdens anonymization.

        Args:
            filename: Naam van bestand waar error optrad
            error: Error message
        """
        self._log(
            self.ACTION_ANONYMIZE_ERROR,
            file=filename,
            error=error
        )

    def log_mapping_saved(self, mapping_count: int, encrypted: bool = True) -> None:
        """
        Log opslaan van mapping.

        Args:
            mapping_count: Aantal mappings opgeslagen
            encrypted: Of mapping encrypted is
        """
        self._log(
            self.ACTION_MAPPING_SAVED,
            mappings=mapping_count,
            encrypted=str(encrypted).lower()
        )

    def log_mapping_loaded(self, mapping_count: int, encrypted: bool = True) -> None:
        """
        Log laden van mapping.

        Args:
            mapping_count: Aantal mappings geladen
            encrypted: Of mapping encrypted was
        """
        self._log(
            self.ACTION_MAPPING_LOADED,
            mappings=mapping_count,
            encrypted=str(encrypted).lower()
        )

    def log_reverse_start(self, filename: str, file_type: str) -> None:
        """
        Log start van reverse anonymization.

        Args:
            filename: Naam van input bestand
            file_type: Type bestand
        """
        self._log(
            self.ACTION_REVERSE_START,
            file=filename,
            type=file_type
        )

    def log_reverse_complete(self, filename: str, mappings_applied: Optional[int] = None) -> None:
        """
        Log succesvolle completion van reverse anonymization.

        Args:
            filename: Naam van output bestand
            mappings_applied: Aantal toegepaste mappings (optioneel)
        """
        kwargs = {'file': filename}
        if mappings_applied is not None:
            kwargs['mappings_applied'] = mappings_applied

        self._log(self.ACTION_REVERSE_COMPLETE, **kwargs)

    def log_reverse_error(self, filename: str, error: str) -> None:
        """
        Log error tijdens reverse anonymization.

        Args:
            filename: Naam van bestand waar error optrad
            error: Error message
        """
        self._log(
            self.ACTION_REVERSE_ERROR,
            file=filename,
            error=error
        )

    def get_audit_log_path(self) -> Path:
        """
        Krijg pad naar audit log bestand.

        Returns:
            Path naar audit.log
        """
        return self.audit_log_path

    def read_audit_log(self) -> str:
        """
        Lees audit log contents.

        Returns:
            String met complete audit log contents

        Raises:
            FileNotFoundError: Als audit.log nog niet bestaat
        """
        if not self.audit_log_path.exists():
            return ""

        with open(self.audit_log_path, 'r', encoding='utf-8') as f:
            return f.read()


def create_audit_logger(session_id: str, output_dir: Path) -> AuditLogger:
    """
    Factory function voor audit logger.

    Args:
        session_id: UUID van session
        output_dir: Output directory

    Returns:
        AuditLogger instance
    """
    return AuditLogger(session_id, output_dir)
