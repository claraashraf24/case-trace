from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


ALLOWED_TEXT_EXTENSIONS = {".txt"}


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_case_upload_dir(case_id: int) -> Path:
    project_root = get_project_root()
    upload_dir = project_root / "data" / "raw" / f"case_{case_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def validate_text_file(filename: str) -> None:
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_TEXT_EXTENSIONS:
        raise ValueError("Only .txt files are supported in this step.")


def build_safe_filename(original_filename: str) -> str:
    extension = Path(original_filename).suffix.lower()
    stem = Path(original_filename).stem.replace(" ", "_")
    unique_id = uuid4().hex[:8]

    return f"{stem}_{unique_id}{extension}"


async def save_upload_file(case_id: int, file: UploadFile) -> tuple[str, str]:
    if not file.filename:
        raise ValueError("Uploaded file must have a filename.")

    validate_text_file(file.filename)

    upload_dir = get_case_upload_dir(case_id)
    safe_filename = build_safe_filename(file.filename)
    file_path = upload_dir / safe_filename

    content = await file.read()

    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("File must be UTF-8 encoded text.") from exc

    file_path.write_bytes(content)

    relative_path = file_path.relative_to(get_project_root())

    return str(relative_path), text_content