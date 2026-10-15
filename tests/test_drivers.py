from models.driver import Driver
from models.vehicle import Vehicle, AuthStatus
from models.movement import VehicleMovement, MovementStatus
from services.driver_service import DriverService
from database.db_init import db

def test_driver_crud(app):
    with app.app_context():

        # Test creating new driver
        ok, msg, new_drv = DriverService.create_driver({
            'name': 'Test New Driver',
            'armynumber': 'JC-999999Z',
            'driver_rank': 'Havaldar',
            'company': 'HQ Coy',
            'section': 'MT Sec',
            'hill_driving': 'YES',
            'authorized_vehicle_types': ['Gypsy', 'ALS'],
            'mobile_number': '9999888877',
            'designation': 'Chauffeur'
        })
        assert ok is True
        assert new_drv.name == 'Test New Driver'
        assert new_drv.armynumber == 'JC-999999Z'
        assert new_drv.auth_status == 'AUTHORIZED'
        assert new_drv.hill_driving == 'YES'

        # Test updating driver
        ok_upd, msg_upd = DriverService.update_driver(new_drv.id, {
            'name': 'Test New Driver Updated',
            'designation': 'Senior Chauffeur'
        })
        assert ok_upd is True
        assert db.session.get(Driver, new_drv.id).name == 'Test New Driver Updated'

        # Test deleting driver
        ok_del, msg_del = DriverService.delete_driver(new_drv.id)
        assert ok_del is True
        assert db.session.get(Driver, new_drv.id) is None

def test_driver_routes_and_live_assignment(client, admin_user, app):
    client.post('/login', data={'username': 'admin', 'password': 'AdminPass123!'})

    with app.app_context():
        d = Driver(name="Test Driver Alpha", employee_id="DRV-TEST", mobile_number="9800000000", is_active=True)
        db.session.add(d)
        db.session.commit()

    # 1. Test Driver Master List View
    resp_list = client.get('/drivers')
    assert resp_list.status_code == 200
    assert b"Driver Master" in resp_list.data

    # 2. Test API Driver List
    resp_api = client.get('/api/drivers/list')
    assert resp_api.status_code == 200
    data = resp_api.get_json()
    assert data["success"] is True
    assert len(data["drivers"]) >= 1

    # 3. Test Live Movement Driver Assignment
    with app.app_context():
        v = Vehicle(registration_number="MH02TEST8888", driver_name="Owner Default", auth_status=AuthStatus.AUTHORIZED)
        db.session.add(v)
        db.session.flush()

        mov = VehicleMovement(vehicle_id=v.id, driver_name="Owner Default", status=MovementStatus.INSIDE)
        db.session.add(mov)
        db.session.commit()
        mov_id = mov.id

        sample_driver = Driver.query.first()
        sample_driver_id = sample_driver.id
        sample_driver_name = sample_driver.name

    resp_assign = client.post(f'/api/movements/{mov_id}/assign_driver', json={
        'driver_id': sample_driver_id,
        'driver_name': sample_driver_name
    })
    assert resp_assign.status_code == 200
    assign_data = resp_assign.get_json()
    assert assign_data["success"] is True
    assert assign_data["driver_name"] == sample_driver_name

    with app.app_context():
        updated_mov = db.session.get(VehicleMovement, mov_id)
        assert updated_mov.driver_id == sample_driver_id
        assert updated_mov.driver_name == sample_driver_name

        # Clean up
        db.session.delete(updated_mov)
        db.session.delete(v)
        db.session.delete(d)
        db.session.commit()

def test_rfid_card_driver_assignment(client, app):
    from models.user import User
    from models.rfid import RFIDCard
    from services.rfid_service import RFIDService

    with app.app_context():
        admin = User.query.filter_by(username='tiger').first()
        driver = Driver(name="Driver Havaldar Singh", armynumber="ARM-8899", driver_rank="Havaldar", is_active=True)
        db.session.add(driver)
        db.session.commit()
        driver_id = driver.id

        # 1. Assign RFID card to driver
        test_uid = "D9988A12"
        ok, msg, card = RFIDService.assign_card(uid=test_uid, driver_id=driver_id, user=admin)
        assert ok is True
        assert card.driver_id == driver_id

        # 2. Verify Database Links
        card_db = RFIDCard.query.filter_by(uid=test_uid).first()
        driver_db = db.session.get(Driver, driver_id)
        assert card_db.driver_id == driver_id
        assert driver_db.rfid_uid == test_uid
        assert driver_db.primary_rfid_uid == test_uid

        # 3. Test Querying cards list with search
        cards = RFIDService.get_all_cards(search="Havaldar")
        assert len(cards) >= 1
        assert cards[0].driver.name == "Driver Havaldar Singh"

        # 4. Test Unassigning card
        ok_unassign, _ = RFIDService.unassign_card(card_db.id, user=admin)
        assert ok_unassign is True
        assert card_db.driver_id is None
        assert driver_db.rfid_uid is None

        # Clean up
        db.session.delete(card_db)
        db.session.delete(driver_db)
        db.session.commit()
