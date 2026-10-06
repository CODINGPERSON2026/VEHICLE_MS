import uuid
from datetime import date, timedelta
from models.vehicle import Vehicle, AuthStatus, VehicleType
from models.rfid import RFIDCard, CardStatus, normalize_uid
from models.movement import VehicleMovement, MovementStatus, GateDirection
from models.device import Device, DeviceDirection
from models.denied_attempt import DeniedAttempt
from services.rfid_service import RFIDService
from services.movement_service import MovementService
from database.db_init import db

def test_rfid_normalization_and_assignment(app):
    with app.app_context():
        assert normalize_uid(" a3:7f:29:1c ") == "A37F291C"
        
        veh = Vehicle(registration_number="MH12AB1234", vehicle_type=VehicleType.GYPSY, auth_status=AuthStatus.AUTHORIZED)
        db.session.add(veh)
        db.session.commit()

        success, msg, card = RFIDService.assign_card(uid="A37F291C", vehicle_id=veh.id)
        assert success is True
        assert card.uid == "A37F291C"
        assert card.vehicle_id == veh.id
        assert card.card_status == CardStatus.ACTIVE

def test_prevent_duplicate_rfid_assignment(app):
    with app.app_context():
        v1 = Vehicle(registration_number="V01")
        v2 = Vehicle(registration_number="V02")
        db.session.add_all([v1, v2])
        db.session.commit()

        RFIDService.assign_card(uid="TAG001", vehicle_id=v1.id)
        # Attempt assigning same active UID to v2
        success, msg, _ = RFIDService.assign_card(uid="TAG001", vehicle_id=v2.id)
        assert success is False
        assert "already assigned" in msg

def test_valid_rfid_entry_and_exit_flow(client, test_device, app):
    with app.app_context():
        v = Vehicle(registration_number="MH12AB1234", auth_status=AuthStatus.AUTHORIZED)
        db.session.add(v)
        db.session.flush()
        c = RFIDCard(uid="A37F291C", vehicle_id=v.id, card_status=CardStatus.ACTIVE)
        db.session.add(c)
        db.session.commit()

    # 1. First Scan on Depot vehicle (dispatches OUTSIDE)
    resp = client.post('/api/rfid/scan', json={
        "uid": "A37F291C",
        "device_id": "GATE_ENTRY_01",
        "api_key": "test_api_key_123",
        "direction": "EXIT",
        "event_id": "evt-exit-001"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["decision"] == "EXIT_RECORDED"
    assert data["movement_status"] == "OUTSIDE"
    assert data["vehicle_number"] == "MH12AB1234"

    # 2. Second Scan on returning vehicle (returns INSIDE depot)
    ret_resp = client.post('/api/rfid/scan', json={
        "uid": "A37F291C",
        "device_id": "GATE_ENTRY_01",
        "api_key": "test_api_key_123",
        "direction": "ENTRY",
        "event_id": "evt-ret-001"
    })
    assert ret_resp.status_code == 200
    ret_data = ret_resp.get_json()
    assert ret_data["success"] is True
    assert ret_data["decision"] == "ENTRY_ALLOWED"
    assert ret_data["movement_status"] == "INSIDE"

    # 3. Third Scan (dispatches OUTSIDE again)
    exit_resp = client.post('/api/rfid/scan', json={
        "uid": "A37F291C",
        "device_id": "GATE_ENTRY_01",
        "api_key": "test_api_key_123",
        "direction": "EXIT",
        "event_id": "evt-exit-002"
    })
    assert exit_resp.status_code == 200
    exit_data = exit_resp.get_json()
    assert exit_data["success"] is True
    assert exit_data["decision"] == "EXIT_RECORDED"
    assert exit_data["movement_status"] == "OUTSIDE"

    # 4. Outbound Exit for Depot-based vehicle
    with app.app_context():
        v2 = Vehicle(registration_number="MH12DEPOT99", auth_status=AuthStatus.AUTHORIZED)
        db.session.add(v2)
        db.session.flush()
        c2 = RFIDCard(uid="DEADBEEF01", vehicle_id=v2.id, card_status=CardStatus.ACTIVE)
        db.session.add(c2)
        db.session.commit()

    exit2_resp = client.post('/api/rfid/scan', json={
        "uid": "DEADBEEF01",
        "device_id": "GATE_ENTRY_01",
        "api_key": "test_api_key_123",
        "direction": "EXIT",
        "event_id": "evt-exit-003"
    })
    assert exit2_resp.status_code == 200
    exit2_data = exit2_resp.get_json()
    assert exit2_data["success"] is True
    assert exit2_data["decision"] == "EXIT_RECORDED"
    assert exit2_data["movement_status"] == "OUTSIDE"
    assert exit2_data["vehicle_number"] == "MH12DEPOT99"

def test_unknown_and_blocked_rfid_scans(client, test_device, app):
    with app.app_context():
        v = Vehicle(registration_number="BLOCKED01", auth_status=AuthStatus.BLOCKED)
        db.session.add(v)
        db.session.flush()
        c = RFIDCard(uid="CAFEBABE", vehicle_id=v.id, card_status=CardStatus.BLOCKED)
        db.session.add(c)
        db.session.commit()

    # Unknown RFID
    resp_unknown = client.post('/api/rfid/scan', json={
        "uid": "UNKNOWN_TAG",
        "device_id": "GATE_ENTRY_01",
        "api_key": "test_api_key_123",
        "direction": "ENTRY"
    })
    assert resp_unknown.status_code == 404
    assert resp_unknown.get_json()["reason"] == "UNKNOWN_RFID"

    # Blocked Card
    resp_blocked = client.post('/api/rfid/scan', json={
        "uid": "CAFEBABE",
        "device_id": "GATE_ENTRY_01",
        "api_key": "test_api_key_123",
        "direction": "ENTRY"
    })
    assert resp_blocked.status_code == 403
    assert resp_blocked.get_json()["reason"] == "BLOCKED_CARD"

def test_device_authentication_and_heartbeat(client, test_device):
    # Invalid device key
    resp_bad_key = client.post('/api/rfid/scan', json={
        "uid": "A37F291C",
        "device_id": "GATE_ENTRY_01",
        "api_key": "WRONG_KEY"
    })
    assert resp_bad_key.status_code == 403

    # Device Heartbeat
    resp_hb = client.post('/api/device/heartbeat', json={
        "device_id": "GATE_ENTRY_01",
        "api_key": "test_api_key_123",
        "firmware_version": "v1.0.0"
    })
    assert resp_hb.status_code == 200
    assert resp_hb.get_json()["status"] == "ONLINE"

def test_manual_entry_and_exit(app, operator_user):
    with app.app_context():
        veh = Vehicle(registration_number="DL01XY9999", auth_status=AuthStatus.AUTHORIZED)
        db.session.add(veh)
        db.session.commit()

        # Manual Entry
        success, msg, mov = MovementService.process_manual_movement(
            vehicle_id=veh.id,
            direction=GateDirection.ENTRY,
            reason="RFID card left at home",
            operator_user=operator_user
        )
        assert success is True
        assert mov.status == MovementStatus.INSIDE
        assert mov.is_manual is True
        assert mov.manual_reason == "RFID card left at home"

        # Manual Exit
        success_exit, msg_exit, mov_exit = MovementService.process_manual_movement(
            vehicle_id=veh.id,
            direction=GateDirection.EXIT,
            reason="Operator manual gate exit",
            operator_user=operator_user
        )
        assert success_exit is True
        assert mov_exit.status == MovementStatus.OUTSIDE

def test_gate01_default_device_and_direction_toggle(client, app, admin_user):
    # Test setting gate direction
    client.post('/login', data={'username': 'admin', 'password': 'AdminPass123!'})
    resp_dir = client.post('/movements/set-direction', data={'direction': 'EXIT'}, follow_redirects=True)
    assert resp_dir.status_code == 200

    with app.app_context():
        # GATE01 seeded in db_init
        dev = Device.query.filter_by(device_id='GATE01').first()
        assert dev is not None
        assert dev.check_api_key('dev_gate01_secret') is True

def test_unassign_and_delete_rfid_card(app, client, admin_user):
    client.post('/login', data={'username': 'admin', 'password': 'AdminPass123!'})
    with app.app_context():
        v = Vehicle(registration_number="MH04XY7777")
        db.session.add(v)
        db.session.flush()
        c = RFIDCard(uid="TESTUNASSIGN1", vehicle_id=v.id)
        db.session.add(c)
        db.session.commit()
        card_id = c.id

    # Test Unassign
    resp_unassign = client.post(f'/rfid-cards/{card_id}/unassign', follow_redirects=True)
    assert resp_unassign.status_code == 200
    with app.app_context():
        card = db.session.get(RFIDCard, card_id)
        assert card.vehicle_id is None

    # Test Delete
    resp_delete = client.post(f'/rfid-cards/{card_id}/delete', follow_redirects=True)
    assert resp_delete.status_code == 200
    with app.app_context():
        assert db.session.get(RFIDCard, card_id) is None

def test_reassign_existing_card_with_string_expiry_date(app):
    with app.app_context():
        v1 = Vehicle(registration_number="MH01AA1111")
        v2 = Vehicle(registration_number="MH01BB2222")
        db.session.add_all([v1, v2])
        db.session.commit()

        # Initial assign with string date
        ok, msg, card = RFIDService.assign_card(uid="TAGEXP123", vehicle_id=v1.id, expiry_date="2026-12-31")
        assert ok is True
        assert card.expiry_date == date(2026, 12, 31)

        # Unassign first
        RFIDService.unassign_card(card.id)

        # Reassign to v2 with string date (this triggered StatementError before)
        ok2, msg2, card2 = RFIDService.assign_card(uid="TAGEXP123", vehicle_id=v2.id, expiry_date="2027-06-30")
        assert ok2 is True
        assert card2.vehicle_id == v2.id
        assert card2.expiry_date == date(2027, 6, 30)

def test_driver_selection_and_assignment_flow(app, client, admin_user, test_device):
    client.post('/login', data={'username': 'admin', 'password': 'AdminPass123!'})
    from models.driver import Driver
    with app.app_context():
        v = Vehicle(registration_number="MH20DRV001", driver_name="Default Owner", auth_status=AuthStatus.AUTHORIZED)
        db.session.add(v)
        db.session.flush()
        c = RFIDCard(uid="A1B2C3D4", vehicle_id=v.id, card_status=CardStatus.ACTIVE)
        d = Driver(name="Pool Driver Vikram", employee_id="DRV- Vikram", designation="Senior Driver", is_active=True)
        db.session.add_all([c, d])
        db.session.commit()
        driver_id = d.id

    # 1. RFID Scan arrives
    resp = client.post('/api/rfid/scan', json={
        "uid": "A1B2C3D4",
        "device_id": "GATE_ENTRY_01",
        "api_key": "test_api_key_123",
        "direction": "ENTRY"
    })
    assert resp.status_code == 200

    # 2. Live feed returns event with movement_id and default driver
    feed_resp = client.get('/api/movements/live_feed')
    assert feed_resp.status_code == 200
    feed_data = feed_resp.get_json()
    assert feed_data["last_event"] is not None
    mov_id = feed_data["last_event"]["movement_id"]
    assert feed_data["last_event"]["vehicle_number"] == "MH20DRV001"
    assert feed_data["last_event"]["owner_driver"] == "Default Owner"

    # 3. Operator selects Pool Driver Vikram
    assign_resp = client.post(f'/api/movements/{mov_id}/assign_driver', json={
        "driver_id": driver_id,
        "driver_name": "Pool Driver Vikram"
    })
    assert assign_resp.status_code == 200
    assign_data = assign_resp.get_json()
    assert assign_data["success"] is True
    assert assign_data["driver_name"] == "Pool Driver Vikram"

    with app.app_context():
        mov = db.session.get(VehicleMovement, mov_id)
        assert mov.driver_name == "Pool Driver Vikram"
        assert mov.driver_id == driver_id

def test_vehicles_outside_and_quick_return(app, client, admin_user, test_device):
    client.post('/login', data={'username': 'admin', 'password': 'AdminPass123!'})
    with app.app_context():
        v = Vehicle(registration_number="MH14OUT1234", driver_name="Depot Driver", auth_status=AuthStatus.AUTHORIZED)
        db.session.add(v)
        db.session.flush()
        c = RFIDCard(uid="FA551234", vehicle_id=v.id, card_status=CardStatus.ACTIVE)
        db.session.add(c)
        db.session.commit()
        veh_id = v.id

    # 1. Vehicle exits on RFID touch (starts from depot)
    scan_resp = client.post('/api/rfid/scan', json={
        "uid": "FA551234",
        "device_id": "GATE_ENTRY_01",
        "api_key": "test_api_key_123",
        "direction": "EXIT"
    })
    assert scan_resp.status_code == 200
    assert scan_resp.get_json()["decision"] == "EXIT_RECORDED"
    assert scan_resp.get_json()["movement_status"] == "OUTSIDE"

    # 2. View Vehicles Outside page
    out_page_resp = client.get('/vehicles-outside')
    assert out_page_resp.status_code == 200
    assert b"MH14OUT1234" in out_page_resp.data

    # 3. 1-click Quick Return (Arrival Check-In) back to Depot
    ret_resp = client.post(f'/movements/{veh_id}/quick_return', follow_redirects=True)
    assert ret_resp.status_code == 200

    # 4. Verify vehicle is now INSIDE
    with app.app_context():
        veh = db.session.get(Vehicle, veh_id)
        assert veh.has_active_movement() is not None
        assert veh.has_active_movement().status == MovementStatus.INSIDE



