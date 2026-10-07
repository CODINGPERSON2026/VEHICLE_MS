from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from database.db_init import db
from models.vehicle import Vehicle, AuthStatus, VehicleType
from models.rfid import RFIDCard, CardStatus
from models.movement import VehicleMovement, MovementStatus, GateDirection
from models.denied_attempt import DeniedAttempt
from models.device import Device, DeviceStatus
from models.settings import SystemSetting

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    refresh_interval = int(SystemSetting.get_value('dashboard_refresh_interval', '1'))
    return render_template('dashboard.html', refresh_interval=refresh_interval)

@dashboard_bp.route('/api/dashboard/stats')
@login_required
def get_stats():
    """Returns real-time KPI metrics."""
    today = date.today()
    start_today = datetime.combine(today, datetime.min.time())
    end_today = datetime.combine(today, datetime.max.time())

    total_vehicles = Vehicle.query.filter_by(is_active=True).count()
    authorized_vehicles = Vehicle.query.filter_by(is_active=True, auth_status=AuthStatus.AUTHORIZED).count()
    expired_vehicles = Vehicle.query.filter_by(is_active=True, auth_status=AuthStatus.EXPIRED).count()
    blocked_vehicles = Vehicle.query.filter_by(is_active=True, auth_status=AuthStatus.BLOCKED).count()
    
    total_rfid_cards = RFIDCard.query.count()
    vehicles_outside = Vehicle.query.filter_by(is_active=True, current_vehicle_location='OUT').count()
    vehicles_inside = Vehicle.query.filter_by(is_active=True, current_vehicle_location='INSIDE').count()
    
    today_in = VehicleMovement.query.filter(
        VehicleMovement.entry_time.between(start_today, end_today)
    ).count()
    
    today_out = VehicleMovement.query.filter(
        VehicleMovement.exit_time.between(start_today, end_today)
    ).count()
    
    today_denied = DeniedAttempt.query.filter(
        DeniedAttempt.timestamp.between(start_today, end_today)
    ).count()

    # Calculate active online devices
    timeout_sec = int(SystemSetting.get_value('device_heartbeat_timeout', '35'))
    threshold_time = datetime.utcnow() - timedelta(seconds=timeout_sec)
    connected_devices = Device.query.filter(
        Device.is_active == True,
        Device.last_seen >= threshold_time
    ).count()

    return jsonify({
        "total_vehicles": total_vehicles,
        "authorized_vehicles": authorized_vehicles,
        "expired_vehicles": expired_vehicles,
        "blocked_vehicles": blocked_vehicles,
        "total_rfid_cards": total_rfid_cards,
        "vehicles_inside": vehicles_inside,
        "vehicles_outside": vehicles_outside,
        "today_in": today_in,
        "today_out": today_out,
        "denied_attempts": today_denied,
        "connected_devices": connected_devices,
        "timestamp": datetime.utcnow().isoformat()
    })

@dashboard_bp.route('/api/dashboard/charts')
@login_required
def get_charts():
    """Returns series data for Chart.js dashboard charts."""
    today = date.today()

    # 1. Daily IN vs OUT (Last 7 Days)
    days_labels = []
    daily_in_data = []
    daily_out_data = []
    for i in range(6, -1, -1):
        day_val = today - timedelta(days=i)
        days_labels.append(day_val.strftime('%a, %d %b'))
        
        s_dt = datetime.combine(day_val, datetime.min.time())
        e_dt = datetime.combine(day_val, datetime.max.time())
        
        in_cnt = VehicleMovement.query.filter(VehicleMovement.entry_time.between(s_dt, e_dt)).count()
        out_cnt = VehicleMovement.query.filter(VehicleMovement.exit_time.between(s_dt, e_dt)).count()
        
        daily_in_data.append(in_cnt)
        daily_out_data.append(out_cnt)

    # 2. Vehicle Type Distribution
    type_labels = VehicleType.CHOICES
    type_counts = []
    for vt in type_labels:
        cnt = Vehicle.query.filter_by(is_active=True, vehicle_type=vt).count()
        type_counts.append(cnt)

    # 3. Denied attempts trend (Last 7 Days)
    denied_trend = []
    for i in range(6, -1, -1):
        day_val = today - timedelta(days=i)
        s_dt = datetime.combine(day_val, datetime.min.time())
        e_dt = datetime.combine(day_val, datetime.max.time())
        d_cnt = DeniedAttempt.query.filter(DeniedAttempt.timestamp.between(s_dt, e_dt)).count()
        denied_trend.append(d_cnt)

    # 4. Weekly movement (Last 4 Weeks)
    week_labels = []
    week_movements = []
    for w in range(3, -1, -1):
        w_start = today - timedelta(days=(w + 1) * 7)
        w_end = today - timedelta(days=w * 7)
        week_labels.append(f"Week {4 - w}")
        s_dt = datetime.combine(w_start, datetime.min.time())
        e_dt = datetime.combine(w_end, datetime.max.time())
        w_cnt = VehicleMovement.query.filter(VehicleMovement.entry_time.between(s_dt, e_dt)).count()
        week_movements.append(w_cnt)

    return jsonify({
        "daily_in_out": {
            "labels": days_labels,
            "in_data": daily_in_data,
            "out_data": daily_out_data
        },
        "vehicle_types": {
            "labels": type_labels,
            "data": type_counts
        },
        "denied_trend": {
            "labels": days_labels,
            "data": denied_trend
        },
        "weekly_movement": {
            "labels": week_labels,
            "data": week_movements
        }
    })

@dashboard_bp.route('/api/dashboard/recent_activity')
@login_required
def get_recent_activity():
    """Returns recent combined activity feed for the dashboard table."""
    from models.driver import Driver
    recent_movements = VehicleMovement.query.order_by(
        db.func.coalesce(VehicleMovement.exit_time, VehicleMovement.entry_time).desc()
    ).limit(10).all()
    recent_denials = DeniedAttempt.query.order_by(DeniedAttempt.timestamp.desc()).limit(10).all()

    combined = []
    for m in recent_movements:
        drv_record = None
        if m.driver_id:
            drv_record = db.session.get(Driver, m.driver_id)
        if not drv_record and m.rfid_card and m.rfid_card.driver:
            drv_record = m.rfid_card.driver
        if not drv_record and m.driver_name:
            drv_record = Driver.query.filter_by(name=m.driver_name).first()

        drv_name = m.driver_name or (drv_record.name if drv_record else "Unassigned")
        drv_mobile = drv_record.mobile_number if drv_record and drv_record.mobile_number else None

        v_type = m.vehicle.vehicle_type if m.vehicle else "N/A"
        v_plate = m.vehicle.registration_number if m.vehicle else "N/A"
        event_time = m.exit_time if m.exit_time and m.status == MovementStatus.OUTSIDE else m.entry_time

        combined.append({
            "timestamp": event_time.strftime('%H:%M:%S') if event_time else "--:--:--",
            "raw_time": event_time,
            "driver_name": drv_name,
            "driver_mobile": drv_mobile,
            "vehicle_number": v_plate,
            "vehicle_type": v_type,
            "event": "EXIT" if m.status == MovementStatus.OUTSIDE else "ENTRY",
            "badge_class": "bg-info text-white" if m.status == MovementStatus.OUTSIDE else "bg-success text-white"
        })

    for d in recent_denials:
        drv_record = None
        if d.rfid_uid:
            card = RFIDCard.query.filter_by(uid=d.rfid_uid).first()
            if card and card.driver:
                drv_record = card.driver

        drv_name = drv_record.name if drv_record else "Unknown"
        drv_mobile = drv_record.mobile_number if drv_record and drv_record.mobile_number else None

        v_type = d.vehicle.vehicle_type if d.vehicle else "N/A"
        v_plate = d.vehicle_number or (d.vehicle.registration_number if d.vehicle else "N/A")

        combined.append({
            "timestamp": d.timestamp.strftime('%H:%M:%S') if d.timestamp else "--:--:--",
            "raw_time": d.timestamp,
            "driver_name": drv_name,
            "driver_mobile": drv_mobile,
            "vehicle_number": v_plate,
            "vehicle_type": v_type,
            "event": f"DENIED ({d.direction})" if d.direction else "DENIED",
            "badge_class": "bg-danger text-white"
        })

    combined.sort(key=lambda x: x['raw_time'] or datetime.min, reverse=True)
    clean_feed = [{k: v for k, v in item.items() if k != 'raw_time'} for item in combined[:15]]

    return jsonify(clean_feed)
