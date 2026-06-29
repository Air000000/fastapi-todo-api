from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


DocumentCategory = Literal[
    "it",
    "hr",
    "finance",
    "admin",
    "security",
    "other",
]

DocumentStatus = Literal[
    "uploaded",
    "indexing",
    "indexed",
    "failed",
    "deleted",
]


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    uploaded_by: str

    filename: str
    file_type: str
    category: str

    source_path: str

    status: str
    version: int
    checksum: str

    chunk_count: int
    error_message: str | None = None

    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    offset: int = Field(..., ge=0)


class DocumentIndexResponse(BaseModel):
    document_id: str
    status: str
    chunk_count: int = Field(..., ge=0)


class DocumentDeleteResponse(BaseModel):
    document_id: str
    status: str
    deleted_embeddings: int = Field(..., ge=0)