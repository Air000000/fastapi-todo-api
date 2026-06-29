from models.document import Document, DocumentChunk
from schemas.document import DocumentResponse


def test_document_model_defaults():
    document = Document(
        tenant_id="tenant_demo",
        uploaded_by="user_demo",
        filename="vpn_guide.md",
        file_type="md",
        category="it",
        source_path="storage/documents/tenant_demo/doc_test/v1/vpn_guide.md",
        checksum="abc123",
    )

    assert document.id.startswith("doc_")
    assert document.tenant_id == "tenant_demo"
    assert document.uploaded_by == "user_demo"
    assert document.filename == "vpn_guide.md"
    assert document.file_type == "md"
    assert document.category == "it"
    assert document.status == "uploaded"
    assert document.version == 1
    assert document.chunk_count == 0
    assert document.error_message is None
    assert document.created_at is not None
    assert document.updated_at is not None


def test_document_chunk_model_fields():
    chunk = DocumentChunk(
        tenant_id="tenant_demo",
        document_id="doc_test",
        chunk_index=0,
        content="VPN 连接失败时，用户应先检查网络、账号状态和客户端配置。",
        category="it",
        metadata_json='{"document_id": "doc_test", "category": "it"}',
        embedding_id="doc:doc_test:v1:chunk:0",
    )

    assert chunk.id.startswith("chunk_")
    assert chunk.tenant_id == "tenant_demo"
    assert chunk.document_id == "doc_test"
    assert chunk.chunk_index == 0
    assert chunk.category == "it"
    assert chunk.embedding_id == "doc:doc_test:v1:chunk:0"
    assert "VPN" in chunk.content
    assert chunk.created_at is not None


def test_document_response_schema_from_model():
    document = Document(
        id="doc_test",
        tenant_id="tenant_demo",
        uploaded_by="user_demo",
        filename="leave_policy.txt",
        file_type="txt",
        category="hr",
        source_path="storage/documents/tenant_demo/doc_test/v1/leave_policy.txt",
        checksum="checksum123",
    )

    response = DocumentResponse.model_validate(document)

    assert response.id == "doc_test"
    assert response.tenant_id == "tenant_demo"
    assert response.uploaded_by == "user_demo"
    assert response.filename == "leave_policy.txt"
    assert response.file_type == "txt"
    assert response.category == "hr"
    assert response.status == "uploaded"
    assert response.version == 1
    assert response.chunk_count == 0