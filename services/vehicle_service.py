from datetime import datetime, date
from database.db_init import db
from models.vehicle import Vehicle, AuthStatus, VehicleType, normalize_plate
from models.movement import VehicleMovement, MovementStatus
from models.audit import AuditAction
from services.audit_service import log_audit

class VehicleService:
    @staticmethod
    def get_all_vehicles(search=None, vehicle_type=None, auth_status=None, active_only=True, is_demo=None):
        """Query vehicles with filtering."""
        query = Vehicle.query
        
        if active_only:
            query = query.filter_by(is_active=True)
            
        if is_demo is not None:
            query = query.filter_by(is_demo=is_demo)
            
        if search:
            s = f"%{search.strip()}%"
            norm_s = normalize_plate(search)
            query = query.filter(
                (Vehicle.registration_number.ilike(f"%{norm_s}%") if norm_s else False) |
                Vehicle.custodian_name.ilike(s) |
                Vehicle.armynumber.ilike(s) |
                Vehicle.mobile_number.ilike(s)
            )
            
        if vehicle_type and vehicle_type in VehicleType.CHOICES:
            query = query.filter_by(vehicle_type=vehicle_type)
            
        if auth_status and auth_status in AuthStatus.CHOICES:
            query = query.filter_by(auth_status=auth_status)
            
        return query.order_by(Vehicle.created_at.desc()).all()

    @staticmethod
    def get_by_id(vehicle_id):
        return db.session.get(Vehicle, vehicle_id)

    @staticmethod
    def get_by_plate(plate_number):
        normalized = normalize_plate(plate_number)
        if not normalized:
            return None
        return Vehicle.query.filter_by(registration_number=normalized).first()

    @staticmethod
    def create_vehicle(data, user=None, is_demo=False):
        """Create a new vehicle record."""
        norm_plate = normalize_plate(data.get('registration_number', ''))
        if not norm_plate:
            return False, "Registration number cannot be empty.", None
            
        existing = Vehicle.query.filter_by(registration_number=norm_plate).first()
        if existing:
            if not existing.is_active:
                return False, f"Vehicle '{norm_plate}' exists but is deactivated. Reactivate it from the vehicle list.", None
            return False, f"Vehicle '{norm_plate}' is already registered.", None

        # Parse issue date
        issue_date = data.get('issue_date')
        if isinstance(issue_date, str) and issue_date:
            try:
                issue_date = datetime.strptime(issue_date, '%Y-%m-%d').date()
            except ValueError:
                issue_date = None
        elif not isinstance(issue_date, date):
            issue_date = None

        custodian_name = (data.get('custodian_name') or data.get('driver_name') or '').strip()
        armynumber = (data.get('armynumber') or data.get('army_number') or data.get('driver_id') or '').strip()

        vehicle = Vehicle(
            registration_number=norm_plate,
            vehicle_type=data.get('vehicle_type', VehicleType.GYPSY),
            issue_date=issue_date,
            custodian_name=custodian_name,
            armynumber=armynumber,
            mobile_number=data.get('mobile_number', '').strip(),
            auth_status=data.get('auth_status', AuthStatus.AUTHORIZED),
            current_vehicle_location='INSIDE',
            is_active=True,
            is_demo=is_demo
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        log_audit(
            action=AuditAction.VEHICLE_CREATE,
            description=f"Created vehicle '{norm_plate}' ({vehicle.vehicle_type}, Status: {vehicle.auth_status})",
            related_vehicle=norm_plate,
            user=user
        )
        return True, "Vehicle registered successfully.", vehicle

    @staticmethod
    def update_vehicle(vehicle_id, data, user=None):
        """Update vehicle details."""
        vehicle = db.session.get(Vehicle, vehicle_id)
        if not vehicle:
            return False, "Vehicle not found."

        norm_plate = normalize_plate(data.get('registration_number', ''))
        if norm_plate and norm_plate != vehicle.registration_number:
            existing = Vehicle.query.filter_by(registration_number=norm_plate).first()
            if existing and existing.id != vehicle.id:
                return False, f"Registration number '{norm_plate}' is already used by another vehicle."
            vehicle.registration_number = norm_plate

        vehicle.vehicle_type = data.get('vehicle_type', vehicle.vehicle_type)
        
        if 'issue_date' in data:
            id_val = data['issue_date']
            if isinstance(id_val, str):
                vehicle.issue_date = datetime.strptime(id_val, '%Y-%m-%d').date() if id_val else None
            elif isinstance(id_val, date):
                vehicle.issue_date = id_val

        if 'custodian_name' in data or 'driver_name' in data:
            c_name = data.get('custodian_name', data.get('driver_name'))
            if c_name is not None:
                vehicle.custodian_name = c_name.strip()

        if 'armynumber' in data or 'army_number' in data or 'driver_id' in data:
            a_num = data.get('armynumber', data.get('army_number', data.get('driver_id')))
            if a_num is not None:
                vehicle.armynumber = a_num.strip()

        vehicle.mobile_number = data.get('mobile_number', vehicle.mobile_number).strip() if data.get('mobile_number') is not None else vehicle.mobile_number
        vehicle.auth_status = data.get('auth_status', vehicle.auth_status)

        db.session.commit()
        
        log_audit(
            action=AuditAction.VEHICLE_UPDATE,
            description=f"Updated vehicle '{vehicle.registration_number}' details (Status: {vehicle.auth_status})",
            related_vehicle=vehicle.registration_number,
            user=user
        )
        return True, "Vehicle details updated successfully."

    @staticmethod
    def deactivate_vehicle(vehicle_id, user=None):
        """Soft-deactivate a vehicle to protect movement history."""
        vehicle = db.session.get(Vehicle, vehicle_id)
        if not vehicle:
            return False, "Vehicle not found."
            
        vehicle.is_active = False
        db.session.commit()
        
        log_audit(
            action=AuditAction.VEHICLE_DEACTIVATE,
            description=f"Deactivated vehicle '{vehicle.registration_number}'",
            related_vehicle=vehicle.registration_number,
            user=user
        )
        return True, "Vehicle deactivated successfully."

    @staticmethod
    def reactivate_vehicle(vehicle_id, user=None):
        """Reactivate a soft-deactivated vehicle."""
        vehicle = db.session.get(Vehicle, vehicle_id)
        if not vehicle:
            return False, "Vehicle not found."
            
        vehicle.is_active = True
        db.session.commit()
        
        log_audit(
            action=AuditAction.VEHICLE_REACTIVATE,
            description=f"Reactivated vehicle '{vehicle.registration_number}'",
            related_vehicle=vehicle.registration_number,
            user=user
        )
        return True, "Vehicle reactivated successfully."

    @staticmethod
    def delete_vehicle(vehicle_id, user=None):
        """Permanently delete a vehicle record, clean related records, and unassign any linked cards."""
        vehicle = db.session.get(Vehicle, vehicle_id)
        if not vehicle:
            return False, "Vehicle not found."

        reg_no = vehicle.registration_number

        # 1. Unassign linked RFID cards so physical cards are preserved for reuse
        for card in list(vehicle.rfid_cards):
            card.vehicle_id = None

        # 2. Clean up foreign keys and related tables
        from models.movement import VehicleMovement
        from models.denied_attempt import DeniedAttempt
        from models.camera import ANPREvent

        # Delete historical movements and denied attempts for this vehicle
        VehicleMovement.query.filter_by(vehicle_id=vehicle.id).delete()
        DeniedAttempt.query.filter((DeniedAttempt.vehicle_id == vehicle.id) | (DeniedAttempt.vehicle_number == reg_no)).delete()
        ANPREvent.query.filter_by(matched_vehicle_id=vehicle.id).update({ANPREvent.matched_vehicle_id: None})

        db.session.delete(vehicle)
        db.session.commit()

        log_audit(
            action=AuditAction.VEHICLE_DEACTIVATE,
            description=f"Permanently deleted vehicle '{reg_no}'",
            related_vehicle=reg_no,
            user=user
        )
        return True, f"Vehicle '{reg_no}' deleted successfully."
