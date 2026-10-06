import secrets
import hashlib
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_init import db

class DeviceType:
    ESP32_RFID = 'ESP32 RFID'
    ANPR_CAMERA = 'ANPR Camera'
    BARRIER_CONTROLLER = 'Barrier Controller'
    
    CHOICES = [ESP32_RFID, ANPR_CAMERA, BARRIER_CONTROLLER]

class DeviceStatus:
    ONLINE = 'ONLINE'
    OFFLINE = 'OFFLINE'
    DISABLED = 'DISABLED'
    ERROR = 'ERROR'
    
    CHOICES = [ONLINE, OFFLINE, DISABLED, ERROR]

class DeviceDirection:
    ENTRY = 'ENTRY'
    EXIT = 'EXIT'
    BOTH = 'BOTH'
    
    CHOICES = [ENTRY, EXIT, BOTH]

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(64), unique=True, nullable=False, index=True) # e.g. GATE_ENTRY_01
    device_name = db.Column(db.String(120), nullable=False)
    device_type = db.Column(db.String(32), nullable=False, default=DeviceType.ESP32_RFID)
    gate = db.Column(db.String(64), nullable=False, default='Main Gate')
    direction = db.Column(db.String(16), nullable=False, default=DeviceDirection.ENTRY)
    ip_address = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(16), nullable=False, default=DeviceStatus.OFFLINE)
    
    last_seen = db.Column(db.DateTime, nullable=True)
    last_event = db.Column(db.String(255), nullable=True)
    firmware_version = db.Column(db.String(32), default='v1.0.0')
    
    api_key_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Event logs
    events = db.relationship('DeviceEvent', backref='device', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_api_key(self, raw_key: str):
        """Hash and save device API key."""
        self.api_key_hash = generate_password_hash(raw_key)
        
    def check_api_key(self, raw_key: str) -> bool:
        """Verify device API key."""
        if not self.api_key_hash or not raw_key:
            return False
        return check_password_hash(self.api_key_hash, raw_key)
    
    @staticmethod
    def generate_api_key():
        """Generate a cryptographically secure random API key."""
        return "dev_" + secrets.token_urlsafe(24)

    def is_online(self, timeout_seconds=35):
        """Evaluate if device has sent a heartbeat or scan recently."""
        if not self.is_active or self.status == DeviceStatus.DISABLED:
            return False
        if not self.last_seen:
            return False
        return (datetime.utcnow() - self.last_seen) < timedelta(seconds=timeout_seconds)

    def update_heartbeat(self, ip_address=None, firmware_version=None):
        """Update last seen timestamp, IP, and status."""
        self.last_seen = datetime.utcnow()
        if self.status != DeviceStatus.DISABLED:
            self.status = DeviceStatus.ONLINE
        if ip_address:
            self.ip_address = ip_address
        if firmware_version:
            self.firmware_version = firmware_version

    def __repr__(self):
        return f"<Device {self.device_id} ({self.device_type} - {self.status})>"

class DeviceEvent(db.Model):
    __tablename__ = 'device_events'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False, index=True)
    event_type = db.Column(db.String(32), nullable=False) # SCAN, HEARTBEAT, ERROR, STATUS_CHANGE
    event_id = db.Column(db.String(64), nullable=True, index=True) # Idempotency token
    raw_payload = db.Column(db.Text, nullable=True)
    response_summary = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<DeviceEvent {self.event_type} on Device #{self.device_id}>"
