from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.contradiction import ContradictionReport, ContradictionSummary
from app.services.case_service import get_case_by_id
from app.services.contradiction_service import (
    build_contradiction_report,
    detect_case_contradictions,
)


router = APIRouter(tags=["Contradictions"])




@router.get(
    "/cases/{case_id}/contradictions/report",
    response_model=ContradictionReport,
)
def get_case_contradiction_report(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(db=db, case_id=case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return build_contradiction_report(db=db, case_id=case_id)
@router.get(
    "/cases/{case_id}/contradictions",
    response_model=ContradictionSummary,
)
def get_case_contradictions(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(db=db, case_id=case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return detect_case_contradictions(db=db, case_id=case_id)