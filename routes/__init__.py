"""
Routes Module - Blueprint Registration

Dit module registreert alle Flask blueprints voor de applicatie.
Iedere blueprint bevat gerelateerde routes.
"""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """
    Registreer alle blueprints bij de Flask applicatie.

    Args:
        app: Flask applicatie instance
    """
    from .main_routes import main_bp
    from .upload_routes import upload_bp
    from .processing_routes import processing_bp
    from .download_routes import download_bp
    from .reverse_routes import reverse_bp

    # Registreer alle blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(processing_bp, url_prefix='/api')
    app.register_blueprint(download_bp, url_prefix='/api')
    app.register_blueprint(reverse_bp, url_prefix='/api')
