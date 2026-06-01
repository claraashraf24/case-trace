from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evidence import (
    EvidenceCreate,
    EvidenceProcessingResult,
    EvidenceRead,
    EvidenceUpdate,
)
from app.services.evidence_service import (
    create_evidence,
    create_uploaded_text_evidence,
    delete_evidence,
    get_evidence_by_id,
    get_evidence_for_case,
    process_evidence,
    update_evidence,
)

from app.utils.file_storage import save_upload_file


router = APIRouter(tags=["Evidence"])


@router.post(
    "/cases/{case_id}/evidence",
    response_model=EvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_case_evidence(
    case_id: int,
    evidence_data: EvidenceCreate,
    db: Session = Depends(get_db),
):
    evidence = create_evidence(
        db=db,
        case_id=case_id,
        evidence_data=evidence_data,
    )

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return evidence


@router.post(
    "/cases/{case_id}/evidence/upload-text",
    response_model=EvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_text_evidence(
    case_id: int,
    title: str = Form(...),
    evidence_type: str = Form("other"),
    source_name: str | None = Form(None),
    source_reference: str | None = Form(None),
    notes: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        file_path, raw_text = await save_upload_file(case_id=case_id, file=file)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    evidence = create_uploaded_text_evidence(
        db=db,
        case_id=case_id,
        title=title,
        evidence_type=evidence_type,
        source_name=source_name,
        source_reference=source_reference,
        file_name=file.filename or "uploaded_file.txt",
        file_type=Path(file.filename or "").suffix.lower().replace(".", ""),
        file_path=file_path,
        raw_text=raw_text,
        notes=notes,
    )

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return evidence


@router.post(
    "/evidence/{evidence_id}/process",
    response_model=EvidenceProcessingResult,
)
def process_evidence_item(
    evidence_id: int,
    db: Session = Depends(get_db),
):
    result = process_evidence(db=db, evidence_id=evidence_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    return result

@router.get(
    "/cases/{case_id}/evidence",
    response_model=list[EvidenceRead],
)
def list_case_evidence(
    case_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    evidence_items = get_evidence_for_case(
        db=db,
        case_id=case_id,
        skip=skip,
        limit=limit,
    )

    if evidence_items is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return evidence_items


@router.get(
    "/evidence/{evidence_id}",
    response_model=EvidenceRead,
)
def read_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
):
    evidence = get_evidence_by_id(db=db, evidence_id=evidence_id)

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    return evidence


@router.patch(
    "/evidence/{evidence_id}",
    response_model=EvidenceRead,
)
def edit_evidence(
    evidence_id: int,
    evidence_data: EvidenceUpdate,
    db: Session = Depends(get_db),
):
    evidence = update_evidence(
        db=db,
        evidence_id=evidence_id,
        evidence_data=evidence_data,
    )

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    return evidence


@router.delete(
    "/evidence/{evidence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
):
    deleted = delete_evidence(db=db, evidence_id=evidence_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    return None