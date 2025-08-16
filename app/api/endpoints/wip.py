from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.dependencies import get_db, get_current_user, get_admin_user
from app.models.user import User
from app.models.project import Project
from app.models.wip_snapshot import WIPSnapshot
from app.services.wip_service import WIPService
from app.schemas.wip import (
    WIPSnapshotCreate,
    WIPSnapshotUpdate,
    WIPSnapshotResponse,
    WIPComparisonResponse,
)

router = APIRouter()


@router.get("/", response_model=List[WIPSnapshotResponse])
def list_wip_snapshots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    report_date: Optional[date] = Query(
        None, description="Filter by specific report date"
    ),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    job_number: Optional[str] = Query(None, description="Filter by job number"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List WIP snapshots with optional filters"""

    query = db.query(WIPSnapshot, Project.name.label("project_name")).join(Project)

    # Apply filters
    if report_date:
        query = query.filter(WIPSnapshot.report_date == report_date)
    if project_id:
        query = query.filter(WIPSnapshot.project_id == project_id)
    if job_number:
        query = query.filter(WIPSnapshot.job_number.ilike(f"%{job_number}%"))

    # Order by most recent first, then by job number
    wip_snapshots = (
        query.order_by(desc(WIPSnapshot.report_date), WIPSnapshot.job_number)
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Convert to response format
    result = []
    for wip, project_name in wip_snapshots:
        wip_response = WIPSnapshotResponse.from_orm(wip)
        wip_response.project_name = project_name
        result.append(wip_response)

    return result


@router.get("/latest", response_model=List[WIPSnapshotResponse])
def get_latest_wip_snapshots(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get the most recent WIP snapshot for each project"""

    # Subquery to get the latest report date for each project
    latest_dates = (
        db.query(
            WIPSnapshot.project_id,
            func.max(WIPSnapshot.report_date).label("latest_date"),
        )
        .group_by(WIPSnapshot.project_id)
        .subquery()
    )

    # Get WIP snapshots with the latest dates
    wip_snapshots = (
        db.query(WIPSnapshot, Project.name.label("project_name"))
        .join(Project)
        .join(
            latest_dates,
            (WIPSnapshot.project_id == latest_dates.c.project_id)
            & (WIPSnapshot.report_date == latest_dates.c.latest_date),
        )
        .order_by(WIPSnapshot.job_number)
        .all()
    )

    result = []
    for wip, project_name in wip_snapshots:
        wip_response = WIPSnapshotResponse.from_orm(wip)
        wip_response.project_name = project_name
        result.append(wip_response)

    return result


@router.get("/{wip_id}", response_model=WIPSnapshotResponse)
def get_wip_snapshot(
    wip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific WIP snapshot by ID"""

    wip_data = (
        db.query(WIPSnapshot, Project.name.label("project_name"))
        .join(Project)
        .filter(WIPSnapshot.id == wip_id)
        .first()
    )

    if not wip_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="WIP snapshot not found"
        )

    wip, project_name = wip_data
    wip_response = WIPSnapshotResponse.from_orm(wip)
    wip_response.project_name = project_name

    return wip_response


@router.post(
    "/", response_model=WIPSnapshotResponse, status_code=status.HTTP_201_CREATED
)
def create_wip_snapshot(
    wip_data: WIPSnapshotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Only admins can create
):
    """Create a new WIP snapshot with automatic calculations"""

    # Check if project exists
    project = db.query(Project).filter(Project.id == wip_data.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Check if WIP snapshot already exists for this project and date
    existing_wip = (
        db.query(WIPSnapshot)
        .filter(
            WIPSnapshot.project_id == wip_data.project_id,
            WIPSnapshot.report_date == wip_data.report_date,
        )
        .first()
    )

    if existing_wip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"WIP snapshot already exists for project {project.job_number} on {wip_data.report_date}",
        )

    # Create WIP snapshot using the service (includes calculations)
    wip_service = WIPService(db)
    wip_snapshot = wip_service.create_wip_snapshot(wip_data, current_user.id)

    # Return with project name
    wip_response = WIPSnapshotResponse.from_orm(wip_snapshot)
    wip_response.project_name = project.name

    return wip_response


@router.put("/{wip_id}", response_model=WIPSnapshotResponse)
def update_wip_snapshot(
    wip_id: int,
    wip_update: WIPSnapshotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Only admins can update
):
    """Update a WIP snapshot with automatic recalculations"""

    wip_snapshot = db.query(WIPSnapshot).filter(WIPSnapshot.id == wip_id).first()
    if not wip_snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="WIP snapshot not found"
        )

    # Update using the service (includes recalculations)
    wip_service = WIPService(db)
    updated_wip = wip_service.update_wip_snapshot(
        wip_snapshot, wip_update, current_user.id
    )

    # Get project name
    project = db.query(Project).filter(Project.id == updated_wip.project_id).first()

    wip_response = WIPSnapshotResponse.from_orm(updated_wip)
    wip_response.project_name = project.name if project else None

    return wip_response


@router.get("/compare/{project_id}")
def compare_wip_snapshots(
    project_id: int,
    current_date: date = Query(..., description="Current month date"),
    previous_date: Optional[date] = Query(
        None, description="Previous month date (optional)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get month-to-month comparison for a project"""

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    wip_service = WIPService(db)
    comparison = wip_service.get_month_comparison(
        project_id, current_date, previous_date
    )

    # Calculate change amounts
    current_wip = comparison["current_month"]
    previous_wip = comparison["prior_month"]

    contract_change = None
    final_cost_change = None
    margin_change = None
    completion_change = None

    if current_wip and previous_wip:
        if (
            current_wip.current_month_total_contract_amount
            and previous_wip.current_month_total_contract_amount
        ):
            contract_change = (
                current_wip.current_month_total_contract_amount
                - previous_wip.current_month_total_contract_amount
            )

        if (
            current_wip.current_month_estimated_final_cost
            and previous_wip.current_month_estimated_final_cost
        ):
            final_cost_change = (
                current_wip.current_month_estimated_final_cost
                - previous_wip.current_month_estimated_final_cost
            )

        if (
            current_wip.current_month_estimated_job_margin_at_completion
            and previous_wip.current_month_estimated_job_margin_at_completion
        ):
            margin_change = (
                current_wip.current_month_estimated_job_margin_at_completion
                - previous_wip.current_month_estimated_job_margin_at_completion
            )

        if (
            current_wip.us_gaap_percent_completion
            and previous_wip.us_gaap_percent_completion
        ):
            completion_change = (
                current_wip.us_gaap_percent_completion
                - previous_wip.us_gaap_percent_completion
            )

    return WIPComparisonResponse(
        project_id=project_id,
        job_number=project.job_number,
        project_name=project.name,
        current_month=(
            WIPSnapshotResponse.from_orm(current_wip) if current_wip else None
        ),
        previous_month=(
            WIPSnapshotResponse.from_orm(previous_wip) if previous_wip else None
        ),
        has_significant_changes=comparison.get("has_significant_changes", False),
        contract_amount_change=contract_change,
        estimated_final_cost_change=final_cost_change,
        job_margin_change=margin_change,
        percent_completion_change=completion_change,
    )


@router.delete("/{wip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wip_snapshot(
    wip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Only admins can delete
):
    """Delete a WIP snapshot"""

    wip_snapshot = db.query(WIPSnapshot).filter(WIPSnapshot.id == wip_id).first()
    if not wip_snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="WIP snapshot not found"
        )

    db.delete(wip_snapshot)
    db.commit()


@router.get("/summary/dashboard")
def get_wip_dashboard_summary(
    report_date: Optional[date] = Query(None, description="Specific report date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get WIP dashboard summary statistics"""

    query = db.query(WIPSnapshot)

    if report_date:
        query = query.filter(WIPSnapshot.report_date == report_date)
    else:
        # Get latest snapshots for each project
        latest_dates = (
            db.query(
                WIPSnapshot.project_id,
                func.max(WIPSnapshot.report_date).label("latest_date"),
            )
            .group_by(WIPSnapshot.project_id)
            .subquery()
        )

        query = query.join(
            latest_dates,
            (WIPSnapshot.project_id == latest_dates.c.project_id)
            & (WIPSnapshot.report_date == latest_dates.c.latest_date),
        )

    snapshots = query.all()

    total_contract_value = sum(
        s.current_month_total_contract_amount or 0 for s in snapshots
    )
    total_cost_to_date = sum(s.current_month_cost_to_date or 0 for s in snapshots)
    total_billed_to_date = sum(
        s.current_month_revenue_billed_to_date or 0 for s in snapshots
    )
    total_estimated_final_cost = sum(
        s.current_month_estimated_final_cost or 0 for s in snapshots
    )

    return {
        "total_projects": len(snapshots),
        "total_contract_value": total_contract_value,
        "total_cost_to_date": total_cost_to_date,
        "total_billed_to_date": total_billed_to_date,
        "total_estimated_final_cost": total_estimated_final_cost,
        "overall_margin": (
            total_contract_value - total_estimated_final_cost
            if total_estimated_final_cost
            else None
        ),
        "overall_margin_percent": (
            (
                (total_contract_value - total_estimated_final_cost)
                / total_contract_value
                * 100
            )
            if total_contract_value and total_estimated_final_cost
            else None
        ),
        "report_date": report_date or "Latest",
    }


@router.get("/export/excel")
async def export_wip_to_excel(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Export WIP data to Excel file"""
    import pandas as pd
    from io import BytesIO
    from fastapi.responses import StreamingResponse

    # Get latest WIP snapshots using the same logic as get_latest_wip_snapshots
    # Subquery to get the latest report date for each project
    latest_dates = (
        db.query(
            WIPSnapshot.project_id,
            func.max(WIPSnapshot.report_date).label("latest_date"),
        )
        .group_by(WIPSnapshot.project_id)
        .subquery()
    )

    # Get WIP snapshots with the latest dates
    wip_snapshots = (
        db.query(WIPSnapshot, Project.name.label("project_name"))
        .join(Project)
        .join(
            latest_dates,
            (WIPSnapshot.project_id == latest_dates.c.project_id)
            & (WIPSnapshot.report_date == latest_dates.c.latest_date),
        )
        .order_by(WIPSnapshot.job_number)
        .all()
    )

    # Convert to DataFrame
    data_for_export = []
    for wip, project_name in wip_snapshots:
        data_for_export.append(
            {
                "Job #": wip.job_number,
                "Project Name": project_name,
                "Original Contract": wip.current_month_original_contract_amount,
                "Change Orders": wip.current_month_change_order_amount,
                "Total Contract": wip.current_month_total_contract_amount,
                "Prior Contract": wip.prior_month_total_contract_amount,
                "Contract Variance": wip.current_vs_prior_contract_variance,
                "Cost to Date": wip.current_month_cost_to_date,
                "Est. Cost to Complete": wip.current_month_estimated_cost_to_complete,
                "Est. Final Cost": wip.current_month_estimated_final_cost,
                "Prior Final Cost": wip.prior_month_estimated_final_cost,
                "Final Cost Variance": wip.current_vs_prior_estimated_final_cost_variance,
                "GAAP % Complete": wip.us_gaap_percent_completion,
                "Revenue Earned (GAAP)": wip.revenue_earned_to_date_us_gaap,
                "Job Margin (GAAP)": wip.estimated_job_margin_to_date_us_gaap,
                "Job Margin %": wip.estimated_job_margin_to_date_percent_sales,
                "Est. Job Margin": wip.current_month_estimated_job_margin_at_completion,
                "Prior Job Margin": wip.prior_month_estimated_job_margin_at_completion,
                "Job Margin Variance": wip.current_vs_prior_estimated_job_margin,
                "Job Margin % Sales": wip.current_month_estimated_job_margin_percent_sales,
                "Revenue Billed": wip.current_month_revenue_billed_to_date,
                "Costs in Excess": wip.current_month_costs_in_excess_billings,
                "Billings in Excess": wip.current_month_billings_excess_revenue,
                "Additional Entry": wip.current_month_addl_entry_required,
                "Report Date": (
                    wip.report_date.strftime("%Y-%m-%d") if wip.report_date else None
                ),
            }
        )

    df = pd.DataFrame(data_for_export)

    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="WIP Report", index=False)

        # Auto-adjust column widths
        worksheet = writer.sheets["WIP Report"]
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)

    # Return Excel file
    today = pd.Timestamp.now().strftime("%Y-%m-%d")
    filename = f"TSI_WIP_Report_{today}.xlsx"

    return StreamingResponse(
        BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/latest/with-totals")
def get_latest_wip_with_totals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get latest WIP snapshots for each project with column totals"""

    # Get latest snapshots for each project (existing logic)
    latest_dates = (
        db.query(
            WIPSnapshot.project_id,
            func.max(WIPSnapshot.report_date).label("latest_date"),
        )
        .group_by(WIPSnapshot.project_id)
        .subquery()
    )

    # Get WIP snapshots with project names (like existing /latest endpoint)
    wip_snapshots = (
        db.query(WIPSnapshot, Project.name.label("project_name"))
        .join(Project)
        .join(
            latest_dates,
            (WIPSnapshot.project_id == latest_dates.c.project_id)
            & (WIPSnapshot.report_date == latest_dates.c.latest_date),
        )
        .filter(Project.is_active == True)
        .order_by(WIPSnapshot.job_number)
        .all()
    )

    # Extract snapshots for calculations
    snapshots = [wip for wip, project_name in wip_snapshots]

    # Calculate column totals
    def safe_sum(values):
        """Safely sum values, treating None as 0"""
        return sum(v for v in values if v is not None)

    # Contract section totals
    total_original_contract = safe_sum(
        [s.current_month_original_contract_amount for s in snapshots]
    )
    total_change_orders = safe_sum(
        [s.current_month_change_order_amount for s in snapshots]
    )
    total_contract = safe_sum(
        [s.current_month_total_contract_amount for s in snapshots]
    )
    total_prior_contract = safe_sum(
        [s.prior_month_total_contract_amount for s in snapshots]
    )

    # Cost section totals
    total_cost_to_date = safe_sum([s.current_month_cost_to_date for s in snapshots])
    total_est_cost_complete = safe_sum(
        [s.current_month_estimated_cost_to_complete for s in snapshots]
    )
    total_estimated_final_cost = safe_sum(
        [s.current_month_estimated_final_cost for s in snapshots]
    )
    total_prior_final_cost = safe_sum(
        [s.prior_month_estimated_final_cost for s in snapshots]
    )

    # Revenue/Billing section totals
    total_billed_to_date = safe_sum(
        [s.current_month_revenue_billed_to_date for s in snapshots]
    )
    total_revenue_earned = safe_sum(
        [s.revenue_earned_to_date_us_gaap for s in snapshots]
    )

    # Job margin totals
    total_job_margin = safe_sum(
        [s.current_month_estimated_job_margin_at_completion for s in snapshots]
    )
    total_prior_job_margin = safe_sum(
        [s.prior_month_estimated_job_margin_at_completion for s in snapshots]
    )

    # WIP adjustment totals
    total_costs_excess_billings = safe_sum(
        [s.current_month_costs_in_excess_billings for s in snapshots]
    )
    total_billings_excess_revenue = safe_sum(
        [s.current_month_billings_excess_revenue for s in snapshots]
    )

    # Calculate percentage totals (weighted averages)
    avg_us_gaap_completion = 0
    avg_job_margin_percent = 0

    if snapshots:
        # Weight by contract value for meaningful averages
        total_weight = safe_sum(
            [s.current_month_total_contract_amount or 0 for s in snapshots]
        )
        if total_weight > 0:
            avg_us_gaap_completion = (
                sum(
                    [
                        (s.us_gaap_percent_completion or 0)
                        * (s.current_month_total_contract_amount or 0)
                        for s in snapshots
                    ]
                )
                / total_weight
            )

            avg_job_margin_percent = (
                sum(
                    [
                        (s.current_month_estimated_job_margin_percent_sales or 0)
                        * (s.current_month_total_contract_amount or 0)
                        for s in snapshots
                    ]
                )
                / total_weight
            )

    # Prepare response
    totals = {
        # Contract section
        "total_original_contract": (
            float(total_original_contract) if total_original_contract else 0
        ),
        "total_change_orders": float(total_change_orders) if total_change_orders else 0,
        "total_contract": float(total_contract) if total_contract else 0,
        "total_prior_contract": (
            float(total_prior_contract) if total_prior_contract else 0
        ),
        "contract_variance": (
            float(total_contract - total_prior_contract)
            if total_contract and total_prior_contract
            else 0
        ),
        # Cost section
        "total_cost_to_date": float(total_cost_to_date) if total_cost_to_date else 0,
        "total_est_cost_complete": (
            float(total_est_cost_complete) if total_est_cost_complete else 0
        ),
        "total_estimated_final_cost": (
            float(total_estimated_final_cost) if total_estimated_final_cost else 0
        ),
        "total_prior_final_cost": (
            float(total_prior_final_cost) if total_prior_final_cost else 0
        ),
        "final_cost_variance": (
            float(total_estimated_final_cost - total_prior_final_cost)
            if total_estimated_final_cost and total_prior_final_cost
            else 0
        ),
        # Percentages (weighted averages)
        "avg_us_gaap_completion": round(float(avg_us_gaap_completion), 2),
        # Revenue section
        "total_billed_to_date": (
            float(total_billed_to_date) if total_billed_to_date else 0
        ),
        "total_revenue_earned": (
            float(total_revenue_earned) if total_revenue_earned else 0
        ),
        # Job margin section
        "total_job_margin": float(total_job_margin) if total_job_margin else 0,
        "total_prior_job_margin": (
            float(total_prior_job_margin) if total_prior_job_margin else 0
        ),
        "job_margin_variance": (
            float(total_job_margin - total_prior_job_margin)
            if total_job_margin and total_prior_job_margin
            else 0
        ),
        "avg_job_margin_percent": round(float(avg_job_margin_percent), 2),
        # WIP adjustments
        "total_costs_excess_billings": (
            float(total_costs_excess_billings) if total_costs_excess_billings else 0
        ),
        "total_billings_excess_revenue": (
            float(total_billings_excess_revenue) if total_billings_excess_revenue else 0
        ),
        # Summary stats
        "total_projects": len(snapshots),
        "overall_margin_percent": round(
            (
                (float(total_job_margin) / float(total_contract) * 100)
                if total_contract and total_contract != 0
                else 0
            ),
            2,
        ),
    }

    # Convert to response format with project names
    result = []
    for wip, project_name in wip_snapshots:
        wip_response = WIPSnapshotResponse.from_orm(wip)
        wip_response.project_name = project_name
        result.append(wip_response)

    return {
        "snapshots": result,
        "totals": totals,
        "report_date": snapshots[0].report_date.isoformat() if snapshots else None,
    }
