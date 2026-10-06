import secrets
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from database.db_init import db
from models.device import Device, DeviceType, DeviceStatus, DeviceDirection
from models.camera import CameraConfig, CameraRole, ANPREvent, ANPRVerificationStatus
from models.user import Role
from models.audit import AuditAction
from services.audit_service import log_audit
from services.anpr_service import ANPRService

devices_bp = Blueprint('devices', __name__)

# ----------------- DEVICE MANAGEMENT ----------------- #

@devices_bp.route('/devices')
@login_required
def list_devices():
    devices = Device.query.order_by(Device.created_at.desc()).all()
    return render_template(
        'devices.html',
        devices=devices,
        device_types=DeviceType.CHOICES,
        directions=DeviceDirection.CHOICES
    )

@devices_bp.route('/devices/new', methods=['POST'])
@login_required
def register_device():
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can register new devices.', 'danger')
        return redirect(url_for('devices.list_devices'))

    device_id = request.form.get('device_id', '').strip().upper()
    device_name = request.form.get('device_name', '').strip()
    device_type = request.form.get('device_type', DeviceType.ESP32_RFID)
    gate = request.form.get('gate', 'Main Gate').strip()
    direction = request.form.get('direction', DeviceDirection.ENTRY)

    if not device_id or not device_name:
        flash('Device ID and Name are required.', 'warning')
        return redirect(url_for('devices.list_devices'))

    existing = Device.query.filter_by(device_id=device_id).first()
    if existing:
        flash(f"Device ID '{device_id}' is already registered.", 'danger')
        return redirect(url_for('devices.list_devices'))

    raw_api_key = Device.generate_api_key()
    device = Device(
        device_id=device_id,
        device_name=device_name,
        device_type=device_type,
        gate=gate,
        direction=direction,
        status=DeviceStatus.OFFLINE,
        is_active=True
    )
    device.set_api_key(raw_api_key)
    db.session.add(device)
    db.session.commit()

    log_audit(
        action=AuditAction.DEVICE_REGISTER,
        description=f"Registered device '{device_name}' ({device_id})",
        related_device=device_id,
        user=current_user
    )

    flash(f"Device '{device_name}' registered successfully! SAVE THIS API KEY NOW: {raw_api_key}", 'warning')
    return redirect(url_for('devices.list_devices'))

@devices_bp.route('/devices/<int:device_id>/toggle', methods=['POST'])
@login_required
def toggle_device(device_id):
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can modify device state.', 'danger')
        return redirect(url_for('devices.list_devices'))

    device = db.session.get(Device, device_id)
    if not device:
        flash('Device not found.', 'danger')
        return redirect(url_for('devices.list_devices'))

    device.is_active = not device.is_active
    device.status = DeviceStatus.OFFLINE if device.is_active else DeviceStatus.DISABLED
    db.session.commit()

    state_str = "Enabled" if device.is_active else "Disabled"
    log_audit(
        action=AuditAction.DEVICE_UPDATE,
        description=f"{state_str} device '{device.device_name}' ({device.device_id})",
        related_device=device.device_id,
        user=current_user
    )

    flash(f"Device '{device.device_name}' is now {state_str}.", 'success')
    return redirect(url_for('devices.list_devices'))

@devices_bp.route('/devices/<int:device_id>/rotate-key', methods=['POST'])
@login_required
def rotate_key(device_id):
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can rotate API keys.', 'danger')
        return redirect(url_for('devices.list_devices'))

    device = db.session.get(Device, device_id)
    if not device:
        flash('Device not found.', 'danger')
        return redirect(url_for('devices.list_devices'))

    new_key = Device.generate_api_key()
    device.set_api_key(new_key)
    db.session.commit()

    log_audit(
        action=AuditAction.DEVICE_KEY_ROTATE,
        description=f"Rotated API key for device '{device.device_name}' ({device.device_id})",
        related_device=device.device_id,
        user=current_user
    )

    flash(f"NEW API KEY for '{device.device_id}': {new_key} (Copy it now, it will not be shown again).", 'warning')
    return redirect(url_for('devices.list_devices'))


# ----------------- CAMERA & ANPR CONFIGURATION ----------------- #

@devices_bp.route('/cameras')
@login_required
def camera_config():
    cameras = CameraConfig.query.order_by(CameraConfig.created_at.desc()).all()
    recent_anpr = ANPREvent.query.order_by(ANPREvent.timestamp.desc()).limit(15).all()
    return render_template(
        'cameras.html',
        cameras=cameras,
        recent_anpr=recent_anpr,
        roles=CameraRole.CHOICES
    )

@devices_bp.route('/cameras/new', methods=['POST'])
@login_required
def add_camera():
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can configure cameras.', 'danger')
        return redirect(url_for('devices.camera_config'))

    cam_id = request.form.get('camera_id', '').strip().upper()
    cam_name = request.form.get('camera_name', '').strip()
    role = request.form.get('role', CameraRole.ENTRY)
    rtsp_url = request.form.get('rtsp_url', '').strip()
    resolution = request.form.get('resolution', '1920x1080').strip()

    if not cam_id or not cam_name:
        flash('Camera ID and Name are required.', 'warning')
        return redirect(url_for('devices.camera_config'))

    existing = CameraConfig.query.filter_by(camera_id=cam_id).first()
    if existing:
        flash(f"Camera ID '{cam_id}' is already configured.", 'danger')
        return redirect(url_for('devices.camera_config'))

    cam = CameraConfig(
        camera_id=cam_id,
        camera_name=cam_name,
        role=role,
        rtsp_url=rtsp_url if rtsp_url else None,
        resolution=resolution,
        is_enabled=True
    )
    db.session.add(cam)
    db.session.commit()

    log_audit(
        action=AuditAction.CAMERA_CONFIG,
        description=f"Added camera '{cam_name}' ({cam_id}, Role: {role})",
        user=current_user
    )

    flash(f"Camera '{cam_name}' added successfully.", 'success')
    return redirect(url_for('devices.camera_config'))

@devices_bp.route('/cameras/anpr-test', methods=['GET', 'POST'])
@login_required
def anpr_test():
    """ANPR Test Mode: simulate plate OCR and verify against vehicle/RFID."""
    result = None
    if request.method == 'POST':
        plate_text = request.form.get('plate_text', '').strip()
        confidence = float(request.form.get('confidence', 95.0))
        camera_id = request.form.get('camera_id', type=int)
        rfid_uid = request.form.get('rfid_uid', '').strip()

        result = ANPRService.process_plate_detection(
            plate_text=plate_text,
            confidence=confidence,
            camera_id=camera_id,
            rfid_event_id=rfid_uid if rfid_uid else None,
            is_demo=True
        )

    cameras = CameraConfig.query.filter_by(is_enabled=True).all()
    recent_events = ANPREvent.query.order_by(ANPREvent.timestamp.desc()).limit(10).all()

    return render_template(
        'anpr_test.html',
        cameras=cameras,
        recent_events=recent_events,
        result=result
    )
