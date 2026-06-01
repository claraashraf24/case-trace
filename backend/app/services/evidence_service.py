from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceCreate, EvidenceUpdate
from app.ai.hybrid_evidence_processor import process_evidence_text_hybrid
from app.schemas.event import EventCreate
from app.services.event_service import upsert_event_from_evidence
from app.utils.time_normalizer import extract_clean_time


def case_exists(db: Session, case_id: int) -> bool:
    return db.query(Case).filter(Case.id == case_id).first() is not None


def create_evidence(
    db: Session,
    case_id: int,
    evidence_data: EvidenceCreate,
) -> Evidence | None:
    if not case_exists(db=db, case_id=case_id):
        return None

    evidence = Evidence(
        case_id=case_id,
        **evidence_data.model_dump(),
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def get_evidence_for_case(
    db: Session,
    case_id: int,
    skip: int = 0,
    limit: int = 50,
) -> list[Evidence] | None:
    if not case_exists(db=db, case_id=case_id):
        return None

    return (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_evidence_by_id(
    db: Session,
    evidence_id: int,
) -> Evidence | None:
    return db.query(Evidence).filter(Evidence.id == evidence_id).first()


def update_evidence(
    db: Session,
    evidence_id: int,
    evidence_data: EvidenceUpdate,
) -> Evidence | None:
    evidence = get_evidence_by_id(db=db, evidence_id=evidence_id)

    if not evidence:
        return None

    update_data = evidence_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(evidence, field, value)

    db.commit()
    db.refresh(evidence)
    return evidence


def delete_evidence(
    db: Session,
    evidence_id: int,
) -> bool:
    evidence = get_evidence_by_id(db=db, evidence_id=evidence_id)

    if not evidence:
        return False

    db.delete(evidence)
    db.commit()
    return True

def create_uploaded_text_evidence(
    db: Session,
    case_id: int,
    title: str,
    evidence_type: str,
    source_name: str | None,
    source_reference: str | None,
    file_name: str,
    file_type: str,
    file_path: str,
    raw_text: str,
    notes: str | None = None,
) -> Evidence | None:
    if not case_exists(db=db, case_id=case_id):
        return None

    evidence = Evidence(
        case_id=case_id,
        title=title,
        evidence_type=evidence_type,
        source_name=source_name,
        source_reference=source_reference,
        file_name=file_name,
        file_type=file_type,
        file_path=file_path,
        raw_text=raw_text,
        summary=None,
        status="uploaded",
        confidence_score=None,
        notes=notes,
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence

def process_evidence(
    db: Session,
    evidence_id: int,
) -> dict | None:
    evidence = get_evidence_by_id(db=db, evidence_id=evidence_id)

    if not evidence:
        return None

    if not evidence.raw_text:
        return {
            "error": "Evidence has no raw_text to process."
        }

    result = process_evidence_text_hybrid(
        evidence_id=evidence.id,
        text=evidence.raw_text,
    )

    event_draft = result["event_draft"]

    saved_event = upsert_event_from_evidence(
            db=db,
            event_data=EventCreate(
                case_id=evidence.case_id,
                evidence_id=evidence.id,
                event_time=extract_clean_time(event_draft["time"]),
                normalized_time=None,
                location=event_draft["location"],
                description=event_draft["description"],
                participants=event_draft["participants"],
                actions=event_draft["actions"],
                objects=event_draft["objects"],
                confidence_score=event_draft["confidence"],
                source_type="extracted",
                status="draft",
            ),
        )

    evidence.status = "processed"
    evidence.confidence_score = event_draft["confidence"]
    evidence.extraction_method = result.get("extraction_method")
    evidence.uncertainty_notes = result.get("uncertainty_notes") or []

    if not evidence.summary:
        evidence.summary = event_draft["description"][:250]

    db.commit()
    db.refresh(evidence)

    result["saved_event_id"] = saved_event.id

    return result