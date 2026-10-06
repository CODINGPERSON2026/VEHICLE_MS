from datetime import date, timedelta
from services.vehicle_service import VehicleService
from models.vehicle import Vehicle, AuthStatus, VehicleType, normalize_plate

def test_normalize_plate():
    assert normalize_plate("mh-12 ab 1234") == "MH12AB1234"
    assert normalize_plate(" dl 01 xy-9999 ") == "DL01XY9999"
    assert normalize_plate("") == ""

def test_create_vehicle_success(app):
    with app.app_context():
        success, msg, veh = VehicleService.create_vehicle({
            'registration_number': 'MH12AB1234',
            'vehicle_type': VehicleType.GYPSY,
            'issue_date': '2025-01-15',
            'custodian_name': 'Subedar Rajesh Sharma',
            'armynumber': 'JC-847291A',
            'mobile_number': '9876543210',
            'auth_status': AuthStatus.AUTHORIZED
        })
        assert success is True
        assert veh.registration_number == 'MH12AB1234'
        assert veh.custodian_name == 'Subedar Rajesh Sharma'
        assert veh.armynumber == 'JC-847291A'
        assert veh.is_active is True

def test_prevent_duplicate_vehicle(app):
    with app.app_context():
        VehicleService.create_vehicle({'registration_number': 'MH12AB1234'})
        # Try registering with spaces/lowercase
        success, msg, veh = VehicleService.create_vehicle({'registration_number': 'mh 12 ab 1234'})
        assert success is False
        assert "already registered" in msg

def test_vehicle_authorization_logic(app):
    with app.app_context():
        # Valid vehicle
        v1 = Vehicle(registration_number='V1', auth_status=AuthStatus.AUTHORIZED)
        is_auth, _ = v1.is_currently_authorized()
        assert is_auth is True

        # Expired vehicle
        v2 = Vehicle(registration_number='V2', auth_status=AuthStatus.EXPIRED)
        is_auth, reason = v2.is_currently_authorized()
        assert is_auth is False
        assert reason == "EXPIRED_AUTHORIZATION"

        # Blocked vehicle
        v3 = Vehicle(registration_number='V3', auth_status=AuthStatus.BLOCKED)
        is_auth, reason = v3.is_currently_authorized()
        assert is_auth is False
        assert reason == "BLOCKED_VEHICLE"

def test_soft_deactivate_and_reactivate(app):
    with app.app_context():
        _, _, v = VehicleService.create_vehicle({'registration_number': 'KA04ZZ9999'})
        assert v.is_active is True

        VehicleService.deactivate_vehicle(v.id)
        assert v.is_active is False
        is_auth, reason = v.is_currently_authorized()
        assert is_auth is False
        assert reason == "VEHICLE_DEACTIVATED"

        VehicleService.reactivate_vehicle(v.id)
        assert v.is_active is True

def test_view_vehicle_route(client, admin_user, app):
    client.post('/login', data={'username': 'admin', 'password': 'AdminPass123!'})
    with app.app_context():
        _, _, v = VehicleService.create_vehicle({'registration_number': 'MH12AA1111'})
        v_id = v.id
    
    resp = client.get(f'/vehicles/{v_id}')
    assert resp.status_code == 200
    assert b"MH12AA1111" in resp.data

def test_delete_vehicle_with_movements_and_rfid_cards(client, admin_user, app):
    from models.movement import VehicleMovement, MovementStatus
    from models.rfid import RFIDCard
    from database.db_init import db

    client.post('/login', data={'username': 'admin', 'password': 'AdminPass123!'})
    with app.app_context():
        v = Vehicle(registration_number="MH14DEL9999", auth_status=AuthStatus.AUTHORIZED)
        db.session.add(v)
        db.session.flush()

        # Add assigned card
        card = RFIDCard(uid="DELCARD123", vehicle_id=v.id)
        db.session.add(card)
        db.session.flush()

        # Add movements
        m1 = VehicleMovement(vehicle_id=v.id, rfid_card_id=card.id, status=MovementStatus.OUTSIDE)
        m2 = VehicleMovement(vehicle_id=v.id, rfid_card_id=card.id, status=MovementStatus.INSIDE)
        db.session.add_all([m1, m2])
        db.session.commit()

        v_id = v.id
        card_id = card.id

    # Delete vehicle via POST endpoint
    resp = client.post(f'/vehicles/{v_id}/delete', follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        # Vehicle is removed
        assert db.session.get(Vehicle, v_id) is None
        # Linked card is preserved and unassigned
        saved_card = db.session.get(RFIDCard, card_id)
        assert saved_card is not None
        assert saved_card.vehicle_id is None
        # Vehicle movements for deleted vehicle are cleaned up
        assert VehicleMovement.query.filter_by(vehicle_id=v_id).count() == 0

