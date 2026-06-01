from sqlalchemy.orm import Session

from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate


def create_event(db: Session, event_data: EventCreate) -> Event:
    event = Event(**event_data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_events_for_case(
    db: Session,
    case_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Event]:
    return (
        db.query(Event)
        .filter(Event.case_id == case_id)
        .order_by(Event.event_time.asc().nullslast(), Event.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_event_by_id(db: Session, event_id: int) -> Event | None:
    return db.query(Event).filter(Event.id == event_id).first()


def update_event(
    db: Session,
    event_id: int,
    event_data: EventUpdate,
) -> Event | None:
    event = get_event_by_id(db=db, event_id=event_id)

    if not event:
        return None

    update_data = event_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event_id: int) -> bool:
    event = get_event_by_id(db=db, event_id=event_id)

    if not event:
        return False

    db.delete(event)
    db.commit()
    return True

def get_event_by_evidence_id(
    db: Session,
    evidence_id: int,
) -> Event | None:
    return db.query(Event).filter(Event.evidence_id == evidence_id).first()


def upsert_event_from_evidence(
    db: Session,
    event_data: EventCreate,
) -> Event:
    existing_event = None

    if event_data.evidence_id is not None:
        existing_event = get_event_by_evidence_id(
            db=db,
            evidence_id=event_data.evidence_id,
        )

    if not existing_event:
        return create_event(db=db, event_data=event_data)

    update_data = event_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(existing_event, field, value)

    db.commit()
    db.refresh(existing_event)

    return existing_event