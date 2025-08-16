from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    job_number: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Job number (e.g., '2215', '2305-1')",
    )
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    original_contract_amount: Optional[Decimal] = Field(
        None, description="Original contract amount"
    )
    is_active: bool = Field(True, description="Whether project is active")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project"""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    original_contract_amount: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """Schema for returning project data"""

    id: int
    created_at: datetime
    updated_at: datetime

    # Additional computed fields
    total_wip_snapshots: Optional[int] = Field(
        None, description="Number of WIP snapshots for this project"
    )
    latest_report_date: Optional[datetime] = Field(
        None, description="Most recent WIP report date"
    )

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for listing projects with summary info"""

    id: int
    job_number: str
    name: str
    original_contract_amount: Optional[Decimal] = None
    is_active: bool
    total_wip_snapshots: int = 0
    latest_report_date: Optional[datetime] = None

    class Config:
        from_attributes = True
