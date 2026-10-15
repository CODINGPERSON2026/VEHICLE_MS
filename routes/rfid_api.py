import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from database.db_init import db
from models.rfid import RFIDCard, CardStatus, normalize_uid
from models.vehicle import Vehicle
from models.driver import Driver
from models.device import Device, DeviceStatus
from models.denied_attempt import DeniedAttempt, DeniedReason
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
    
    # Query all active vehicles that do NOT currently have an active RFID card assigned
    assigned_vehicle_ids = [
        c.vehicle_id for c in RFIDCard.query.filter(
            RFIDCard.vehicle_id.isnot(None),
            RFIDCard.card_status == CardStatus.ACTIVE
        ).all()
    ]
    if assigned_vehicle_ids:
        unassigned_vehicles = Vehicle.query.filter(
            Vehicle.is_active == True,
            ~Vehicle.id.in_(assigned_vehicle_ids)
        ).order_by(Vehicle.registration_number.asc()).all()
    else:
        unassigned_vehicles = Vehicle.query.filter_by(is_active=True).order_by(Vehicle.registration_number.asc()).all()
        
    drivers = Driver.query.filter_by(is_active=True).order_by(Driver.name.asc()).all()
    
    return render_template(
        'rfid_cards.html',
        cards=cards,
        vehicles=unassigned_vehicles,
        unassigned_vehicles=unassigned_vehicles,
        drivers=drivers,
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
    assign_type = request.form.get('assign_type', '').strip()
    driver_id = request.form.get('driver_id')
    vehicle_id = request.form.get('vehicle_id')
    expiry_date = request.form.get('expiry_date')
    remarks = request.form.get('remarks', '').strip()

    d_id = int(driver_id) if driver_id and str(driver_id).isdigit() else None
    v_id = int(vehicle_id) if vehicle_id and str(vehicle_id).isdigit() else None

    # Support unassigned tag registration or assigning driver, vehicle, or both
    if assign_type == 'unassigned':
        d_id = None
        v_id = None
    elif not d_id and not v_id:
        flash('Please select at least a Driver or an Unassigned Vehicle (or both) to assign this RFID card.', 'warning')
        return redirect(url_for('rfid.list_cards'))

    success, msg, card = RFIDService.assign_card(
        uid=uid,
        vehicle_id=v_id,
        driver_id=d_id,
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
    alcohol_detected = bool(data.get('alcohol_detected', False))
    alcohol_value = data.get('alcohol_value')
    if alcohol_value is not None:
        try:
            alcohol_value = float(alcohol_value)
            if alcohol_value > 600:
                alcohol_detected = True
        except (ValueError, TypeError):
            pass

    if not uid:
        return jsonify({
            "success": False,
            "decision": "ENTRY_DENIED",
            "reason": "UNKNOWN_RFID",
            "message": "Missing 'uid' in scan request."
        }), 400

    # Capture card for Live Hardware Enrollment Modal immediately
    norm_uid = normalize_uid(uid)
    if norm_uid:
        try:
            RFIDService.capture_enrollment_scan(norm_uid, device_id)
        except Exception:
            pass

    # If alcohol is detected, immediately deny access and do not stage as pending confirmation
    if alcohol_detected:
        response_data, status_code = MovementService.process_rfid_scan(
            device_id=device_id,
            api_key=api_key,
            uid=uid,
            direction=direction,
            event_id=event_id,
            is_demo=is_demo,
            alcohol_detected=True,
            alcohol_value=alcohol_value
        )
        return jsonify(response_data), status_code

    require_confirmation = SystemSetting.get_value('require_guard_confirmation', '1') != '0'
    bypass_confirm = bool(data.get('bypass_confirmation', False)) or bool(data.get('direct', False))

    if require_confirmation and not bypass_confirm:
        lookup = RFIDService.stage_pending_scan(uid, device_id=device_id, alcohol_value=alcohol_value, alcohol_detected=alcohol_detected)
        if not lookup.get('success'):
            return jsonify({
                "success": False,
                "decision": "ENTRY_DENIED",
                "reason": lookup.get("reason", "UNKNOWN_RFID"),
                "message": lookup.get("message", "Scan validation failed.")
            }), 400

        return jsonify({
            "success": True,
            "decision": "AWAITING_CONFIRMATION",
            "message": "Card scan accepted. Awaiting guard confirmation in Gate Control.",
            "vehicle_number": lookup["vehicle"]["registration_number"],
            "vehicle_type": lookup["vehicle"]["vehicle_type"],
            "driver_name": lookup["driver"]["name"],
            "current_status": lookup["current_status"],
            "recommended_direction": lookup["recommended_direction"],
            "scan_id": lookup.get("scan_id"),
            "event_id": event_id
        }), 200

    response_data, status_code = MovementService.process_rfid_scan(
        device_id=device_id,
        api_key=api_key,
        uid=uid,
        direction=direction,
        event_id=event_id,
        is_demo=is_demo,
        alcohol_detected=alcohol_detected,
        alcohol_value=alcohol_value
    )
    
    return jsonify(response_data), status_code

@rfid_bp.route('/api/rfid/lookup_scan', methods=['POST'])
def api_lookup_scan():
    """Look up card, vehicle, and driver details for confirmation modal."""
    data = request.get_json(silent=True) or {}
    uid = data.get('uid')
    device_id = data.get('device_id', 'GATE01')
    if not uid:
        return jsonify({"success": False, "message": "UID is required."}), 400

    result = RFIDService.stage_pending_scan(uid, device_id=device_id)
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code

@rfid_bp.route('/api/rfid/cancel_pending_scan', methods=['POST'])
def api_cancel_pending_scan():
    """Cancel and discard currently active pending scan."""
    RFIDService.clear_pending_scan()
    return jsonify({"success": True, "message": "Pending scan discarded."})

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

    # Capture live gas/alcohol reading if sent in heartbeat
    raw_gas = data.get('alcohol_value') or data.get('gas_value') or data.get('gasValue') or data.get('analog_value')
    if raw_gas is not None:
        try:
            gas_num = float(raw_gas)
            RFIDService.record_live_sensor_reading(gas_num, device_id)
            RFIDService.record_sobriety_test(gas_num, device_id)
        except (ValueError, TypeError):
            pass

    pending = RFIDService.get_pending_scan()
    return jsonify({
        "success": True,
        "message": "Heartbeat acknowledged",
        "device_id": device.device_id,
        "status": device.status,
        "has_pending_scan": pending is not None,
        "server_time": datetime.now().isoformat()
    }), 200

@rfid_bp.route('/api/device/status', methods=['GET'])
def api_device_status():
    """Returns server status and configured gate direction."""
    return jsonify({
        "server": "Smart Vehicle Gate API",
        "status": "ONLINE",
        "server_time": datetime.now().isoformat(),
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
        "timestamp": datetime.now().isoformat()
    })

@rfid_bp.route('/api/device/alcohol_alert', methods=['POST'])
def api_device_alcohol_alert():
    """
    Real-time endpoint triggered when hardware MQ sensor alarms on alcohol/liquor.
    If a vehicle scan is currently open/pending confirmation on screen, automatically flags it as INTOXICATED,
    records a DeniedAttempt violation, and triggers real-time alerts.
    """
    data = request.get_json(silent=True) or {}
    device_id = data.get('device_id') or request.headers.get('X-Device-Id', 'GATE01')
    alcohol_value = data.get('alcohol_value')
    if alcohol_value is not None:
        try:
            alcohol_value = float(alcohol_value)
        except (ValueError, TypeError):
            pass

    # If reading is within normal limits (<= 600), record normal sobriety reading instead of alarm
    if alcohol_value is not None and alcohol_value <= 600:
        RFIDService.record_live_sensor_reading(alcohol_value, device_id)
        ok, pending_data = RFIDService.record_sobriety_test(alcohol_value=alcohol_value, device_id=device_id)
        return jsonify({
            "success": True,
            "message": "Normal sensor reading accepted.",
            "alcohol_detected": False,
            "alcohol_value": alcohol_value,
            "has_pending_scan": ok,
            "sobriety_status": "PASSED" if ok else "NORMAL"
        }), 200

    pending = RFIDService.get_pending_scan()
    if pending:
        # If vehicle is currently outside (returning for IN), alcohol check is NOT applicable
        is_returning = (pending.get('is_outside') is True or pending.get('current_status') == 'OUTSIDE' or pending.get('recommended_direction') == 'ENTRY')
        if is_returning:
            return jsonify({
                "success": True,
                "message": "Vehicle is returning to depot (IN). Alcohol check not applicable for arrival.",
                "has_pending_scan": True,
                "alcohol_detected": False
            }), 200

        # Flag pending scan as alcohol detected for OUTBOUND dispatch
        RFIDService.flag_pending_scan_alcohol(device_id=device_id, alcohol_value=alcohol_value)

        # Automatically log to DeniedAttempt without clearing pending scan so MT NCO can reassign driver!
        veh = pending.get('vehicle', {})
        drv = pending.get('driver', {})
        uid = pending.get('uid')
        direction = pending.get('recommended_direction', 'ENTRY')

        MovementService.report_alcohol_violation(
            uid=uid,
            direction=direction,
            driver_id=drv.get('id'),
            driver_name=drv.get('name'),
            remarks=f"Automatic Hardware Sensor Alarm: MQ-3 sensor alarm triggered (Value: {alcohol_value or 'Threshold exceeded'}).",
            device_id=device_id,
            vehicle_id=veh.get('id'),
            clear_pending=False
        )

        return jsonify({
            "success": True,
            "message": "Alcohol detected on pending vehicle scan. Driver flagged as INTOXICATED. Reassign driver required.",
            "alcohol_detected": True,
            "alcohol_value": alcohol_value,
            "driver_name": drv.get('name')
        }), 200
    else:
        # Only look for alcohol detection when the MODAL Verify Vehicle & Driver IS OPEN
        # When no verification modal is open, do not create DeniedAttempt or alarms
        return jsonify({
            "success": True,
            "message": "Ignored alcohol trigger: No vehicle verification modal is currently open.",
            "alcohol_detected": False,
            "has_pending_scan": False
        }), 200

@rfid_bp.route('/api/device/sobriety_reading', methods=['POST'])
def api_device_sobriety_reading():
    """
    Receives MQ-3 breathalyzer analog reading (0-4095).
    If <= 600: Clears sobriety test as PASSED (SOBER).
    If > 600: Flags as FAILED (INTOXICATED), records violation, and instructs voice warning.
    """
    data = request.get_json(silent=True) or {}
    device_id = data.get('device_id') or request.headers.get('X-Device-Id', 'GATE01')
    raw_val = data.get('alcohol_value')
    if raw_val is None:
        return jsonify({"success": False, "message": "alcohol_value is required"}), 400

    try:
        alcohol_value = float(raw_val)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid numeric alcohol_value"}), 400

    ok, pending_data = RFIDService.record_sobriety_test(alcohol_value=alcohol_value, device_id=device_id)
    passed = (alcohol_value <= 600)

    if not ok:
        return jsonify({
            "success": True,
            "has_pending_scan": False,
            "alcohol_value": alcohol_value,
            "passed": passed,
            "message": "No active vehicle scan currently waiting for sobriety test."
        }), 200

    if not passed:
        # Log violation to DeniedAttempt
        veh = pending_data.get('vehicle', {})
        drv = pending_data.get('driver', {})
        MovementService.report_alcohol_violation(
            uid=pending_data.get('uid'),
            direction=pending_data.get('recommended_direction', 'ENTRY'),
            driver_id=drv.get('id'),
            driver_name=drv.get('name'),
            remarks=f"MQ-3 Breathalyzer Failed: Value {alcohol_value} > 600. Driver intoxicated.",
            device_id=device_id,
            vehicle_id=veh.get('id'),
            clear_pending=False
        )

    return jsonify({
        "success": True,
        "has_pending_scan": True,
        "passed": passed,
        "alcohol_value": alcohol_value,
        "sobriety_status": "PASSED" if passed else "FAILED",
        "driver_name": pending_data.get('driver', {}).get('name'),
        "message": "Sobriety test PASSED (< 600)" if passed else "Liquor DETECTED (> 600)!"
    }), 200

@rfid_bp.route('/api/rfid/update_pending_driver', methods=['POST'])
@login_required
def api_update_pending_driver():
    """
    Called when MT NCO / Guard selects a replacement driver from the modal dropdown.
    Resets the sobriety state to AWAITING_TEST so the new driver must blow into MQ-3 detector!
    """
    data = request.get_json(silent=True) or {}
    driver_id = data.get('driver_id')
    driver_name = data.get('driver_name')

    ok, updated_data = RFIDService.update_pending_driver(
        driver_id=driver_id,
        driver_name=driver_name
    )

    if not ok:
        return jsonify({"success": False, "message": "No active pending scan found to update."}), 404

    return jsonify({
        "success": True,
        "message": "Driver updated. Sobriety test reset to AWAITING_TEST.",
        "pending_scan": updated_data
    }), 200
