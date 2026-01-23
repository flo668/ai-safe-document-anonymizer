"""
Pytest Fixtures - Gedeelde test fixtures voor alle tests

Dit bestand bevat fixtures voor:
- Flask app en test client
- Sample tekst met PII data
- Test bestanden (txt, docx, xlsx, pdf)
- Anonimisatie regels
"""

import pytest
from pathlib import Path
from app import create_app
from anonymizer import AnonymizationRule, ExcelColumnRule


@pytest.fixture
def app():
    """Flask app instance voor testing"""
    app = create_app('testing')

    yield app

    # Cleanup na tests
    import shutil
    shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
    shutil.rmtree(app.config['OUTPUT_FOLDER'], ignore_errors=True)


@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Flask CLI test runner"""
    return app.test_cli_runner()


# Sample Data Fixtures

@pytest.fixture
def sample_text_with_pii():
    """Sample tekst met Nederlandse telefoons en emails"""
    return """
    Contactgegevens afdeling Verkoop:

    Jan de Vries
    Telefoon: 06-12345678
    Email: jan.devries@example.com

    Maria Jansen
    Mobiel: 0612345678
    E-mail: maria.jansen@bedrijf.nl

    Kantoor Amsterdam:
    Tel: +31612345678
    Info: info@amsterdam.example.com

    Emergency: 06 12 34 56 78
    """


@pytest.fixture
def sample_text_clean():
    """Schone tekst zonder PII"""
    return "Dit is een test document zonder persoonlijke informatie."


@pytest.fixture
def sample_phones():
    """Lijst met verschillende Nederlandse telefoonformaten"""
    return [
        "06-12345678",
        "0612345678",
        "+31612345678",
        "06 12345678",
        "06 12 34 56 78",
        "+31 6 12345678",
        "0031612345678",
        "(06) 12345678",
        "06.12.34.56.78",
        "06/12345678"
    ]


@pytest.fixture
def sample_emails():
    """Lijst met email adressen"""
    return [
        "test@example.com",
        "jan.de.vries@bedrijf.nl",
        "info@sub.domain.com",
        "user+tag@gmail.com",
        "admin@localhost"
    ]


# Rule Fixtures

@pytest.fixture
def text_rule_regex():
    """Voorbeeld regex regel"""
    return AnonymizationRule({
        'id': 'test-regex-1',
        'pattern': r'\b\d{4}\s?[A-Z]{2}\b',  # Postcode
        'isRegex': True,
        'replacementTerm': '[POSTCODE]',
        'caseSensitive': False
    })


@pytest.fixture
def text_rule_literal():
    """Voorbeeld literal string regel"""
    return AnonymizationRule({
        'id': 'test-literal-1',
        'pattern': 'Jan de Vries',
        'isRegex': False,
        'replacementTerm': '[NAAM]',
        'caseSensitive': False
    })


@pytest.fixture
def excel_rule_hash():
    """Excel regel met hash strategie"""
    return ExcelColumnRule({
        'id': 'excel-1',
        'columnName': 'Email',
        'strategy': 'hash',
        'reversible': False
    })


@pytest.fixture
def excel_rule_mask():
    """Excel regel met mask strategie"""
    return ExcelColumnRule({
        'id': 'excel-2',
        'columnName': 'Telefoon',
        'strategy': 'mask',
        'reversible': False
    })


# File Path Fixtures

@pytest.fixture
def fixture_dir():
    """Directory met test fixture bestanden"""
    return Path(__file__).parent / 'fixtures'


@pytest.fixture
def sample_txt_file(fixture_dir):
    """Pad naar sample .txt bestand"""
    return fixture_dir / 'test_document.txt'


@pytest.fixture
def sample_docx_file(fixture_dir):
    """Pad naar sample .docx bestand"""
    return fixture_dir / 'test_document.docx'


@pytest.fixture
def sample_xlsx_file(fixture_dir):
    """Pad naar sample .xlsx bestand"""
    return fixture_dir / 'test_spreadsheet.xlsx'


@pytest.fixture
def sample_pdf_file(fixture_dir):
    """Pad naar sample .pdf bestand"""
    return fixture_dir / 'test.pdf'


# Temporary File Fixtures

@pytest.fixture
def temp_output_file(tmp_path):
    """Tijdelijk output bestand"""
    return tmp_path / 'output.txt'


@pytest.fixture
def temp_mapping_file(tmp_path):
    """Tijdelijk mapping.json bestand"""
    return tmp_path / 'mapping.json'


# Edge Case Testing Fixtures (Phase 4)

@pytest.fixture
def corrupt_file_generators():
    """
    Import corrupt file generators for edge case tests

    From tests/fixtures/corrupt_files.py
    Used in test_edge_cases.py (Task 04-02)
    """
    from tests.fixtures import corrupt_files
    return corrupt_files


@pytest.fixture
def special_characters():
    """
    Special characters for encoding tests

    From PITFALLS.md line 56:
    Tests encoding preservation across multiple character sets
    """
    return {
        'western_european': 'Café Müller — naïve résumé',
        'currency': '€100 £50 ¥1000',
        'spanish': 'mañana piñata',
        'german': 'Übergrößenträger',
        'french': 'Côte d\'Azur',
        'mixed': 'Café €10 — São Paulo résumé'
    }


# Pytest configuration for edge case tests

def pytest_configure(config):
    """Register custom markers for edge case tests"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "edge_case: marks tests for edge cases from PITFALLS.md"
    )
