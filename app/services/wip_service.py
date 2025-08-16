from typing import Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from app.models.wip_snapshot import WIPSnapshot
from app.models.project import Project
from app.services.wip_calculations import WIPCalculator
from app.schemas.wip import WIPSnapshotCreate, WIPSnapshotUpdate


class WIPService:
    """Service for handling WIP operations with automatic calculations"""

    def __init__(self, db: Session):
        self.db = db
        self.calculator = WIPCalculator()

    def get_prior_month_data(
        self, project_id: int, current_date: date
    ) -> Optional[WIPSnapshot]:
        """Get the most recent WIP snapshot before the current date for comparison"""
        return (
            self.db.query(WIPSnapshot)
            .filter(
                WIPSnapshot.project_id == project_id,
                WIPSnapshot.report_date < current_date,
            )
            .order_by(WIPSnapshot.report_date.desc())
            .first()
        )

    def create_wip_snapshot(
        self, wip_data: WIPSnapshotCreate, created_by_user_id: int
    ) -> WIPSnapshot:
        """Create a new WIP snapshot with automatic calculations"""

        # Get prior month data for comparisons
        prior_month = self.get_prior_month_data(
            wip_data.project_id, wip_data.report_date
        )

        # Prepare input data including prior month values
        input_data = wip_data.dict(exclude_unset=True)

        # Add prior month data for calculations
        if prior_month:
            input_data.update(
                {
                    "prior_month_total_contract_amount": prior_month.current_month_total_contract_amount,
                    "prior_month_estimated_final_cost": prior_month.current_month_estimated_final_cost,
                    "prior_month_estimated_job_margin_at_completion": prior_month.current_month_estimated_job_margin_at_completion,
                }
            )

        # Calculate all dependent fields
        calculated_data = self.calculator.calculate_all_fields(input_data)

        # Create the WIP snapshot
        db_wip = WIPSnapshot(**calculated_data, created_by=created_by_user_id)

        self.db.add(db_wip)
        self.db.commit()
        self.db.refresh(db_wip)

        return db_wip

    def update_wip_snapshot(
        self,
        wip_snapshot: WIPSnapshot,
        update_data: WIPSnapshotUpdate,
        updated_by_user_id: int,
    ) -> WIPSnapshot:
        """Update a WIP snapshot with automatic recalculations"""

        # Get current data and merge with updates
        current_data = {
            "project_id": wip_snapshot.project_id,
            "report_date": wip_snapshot.report_date,
            "job_number": wip_snapshot.job_number,
            "current_month_original_contract_amount": wip_snapshot.current_month_original_contract_amount,
            "current_month_change_order_amount": wip_snapshot.current_month_change_order_amount,
            "current_month_cost_to_date": wip_snapshot.current_month_cost_to_date,
            "current_month_estimated_cost_to_complete": wip_snapshot.current_month_estimated_cost_to_complete,
            "current_month_revenue_billed_to_date": wip_snapshot.current_month_revenue_billed_to_date,
            "current_month_addl_entry_required": wip_snapshot.current_month_addl_entry_required,
        }

        # Apply updates
        update_dict = update_data.dict(exclude_unset=True)
        current_data.update(update_dict)

        # Get prior month data for comparisons
        prior_month = self.get_prior_month_data(
            wip_snapshot.project_id, wip_snapshot.report_date
        )
        if prior_month:
            current_data.update(
                {
                    "prior_month_total_contract_amount": prior_month.current_month_total_contract_amount,
                    "prior_month_estimated_final_cost": prior_month.current_month_estimated_final_cost,
                    "prior_month_estimated_job_margin_at_completion": prior_month.current_month_estimated_job_margin_at_completion,
                }
            )

        # Recalculate all fields
        calculated_data = self.calculator.calculate_all_fields(current_data)

        # Update the record
        for field, value in calculated_data.items():
            if hasattr(wip_snapshot, field):
                setattr(wip_snapshot, field, value)

        # Update metadata
        wip_snapshot.created_by = updated_by_user_id  # Track who last updated

        self.db.commit()
        self.db.refresh(wip_snapshot)

        return wip_snapshot

    def get_month_comparison(
        self, project_id: int, current_date: date, prior_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get month-to-month comparison data"""

        current_wip = (
            self.db.query(WIPSnapshot)
            .filter(
                WIPSnapshot.project_id == project_id,
                WIPSnapshot.report_date == current_date,
            )
            .first()
        )

        if prior_date:
            prior_wip = (
                self.db.query(WIPSnapshot)
                .filter(
                    WIPSnapshot.project_id == project_id,
                    WIPSnapshot.report_date == prior_date,
                )
                .first()
            )
        else:
            prior_wip = self.get_prior_month_data(project_id, current_date)

        return {
            "current_month": current_wip,
            "prior_month": prior_wip,
            "has_changes": self._detect_significant_changes(current_wip, prior_wip),
        }

    def _detect_significant_changes(
        self,
        current: Optional[WIPSnapshot],
        prior: Optional[WIPSnapshot],
        threshold_percent: float = 5.0,
    ) -> Dict[str, bool]:
        """Detect significant changes between months"""

        if not current or not prior:
            return {"has_significant_changes": False}

        changes = {}

        # Check key fields for significant changes
        key_fields = [
            "current_month_total_contract_amount",
            "current_month_estimated_final_cost",
            "current_month_estimated_job_margin_at_completion",
            "us_gaap_percent_completion",
        ]

        for field in key_fields:
            current_val = getattr(current, field)
            prior_val = getattr(
                prior, field.replace("current_month_", "current_month_")
            )

            if current_val and prior_val and prior_val != 0:
                change_percent = abs((current_val - prior_val) / prior_val * 100)
                changes[f"{field}_changed"] = change_percent > threshold_percent

        changes["has_significant_changes"] = any(changes.values())

        return changes
