from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def generate_document_id() -> str:
    return f"doc_{uuid4().hex}"


def generate_chunk_id() -> str:
    return f"chunk_{uuid4().hex}"


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: str = Field(default_factory=generate_document_id, primary_key=True)

    tenant_id: str = Field(index=True)
    uploaded_by: str = Field(index=True)

    filename: str = Field(max_length=255)
    file_type: str = Field(max_length=20)
    category: str = Field(default="other", index=True)

    source_path: str = Field(max_length=1000)

    status: str = Field(default="uploaded", index=True)
    version: int = Field(default=1)
    checksum: str = Field(max_length=128)

    chunk_count: int = Field(default=0)
    error_message: Optional[str] = Field(default=None, max_length=2000)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"

    id: str = Field(default_factory=generate_chunk_id, primary_key=True)

    tenant_id: str = Field(index=True)
    document_id: str = Field(index=True)

    chunk_index: int = Field(index=True)
    content: str = Field(max_length=8000)
    category: str = Field(default="other", index=True)

    metadata_json: str = Field(default="{}")
    embedding_id: str = Field(index=True, max_length=255)

    created_at: datetime = Field(default_factory=utc_now)