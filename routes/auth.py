from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from database.db_init import db
from models.user import User, Role
from models.audit import AuditAction
from services.audit_service import log_audit

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If no users exist, redirect to initial setup wizard
    if User.query.count() == 0:
        return redirect(url_for('auth.first_time_setup'))

    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                log_audit(
                    action=AuditAction.LOGIN_FAILED,
                    description=f"Failed login attempt for deactivated user '{username}'",
                    user=user
                )
                return render_template('login.html')

            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            session.permanent = True

            log_audit(
                action=AuditAction.LOGIN,
                description=f"User '{user.username}' logged in successfully ({user.role})",
                user=user
            )

            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid username or password.', 'danger')
            log_audit(
                action=AuditAction.LOGIN_FAILED,
                description=f"Failed login attempt with username '{username}'"
            )

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    log_audit(
        action=AuditAction.LOGOUT,
        description=f"User '{username}' logged out"
    )
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/first-time-setup', methods=['GET', 'POST'])
def first_time_setup():
    # Only allowed if zero users exist in the database
    if User.query.count() > 0:
        flash('Setup has already been completed. Please log in.', 'info')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not full_name or not password:
            flash('Username, Full Name, and Password are required.', 'warning')
            return render_template('setup_wizard.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('setup_wizard.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('setup_wizard.html')

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

        log_audit(
            action=AuditAction.LOGIN,
            description=f"Initial Admin account created: '{username}'",
            user=admin
        )

        login_user(admin)
        flash('Initial Administrator account created successfully! Welcome to the Gate Management System.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('setup_wizard.html')
