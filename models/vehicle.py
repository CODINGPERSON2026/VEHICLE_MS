import re
from datetime import datetime, date
from database.db_init import db

class VehicleType:
    GYPSY = 'Gypsy'
    TWO_POINT_FIVE_TON = '2.5 Ton'
    ALS = 'ALS'
    LRV = 'LRV'
    HMV = 'HMV'
    TATA_YODHA = 'Tata YODHA'
    ALS_WB = 'ALS W/B'
    RE = 'R/E'
    FORTUNER = 'Fortuner'
    SCORPIO = 'Scorpio'

    CHOICES = [
        GYPSY,
        TWO_POINT_FIVE_TON,
        ALS,
        LRV,
        HMV,
        TATA_YODHA,
        ALS_WB,
        RE,
        FORTUNER,
        SCORPIO
    ]

class AuthStatus:
    AUTHORIZED = 'AUTHORIZED'
    NOT_AUTHORIZED = 'NOT AUTHORIZED'
    EXPIRED = 'EXPIRED'
    BLOCKED = 'BLOCKED'
    
    CHOICES = [AUTHORIZED, NOT_AUTHORIZED, EXPIRED, BLOCKED]

def normalize_plate(plate_str):
    """Normalize vehicle registration number: uppercase, alphanumeric only."""
    if not plate_str:
        return ""
    return re.sub(r'[^A-Z0-9]', '', plate_str.strip().upper())

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    vehicle_type = db.Column(db.String(32), nullable=False, default=VehicleType.GYPSY)
    issue_date = db.Column(db.Date, nullable=True)
    custodian_name = db.Column(db.String(120), nullable=True)
    armynumber = db.Column(db.String(64), nullable=True)
    mobile_number = db.Column(db.String(24), nullable=True)
    
    auth_status = db.Column(db.String(32), nullable=False, default=AuthStatus.AUTHORIZED, index=True)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True) # Soft delete
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Aliases for compatibility
    @property
    def driver_name(self):
        return self.custodian_name

    @driver_name.setter
    def driver_name(self, value):
        self.custodian_name = value

    @property
    def driver_id(self):
        return self.armynumber

    @driver_id.setter
    def driver_id(self, value):
        self.armynumber = value

    @property
    def army_number(self):
        return self.armynumber

    @army_number.setter
    def army_number(self, value):
        self.armynumber = value
    
    # Relationships
    rfid_cards = db.relationship('RFIDCard', backref='vehicle', lazy=True)
    movements = db.relationship('VehicleMovement', backref='vehicle', lazy='dynamic', cascade='all, delete-orphan')
    
    def is_currently_authorized(self):
        """Check if vehicle is authorized today."""
        if self.is_active is False:
            return False, "VEHICLE_DEACTIVATED"
        if self.auth_status == AuthStatus.BLOCKED:
            return False, "BLOCKED_VEHICLE"
        if self.auth_status == AuthStatus.NOT_AUTHORIZED:
            return False, "UNAUTHORIZED_VEHICLE"
        if self.auth_status == AuthStatus.EXPIRED:
            return False, "EXPIRED_AUTHORIZATION"
            
        return True, "AUTHORIZED"

    def get_active_outside_movement(self):
        """Get the current active OUTSIDE trip movement if any."""
        from models.movement import VehicleMovement, MovementStatus
        return VehicleMovement.query.filter_by(
            vehicle_id=self.id,
            status=MovementStatus.OUTSIDE
        ).order_by(VehicleMovement.exit_time.desc()).first()

    @property
    def is_currently_outside(self):
        """Returns True if vehicle is currently dispatched on an outside trip."""
        return self.get_active_outside_movement() is not None

    @property
    def is_currently_inside(self):
        """Returns True if vehicle is stationed in depot (not outside)."""
        return not self.is_currently_outside

    @property
    def primary_rfid_uid(self):
        """Returns primary assigned RFID card UID or '-'."""
        if self.rfid_cards and len(self.rfid_cards) > 0:
            return self.rfid_cards[0].uid
        return "-"

    def has_active_movement(self):
        """Check if vehicle currently has an open (INSIDE or OUTSIDE) movement."""
        from models.movement import VehicleMovement, MovementStatus
        return VehicleMovement.query.filter(
            VehicleMovement.vehicle_id == self.id,
            VehicleMovement.status.in_([MovementStatus.INSIDE, MovementStatus.OUTSIDE])
        ).first()

    def __repr__(self):
        return f"<Vehicle {self.registration_number} ({self.auth_status})>"
