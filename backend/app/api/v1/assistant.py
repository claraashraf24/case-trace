from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.assistant import AssistantAnswer, AssistantQuery
from app.services.assistant_service import generate_assistant_answer
from app.services.case_service import get_case_by_id


router = APIRouter(tags=["Assistant"])


@router.post(
    "/cases/{case_id}/assistant/query",
    response_model=AssistantAnswer,
)
def query_case_assistant(
    case_id: int,
    query: AssistantQuery,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(db=db, case_id=case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return generate_assistant_answer(
        db=db,
        case_id=case_id,
        question=query.question,
    )