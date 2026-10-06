from datetime import datetime
from database.db_init import db

class Driver(db.Model):
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    armynumber = db.Column(db.String(64), nullable=True, index=True)
    driver_rank = db.Column(db.String(64), nullable=True) # DriveRank
    company = db.Column(db.String(64), nullable=True)
    section = db.Column(db.String(64), nullable=True)
    hill_driving = db.Column(db.String(10), default='NO', nullable=False) # 'YES' or 'NO'
    auth_status = db.Column(db.String(32), default='NOT AUTHORIZED', nullable=False) # 'AUTHORIZED' or 'NOT AUTHORIZED'
    authorized_vehicle_types = db.Column(db.Text, nullable=True) # Comma-separated authorized vehicle types

    license_number = db.Column(db.String(64), nullable=True)
    mobile_number = db.Column(db.String(24), nullable=True)
    designation = db.Column(db.String(64), default='Staff Driver', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    remarks = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @property
    def driverank(self):
        return self.driver_rank

    @driverank.setter
    def driverank(self, val):
        self.driver_rank = val

    @property
    def employee_id(self):
        """Compatibility alias for armynumber."""
        return self.armynumber

    @employee_id.setter
    def employee_id(self, val):
        self.armynumber = val

    @property
    def authorized_types_list(self):
        if self.authorized_vehicle_types:
            return [t.strip() for t in self.authorized_vehicle_types.split(',') if t.strip()]
        return []
    
    def __repr__(self):
        return f"<Driver {self.name} ({self.armynumber or 'No Army No'})>"
