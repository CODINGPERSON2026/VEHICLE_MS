from datetime import datetime
from database.db_init import db
from models.driver import Driver
from models.audit import AuditAction
from services.audit_service import log_audit

DEFAULT_SAMPLE_DRIVERS = [
    {"name": "Rajesh Sharma", "employee_id": "DRV-001", "mobile_number": "9820123456", "designation": "Senior Driver"},
    {"name": "Sunil Verma", "employee_id": "DRV-002", "mobile_number": "9820234567", "designation": "Staff Driver"},
    {"name": "Ramesh Patil", "employee_id": "DRV-003", "mobile_number": "9820345678", "designation": "Staff Driver"},
    {"name": "Arsh Mulla", "employee_id": "DRV-004", "mobile_number": "9820456789", "designation": "Executive Chauffeur"},
    {"name": "Vikram Singh", "employee_id": "DRV-005", "mobile_number": "9820567890", "designation": "Heavy Vehicle Driver"},
    {"name": "Amit Deshmukh", "employee_id": "DRV-006", "mobile_number": "9820678901", "designation": "Staff Driver"},
    {"name": "Pradeep Kumar", "employee_id": "DRV-007", "mobile_number": "9820789012", "designation": "Pool Driver"},
    {"name": "Sanjay Yadav", "employee_id": "DRV-008", "mobile_number": "9820890123", "designation": "Pool Driver"},
    {"name": "Manoj Shinde", "employee_id": "DRV-009", "mobile_number": "9820901234", "designation": "Contractor Driver"},
    {"name": "Ganesh Kadam", "employee_id": "DRV-010", "mobile_number": "9821012345", "designation": "Staff Driver"},
    {"name": "Dinesh Pawar", "employee_id": "DRV-011", "mobile_number": "9821123456", "designation": "Staff Driver"},
    {"name": "Suresh More", "employee_id": "DRV-012", "mobile_number": "9821234567", "designation": "Pool Driver"},
    {"name": "Kiran Sawant", "employee_id": "DRV-013", "mobile_number": "9821345678", "designation": "Valet Driver"},
    {"name": "Mahesh Gaikwad", "employee_id": "DRV-014", "mobile_number": "9821456789", "designation": "Staff Driver"},
    {"name": "Vijay Jadhav", "employee_id": "DRV-015", "mobile_number": "9821567890", "designation": "Heavy Vehicle Driver"},
    {"name": "Rahul Bhosle", "employee_id": "DRV-016", "mobile_number": "9821678901", "designation": "Pool Driver"},
    {"name": "Sachin Chavan", "employee_id": "DRV-017", "mobile_number": "9821789012", "designation": "Contractor Driver"},
    {"name": "Pravin Salunkhe", "employee_id": "DRV-018", "mobile_number": "9821890123", "designation": "Executive Chauffeur"},
    {"name": "Nitin Kamble", "employee_id": "DRV-019", "mobile_number": "9821901234", "designation": "Staff Driver"},
    {"name": "Anil Mane", "employee_id": "DRV-020", "mobile_number": "9822012345", "designation": "Emergency / Ambulance"}
]

class DriverService:
    @staticmethod
    def get_all_drivers(search=None, active_only=False):
        """Query drivers with search and active filtering."""
        query = Driver.query
        if active_only:
            query = query.filter_by(is_active=True)
            
        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                Driver.name.ilike(s) |
                Driver.armynumber.ilike(s) |
                Driver.driver_rank.ilike(s) |
                Driver.company.ilike(s) |
                Driver.section.ilike(s) |
                Driver.mobile_number.ilike(s) |
                Driver.license_number.ilike(s) |
                Driver.designation.ilike(s)
            )
            
        return query.order_by(Driver.name.asc()).all()

    @staticmethod
    def get_by_id(driver_id):
        return db.session.get(Driver, driver_id)

    @staticmethod
    def create_driver(data, user=None):
        name = data.get('name', '').strip()
        if not name:
            return False, "Driver name is required.", None
            
        armynumber = (data.get('armynumber') or data.get('army_number') or '').strip() or None
        driver_rank = (data.get('driver_rank') or data.get('driverank') or '').strip() or None
        company = data.get('company', '').strip() or None
        section = data.get('section', '').strip() or None

        hill_driving = 'YES' if data.get('hill_driving', '').upper() in ('YES', '1', 'TRUE') else 'NO'
        if hill_driving == 'YES':
            auth_status = 'AUTHORIZED'
            if hasattr(data, 'getlist'):
                v_types = data.getlist('authorized_vehicle_types')
            else:
                v_types = data.get('authorized_vehicle_types', [])
                if isinstance(v_types, str):
                    v_types = [v_types]
            authorized_vehicle_types = ', '.join([vt.strip() for vt in v_types if vt.strip()]) if v_types else None
        else:
            auth_status = 'NOT AUTHORIZED'
            authorized_vehicle_types = None

        driver = Driver(
            name=name,
            armynumber=armynumber,
            driver_rank=driver_rank,
            company=company,
            section=section,
            hill_driving=hill_driving,
            auth_status=auth_status,
            authorized_vehicle_types=authorized_vehicle_types,
            license_number=data.get('license_number', '').strip() or None,
            mobile_number=data.get('mobile_number', '').strip() or None,
            designation=data.get('designation', driver_rank or 'Staff Driver').strip(),
            remarks=data.get('remarks', '').strip() or None,
            is_active=True
        )
        db.session.add(driver)
        db.session.commit()

        log_audit(
            action=AuditAction.DRIVER_CREATE,
            description=f"Created Driver profile: '{driver.name}' ({driver.armynumber or 'No Army No'}, Hill Driving: {driver.hill_driving}, Status: {driver.auth_status})",
            user=user
        )
        return True, f"Driver '{driver.name}' registered successfully.", driver

    @staticmethod
    def update_driver(driver_id, data, user=None):
        driver = db.session.get(Driver, driver_id)
        if not driver:
            return False, "Driver not found."

        name = data.get('name', '').strip()
        if not name:
            return False, "Driver name cannot be empty."

        driver.name = name
        if 'armynumber' in data or 'army_number' in data:
            driver.armynumber = (data.get('armynumber') or data.get('army_number') or '').strip() or None
        if 'driver_rank' in data or 'driverank' in data:
            driver.driver_rank = (data.get('driver_rank') or data.get('driverank') or '').strip() or None
        if 'company' in data:
            driver.company = data.get('company', '').strip() or None
        if 'section' in data:
            driver.section = data.get('section', '').strip() or None

        if 'hill_driving' in data:
            hill_driving = 'YES' if data.get('hill_driving', '').upper() in ('YES', '1', 'TRUE') else 'NO'
            driver.hill_driving = hill_driving
            if hill_driving == 'YES':
                driver.auth_status = 'AUTHORIZED'
                if hasattr(data, 'getlist'):
                    v_types = data.getlist('authorized_vehicle_types')
                else:
                    v_types = data.get('authorized_vehicle_types', [])
                    if isinstance(v_types, str):
                        v_types = [v_types]
                driver.authorized_vehicle_types = ', '.join([vt.strip() for vt in v_types if vt.strip()]) if v_types else None
            else:
                driver.auth_status = 'NOT AUTHORIZED'
                driver.authorized_vehicle_types = None

        driver.license_number = data.get('license_number', '').strip() or None
        driver.mobile_number = data.get('mobile_number', '').strip() or None
        if 'designation' in data:
            driver.designation = data.get('designation', driver.designation).strip()
        driver.remarks = data.get('remarks', '').strip() or None
        
        if 'is_active' in data:
            driver.is_active = bool(data['is_active'])

        db.session.commit()

        log_audit(
            action=AuditAction.DRIVER_UPDATE,
            description=f"Updated Driver profile: '{driver.name}' ({driver.armynumber or 'No Army No'}, Status: {driver.auth_status})",
            user=user
        )
        return True, f"Driver '{driver.name}' updated successfully."

    @staticmethod
    def delete_driver(driver_id, user=None):
        driver = db.session.get(Driver, driver_id)
        if not driver:
            return False, "Driver not found."

        name = driver.name
        # Unlink from historical movements so logs stay intact
        from models.movement import VehicleMovement
        VehicleMovement.query.filter_by(driver_id=driver.id).update({VehicleMovement.driver_id: None})

        db.session.delete(driver)
        db.session.commit()

        log_audit(
            action=AuditAction.DRIVER_DELETE,
            description=f"Deleted Driver profile: '{name}'",
            user=user
        )
        return True, f"Driver '{name}' deleted successfully."

    @staticmethod
    def seed_default_drivers():
        """Ensure 20 default sample drivers exist in database."""
        if Driver.query.count() == 0:
            for item in DEFAULT_SAMPLE_DRIVERS:
                drv = Driver(
                    name=item["name"],
                    employee_id=item["employee_id"],
                    mobile_number=item["mobile_number"],
                    designation=item["designation"],
                    is_active=True
                )
                db.session.add(drv)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
