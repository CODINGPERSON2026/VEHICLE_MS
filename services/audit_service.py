from datetime import datetime
from flask import request, has_request_context
from flask_login import current_user
from database.db_init import db
from models.audit import AuditLog

def log_audit(action: str, description: str, related_vehicle: str = None, related_device: str = None, user=None):
    """
    Log an event into the audit trail.
    Safe to call with or without an active Flask request context.
    """
    user_id = None
    username = 'SYSTEM'
    ip_address = '127.0.0.1'
    
    if user:
        user_id = user.id
        username = user.username
    elif has_request_context():
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
            username = current_user.username
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
        if ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()

    audit_entry = AuditLog(
        timestamp=datetime.utcnow(),
        user_id=user_id,
        username=username,
        action=action,
        related_vehicle=related_vehicle,
        related_device=related_device,
        description=description,
        ip_address=ip_address
    )
    
    try:
        db.session.add(audit_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Keep silent to prevent breaking primary action, but log to stderr if needed
        print(f"[AUDIT LOG ERROR] Failed to save audit log: {e}")
