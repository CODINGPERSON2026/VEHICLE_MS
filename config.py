import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-rfid-gate-management-secret-key-2026-xyz')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'mysql+pymysql://root:qaz123QAZ%21%40%23@localhost/vehicle_management'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
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
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
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
