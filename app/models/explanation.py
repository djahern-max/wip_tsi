# app/models/explanation.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class CellExplanation(Base):
    __tablename__ = "cell_explanations"

    id = Column(Integer, primary_key=True, index=True)
    wip_snapshot_id = Column(Integer, ForeignKey("wip_snapshots.id"), nullable=False)
    field_name = Column(
        String(100), nullable=False, index=True
    )  # e.g., 'us_gaap_percent_completion'
    explanation = Column(Text, nullable=False)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    wip_snapshot = relationship("WIPSnapshot", back_populates="explanations")
    created_by_user = relationship("User")

    def __repr__(self):
        return f"<CellExplanation(field='{self.field_name}', wip_snapshot_id={self.wip_snapshot_id})>"


# Helper function to get all explainable fields
def get_explainable_fields():
    """
    Returns a list of all WIP fields that can have explanations attached
    """
    return [
        # Contract Section
        "current_month_original_contract_amount",
        "current_month_change_order_amount",
        "current_month_total_contract_amount",
        "prior_month_total_contract_amount",
        "current_vs_prior_contract_variance",
        # Cost Section
        "current_month_cost_to_date",
        "current_month_estimated_cost_to_complete",
        "current_month_estimated_final_cost",
        "prior_month_estimated_final_cost",
        "current_vs_prior_estimated_final_cost_variance",
        # US GAAP Section
        "us_gaap_percent_completion",
        "revenue_earned_to_date_us_gaap",
        "estimated_job_margin_to_date_us_gaap",
        "estimated_job_margin_to_date_percent_sales",
        # Job Margin Section
        "current_month_estimated_job_margin_at_completion",
        "prior_month_estimated_job_margin_at_completion",
        "current_vs_prior_estimated_job_margin",
        "current_month_estimated_job_margin_percent_sales",
        # Billing Section
        "current_month_revenue_billed_to_date",
        # WIP Adjustments
        "current_month_costs_in_excess_billings",
        "current_month_billings_excess_revenue",
        "current_month_addl_entry_required",
    ]
