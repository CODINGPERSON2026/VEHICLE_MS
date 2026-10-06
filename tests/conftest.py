import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.db_init import db
from models.user import User, Role
from models.device import Device, DeviceType, DeviceStatus, DeviceDirection
from models.vehicle import Vehicle, VehicleType, AuthStatus
from models.rfid import RFIDCard, CardStatus

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def admin_user(app):
    admin = User(
        username='admin',
        full_name='Master Admin',
        email='admin@gate.local',
        role=Role.ADMIN,
        is_active=True
    )
    admin.set_password('AdminPass123!')
    db.session.add(admin)
    db.session.commit()
    return admin

@pytest.fixture
def operator_user(app):
    operator = User(
        username='operator',
        full_name='Gate Guard',
        email='guard@gate.local',
        role=Role.GATE_OPERATOR,
        is_active=True
    )
    operator.set_password('GuardPass123!')
    db.session.add(operator)
    db.session.commit()
    return operator

@pytest.fixture
def test_device(app):
    device = Device(
        device_id='GATE_ENTRY_01',
        device_name='Main Ingress Reader',
        device_type=DeviceType.ESP32_RFID,
        gate='Main Gate',
        direction=DeviceDirection.ENTRY,
        status=DeviceStatus.ONLINE,
        is_active=True
    )
    device.set_api_key('test_api_key_123')
    db.session.add(device)
    db.session.commit()
    return device
