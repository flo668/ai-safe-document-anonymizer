# Contributing Guide

Bedankt voor je interesse in het Multi-Bestand Anonimiseren Tool project! We verwelkomen contributions van iedereen, van beginners tot ervaren ontwikkelaars.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Questions?](#questions)

## 🤝 Code of Conduct

Dit project volgt een simpele regel: **Wees aardig en respectvol**. We verwelkomen iedereen, ongeacht ervaring, achtergrond of identiteit.

## 🎯 How Can I Contribute?

### 🐛 Reporting Bugs

Vond je een bug? Help ons door een gedetailleerd bug report te maken:

1. **Check eerst** of de bug al is gerapporteerd in [Issues](https://github.com/username/repo/issues)
2. Als het een nieuwe bug is, [open een issue](https://github.com/username/repo/issues/new) met:
   - **Duidelijke titel**: "Excel Reversible Mode checkbox niet zichtbaar"
   - **Stappen om te reproduceren**:
     ```
     1. Open Excel tab
     2. Upload een .xlsx bestand
     3. Kijk naar de opties
     ```
   - **Verwacht gedrag**: "Reversible Mode checkbox zou zichtbaar moeten zijn"
   - **Actueel gedrag**: "Checkbox is niet zichtbaar"
   - **Screenshots** (indien relevant)
   - **Environment info**:
     - OS: macOS 14.2 / Windows 11 / Ubuntu 24.04
     - Python version: `python --version`
     - Browser: Chrome 120 / Firefox 121 / Safari 17
     - App version: v1.0 / development

### 💡 Suggesting Enhancements

Heb je een idee voor een nieuwe feature? We horen het graag!

1. [Open een issue](https://github.com/username/repo/issues/new) met tag `enhancement`
2. Beschrijf:
   - **Probleem**: Welk probleem lost het op?
   - **Oplossing**: Hoe zou de feature werken?
   - **Alternatieven**: Heb je andere oplossingen overwogen?
   - **Use case**: Concrete voorbeelden van gebruik

**Voorbeelden van goede feature requests:**
- ✅ "Multi-sheet Excel support - Gebruikers willen specifieke sheets selecteren ipv alleen eerste sheet"
- ✅ "Dark mode UI - Veel gebruikers werken 's avonds en vinden de lichte UI te fel"
- ❌ "Maak het beter" (te vaag)

### 📖 Improving Documentation

Documentatie verbeteringen zijn super welkom! Dit kan zijn:
- Typo fixes in README.md
- Verduidelijking van onduidelijke uitleg
- Nieuwe voorbeelden toevoegen
- Vertaling naar andere talen (Engels, Duits, Frans)

Kleine docs changes kunnen direct als PR, grote docs changes liever eerst issue.

### 🔧 Code Contributions

Wil je code bijdragen? Geweldig! Volg de stappen hieronder.

## 🚀 Development Setup

### Prerequisites

- Python 3.10 of hoger
- Git
- virtualenv (aanbevolen)

### Setup Steps

```bash
# 1. Fork het project op GitHub
#    Klik op "Fork" knop rechtsboven

# 2. Clone je fork
git clone https://github.com/JE-USERNAME/flask-anonimiseren-tool.git
cd flask-anonimiseren-tool

# 3. Voeg upstream remote toe (om up-to-date te blijven)
git remote add upstream https://github.com/ORIGINAL-OWNER/flask-anonimiseren-tool.git

# 4. Maak virtual environment
python3 -m venv venv

# 5. Activeer virtual environment
source venv/bin/activate  # Linux/Mac
# of
venv\Scripts\activate     # Windows

# 6. Installeer dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Voor testing tools

# 7. Run de applicatie
python app.py

# 8. Open browser
# Ga naar http://localhost:5000
```

### Project Structure

```
flask-anonimiseren-tool/
├── app.py                      # Main Flask application
├── config.py                   # Configuration (dev/prod)
├── anonymizer/                 # Core anonymization logic
│   ├── text_anonymizer.py      # Text/DOCX processing
│   ├── excel_anonymizer.py     # Excel/CSV processing
│   ├── pdf_anonymizer.py       # PDF processing
│   ├── reverse_anonymizer.py   # De-anonymization
│   └── patterns.py             # Pattern library (BSN, IBAN, etc.)
├── routes/                     # API endpoints
│   ├── upload_routes.py
│   ├── processing_routes.py
│   ├── download_routes.py
│   └── reverse_routes.py
├── utils/                      # Utilities
│   ├── encryption.py           # Fernet encryption
│   ├── validators.py           # ReDoS protection, validation
│   └── metrics.py              # Performance monitoring
├── templates/                  # Jinja2 templates
│   ├── base.html
│   └── index.html
├── static/                     # Frontend assets
│   ├── css/styles.css
│   └── js/app.js
└── tests/                      # Test suite
    ├── test_anonymizer.py
    ├── test_routes.py
    └── test_patterns.py
```

## 🔀 Pull Request Process

### 1. Create a Feature Branch

```bash
# Update je fork met latest upstream changes
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch (met duidelijke naam)
git checkout -b feature/amazing-feature
# of
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - Nieuwe functionaliteit (bijv. `feature/multi-sheet-excel`)
- `fix/` - Bug fixes (bijv. `fix/reversible-mode-checkbox`)
- `docs/` - Documentatie (bijv. `docs/improve-readme`)
- `refactor/` - Code refactor (bijv. `refactor/extract-validation`)
- `test/` - Tests toevoegen (bijv. `test/add-pattern-tests`)
- `perf/` - Performance verbetering (bijv. `perf/optimize-excel-processing`)

### 2. Make Your Changes

- Schrijf **duidelijke, leesbare code**
- Volg de [Coding Standards](#coding-standards)
- Voeg **tests** toe voor nieuwe functionaliteit
- Update **documentatie** indien nodig
- Test je changes lokaal met `pytest`

### 3. Commit Your Changes

```bash
# Stage je wijzigingen
git add .

# Commit met duidelijk bericht (zie Commit Guidelines)
git commit -m "feat: add multi-sheet Excel support"

# Push naar je fork
git push origin feature/amazing-feature
```

### 4. Open Pull Request

1. Ga naar je fork op GitHub
2. Klik "Compare & pull request"
3. Vul de PR template in:

```markdown
## Description
Korte beschrijving van wat deze PR doet.

## Type of Change
- [ ] Bug fix (non-breaking change die een issue oplost)
- [ ] New feature (non-breaking change die functionaliteit toevoegt)
- [ ] Breaking change (fix of feature die bestaande functionaliteit breekt)
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Unit tests toegevoegd/geüpdatet
- [ ] Handmatig getest op [OS/browser]
- [ ] Alle bestaande tests passeren

## Checklist
- [ ] Code volgt project style guidelines
- [ ] Self-review gedaan
- [ ] Comments toegevoegd voor complexe code
- [ ] Documentatie geüpdatet
- [ ] Geen nieuwe warnings
- [ ] Tests toegevoegd die nieuwe functionaliteit bewijzen
- [ ] Alle tests passeren lokaal

## Screenshots (indien relevant)
[Voeg screenshots toe van UI changes]

## Related Issues
Fixes #123
Related to #456
```

4. Wacht op review feedback
5. Maak requested changes indien nodig
6. PR wordt gemerged door maintainer 🎉

## 📝 Coding Standards

### Python Code Style

We volgen **PEP 8** met kleine aanpassingen:

```python
# Good ✅
def anonymize_text(text: str, rules: List[AnonymizationRule]) -> str:
    """
    Anonymize text based on provided rules.

    Args:
        text: Input text to anonymize
        rules: List of anonymization rules to apply

    Returns:
        Anonymized text string

    Example:
        >>> rules = [AnonymizationRule(pattern=r'\d{4}', replacement='XXXX')]
        >>> anonymize_text("My BSN is 1234", rules)
        'My BSN is XXXX'
    """
    for rule in rules:
        text = re.sub(rule.pattern, rule.replacement, text)
    return text


# Bad ❌
def anon(t, r):  # No type hints, unclear names
    for x in r:
        t = re.sub(x.p, x.r, t)
    return t
```

### Key Principles

1. **Type Hints**: Gebruik type hints voor function parameters en returns
   ```python
   def process_file(filepath: str, rules: List[Rule]) -> Tuple[str, List[str]]:
   ```

2. **Docstrings**: Schrijf docstrings voor alle publieke functies/classes
   ```python
   """
   Short one-line description.

   Longer description if needed.

   Args:
       param1: Description
       param2: Description

   Returns:
       Description of return value

   Raises:
       ValueError: When something goes wrong
   """
   ```

3. **Naming Conventions**:
   - `snake_case` voor functies en variabelen
   - `PascalCase` voor classes
   - `UPPER_CASE` voor constanten
   - Duidelijke, beschrijvende namen (niet `x`, `tmp`, `data`)

4. **Line Length**: Max 100 karakters (niet de standaard 79)

5. **Imports**: Gegroepeerd en gesorteerd
   ```python
   # Standard library
   import os
   import sys
   from typing import List, Dict

   # Third-party
   import flask
   from werkzeug.utils import secure_filename

   # Local
   from anonymizer.text_anonymizer import TextAnonymizer
   from utils.validators import validate_file
   ```

### JavaScript Code Style

```javascript
// Good ✅
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.success) {
            showSuccessMessage(data.filename);
        } else {
            showError(data.error);
        }
    } catch (error) {
        showError('Upload failed: ' + error.message);
    }
}

// Bad ❌
function upload(f) {
    var fd = new FormData();
    fd.append('file', f);
    fetch('/api/upload', {method: 'POST', body: fd}).then(r => r.json()).then(d => {
        if (d.success) { alert('ok'); } else { alert('error'); }
    });
}
```

### CSS Code Style

```css
/* Good ✅ */
.upload-card {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.upload-card:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    transition: box-shadow 0.3s ease;
}

/* Bad ❌ */
.upload-card{background-color:#fff;border-radius:8px;padding:20px;}
```

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_patterns.py

# Run specific test function
pytest tests/test_patterns.py::test_bsn_validation
```

### Writing Tests

We gebruiken `pytest` voor alle tests. Elke nieuwe feature MOET tests hebben.

```python
# tests/test_patterns.py

import pytest
from anonymizer.patterns import PatternMatcher

class TestBSNValidation:
    """Tests for BSN (Dutch social security number) validation."""

    def test_valid_bsn_passes_checksum(self):
        """Valid BSN should pass 11-proef checksum."""
        matcher = PatternMatcher()
        result = matcher.validate_bsn("123456782")  # Valid BSN
        assert result is True

    def test_invalid_bsn_fails_checksum(self):
        """Invalid BSN should fail 11-proef checksum."""
        matcher = PatternMatcher()
        result = matcher.validate_bsn("123456783")  # Invalid checksum
        assert result is False

    @pytest.mark.parametrize("invalid_bsn", [
        "000000000",  # All zeros (deny list)
        "111111111",  # All ones (deny list)
        "12345678",   # Too short
        "1234567890", # Too long
    ])
    def test_deny_list_bsns_rejected(self, invalid_bsn):
        """Common fake BSNs should be rejected."""
        matcher = PatternMatcher()
        result = matcher.validate_bsn(invalid_bsn)
        assert result is False
```

### Test Coverage

We streven naar **>80% coverage** voor nieuwe code. Check coverage met:

```bash
pytest --cov=. --cov-report=term-missing
```

### Test Types

1. **Unit Tests**: Test individuele functies in isolatie
2. **Integration Tests**: Test hoe componenten samenwerken
3. **Edge Case Tests**: Test randgevallen, errors, edge cases

## 📝 Commit Message Guidelines

We volgen **Conventional Commits** voor consistente commit messages:

### Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types

- `feat:` - Nieuwe feature
- `fix:` - Bug fix
- `docs:` - Documentatie wijzigingen
- `style:` - Code formatting (geen logic changes)
- `refactor:` - Code refactor (geen behavior change)
- `perf:` - Performance verbetering
- `test:` - Tests toevoegen/updaten
- `chore:` - Build process, dependencies

### Scope (optioneel)

- `(excel)` - Excel gerelateerd
- `(patterns)` - Pattern matching
- `(ui)` - User interface
- `(api)` - API endpoints
- `(security)` - Security gerelateerd

### Examples

```bash
# Good ✅
git commit -m "feat(excel): add multi-sheet support"
git commit -m "fix(ui): reversible mode checkbox now visible in Excel tab"
git commit -m "docs: update README with installation steps"
git commit -m "refactor(patterns): extract BSN validation to separate function"
git commit -m "test: add unit tests for IBAN checksum validation"

# Bad ❌
git commit -m "changes"
git commit -m "fixed bug"
git commit -m "updates"
git commit -m "WIP"
```

### Breaking Changes

Voor breaking changes, voeg `BREAKING CHANGE:` toe aan footer:

```bash
git commit -m "feat(api): change reversible mode parameter name

BREAKING CHANGE: API parameter 'reversible' renamed to 'reversibleMode' for consistency"
```

## ❓ Questions?

### Waar kan ik hulp vragen?

- **Bug reports**: [GitHub Issues](https://github.com/username/repo/issues)
- **Feature ideas**: [GitHub Discussions](https://github.com/username/repo/discussions)
- **General questions**: Open een issue met tag `question`
- **Security issues**: Zie [SECURITY.md](SECURITY.md) voor responsible disclosure

### Nieuwe contributor?

Zoek naar issues met label `good first issue` - dit zijn geschikte issues voor beginners!

### Code review duurt lang?

Wees geduldig! Maintainers doen dit in hun vrije tijd. Gemiddelde review tijd is 3-7 dagen.

## 🎉 Recognition

Alle contributors worden:
- Vermeld in [CREDITS.md](CREDITS.md)
- Getoond op GitHub Contributors page
- Bedankt in release notes

## 📜 License

Door bij te dragen, ga je akkoord dat je contributions gelicenseerd worden onder de [MIT License](LICENSE).

---

**Bedankt voor je bijdrage!** 🙏

Elke contribution, groot of klein, wordt enorm gewaardeerd. Je maakt dit project beter voor iedereen! ❤️
