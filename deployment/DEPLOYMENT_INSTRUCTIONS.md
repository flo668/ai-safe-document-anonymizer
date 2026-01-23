# Flask Anonimiseren Tool - VPS Deployment Instructies

**Status**: ✅ DEPLOYED & LIVE (3 januari 2026)
**URL**: https://apps.nightstory.nl/anonimiseren/
**Dashboard**: https://apps.nightstory.nl/

## Deployment naar apps.nightstory.nl/anonimiseren

> **⚠️ BELANGRIJK**: Lees eerst `LESSONS_LEARNED.md` voor troubleshooting en best practices!

### Stap 1: Upload app naar VPS

Vanaf je Mac (in de project directory):

```bash
# Maak een tar.gz van de app (zonder node_modules, tests, etc.)
cd "/Users/ncroiset/Vibe Coding Projecten/Project Anonimiseer_tool_word_excel/flask-anonimiseren-tool"

tar -czf flask-anonimiseren-tool.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='tests' \
    --exclude='uploads/*' \
    --exclude='output/*' \
    --exclude='deployment' \
    .

# Upload naar VPS
scp flask-anonimiseren-tool.tar.gz nightstory@37.97.194.228:/home/nightstory/

# Cleanup lokaal
rm flask-anonimiseren-tool.tar.gz
```

### Stap 2: Installeer op VPS

SSH naar de server:

```bash
ssh nightstory@37.97.194.228
```

Dan op de VPS:

```bash
# Maak apps directory aan (als die nog niet bestaat)
mkdir -p /home/nightstory/apps

# Pak de app uit
cd /home/nightstory/apps
tar -xzf /home/nightstory/flask-anonimiseren-tool.tar.gz -C /home/nightstory/apps/flask-anonimiseren-tool
cd flask-anonimiseren-tool

# Maak virtual environment
python3 -m venv venv
source venv/bin/activate

# Installeer dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Maak directories
mkdir -p uploads output logs

# KRITIEK: Fix permissions voor nginx!
chmod 755 /home/nightstory/
chmod 755 /home/nightstory/apps/flask-anonimiseren-tool/
chmod -R 755 static/
find static/ -type f -exec chmod 644 {} \;

# Test of app kan starten
python app.py
# Als het werkt: Ctrl+C om te stoppen
```

### Stap 3: Installeer Systemd Service

```bash
# Kopieer service file
sudo cp /home/nightstory/apps/flask-anonimiseren-tool/deployment/flask-anonimiseren.service /etc/systemd/system/

# Of maak handmatig aan:
sudo nano /etc/systemd/system/flask-anonimiseren.service
# Plak de inhoud van deployment/flask-anonimiseren.service

# BELANGRIJK: Genereer een veilige SECRET_KEY
# Run dit op de VPS:
python3 -c "import secrets; print(secrets.token_hex(32))"

# Edit de service file en vervang de SECRET_KEY
sudo nano /etc/systemd/system/flask-anonimiseren.service

# Reload systemd
sudo systemctl daemon-reload

# Start de service
sudo systemctl start flask-anonimiseren

# Check status
sudo systemctl status flask-anonimiseren

# Enable voor automatisch starten bij boot
sudo systemctl enable flask-anonimiseren

# Bekijk logs
sudo journalctl -u flask-anonimiseren -f
```

### Stap 4: Update Nginx Configuratie

```bash
# Backup huidige config
sudo cp /etc/nginx/sites-available/tableau-analyzer /etc/nginx/sites-available/tableau-analyzer.backup

# Update de config (optie 1: handmatig)
sudo nano /etc/nginx/sites-available/tableau-analyzer
# Voeg de location /anonimiseren block toe zoals in nginx-updated-config.conf

# Of optie 2: vervang hele bestand
# sudo cp /home/nightstory/apps/flask-anonimiseren-tool/deployment/nginx-updated-config.conf /etc/nginx/sites-available/tableau-analyzer

# Test nginx configuratie
sudo nginx -t

# Als test OK is, reload nginx
sudo systemctl reload nginx
```

### Stap 5: Test de Deployment

Open in browser:
- https://apps.nightstory.nl/anonimiseren

Je zou nu de Flask app moeten zien!

## Troubleshooting

### App start niet

```bash
# Check logs
sudo journalctl -u flask-anonimiseren -n 50

# Check of poort 5002 beschikbaar is
sudo netstat -tulpn | grep 5002

# Handmatig testen
cd /home/nightstory/apps/flask-anonimiseren-tool
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:5002 app:app
```

### Nginx errors

```bash
# Check nginx error log
sudo tail -f /var/log/nginx/error.log

# Test config
sudo nginx -t
```

### File upload werkt niet

Check of de uploads/output directories de juiste permissions hebben:

```bash
cd /home/nightstory/apps/flask-anonimiseren-tool
ls -la uploads output

# Als nodig:
chmod 755 uploads output
```

### Static files geven 503 of 403 errors

**MEEST VOORKOMEND PROBLEEM!** Nginx heeft permissions nodig op HELE PATH.

```bash
# Check error log voor "Permission denied"
sudo tail -f /var/log/nginx/error.log

# Fix: home directory MOET 755 zijn
chmod 755 /home/nightstory/

# Fix: static directory permissions
chmod -R 755 /home/nightstory/apps/flask-anonimiseren-tool/static/
find /home/nightstory/apps/flask-anonimiseren-tool/static/ -type f -exec chmod 644 {} \;

# Verify permissions
namei -l /home/nightstory/apps/flask-anonimiseren-tool/static/css/styles.css

# Test direct
curl -I https://apps.nightstory.nl/anonimiseren/static/css/styles.css
```

### Dashboard geeft 403 Forbidden

```bash
# Check of index.html bestaat (niet dashboard.html!)
ls -la /home/nightstory/dashboard/

# Rename als nodig
mv /home/nightstory/dashboard/dashboard.html /home/nightstory/dashboard/index.html

# Fix permissions
chmod 755 /home/nightstory/dashboard/
chmod 644 /home/nightstory/dashboard/index.html
chmod -R 755 /home/nightstory/dashboard/assets/
```

## Handige Commando's

```bash
# Service management
sudo systemctl status flask-anonimiseren
sudo systemctl restart flask-anonimiseren
sudo systemctl stop flask-anonimiseren
sudo systemctl start flask-anonimiseren

# Logs bekijken
sudo journalctl -u flask-anonimiseren -f

# Nginx
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl restart nginx
```

## Updates Deployen

```bash
# Op Mac: maak nieuwe tar.gz en upload
cd "/Users/ncroiset/Vibe Coding Projecten/Project Anonimiseer_tool_word_excel/flask-anonimiseren-tool"
tar -czf flask-anonimiseren-tool.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='tests' \
    --exclude='uploads/*' \
    --exclude='output/*' \
    --exclude='deployment' \
    .
scp flask-anonimiseren-tool.tar.gz nightstory@37.97.194.228:/home/nightstory/

# Op VPS:
ssh nightstory@37.97.194.228
cd /home/nightstory/apps/flask-anonimiseren-tool
sudo systemctl stop flask-anonimiseren
tar -xzf /home/nightstory/flask-anonimiseren-tool.tar.gz -C /home/nightstory/apps/flask-anonimiseren-tool
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start flask-anonimiseren
sudo systemctl status flask-anonimiseren
```

---

**Deployed**: 3 januari 2026 ✅
**URL**: https://apps.nightstory.nl/anonimiseren/
**Dashboard**: https://apps.nightstory.nl/
**Status**: LIVE & OPERATIONAL

> 📖 Voor gedetailleerde troubleshooting, zie `LESSONS_LEARNED.md`
