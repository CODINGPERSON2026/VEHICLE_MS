import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from database.db_init import db
from models.rfid import RFIDCard, CardStatus, normalize_uid
from models.vehicle import Vehicle
from models.device import Device, DeviceStatus
from models.settings import SystemSetting
from models.user import Role
from services.rfid_service import RFIDService
from services.movement_service import MovementService

rfid_bp = Blueprint('rfid', __name__)

# ----------------- WEB RFID MANAGEMENT ----------------- #

@rfid_bp.route('/rfid-cards')
@login_required
def list_cards():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    
    cards = RFIDService.get_all_cards(search=search, status=status)
    vehicles = Vehicle.query.filter_by(is_active=True).order_by(Vehicle.registration_number.asc()).all()
    
    return render_template(
        'rfid_cards.html',
        cards=cards,
        vehicles=vehicles,
        search=search,
        status=status,
        statuses=CardStatus.CHOICES
    )

@rfid_bp.route('/rfid-cards/assign', methods=['POST'])
@login_required
def assign_card():
    if current_user.role == Role.REPORT_VIEWER:
        flash('Permission denied.', 'danger')
        return redirect(url_for('rfid.list_cards'))

    uid = request.form.get('uid', '').strip()
    vehicle_id = request.form.get('vehicle_id')
    expiry_date = request.form.get('expiry_date')
    remarks = request.form.get('remarks', '').strip()

    v_id = int(vehicle_id) if vehicle_id and vehicle_id.isdigit() else None
    success, msg, card = RFIDService.assign_card(
        uid=uid,
        vehicle_id=v_id,
        expiry_date=expiry_date,
        remarks=remarks,
        user=current_user
    )
    
    # Clear enrollment cache if this was the enrolled UID
    RFIDService.clear_enrollment()
    
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('rfid.list_cards'))

@rfid_bp.route('/rfid-cards/<int:card_id>/status', methods=['POST'])
@login_required
def update_card_status(card_id):
    if current_user.role == Role.REPORT_VIEWER:
        flash('Permission denied.', 'danger')
        return redirect(url_for('rfid.list_cards'))

    new_status = request.form.get('status', '').strip()
    remarks = request.form.get('remarks', '').strip()

    success, msg = RFIDService.update_card_status(
        card_id=card_id,
        new_status=new_status,
        remarks=remarks,
        user=current_user
    )
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('rfid.list_cards'))

@rfid_bp.route('/rfid-cards/<int:card_id>/unassign', methods=['POST'])
@login_required
def unassign_card(card_id):
    if current_user.role == Role.REPORT_VIEWER:
        flash('Permission denied.', 'danger')
        return redirect(url_for('rfid.list_cards'))

    success, msg = RFIDService.unassign_card(card_id, user=current_user)
    flash(msg, 'success' if success else 'danger')
    next_url = request.referrer or url_for('rfid.list_cards')
    return redirect(next_url)

@rfid_bp.route('/rfid-cards/<int:card_id>/delete', methods=['POST'])
@login_required
def delete_card(card_id):
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can delete RFID card records.', 'danger')
        return redirect(url_for('rfid.list_cards'))

    success, msg = RFIDService.delete_card(card_id, user=current_user)
    flash(msg, 'success' if success else 'danger')
    next_url = request.referrer or url_for('rfid.list_cards')
    return redirect(next_url)


# ----------------- REST API ENDPOINTS FOR ESP32 & HARDWARE ----------------- #

@rfid_bp.route('/api/rfid/scan', methods=['POST'])
def api_rfid_scan():
    """
    Main hardware endpoint for RFID scans from ESP32.
    Accepts JSON payload:
    {
      "uid": "A37F291C",
      "device_id": "GATE_ENTRY_01",
      "api_key": "...",
      "direction": "ENTRY",
      "event_id": "unique-event-id"
    }
    """
    data = request.get_json(silent=True) or {}
    
    # Extract params (Support both JSON body and HTTP headers for device auth)
    device_id = data.get('device_id') or request.headers.get('X-Device-Id')
    api_key = data.get('api_key') or request.headers.get('X-Api-Key')
    uid = data.get('uid')
    direction = data.get('direction')
    event_id = data.get('event_id') or str(uuid.uuid4())
    is_demo = bool(data.get('is_demo', False))

    if not uid:
        return jsonify({
            "success": False,
            "decision": "ENTRY_DENIED",
            "reason": "UNKNOWN_RFID",
            "message": "Missing 'uid' in scan request."
        }), 400

    response_data, status_code = MovementService.process_rfid_scan(
        device_id=device_id,
        api_key=api_key,
        uid=uid,
        direction=direction,
        event_id=event_id,
        is_demo=is_demo
    )
    
    return jsonify(response_data), status_code

@rfid_bp.route('/api/device/heartbeat', methods=['POST'])
def api_device_heartbeat():
    """
    ESP32 periodic heartbeat endpoint to update online status & IP address.
    """
    data = request.get_json(silent=True) or {}
    device_id = data.get('device_id') or request.headers.get('X-Device-Id')
    api_key = data.get('api_key') or request.headers.get('X-Api-Key')
    firmware_version = data.get('firmware_version', 'v1.0.0')

    if not device_id or not api_key:
        return jsonify({"success": False, "message": "Missing device credentials"}), 401

    device = Device.query.filter_by(device_id=device_id).first()
    if not device or not device.is_active:
        return jsonify({"success": False, "message": "Device not found or inactive"}), 401

    if not device.check_api_key(api_key):
        return jsonify({"success": False, "message": "Invalid device API key"}), 403

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
    if ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    device.update_heartbeat(ip_address=client_ip, firmware_version=firmware_version)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Heartbeat acknowledged",
        "device_id": device.device_id,
        "status": device.status,
        "server_time": datetime.utcnow().isoformat()
    }), 200

@rfid_bp.route('/api/device/status', methods=['GET'])
def api_device_status():
    """Returns server status and configured gate direction."""
    return jsonify({
        "server": "Smart Vehicle Gate API",
        "status": "ONLINE",
        "server_time": datetime.utcnow().isoformat(),
        "gate_direction_mode": SystemSetting.get_value('gate_direction_mode', 'MANUAL_DIRECTION'),
        "scan_cooldown_seconds": int(SystemSetting.get_value('scan_cooldown_seconds', '3'))
    })

@rfid_bp.route('/api/rfid/enroll_scan', methods=['POST'])
def api_enroll_scan():
    """ESP32 sends scan here when enrolling new tags."""
    data = request.get_json(silent=True) or {}
    uid = data.get('uid')
    device_id = data.get('device_id', 'ESP32_READER')
    
    if not uid:
        return jsonify({"success": False, "message": "UID required"}), 400
        
    success, msg = RFIDService.capture_enrollment_scan(uid, device_id)
    return jsonify({"success": success, "message": msg, "uid": normalize_uid(uid)})

@rfid_bp.route('/api/rfid/latest_enrollment', methods=['GET'])
@login_required
def api_latest_enrollment():
    """Frontend polls this to receive newly scanned RFID tag in real-time."""
    enrollment = RFIDService.get_latest_enrollment()
    return jsonify({
        "active": enrollment is not None,
        "data": enrollment
    })

@rfid_bp.route('/api/barrier/status', methods=['GET', 'POST'])
def api_barrier_status():
    """Barrier state simulation polling or triggering."""
    delay = int(SystemSetting.get_value('barrier_auto_close_delay', '4'))
    return jsonify({
        "barrier_status": "READY",
        "auto_close_delay_seconds": delay,
        "timestamp": datetime.utcnow().isoformat()
    })
