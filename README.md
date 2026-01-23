# Flask Anonimiseren Tool - Multi-Bestand Anonimisatie Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.1](https://img.shields.io/badge/flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![Live Demo](https://img.shields.io/badge/demo-live-success.svg)](https://apps.nightstory.nl/anonimiseren/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> **Privacy-preserving document processing** - Server-side multi-bestand anonimisatie tool met geavanceerde features voor tekst, Word, Excel en PDF documenten.

[🌐 Live Demo](https://apps.nightstory.nl/anonimiseren/) | [📖 Documentation](docs/) | [🐛 Report Bug](https://github.com/username/repo/issues) | [💡 Request Feature](https://github.com/username/repo/issues/new?labels=enhancement)

## ✨ Features

### 📁 Bestandsondersteuning
- ✅ **Tekst**: .txt bestanden
- ✅ **Word**: .docx documenten
- ✅ **Excel**: .xlsx en .csv spreadsheets
- ✅ **PDF**: .pdf documenten (met auto-detectie)

### 🎯 Anonimisatie Methoden

#### Word/Tekst
- **Automatische Detectie**: Nederlandse telefoonnummers (06, +31) en e-mailadressen
- **Handmatige Regels**: Regex support met case-sensitive opties
- **Reversible Mode**: Sla mapping.json op om later te de-anonimiseren
- **Aangepaste Placeholders**: Configureerbare vervangingen voor telefoon/email

#### Excel
- **Kolom-gebaseerde Anonimisatie**: Selecteer kolommen om te anonimiseren
- **Excel Preview**: Bekijk kolommen en eerste 5 rijen voor verwerking
- **Meerdere Methoden**:
  - Masking (eerste/laatste N karakters tonen)
  - Hashing (SHA-256 met optionele salt)
  - Replacement (vaste waarde)
  - Removal (cel leegmaken)
- **Reversible Mode**: Mapping.json voor Excel data
- **Header Preservation**: Kolomnamen blijven behouden

### 🎨 User Interface
- **Tabbed Interface**: Aparte tabs voor Word/Tekst en Excel
- **Kleurcodering**:
  - 🔵 Word Blue: Word/Tekst features
  - 🟢 Excel Green: Excel features
  - 🟠 Terra Orange: Globale acties (Download ZIP, Sessie)
- **Bootstrap Icons**: Consistente, professionele iconografie
- **Tooltips**: Uitleg bij elke instelling (? iconen)
- **Real-time Feedback**: Progress indicators en duidelijke error messages

### 🔄 Workflow Features
- **Multi-file Upload**: Upload meerdere bestanden tegelijk
- **Batch Processing**: Verwerk alle bestanden in één keer
- **ZIP Download**: Download alle geanonimiseerde bestanden + mapping.json
- **Session Management**: 24-uurs sessies met automatische cleanup
- **De-anonimisatie**: Gebruik mapping.json om proces om te keren

### 🛡️ Security & Privacy
- **Session Isolatie**: Elk sessie krijgt eigen directory
- **Automatische Cleanup**: Bestanden verwijderd na 24 uur
- **Geen Data Lekkage**: Bestanden tussen sessies gescheiden
- **Secure File Handling**: Metadata files voor originele bestandsnamen

## 🚀 Snelstart (Lokaal Testen)

### 1. Python Virtual Environment

```bash
cd flask-anonimiseren-tool
python3 -m venv venv
source venv/bin/activate  # Op Windows: venv\Scripts\activate
```

### 2. Dependencies Installeren

```bash
pip install -r requirements.txt
```

Installeerde packages:
- Flask 3.1.0 - Web framework
- python-docx 1.1.2 - Word document processing
- openpyxl 3.1.5 - Excel processing
- pdfplumber 0.11.4 - PDF text extraction
- reportlab 4.2.5 - PDF creation
- Werkzeug 3.1.3 - WSGI utilities
- Gunicorn 23.0.0 - Production server

### 3. Environment Setup

```bash
# Kopieer environment template
cp .env.example .env

# Edit .env en pas SECRET_KEY aan
nano .env
```

### 4. Run Development Server

```bash
# Development mode (Flask debug server)
python app.py

# Of met Flask CLI
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run
```

De app draait nu op: **http://localhost:5001** (of 5000 als 5001 bezet is)

## 🌐 Production Deployment

**Status**: ✅ LIVE
**URL**: https://apps.nightstory.nl/anonimiseren/
**Deployed**: 3 januari 2026

### Live URLs
- **Dashboard**: https://apps.nightstory.nl/ - Overzicht van alle apps
- **Anonimiseren Tool**: https://apps.nightstory.nl/anonimiseren/ - Deze app
- **Tableau Analyzer**: https://apps.nightstory.nl/tableau/
- **Excel Analyzer**: https://apps.nightstory.nl/excel/
- **Callsheet Anonimizer**: https://apps.nightstory.nl/callsheet/

### Deployment Documentatie
- **DEPLOYMENT_INSTRUCTIONS.md**: Stap-voor-stap deployment handleiding
- **LESSONS_LEARNED.md**: Belangrijke troubleshooting & best practices
- **deploy.sh**: Geautomatiseerd deployment script

### Technische Details
- **Server**: TransIP VPS (Ubuntu 24.04)
- **Web Server**: Nginx + Gunicorn
- **SSL**: Let's Encrypt automatisch certificaat
- **Port**: 5002 (intern), proxied via Nginx
- **Auto-start**: Systemd service `flask-anonimiseren`
- **Cleanup**: Automatisch na 24 uur

### Localhost vs Production
- **Localhost**: `http://localhost:5001` (development, Werkzeug)
- **Production**: `https://apps.nightstory.nl/anonimiseren/` (Gunicorn + Nginx)
- **Static Path**: Automatisch aangepast via `STATIC_URL_PATH` environment variable
- **Design**: Identiek op beide omgevingen

> 📖 Voor deployment instructies, zie `deployment/DEPLOYMENT_INSTRUCTIONS.md`

## 📖 Gebruikshandleiding

### Word/Tekst Anonimisatie

1. **Upload Bestanden**: Klik "Kies Bestanden" in de Word/Tekst tab
2. **Configureer Instellingen**:
   - ✅ **Automatische Detectie**: Vindt telefoonnummers en emails automatisch
   - 📞 **Telefoon Placeholder**: Standaard `[TEL VERWIJDERD]`
   - 📧 **Email Placeholder**: Standaard `[EMAIL VERWIJDERD]`
   - 🔄 **Reversible Mode**: Sla mapping.json op voor de-anonimisatie
3. **Voeg Handmatige Regels Toe** (optioneel):
   - Zoekterm: Tekst om te vinden
   - Vervangterm: Waarmee te vervangen
   - ☑️ Regex: Gebruik reguliere expressies
   - ☑️ Hoofdlettergevoelig: "Test" ≠ "test"
   - ☑️ Verwijderen: Verwijder in plaats van vervangen
4. **Verwerk**: Klik "Start Anonimisatie"
5. **Download**: Download individuele bestanden of "Download Alle Bestanden (ZIP)"

### Excel Anonimisatie

1. **Upload Bestanden**: Klik "Kies Bestanden" in de Excel tab
2. **Preview Bekijken**: Klik "Bekijk Preview" om kolommen te zien
3. **Configureer Excel Instellingen**:
   - 🔄 **Reversible Mode**: Mapping.json voor omkeerbare anonimisatie
4. **Voeg Kolom Regels Toe**:
   - **Kolomnaam**: Naam van de kolom om te anonimiseren
   - **Kolom Type**: Text, Email, Telefoon, etc.
   - **Anonimisatie Type**:
     - **Masking**: Toon eerste/laatste N karakters, verberg midden
     - **Hashing**: SHA-256 hash (optioneel met salt)
     - **Replacement**: Vervang met vaste waarde
     - **Removal**: Maak cel leeg
   - **Parameters**: Afhankelijk van gekozen type
5. **Verwerk**: Klik "Start Excel Anonimisatie"
6. **Download**: ZIP bevat geanonimiseerde Excel + mapping.json

### De-anonimisatie

1. **Upload Mapping.json**: In de "De-Anonimisatie" sectie
2. **Upload Geanonimiseerd Bestand**: Het bestand dat je wilt omkeren
3. **Verwerk**: Klik "Start De-Anonimisatie"
4. **Download**: Originele data is hersteld

## 🏗️ Project Structuur

```
flask-anonimiseren-tool/
├── app.py                      # Main Flask application
├── config.py                   # Configuratie (dev/prod)
├── requirements.txt            # Python dependencies
├── gunicorn.conf.py           # Gunicorn productie config
├── nginx.conf.example         # Nginx reverse proxy config
├── anonimiseren-tool.service  # Systemd service
├── .env.example               # Environment variabelen template
├── .gitignore                 # Git ignore rules
│
├── anonymizer/
│   ├── __init__.py
│   ├── text_anonymizer.py     # Text/DOCX processing met auto-detectie
│   ├── excel_anonymizer.py    # Excel/CSV processing
│   ├── pdf_anonymizer.py      # PDF processing
│   └── models.py              # AnonymizationRule, ExcelColumnRule, AnonymizationMapping
│
├── templates/
│   ├── base.html              # Base template met Bootstrap 5.3.2
│   └── index.html             # Main interface (tabbed UI)
│
├── static/
│   ├── css/
│   │   └── styles.css         # Custom styling (Word Blue, Excel Green, Terra Orange)
│   └── js/
│       └── app.js             # Frontend logic met Bootstrap tooltips
│
├── uploads/                   # Temp uploaded files (auto-created, session-gebaseerd)
├── output/                    # Processed files (auto-created, session-gebaseerd)
└── logs/                      # Application logs (create manually voor productie)
```

## 🔌 API Endpoints

### POST /api/upload
Upload bestanden

**Request**: `multipart/form-data` met `files[]`

**Response**:
```json
{
  "success": true,
  "files": [{
    "id": "uuid",
    "originalName": "document.docx",
    "fileType": "docx",
    "size": 15420,
    "status": "uploaded"
  }],
  "sessionId": "session-uuid"
}
```

### POST /api/preview
Preview auto-detectie voor bestanden

**Request**:
```json
{
  "fileIds": ["file-uuid"],
  "phonePlaceholder": "[TEL VERWIJDERD]",
  "emailPlaceholder": "[EMAIL VERWIJDERD]"
}
```

**Response**:
```json
{
  "success": true,
  "previews": [{
    "id": "file-uuid",
    "originalName": "test.txt",
    "detectedPhones": ["06-12345678", "+31612345678"],
    "detectedEmails": ["test@example.com"],
    "previewText": "Eerste 500 karakters..."
  }]
}
```

### POST /api/process
Verwerk bestanden met regels

**Request**:
```json
{
  "fileIds": ["file-uuid"],
  "rules": [{
    "id": "rule-uuid",
    "originalTerm": "John",
    "replacementTerm": "[NAAM]",
    "isRegex": false,
    "caseSensitive": false,
    "removeInsteadOfReplace": false
  }],
  "excelRules": [{
    "id": "rule-uuid",
    "columnName": "Email",
    "columnType": "email",
    "anonymizationType": "hashing",
    "parameters": {
      "hashAlgorithm": "sha256",
      "useSalt": true
    }
  }],
  "activeTab": "text",
  "phonePlaceholder": "[TEL VERWIJDERD]",
  "emailPlaceholder": "[EMAIL VERWIJDERD]",
  "generalPlaceholder": "[ANONIEM]",
  "autoDetectEnabled": true,
  "reversibleMode": false
}
```

**Response**:
```json
{
  "success": true,
  "results": [{
    "id": "file-uuid",
    "status": "anonymized",
    "originalName": "test.txt",
    "anonymizedName": "test_ann_1430.txt",
    "logs": [...],
    "auto_detect_report": {
      "phone_numbers": {
        "count": 3,
        "examples": ["06-12345678"]
      },
      "emails": {
        "count": 2,
        "examples": ["test@example.com"]
      }
    }
  }],
  "logs": [...],
  "statistics": {
    "total_phones": 3,
    "total_emails": 2,
    "total_manual_replacements": 5
  },
  "mappingAvailable": true,
  "mappingId": "session-uuid",
  "totalMappings": 10
}
```

### GET /api/download/\<file_id\>
Download geanonimiseerd bestand

### GET /api/download-all
Download alle bestanden als ZIP (inclusief mapping.json bij reversible mode)

### GET /api/download-mapping/\<mapping_id\>
Download mapping.json voor de-anonimisatie

### POST /api/cleanup
Cleanup sessie bestanden

### POST /api/deanonymize
De-anonimiseer bestand met mapping.json

## ⚙️ Configuratie

### Environment Variabelen (.env)

```bash
FLASK_ENV=development          # development | production
SECRET_KEY=your-secret-key     # Wijzig in productie! (genereer met: python -c "import secrets; print(secrets.token_hex(32))")
HOST=0.0.0.0                   # Server host
PORT=5000                      # Server port
CLEANUP_OLDER_THAN_HOURS=24    # Auto cleanup tijd
MAX_CONTENT_LENGTH_MB=100      # Max upload size
```

### config.py Opties

- `MAX_CONTENT_LENGTH`: Max file size (100MB default)
- `ALLOWED_EXTENSIONS`: `{'txt', 'docx', 'xlsx', 'csv', 'pdf'}`
- `UPLOAD_FOLDER`: `uploads/` (session-gebaseerd)
- `OUTPUT_FOLDER`: `output/` (session-gebaseerd)
- `CLEANUP_OLDER_THAN_HOURS`: 24 uur default
- `SEND_FILE_MAX_AGE_DEFAULT`: 0 (disable caching voor development)

## 🖥️ VPS Deployment

### Stap 1: Server Voorbereiding

```bash
# Update systeem
sudo apt update && sudo apt upgrade -y

# Installeer Python en dependencies
sudo apt install python3 python3-pip python3-venv nginx -y

# Maak application user
sudo useradd -m -s /bin/bash anonimiseren
```

### Stap 2: Project Setup

```bash
# Clone of upload project naar VPS
sudo mkdir -p /var/www/anonimiseren-tool
sudo chown anonimiseren:anonimiseren /var/www/anonimiseren-tool
cd /var/www/anonimiseren-tool

# Upload project files
# (via git clone, scp, of andere methode)

# Virtual environment als anonimiseren user
sudo su - anonimiseren
cd /var/www/anonimiseren-tool/flask-anonimiseren-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Environment configuratie
cp .env.example .env
nano .env  # Edit: SECRET_KEY, FLASK_ENV=production

# Maak logs directory
mkdir -p logs
```

### Stap 3: Gunicorn Setup

```bash
# Test Gunicorn
gunicorn -c gunicorn.conf.py app:app

# Als het werkt, installeer als systemd service
exit  # Terug naar root/sudo user
sudo cp /var/www/anonimiseren-tool/flask-anonimiseren-tool/anonimiseren-tool.service /etc/systemd/system/
sudo nano /etc/systemd/system/anonimiseren-tool.service
# Pas paden aan naar jouw setup

# Enable en start service
sudo systemctl daemon-reload
sudo systemctl enable anonimiseren-tool
sudo systemctl start anonimiseren-tool
sudo systemctl status anonimiseren-tool
```

### Stap 4: Nginx Setup

```bash
# Kopieer en edit nginx config
sudo cp /var/www/anonimiseren-tool/flask-anonimiseren-tool/nginx.conf.example /etc/nginx/sites-available/anonimiseren-tool
sudo nano /etc/nginx/sites-available/anonimiseren-tool
# Pas server_name, paths en client_max_body_size aan

# Enable site
sudo ln -s /etc/nginx/sites-available/anonimiseren-tool /etc/nginx/sites-enabled/

# Remove default site (optioneel)
sudo rm /etc/nginx/sites-enabled/default

# Test en reload
sudo nginx -t
sudo systemctl reload nginx
```

### Stap 5: SSL/HTTPS met Let's Encrypt

```bash
# Installeer Certbot
sudo apt install certbot python3-certbot-nginx -y

# Verkrijg SSL certificaat
sudo certbot --nginx -d jouw-domein.com -d www.jouw-domein.com

# Auto-renewal is standaard enabled
sudo certbot renew --dry-run

# Check auto-renewal timer
sudo systemctl status certbot.timer
```

### Stap 6: Firewall

```bash
# Configureer UFW
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
sudo ufw status
```

## 📊 Monitoring & Logging

### Systemd Service Logs

```bash
# Real-time logs
sudo journalctl -u anonimiseren-tool -f

# Laatste 50 regels
sudo journalctl -u anonimiseren-tool -n 50

# Logs sinds vandaag
sudo journalctl -u anonimiseren-tool --since today
```

### Gunicorn Logs

```bash
# Access logs
tail -f /var/www/anonimiseren-tool/flask-anonimiseren-tool/logs/gunicorn-access.log

# Error logs
tail -f /var/www/anonimiseren-tool/flask-anonimiseren-tool/logs/gunicorn-error.log
```

### Nginx Logs

```bash
# Access logs
sudo tail -f /var/log/nginx/anonimiseren-access.log

# Error logs
sudo tail -f /var/log/nginx/anonimiseren-error.log
```

### Handmatige Cleanup

```bash
# Cleanup oude sessies
cd /var/www/anonimiseren-tool/flask-anonimiseren-tool
source venv/bin/activate
python -c "from app import create_app, cleanup_old_files; app = create_app('production'); cleanup_old_files(app)"
```

## 🐛 Troubleshooting

### App start niet

```bash
# Check logs
sudo journalctl -u anonimiseren-tool -n 50

# Check permissions
ls -la /var/www/anonimiseren-tool/flask-anonimiseren-tool/uploads/
ls -la /var/www/anonimiseren-tool/flask-anonimiseren-tool/output/

# Handmatig starten voor debugging
sudo su - anonimiseren
cd /var/www/anonimiseren-tool/flask-anonimiseren-tool
source venv/bin/activate
FLASK_DEBUG=1 python app.py
```

### Upload lukt niet

```bash
# Check nginx max upload size
sudo nano /etc/nginx/sites-available/anonimiseren-tool
# client_max_body_size moet >= MAX_CONTENT_LENGTH zijn (bijv. 100M)

# Check directory permissions
sudo chown -R anonimiseren:anonimiseren /var/www/anonimiseren-tool/flask-anonimiseren-tool/uploads/
sudo chown -R anonimiseren:anonimiseren /var/www/anonimiseren-tool/flask-anonimiseren-tool/output/
sudo chmod -R 755 /var/www/anonimiseren-tool/flask-anonimiseren-tool/uploads/
sudo chmod -R 755 /var/www/anonimiseren-tool/flask-anonimiseren-tool/output/

# Restart services
sudo systemctl restart anonimiseren-tool
sudo systemctl reload nginx
```

### "Unknown file type" error

Dit gebeurde bij .docx bestanden door een bug waarbij `.meta.json` files per ongeluk werden gepakt.

**Fix**: Geïmplementeerd in versie 0.3 - `.meta.json` files worden nu geskipt tijdens file type detectie.

### Browser cache issues

Chrome en Safari cachen soms agressief. Gebruik Firefox voor development, of:

```bash
# Disable Flask caching in development
# In app.py:
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Hard refresh in browser
Cmd+Shift+R (Mac) / Ctrl+Shift+R (Windows/Linux)
```

### SSL certificaat werkt niet

```bash
# Check DNS records
nslookup jouw-domein.com

# Check firewall
sudo ufw status

# Check nginx config
sudo nginx -t

# Check certbot logs
sudo cat /var/log/letsencrypt/letsencrypt.log

# Retry certbot
sudo certbot --nginx -d jouw-domein.com
```

## 🔒 Security Checklist

- [ ] `SECRET_KEY` aangepast in productie (gebruik: `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] `FLASK_ENV=production` gezet in .env
- [ ] Firewall geconfigureerd (alleen 22, 80, 443)
- [ ] SSL/HTTPS enabled met Let's Encrypt
- [ ] Nginx `client_max_body_size` niet hoger dan nodig
- [ ] Auto-cleanup enabled (24 uur)
- [ ] Application user heeft minimale permissions
- [ ] Logs rotation geconfigureerd
- [ ] Regular backups ingesteld
- [ ] `.env` niet gecommit naar git
- [ ] Gunicorn draait niet als root

## ⚡ Performance Tips

### 1. Gunicorn Workers

Pas aan in `gunicorn.conf.py`:

```python
import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1  # Aanbevolen formule
worker_class = 'sync'  # Of 'gthread' voor threading
threads = 2  # Bij gebruik van gthread
timeout = 120  # Voor grote files
```

### 2. Nginx Caching

Uncomment in `nginx.conf.example`:

```nginx
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. File Cleanup

Verlaag `CLEANUP_OLDER_THAN_HOURS` als disk space beperkt is:

```bash
# In .env
CLEANUP_OLDER_THAN_HOURS=6  # 6 uur in plaats van 24
```

### 4. Max Upload Size

Alleen verhogen als echt nodig (security risk):

```bash
# In .env
MAX_CONTENT_LENGTH_MB=50  # In plaats van 100

# Ook aanpassen in nginx.conf
client_max_body_size 50M;
```

## 📝 Changelog

### Version 0.3 (December 2025)
- ✅ Fixed: "Unknown file type" bug (.meta.json werd per ongeluk gepakt)
- ✅ Fixed: Kleurconsistentie - Word Blue voor Word tab, Excel Green voor Excel tab, Terra Orange voor globale elementen
- ✅ Added: Bootstrap Icons door hele app (vervangt emoji's)
- ✅ Added: Tooltips bij alle instellingen (? iconen met uitleg)
- ✅ Added: Reversible Mode voor zowel Word als Excel
- ✅ Added: Sessie knop rechtsboven met tooltip
- ✅ Added: Error messages tonen nu bestandsnaam
- ✅ Improved: File item kleuren - terra oranje voor Word, groen voor Excel
- ✅ Improved: Badge tekst toont "ANONYMIZED" in hoofdletters
- 🐛 Fixed: `generalPlaceholder` undefined error in JavaScript
- 🐛 Fixed: Duplicate "Start Nieuwe Sessie" knop verwijderd

### Version 0.2 (November 2025)
- ✅ Added: Automatische detectie Nederlandse telefoonnummers en emails
- ✅ Added: PDF ondersteuning met pdfplumber en reportlab
- ✅ Added: Reversible anonymization met mapping.json
- ✅ Added: De-anonimisatie feature
- ✅ Added: Excel preview functionaliteit
- ✅ Added: Aangepaste placeholders voor telefoon/email
- ✅ Added: Statistics in process response
- ✅ Improved: Tabbed UI (Word/Tekst en Excel gescheiden)
- ✅ Improved: Settings verplaatst naar binnen tabs

### Version 0.1 (October 2025)
- ✅ Initial Flask implementation
- ✅ Text/DOCX anonimisatie met regex
- ✅ Excel kolom-gebaseerde anonimisatie
- ✅ Session management met UUID
- ✅ ZIP download functionaliteit
- ✅ Auto cleanup oude bestanden

## 🎯 Roadmap

### Geplande Features (v0.4)
- [ ] Excel multi-select kolommen in preview (checkboxes)
- [ ] Kolom autocomplete dropdown met datalist
- [ ] Markdown (.md) ondersteuning
- [ ] Pages (.pages) ondersteuning
- [ ] Numbers (.numbers) ondersteuning
- [ ] Oude Excel (.xls) ondersteuning
- [ ] Reduceer preview rijen naar 5 (in plaats van 10-20)
- [ ] Individuele bestand download optie (naast ZIP)
- [ ] Regel creatie begeleiding ("⚠️ Klik op 'Regel Toevoegen' om de regel op te slaan")
- [ ] Actieve regels teller

### Mogelijk Toekomstig
- [ ] API rate limiting
- [ ] User authentication
- [ ] Bulk operations dashboard
- [ ] Export audit logs
- [ ] Custom anonimisatie templates
- [ ] Multi-language support

## 🤝 Contributing

We verwelkomen contributions van iedereen! Of je nu een bug wilt fixen, een feature wilt toevoegen, of documentatie wilt verbeteren - alle bijdragen zijn welkom.

### Hoe bij te dragen?

1. **🐛 Bug Reports**: Vond je een bug? [Open een issue](https://github.com/username/repo/issues/new)
2. **💡 Feature Requests**: Heb je een idee? [Suggest een feature](https://github.com/username/repo/issues/new?labels=enhancement)
3. **📖 Documentatie**: Zie een typo of onduidelijke uitleg? Open een PR!
4. **🔧 Code**: Wil je code bijdragen? Check [CONTRIBUTING.md](CONTRIBUTING.md) voor guidelines

### Quick Start voor Contributors

```bash
# Fork het project en clone je fork
git clone https://github.com/JE-USERNAME/flask-anonimiseren-tool.git
cd flask-anonimiseren-tool

# Setup development environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Maak feature branch
git checkout -b feature/amazing-feature

# Run tests
pytest

# Push en open PR
git push origin feature/amazing-feature
```

Voor gedetailleerde guidelines, zie [CONTRIBUTING.md](CONTRIBUTING.md).

## 🙏 Credits & Acknowledgments

Dit project zou niet mogelijk zijn zonder de geweldige open source community.

**Hoofdauteur**: Nico Croiset (GHX | Nightstory)

**Dependencies**:
- Flask, python-docx, openpyxl, pdfplumber, reportlab
- Bootstrap, Gunicorn, Nginx

**Inspiratie**:
- Microsoft Presidio (pattern matching research)
- Flask-Session (session management patterns)
- OWASP Security Guidelines (ReDoS protection, formula injection prevention)

Voor volledige lijst van dependencies, code inspiratie en special thanks, zie [CREDITS.md](CREDITS.md).

## 📄 License

Dit project is gelicenseerd onder de [MIT License](LICENSE).

Dit betekent:
- ✅ Commercieel gebruik toegestaan
- ✅ Modificatie toegestaan
- ✅ Distributie toegestaan
- ✅ Privégebruik toegestaan
- ⚠️ License en copyright notice moet behouden blijven
- ⚠️ Geen warranty of liability

Zie [LICENSE](LICENSE) file voor volledige details.

---

**Ontwikkeld met ❤️ voor privacy-compliant data processing**

[![GitHub stars](https://img.shields.io/github/stars/username/repo.svg?style=social&label=Star)](https://github.com/username/repo)
[![GitHub issues](https://img.shields.io/github/issues/username/repo.svg)](https://github.com/username/repo/issues)
