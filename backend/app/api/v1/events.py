from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.services.case_service import get_case_by_id
from app.services.event_service import (
    create_event,
    delete_event,
    get_event_by_id,
    get_events_for_case,
    update_event,
)


router = APIRouter(tags=["Events"])


@router.post(
    "/cases/{case_id}/events",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_case_event(
    case_id: int,
    event_data: EventCreate,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(db=db, case_id=case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    payload = event_data.model_copy(update={"case_id": case_id})
    return create_event(db=db, event_data=payload)


@router.get(
    "/cases/{case_id}/events",
    response_model=list[EventRead],
)
def list_case_events(
    case_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=300),
    db: Session = Depends(get_db),
):
    case = get_case_by_id(db=db, case_id=case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return get_events_for_case(
        db=db,
        case_id=case_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/events/{event_id}",
    response_model=EventRead,
)
def read_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = get_event_by_id(db=db, event_id=event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event


@router.patch(
    "/events/{event_id}",
    response_model=EventRead,
)
def edit_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
):
    event = update_event(
        db=db,
        event_id=event_id,
        event_data=event_data,
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    deleted = delete_event(db=db, event_id=event_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return None