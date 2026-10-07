from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize database and create all tables if they do not exist."""
    with app.app_context():
        # Import models to register them with SQLAlchemy
        import models.user
        import models.driver
        import models.vehicle
        import models.rfid
        import models.movement
        import models.device
        import models.denied_attempt
        import models.audit
        import models.camera
        import models.settings

        db.create_all()
        seed_default_settings()


def seed_default_settings():
    """Seed initial system settings if not already present."""
    from models.settings import SystemSetting

    defaults = {
        'system_name': ('Smart RFID + ANPR Vehicle Gate System', 'Display name of the application'),
        'gate_direction_mode': ('EXIT_ONLY', 'Default direction mode (EXIT_ONLY, ENTRY_ONLY, MANUAL_DIRECTION)'),
        'scan_cooldown_seconds': ('3', 'Cooldown duration between scans for same RFID in seconds'),
        'device_heartbeat_timeout': ('35', 'Seconds before an inactive device is marked OFFLINE'),
        'barrier_auto_close_delay': ('4', 'Seconds to simulate barrier gate open before auto-closing'),
        'anpr_confidence_threshold': ('80.0', 'Minimum confidence score (%) for ANPR auto-match'),
        'dashboard_refresh_interval': ('1', 'Dashboard auto-refresh interval in seconds')
    }

    for key, (val, desc) in defaults.items():
        setting = SystemSetting.query.filter_by(key=key).first()
        if not setting:
            new_setting = SystemSetting(key=key, value=val, description=desc)
            db.session.add(new_setting)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
