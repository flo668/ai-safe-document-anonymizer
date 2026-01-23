# Lessons Learned - VPS Deployment Flask Anonimiseren Tool

**Deployment Datum**: 2-3 januari 2026
**VPS**: TransIP Ubuntu 24.04 (37.97.194.228)
**URL**: https://apps.nightstory.nl/anonimiseren/
**Status**: ✅ LIVE & WERKEND

---

## Executive Summary

Succesvolle deployment van Flask Anonimiseren Tool v0.9.0 Beta naar VPS met multi-app dashboard. Belangrijkste uitdagingen waren **permissions** en **static file serving** in een subpath configuratie.

---

## Deployment Architectuur

### Multi-App Dashboard Setup

**Live Structure**:
```
https://apps.nightstory.nl/              → Dashboard (static HTML)
https://apps.nightstory.nl/tableau/      → Tableau Analyzer (port 8501)
https://apps.nightstory.nl/excel/        → Excel Analyzer (port 8503)
https://apps.nightstory.nl/callsheet/    → Callsheet Anonimizer (port 8502)
https://apps.nightstory.nl/anonimiseren/ → Flask Anonimiseren Tool (port 5002)
```

**App Directory Structure**:
```
/home/nightstory/
├── dashboard/
│   ├── index.html          # Dashboard homepage
│   └── assets/             # Logo, CSS, images
└── apps/
    ├── tableau-analyzer/
    ├── excel-analyzer/
    ├── callsheet-anonimizer/
    └── flask-anonimiseren-tool/
```

---

## Kritieke Lessons Learned

### 1. File Permissions (GROOTSTE ISSUE)

**Probleem**: 503 en 403 errors op static files en dashboard

**Root Cause**: Nginx draait als `www-data` user en heeft execute permissions nodig op ALLE parent directories om bestanden te bereiken.

**Solution**:
```bash
# Home directory MOET 755 zijn (niet 750!)
chmod 755 /home/nightstory/

# Static directories 755
chmod -R 755 /home/nightstory/apps/flask-anonimiseren-tool/static/

# Static files 644 (lees permissions voor alle users)
find /home/nightstory/apps/flask-anonimiseren-tool/static/ -type f -exec chmod 644 {} \;

# Dashboard directory 755
chmod 755 /home/nightstory/dashboard/

# Dashboard assets 755 (directories)
chmod -R 755 /home/nightstory/dashboard/assets/
```

**Critical Discovery**:
- **Symptoom**: `Permission denied` in nginx error log
- **Fix**: Niet alleen file permissions, maar HELE PATH vanaf root moet toegankelijk zijn
- **Check commando**: `namei -l /home/nightstory/apps/flask-anonimiseren-tool/static/css/styles.css`

---

### 2. Static Files in Subpath Deployment

**Probleem**: Flask genereerde `/static/...` URLs, maar app draait op `/anonimiseren/` subpath

**Bad Approach (WERKT NIET)**:
```python
# SCRIPT_NAME environment variable - Causes Bad Request errors
Environment="SCRIPT_NAME=/anonimiseren"
```

**Good Approach**:
```python
# app.py - Custom static_url_path met environment variable
def create_app(config_name='default'):
    static_path = os.environ.get('STATIC_URL_PATH', '/static')  # Default voor localhost!
    app = Flask(__name__, static_url_path=static_path)
    # ...
```

**Systemd Service**:
```ini
Environment="STATIC_URL_PATH=/anonimiseren/static"
```

**Why This Works**:
- ✅ Localhost gebruikt default `/static` → origineel ontwerp behouden
- ✅ VPS gebruikt `/anonimiseren/static` → subpath compatible
- ✅ Geen breaking changes voor development workflow

---

### 3. Nginx Location Block Volgorde

**CRITICAL**: Static files location MOET VOOR de proxy_pass location!

**Correct Volgorde**:
```nginx
# EERST: Static files (specifieke match)
location /anonimiseren/static/ {
    alias /home/nightstory/apps/flask-anonimiseren-tool/static/;
    expires 30d;
}

# DAARNA: Flask proxy (bredere match)
location /anonimiseren/ {
    proxy_pass http://localhost:5002/;
}
```

**Why**: Nginx matcht van boven naar beneden. Als proxy eerst komt, haalt Flask de static files (trager + onnodige load).

---

### 4. Gunicorn Application Factory Pattern

**Probleem**: `ImportError: cannot import name 'app' from 'app'`

**Bad**:
```ini
ExecStart=gunicorn -w 4 -b 127.0.0.1:5002 app:app
```

**Good**:
```ini
ExecStart=gunicorn -w 4 -b 127.0.0.1:5002 "app:create_app()"
```

**Why**: We gebruiken application factory pattern (`create_app()`) ipv direct `app` instance.

---

### 5. Dashboard Filename Convention

**Probleem**: 403 Forbidden op root path

**Root Cause**: Nginx verwacht `index.html`, maar bestand heette `dashboard.html`

**Fix**:
```bash
mv /home/nightstory/dashboard/dashboard.html /home/nightstory/dashboard/index.html
```

**Alternative Fix**: Nginx directive toevoegen:
```nginx
location / {
    index dashboard.html;
    try_files $uri $uri/ /dashboard.html;
}
```

---

### 6. Port Allocation Strategy

**Port Schema**:
- **5001**: Localhost development (alle Flask apps)
- **5002**: Flask Anonimiseren Tool (VPS production)
- **8501**: Tableau Analyzer (Streamlit)
- **8502**: Callsheet Anonimizer
- **8503**: Excel Analyzer

**Best Practice**: Reserveer poort ranges per app type:
- 5000-5099: Flask apps
- 8500-8599: Streamlit/data apps

---

## Troubleshooting Workflow

### Diagnostics Commands

```bash
# 1. Check service status
sudo systemctl status flask-anonimiseren

# 2. Check app responds locally
curl http://localhost:5002/

# 3. Check nginx config
sudo nginx -t

# 4. Check recent nginx errors
sudo tail -f /var/log/nginx/error.log

# 5. Check file permissions PATH
namei -l /home/nightstory/apps/flask-anonimiseren-tool/static/css/styles.css

# 6. Test HTTP response codes
curl -I https://apps.nightstory.nl/anonimiseren/static/css/styles.css
```

### Error Patterns & Solutions

| Error | Symptoom | Fix |
|-------|----------|-----|
| **503 Service Unavailable** | Static files niet bereikbaar | Check file permissions (644) en parent directory permissions (755) |
| **403 Forbidden** | Directory listing verboden | Check home directory permissions (755) of rename naar index.html |
| **502 Bad Gateway** | Flask app niet bereikbaar | Check systemctl status, verify poort, check gunicorn logs |
| **404 Not Found** | Nginx route niet gevonden | Check location blocks volgorde in nginx config |
| **Connection refused** | Port niet open | Check firewall, verify app listens op juiste poort |

---

## Deployment Checklist (Future Reference)

### Pre-Deployment
- [ ] Test app lokaal op localhost:5001
- [ ] Verify `create_app()` factory pattern
- [ ] Check `STATIC_URL_PATH` environment variable support
- [ ] Commit & push code to git
- [ ] Generate SECRET_KEY: `python3 -c "import secrets; print(secrets.token_hex(32))"`

### Packaging
- [ ] Run `deploy.sh` script
- [ ] Verify tar.gz created without venv/tests
- [ ] Upload succesvol naar VPS

### VPS Setup
- [ ] Extract app naar `/home/nightstory/apps/`
- [ ] Create virtual environment
- [ ] Install requirements.txt
- [ ] Create `uploads/` en `output/` directories
- [ ] Create `logs/` directory voor gunicorn

### Systemd Service
- [ ] Copy service file naar `/etc/systemd/system/`
- [ ] Add SECRET_KEY environment variable
- [ ] Add STATIC_URL_PATH environment variable
- [ ] Set correct port number
- [ ] `sudo systemctl daemon-reload`
- [ ] `sudo systemctl start <service>`
- [ ] `sudo systemctl enable <service>`
- [ ] Verify: `sudo systemctl status <service>`

### Nginx Configuration
- [ ] Add location blocks (static VOOR proxy!)
- [ ] Test config: `sudo nginx -t`
- [ ] Reload: `sudo systemctl reload nginx`
- [ ] Verify SSL certificate werkt

### Permissions (KRITIEK!)
- [ ] Home directory: `chmod 755 /home/nightstory/`
- [ ] App directory: `chmod 755 /home/nightstory/apps/<app>/`
- [ ] Static directory: `chmod -R 755 /home/nightstory/apps/<app>/static/`
- [ ] Static files: `find ... -type f -exec chmod 644 {} \;`
- [ ] Dashboard: `chmod 755 /home/nightstory/dashboard/`

### Testing
- [ ] Test localhost: `curl http://localhost:<PORT>/`
- [ ] Test nginx: `curl -I https://apps.nightstory.nl/<path>/`
- [ ] Test static files: `curl -I https://apps.nightstory.nl/<path>/static/css/styles.css`
- [ ] Manual browser test: Upload → Process → Download workflow
- [ ] Check browser console voor errors

---

## Performance Optimizations

### Nginx Caching
```nginx
# Static files - lange cache
location /anonimiseren/static/ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### Gunicorn Workers
```
# Recommended: (2 x CPU cores) + 1
-w 4  # Voor 2-core VPS
```

---

## Security Best Practices

### Environment Variables
```ini
# Systemd service
Environment="SECRET_KEY=<64-char-hex>"          # NOOIT in git!
Environment="FLASK_ENV=production"              # Disable debug mode
Environment="STATIC_URL_PATH=/anonimiseren/static"
```

### File Upload Restrictions
```python
# config.py
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'txt', 'docx', 'xlsx', 'csv', 'pdf', 'md'}
```

### Session Cleanup
```python
# Automatisch verwijderen na 24 uur
CLEANUP_OLDER_THAN_HOURS = 24
```

---

## Localhost vs VPS Verschillen

| Aspect | Localhost | VPS |
|--------|-----------|-----|
| **URL** | http://localhost:5001 | https://apps.nightstory.nl/anonimiseren/ |
| **Static Path** | `/static/` | `/anonimiseren/static/` |
| **Server** | Werkzeug (development) | Gunicorn + Nginx |
| **SSL** | Geen | Let's Encrypt |
| **Port** | 5001 | 5002 (intern) |
| **Environment** | FLASK_ENV=development | FLASK_ENV=production |
| **Design** | ✅ Volledig behouden | ✅ Identiek |

**GARANTIE**: Localhost werkt nog precies zoals ontworpen - niets weggegooid!

---

## Common Mistakes & Pitfalls

### ❌ FOUT: SCRIPT_NAME gebruiken
```python
# Dit veroorzaakt Bad Request errors
Environment="SCRIPT_NAME=/anonimiseren"
```

### ❌ FOUT: Hard-coded static paths
```python
# Werkt niet op VPS subpath
app = Flask(__name__, static_url_path='/static')
```

### ❌ FOUT: Directory permissions vergeten
```bash
# Dit is niet genoeg!
chmod 644 /home/nightstory/apps/flask-anonimiseren-tool/static/css/styles.css
# Je MOET OOK parent directories fixen:
chmod 755 /home/nightstory/
```

### ❌ FOUT: Nginx location volgorde verkeerd
```nginx
# Proxy eerst = static files gaan via Flask (sloom!)
location /anonimiseren/ { ... }
location /anonimiseren/static/ { ... }  # Te laat!
```

### ✅ CORRECT: Environment variable voor static path
```python
static_path = os.environ.get('STATIC_URL_PATH', '/static')
app = Flask(__name__, static_url_path=static_path)
```

---

## Update Procedure (Future Deployments)

```bash
# 1. Lokaal: package nieuwe versie
cd "/Users/ncroiset/Vibe Coding Projecten/Project Anonimiseer_tool_word_excel/flask-anonimiseren-tool"
tar -czf flask-anonimiseren-tool.tar.gz \
    --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.pytest_cache' --exclude='tests' \
    --exclude='uploads/*' --exclude='output/*' --exclude='deployment' .

# 2. Upload
scp flask-anonimiseren-tool.tar.gz nightstory@37.97.194.228:/home/nightstory/

# 3. VPS: stop service
ssh nightstory@37.97.194.228
sudo systemctl stop flask-anonimiseren

# 4. Backup oude versie (optioneel)
cd /home/nightstory/apps
tar -czf flask-anonimiseren-tool-backup-$(date +%Y%m%d).tar.gz flask-anonimiseren-tool/

# 5. Extract nieuwe versie
tar -xzf /home/nightstory/flask-anonimiseren-tool.tar.gz -C /home/nightstory/apps/flask-anonimiseren-tool

# 6. Update dependencies
cd /home/nightstory/apps/flask-anonimiseren-tool
source venv/bin/activate
pip install -r requirements.txt

# 7. Fix permissions (ALTIJD!)
chmod -R 755 static/
find static/ -type f -exec chmod 644 {} \;

# 8. Restart
sudo systemctl start flask-anonimiseren
sudo systemctl status flask-anonimiseren

# 9. Test
curl http://localhost:5002/
curl -I https://apps.nightstory.nl/anonimiseren/
```

---

## Monitoring & Maintenance

### Health Checks
```bash
# Dagelijks: check alle apps
for path in "" "tableau" "excel" "callsheet" "anonimiseren"; do
    echo -n "$path: "
    curl -s -o /dev/null -w "%{http_code}" "https://apps.nightstory.nl/$path/"
    echo ""
done
```

### Log Monitoring
```bash
# Flask app logs
sudo journalctl -u flask-anonimiseren -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log | grep anonimiseren

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Disk Space
```bash
# Check uploads/output directories
du -sh /home/nightstory/apps/flask-anonimiseren-tool/uploads/
du -sh /home/nightstory/apps/flask-anonimiseren-tool/output/

# Cleanup werkt automatisch (24 uur), maar handmatig kan ook:
cd /home/nightstory/apps/flask-anonimiseren-tool
find uploads/ -type d -mtime +1 -exec rm -rf {} \;
find output/ -type d -mtime +1 -exec rm -rf {} \;
```

---

## Success Metrics

### ✅ Deployment Geslaagd Als:
- [ ] Alle 5 URLs geven HTTP 200 response
- [ ] Static files (CSS/JS) laden correct
- [ ] Upload → Process → Download workflow werkt
- [ ] Localhost nog steeds werkend (http://localhost:5001)
- [ ] Geen errors in nginx error log
- [ ] Service blijft draaien na reboot (`systemctl enable` gedaan)

### 📊 Huidige Status (3 jan 2026):
- ✅ Dashboard: 200 OK
- ✅ Tableau: 200 OK
- ✅ Excel: 200 OK
- ✅ Callsheet: 200 OK
- ✅ Anonimiseren: 200 OK
- ✅ Static files: 200 OK
- ✅ Localhost: 200 OK

---

## Contact & Support

**Deployed by**: Claude Sonnet 4.5 (AI Assistant)
**Project Owner**: Niels Croiset
**VPS Provider**: TransIP
**Deployment Date**: 2-3 januari 2026

**Emergency Rollback**:
```bash
# Stop huidige versie
sudo systemctl stop flask-anonimiseren

# Restore backup
cd /home/nightstory/apps
rm -rf flask-anonimiseren-tool/
tar -xzf flask-anonimiseren-tool-backup-YYYYMMDD.tar.gz

# Restart
sudo systemctl start flask-anonimiseren
```

---

**BELANGRIJKSTE LESSON**: Permissions zijn ALLES bij nginx static file serving! Check altijd de HELE PATH vanaf root.

