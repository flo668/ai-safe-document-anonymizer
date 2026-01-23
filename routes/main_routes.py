"""
Main Routes - Homepage

Blueprint voor de hoofdpagina van de applicatie.
"""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage met upload interface"""
    return render_template('index.html')
