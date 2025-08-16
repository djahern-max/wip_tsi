from sqlalchemy import Boolean, Column, Integer, String, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    job_number = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    original_contract_amount = Column(Numeric(15, 2))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    wip_snapshots = relationship(
        "WIPSnapshot", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Project(job_number='{self.job_number}', name='{self.name}')>"
