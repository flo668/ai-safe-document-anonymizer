"""PDF anonimisatie module"""

from pathlib import Path
from typing import List, Tuple
try:
    import pdfplumber
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from .text_anonymizer import AnonymizationRule, LogEntry, TextAnonymizer
except ImportError:
    from text_anonymizer import AnonymizationRule, LogEntry, TextAnonymizer


class PdfAnonymizer:
    """PDF anonimisatie processor"""

    @staticmethod
    def check_support() -> bool:
        """Check of PDF ondersteuning beschikbaar is"""
        return PDF_SUPPORT

    @staticmethod
    def process_pdf_file(
        input_path: Path,
        output_path: Path,
        rules: List[AnonymizationRule],
        auto_detect_enabled: bool = True,
        phone_placeholder: str = "[TEL VERWIJDERD]",
        email_placeholder: str = "[EMAIL VERWIJDERD]"
    ) -> Tuple[List[LogEntry], dict]:
        """
        Verwerk een PDF bestand met anonimisatie

        Args:
            input_path: Pad naar input PDF
            output_path: Pad naar output PDF
            rules: List van anonimisatie regels
            auto_detect_enabled: Of auto-detectie aan staat
            phone_placeholder: Placeholder voor telefoons
            email_placeholder: Placeholder voor emails

        Returns:
            Tuple van (log entries, auto_detect_report)
        """
        if not PDF_SUPPORT:
            raise ImportError(
                "PDF ondersteuning niet beschikbaar. "
                "Installeer: pip install pdfplumber reportlab"
            )

        # Extraheer tekst uit PDF
        full_text = []
        with pdfplumber.open(input_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)

        # Combineer alle tekst
        combined_text = '\n\n'.join(full_text)

        # Anonimiseer met auto-detectie
        anonymized_text, log_entries, auto_detect_report = TextAnonymizer.anonymize_text_with_auto_detection(
            combined_text, rules, auto_detect_enabled, phone_placeholder, email_placeholder
        )

        # Maak nieuwe PDF met geanonimiseerde tekst
        PdfAnonymizer._create_pdf(output_path, anonymized_text)

        return log_entries, auto_detect_report

    @staticmethod
    def _create_pdf(output_path: Path, text: str):
        """
        Maak een nieuwe PDF met gegeven tekst

        Args:
            output_path: Pad waar PDF opgeslagen wordt
            text: Tekst om in PDF te schrijven
        """
        # Maak PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Styles
        styles = getSampleStyleSheet()
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=12
        )

        # Content elementen
        story = []

        # Split text in paragrafen en voeg toe aan story
        paragraphs = text.split('\n')
        for para_text in paragraphs:
            if para_text.strip():
                # Escape special chars voor ReportLab
                safe_text = para_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                p = Paragraph(safe_text, normal_style)
                story.append(p)
            else:
                # Lege regel = spacer
                story.append(Spacer(1, 0.2 * inch))

        # Build PDF
        doc.build(story)

    @staticmethod
    def extract_text_for_preview(input_path: Path, max_chars: int = 500) -> str:
        """
        Extraheer tekst uit PDF voor preview

        Args:
            input_path: Pad naar PDF
            max_chars: Maximum aantal karakters

        Returns:
            Eerste max_chars karakters van de PDF
        """
        if not PDF_SUPPORT:
            return "PDF ondersteuning niet beschikbaar"

        text_parts = []
        total_chars = 0

        with pdfplumber.open(input_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
                    total_chars += len(text)
                    if total_chars >= max_chars:
                        break

        full_text = '\n\n'.join(text_parts)
        return full_text[:max_chars]
