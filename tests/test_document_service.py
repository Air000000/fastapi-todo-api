from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import HTTPException

from database import create_db_and_tables
from services.document_service import (
    calculate_checksum,
    create_document_from_bytes,
    get_document,
    list_documents,
)


def unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def test_create_document_from_bytes_saves_file_and_record(tmp_path: Path):
    create_db_and_tables()

    content = b"# VPN Guide\n\nCheck network, account status, and VPN client config."
    tenant_id = unique_name("tenant_demo")

    document = create_document_from_bytes(
        filename="vpn_guide.md",
        content=content,
        tenant_id=tenant_id,
        uploaded_by="user_demo",
        category="it",
        storage_root=tmp_path,
    )

    assert document.id.startswith("doc_")
    assert document.tenant_id == tenant_id
    assert document.uploaded_by == "user_demo"
    assert document.filename == "vpn_guide.md"
    assert document.file_type == "md"
    assert document.category == "it"
    assert document.status == "uploaded"
    assert document.version == 1
    assert document.checksum == calculate_checksum(content)

    saved_path = Path(document.source_path)
    assert saved_path.exists()
    assert saved_path.read_bytes() == content


def test_create_document_rejects_unsupported_file_type(tmp_path: Path):
    create_db_and_tables()

    with pytest.raises(HTTPException) as exc_info:
        create_document_from_bytes(
            filename="policy.pdf",
            content=b"fake pdf content",
            tenant_id=unique_name("tenant_demo"),
            uploaded_by="user_demo",
            category="hr",
            storage_root=tmp_path,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Only .md and .txt files are supported"


def test_list_documents_filters_by_tenant_and_category(tmp_path: Path):
    create_db_and_tables()

    tenant_a = unique_name("tenant_a")
    tenant_b = unique_name("tenant_b")

    hr_document = create_document_from_bytes(
        filename="leave_policy.txt",
        content=b"Annual leave must be submitted in the HR system.",
        tenant_id=tenant_a,
        uploaded_by="user_demo",
        category="hr",
        storage_root=tmp_path,
    )

    create_document_from_bytes(
        filename="vpn_guide.md",
        content=b"VPN troubleshooting guide.",
        tenant_id=tenant_a,
        uploaded_by="user_demo",
        category="it",
        storage_root=tmp_path,
    )

    create_document_from_bytes(
        filename="other_tenant_hr.txt",
        content=b"Other tenant HR policy.",
        tenant_id=tenant_b,
        uploaded_by="user_demo",
        category="hr",
        storage_root=tmp_path,
    )

    documents, total = list_documents(
        tenant_id=tenant_a,
        category="hr",
    )

    assert total == 1
    assert len(documents) == 1
    assert documents[0].id == hr_document.id
    assert documents[0].tenant_id == tenant_a
    assert documents[0].category == "hr"


def test_get_document_requires_matching_tenant(tmp_path: Path):
    create_db_and_tables()

    tenant_id = unique_name("tenant_demo")
    document = create_document_from_bytes(
        filename="invoice_rules.md",
        content=b"Invoice rules for reimbursement.",
        tenant_id=tenant_id,
        uploaded_by="user_demo",
        category="finance",
        storage_root=tmp_path,
    )

    fetched = get_document(
        document_id=document.id,
        tenant_id=tenant_id,
    )

    assert fetched.id == document.id
    assert fetched.tenant_id == tenant_id

    with pytest.raises(HTTPException) as exc_info:
        get_document(
            document_id=document.id,
            tenant_id=unique_name("tenant_other"),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Document not found"