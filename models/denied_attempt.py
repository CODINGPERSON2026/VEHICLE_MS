from datetime import datetime
from database.db_init import db

class DeniedReason:
    UNKNOWN_RFID = 'UNKNOWN_RFID'
    BLOCKED_CARD = 'BLOCKED_CARD'
    EXPIRED_CARD = 'EXPIRED_CARD'
    INACTIVE_CARD = 'INACTIVE_CARD'
    UNAUTHORIZED_VEHICLE = 'UNAUTHORIZED_VEHICLE'
    EXPIRED_AUTHORIZATION = 'EXPIRED_AUTHORIZATION'
    BLOCKED_VEHICLE = 'BLOCKED_VEHICLE'
    DUPLICATE_ENTRY = 'DUPLICATE_ENTRY'
    NO_ACTIVE_ENTRY = 'NO_ACTIVE_ENTRY'
    INVALID_DEVICE = 'INVALID_DEVICE'
    INVALID_DIRECTION = 'INVALID_DIRECTION'
    MANUAL_EXCEPTION = 'MANUAL_EXCEPTION'

    CHOICES = [
        UNKNOWN_RFID, BLOCKED_CARD, EXPIRED_CARD, INACTIVE_CARD,
        UNAUTHORIZED_VEHICLE, EXPIRED_AUTHORIZATION, BLOCKED_VEHICLE,
        DUPLICATE_ENTRY, NO_ACTIVE_ENTRY, INVALID_DEVICE, INVALID_DIRECTION,
        MANUAL_EXCEPTION
    ]

class DeniedAttempt(db.Model):
    __tablename__ = 'denied_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    rfid_uid = db.Column(db.String(32), nullable=True, index=True)
    vehicle_number = db.Column(db.String(32), nullable=True, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)
    direction = db.Column(db.String(16), nullable=False, default='ENTRY')
    reason = db.Column(db.String(64), nullable=False, index=True)
    event_id = db.Column(db.String(64), nullable=True, index=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    vehicle = db.relationship('Vehicle', foreign_keys=[vehicle_id], backref='denied_attempts')
    device = db.relationship('Device', foreign_keys=[device_id], backref='denied_attempts')
    operator = db.relationship('User', foreign_keys=[operator_id], backref='logged_denied_attempts')

    def __repr__(self):
        return f"<DeniedAttempt #{self.id} UID:{self.rfid_uid} Reason:{self.reason}>"
