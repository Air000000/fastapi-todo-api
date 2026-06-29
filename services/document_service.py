from __future__ import annotations

import hashlib
import re
from pathlib import Path

from fastapi import HTTPException
from sqlmodel import Session, select

from database import engine
from models.document import Document, generate_document_id


ALLOWED_FILE_TYPES = {"md", "txt"}
ALLOWED_CATEGORIES = {"it", "hr", "finance", "admin", "security", "other"}

DEFAULT_STORAGE_ROOT = Path("storage/documents")
MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024


def calculate_checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def get_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")

    if suffix not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only .md and .txt files are supported",
        )

    return suffix


def build_safe_filename(filename: str) -> str:
    original_name = Path(filename or "").name

    if not original_name:
        raise HTTPException(status_code=400, detail="Filename is required")

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", original_name).strip("._")

    if not safe_name:
        raise HTTPException(status_code=400, detail="Filename is invalid")

    return safe_name


def validate_document_content(content: bytes) -> None:
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File is too large",
        )


def validate_category(category: str) -> str:
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid document category")

    return category


def build_document_storage_path(
    storage_root: Path,
    tenant_id: str,
    document_id: str,
    version: int,
    safe_filename: str,
) -> Path:
    return storage_root / tenant_id / document_id / f"v{version}" / safe_filename


def create_document_from_bytes(
    *,
    filename: str,
    content: bytes,
    tenant_id: str,
    uploaded_by: str,
    category: str = "other",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
) -> Document:
    safe_filename = build_safe_filename(filename)
    file_type = get_file_type(safe_filename)
    validate_document_content(content)
    category = validate_category(category)

    document_id = generate_document_id()
    version = 1
    checksum = calculate_checksum(content)

    save_path = build_document_storage_path(
        storage_root=storage_root,
        tenant_id=tenant_id,
        document_id=document_id,
        version=version,
        safe_filename=safe_filename,
    )

    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(content)

    document = Document(
        id=document_id,
        tenant_id=tenant_id,
        uploaded_by=uploaded_by,
        filename=filename,
        file_type=file_type,
        category=category,
        source_path=save_path.as_posix(),
        status="uploaded",
        version=version,
        checksum=checksum,
    )

    with Session(engine) as session:
        session.add(document)
        session.commit()
        session.refresh(document)
        return document


def list_documents(
    *,
    tenant_id: str,
    category: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Document], int]:
    with Session(engine) as session:
        statement = select(Document).where(Document.tenant_id == tenant_id)

        if category is not None:
            statement = statement.where(Document.category == category)

        if status is not None:
            statement = statement.where(Document.status == status)
        else:
            statement = statement.where(Document.status != "deleted")

        documents = list(session.exec(statement).all())
        total = len(documents)

        return documents[offset : offset + limit], total


def get_document(
    *,
    document_id: str,
    tenant_id: str,
) -> Document:
    with Session(engine) as session:
        document = session.get(Document, document_id)

        if (
            document is None
            or document.tenant_id != tenant_id
            or document.status == "deleted"
        ):
            raise HTTPException(status_code=404, detail="Document not found")

        return document