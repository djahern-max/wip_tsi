# app/schemas/explanation.py
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ExplanationBase(BaseModel):
    field_name: str = Field(..., description="Name of the field being explained")
    explanation: str = Field(..., min_length=1, description="Explanation text")


class ExplanationCreate(ExplanationBase):
    """Schema for creating a new explanation"""

    pass


class ExplanationUpdate(BaseModel):
    """Schema for updating an explanation"""

    explanation: str = Field(..., min_length=1, description="Updated explanation text")


class ExplanationResponse(ExplanationBase):
    """Schema for returning explanation data"""

    id: int
    wip_snapshot_id: int
    created_by: int
    created_by_name: Optional[str] = None  # Will be populated from user relationship
    created_by_first_name: Optional[str] = None  # ADD THIS
    created_by_last_name: Optional[str] = None  # ADD THIS
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WIPWithExplanations(BaseModel):
    """Schema for WIP data with explanation indicators"""

    wip_data: dict  # The actual WIP snapshot data
    explanations: dict[str, ExplanationResponse]  # field_name -> explanation mapping

    # Helper to check if a field has an explanation
    def has_explanation(self, field_name: str) -> bool:
        return field_name in self.explanations


# Field display names for UI
FIELD_DISPLAY_NAMES = {
    # Contract Section
    "current_month_original_contract_amount": "Original Contract Amount",
    "current_month_change_order_amount": "Change Order Amount",
    "current_month_total_contract_amount": "Total Contract Amount",
    "prior_month_total_contract_amount": "Prior Month Contract Amount",
    "current_vs_prior_contract_variance": "Contract Variance",
    # Cost Section
    "current_month_cost_to_date": "Cost to Date",
    "current_month_estimated_cost_to_complete": "Estimated Cost to Complete",
    "current_month_estimated_final_cost": "Estimated Final Cost",
    "prior_month_estimated_final_cost": "Prior Month Final Cost",
    "current_vs_prior_estimated_final_cost_variance": "Final Cost Variance",
    # US GAAP Section
    "us_gaap_percent_completion": "US GAAP % Completion",
    "revenue_earned_to_date_us_gaap": "Revenue Earned to Date",
    "estimated_job_margin_to_date_us_gaap": "Job Margin to Date (US GAAP)",
    "estimated_job_margin_to_date_percent_sales": "Job Margin to Date %",
    # Job Margin Section
    "current_month_estimated_job_margin_at_completion": "Estimated Job Margin at Completion",
    "prior_month_estimated_job_margin_at_completion": "Prior Month Job Margin",
    "current_vs_prior_estimated_job_margin": "Job Margin Variance",
    "current_month_estimated_job_margin_percent_sales": "Job Margin % of Sales",
    # Billing Section
    "current_month_revenue_billed_to_date": "Revenue Billed to Date",
    # WIP Adjustments
    "current_month_costs_in_excess_billings": "Costs in Excess of Billings",
    "current_month_billings_excess_revenue": "Billings in Excess of Revenue",
    "current_month_addl_entry_required": "Additional Entry Required",
}
