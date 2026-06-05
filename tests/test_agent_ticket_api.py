from datetime import datetime

from fastapi.testclient import TestClient

from main import app
from schemas.agent_ticket import (
    TicketAgentConfirmResponse,
    TicketAgentPreviewResponse,
    TicketAgentSource,
    TicketDraft,
)
from schemas.ticket import TicketResponse


def test_agent_ticket_preview_returns_draft(monkeypatch):
    calls = {}

    def fake_preview_ticket_service(request, tenant_id: str):
        calls["message"] = request.message
        calls["category"] = request.category
        calls["tenant_id"] = tenant_id

        return TicketAgentPreviewResponse(
            should_create_ticket=True,
            reason="用户描述包含故障信号，建议创建工单。",
            draft=TicketDraft(
                title="VPN 连不上",
                description="用户远程办公时 VPN 连不上，重启客户端后仍未恢复。",
                category="it",
                priority="high",
            ),
            sources=[
                TicketAgentSource(
                    document_id="doc_vpn_guide",
                    chunk_id="doc_vpn_guide_chunk_1",
                    title="vpn_guide",
                    source_path="experiments/docs/it/vpn_guide.md",
                    distance=0.52,
                    preview="VPN 排查说明...",
                    category="it",
                )
            ],
        )

    monkeypatch.setattr(
        "routers.agent_ticket.preview_ticket_service",
        fake_preview_ticket_service,
    )

    with TestClient(app) as client:
        response = client.post(
            "/agent/ticket/preview",
            json={
                "message": "VPN 连不上，重启客户端也没用",
                "category": "it",
            },
        )

    assert response.status_code == 200

    data = response.json()
    assert data["should_create_ticket"] is True
    assert data["reason"] == "用户描述包含故障信号，建议创建工单。"
    assert data["draft"]["title"] == "VPN 连不上"
    assert data["draft"]["category"] == "it"
    assert data["draft"]["priority"] == "high"
    assert data["sources"][0]["document_id"] == "doc_vpn_guide"
    assert data["sources"][0]["category"] == "it"

    assert calls["message"] == "VPN 连不上，重启客户端也没用"
    assert calls["category"] == "it"
    assert calls["tenant_id"] == "tenant_demo"


def test_agent_ticket_preview_can_return_no_ticket(monkeypatch):
    def fake_preview_ticket_service(request, tenant_id: str):
        return TicketAgentPreviewResponse(
            should_create_ticket=False,
            reason="知识库中已检索到相关资料，暂不建议创建工单。",
            draft=None,
            sources=[
                TicketAgentSource(
                    document_id="doc_leave_policy",
                    chunk_id="doc_leave_policy_chunk_1",
                    title="leave_policy",
                    source_path="experiments/docs/hr/leave_policy.md",
                    distance=0.48,
                    preview="请假流程说明...",
                    category="hr",
                )
            ],
        )

    monkeypatch.setattr(
        "routers.agent_ticket.preview_ticket_service",
        fake_preview_ticket_service,
    )

    with TestClient(app) as client:
        response = client.post(
            "/agent/ticket/preview",
            json={
                "message": "请假怎么申请？",
                "category": "hr",
            },
        )

    assert response.status_code == 200

    data = response.json()
    assert data["should_create_ticket"] is False
    assert data["draft"] is None
    assert data["sources"][0]["document_id"] == "doc_leave_policy"


def test_agent_ticket_confirm_creates_ticket(monkeypatch):
    calls = {}

    def fake_confirm_ticket_service(request, tenant_id: str, created_by: str):
        calls["draft_title"] = request.draft.title
        calls["draft_category"] = request.draft.category
        calls["tenant_id"] = tenant_id
        calls["created_by"] = created_by

        return TicketAgentConfirmResponse(
            ticket=TicketResponse(
                id=1,
                tenant_id=tenant_id,
                created_by=created_by,
                title=request.draft.title,
                description=request.draft.description,
                category=request.draft.category,
                priority=request.draft.priority,
                status="open",
                created_at=datetime(2026, 1, 1, 10, 0, 0),
                updated_at=datetime(2026, 1, 1, 10, 0, 0),
            )
        )

    monkeypatch.setattr(
        "routers.agent_ticket.confirm_ticket_service",
        fake_confirm_ticket_service,
    )

    with TestClient(app) as client:
        response = client.post(
            "/agent/ticket/confirm",
            json={
                "draft": {
                    "title": "VPN 连不上",
                    "description": "用户远程办公时 VPN 连不上，重启客户端后仍未恢复。",
                    "category": "it",
                    "priority": "high",
                }
            },
        )

    assert response.status_code == 201

    data = response.json()
    assert data["ticket"]["id"] == 1
    assert data["ticket"]["tenant_id"] == "tenant_demo"
    assert data["ticket"]["created_by"] == "user_demo"
    assert data["ticket"]["title"] == "VPN 连不上"
    assert data["ticket"]["category"] == "it"
    assert data["ticket"]["priority"] == "high"
    assert data["ticket"]["status"] == "open"

    assert calls["draft_title"] == "VPN 连不上"
    assert calls["draft_category"] == "it"
    assert calls["tenant_id"] == "tenant_demo"
    assert calls["created_by"] == "user_demo"


def test_agent_ticket_preview_with_empty_message_should_fail():
    with TestClient(app) as client:
        response = client.post(
            "/agent/ticket/preview",
            json={
                "message": "",
                "category": "it",
            },
        )

    assert response.status_code == 422


def test_agent_ticket_preview_with_invalid_category_should_fail():
    with TestClient(app) as client:
        response = client.post(
            "/agent/ticket/preview",
            json={
                "message": "VPN 连不上",
                "category": "invalid",
            },
        )

    assert response.status_code == 422


def test_agent_ticket_confirm_with_invalid_priority_should_fail():
    with TestClient(app) as client:
        response = client.post(
            "/agent/ticket/confirm",
            json={
                "draft": {
                    "title": "VPN 连不上",
                    "description": "用户远程办公时 VPN 连不上。",
                    "category": "it",
                    "priority": "invalid",
                }
            },
        )

    assert response.status_code == 422