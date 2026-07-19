from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

def write_audit_log(db: Session, actor_user_id, action: str, resource_id: str = None, ip_address: str = None):
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        resource_id=resource_id,
        ip_address=ip_address,
    )
    db.add(entry)