import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config_by_name, BASE_DIR
from database.db_init import db, init_db
from models.user import User, Role
from models.settings import SystemSetting

csrf = CSRFProtect()
login_manager = LoginManager()

def create_app(config_name=None):
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))
    app.config['BASE_DIR'] = BASE_DIR

    # Ensure required runtime folders exist
    os.makedirs(app.config['BACKUP_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SNAPSHOT_ENTRY_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SNAPSHOT_EXIT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['ANPR_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    
    # Exempt Hardware / REST APIs from CSRF (ESP32 uses API keys, fetch calls use session)
    csrf.exempt('routes.rfid_api.api_rfid_scan')
    csrf.exempt('routes.rfid_api.api_device_heartbeat')
    csrf.exempt('routes.rfid_api.api_enroll_scan')
    csrf.exempt('routes.rfid_api.api_barrier_status')
    csrf.exempt('routes.drivers.api_assign_movement_driver')

    # Setup Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access the Smart Vehicle Gate System.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.vehicles import vehicles_bp
    from routes.drivers import drivers_bp
    from routes.rfid_api import rfid_bp
    from routes.movements import movements_bp
    from routes.reports import reports_bp
    from routes.devices import devices_bp
    from routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(drivers_bp)
    app.register_blueprint(rfid_bp)
    app.register_blueprint(movements_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(settings_bp)

    # Initialize database tables & defaults
    init_db(app)

    # Inject template globals
    @app.context_processor
    def inject_globals():
        def get_setting(k, d=''):
            try:
                return SystemSetting.get_value(k, d)
            except Exception:
                return d

        return {
            'system_name': get_setting('system_name', 'Smart Vehicle Gate System'),
            'demo_mode_enabled': get_setting('demo_mode_enabled', '0') == '1',
            'gate_direction_mode': get_setting('gate_direction_mode', 'MANUAL_DIRECTION'),
            'Role': Role
        }

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403

    # CLI Command: flask create-admin
    @app.cli.command("create-admin")
    def create_admin_cmd():
        """Create an administrative user from command line."""
        import click
        username = click.prompt("Enter admin username", type=str)
        full_name = click.prompt("Enter full name", type=str)
        email = click.prompt("Enter email (optional)", type=str, default="")
        password = click.prompt("Enter password", hide_input=True, confirmation_prompt=True)
        
        user = User.query.filter_by(username=username).first()
        if user:
            click.echo(f"Error: User '{username}' already exists.")
            return
            
        admin = User(
            username=username,
            full_name=full_name,
            email=email if email else None,
            role=Role.ADMIN,
            is_active=True
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Success: Administrator '{username}' created successfully.")

    return app

app = create_app()

if __name__ == '__main__':
    # Listen on 0.0.0.0:5000 for local PC and ESP32 Wi-Fi access
    app.run(host='0.0.0.0', port=5000, debug=True)
