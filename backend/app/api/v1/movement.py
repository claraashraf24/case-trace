from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.movement import MovementReconstructionResponse
from app.services.case_service import get_case_by_id
from app.services.movement_service import reconstruct_case_movement


router = APIRouter(tags=["Movement"])


@router.get(
    "/cases/{case_id}/movement",
    response_model=MovementReconstructionResponse,
)
def read_case_movement(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(db=db, case_id=case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return reconstruct_case_movement(
        db=db,
        case_id=case_id,
    )