from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from database.db_init import db
from models.movement import VehicleMovement, MovementStatus, GateDirection
from models.vehicle import Vehicle, normalize_plate
from models.rfid import RFIDCard, normalize_uid
from models.device import Device
from models.denied_attempt import DeniedAttempt, DeniedReason
from models.settings import SystemSetting
from models.user import Role
from services.movement_service import MovementService
from services.vehicle_service import VehicleService
from services.rfid_service import RFIDService

movements_bp = Blueprint('movements', __name__)


@movements_bp.route('/gate-control')
@login_required
def gate_control():
    """Live Gate Control interface for operators."""
    devices = Device.query.filter_by(is_active=True).all()
    vehicles = Vehicle.query.filter_by(is_active=True).order_by(Vehicle.registration_number.asc()).all()
    direction_mode = SystemSetting.get_value('gate_direction_mode', 'EXIT_ONLY')
    barrier_delay = int(SystemSetting.get_value('barrier_auto_close_delay', '4'))
    
    # Fetch recent movement or denial within last 10 seconds (active scan window)
    threshold = datetime.utcnow() - timedelta(seconds=10)
    latest_movement = VehicleMovement.query.filter(
        (VehicleMovement.exit_time >= threshold) | (VehicleMovement.entry_time >= threshold)
    ).order_by(db.func.coalesce(VehicleMovement.exit_time, VehicleMovement.entry_time).desc()).first()
    latest_denied = DeniedAttempt.query.filter(DeniedAttempt.timestamp >= threshold).order_by(DeniedAttempt.timestamp.desc()).first()

    from models.driver import Driver
    drivers = Driver.query.filter_by(is_active=True).order_by(Driver.name.asc()).all()
    
    outside_count = Vehicle.query.filter_by(is_active=True, current_vehicle_location='OUT').count()
    inside_count = Vehicle.query.filter_by(is_active=True, current_vehicle_location='INSIDE').count()

    return render_template(
        'gate_control.html',
        devices=devices,
        vehicles=vehicles,
        drivers=drivers,
        direction_mode=direction_mode,
        barrier_delay=barrier_delay,
        latest_movement=latest_movement,
        latest_denied=latest_denied,
        inside_count=inside_count,
        outside_count=outside_count
    )

@movements_bp.route('/movements/set-direction', methods=['POST'])
@login_required
def set_gate_direction():
    """Quickly switch active gate direction between ENTRY, EXIT, or MANUAL."""
    new_dir = request.form.get('direction', 'ENTRY').strip().upper()
    if new_dir in ['ENTRY', 'ENTRY_ONLY']:
        SystemSetting.set_value('gate_direction_mode', 'ENTRY_ONLY')
        flash('Gate Mode switched to: ENTRY ONLY (Incoming Vehicles)', 'success')
    elif new_dir in ['EXIT', 'EXIT_ONLY']:
        SystemSetting.set_value('gate_direction_mode', 'EXIT_ONLY')
        flash('Gate Mode switched to: EXIT ONLY (Outgoing Vehicles)', 'info')
    else:
        SystemSetting.set_value('gate_direction_mode', 'MANUAL_DIRECTION')
        flash('Gate Mode switched to: MANUAL / FLEXIBLE DIRECTION', 'secondary')

    next_page = request.referrer or url_for('movements.gate_control')
    return redirect(next_page)

@movements_bp.route('/movement-register')
@login_required
def movement_register():
    """Digital gate register with filtering and pagination."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    direction = request.args.get('direction', '').strip()

    query = VehicleMovement.query.join(Vehicle)

    if search:
        s = f"%{search}%"
        norm_s = normalize_plate(search)
        query = query.filter(
            (Vehicle.registration_number.ilike(f"%{norm_s}%") if norm_s else False) |
            Vehicle.driver_name.ilike(s) |
            Vehicle.mobile_number.ilike(s) |
            VehicleMovement.remarks.ilike(s)
        )

    if status and status in MovementStatus.CHOICES:
        query = query.filter(VehicleMovement.status == status)

    if direction and direction in [GateDirection.ENTRY, GateDirection.EXIT]:
        query = query.filter(VehicleMovement.direction == direction)

    if start_date:
        try:
            s_dt = datetime.combine(datetime.strptime(start_date, '%Y-%m-%d').date(), datetime.min.time())
            query = query.filter(VehicleMovement.entry_time >= s_dt)
        except ValueError:
            pass

    if end_date:
        try:
            e_dt = datetime.combine(datetime.strptime(end_date, '%Y-%m-%d').date(), datetime.max.time())
            query = query.filter(VehicleMovement.entry_time <= e_dt)
        except ValueError:
            pass

    pagination = query.order_by(VehicleMovement.entry_time.desc()).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        'movement_register.html',
        pagination=pagination,
        movements=pagination.items,
        search=search,
        status=status,
        direction=direction,
        start_date=start_date,
        end_date=end_date,
        statuses=MovementStatus.CHOICES
    )

@movements_bp.route('/currently-inside')
@movements_bp.route('/vehicles-inside')
@login_required
def currently_inside():
    """Vehicles currently stationed INSIDE depot/premises (Available)."""
    search = request.args.get('search', '').strip()
    
    query = Vehicle.query.filter(
        Vehicle.is_active == True,
        Vehicle.current_vehicle_location == 'INSIDE'
    )
    
    if search:
        s = f"%{search}%"
        norm_s = normalize_plate(search)
        query = query.filter(
            (Vehicle.registration_number.ilike(f"%{norm_s}%") if norm_s else False) |
            Vehicle.driver_name.ilike(s) |
            Vehicle.mobile_number.ilike(s)
        )
        
    inside_vehicles = query.order_by(Vehicle.registration_number.asc()).all()
    return render_template('currently_inside.html', vehicles=inside_vehicles, search=search)

@movements_bp.route('/currently-outside')
@movements_bp.route('/vehicles-outside')
@login_required
def currently_outside():
    """Vehicles currently on trip (OUTSIDE premises)."""
    search = request.args.get('search', '').strip()
    
    query = VehicleMovement.query.filter_by(status=MovementStatus.OUTSIDE).join(Vehicle)
    if search:
        s = f"%{search}%"
        norm_s = normalize_plate(search)
        query = query.filter(
            (Vehicle.registration_number.ilike(f"%{norm_s}%") if norm_s else False) |
            Vehicle.driver_name.ilike(s) |
            VehicleMovement.driver_name.ilike(s) |
            Vehicle.mobile_number.ilike(s)
        )
        
    outside_vehicles = query.order_by(VehicleMovement.exit_time.desc()).all()
    return render_template('currently_outside.html', movements=outside_vehicles, search=search)

@movements_bp.route('/movements/<int:vehicle_id>/quick_return', methods=['POST'])
@login_required
def quick_return_vehicle(vehicle_id):
    """1-click action to record vehicle return back to depot (Manual Check-In / IN)."""
    if current_user.role == Role.REPORT_VIEWER:
        flash('Permission denied.', 'danger')
        return redirect(request.referrer or url_for('movements.gate_control'))

    remarks = request.form.get('remarks', 'Vehicle Returned to Depot (Arrival Check-In)').strip()
    success, msg, _ = MovementService.process_manual_movement(
        vehicle_id=vehicle_id,
        direction=GateDirection.ENTRY,
        reason="Vehicle returned to depot (Arrival Check-In)",
        operator_user=current_user,
        remarks=remarks
    )
    if success:
        flash('Vehicle marked RETURNED (IN Depot) successfully.', 'success')
    else:
        flash(msg, 'danger')

    return redirect(request.referrer or url_for('movements.gate_control'))

@movements_bp.route('/denied-attempts')
@login_required
def denied_attempts():
    """Log of unauthorized and denied scan attempts."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    reason = request.args.get('reason', '').strip()

    query = DeniedAttempt.query
    if search:
        s = f"%{search}%"
        norm_s = normalize_plate(search)
        norm_uid = normalize_uid(search)
        query = query.filter(
            (DeniedAttempt.vehicle_number.ilike(f"%{norm_s}%") if norm_s else False) |
            (DeniedAttempt.rfid_uid.ilike(f"%{norm_uid}%") if norm_uid else False) |
            DeniedAttempt.remarks.ilike(s)
        )

    if reason and reason in DeniedReason.CHOICES:
        query = query.filter_by(reason=reason)

    pagination = query.order_by(DeniedAttempt.timestamp.desc()).paginate(page=page, per_page=25, error_out=False)

    return render_template(
        'denied_attempts.html',
        pagination=pagination,
        attempts=pagination.items,
        search=search,
        reason=reason,
        reasons=DeniedReason.CHOICES
    )

@movements_bp.route('/movements/manual', methods=['POST'])
@login_required
def manual_movement():
    """Process manual vehicle IN or OUT with mandatory operator reason."""
    if current_user.role == Role.REPORT_VIEWER:
        flash('Permission denied. Report Viewers cannot perform manual overrides.', 'danger')
        return redirect(url_for('movements.gate_control'))

    vehicle_id = request.form.get('vehicle_id', type=int)
    direction = request.form.get('direction', 'ENTRY')
    reason = request.form.get('reason', '').strip()
    remarks = request.form.get('remarks', '').strip()

    if not vehicle_id:
        flash('Please select a valid vehicle.', 'warning')
        return redirect(url_for('movements.gate_control'))

    success, msg, mov = MovementService.process_manual_movement(
        vehicle_id=vehicle_id,
        direction=direction,
        reason=reason,
        operator_user=current_user,
        remarks=remarks
    )

    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')

    return redirect(url_for('movements.gate_control'))

@movements_bp.route('/api/movements/live_feed')
@login_required
def live_gate_feed():
    """Live JSON endpoint for Gate Control view polling."""
    threshold = datetime.utcnow() - timedelta(seconds=10)
    latest_movement = VehicleMovement.query.filter(
        (VehicleMovement.exit_time >= threshold) | (VehicleMovement.entry_time >= threshold)
    ).order_by(db.func.coalesce(VehicleMovement.exit_time, VehicleMovement.entry_time).desc()).first()
    latest_denied = DeniedAttempt.query.filter(DeniedAttempt.timestamp >= threshold).order_by(DeniedAttempt.timestamp.desc()).first()
    
    last_event = None
    if latest_movement and latest_denied:
        m_time = latest_movement.exit_time if latest_movement.status == MovementStatus.OUTSIDE and latest_movement.exit_time else latest_movement.entry_time
        if m_time >= latest_denied.timestamp:
            event_type = 'MOVEMENT'
        else:
            event_type = 'DENIED'
    elif latest_movement:
        event_type = 'MOVEMENT'
    elif latest_denied:
        event_type = 'DENIED'
    else:
        event_type = None

    if event_type == 'MOVEMENT' and latest_movement:
        evt_time = latest_movement.exit_time if latest_movement.status == MovementStatus.OUTSIDE and latest_movement.exit_time else latest_movement.entry_time
        last_event = {
            "type": "MOVEMENT",
            "movement_id": latest_movement.id,
            "decision": "EXIT_RECORDED" if latest_movement.status == MovementStatus.OUTSIDE else "ENTRY_ALLOWED",
            "vehicle_number": latest_movement.vehicle.registration_number if latest_movement.vehicle else "N/A",
            "vehicle_type": latest_movement.vehicle.vehicle_type if latest_movement.vehicle else "N/A",
            "driver_name": latest_movement.driver_name or (latest_movement.vehicle.driver_name if latest_movement.vehicle else "N/A"),
            "owner_driver": latest_movement.vehicle.driver_name if latest_movement.vehicle else "N/A",
            "auth_status": latest_movement.vehicle.auth_status if latest_movement.vehicle else "N/A",
            "rfid_uid": latest_movement.rfid_card.uid if latest_movement.rfid_card else "N/A",
            "direction": latest_movement.direction,
            "status": latest_movement.status,
            "duration": latest_movement.formatted_duration,
            "time": evt_time.strftime('%H:%M:%S') if evt_time else '',
            "is_manual": latest_movement.is_manual
        }
    elif event_type == 'DENIED' and latest_denied:
        last_event = {
            "type": "DENIED",
            "decision": f"DENIED_{latest_denied.direction}",
            "vehicle_number": latest_denied.vehicle_number or (latest_denied.vehicle.registration_number if latest_denied.vehicle else "N/A"),
            "vehicle_type": latest_denied.vehicle.vehicle_type if latest_denied.vehicle else "Unknown",
            "driver_name": latest_denied.vehicle.driver_name if latest_denied.vehicle else "Unknown",
            "auth_status": latest_denied.vehicle.auth_status if latest_denied.vehicle else "DENIED",
            "rfid_uid": latest_denied.rfid_uid or "Unknown",
            "direction": latest_denied.direction,
            "status": latest_denied.reason,
            "time": latest_denied.timestamp.strftime('%H:%M:%S'),
            "remarks": latest_denied.remarks
        }

    outside_count = Vehicle.query.filter_by(is_active=True, current_vehicle_location='OUT').count()
    inside_count = Vehicle.query.filter_by(is_active=True, current_vehicle_location='INSIDE').count()
    pending_scan = RFIDService.get_pending_scan()

    return jsonify({
        "last_event": last_event,
        "pending_scan": pending_scan,
        "inside_count": inside_count,
        "outside_count": outside_count,
        "server_time": datetime.utcnow().strftime('%H:%M:%S')
    })

@movements_bp.route('/api/movements/confirm_scan', methods=['POST'])
@login_required
def api_confirm_scan():
    """
    Operator confirms IN or OUT for a scanned vehicle.
    Updates the movement record, inside/outside counts, and audit trail.
    """
    data = request.get_json(silent=True) or {}
    uid = data.get('uid')
    direction = data.get('direction', 'ENTRY')
    vehicle_id = data.get('vehicle_id')
    driver_id = data.get('driver_id')
    driver_name = data.get('driver_name')
    remarks = data.get('remarks')
    device_id = data.get('device_id', 'GATE01')

    if not uid:
        return jsonify({"success": False, "message": "RFID UID is required."}), 400

    v_id = int(vehicle_id) if vehicle_id and str(vehicle_id).isdigit() else None
    d_id = int(driver_id) if driver_id and str(driver_id).isdigit() else None

    success, msg, movement_data = MovementService.confirm_movement(
        uid=uid,
        direction=direction,
        driver_id=d_id,
        driver_name=driver_name,
        operator_user=current_user,
        remarks=remarks,
        device_id=device_id,
        vehicle_id=v_id
    )

    if not success:
        return jsonify({"success": False, "message": msg}), 400

    return jsonify({
        "success": True,
        "message": msg,
        "data": movement_data
    }), 200
