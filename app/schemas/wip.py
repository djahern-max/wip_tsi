# app/schemas/wip.py
from typing import Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field


class WIPSnapshotBase(BaseModel):
    """Base WIP snapshot schema with only user-input fields"""

    job_number: str = Field(..., description="Job number")
    report_date: date = Field(..., description="Report date (e.g., 2025-07-31)")

    # USER INPUT FIELDS (what users actually enter)
    current_month_original_contract_amount: Optional[Decimal] = Field(
        None, description="Original contract amount"
    )
    current_month_change_order_amount: Optional[Decimal] = Field(
        None, description="Change order amount"
    )
    current_month_cost_to_date: Optional[Decimal] = Field(
        None, description="Cost to date"
    )
    current_month_estimated_cost_to_complete: Optional[Decimal] = Field(
        None, description="Estimated cost to complete"
    )
    current_month_revenue_billed_to_date: Optional[Decimal] = Field(
        None, description="Revenue billed to date"
    )
    current_month_addl_entry_required: Optional[Decimal] = Field(
        None, description="Additional entry required"
    )


class WIPSnapshotCreate(WIPSnapshotBase):
    """Schema for creating a new WIP snapshot"""

    project_id: int = Field(..., description="Project ID")


class WIPSnapshotUpdate(BaseModel):
    """Schema for updating a WIP snapshot - only input fields can be updated"""

    current_month_original_contract_amount: Optional[Decimal] = None
    current_month_change_order_amount: Optional[Decimal] = None
    current_month_cost_to_date: Optional[Decimal] = None
    current_month_estimated_cost_to_complete: Optional[Decimal] = None
    current_month_revenue_billed_to_date: Optional[Decimal] = None
    current_month_addl_entry_required: Optional[Decimal] = None


class WIPSnapshotResponse(BaseModel):
    """Schema for returning complete WIP snapshot data (including calculated fields)"""

    id: int
    project_id: int
    job_number: str
    report_date: date

    # Input fields
    current_month_original_contract_amount: Optional[Decimal] = None
    current_month_change_order_amount: Optional[Decimal] = None
    current_month_cost_to_date: Optional[Decimal] = None
    current_month_estimated_cost_to_complete: Optional[Decimal] = None
    current_month_revenue_billed_to_date: Optional[Decimal] = None
    current_month_addl_entry_required: Optional[Decimal] = None

    # CALCULATED CONTRACT FIELDS
    current_month_total_contract_amount: Optional[Decimal] = None
    prior_month_total_contract_amount: Optional[Decimal] = None
    current_vs_prior_contract_variance: Optional[Decimal] = None

    # CALCULATED COST FIELDS
    current_month_estimated_final_cost: Optional[Decimal] = None
    prior_month_estimated_final_cost: Optional[Decimal] = None
    current_vs_prior_estimated_final_cost_variance: Optional[Decimal] = None

    # CALCULATED US GAAP FIELDS
    us_gaap_percent_completion: Optional[Decimal] = None
    revenue_earned_to_date_us_gaap: Optional[Decimal] = None
    estimated_job_margin_to_date_us_gaap: Optional[Decimal] = None
    estimated_job_margin_to_date_percent_sales: Optional[Decimal] = None

    # CALCULATED JOB MARGIN FIELDS
    current_month_estimated_job_margin_at_completion: Optional[Decimal] = None
    prior_month_estimated_job_margin_at_completion: Optional[Decimal] = None
    current_vs_prior_estimated_job_margin: Optional[Decimal] = None
    current_month_estimated_job_margin_percent_sales: Optional[Decimal] = None

    # CALCULATED WIP ADJUSTMENTS
    current_month_costs_in_excess_billings: Optional[Decimal] = None
    current_month_billings_excess_revenue: Optional[Decimal] = None

    # Project info (from relationship)
    project_name: Optional[str] = Field(None, description="Project name for display")

    class Config:
        from_attributes = True


class WIPComparisonResponse(BaseModel):
    """Schema for month-to-month comparison"""

    project_id: int
    job_number: str
    project_name: str
    current_month: Optional[WIPSnapshotResponse] = None
    previous_month: Optional[WIPSnapshotResponse] = None

    # Change indicators
    has_significant_changes: bool = False
    contract_amount_change: Optional[Decimal] = None
    estimated_final_cost_change: Optional[Decimal] = None
    job_margin_change: Optional[Decimal] = None
    percent_completion_change: Optional[Decimal] = None


class WIPInputValidation(BaseModel):
    """Schema for validating WIP input before calculations"""

    errors: list[str] = []
    warnings: list[str] = []
    is_valid: bool = True

    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        self.warnings.append(message)
