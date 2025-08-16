from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.dependencies import get_db, get_current_user, get_admin_user
from app.models.user import User
from app.models.project import Project
from app.models.wip_snapshot import WIPSnapshot
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)

router = APIRouter()


@router.get("/", response_model=List[ProjectListResponse])
def list_projects(
    skip: int = Query(0, ge=0, description="Number of projects to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of projects to return"),
    active_only: bool = Query(True, description="Only return active projects"),
    search: Optional[str] = Query(None, description="Search in job number or name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all projects with summary information"""

    query = db.query(
        Project.id,
        Project.job_number,
        Project.name,
        Project.original_contract_amount,
        Project.is_active,
        func.count(WIPSnapshot.id).label("total_wip_snapshots"),
        func.max(WIPSnapshot.report_date).label("latest_report_date"),
    ).outerjoin(WIPSnapshot)

    # Apply filters
    if active_only:
        query = query.filter(Project.is_active == True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Project.job_number.ilike(search_term)) | (Project.name.ilike(search_term))
        )

    # Group by project fields and apply pagination
    projects = (
        query.group_by(
            Project.id,
            Project.job_number,
            Project.name,
            Project.original_contract_amount,
            Project.is_active,
        )
        .order_by(Project.job_number)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        ProjectListResponse(
            id=p.id,
            job_number=p.job_number,
            name=p.name,
            original_contract_amount=p.original_contract_amount,
            is_active=p.is_active,
            total_wip_snapshots=p.total_wip_snapshots or 0,
            latest_report_date=p.latest_report_date,
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific project by ID"""

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Get additional stats
    wip_count = (
        db.query(func.count(WIPSnapshot.id))
        .filter(WIPSnapshot.project_id == project_id)
        .scalar()
    )

    latest_report = (
        db.query(func.max(WIPSnapshot.report_date))
        .filter(WIPSnapshot.project_id == project_id)
        .scalar()
    )

    response = ProjectResponse.from_orm(project)
    response.total_wip_snapshots = wip_count or 0
    response.latest_report_date = latest_report

    return response


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Only admins can create projects
):
    """Create a new project"""

    # Check if job number already exists
    existing_project = (
        db.query(Project).filter(Project.job_number == project.job_number).first()
    )

    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project with job number '{project.job_number}' already exists",
        )

    # Create new project
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return ProjectResponse.from_orm(db_project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Only admins can update projects
):
    """Update a project"""

    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Update fields
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)

    db.commit()
    db.refresh(db_project)

    return ProjectResponse.from_orm(db_project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Only admins can delete projects
):
    """Delete a project (soft delete by setting is_active=False)"""

    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Check if project has WIP snapshots
    wip_count = (
        db.query(func.count(WIPSnapshot.id))
        .filter(WIPSnapshot.project_id == project_id)
        .scalar()
    )

    if wip_count > 0:
        # Soft delete - just mark as inactive
        db_project.is_active = False
        db.commit()
    else:
        # Hard delete if no WIP data
        db.delete(db_project)
        db.commit()


@router.get("/{project_id}/wip-summary")
def get_project_wip_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get WIP summary for a specific project"""

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Get WIP snapshots for this project
    wip_snapshots = (
        db.query(WIPSnapshot)
        .filter(WIPSnapshot.project_id == project_id)
        .order_by(WIPSnapshot.report_date.desc())
        .limit(12)  # Last 12 months
        .all()
    )

    return {
        "project": ProjectResponse.from_orm(project),
        "recent_wip_snapshots": len(wip_snapshots),
        "latest_report_date": wip_snapshots[0].report_date if wip_snapshots else None,
        "wip_trend": [
            {
                "report_date": wip.report_date,
                "contract_amount": wip.current_month_total_contract_amount,
                "cost_to_date": wip.current_month_cost_to_date,
                "percent_complete": wip.us_gaap_percent_completion,
                "job_margin": wip.current_month_estimated_job_margin_at_completion,
            }
            for wip in wip_snapshots[:6]  # Last 6 months for trend
        ],
    }
