# app/models/wip_snapshot.py
from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class WIPSnapshot(Base):
    __tablename__ = "wip_snapshots"

    # Primary identifiers
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    report_date = Column(Date, nullable=False, index=True)  # e.g., 2025-07-31

    # Basic project info
    job_number = Column(String(20), index=True)  # From Job # column

    # CONTRACT SECTION
    # Current month contract data
    current_month_original_contract_amount = Column(
        Numeric(15, 2), comment="Current month original contract amount"
    )
    current_month_change_order_amount = Column(
        Numeric(15, 2), comment="Current month change order amount"
    )
    current_month_total_contract_amount = Column(
        Numeric(15, 2), comment="Current month total contract amount"
    )

    # Prior month contract data for comparison
    prior_month_total_contract_amount = Column(
        Numeric(15, 2), comment="Prior month total contract amount"
    )

    # Contract variance (current vs prior month)
    current_vs_prior_contract_variance = Column(
        Numeric(15, 2), comment="Current month vs prior month contract variance"
    )

    # COST SECTION
    current_month_cost_to_date = Column(
        Numeric(15, 2), comment="Current month cost to date"
    )
    current_month_estimated_cost_to_complete = Column(
        Numeric(15, 2), comment="Current month estimated cost to complete"
    )

    # Estimated final costs
    current_month_estimated_final_cost = Column(
        Numeric(15, 2), comment="Current month estimated final cost"
    )
    prior_month_estimated_final_cost = Column(
        Numeric(15, 2), comment="Prior month estimated final cost"
    )
    current_vs_prior_estimated_final_cost_variance = Column(
        Numeric(15, 2), comment="Current vs prior month estimated final cost variance"
    )

    # US GAAP SECTION (Revenue Recognition)
    us_gaap_percent_completion = Column(
        Numeric(5, 2), comment="US GAAP % of Completion"
    )
    revenue_earned_to_date_us_gaap = Column(
        Numeric(15, 2), comment="Revenue Earned to Date US GAAP % of Completion"
    )
    estimated_job_margin_to_date_us_gaap = Column(
        Numeric(15, 2),
        comment="Estimated Job Margin to Date Using US GAAP % of Completion",
    )
    estimated_job_margin_to_date_percent_sales = Column(
        Numeric(5, 2), comment="Estimated Job Margin to Date as a % of Sales"
    )

    # JOB MARGIN SECTION
    current_month_estimated_job_margin_at_completion = Column(
        Numeric(15, 2), comment="Current month estimated job margin at completion"
    )
    prior_month_estimated_job_margin_at_completion = Column(
        Numeric(15, 2), comment="Prior month estimated job margin at completion"
    )
    current_vs_prior_estimated_job_margin = Column(
        Numeric(15, 2), comment="Current vs prior month estimated job margin variance"
    )
    current_month_estimated_job_margin_percent_sales = Column(
        Numeric(5, 2), comment="Current month estimated job margin as % of sales"
    )

    # BILLING SECTION
    current_month_revenue_billed_to_date = Column(
        Numeric(15, 2), comment="Current month revenue billed to date"
    )

    # WIP ADJUSTMENTS SECTION (with accounting entries)
    current_month_costs_in_excess_billings = Column(
        Numeric(15, 2), comment="Current month costs in excess of billings"
    )
    current_month_billings_excess_revenue = Column(
        Numeric(15, 2), comment="Current month billings in excess of revenue"
    )
    current_month_addl_entry_required = Column(
        Numeric(15, 2), comment="Current month additional entry required"
    )

    # BILLING SECTION
    billed_to_date = Column(Numeric(15, 2), comment="Current month billed to date")

    # WIP ADJUSTMENTS SECTION
    costs_in_excess_of_billings = Column(
        Numeric(15, 2), comment="Costs in Excess of Billings"
    )
    billings_in_excess_of_costs = Column(
        Numeric(15, 2), comment="Billings in Excess of Costs"
    )

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project = relationship("Project", back_populates="wip_snapshots")
    explanations = relationship(
        "CellExplanation", back_populates="wip_snapshot", cascade="all, delete-orphan"
    )
    created_by_user = relationship("User")

    # Ensure unique project per report date
    __table_args__ = (
        UniqueConstraint("project_id", "report_date", name="uq_project_report_date"),
    )

    def __repr__(self):
        return f"<WIPSnapshot(job_number='{self.job_number}', report_date='{self.report_date}')>"


# Helper class to track field definitions as we build them
class WIPFieldDefinition(Base):
    """
    This table will help us track what each field means as we build the model
    """

    __tablename__ = "wip_field_definitions"

    id = Column(Integer, primary_key=True)
    field_name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)  # Human readable name
    description = Column(Text)  # What this field represents
    column_position = Column(Integer)  # Position in original spreadsheet
    data_type = Column(String(50))  # numeric, text, percentage, etc.
    is_calculated = Column(
        String(10), default=False
    )  # True if this is a calculated field
    calculation_formula = Column(Text)  # If calculated, what's the formula

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<WIPFieldDefinition(field_name='{self.field_name}', display_name='{self.display_name}')>"
