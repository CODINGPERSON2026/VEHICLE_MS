import os
from datetime import datetime
from database.db_init import db
from models.camera import CameraConfig, ANPREvent, ANPRVerificationStatus
from models.vehicle import Vehicle, normalize_plate
from models.rfid import RFIDCard
from models.settings import SystemSetting
from models.audit import AuditAction
from services.audit_service import log_audit

class ANPRService:
    @staticmethod
    def process_plate_detection(plate_text: str, confidence: float, camera_id: int = None, rfid_event_id: str = None, snapshot_filename: str = None, is_demo: bool = False):
        """
        Process a captured license plate from ANPR camera or test simulation.
        Cross-verifies against database and optional RFID event.
        """
        norm_plate = normalize_plate(plate_text)
        if not norm_plate:
            return {
                "success": False,
                "status": ANPRVerificationStatus.LOW_CONFIDENCE,
                "message": "Plate text is empty or unreadable.",
                "matched_vehicle": None
            }

        # Check confidence threshold
        threshold = float(SystemSetting.get_value('anpr_confidence_threshold', '80.0'))
        if confidence < threshold:
            verification_status = ANPRVerificationStatus.LOW_CONFIDENCE
            matched_vehicle = None
            msg = f"Low OCR confidence ({confidence:.1f}% < {threshold:.1f}%). Operator review required."
        else:
            # Look up vehicle
            matched_vehicle = Vehicle.query.filter_by(registration_number=norm_plate, is_active=True).first()
            
            if rfid_event_id:
                # Compare with RFID vehicle
                # Look up card or movement associated with rfid_event_id
                rfid_card = RFIDCard.query.filter_by(uid=rfid_event_id).first()
                if rfid_card and rfid_card.vehicle:
                    if rfid_card.vehicle.registration_number == norm_plate:
                        verification_status = ANPRVerificationStatus.MATCH
                        msg = f"ANPR plate '{norm_plate}' matches RFID tag vehicle."
                    else:
                        verification_status = ANPRVerificationStatus.MISMATCH
                        msg = f"MISMATCH: ANPR detected '{norm_plate}', but RFID card belongs to '{rfid_card.vehicle.registration_number}'."
                else:
                    verification_status = ANPRVerificationStatus.MATCH if matched_vehicle else ANPRVerificationStatus.MISMATCH
                    msg = f"Vehicle '{norm_plate}' found in system." if matched_vehicle else f"Vehicle '{norm_plate}' not in database."
            else:
                if matched_vehicle:
                    verification_status = ANPRVerificationStatus.MATCH
                    msg = f"Vehicle '{norm_plate}' identified in vehicle database."
                else:
                    verification_status = ANPRVerificationStatus.MISMATCH
                    msg = f"Vehicle '{norm_plate}' not found in registered database."

        # Record ANPR Event
        anpr_event = ANPREvent(
            timestamp=datetime.utcnow(),
            camera_id=camera_id,
            captured_plate=norm_plate,
            confidence=confidence,
            matched_vehicle_id=matched_vehicle.id if matched_vehicle else None,
            rfid_event_id=rfid_event_id,
            verification_status=verification_status,
            snapshot_path=snapshot_filename,
            is_demo=is_demo
        )
        db.session.add(anpr_event)
        db.session.commit()

        log_audit(
            action=AuditAction.CAMERA_CONFIG,
            description=f"ANPR Event: Plate '{norm_plate}' ({confidence:.1f}%) -> {verification_status}",
            related_vehicle=norm_plate
        )

        return {
            "success": True,
            "status": verification_status,
            "confidence": confidence,
            "captured_plate": norm_plate,
            "matched_vehicle": {
                "id": matched_vehicle.id,
                "registration_number": matched_vehicle.registration_number,
                "vehicle_type": matched_vehicle.vehicle_type,
                "auth_status": matched_vehicle.auth_status,
                "driver_name": matched_vehicle.driver_name
            } if matched_vehicle else None,
            "message": msg,
            "event_id": anpr_event.id
        }
