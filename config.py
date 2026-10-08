import os
from datetime import timedelta
from urllib.parse import quote_plus

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database Credentials
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'qaz123QAZ!@#')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'vehicle_management')

# Constructed MySQL SQLAlchemy Connection URI
DEFAULT_DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    if DB_PASSWORD else
    f"mysql+pymysql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-rfid-gate-management-secret-key-2026-xyz')
    
    # Database Configuration
    DB_USER = DB_USER
    DB_PASSWORD = DB_PASSWORD
    DB_HOST = DB_HOST
    DB_PORT = DB_PORT
    DB_NAME = DB_NAME
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', DEFAULT_DATABASE_URL)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True
    }
    
    # Session security
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.environ.get('SESSION_TIMEOUT_MINUTES', 60)))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Storage paths
    BACKUP_FOLDER = os.path.join(BASE_DIR, 'backups')
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'reports')
    SNAPSHOT_ENTRY_FOLDER = os.path.join(BASE_DIR, 'data', 'snapshots', 'entry')
    SNAPSHOT_EXIT_FOLDER = os.path.join(BASE_DIR, 'data', 'snapshots', 'exit')
    ANPR_FOLDER = os.path.join(BASE_DIR, 'data', 'anpr')
    
    # Gate & Device Settings
    DEVICE_HEARTBEAT_TIMEOUT = int(os.environ.get('DEVICE_HEARTBEAT_TIMEOUT', 35)) # seconds
    SCAN_COOLDOWN_SECONDS = int(os.environ.get('SCAN_COOLDOWN_SECONDS', 3))
    BARRIER_CLOSE_DELAY_SECONDS = int(os.environ.get('BARRIER_CLOSE_DELAY_SECONDS', 4))
    
    # Dashboard Auto-refresh interval (seconds)
    DASHBOARD_REFRESH_INTERVAL = int(os.environ.get('DASHBOARD_REFRESH_INTERVAL', 1))

    # WTForms CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'TEST_DATABASE_URL',
        os.environ.get('DATABASE_URL', DEFAULT_DATABASE_URL)
    )
    WTF_CSRF_ENABLED = False
    DEVICE_HEARTBEAT_TIMEOUT = 10

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
