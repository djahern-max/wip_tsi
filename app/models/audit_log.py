from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    field_name = Column(String(50))
    old_value = Column(Text)
    new_value = Column(Text)
    action = Column(String(20), nullable=False)  # 'INSERT', 'UPDATE', 'DELETE'
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<AuditLog(table='{self.table_name}', action='{self.action}', user_id={self.user_id})>"
