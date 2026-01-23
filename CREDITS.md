# Credits & Acknowledgments

Dit project zou niet mogelijk zijn zonder de geweldige open source community. Hieronder een overzicht van alle dependencies, inspiratiebronnen en bijdragen.

## 📦 Direct Dependencies

### Backend Framework & Core
- **[Flask](https://github.com/pallets/flask)** (BSD-3-Clause) - Web framework
  - Version: 3.1.0
  - Gebruikt voor: Application routing, request handling, templating
- **[Werkzeug](https://github.com/pallets/werkzeug)** (BSD-3-Clause) - WSGI utility library
  - Version: 3.1.3
  - Gebruikt voor: Secure filename handling, request/response utilities
- **[Gunicorn](https://github.com/benoitc/gunicorn)** (MIT) - Production WSGI server
  - Version: 23.0.0
  - Gebruikt voor: Production deployment, worker management

### Document Processing Libraries
- **[python-docx](https://github.com/python-openxml/python-docx)** (MIT) - Word document processing
  - Version: 1.1.2
  - Gebruikt voor: Reading and writing .docx files, paragraph manipulation
- **[openpyxl](https://github.com/theorchard/openpyxl)** (MIT) - Excel processing
  - Version: 3.1.5
  - Gebruikt voor: Reading/writing .xlsx files, cell manipulation, formulas
- **[pdfplumber](https://github.com/jsvine/pdfplumber)** (MIT) - PDF text extraction
  - Version: 0.11.4
  - Gebruikt voor: Reading text from PDF files, table detection
- **[reportlab](https://github.com/MrBitBucket/reportlab-mirror)** (BSD) - PDF generation
  - Version: 4.2.5
  - Gebruikt voor: Writing anonymized PDF files

### Security & Encryption
- **[cryptography](https://github.com/pyca/cryptography)** (Apache-2.0/BSD) - Cryptographic recipes
  - Gebruikt voor: Fernet symmetric encryption voor mapping.json bestanden
  - Implementation: `utils/encryption.py` - SecureMappingStorage class

### Development & Testing
- **[pytest](https://github.com/pytest-dev/pytest)** (MIT) - Testing framework
  - Version: 8.3.4
  - Gebruikt voor: Unit tests, integration tests, coverage reporting
- **[pytest-cov](https://github.com/pytest-dev/pytest-cov)** (MIT) - Coverage plugin
  - Version: 6.0.0
  - Gebruikt voor: Code coverage analysis

### Configuration
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** (BSD-3-Clause) - Environment variable management
  - Version: 1.0.0
  - Gebruikt voor: Loading .env configuration files

## 🎨 Frontend Dependencies (CDN)

- **[Bootstrap](https://github.com/twbs/bootstrap)** (MIT) - CSS framework
  - Version: 5.3.2
  - Gebruikt voor: Responsive layout, components, utilities
- **[Bootstrap Icons](https://github.com/twbs/icons)** (MIT) - Icon library
  - Version: 1.11.1
  - Gebruikt voor: UI icons throughout the application

## 💡 Code Inspiration & Patterns

### Session Management
- **Pattern inspiratie**: [Flask-Session](https://github.com/pallets-eco/flask-session)
  - Gebruikt concept: UUID-based session isolation
  - Onze implementatie: Eigen session management in `app.py` met 24h auto-cleanup

### File Upload Handling
- **Pattern inspiratie**: [Werkzeug Documentation](https://werkzeug.palletsprojects.com/en/stable/utils/#werkzeug.utils.secure_filename)
  - Gebruikt concept: Secure filename sanitization
  - Onze implementatie: `routes/upload_routes.py` met extra file size validation

### Pattern Matching & Validation
- **Research inspiratie**: [Microsoft Presidio](https://github.com/microsoft/presidio)
  - Concept: Multi-layer validation (regex → checksum → context)
  - ⚠️ **Let op**: We gebruiken NIET de Presidio library zelf
  - Onze implementatie: Volledig custom `anonymizer/patterns.py` met:
    - BSN 11-proef checksum validatie
    - IBAN mod-97 checksum validatie
    - Context-aware pattern matching
    - Dutch-specific patterns (telefoonnummers, postcodes)

### ReDoS Protection
- **Pattern inspiratie**: [OWASP ReDoS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Regular_expression_Denial_of_Service_Prevention_Cheat_Sheet.html)
  - Concept: Regex timeout to prevent catastrophic backtracking
  - Onze implementatie: `utils/validators.py` - signal-based timeout (1s limit)

### Excel Formula Injection Prevention
- **Research bron**: [OWASP - Formula Injection](https://owasp.org/www-community/attacks/CSV_Injection)
  - Concept: Escape dangerous formulas in Excel exports
  - Onze implementatie: `anonymizer/excel_anonymizer.py` - prepend single quote to `=`, `+`, `-`, `@`

## 🌟 Special Thanks

### Development Tools
- **[Claude](https://claude.ai/)** (Anthropic) - AI assistant voor development, code review, en architecture design
- **[VS Code](https://github.com/microsoft/vscode)** (MIT) - Code editor
- **[Git](https://git-scm.com/)** (GPL-2.0) - Version control

### Infrastructure & Hosting
- **[TransIP](https://www.transip.nl/)** - VPS hosting provider (Ubuntu 24.04)
- **[Nginx](https://github.com/nginx/nginx)** (BSD-2-Clause) - Reverse proxy en static file serving
- **[Let's Encrypt](https://letsencrypt.org/)** - SSL/TLS certificates
- **[Systemd](https://github.com/systemd/systemd)** (LGPL-2.1+) - Service management

### Research & Documentation
- **[RDW BSN Specification](https://www.rvig.nl/bsn)** - BSN 11-proef checksum algorithm
- **[IBAN Registry](https://www.swift.com/standards/data-standards/iban)** - IBAN mod-97 validation
- **[GDPR Guidelines](https://gdpr.eu/)** - Privacy compliance research
- **[Flask Documentation](https://flask.palletsprojects.com/)** - Framework reference
- **[Python Docs](https://docs.python.org/3/)** - Language reference

## 🤝 Community Contributions

Bedankt aan alle gebruikers die hebben bijgedragen via:
- 🐛 Bug reports in GitHub Issues
- 💡 Feature suggestions
- 🔍 Code reviews
- 📖 Documentation improvements
- ✅ Testing en feedback

### Contributors
<!-- GitHub auto-generates this list -->
_(Zie [Contributors page](https://github.com/username/repo/graphs/contributors) voor volledige lijst)_

## 📜 License Compatibility

Alle gebruikte libraries zijn compatibel met onze MIT License:
- **MIT**: Volledig compatibel ✅
- **BSD-3-Clause**: Volledig compatibel ✅
- **Apache-2.0**: Volledig compatibel ✅
- **LGPL-2.1+**: Dynamic linking only (geen modificaties) ✅

## 🙏 How to Contribute

Wil je bijdragen aan dit project? Zie [CONTRIBUTING.md](CONTRIBUTING.md) voor guidelines.

---

**Last updated**: 23 januari 2026

*Mis je iets in deze lijst? Open een [issue](https://github.com/username/repo/issues) of [pull request](https://github.com/username/repo/pulls)!*
