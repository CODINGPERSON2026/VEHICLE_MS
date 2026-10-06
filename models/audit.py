from datetime import datetime
from database.db_init import db

class AuditAction:
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    LOGIN_FAILED = 'LOGIN_FAILED'
    
    VEHICLE_CREATE = 'VEHICLE_CREATE'
    VEHICLE_UPDATE = 'VEHICLE_UPDATE'
    VEHICLE_DEACTIVATE = 'VEHICLE_DEACTIVATE'
    VEHICLE_REACTIVATE = 'VEHICLE_REACTIVATE'
    
    DRIVER_CREATE = 'DRIVER_CREATE'
    DRIVER_UPDATE = 'DRIVER_UPDATE'
    DRIVER_DELETE = 'DRIVER_DELETE'
    
    RFID_ASSIGN = 'RFID_ASSIGN'
    RFID_REASSIGN = 'RFID_REASSIGN'
    RFID_STATUS_CHANGE = 'RFID_STATUS_CHANGE'
    RFID_DEACTIVATE = 'RFID_DEACTIVATE'
    RFID_BLOCK = 'RFID_BLOCK'
    
    VEHICLE_ENTRY = 'VEHICLE_ENTRY'
    VEHICLE_EXIT = 'VEHICLE_EXIT'
    DENIED_ATTEMPT = 'DENIED_ATTEMPT'
    MANUAL_OVERRIDE = 'MANUAL_OVERRIDE'
    
    DEVICE_REGISTER = 'DEVICE_REGISTER'
    DEVICE_UPDATE = 'DEVICE_UPDATE'
    DEVICE_KEY_ROTATE = 'DEVICE_KEY_ROTATE'
    
    CAMERA_CONFIG = 'CAMERA_CONFIG'
    SETTINGS_UPDATE = 'SETTINGS_UPDATE'
    DATABASE_BACKUP = 'DATABASE_BACKUP'
    DATABASE_RESTORE = 'DATABASE_RESTORE'
    DEMO_MODE_TOGGLE = 'DEMO_MODE_TOGGLE'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    username = db.Column(db.String(64), nullable=False, default='SYSTEM')
    action = db.Column(db.String(64), nullable=False, index=True)
    related_vehicle = db.Column(db.String(64), nullable=True)
    related_device = db.Column(db.String(64), nullable=True)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f"<AuditLog #{self.id} [{self.action}] by {self.username}>"
