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
    refresh_interval = int(SystemSetting.get_value('dashboard_refresh_interval', '5'))
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
    vehicles_outside = VehicleMovement.query.filter_by(status=MovementStatus.OUTSIDE).count()
    vehicles_inside = max(0, total_vehicles - vehicles_outside)
    
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
    recent_movements = VehicleMovement.query.order_by(VehicleMovement.entry_time.desc()).limit(10).all()
    recent_denials = DeniedAttempt.query.order_by(DeniedAttempt.timestamp.desc()).limit(10).all()

    combined = []
    for m in recent_movements:
        combined.append({
            "timestamp": m.exit_time.strftime('%H:%M:%S') if m.exit_time and m.status == MovementStatus.OUTSIDE else m.entry_time.strftime('%H:%M:%S'),
            "raw_time": m.exit_time if m.exit_time and m.status == MovementStatus.OUTSIDE else m.entry_time,
            "vehicle_number": m.vehicle.registration_number if m.vehicle else "N/A",
            "rfid_uid": m.rfid_card.uid if m.rfid_card else "N/A",
            "event": "EXIT" if m.status == MovementStatus.OUTSIDE else "ENTRY",
            "status": m.status,
            "device": m.exit_device.device_name if m.status == MovementStatus.OUTSIDE and m.exit_device else (m.entry_device.device_name if m.entry_device else "System"),
            "badge_class": "bg-success" if m.status == MovementStatus.INSIDE else "bg-info"
        })

    for d in recent_denials:
        combined.append({
            "timestamp": d.timestamp.strftime('%H:%M:%S'),
            "raw_time": d.timestamp,
            "vehicle_number": d.vehicle_number or (d.vehicle.registration_number if d.vehicle else "Unknown"),
            "rfid_uid": d.rfid_uid or "Unknown",
            "event": f"DENIED ({d.direction})",
            "status": d.reason,
            "device": d.device.device_name if d.device else "System",
            "badge_class": "bg-danger"
        })

    combined.sort(key=lambda x: x['raw_time'], reverse=True)
    clean_feed = [{k: v for k, v in item.items() if k != 'raw_time'} for item in combined[:15]]

    return jsonify(clean_feed)
