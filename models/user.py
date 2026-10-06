from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from database.db_init import db

class Role:
    ADMIN = 'ADMIN'
    GATE_OPERATOR = 'GATE OPERATOR'
    REPORT_VIEWER = 'REPORT VIEWER'
    MAINGATE = 'MAINGATE'
    
    CHOICES = [ADMIN, GATE_OPERATOR, REPORT_VIEWER, MAINGATE]

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(32), nullable=False, default=Role.GATE_OPERATOR)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Audit log relationship
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role == Role.ADMIN
    
    @property
    def is_operator(self):
        return self.role in [Role.ADMIN, Role.GATE_OPERATOR, Role.MAINGATE]
    
    @property
    def is_maingate(self):
        return self.role == Role.MAINGATE
    
    @property
    def can_view_reports(self):
        return self.role in [Role.ADMIN, Role.GATE_OPERATOR, Role.REPORT_VIEWER]

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
