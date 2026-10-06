import os
import shutil
import sqlite3
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from database.db_init import db
from models.settings import SystemSetting
from models.user import User, Role
from models.audit import AuditLog, AuditAction
from models.vehicle import Vehicle, VehicleType, AuthStatus
from models.rfid import RFIDCard, CardStatus
from models.movement import VehicleMovement, MovementStatus, GateDirection
from models.denied_attempt import DeniedAttempt, DeniedReason
from models.device import Device, DeviceType, DeviceStatus
from services.audit_service import log_audit
from services.vehicle_service import VehicleService
from services.rfid_service import RFIDService

settings_bp = Blueprint('settings', __name__)

# ----------------- SYSTEM SETTINGS ----------------- #

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def system_settings():
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can modify system settings.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        settings_keys = [
            'system_name', 'gate_direction_mode', 'scan_cooldown_seconds',
            'device_heartbeat_timeout', 'barrier_auto_close_delay',
            'anpr_confidence_threshold', 'dashboard_refresh_interval', 'demo_mode_enabled'
        ]
        
        for k in settings_keys:
            if k in request.form:
                val = request.form.get(k).strip()
                SystemSetting.set_value(k, val)

        log_audit(
            action=AuditAction.SETTINGS_UPDATE,
            description="Updated system configuration settings",
            user=current_user
        )
        flash('Settings saved successfully.', 'success')
        return redirect(url_for('settings.system_settings'))

    all_settings = {s.key: s.value for s in SystemSetting.query.all()}
    return render_template('settings.html', settings=all_settings)


# ----------------- USER MANAGEMENT (ADMIN ONLY) ----------------- #

@settings_bp.route('/users')
@login_required
def list_users():
    if current_user.role != Role.ADMIN:
        flash('Access restricted to Administrators.', 'danger')
        return redirect(url_for('dashboard.index'))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=users, roles=Role.CHOICES)

@settings_bp.route('/users/new', methods=['POST'])
@login_required
def create_user():
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can create new accounts.', 'danger')
        return redirect(url_for('settings.list_users'))

    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    role = request.form.get('role', Role.GATE_OPERATOR)
    password = request.form.get('password', '')

    if not username or not full_name or not password:
        flash('All fields are required.', 'warning')
        return redirect(url_for('settings.list_users'))

    if len(password) < 6:
        flash('Password must be at least 6 characters long.', 'warning')
        return redirect(url_for('settings.list_users'))

    existing = User.query.filter_by(username=username).first()
    if existing:
        flash(f"Username '{username}' already exists.", 'danger')
        return redirect(url_for('settings.list_users'))

    new_user = User(
        username=username,
        full_name=full_name,
        email=email if email else None,
        role=role,
        is_active=True
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    log_audit(
        action=AuditAction.LOGIN,
        description=f"Admin created user account '{username}' ({role})",
        user=current_user
    )

    flash(f"User '{username}' created successfully.", 'success')
    return redirect(url_for('settings.list_users'))

@settings_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user(user_id):
    if current_user.role != Role.ADMIN:
        flash('Permission denied.', 'danger')
        return redirect(url_for('settings.list_users'))

    if user_id == current_user.id:
        flash('You cannot deactivate your own administrative account.', 'warning')
        return redirect(url_for('settings.list_users'))

    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('settings.list_users'))

    user.is_active = not user.is_active
    db.session.commit()

    action_str = "activated" if user.is_active else "deactivated"
    flash(f"User '{user.username}' has been {action_str}.", 'info')
    return redirect(url_for('settings.list_users'))


# ----------------- AUDIT LOGS ----------------- #

@settings_bp.route('/audit-logs')
@login_required
def audit_logs():
    if current_user.role != Role.ADMIN:
        flash('Access restricted to Administrators.', 'danger')
        return redirect(url_for('dashboard.index'))

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    action = request.args.get('action', '').strip()

    query = AuditLog.query
    if search:
        s = f"%{search}%"
        query = query.filter(
            AuditLog.description.ilike(s) |
            AuditLog.username.ilike(s) |
            AuditLog.related_vehicle.ilike(s) |
            AuditLog.related_device.ilike(s)
        )

    if action:
        query = query.filter_by(action=action)

    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=30, error_out=False)

    return render_template(
        'audit_logs.html',
        pagination=pagination,
        logs=pagination.items,
        search=search,
        action=action
    )


# ----------------- DATABASE BACKUP & RESTORE ----------------- #

@settings_bp.route('/backups')
@login_required
def backups():
    if current_user.role != Role.ADMIN:
        flash('Access restricted to Administrators.', 'danger')
        return redirect(url_for('dashboard.index'))

    backup_folder = current_app.config['BACKUP_FOLDER']
    os.makedirs(backup_folder, exist_ok=True)

    backup_files = []
    for f in os.listdir(backup_folder):
        if f.endswith('.db') or f.endswith('.sqlite'):
            path = os.path.join(backup_folder, f)
            stat = os.stat(path)
            backup_files.append({
                'filename': f,
                'size_kb': round(stat.st_size / 1024, 1),
                'created_at': datetime.fromtimestamp(stat.st_ctime)
            })

    backup_files.sort(key=lambda x: x['created_at'], reverse=True)
    return render_template('backups.html', backups=backup_files)

@settings_bp.route('/backups/create', methods=['POST'])
@login_required
def create_backup():
    if current_user.role != Role.ADMIN:
        flash('Permission denied.', 'danger')
        return redirect(url_for('settings.backups'))

    backup_folder = current_app.config['BACKUP_FOLDER']
    os.makedirs(backup_folder, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"backup_gate_{timestamp}.db"
    backup_filepath = os.path.join(backup_folder, backup_filename)

    # SQLite online backup API ensures transactional consistency
    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:///'):
        src_path = db_uri.replace('sqlite:///', '')
        if not os.path.isabs(src_path):
            src_path = os.path.join(current_app.config['BASE_DIR'], src_path)

        try:
            src_conn = sqlite3.connect(src_path)
            dst_conn = sqlite3.connect(backup_filepath)
            with dst_conn:
                src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()

            log_audit(
                action=AuditAction.DATABASE_BACKUP,
                description=f"Created database backup: '{backup_filename}'",
                user=current_user
            )
            flash(f"Database backup '{backup_filename}' created successfully.", 'success')
        except Exception as e:
            flash(f"Backup failed: {str(e)}", 'danger')
    else:
        flash("Online backup is configured for SQLite database.", 'warning')

    return redirect(url_for('settings.backups'))

@settings_bp.route('/backups/download/<filename>')
@login_required
def download_backup(filename):
    if current_user.role != Role.ADMIN:
        flash('Permission denied.', 'danger')
        return redirect(url_for('settings.backups'))

    backup_folder = current_app.config['BACKUP_FOLDER']
    filepath = os.path.join(backup_folder, filename)
    if not os.path.exists(filepath):
        flash('Backup file not found.', 'danger')
        return redirect(url_for('settings.backups'))

    return send_file(filepath, as_attachment=True, download_name=filename)

@settings_bp.route('/backups/restore/<filename>', methods=['POST'])
@login_required
def restore_backup(filename):
    if current_user.role != Role.ADMIN:
        flash('Permission denied.', 'danger')
        return redirect(url_for('settings.backups'))

    confirmation = request.form.get('confirm_restore')
    if confirmation != 'RESTORE':
        flash("Restoration cancelled. You must type 'RESTORE' to confirm database overwrite.", 'warning')
        return redirect(url_for('settings.backups'))

    backup_folder = current_app.config['BACKUP_FOLDER']
    backup_filepath = os.path.join(backup_folder, filename)

    if not os.path.exists(backup_filepath):
        flash('Backup file does not exist.', 'danger')
        return redirect(url_for('settings.backups'))

    # Validate backup file integrity
    try:
        test_conn = sqlite3.connect(backup_filepath)
        test_cursor = test_conn.cursor()
        test_cursor.execute("PRAGMA integrity_check")
        res = test_cursor.fetchone()
        test_conn.close()
        if not res or res[0] != 'ok':
            flash('Corrupt backup file. Integrity check failed. Restoration aborted.', 'danger')
            return redirect(url_for('settings.backups'))
    except Exception as e:
        flash(f'Backup file validation error: {e}', 'danger')
        return redirect(url_for('settings.backups'))

    # Restore by copying
    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:///'):
        src_path = db_uri.replace('sqlite:///', '')
        if not os.path.isabs(src_path):
            src_path = os.path.join(current_app.config['BASE_DIR'], src_path)

        try:
            # Create a safety pre-restore backup of current db
            safety_file = os.path.join(backup_folder, f"pre_restore_safety_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db")
            if os.path.exists(src_path):
                shutil.copy2(src_path, safety_file)

            # Copy validated backup over active database
            shutil.copy2(backup_filepath, src_path)

            log_audit(
                action=AuditAction.DATABASE_RESTORE,
                description=f"Restored database from '{filename}'",
                user=current_user
            )
            flash(f"Database successfully restored from '{filename}'. Safety snapshot created at '{os.path.basename(safety_file)}'.", 'success')
        except Exception as e:
            flash(f"Restore error: {str(e)}", 'danger')

    return redirect(url_for('settings.backups'))


# ----------------- DEMO MODE DATA SEEDING ----------------- #

@settings_bp.route('/demo/seed', methods=['POST'])
@login_required
def seed_demo_data():
    """Seed comprehensive demo dataset with vehicles, RFID tags, and movements."""
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can seed demo data.', 'danger')
        return redirect(url_for('dashboard.index'))

    # Ensure a default ESP32 device exists
    default_dev = Device.query.filter_by(device_id='GATE_ENTRY_01').first()
    if not default_dev:
        default_dev = Device(
            device_id='GATE_ENTRY_01',
            device_name='Main Gate ESP32 Reader',
            device_type=DeviceType.ESP32_RFID,
            gate='Main Gate',
            direction=DeviceDirection.ENTRY,
            status=DeviceStatus.ONLINE,
            last_seen=datetime.utcnow(),
            is_active=True
        )
        default_dev.set_api_key('demo_secret_key_123')
        db.session.add(default_dev)
        db.session.commit()

    # Sample demo vehicles
    demo_vehicles_data = [
        {"reg": "MH12AB1234", "type": VehicleType.GYPSY, "driver": "Subedar Rajesh Sharma", "phone": "9876543210", "auth": AuthStatus.AUTHORIZED, "valid_days": 365, "uid": "A37F291C"},
        {"reg": "DL01XY9876", "type": VehicleType.TWO_POINT_FIVE_TON, "driver": "Havaldar Vikram Singh", "phone": "9811223344", "auth": AuthStatus.AUTHORIZED, "valid_days": 180, "uid": "E5B2104A"},
        {"reg": "KA04CD5555", "type": VehicleType.ALS, "driver": "Naik Anil Kumar", "phone": "9988776655", "auth": AuthStatus.AUTHORIZED, "valid_days": 90, "uid": "89C4123D"},
        {"reg": "MH14ZZ7777", "type": VehicleType.TATA_YODHA, "driver": "Subedar Suresh Patel", "phone": "9123456780", "auth": AuthStatus.AUTHORIZED, "valid_days": 730, "uid": "11223344"},
        {"reg": "UP32FF4321", "type": VehicleType.HMV, "driver": "Havaldar Mohan Lal", "phone": "9765432109", "auth": AuthStatus.EXPIRED, "valid_days": -10, "uid": "DEADBEEF"},
        {"reg": "HR26BK9999", "type": VehicleType.FORTUNER, "driver": "Subedar Major Ramesh Verma", "phone": "9845123678", "auth": AuthStatus.BLOCKED, "valid_days": 30, "uid": "CAFEBABE"}
    ]

    for idx, item in enumerate(demo_vehicles_data):
        veh = Vehicle.query.filter_by(registration_number=item["reg"]).first()
        if not veh:
            v_issue = date.today() - timedelta(days=30)
            veh = Vehicle(
                registration_number=item["reg"],
                vehicle_type=item["type"],
                issue_date=v_issue,
                custodian_name=item["driver"],
                armynumber=f"JC-{200000 + idx}",
                mobile_number=item["phone"],
                auth_status=item["auth"],
                is_active=True,
                is_demo=True
            )
            db.session.add(veh)
            db.session.flush()

            card = RFIDCard.query.filter_by(uid=item["uid"]).first()
            if not card:
                card = RFIDCard(
                    uid=item["uid"],
                    vehicle_id=veh.id,
                    card_status=CardStatus.BLOCKED if item["auth"] == AuthStatus.BLOCKED else CardStatus.ACTIVE,
                    assigned_date=date.today() - timedelta(days=20),
                    is_demo=True
                )
                db.session.add(card)

    db.session.commit()

    # Add sample demo movements
    v1 = Vehicle.query.filter_by(registration_number="MH12AB1234").first()
    v2 = Vehicle.query.filter_by(registration_number="DL01XY9876").first()
    
    if v1 and not v1.has_active_movement():
        # Inside movement
        m1 = VehicleMovement(
            vehicle_id=v1.id,
            entry_time=datetime.utcnow() - timedelta(hours=2, minutes=15),
            entry_device_id=default_dev.id,
            direction=GateDirection.ENTRY,
            status=MovementStatus.INSIDE,
            is_demo=True
        )
        db.session.add(m1)

    if v2:
        # Completed historical movement
        m2 = VehicleMovement(
            vehicle_id=v2.id,
            entry_time=datetime.utcnow() - timedelta(hours=5),
            exit_time=datetime.utcnow() - timedelta(hours=1),
            duration_seconds=14400,
            entry_device_id=default_dev.id,
            exit_device_id=default_dev.id,
            direction=GateDirection.EXIT,
            status=MovementStatus.OUTSIDE,
            is_demo=True
        )
        db.session.add(m2)

    # Sample denied attempt
    d1 = DeniedAttempt(
        timestamp=datetime.utcnow() - timedelta(minutes=45),
        rfid_uid="UNKNOWN999",
        direction="ENTRY",
        reason=DeniedReason.UNKNOWN_RFID,
        device_id=default_dev.id,
        remarks="Demo unregistered tag scan",
        is_demo=True
    )
    db.session.add(d1)

    db.session.commit()
    SystemSetting.set_value('demo_mode_enabled', '1')

    log_audit(
        action=AuditAction.DEMO_MODE_TOGGLE,
        description="Seeded sample demo vehicles, RFID cards, and movements",
        user=current_user
    )

    flash('Demo dataset seeded successfully! Explore dashboard, vehicle master, RFID management, and gate control.', 'success')
    return redirect(url_for('dashboard.index'))

@settings_bp.route('/demo/clear', methods=['POST'])
@login_required
def clear_demo_data():
    """Clear only demo marked records without touching real system data."""
    if current_user.role != Role.ADMIN:
        flash('Permission denied.', 'danger')
        return redirect(url_for('dashboard.index'))

    VehicleMovement.query.filter_by(is_demo=True).delete()
    DeniedAttempt.query.filter_by(is_demo=True).delete()
    RFIDCard.query.filter_by(is_demo=True).delete()
    Vehicle.query.filter_by(is_demo=True).delete()
    
    SystemSetting.set_value('demo_mode_enabled', '0')
    db.session.commit()

    log_audit(
        action=AuditAction.DEMO_MODE_TOGGLE,
        description="Cleared all demo records from system",
        user=current_user
    )

    flash('Demo records removed successfully.', 'info')
    return redirect(url_for('dashboard.index'))

@settings_bp.route('/movements/clear-all-history', methods=['POST'])
@login_required
def clear_all_movement_history():
    """Clear all vehicle movement logs and reset gate state for a fresh start."""
    if current_user.role != Role.ADMIN:
        flash('Permission denied. Only administrators can clear movement history.', 'danger')
        return redirect(url_for('movements.movement_register'))

    mov_cnt = VehicleMovement.query.delete()
    den_cnt = DeniedAttempt.query.delete()
    DeviceEvent.query.delete()
    for d in Device.query.all():
        d.last_event = None
    db.session.commit()

    log_audit(
        action=AuditAction.SETTINGS_UPDATE,
        description=f"Cleared all movement logs ({mov_cnt} movements, {den_cnt} denied attempts)",
        user=current_user
    )

    flash(f'Movement history cleared successfully ({mov_cnt} movement records, {den_cnt} denied logs removed). System is ready for a fresh start!', 'success')
    return redirect(request.referrer or url_for('movements.gate_control'))
