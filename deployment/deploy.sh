#!/bin/bash

# Flask Anonimiseren Tool - Deployment Script
# Deploy naar apps.nightstory.nl/anonimiseren

set -e  # Exit on error

echo "🚀 Flask Anonimiseren Tool - VPS Deployment"
echo "============================================"
echo ""

# Configuratie
VPS_USER="nightstory"
VPS_HOST="37.97.194.228"
APP_NAME="flask-anonimiseren-tool"
PROJECT_DIR="/Users/ncroiset/Vibe Coding Projecten/Project Anonimiseer_tool_word_excel/flask-anonimiseren-tool"

# Stap 1: Maak tar.gz
echo "📦 Stap 1: Package app..."
cd "$PROJECT_DIR"

tar -czf ${APP_NAME}.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='tests' \
    --exclude='uploads/*' \
    --exclude='output/*' \
    --exclude='deployment' \
    --exclude='.git' \
    .

echo "✅ Package created: ${APP_NAME}.tar.gz"

# Stap 2: Upload naar VPS
echo ""
echo "📤 Stap 2: Upload naar VPS..."
scp ${APP_NAME}.tar.gz ${VPS_USER}@${VPS_HOST}:/home/${VPS_USER}/

echo "✅ Upload complete"

# Stap 3: Extract en setup op VPS
echo ""
echo "⚙️  Stap 3: Setup op VPS..."

ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
    set -e

    APP_NAME="flask-anonimiseren-tool"
    APP_DIR="/home/nightstory/apps/${APP_NAME}"

    echo "  → Maak directory aan..."
    mkdir -p ${APP_DIR}

    echo "  → Extract app..."
    tar -xzf /home/nightstory/${APP_NAME}.tar.gz -C ${APP_DIR}

    echo "  → Maak virtual environment..."
    cd ${APP_DIR}
    python3 -m venv venv

    echo "  → Installeer dependencies..."
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q

    echo "  → Maak directories..."
    mkdir -p uploads output

    echo "  → Cleanup tar.gz..."
    rm /home/nightstory/${APP_NAME}.tar.gz

    echo "✅ VPS setup complete"
ENDSSH

# Stap 4: Cleanup lokaal
echo ""
echo "🧹 Stap 4: Cleanup lokaal..."
rm ${APP_NAME}.tar.gz
echo "✅ Cleanup complete"

echo ""
echo "✨ Deployment package ready op VPS!"
echo ""
echo "📝 Volgende stappen (handmatig):"
echo "   1. SSH naar VPS: ssh ${VPS_USER}@${VPS_HOST}"
echo "   2. Genereer SECRET_KEY: python3 -c \"import secrets; print(secrets.token_hex(32))\""
echo "   3. Installeer systemd service (zie DEPLOYMENT_INSTRUCTIONS.md)"
echo "   4. Update nginx config (zie DEPLOYMENT_INSTRUCTIONS.md)"
echo "   5. Test: https://apps.nightstory.nl/anonimiseren"
echo ""
