from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from database.db_init import db
from models.driver import Driver
from models.movement import VehicleMovement
from models.user import Role
from services.driver_service import DriverService

drivers_bp = Blueprint('drivers', __name__)

from models.vehicle import VehicleType

@drivers_bp.route('/drivers')
@login_required
def list_drivers():
    search = request.args.get('search', '').strip()
    active_only = request.args.get('active_only') == '1'
    drivers = DriverService.get_all_drivers(search=search, active_only=active_only)
    
    return render_template(
        'drivers.html',
        drivers=drivers,
        search=search,
        active_only=active_only,
        vehicle_types=VehicleType.CHOICES
    )

@drivers_bp.route('/drivers/new', methods=['POST'])
@login_required
def create_driver():
    if current_user.role == Role.REPORT_VIEWER:
        flash('Permission denied.', 'danger')
        return redirect(url_for('drivers.list_drivers'))

    success, msg, _ = DriverService.create_driver(request.form, user=current_user)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('drivers.list_drivers'))

@drivers_bp.route('/drivers/<int:driver_id>/edit', methods=['POST'])
@login_required
def edit_driver(driver_id):
    if current_user.role == Role.REPORT_VIEWER:
        flash('Permission denied.', 'danger')
        return redirect(url_for('drivers.list_drivers'))

    success, msg = DriverService.update_driver(driver_id, request.form, user=current_user)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('drivers.list_drivers'))

@drivers_bp.route('/drivers/<int:driver_id>/delete', methods=['POST'])
@login_required
def delete_driver(driver_id):
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can delete driver profiles.', 'danger')
        return redirect(url_for('drivers.list_drivers'))

    success, msg = DriverService.delete_driver(driver_id, user=current_user)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('drivers.list_drivers'))

@drivers_bp.route('/api/drivers/list')
@login_required
def api_drivers_list():
    """Returns JSON list of active drivers for Gate Control quick picker."""
    drivers = Driver.query.filter_by(is_active=True).order_by(Driver.name.asc()).all()
    return jsonify({
        "success": True,
        "drivers": [
            {
                "id": d.id,
                "name": d.name,
                "employee_id": d.employee_id or "",
                "mobile_number": d.mobile_number or "",
                "designation": d.designation
            }
            for d in drivers
        ]
    })

@drivers_bp.route('/api/movements/<int:movement_id>/assign_driver', methods=['POST'])
@login_required
def api_assign_movement_driver(movement_id):
    """Assign/Change active trip driver for a gate movement in real-time."""
    mov = db.session.get(VehicleMovement, movement_id)
    if not mov:
        return jsonify({"success": False, "message": "Movement record not found."}), 404

    data = request.get_json(silent=True) or request.form
    driver_id = data.get('driver_id')
    driver_name = data.get('driver_name')

    if driver_id:
        drv = db.session.get(Driver, int(driver_id))
        if drv:
            mov.driver_id = drv.id
            mov.driver_name = drv.name
    elif driver_name:
        mov.driver_name = driver_name.strip()
        mov.driver_id = None

    db.session.commit()
    return jsonify({
        "success": True,
        "message": f"Trip Driver updated to '{mov.driver_name}'",
        "movement_id": mov.id,
        "driver_name": mov.driver_name
    })
