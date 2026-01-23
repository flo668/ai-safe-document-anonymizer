# Changelog - Multi-Bestand Anonimiseren Tool

Alle belangrijke wijzigingen in dit project worden gedocumenteerd in dit bestand.

Het formaat is gebaseerd op [Keep a Changelog](https://keepachangelog.com/nl/1.0.0/),
en dit project volgt [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0-beta] - 2025-12-31

### ✨ Toegevoegd

#### Code Quality & Architectuur
- Refactored monolithic app.py (789 regels) naar gemodulariseerde blueprint structuur
- Nieuwe routes module met logische scheiding (main, upload, processing, download, reverse)
- Utils module met herbruikbare helpers (file_utils, session_utils, validation, logger)
- Structured JSON logging met timestamp en context voor productie debugging
- Type hints en docstrings door hele codebase

#### Testing & Kwaliteit
- Pytest foundation met 70%+ code coverage target
- Unit tests voor alle anonymizer modules (text, excel, pdf, patterns, reverse)
- Integration tests voor API endpoints
- Test fixtures voor document types (txt, docx, xlsx, pdf)
- pytest.ini configuratie met coverage rapportage
- requirements-dev.txt voor development dependencies

#### Security
- Enhanced input validation module (validation.py)
- MIME type verificatie naast extensie checks
- Session ID en File ID validatie met UUID format checks
- Improved file upload restrictions met size limits
- Security audit completed

#### Excel Functionaliteit
- **Reversible Mode per kolom**: Radio button keuze tussen vaste waarde en unieke placeholders
- **Column Subtypes**: Predefined types (Supplier, Artikelnaam, Artikelnummer, Provider) met auto-prefixes
- **Excel Preview Caching**: Client-side cache voorkomt onnodige server calls
- **Green Theme Consistency**: Volledige groene kleurstelling voor Excel preview en alle UI elementen
- **A1 Cell Opening**: Excel bestanden openen nu correct op cel A1 in plaats van laatste gebruikte cel
- **Excel Warning Documentation**: Uitgebreide info box met uitleg over twee beveiligingspopups

#### Pattern Matching
- Nieuwe `MOBILE_SINGLE_SPACE` pattern voor "06 12345678" format
- Verbeterde Nederlandse telefoonnummer detectie (11+ patterns)
- Support voor diverse spatie/dash variaties

#### UI/UX Verbeteringen
- Colored tab borders (blauw voor Tekst, groen voor Excel) zelfs wanneer inactief
- Visible radio buttons met duidelijke styling (1.5rem, witte check dot)
- Improved reversible mode uitleg direct onder radio buttons
- Green scrollbar in Excel preview modal voor consistentie
- Removed speaker icon en andere storende elementen
- Optimized log view met beperkt aantal regels (5 in plaats van 25+)

#### Documentatie
- **CHANGELOG.md**: Compleet versie overzicht met changelog conventies
- Updated all version references naar v0.9.0 Beta
- Corrected line counts in documentation (app.py: 789, index.html: 721, app.js: 1121, styles.css: 931)
- Updated dependencies naar current versions (Flask 3.1.0, openpyxl 3.1.5, etc.)
- Voorbereiding documentatie voor email anonymization (v1.0) en standalone apps

### 🔧 Gewijzigd

#### Refactoring
- app.py: 789 → ~150 regels (75% reductie door blueprint extractie)
- Replaced print() statements met structured logger calls
- Improved error handling met exc_info logging
- Session cleanup als dedicated utility module

#### UI Aanpassingen
- Excel preview table headers: CSS variables → hardcoded hex colors (#217346)
- Radio button spacing: 0.75rem margin-right voor betere leesbaarheid
- Info boxes: Verwijderd storende borders en lightbulb emoji's
- Modal kleuren: Consistent green theme met !important flags

### 🐛 Opgelost

#### Pattern Detection
- Fixed "06 28659589" format niet gedetecteerd (toegevoegd MOBILE_SINGLE_SPACE pattern)
- Fixed phone pattern regex om alle spatie variaties te ondersteunen

#### Excel Issues
- Fixed preview modal bleef blauw in alle browsers (hardcoded hex colors nodig)
- Fixed Excel bestanden openen op verkeerde cel (SheetView.topLeftCell implementatie)
- Fixed alle kolommen krijgen zelfde placeholder prefix (columnSubtype toegevoegd)
- Fixed Excel warning info box verscheen te vroeg (removed from updateDeanonColors)

#### UI Bugs
- Fixed radio buttons niet zichtbaar ("ghost" checkboxes)
- Fixed optgroup labels onleesbaar in dark mode (vervangen door disabled separator)
- Fixed Excel warning info blijft zichtbaar bij switch naar Text tab

### 🔒 Security

- Input validation voor alle file uploads (extensie + MIME type)
- Session ID validatie (UUID format checks)
- File size limits (MAX_CONTENT_LENGTH: 100MB)
- Sanitized filenames voor veilige opslag
- Improved session isolation en cleanup

### 📚 Documentatie

- CHANGELOG.md aangemaakt met volledige versiegeschiedenis
- Versie consistency across base.html, CLAUDE.md, project-context.md, README.md
- Regel counts gecorrigeerd in technische documentatie
- Dependencies versies up-to-date in alle docs

### ⚡ Breaking Changes

**Geen** - Deze release is volledig backward compatible met v0.3.

Alle bestaande sessies, mapping.json files, en API calls blijven werken.

---

## [0.3.0] - 2025-12-27

### ✨ Toegevoegd
- Reversible Mode voor zowel Word als Excel
- Bootstrap Icons door hele app (vervangt emoji's)
- Tooltips bij alle instellingen (? iconen met uitleg)
- Sessie knop rechtsboven met tooltip
- Error messages tonen nu bestandsnaam

### 🔧 Gewijzigd
- Kleurconsistentie: Word Blue voor Word tab, Excel Green voor Excel tab, Terra Orange voor globale elementen
- File item kleuren: terra oranje voor Word, groen voor Excel
- Badge tekst toont "ANONYMIZED" in hoofdletters

### 🐛 Opgelost
- Fixed: "Unknown file type" bug (.meta.json werd per ongeluk gepakt)
- Fixed: `generalPlaceholder` undefined error in JavaScript
- Fixed: Duplicate "Start Nieuwe Sessie" knop verwijderd

---

## [0.2.0] - 2025-11-20

### ✨ Toegevoegd
- Automatische detectie Nederlandse telefoonnummers en emails
- PDF ondersteuning met pdfplumber en reportlab
- Reversible anonymization met mapping.json
- De-anonimisatie feature
- Excel preview functionaliteit
- Aangepaste placeholders voor telefoon/email
- Statistics in process response

### 🔧 Gewijzigd
- Tabbed UI (Word/Tekst en Excel gescheiden)
- Settings verplaatst naar binnen tabs

---

## [0.1.0] - 2025-10-15

### ✨ Toegevoegd
- Initial Flask implementation
- Text/DOCX anonimisatie met regex
- Excel kolom-gebaseerde anonimisatie
- Session management met UUID
- ZIP download functionaliteit
- Auto cleanup oude bestanden (24 uur)

---

## Legenda

- ✨ Toegevoegd: Nieuwe features
- 🔧 Gewijzigd: Wijzigingen in bestaande functionaliteit
- 🐛 Opgelost: Bug fixes
- 🔒 Security: Security verbeteringen
- 📚 Documentatie: Documentatie updates
- ⚡ Breaking Changes: Niet backward compatible wijzigingen
