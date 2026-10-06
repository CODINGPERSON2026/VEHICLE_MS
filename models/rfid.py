import re
from datetime import datetime, date
from database.db_init import db

class CardStatus:
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    LOST = 'LOST'
    BLOCKED = 'BLOCKED'
    EXPIRED = 'EXPIRED'
    
    CHOICES = [ACTIVE, INACTIVE, LOST, BLOCKED, EXPIRED]

def normalize_uid(uid_str):
    """Normalize RFID UID: uppercase alphanumeric hex without colons or spaces."""
    if not uid_str:
        return ""
    return re.sub(r'[^A-Fa-f0-9]', '', uid_str.strip()).upper()

class RFIDCard(db.Model):
    __tablename__ = 'rfid_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(32), unique=True, nullable=False, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=True, index=True)
    card_status = db.Column(db.String(32), nullable=False, default=CardStatus.ACTIVE, index=True)
    assigned_date = db.Column(db.Date, default=date.today, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Movements associated with this card
    movements = db.relationship('VehicleMovement', backref='rfid_card', lazy='dynamic')
    
    def is_valid(self):
        """Check if card itself is active and unexpired."""
        if self.card_status == CardStatus.BLOCKED:
            return False, "BLOCKED_CARD"
        if self.card_status == CardStatus.LOST:
            return False, "LOST_CARD"
        if self.card_status == CardStatus.INACTIVE:
            return False, "INACTIVE_CARD"
        if self.card_status == CardStatus.EXPIRED:
            return False, "EXPIRED_CARD"
            
        today = date.today()
        if self.expiry_date and today > self.expiry_date:
            return False, "EXPIRED_CARD"
            
        return True, "ACTIVE"

    def __repr__(self):
        return f"<RFIDCard {self.uid} (Vehicle #{self.vehicle_id}, Status: {self.card_status})>"
