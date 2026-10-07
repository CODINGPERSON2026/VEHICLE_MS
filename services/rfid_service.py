import uuid
from datetime import datetime, date, timedelta
from database.db_init import db
from models.rfid import RFIDCard, CardStatus, normalize_uid
from models.vehicle import Vehicle
from models.audit import AuditAction
from services.audit_service import log_audit

# In-memory enrollment buffer: { 'uid': str, 'timestamp': datetime, 'device_id': str }
_enrollment_buffer = {
    'uid': None,
    'timestamp': None,
    'device_id': None
}

# In-memory pending scan buffer awaiting guard confirmation
_pending_scan_buffer = {
    'uid': None,
    'timestamp': None,
    'device_id': None,
    'scan_id': None,
    'data': None
}

class RFIDService:
    @staticmethod
    def capture_enrollment_scan(raw_uid: str, device_id: str = None):
        """Save a scanned UID into the temporary enrollment buffer."""
        norm_uid = normalize_uid(raw_uid)
        if not norm_uid:
            return False, "Invalid UID"
            
        global _enrollment_buffer
        _enrollment_buffer = {
            'uid': norm_uid,
            'timestamp': datetime.utcnow(),
            'device_id': device_id or 'UNKNOWN'
        }
        return True, "UID captured for enrollment."

    @staticmethod
    def get_latest_enrollment(timeout_seconds=60):
        """Retrieve latest scanned UID if scanned within timeout."""
        global _enrollment_buffer
        if _enrollment_buffer['uid'] and _enrollment_buffer['timestamp']:
            age = (datetime.utcnow() - _enrollment_buffer['timestamp']).total_seconds()
            if age <= timeout_seconds:
                return {
                    'uid': _enrollment_buffer['uid'],
                    'device_id': _enrollment_buffer['device_id'],
                    'age_seconds': int(age)
                }
        return None

    @staticmethod
    def clear_enrollment():
        """Clear enrollment buffer."""
        global _enrollment_buffer
        _enrollment_buffer = {'uid': None, 'timestamp': None, 'device_id': None}

    @staticmethod
    def lookup_card_and_vehicle(raw_uid: str):
        """Lookup full vehicle and driver telemetry for RFID card confirmation."""
        norm_uid = normalize_uid(raw_uid)
        if not norm_uid:
            return {"success": False, "reason": "INVALID_UID", "message": "Invalid or empty RFID UID."}

        card = RFIDCard.query.filter_by(uid=norm_uid).first()
        if not card:
            return {"success": False, "reason": "UNKNOWN_RFID", "message": f"RFID tag '{norm_uid}' is not registered in the system."}

        is_valid, card_err = card.is_valid()
        if not is_valid:
            return {"success": False, "reason": card_err, "message": f"RFID card is {card.card_status}."}

        vehicle = card.vehicle
        from models.driver import Driver
        from models.movement import VehicleMovement, MovementStatus

        if not vehicle and card.driver:
            # Check if this driver currently has an active trip outside
            active_out = VehicleMovement.query.filter_by(
                driver_id=card.driver.id,
                status=MovementStatus.OUTSIDE
            ).order_by(VehicleMovement.exit_time.desc()).first()
            if active_out and active_out.vehicle:
                vehicle = active_out.vehicle
            else:
                # Look for vehicle associated with driver
                vehicle = Vehicle.query.filter(
                    Vehicle.is_active == True,
                    (Vehicle.armynumber == card.driver.armynumber if card.driver.armynumber else False) |
                    (Vehicle.driver_name == card.driver.name)
                ).first()
                if not vehicle:
                    # Fallback to any active vehicle
                    vehicle = Vehicle.query.filter_by(is_active=True).first()

        if not vehicle or not vehicle.is_active:
            return {"success": False, "reason": "UNASSIGNED_CARD", "message": "Card is not assigned to an active vehicle or driver."}

        # Check active movement status
        active_outside = vehicle.get_active_outside_movement()
        is_outside = active_outside is not None
        current_status = "OUTSIDE" if is_outside else "INSIDE"
        allowed_direction = "ENTRY" if is_outside else "EXIT"
        forbidden_direction = "EXIT" if is_outside else "ENTRY"
        recommended_direction = allowed_direction

        # Determine driver details (Custodian is NOT driver)
        assigned_driver_name = active_outside.driver_name if active_outside and active_outside.driver_name else (
            card.driver.name if card.driver else "Unassigned Driver"
        )
        
        drv_record = card.driver or Driver.query.filter(
            (Driver.name == assigned_driver_name) | 
            (Driver.armynumber == vehicle.armynumber if vehicle.armynumber else False)
        ).first()

        driver_info = {
            "name": assigned_driver_name,
            "armynumber": drv_record.armynumber if drv_record and drv_record.armynumber else (vehicle.armynumber or "N/A"),
            "rank": drv_record.driver_rank if drv_record and drv_record.driver_rank else (drv_record.designation if drv_record else "Driver"),
            "designation": drv_record.designation if drv_record else "Vehicle Operator",
            "mobile": drv_record.mobile_number if drv_record and drv_record.mobile_number else (vehicle.mobile_number or "N/A"),
            "id": drv_record.id if drv_record else None
        }

        active_trip_info = None
        if active_outside:
            active_trip_info = {
                "exit_time": active_outside.exit_time.strftime('%H:%M:%S') if active_outside.exit_time else "N/A",
                "duration": active_outside.formatted_duration,
                "driver_name": active_outside.driver_name
            }

        pool_drivers = []
        all_drivers = Driver.query.filter_by(is_active=True).order_by(Driver.name.asc()).all()
        for d in all_drivers:
            pool_drivers.append({
                "id": d.id,
                "name": d.name,
                "armynumber": d.armynumber or "",
                "rank": d.driver_rank or d.designation or "",
                "mobile": d.mobile_number or ""
            })

        return {
            "success": True,
            "uid": norm_uid,
            "vehicle": {
                "id": vehicle.id,
                "registration_number": vehicle.registration_number,
                "vehicle_type": vehicle.vehicle_type,
                "auth_status": vehicle.auth_status,
                "custodian_name": vehicle.custodian_name or "N/A",
                "armynumber": vehicle.armynumber or "N/A",
                "mobile_number": vehicle.mobile_number or "N/A"
            },
            "driver": driver_info,
            "current_status": current_status,
            "is_inside": not is_outside,
            "is_outside": is_outside,
            "allowed_direction": allowed_direction,
            "forbidden_direction": forbidden_direction,
            "recommended_direction": recommended_direction,
            "active_trip": active_trip_info,
            "pool_drivers": pool_drivers
        }

    @staticmethod
    def stage_pending_scan(raw_uid: str, device_id: str = None):
        """Look up vehicle and stage as pending scan for operator confirmation."""
        lookup = RFIDService.lookup_card_and_vehicle(raw_uid)
        if not lookup.get('success'):
            return lookup
        global _pending_scan_buffer
        scan_id = str(uuid.uuid4())[:8]
        lookup['scan_id'] = scan_id
        lookup['device_id'] = device_id or 'GATE01'
        lookup['scanned_at'] = datetime.utcnow().strftime('%H:%M:%S')
        _pending_scan_buffer = {
            'uid': lookup['uid'],
            'timestamp': datetime.utcnow(),
            'device_id': device_id or 'GATE01',
            'scan_id': scan_id,
            'data': lookup
        }
        return lookup

    @staticmethod
    def get_pending_scan(timeout_seconds=60):
        """Retrieve active pending scan waiting for confirmation."""
        global _pending_scan_buffer
        if _pending_scan_buffer.get('uid') and _pending_scan_buffer.get('timestamp'):
            age = (datetime.utcnow() - _pending_scan_buffer['timestamp']).total_seconds()
            if age <= timeout_seconds:
                return _pending_scan_buffer['data']
            else:
                RFIDService.clear_pending_scan()
        return None

    @staticmethod
    def clear_pending_scan():
        """Clear active pending scan."""
        global _pending_scan_buffer
        _pending_scan_buffer = {
            'uid': None,
            'timestamp': None,
            'device_id': None,
            'scan_id': None,
            'data': None
        }

    @staticmethod
    def get_all_cards(search=None, status=None, is_demo=None):
        """Query RFID cards with search by UID, vehicle, or driver."""
        from models.driver import Driver
        query = RFIDCard.query.join(Vehicle, RFIDCard.vehicle_id == Vehicle.id, isouter=True)\
                              .join(Driver, RFIDCard.driver_id == Driver.id, isouter=True)
        
        if is_demo is not None:
            query = query.filter(RFIDCard.is_demo == is_demo)
            
        if search:
            s = f"%{search.strip()}%"
            norm_uid = normalize_uid(search)
            query = query.filter(
                (RFIDCard.uid.ilike(f"%{norm_uid}%") if norm_uid else False) |
                RFIDCard.remarks.ilike(s) |
                Vehicle.registration_number.ilike(s) |
                Vehicle.custodian_name.ilike(s) |
                Driver.name.ilike(s) |
                Driver.armynumber.ilike(s)
            )
            
        if status and status in CardStatus.CHOICES:
            query = query.filter(RFIDCard.card_status == status)
            
        return query.order_by(RFIDCard.created_at.desc()).all()

    @staticmethod
    def get_by_uid(uid: str):
        norm_uid = normalize_uid(uid)
        if not norm_uid:
            return None
        return RFIDCard.query.filter_by(uid=norm_uid).first()

    @staticmethod
    def assign_card(uid: str, vehicle_id: int = None, driver_id: int = None, expiry_date=None, remarks: str = None, user=None, is_demo=False):
        """Assign an RFID card to a driver and/or vehicle."""
        from models.driver import Driver
        norm_uid = normalize_uid(uid)
        if not norm_uid:
            return False, "RFID UID cannot be empty.", None

        if not vehicle_id and not driver_id:
            return False, "Please select either a Driver or a Vehicle to assign this RFID card.", None

        vehicle = db.session.get(Vehicle, vehicle_id) if vehicle_id else None
        driver = db.session.get(Driver, driver_id) if driver_id else None

        # Parse expiry date to datetime.date
        exp = None
        if isinstance(expiry_date, str) and expiry_date.strip():
            try:
                exp = datetime.strptime(expiry_date.strip(), '%Y-%m-%d').date()
            except ValueError:
                exp = None
        elif isinstance(expiry_date, (date, datetime)):
            exp = expiry_date if isinstance(expiry_date, date) and not isinstance(expiry_date, datetime) else expiry_date.date()

        # Check existing card
        card = RFIDCard.query.filter_by(uid=norm_uid).first()
        if card:
            # Clear previous driver link if driver is changed
            if card.driver and card.driver.id != driver_id:
                card.driver.rfid_uid = None

            card.vehicle_id = vehicle_id
            card.driver_id = driver_id
            card.card_status = CardStatus.ACTIVE
            card.assigned_date = date.today()
            card.expiry_date = exp
            if remarks:
                card.remarks = remarks.strip()
            
            if driver:
                driver.rfid_uid = norm_uid

            db.session.commit()
            
            target_parts = []
            if driver:
                target_parts.append(f"driver '{driver.name}'")
            if vehicle:
                target_parts.append(f"vehicle '{vehicle.registration_number}'")
            target_desc = " and ".join(target_parts)

            log_audit(
                action=AuditAction.RFID_ASSIGN,
                description=f"Assigned RFID '{norm_uid}' to {target_desc}",
                related_vehicle=vehicle.registration_number if vehicle else None,
                user=user
            )
            return True, f"Card '{norm_uid}' assigned to {target_desc} successfully.", card

        new_card = RFIDCard(
            uid=norm_uid,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            card_status=CardStatus.ACTIVE,
            assigned_date=date.today(),
            expiry_date=exp,
            remarks=remarks.strip() if remarks else None,
            is_demo=is_demo
        )
        if driver:
            driver.rfid_uid = norm_uid

        db.session.add(new_card)
        db.session.commit()

        target_parts = []
        if driver:
            target_parts.append(f"driver '{driver.name}'")
        if vehicle:
            target_parts.append(f"vehicle '{vehicle.registration_number}'")
        target_desc = " and ".join(target_parts)

        log_audit(
            action=AuditAction.RFID_ASSIGN,
            description=f"Registered & assigned RFID '{norm_uid}' to {target_desc}",
            related_vehicle=vehicle.registration_number if vehicle else None,
            user=user
        )
        return True, f"Card '{norm_uid}' registered and assigned to {target_desc} successfully.", new_card

    @staticmethod
    def update_card_status(card_id: int, new_status: str, remarks: str = None, user=None):
        """Update status of a card (e.g., ACTIVE, INACTIVE, LOST, BLOCKED, EXPIRED)."""
        card = db.session.get(RFIDCard, card_id)
        if not card:
            return False, "Card not found."
            
        if new_status not in CardStatus.CHOICES:
            return False, f"Invalid status: {new_status}"

        old_status = card.card_status
        card.card_status = new_status
        if remarks:
            card.remarks = remarks
        db.session.commit()

        action = AuditAction.RFID_BLOCK if new_status == CardStatus.BLOCKED else AuditAction.RFID_STATUS_CHANGE
        log_audit(
            action=action,
            description=f"Changed RFID '{card.uid}' status from {old_status} to {new_status}",
            related_vehicle=card.vehicle.registration_number if card.vehicle else None,
            user=user
        )
        return True, f"Card status changed to {new_status}."

    @staticmethod
    def unassign_card(card_id: int, user=None):
        """Unassign an RFID card from its vehicle and/or driver (removes links)."""
        card = db.session.get(RFIDCard, card_id)
        if not card:
            return False, "Card not found."
            
        old_parts = []
        if card.vehicle:
            old_parts.append(f"vehicle '{card.vehicle.registration_number}'")
        if card.driver:
            old_parts.append(f"driver '{card.driver.name}'")
            card.driver.rfid_uid = None

        card.vehicle_id = None
        card.driver_id = None
        db.session.commit()

        target_desc = " and ".join(old_parts) or "assigned entity"
        log_audit(
            action=AuditAction.RFID_DEACTIVATE,
            description=f"Unassigned RFID '{card.uid}' from {target_desc}",
            user=user
        )
        return True, f"RFID Card '{card.uid}' unassigned successfully."

    @staticmethod
    def delete_card(card_id: int, user=None):
        """Delete an RFID card record and unlink it from historical movement logs."""
        card = db.session.get(RFIDCard, card_id)
        if not card:
            return False, "Card not found."
            
        uid = card.uid
        old_veh = card.vehicle.registration_number if card.vehicle else None

        # Unlink card ID from movements so movements remain intact
        from models.movement import VehicleMovement
        VehicleMovement.query.filter_by(rfid_card_id=card.id).update({VehicleMovement.rfid_card_id: None})

        db.session.delete(card)
        db.session.commit()

        log_audit(
            action=AuditAction.RFID_DEACTIVATE,
            description=f"Deleted RFID Card '{uid}'",
            related_vehicle=old_veh,
            user=user
        )
        return True, f"RFID Card '{uid}' deleted successfully."
