import json
from datetime import datetime, date, timedelta
from database.db_init import db
from models.vehicle import Vehicle, AuthStatus, normalize_plate
from models.rfid import RFIDCard, CardStatus, normalize_uid
from models.device import Device, DeviceEvent, DeviceStatus
from models.movement import VehicleMovement, MovementStatus, GateDirection
from models.denied_attempt import DeniedAttempt, DeniedReason
from models.settings import SystemSetting
from models.audit import AuditAction
from services.audit_service import log_audit

class MovementService:
    @staticmethod
    def process_rfid_scan(device_id: str, api_key: str, uid: str, direction: str = None, event_id: str = None, is_demo: bool = False):
        """
        Core gate movement processing engine for incoming RFID scans.
        Server is the ultimate authority on gate access decisions.
        """
        # 1. Device Authentication & Validation
        device = Device.query.filter_by(device_id=device_id).first() if device_id else None
        if not device or not device.is_active:
            # Log denied attempt for invalid device
            DeniedAttempt_record = DeniedAttempt(
                rfid_uid=normalize_uid(uid),
                direction=direction or 'ENTRY',
                reason=DeniedReason.INVALID_DEVICE,
                event_id=event_id,
                remarks=f"Invalid or disabled device: '{device_id}'",
                is_demo=is_demo
            )
            db.session.add(DeniedAttempt_record)
            db.session.commit()
            # Buffer unregistered UID for Live Enrollment Mode
            norm_uid = normalize_uid(uid)
            if norm_uid:
                try:
                    from services.rfid_service import RFIDService
                    card = RFIDCard.query.filter_by(uid=norm_uid).first()
                    if not card:
                        RFIDService.capture_enrollment_scan(norm_uid, device_id)
                except Exception:
                    pass

            return {
                "success": False,
                "decision": "ENTRY_DENIED",
                "reason": "INVALID_DEVICE",
                "message": "Device not registered or disabled."
            }, 401

        if not device.check_api_key(api_key):
            return {
                "success": False,
                "decision": "ENTRY_DENIED",
                "reason": "INVALID_API_KEY",
                "message": "Device API key authentication failed."
            }, 403

        # Update Device Heartbeat
        device.update_heartbeat()

        # 2. Idempotency Check
        if event_id:
            existing_event = DeviceEvent.query.filter_by(device_id=device.id, event_id=event_id).first()
            if existing_event and existing_event.response_summary:
                try:
                    cached_resp = json.loads(existing_event.raw_payload or '{}')
                    if cached_resp:
                        return cached_resp, 200
                except Exception:
                    pass

        # 3. UID Normalization & Lookup
        norm_uid = normalize_uid(uid)
        if not norm_uid:
            MovementService._log_denied(
                uid=uid,
                device_id=device.id,
                direction=direction or device.direction,
                reason=DeniedReason.UNKNOWN_RFID,
                event_id=event_id,
                remarks="Empty or malformed RFID UID",
                is_demo=is_demo
            )
            return {
                "success": False,
                "decision": "ENTRY_DENIED",
                "reason": "UNKNOWN_RFID",
                "message": "RFID UID is empty or invalid."
            }, 400

        card = RFIDCard.query.filter_by(uid=norm_uid).first()
        if not card:
            # Buffer unregistered UID so Live Enrollment Mode catches it immediately
            try:
                from services.rfid_service import RFIDService
                RFIDService.capture_enrollment_scan(norm_uid, device.device_id if device else device_id)
            except Exception:
                pass

            MovementService._log_denied(
                uid=norm_uid,
                device_id=device.id,
                direction=direction or device.direction,
                reason=DeniedReason.UNKNOWN_RFID,
                event_id=event_id,
                remarks="Unregistered RFID tag scanned",
                is_demo=is_demo
            )
            return {
                "success": False,
                "decision": "ENTRY_DENIED",
                "reason": "UNKNOWN_RFID",
                "message": "RFID tag is not registered in the system."
            }, 404

        # 4. Check Card Status
        is_card_valid, card_err = card.is_valid()
        if not is_card_valid:
            reason_map = {
                "BLOCKED_CARD": DeniedReason.BLOCKED_CARD,
                "LOST_CARD": DeniedReason.BLOCKED_CARD,
                "INACTIVE_CARD": DeniedReason.INACTIVE_CARD,
                "EXPIRED_CARD": DeniedReason.EXPIRED_CARD
            }
            denied_reason = reason_map.get(card_err, DeniedReason.BLOCKED_CARD)
            MovementService._log_denied(
                uid=norm_uid,
                vehicle_id=card.vehicle_id,
                vehicle_number=card.vehicle.registration_number if card.vehicle else None,
                device_id=device.id,
                direction=direction or device.direction,
                reason=denied_reason,
                event_id=event_id,
                remarks=f"Card status: {card.card_status}",
                is_demo=is_demo
            )
            return {
                "success": False,
                "decision": "ENTRY_DENIED",
                "reason": denied_reason,
                "message": f"RFID Card is {card.card_status}."
            }, 403

        # 5. Check Assigned Vehicle or Driver
        vehicle = card.vehicle
        if not vehicle and card.driver:
            active_out = VehicleMovement.query.filter_by(
                driver_id=card.driver.id,
                status=MovementStatus.OUTSIDE
            ).order_by(VehicleMovement.exit_time.desc()).first()
            if active_out and active_out.vehicle:
                vehicle = active_out.vehicle
            else:
                vehicle = Vehicle.query.filter(
                    Vehicle.is_active == True,
                    (Vehicle.armynumber == card.driver.armynumber if card.driver.armynumber else False) |
                    (Vehicle.driver_name == card.driver.name)
                ).first()
                if not vehicle:
                    vehicle = Vehicle.query.filter_by(is_active=True).first()

        if not vehicle or not vehicle.is_active:
            MovementService._log_denied(
                uid=norm_uid,
                device_id=device.id,
                direction=direction or device.direction,
                reason=DeniedReason.UNAUTHORIZED_VEHICLE,
                event_id=event_id,
                remarks="Card not assigned to any active vehicle or driver",
                is_demo=is_demo
            )
            return {
                "success": False,
                "decision": "ENTRY_DENIED",
                "reason": "UNAUTHORIZED_VEHICLE",
                "message": "RFID card is not assigned to an active vehicle or driver."
            }, 403

        # 6. Check Vehicle Authorization
        is_auth, auth_err = vehicle.is_currently_authorized()
        if not is_auth:
            reason_map = {
                "BLOCKED_VEHICLE": DeniedReason.BLOCKED_VEHICLE,
                "EXPIRED_AUTHORIZATION": DeniedReason.EXPIRED_AUTHORIZATION,
                "UNAUTHORIZED_VEHICLE": DeniedReason.UNAUTHORIZED_VEHICLE,
                "VEHICLE_DEACTIVATED": DeniedReason.UNAUTHORIZED_VEHICLE,
                "NOT_YET_VALID": DeniedReason.EXPIRED_AUTHORIZATION
            }
            denied_reason = reason_map.get(auth_err, DeniedReason.UNAUTHORIZED_VEHICLE)
            MovementService._log_denied(
                uid=norm_uid,
                vehicle_id=vehicle.id,
                vehicle_number=vehicle.registration_number,
                device_id=device.id,
                direction=direction or device.direction,
                reason=denied_reason,
                event_id=event_id,
                remarks=f"Vehicle auth check failed: {auth_err}",
                is_demo=is_demo
            )
            return {
                "success": False,
                "decision": "ENTRY_DENIED",
                "reason": denied_reason,
                "message": f"Vehicle authorization status: {vehicle.auth_status} ({auth_err})."
            }, 403

        # 7. Determine Gate Direction
        resolved_direction = MovementService._resolve_direction(device, direction)

        # 8. Process ENTRY Movement (Inbound Return to Depot)
        if resolved_direction == GateDirection.ENTRY:
            active_outside = vehicle.get_active_outside_movement()
            if active_outside:
                # Vehicle returned from its active trip
                active_outside.entry_time = datetime.utcnow()
                active_outside.entry_device_id = device.id
                active_outside.entry_event_id = event_id
                active_outside.status = MovementStatus.INSIDE
                vehicle.current_vehicle_location = 'INSIDE'
                if active_outside.exit_time:
                    active_outside.duration_seconds = max(0, int((active_outside.entry_time - active_outside.exit_time).total_seconds()))
                device.last_event = f"ENTRY (RETURN): {vehicle.registration_number}"
                db.session.commit()
                target_movement = active_outside
            else:
                # Check if vehicle already has an active INSIDE movement
                active_inside = VehicleMovement.query.filter_by(
                    vehicle_id=vehicle.id,
                    status=MovementStatus.INSIDE
                ).first()
                if active_inside:
                    MovementService._log_denied(
                        uid=norm_uid,
                        vehicle_id=vehicle.id,
                        vehicle_number=vehicle.registration_number,
                        device_id=device.id,
                        direction=GateDirection.ENTRY,
                        reason=DeniedReason.DUPLICATE_ENTRY,
                        event_id=event_id,
                        remarks=f"Vehicle already entered at {active_inside.entry_time.strftime('%Y-%m-%d %H:%M:%S')}",
                        is_demo=is_demo
                    )
                    return {
                        "success": False,
                        "decision": "ENTRY_DENIED",
                        "reason": "DUPLICATE_ENTRY",
                        "message": "Vehicle is already marked INSIDE the premises.",
                        "vehicle_number": vehicle.registration_number
                    }, 409

                # Direct entry record
                new_movement = VehicleMovement(
                    vehicle_id=vehicle.id,
                    rfid_card_id=card.id,
                    driver_name=vehicle.driver_name,
                    entry_time=datetime.utcnow(),
                    entry_device_id=device.id,
                    direction=GateDirection.ENTRY,
                    status=MovementStatus.INSIDE,
                    entry_event_id=event_id,
                    is_demo=is_demo
                )
                db.session.add(new_movement)
                vehicle.current_vehicle_location = 'INSIDE'
                device.last_event = f"ENTRY: {vehicle.registration_number}"
                db.session.commit()
                target_movement = new_movement

            log_audit(
                action=AuditAction.VEHICLE_ENTRY,
                description=f"Authorized ENTRY (Arrival to Depot) for {vehicle.registration_number} ({vehicle.vehicle_type}) via {device.device_name}",
                related_vehicle=vehicle.registration_number,
                related_device=device.device_id
            )

            resp_data = {
                "success": True,
                "decision": "ENTRY_ALLOWED",
                "message": "Vehicle return authorized. Gate permitted.",
                "vehicle_number": vehicle.registration_number,
                "vehicle_type": vehicle.vehicle_type,
                "driver_name": target_movement.driver_name or vehicle.driver_name or "N/A",
                "movement_status": MovementStatus.INSIDE,
                "duration": target_movement.formatted_duration,
                "movement_id": target_movement.id,
                "event_id": event_id or "",
                "timestamp": datetime.utcnow().isoformat()
            }
            MovementService._log_device_event(device.id, "SCAN", event_id, resp_data)
            return resp_data, 200

        # 9. Process EXIT Movement (Outbound Dispatch from Depot / Smart Return)
        elif resolved_direction == GateDirection.EXIT:
            # Check if vehicle is already OUTSIDE on an active trip -> Record Inbound Return
            active_outside = vehicle.get_active_outside_movement()
            if active_outside:
                active_outside.entry_time = datetime.utcnow()
                active_outside.entry_device_id = device.id
                active_outside.entry_event_id = event_id
                active_outside.status = MovementStatus.INSIDE
                vehicle.current_vehicle_location = 'INSIDE'
                if active_outside.exit_time:
                    active_outside.duration_seconds = max(0, int((active_outside.entry_time - active_outside.exit_time).total_seconds()))
                device.last_event = f"ENTRY (RETURN): {vehicle.registration_number}"
                db.session.commit()

                log_audit(
                    action=AuditAction.VEHICLE_ENTRY,
                    description=f"Authorized RETURN (Arrival to Depot) for {vehicle.registration_number} ({vehicle.vehicle_type}) via {device.device_name}",
                    related_vehicle=vehicle.registration_number,
                    related_device=device.device_id
                )

                resp_data = {
                    "success": True,
                    "decision": "ENTRY_ALLOWED",
                    "message": f"Vehicle return authorized. Checked into depot.",
                    "vehicle_number": vehicle.registration_number,
                    "vehicle_type": vehicle.vehicle_type,
                    "driver_name": active_outside.driver_name or vehicle.driver_name or "N/A",
                    "movement_status": MovementStatus.INSIDE,
                    "duration": active_outside.formatted_duration,
                    "movement_id": active_outside.id,
                    "event_id": event_id or "",
                    "timestamp": datetime.utcnow().isoformat()
                }
                MovementService._log_device_event(device.id, "SCAN", event_id, resp_data)
                return resp_data, 200

            # Create new OUTBOUND departure record (Fleet Vehicle departing depot)
            new_movement = VehicleMovement(
                vehicle_id=vehicle.id,
                rfid_card_id=card.id,
                driver_name=vehicle.driver_name,
                exit_time=datetime.utcnow(),
                entry_time=None,
                exit_device_id=device.id,
                direction=GateDirection.EXIT,
                status=MovementStatus.OUTSIDE,
                exit_event_id=event_id,
                is_demo=is_demo
            )
            db.session.add(new_movement)
            vehicle.current_vehicle_location = 'OUT'
            device.last_event = f"EXIT: {vehicle.registration_number}"
            db.session.commit()

            log_audit(
                action=AuditAction.VEHICLE_EXIT,
                description=f"Authorized EXIT (Outbound Dispatch) for {vehicle.registration_number} ({vehicle.vehicle_type}) via {device.device_name}",
                related_vehicle=vehicle.registration_number,
                related_device=device.device_id
            )

            resp_data = {
                "success": True,
                "decision": "EXIT_RECORDED",
                "message": "Vehicle exit authorized. Gate permitted.",
                "vehicle_number": vehicle.registration_number,
                "vehicle_type": vehicle.vehicle_type,
                "driver_name": vehicle.driver_name or "N/A",
                "movement_status": MovementStatus.OUTSIDE,
                "duration": "N/A",
                "movement_id": new_movement.id,
                "event_id": event_id or "",
                "timestamp": datetime.utcnow().isoformat()
            }
            MovementService._log_device_event(device.id, "SCAN", event_id, resp_data)
            return resp_data, 200

        else:
            return {
                "success": False,
                "decision": "ENTRY_DENIED",
                "reason": "INVALID_DIRECTION",
                "message": f"Unsupported movement direction: {resolved_direction}"
            }, 400

    @staticmethod
    def confirm_movement(uid: str, direction: str, driver_id: int = None, driver_name: str = None, operator_user = None, remarks: str = None, device_id: str = None, vehicle_id: int = None):
        """
        Operator confirms movement direction (ENTRY or EXIT) for a scanned vehicle.
        Supports vehicle tags and dedicated driver badges.
        Explicitly commits the movement and updates inside/outside counts.
        """
        norm_uid = normalize_uid(uid)
        card = RFIDCard.query.filter_by(uid=norm_uid).first()
        if not card:
            return False, "Scanned RFID card record not found in system.", None

        # Resolve vehicle (support card.vehicle, explicit vehicle_id, or card.driver)
        vehicle = None
        if vehicle_id:
            vehicle = db.session.get(Vehicle, vehicle_id)

        if not vehicle and card.vehicle:
            vehicle = card.vehicle

        if not vehicle and card.driver:
            # Check if this driver currently has an active trip outside
            active_out = VehicleMovement.query.filter_by(
                driver_id=card.driver.id,
                status=MovementStatus.OUTSIDE
            ).order_by(VehicleMovement.exit_time.desc()).first()
            if active_out and active_out.vehicle:
                vehicle = active_out.vehicle
            else:
                vehicle = Vehicle.query.filter(
                    Vehicle.is_active == True,
                    (Vehicle.armynumber == card.driver.armynumber if card.driver.armynumber else False) |
                    (Vehicle.custodian_name == card.driver.name)
                ).first()
                if not vehicle:
                    from services.rfid_service import RFIDService
                    pending = RFIDService.get_pending_scan()
                    if pending and pending.get('vehicle') and pending.get('vehicle', {}).get('id'):
                        vehicle = db.session.get(Vehicle, pending['vehicle']['id'])
                if not vehicle:
                    if direction and direction.upper() == GateDirection.ENTRY:
                        outside_mov = VehicleMovement.query.filter_by(status=MovementStatus.OUTSIDE).order_by(VehicleMovement.exit_time.desc()).first()
                        if outside_mov:
                            vehicle = outside_mov.vehicle
                    if not vehicle:
                        vehicle = Vehicle.query.filter_by(is_active=True).first()

        if not vehicle:
            return False, "No active vehicle assigned or selected for this scan.", None

        is_auth, auth_err = vehicle.is_currently_authorized()
        if not is_auth:
            return False, f"Vehicle authorization status: {vehicle.auth_status} ({auth_err}).", None

        # Resolve driver details
        final_driver_id = driver_id or (card.driver.id if card.driver else None)
        final_driver_name = driver_name
        if final_driver_id:
            from models.driver import Driver
            drv = db.session.get(Driver, final_driver_id)
            if drv:
                final_driver_name = drv.name
        if not final_driver_name:
            if card.driver:
                final_driver_name = card.driver.name
            else:
                final_driver_name = "Unassigned Driver"

        # Resolve device
        dev = Device.query.filter_by(device_id=device_id).first() if device_id else None
        dev_id = dev.id if dev else None

        from services.rfid_service import RFIDService
        RFIDService.clear_pending_scan()

        direction_upper = direction.strip().upper() if direction else GateDirection.ENTRY
        active_outside = vehicle.get_active_outside_movement()
        is_outside = active_outside is not None

        if direction_upper == GateDirection.ENTRY:
            # Cannot enter if vehicle is already inside!
            if not is_outside:
                return False, f"Vehicle '{vehicle.registration_number}' is already INSIDE the depot. Cannot record ENTRY (IN).", None

            # Vehicle returned from its active trip
            active_outside.entry_time = datetime.utcnow()
            active_outside.status = MovementStatus.INSIDE
            active_outside.driver_id = final_driver_id
            active_outside.driver_name = final_driver_name
            vehicle.current_vehicle_location = 'INSIDE'
            if dev_id:
                active_outside.entry_device_id = dev_id
            if operator_user:
                active_outside.entry_operator_id = operator_user.id
            if remarks:
                active_outside.remarks = (active_outside.remarks or "") + ("\n" if active_outside.remarks else "") + remarks
            if active_outside.exit_time:
                active_outside.duration_seconds = max(0, int((active_outside.entry_time - active_outside.exit_time).total_seconds()))
            db.session.commit()
            target_movement = active_outside

            log_audit(
                action=AuditAction.VEHICLE_ENTRY,
                description=f"Confirmed ENTRY (Arrival to Depot) for {vehicle.registration_number} ({vehicle.vehicle_type}) by {operator_user.username if operator_user else 'Operator'}",
                related_vehicle=vehicle.registration_number,
                user=operator_user
            )

            total_vehicles = Vehicle.query.filter_by(is_active=True).count()
            outside_count = VehicleMovement.query.filter_by(status=MovementStatus.OUTSIDE).count()
            inside_count = max(0, total_vehicles - outside_count)

            return True, "Vehicle arrival confirmed. Depot entry authorized.", {
                "decision": "ENTRY_ALLOWED",
                "movement_status": MovementStatus.INSIDE,
                "direction": "ENTRY",
                "vehicle_number": vehicle.registration_number,
                "vehicle_type": vehicle.vehicle_type,
                "driver_name": final_driver_name,
                "movement_id": target_movement.id,
                "duration": target_movement.formatted_duration,
                "inside_count": inside_count,
                "outside_count": outside_count,
                "timestamp": datetime.utcnow().strftime('%H:%M:%S')
            }

        elif direction_upper == GateDirection.EXIT:
            # Cannot exit if vehicle is already outside!
            if is_outside:
                return False, f"Vehicle '{vehicle.registration_number}' is already OUTSIDE on an active trip. Cannot record EXIT (OUT).", None

            # Outbound Exit / Dispatch
            new_movement = VehicleMovement(
                vehicle_id=vehicle.id,
                rfid_card_id=card.id,
                driver_id=final_driver_id,
                driver_name=final_driver_name,
                exit_time=datetime.utcnow(),
                entry_time=None,
                exit_device_id=dev_id,
                exit_operator_id=operator_user.id if operator_user else None,
                direction=GateDirection.EXIT,
                status=MovementStatus.OUTSIDE,
                remarks=remarks
            )
            db.session.add(new_movement)
            vehicle.current_vehicle_location = 'OUT'
            db.session.commit()

            log_audit(
                action=AuditAction.VEHICLE_EXIT,
                description=f"Confirmed EXIT (Outbound Dispatch) for {vehicle.registration_number} ({vehicle.vehicle_type}) by {operator_user.username if operator_user else 'Operator'}",
                related_vehicle=vehicle.registration_number,
                user=operator_user
            )

            total_vehicles = Vehicle.query.filter_by(is_active=True).count()
            outside_count = VehicleMovement.query.filter_by(status=MovementStatus.OUTSIDE).count()
            inside_count = max(0, total_vehicles - outside_count)

            return True, "Vehicle exit confirmed. Outbound dispatch recorded.", {
                "decision": "EXIT_RECORDED",
                "movement_status": MovementStatus.OUTSIDE,
                "direction": "EXIT",
                "vehicle_number": vehicle.registration_number,
                "vehicle_type": vehicle.vehicle_type,
                "driver_name": final_driver_name,
                "movement_id": new_movement.id,
                "duration": "N/A",
                "inside_count": inside_count,
                "outside_count": outside_count,
                "timestamp": datetime.utcnow().strftime('%H:%M:%S')
            }
        else:
            return False, f"Invalid direction: '{direction}'. Expected 'ENTRY' or 'EXIT'.", None

    @staticmethod
    def process_manual_movement(vehicle_id: int, direction: str, reason: str, operator_user, remarks: str = None, is_demo: bool = False):
        """
        Controlled manual entry or exit processing by an authorized operator.
        Does not bypass vehicle authorization validity.
        """
        if not reason or not reason.strip():
            return False, "A mandatory reason must be provided for manual override.", None

        vehicle = db.session.get(Vehicle, vehicle_id)
        if not vehicle:
            return False, "Vehicle not found.", None

        # Verify authorization status
        is_auth, auth_err = vehicle.is_currently_authorized()
        if not is_auth:
            return False, f"Manual operation rejected: Vehicle authorization status is {vehicle.auth_status} ({auth_err}).", None

        if direction == GateDirection.ENTRY:
            # Check if vehicle has an active OUTSIDE trip to close
            active_outside = vehicle.get_active_outside_movement()
            if active_outside:
                active_outside.entry_time = datetime.utcnow()
                active_outside.entry_operator_id = operator_user.id if operator_user else None
                active_outside.status = MovementStatus.INSIDE
                active_outside.is_manual = True
                active_outside.manual_reason = reason.strip()
                vehicle.current_vehicle_location = 'INSIDE'
                if remarks:
                    active_outside.remarks = (active_outside.remarks or "") + ("\n" if active_outside.remarks else "") + remarks
                if active_outside.exit_time:
                    active_outside.duration_seconds = max(0, int((active_outside.entry_time - active_outside.exit_time).total_seconds()))
                db.session.commit()

                log_audit(
                    action=AuditAction.MANUAL_OVERRIDE,
                    description=f"MANUAL RETURN (IN Depot) recorded for '{vehicle.registration_number}' by {operator_user.username if operator_user else 'Operator'}. Trip Duration: {active_outside.formatted_duration}. Reason: {reason}",
                    related_vehicle=vehicle.registration_number,
                    user=operator_user
                )
                return True, f"Vehicle '{vehicle.registration_number}' marked RETURNED to depot successfully.", active_outside

            # Direct manual entry record
            movement = VehicleMovement(
                vehicle_id=vehicle.id,
                entry_time=datetime.utcnow(),
                entry_operator_id=operator_user.id if operator_user else None,
                direction=GateDirection.ENTRY,
                status=MovementStatus.INSIDE,
                is_manual=True,
                manual_reason=reason.strip(),
                remarks=f"MANUAL ENTRY: {remarks or ''}".strip(),
                is_demo=is_demo
            )
            db.session.add(movement)
            vehicle.current_vehicle_location = 'INSIDE'
            db.session.commit()

            log_audit(
                action=AuditAction.MANUAL_OVERRIDE,
                description=f"MANUAL ENTRY recorded for '{vehicle.registration_number}' by {operator_user.username if operator_user else 'Operator'}. Reason: {reason}",
                related_vehicle=vehicle.registration_number,
                user=operator_user
            )
            return True, "Manual entry recorded successfully.", movement

        elif direction == GateDirection.EXIT:
            if vehicle.is_currently_outside:
                return False, f"Vehicle '{vehicle.registration_number}' is already recorded OUTSIDE on a trip.", None

            movement = VehicleMovement(
                vehicle_id=vehicle.id,
                exit_time=datetime.utcnow(),
                entry_time=None,
                exit_operator_id=operator_user.id if operator_user else None,
                direction=GateDirection.EXIT,
                status=MovementStatus.OUTSIDE,
                is_manual=True,
                manual_reason=reason.strip(),
                remarks=f"MANUAL DISPATCH (EXIT): {remarks or ''}".strip(),
                is_demo=is_demo
            )
            db.session.add(movement)
            vehicle.current_vehicle_location = 'OUT'
            db.session.commit()

            log_audit(
                action=AuditAction.MANUAL_OVERRIDE,
                description=f"MANUAL DISPATCH (EXIT) recorded for '{vehicle.registration_number}' by {operator_user.username if operator_user else 'Operator'}. Reason: {reason}",
                related_vehicle=vehicle.registration_number,
                user=operator_user
            )
            return True, "Manual outbound dispatch (EXIT) recorded successfully.", movement

        return False, f"Invalid direction '{direction}'.", None

    @staticmethod
    def _resolve_direction(device: Device, requested_direction: str = None) -> str:
        """Resolve gate direction based on system setting, device, or scan."""
        # 1. System Setting Gate Direction Mode (Server Master Authority)
        mode = SystemSetting.get_value('gate_direction_mode', 'EXIT_ONLY')
        if mode == 'EXIT_ONLY':
            return GateDirection.EXIT
        elif mode == 'ENTRY_ONLY':
            return GateDirection.ENTRY

        # 2. If MANUAL_DIRECTION / FLEXIBLE mode, check requested direction
        if requested_direction and requested_direction in [GateDirection.ENTRY, GateDirection.EXIT]:
            return requested_direction

        # 3. Device fixed direction (from Device table)
        if device and device.direction in [GateDirection.ENTRY, GateDirection.EXIT]:
            return device.direction

        # 4. Fallback to EXIT (Depot fleet outbound dispatch)
        return GateDirection.EXIT

    @staticmethod
    def _log_denied(uid=None, vehicle_id=None, vehicle_number=None, device_id=None, direction='ENTRY', reason=None, event_id=None, remarks=None, is_demo=False):
        """Helper to record denied attempts and trigger audit trail."""
        attempt = DeniedAttempt(
            timestamp=datetime.utcnow(),
            rfid_uid=uid,
            vehicle_id=vehicle_id,
            vehicle_number=vehicle_number,
            device_id=device_id,
            direction=direction or 'ENTRY',
            reason=reason or DeniedReason.UNAUTHORIZED_VEHICLE,
            event_id=event_id,
            remarks=remarks,
            is_demo=is_demo
        )
        db.session.add(attempt)
        db.session.commit()

        log_audit(
            action=AuditAction.DENIED_ATTEMPT,
            description=f"DENIED {direction} for UID '{uid or 'Unknown'}' / Plate '{vehicle_number or 'Unknown'}'. Reason: {reason}. {remarks or ''}",
            related_vehicle=vehicle_number,
            related_device=str(device_id) if device_id else None
        )

    @staticmethod
    def _log_device_event(device_id: int, event_type: str, event_id: str, payload: dict):
        """Helper to store device event for idempotency and audit."""
        evt = DeviceEvent(
            device_id=device_id,
            event_type=event_type,
            event_id=event_id,
            raw_payload=json.dumps(payload),
            response_summary=f"{payload.get('decision', 'PROCESSED')} - {payload.get('message', '')}",
            timestamp=datetime.utcnow()
        )
        db.session.add(evt)
        db.session.commit()
