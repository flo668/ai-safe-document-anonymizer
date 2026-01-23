import os
from pathlib import Path

class Config:
    """Flask configuratie"""

    # Base directory
    BASE_DIR = Path(__file__).parent

    # Secret key voor sessies
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Upload configuratie
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    OUTPUT_FOLDER = BASE_DIR / 'output'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size (hard limit)
    FILE_SIZE_WARNING_THRESHOLD = 5 * 1024 * 1024  # 5MB - warn user about processing time
    FILE_SIZE_HARD_LIMIT = 50 * 1024 * 1024  # 50MB - reject files larger than this
    ALLOWED_EXTENSIONS = {'txt', 'docx', 'xlsx', 'csv', 'pdf', 'md'}

    # Session configuratie
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 uur

    # Cleanup configuratie
    CLEANUP_OLDER_THAN_HOURS = 24  # Verwijder bestanden ouder dan 24 uur

    @staticmethod
    def init_app(app):
        """Initialiseer de applicatie directories"""
        Config.UPLOAD_FOLDER.mkdir(exist_ok=True)
        Config.OUTPUT_FOLDER.mkdir(exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuratie"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuratie"""
    DEBUG = False
    TESTING = False

    # In productie moet SECRET_KEY altijd gezet zijn
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Ensure SECRET_KEY is set in production
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")


class TestingConfig(Config):
    """Testing configuratie"""
    TESTING = True
    DEBUG = True
    # Gebruik tmp folders voor tests
    UPLOAD_FOLDER = Path('/tmp/test_uploads')
    OUTPUT_FOLDER = Path('/tmp/test_outputs')
    SECRET_KEY = 'test-secret-key'

    @staticmethod
    def init_app(app):
        """Initialiseer test directories"""
        TestingConfig.UPLOAD_FOLDER.mkdir(exist_ok=True, parents=True)
        TestingConfig.OUTPUT_FOLDER.mkdir(exist_ok=True, parents=True)


# Config dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
