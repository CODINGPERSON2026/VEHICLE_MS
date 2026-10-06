from datetime import datetime
from database.db_init import db

class CameraRole:
    ENTRY = 'ENTRY'
    EXIT = 'EXIT'
    CHOICES = [ENTRY, EXIT]

class ANPRVerificationStatus:
    MATCH = 'MATCH'
    MISMATCH = 'MISMATCH'
    LOW_CONFIDENCE = 'LOW_CONFIDENCE'
    NO_RFID_COMPARISON = 'NO_RFID_COMPARISON'

class CameraConfig(db.Model):
    __tablename__ = 'camera_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.String(64), unique=True, nullable=False, index=True) # e.g. CAM_ENTRY_01
    camera_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(16), nullable=False, default=CameraRole.ENTRY)
    rtsp_url = db.Column(db.String(255), nullable=True)
    resolution = db.Column(db.String(32), default='1920x1080')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    anpr_events = db.relationship('ANPREvent', backref='camera', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<CameraConfig {self.camera_id} ({self.role})>"

class ANPREvent(db.Model):
    __tablename__ = 'anpr_events'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('camera_configs.id'), nullable=True)
    captured_plate = db.Column(db.String(32), nullable=False, index=True)
    confidence = db.Column(db.Float, nullable=False, default=95.0)
    matched_vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=True)
    rfid_event_id = db.Column(db.String(64), nullable=True, index=True)
    verification_status = db.Column(db.String(32), default=ANPRVerificationStatus.NO_RFID_COMPARISON)
    snapshot_path = db.Column(db.String(255), nullable=True)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationship
    matched_vehicle = db.relationship('Vehicle', foreign_keys=[matched_vehicle_id], backref='anpr_events')

    def __repr__(self):
        return f"<ANPREvent {self.captured_plate} ({self.confidence}%) Status:{self.verification_status}>"
