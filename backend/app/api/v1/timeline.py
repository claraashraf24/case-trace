from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.timeline import TimelineReconstruction, TimelineReport
from app.services.case_service import get_case_by_id
from app.services.timeline_service import build_timeline_report, reconstruct_case_timeline


router = APIRouter(tags=["Timeline"])


@router.get(
    "/cases/{case_id}/timeline/report",
    response_model=TimelineReport,
)
def get_case_timeline_report(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(db=db, case_id=case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return build_timeline_report(db=db, case_id=case_id)

@router.get(
    "/cases/{case_id}/timeline",
    response_model=TimelineReconstruction,
)
def get_case_timeline(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(db=db, case_id=case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return reconstruct_case_timeline(db=db, case_id=case_id)