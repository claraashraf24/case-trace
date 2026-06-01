from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.case import CaseCreate, CaseRead, CaseStats, CaseUpdate
from app.services.case_service import (
    create_case,
    delete_case,
    get_case_by_id,
    get_case_stats,
    get_cases,
    update_case,
)


router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_new_case(case_data: CaseCreate, db: Session = Depends(get_db)):
    return create_case(db=db, case_data=case_data)


@router.get("", response_model=list[CaseRead])
def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, description="Search by title, summary, or location"),
    status: str | None = Query(None, description="Filter by case status"),
    priority: str | None = Query(None, description="Filter by priority"),
    case_type: str | None = Query(None, description="Filter by case type"),
    db: Session = Depends(get_db),
):
    return get_cases(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        priority=priority,
        case_type=case_type,
    )



@router.get("/stats", response_model=CaseStats)
def read_case_stats(db: Session = Depends(get_db)):
    return get_case_stats(db=db)


@router.get("/{case_id}", response_model=CaseRead)
def read_case(case_id: int, db: Session = Depends(get_db)):
    case = get_case_by_id(db=db, case_id=case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return case


@router.patch("/{case_id}", response_model=CaseRead)
def edit_case(case_id: int, case_data: CaseUpdate, db: Session = Depends(get_db)):
    case = update_case(db=db, case_id=case_id, case_data=case_data)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_case(case_id: int, db: Session = Depends(get_db)):
    deleted = delete_case(db=db, case_id=case_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return None