from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.case import Case
from app.schemas.case import CaseCreate, CaseUpdate


def create_case(db: Session, case_data: CaseCreate) -> Case:
    case = Case(**case_data.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_cases(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    case_type: str | None = None,
) -> list[Case]:
    query = db.query(Case)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Case.title.ilike(search_pattern),
                Case.summary.ilike(search_pattern),
                Case.location.ilike(search_pattern),
            )
        )

    if status:
        query = query.filter(Case.status == status)

    if priority:
        query = query.filter(Case.priority == priority)

    if case_type:
        query = query.filter(Case.case_type == case_type)

    return (
        query.order_by(Case.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_case_by_id(db: Session, case_id: int) -> Case | None:
    return db.query(Case).filter(Case.id == case_id).first()


def update_case(db: Session, case_id: int, case_data: CaseUpdate) -> Case | None:
    case = get_case_by_id(db, case_id)

    if not case:
        return None

    update_data = case_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)
    return case


def delete_case(db: Session, case_id: int) -> bool:
    case = get_case_by_id(db, case_id)

    if not case:
        return False

    db.delete(case)
    db.commit()
    return True


def get_case_stats(db: Session) -> dict:
    total_cases = db.query(Case).count()

    open_cases = db.query(Case).filter(Case.status == "open").count()
    in_review_cases = db.query(Case).filter(Case.status == "in_review").count()
    closed_cases = db.query(Case).filter(Case.status == "closed").count()
    archived_cases = db.query(Case).filter(Case.status == "archived").count()

    critical_priority_cases = db.query(Case).filter(Case.priority == "critical").count()
    high_priority_cases = db.query(Case).filter(Case.priority == "high").count()
    medium_priority_cases = db.query(Case).filter(Case.priority == "medium").count()
    low_priority_cases = db.query(Case).filter(Case.priority == "low").count()

    return {
        "total_cases": total_cases,
        "open_cases": open_cases,
        "in_review_cases": in_review_cases,
        "closed_cases": closed_cases,
        "archived_cases": archived_cases,
        "critical_priority_cases": critical_priority_cases,
        "high_priority_cases": high_priority_cases,
        "medium_priority_cases": medium_priority_cases,
        "low_priority_cases": low_priority_cases,
    }