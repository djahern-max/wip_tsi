from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, get_admin_user
from app.models.user import User
from app.models.wip_snapshot import WIPSnapshot
from app.models.explanation import CellExplanation
from app.schemas.explanation import (
    ExplanationCreate,
    ExplanationUpdate,
    ExplanationResponse,
)

router = APIRouter()


@router.get("/wip/{wip_snapshot_id}", response_model=List[ExplanationResponse])
def get_wip_explanations(
    wip_snapshot_id: int,
    field_name: Optional[str] = Query(None, description="Filter by specific field"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all explanations for a WIP snapshot"""

    # Verify WIP snapshot exists
    wip_snapshot = (
        db.query(WIPSnapshot).filter(WIPSnapshot.id == wip_snapshot_id).first()
    )
    if not wip_snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="WIP snapshot not found"
        )

    query = (
        db.query(CellExplanation, User.username.label("created_by_name"))
        .join(User, CellExplanation.created_by == User.id)
        .filter(CellExplanation.wip_snapshot_id == wip_snapshot_id)
    )

    if field_name:
        query = query.filter(CellExplanation.field_name == field_name)

    explanations = query.order_by(CellExplanation.created_at.desc()).all()

    result = []
    for explanation, created_by_name in explanations:
        explanation_response = ExplanationResponse.from_orm(explanation)
        explanation_response.created_by_name = created_by_name
        result.append(explanation_response)

    return result


@router.get(
    "/wip/{wip_snapshot_id}/field/{field_name}", response_model=ExplanationResponse
)
def get_field_explanation(
    wip_snapshot_id: int,
    field_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get explanation for a specific field"""

    explanation_data = (
        db.query(CellExplanation, User.username.label("created_by_name"))
        .join(User, CellExplanation.created_by == User.id)
        .filter(
            CellExplanation.wip_snapshot_id == wip_snapshot_id,
            CellExplanation.field_name == field_name,
        )
        .order_by(CellExplanation.created_at.desc())
        .first()
    )

    if not explanation_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No explanation found for this field",
        )

    explanation, created_by_name = explanation_data
    explanation_response = ExplanationResponse.from_orm(explanation)
    explanation_response.created_by_name = created_by_name

    return explanation_response


@router.post(
    "/wip/{wip_snapshot_id}",
    response_model=ExplanationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_explanation(
    wip_snapshot_id: int,
    explanation_data: ExplanationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Only admins can create explanations
):
    """Create a new explanation for a WIP field"""

    # Verify WIP snapshot exists
    wip_snapshot = (
        db.query(WIPSnapshot).filter(WIPSnapshot.id == wip_snapshot_id).first()
    )
    if not wip_snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="WIP snapshot not found"
        )

    # Check if explanation already exists for this field
    existing_explanation = (
        db.query(CellExplanation)
        .filter(
            CellExplanation.wip_snapshot_id == wip_snapshot_id,
            CellExplanation.field_name == explanation_data.field_name,
        )
        .first()
    )

    if existing_explanation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Explanation already exists for field '{explanation_data.field_name}'. Use PUT to update.",
        )

    # Create new explanation
    db_explanation = CellExplanation(
        wip_snapshot_id=wip_snapshot_id,
        field_name=explanation_data.field_name,
        explanation=explanation_data.explanation,
        created_by=current_user.id,
    )

    db.add(db_explanation)
    db.commit()
    db.refresh(db_explanation)

    # Return with user name
    explanation_response = ExplanationResponse.from_orm(db_explanation)
    explanation_response.created_by_name = current_user.username

    return explanation_response


@router.put("/{explanation_id}", response_model=ExplanationResponse)
def update_explanation(
    explanation_id: int,
    explanation_update: ExplanationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Only admins can update explanations
):
    """Update an existing explanation"""

    explanation = (
        db.query(CellExplanation).filter(CellExplanation.id == explanation_id).first()
    )
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Explanation not found"
        )

    # Update the explanation
    explanation.explanation = explanation_update.explanation
    explanation.created_by = current_user.id  # Track who last updated

    db.commit()
    db.refresh(explanation)

    # Return with user name
    explanation_response = ExplanationResponse.from_orm(explanation)
    explanation_response.created_by_name = current_user.username

    return explanation_response


@router.delete("/{explanation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_explanation(
    explanation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Only admins can delete explanations
):
    """Delete an explanation"""

    explanation = (
        db.query(CellExplanation).filter(CellExplanation.id == explanation_id).first()
    )
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Explanation not found"
        )

    db.delete(explanation)
    db.commit()


@router.get("/fields/available")
def get_available_fields():
    """Get list of all fields that can have explanations"""
    from app.models.explanation import get_explainable_fields
    from app.schemas.explanation import FIELD_DISPLAY_NAMES

    fields = get_explainable_fields()

    return [
        {
            "field_name": field,
            "display_name": FIELD_DISPLAY_NAMES.get(
                field, field.replace("_", " ").title()
            ),
        }
        for field in fields
    ]
