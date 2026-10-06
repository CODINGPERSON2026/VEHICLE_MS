import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify
from flask_login import login_required, current_user
from models.vehicle import Vehicle, VehicleType, AuthStatus, normalize_plate
from models.rfid import RFIDCard, CardStatus
from models.movement import VehicleMovement
from models.user import Role
from services.vehicle_service import VehicleService

vehicles_bp = Blueprint('vehicles', __name__)

@vehicles_bp.route('/vehicles')
@login_required
def list_vehicles():
    search = request.args.get('search', '').strip()
    vehicle_type = request.args.get('type', '').strip()
    status = request.args.get('status', '').strip()
    show_deactivated = request.args.get('show_deactivated') == '1'

    vehicles = VehicleService.get_all_vehicles(
        search=search,
        vehicle_type=vehicle_type,
        auth_status=status,
        active_only=not show_deactivated
    )

    return render_template(
        'vehicles.html',
        vehicles=vehicles,
        search=search,
        vehicle_type=vehicle_type,
        status=status,
        show_deactivated=show_deactivated,
        types=VehicleType.CHOICES,
        statuses=AuthStatus.CHOICES
    )

@vehicles_bp.route('/vehicles/new', methods=['GET', 'POST'])
@login_required
def create_vehicle():
    if current_user.role == Role.REPORT_VIEWER:
        flash('Permission denied. Report Viewers cannot create vehicles.', 'danger')
        return redirect(url_for('vehicles.list_vehicles'))

    form_data = None
    if request.method == 'POST':
        form_data = request.form
        success, msg, vehicle = VehicleService.create_vehicle(request.form, user=current_user)
        if success:
            flash(msg, 'success')
            return redirect(url_for('vehicles.view_vehicle', vehicle_id=vehicle.id))
        else:
            flash(msg, 'danger')

    # Fetch the first stored vehicle to auto-fill custodian details by default
    first_vehicle = Vehicle.query.order_by(Vehicle.id.asc()).first()

    return render_template(
        'vehicle_form.html',
        vehicle=None,
        first_vehicle=first_vehicle,
        form_data=form_data,
        types=VehicleType.CHOICES,
        statuses=AuthStatus.CHOICES,
        action_title="Register New Vehicle"
    )

@vehicles_bp.route('/vehicles/<int:vehicle_id>')
@login_required
def view_vehicle(vehicle_id):
    vehicle = VehicleService.get_by_id(vehicle_id)
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles.list_vehicles'))

    movements = vehicle.movements.order_by(VehicleMovement.entry_time.desc()).limit(20).all()
    cards = vehicle.rfid_cards

    return render_template(
        'vehicle_detail.html',
        vehicle=vehicle,
        cards=cards,
        movements=movements,
        card_statuses=CardStatus.CHOICES
    )

@vehicles_bp.route('/vehicles/<int:vehicle_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_vehicle(vehicle_id):
    if current_user.role == Role.REPORT_VIEWER:
        flash('Permission denied.', 'danger')
        return redirect(url_for('vehicles.list_vehicles'))

    vehicle = VehicleService.get_by_id(vehicle_id)
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles.list_vehicles'))

    if request.method == 'POST':
        success, msg = VehicleService.update_vehicle(vehicle_id, request.form, user=current_user)
        if success:
            flash(msg, 'success')
            return redirect(url_for('vehicles.view_vehicle', vehicle_id=vehicle.id))
        else:
            flash(msg, 'danger')

    return render_template(
        'vehicle_form.html',
        vehicle=vehicle,
        types=VehicleType.CHOICES,
        statuses=AuthStatus.CHOICES,
        action_title=f"Edit Vehicle - {vehicle.registration_number}"
    )

@vehicles_bp.route('/vehicles/<int:vehicle_id>/deactivate', methods=['POST'])
@login_required
def deactivate_vehicle(vehicle_id):
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can deactivate vehicles.', 'danger')
        return redirect(url_for('vehicles.view_vehicle', vehicle_id=vehicle_id))

    success, msg = VehicleService.deactivate_vehicle(vehicle_id, user=current_user)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('vehicles.list_vehicles'))

@vehicles_bp.route('/vehicles/<int:vehicle_id>/reactivate', methods=['POST'])
@login_required
def reactivate_vehicle(vehicle_id):
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can reactivate vehicles.', 'danger')
        return redirect(url_for('vehicles.view_vehicle', vehicle_id=vehicle_id))

    success, msg = VehicleService.reactivate_vehicle(vehicle_id, user=current_user)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('vehicles.view_vehicle', vehicle_id=vehicle_id))

@vehicles_bp.route('/vehicles/<int:vehicle_id>/delete', methods=['POST'])
@login_required
def delete_vehicle(vehicle_id):
    if current_user.role != Role.ADMIN:
        flash('Only Administrators can delete vehicles.', 'danger')
        return redirect(url_for('vehicles.list_vehicles'))

    success, msg = VehicleService.delete_vehicle(vehicle_id, user=current_user)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('vehicles.list_vehicles'))

@vehicles_bp.route('/vehicles/export/csv')
@login_required
def export_vehicles_csv():
    vehicles = VehicleService.get_all_vehicles(active_only=False)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['BA Number', 'Type', 'Date of Issue', 'Custodian Name', 'Army Number', 'Mobile', 'Auth Status', 'Active', 'Created At'])
    
    for v in vehicles:
        writer.writerow([
            v.registration_number,
            v.vehicle_type,
            v.issue_date.strftime('%Y-%m-%d') if v.issue_date else '',
            v.custodian_name or '',
            v.armynumber or '',
            v.mobile_number or '',
            v.auth_status,
            'Yes' if v.is_active else 'No',
            v.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=vehicle_master_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    return response
