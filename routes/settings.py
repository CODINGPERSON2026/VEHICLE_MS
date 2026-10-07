import os
import shutil
import subprocess
from urllib.parse import urlparse, unquote
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
import pymysql
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

        # Checkbox settings (absent from form when unchecked)
        guard_confirm = '1' if request.form.get('require_guard_confirmation') == '1' else '0'
        SystemSetting.set_value('require_guard_confirmation', guard_confirm)

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
        if f.endswith('.sql'):
            path = os.path.join(backup_folder, f)
            stat = os.stat(path)
            backup_files.append({
                'filename': f,
                'size_kb': round(stat.st_size / 1024, 1),
                'created_at': datetime.fromtimestamp(stat.st_ctime)
            })

    backup_files.sort(key=lambda x: x['created_at'], reverse=True)
    return render_template('backups.html', backups=backup_files)

def _dump_mysql_to_file(backup_filepath):
    """Dump MySQL database to standard .sql file compatible with MySQL Workbench."""
    mysqldump_candidates = [
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
        r"C:\Program Files\MySQL\MySQL Workbench 8.0 CE\mysqldump.exe",
        "mysqldump"
    ]
    dump_bin = None
    for p in mysqldump_candidates:
        if os.path.exists(p) or shutil.which(p):
            dump_bin = p
            break

    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    normalized_uri = db_uri.replace('+pymysql', '') if '+pymysql' in db_uri else db_uri
    parsed = urlparse(normalized_uri)
    user = unquote(parsed.username or 'root')
    password = unquote(parsed.password or '')
    host = parsed.hostname or 'localhost'
    port = parsed.port or 3306
    dbname = parsed.path.lstrip('/')

    if dump_bin:
        cmd = [
            dump_bin,
            f"--host={host}",
            f"--port={port}",
            f"--user={user}",
            f"--password={password}",
            "--databases",
            dbname,
            "--routines",
            "--triggers",
            "--single-transaction"
        ]
        with open(backup_filepath, 'w', encoding='utf-8') as out_f:
            res = subprocess.run(cmd, stdout=out_f, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                return True, "Backup created successfully via mysqldump."

    # Pure Python pymysql fallback dump (always works without external binaries)
    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=dbname, charset='utf8mb4')
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        with open(backup_filepath, 'w', encoding='utf-8') as f:
            f.write(f"-- MySQL Database Backup Snapshot\n-- Database: {dbname}\n-- Generated: {datetime.utcnow().isoformat()}\n\n")
            f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_sql = cursor.fetchone()[1]
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
                f.write(f"{create_sql};\n\n")

                cursor.execute(f"SELECT * FROM `{table}`")
                rows = cursor.fetchall()
                if rows:
                    cursor.execute(f"DESCRIBE `{table}`")
                    cols = [f"`{col[0]}`" for col in cursor.fetchall()]
                    cols_str = ", ".join(cols)
                    for r in rows:
                        vals = []
                        for v in r:
                            if v is None:
                                vals.append("NULL")
                            elif isinstance(v, (int, float)):
                                vals.append(str(v))
                            elif isinstance(v, (datetime, date)):
                                vals.append(f"'{v}'")
                            elif isinstance(v, bytes):
                                vals.append(f"X'{v.hex()}'")
                            else:
                                escaped = str(v).replace("'", "''").replace("\\", "\\\\")
                                vals.append(f"'{escaped}'")
                        f.write(f"INSERT INTO `{table}` ({cols_str}) VALUES ({', '.join(vals)});\n")
                    f.write("\n")
            f.write("SET FOREIGN_KEY_CHECKS=1;\n")
    conn.close()
    return True, "Backup created successfully."

def _restore_mysql_from_file(backup_filepath):
    """Restore database from MySQL Workbench .sql script."""
    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    normalized_uri = db_uri.replace('+pymysql', '') if '+pymysql' in db_uri else db_uri
    parsed = urlparse(normalized_uri)
    user = unquote(parsed.username or 'root')
    password = unquote(parsed.password or '')
    host = parsed.hostname or 'localhost'
    port = parsed.port or 3306
    dbname = parsed.path.lstrip('/')

    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=dbname, charset='utf8mb4')
    with conn.cursor() as cursor:
        with open(backup_filepath, 'r', encoding='utf-8', errors='ignore') as f:
            sql_content = f.read()

        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        for stmt in statements:
            lines = [l for l in stmt.splitlines() if not l.strip().startswith('--') and not l.strip().startswith('/*')]
            cleaned_stmt = "\n".join(lines).strip()
            if cleaned_stmt:
                try:
                    cursor.execute(cleaned_stmt)
                except Exception:
                    pass
        conn.commit()
    conn.close()
    return True, "Database restored successfully."

@settings_bp.route('/backups/create', methods=['POST'])
@login_required
def create_backup():
    if current_user.role != Role.ADMIN:
        flash('Permission denied.', 'danger')
        return redirect(url_for('settings.backups'))

    backup_folder = current_app.config['BACKUP_FOLDER']
    os.makedirs(backup_folder, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"backup_gate_{timestamp}.sql"
    backup_filepath = os.path.join(backup_folder, backup_filename)

    try:
        success, msg = _dump_mysql_to_file(backup_filepath)
        if success:
            log_audit(
                action=AuditAction.DATABASE_BACKUP,
                description=f"Created MySQL Workbench database backup: '{backup_filename}'",
                user=current_user
            )
            flash(f"MySQL database backup '{backup_filename}' created successfully.", 'success')
        else:
            flash(f"Backup failed: {msg}", 'danger')
    except Exception as e:
        flash(f"Backup failed: {str(e)}", 'danger')

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

    try:
        success, msg = _restore_mysql_from_file(backup_filepath)
        if success:
            log_audit(
                action=AuditAction.DATABASE_RESTORE,
                description=f"Restored MySQL database from '{filename}'",
                user=current_user
            )
            flash(f"MySQL database successfully restored from '{filename}'.", 'success')
        else:
            flash(f"Restore failed: {msg}", 'danger')
    except Exception as e:
        flash(f"Restore error: {str(e)}", 'danger')

    return redirect(url_for('settings.backups'))


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
    Vehicle.query.update({Vehicle.current_vehicle_location: 'INSIDE'})
    db.session.commit()

    log_audit(
        action=AuditAction.SETTINGS_UPDATE,
        description=f"Cleared all movement logs ({mov_cnt} movements, {den_cnt} denied attempts)",
        user=current_user
    )

    flash(f'Movement history cleared successfully ({mov_cnt} movement records, {den_cnt} denied logs removed). System is ready for a fresh start!', 'success')
    return redirect(request.referrer or url_for('movements.gate_control'))
