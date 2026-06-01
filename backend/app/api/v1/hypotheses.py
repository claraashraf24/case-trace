from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.hypothesis import HypothesisResult
from app.services.case_service import get_case_by_id
from app.services.hypothesis_service import generate_case_hypotheses


router = APIRouter(tags=["Hypotheses"])


@router.get(
    "/cases/{case_id}/hypotheses",
    response_model=HypothesisResult,
)
def get_case_hypotheses(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(db=db, case_id=case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return generate_case_hypotheses(db=db, case_id=case_id)