from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, File, Form, Query, UploadFile

from schemas.document import (
    DocumentCategory,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatus,
)
from services.document_service import (
    create_document_from_bytes,
    get_document as get_document_service,
    list_documents as list_documents_service,
)


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

MOCK_TENANT_ID = "tenant_demo"
MOCK_USER_ID = "user_demo"


def get_document_storage_root() -> Path:
    return Path(os.getenv("DOCUMENT_STORAGE_ROOT", "storage/documents"))


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    category: DocumentCategory = Form("other"),
) -> DocumentResponse:
    content = await file.read()

    document = create_document_from_bytes(
        filename=file.filename or "",
        content=content,
        tenant_id=MOCK_TENANT_ID,
        uploaded_by=MOCK_USER_ID,
        category=category,
        storage_root=get_document_storage_root(),
    )

    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    category: DocumentCategory | None = None,
    status: DocumentStatus | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> DocumentListResponse:
    documents, total = list_documents_service(
        tenant_id=MOCK_TENANT_ID,
        category=category,
        status=status,
        limit=limit,
        offset=offset,
    )

    return DocumentListResponse(
        items=[
            DocumentResponse.model_validate(document)
            for document in documents
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str) -> DocumentResponse:
    document = get_document_service(
        document_id=document_id,
        tenant_id=MOCK_TENANT_ID,
    )

    return DocumentResponse.model_validate(document)