from datetime import datetime
from sqlalchemy.orm import foreign
from database.db_init import db

class MovementStatus:
    INSIDE = 'INSIDE'
    OUTSIDE = 'OUTSIDE'
    ENTRY_DENIED = 'ENTRY DENIED'
    EXIT_EXCEPTION = 'EXIT EXCEPTION'
    MANUAL_REVIEW = 'MANUAL REVIEW'
    
    CHOICES = [INSIDE, OUTSIDE, ENTRY_DENIED, EXIT_EXCEPTION, MANUAL_REVIEW]

class GateDirection:
    ENTRY = 'ENTRY'
    EXIT = 'EXIT'
    MANUAL = 'MANUAL'

class VehicleMovement(db.Model):
    __tablename__ = 'vehicle_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Vehicle, RFID and Trip Driver
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False, index=True)
    rfid_card_id = db.Column(db.Integer, db.ForeignKey('rfid_cards.id'), nullable=True, index=True)
    driver_id = db.Column(db.Integer, nullable=True, index=True)
    driver_name = db.Column(db.String(120), nullable=True) # Actual trip driver name

    # Entry details
    entry_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    entry_device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)
    entry_operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Exit details
    exit_time = db.Column(db.DateTime, nullable=True, index=True)
    exit_device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)
    exit_operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Metrics & State
    duration_seconds = db.Column(db.Integer, nullable=True) # in seconds
    status = db.Column(db.String(32), nullable=False, default=MovementStatus.INSIDE, index=True)
    direction = db.Column(db.String(16), nullable=False, default=GateDirection.ENTRY)
    
    # Manual Override & Exceptions
    is_manual = db.Column(db.Boolean, default=False, nullable=False)
    manual_reason = db.Column(db.String(255), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    
    # Idempotency / Event Reference
    entry_event_id = db.Column(db.String(64), nullable=True, index=True)
    exit_event_id = db.Column(db.String(64), nullable=True, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships to devices, operators and driver
    entry_device = db.relationship('Device', foreign_keys=[entry_device_id], backref='entry_movements')
    exit_device = db.relationship('Device', foreign_keys=[exit_device_id], backref='exit_movements')
    entry_operator = db.relationship('User', foreign_keys=[entry_operator_id], backref='entry_actions')
    exit_operator = db.relationship('User', foreign_keys=[exit_operator_id], backref='exit_actions')
    driver = db.relationship('Driver', primaryjoin='foreign(VehicleMovement.driver_id) == Driver.id', backref='movements')
    
    @property
    def formatted_duration(self):
        """Format duration nicely: e.g. 2h 15m 30s or calculating live if INSIDE."""
        if self.duration_seconds is not None:
            secs = self.duration_seconds
        elif self.status == MovementStatus.INSIDE and self.entry_time:
            secs = int((datetime.utcnow() - self.entry_time).total_seconds())
        else:
            return "N/A"
            
        if secs < 0:
            secs = 0
            
        hours = secs // 3600
        minutes = (secs % 3600) // 60
        seconds = secs % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def close_movement(self, exit_time=None, exit_device_id=None, exit_operator_id=None, exit_event_id=None, remarks=None):
        """Finalize exit for an INSIDE vehicle movement record."""
        self.exit_time = exit_time or datetime.utcnow()
        self.exit_device_id = exit_device_id
        self.exit_operator_id = exit_operator_id
        self.exit_event_id = exit_event_id
        self.status = MovementStatus.OUTSIDE
        if remarks:
            self.remarks = (self.remarks or "") + ("\n" if self.remarks else "") + remarks
        if self.entry_time and self.exit_time:
            self.duration_seconds = max(0, int((self.exit_time - self.entry_time).total_seconds()))

    def __repr__(self):
        return f"<VehicleMovement #{self.id} Vehicle:{self.vehicle_id} Status:{self.status}>"
