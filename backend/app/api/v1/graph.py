from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.graph import CaseGraph
from app.services.case_service import get_case_by_id
from app.services.graph_service import build_case_graph


router = APIRouter(tags=["Graph"])


@router.get(
    "/cases/{case_id}/graph",
    response_model=CaseGraph,
)
def get_case_graph(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(db=db, case_id=case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return build_case_graph(db=db, case_id=case_id)