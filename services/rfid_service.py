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
    def get_all_cards(search=None, status=None, is_demo=None):
        """Query RFID cards with search by UID or vehicle."""
        query = RFIDCard.query.join(Vehicle, RFIDCard.vehicle_id == Vehicle.id, isouter=True)
        
        if is_demo is not None:
            query = query.filter(RFIDCard.is_demo == is_demo)
            
        if search:
            s = f"%{search.strip()}%"
            norm_uid = normalize_uid(search)
            query = query.filter(
                (RFIDCard.uid.ilike(f"%{norm_uid}%") if norm_uid else False) |
                RFIDCard.remarks.ilike(s) |
                Vehicle.registration_number.ilike(s) |
                Vehicle.driver_name.ilike(s)
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
    def assign_card(uid: str, vehicle_id: int, expiry_date=None, remarks: str = None, user=None, is_demo=False):
        """Assign an RFID card to a vehicle."""
        norm_uid = normalize_uid(uid)
        if not norm_uid:
            return False, "RFID UID cannot be empty.", None

        vehicle = db.session.get(Vehicle, vehicle_id) if vehicle_id else None
        if vehicle_id and not vehicle:
            return False, "Selected vehicle not found.", None

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
            if card.vehicle_id and card.vehicle_id != vehicle_id and card.card_status == CardStatus.ACTIVE:
                return False, f"RFID Card '{norm_uid}' is already assigned to active Vehicle '{card.vehicle.registration_number}'. Reassign or deactivate it first.", None
            # Reassignment / Update
            old_veh_id = card.vehicle_id
            card.vehicle_id = vehicle_id
            card.card_status = CardStatus.ACTIVE
            card.assigned_date = date.today()
            card.expiry_date = exp
            if remarks:
                card.remarks = remarks.strip()
            db.session.commit()
            
            log_audit(
                action=AuditAction.RFID_ASSIGN if not old_veh_id else AuditAction.RFID_REASSIGN,
                description=f"Assigned RFID '{norm_uid}' to vehicle '{vehicle.registration_number if vehicle else 'Unassigned'}'",
                related_vehicle=vehicle.registration_number if vehicle else None,
                user=user
            )
            return True, f"Card '{norm_uid}' assigned successfully.", card

        new_card = RFIDCard(
            uid=norm_uid,
            vehicle_id=vehicle_id,
            card_status=CardStatus.ACTIVE,
            assigned_date=date.today(),
            expiry_date=exp,
            remarks=remarks.strip() if remarks else None,
            is_demo=is_demo
        )
        db.session.add(new_card)
        db.session.commit()

        log_audit(
            action=AuditAction.RFID_ASSIGN,
            description=f"Registered & assigned RFID '{norm_uid}' to vehicle '{vehicle.registration_number if vehicle else 'Unassigned'}'",
            related_vehicle=vehicle.registration_number if vehicle else None,
            user=user
        )
        return True, f"Card '{norm_uid}' registered and assigned successfully.", new_card

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
        """Unassign an RFID card from its vehicle (removes link)."""
        card = db.session.get(RFIDCard, card_id)
        if not card:
            return False, "Card not found."
            
        old_vehicle_num = card.vehicle.registration_number if card.vehicle else "None"
        card.vehicle_id = None
        db.session.commit()

        log_audit(
            action=AuditAction.RFID_DEACTIVATE,
            description=f"Unassigned RFID '{card.uid}' from vehicle '{old_vehicle_num}'",
            related_vehicle=old_vehicle_num,
            user=user
        )
        return True, f"RFID Card '{card.uid}' unassigned from vehicle successfully."

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
