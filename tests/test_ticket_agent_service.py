from datetime import datetime
from types import SimpleNamespace

from schemas.agent_ticket import (
    TicketAgentConfirmRequest,
    TicketAgentPreviewRequest,
    TicketDraft,
)
from services.ticket_agent_service import (
    confirm_ticket,
    infer_priority,
    normalize_rag_category,
    preview_ticket,
)


def make_search_result(
    document_id: str = "doc_vpn_guide",
    chunk_id: str = "doc_vpn_guide_chunk_1",
    title: str = "vpn_guide",
    category: str = "it",
    distance: float = 0.52,
    content: str = "VPN 故障排查说明。",
):
    return SimpleNamespace(
        document_id=document_id,
        chunk_id=chunk_id,
        title=title,
        source_path=f"experiments/docs/{category}/{title}.md",
        distance=distance,
        content=content,
        category=category,
    )


def test_normalize_rag_category():
    """
    确认 other 不会被传给 RAG filter，而是直接返回 None，表示不使用 category 过滤 RAG 来源。
    """
    assert normalize_rag_category("it") == "it"
    assert normalize_rag_category("hr") == "hr"
    assert normalize_rag_category("finance") == "finance"
    assert normalize_rag_category("admin") == "admin"
    assert normalize_rag_category("security") == "security"
    assert normalize_rag_category("other") is None
    assert normalize_rag_category(None) is None


def test_infer_priority_client_keyword_should_not_be_urgent():
    """
    防止“客户端”误命中“客户”导致优先级被误判为 urgent。
    """
    priority = infer_priority("VPN 连不上，重启客户端也没用")

    assert priority == "high"


def test_infer_priority_production_incident_should_be_urgent():      
    """
    确认生产系统大面积无法访问的情况应被标记为 urgent。
    """
    priority = infer_priority("生产系统大面积无法访问，客户现场已经阻塞")

    assert priority == "urgent"


def test_preview_ticket_returns_high_priority_for_common_vpn_issue(monkeypatch):
    """
    普通 VPN 故障应是 high
    """
    calls = {}

    def fake_search_chroma(query: str, top_k: int, tenant_id: str, category: str | None):
        calls["query"] = query
        calls["top_k"] = top_k
        calls["tenant_id"] = tenant_id
        calls["category"] = category
        return [
            make_search_result(
                document_id="doc_vpn_guide",
                chunk_id="doc_vpn_guide_chunk_1",
                title="vpn_guide",
                category="it",
            )
        ]

    monkeypatch.setattr(
        "services.ticket_agent_service.search_chroma",
        fake_search_chroma,
    )

    response = preview_ticket(
        request=TicketAgentPreviewRequest(
            message="VPN 连不上，重启客户端也没用",
            category="it",
        ),
        tenant_id="tenant_demo",
    )

    assert response.should_create_ticket is True
    assert response.draft is not None
    assert response.draft.category == "it"
    assert response.draft.priority == "high"
    assert response.sources[0].document_id == "doc_vpn_guide"

    assert calls["query"] == "VPN 连不上，重启客户端也没用"
    assert calls["tenant_id"] == "tenant_demo"
    assert calls["category"] == "it"


def test_preview_ticket_with_other_category_does_not_filter_rag_by_other(monkeypatch):
    """
    当用户选择的 category 是 other 时，不将 other 传给 RAG 过滤器，而是直接不使用 category 过滤。
    """
    calls = {}

    def fake_search_chroma(query: str, top_k: int, tenant_id: str, category: str | None):
        calls["query"] = query
        calls["tenant_id"] = tenant_id
        calls["category"] = category
        return []

    monkeypatch.setattr(
        "services.ticket_agent_service.search_chroma",
        fake_search_chroma,
    )

    response = preview_ticket(
        request=TicketAgentPreviewRequest(
            message="不知道这个问题应该找哪个部门处理",
            category="other",
        ),
        tenant_id="tenant_demo",
    )

    assert calls["category"] is None
    assert response.should_create_ticket is True
    assert response.draft is not None
    assert response.draft.category == "other"
    assert response.sources == []


def test_preview_ticket_infers_category_from_top_source_when_category_missing(monkeypatch):
    """
    用户不传 category 时可从 source 推断
    """
    def fake_search_chroma(query: str, top_k: int, tenant_id: str, category: str | None):
        return [
            make_search_result(
                document_id="doc_data_access_policy",
                chunk_id="doc_data_access_policy_chunk_1",
                title="data_access_policy",
                category="security",
                content="数据访问权限申请说明。",
            )
        ]

    monkeypatch.setattr(
        "services.ticket_agent_service.search_chroma",
        fake_search_chroma,
    )

    response = preview_ticket(
        request=TicketAgentPreviewRequest(
            message="申请客户数据访问权限失败了",
            category=None,
        ),
        tenant_id="tenant_demo",
    )

    assert response.should_create_ticket is True
    assert response.draft is not None
    assert response.draft.category == "security"
    assert response.draft.priority == "high"
    assert response.sources[0].category == "security"


def test_preview_ticket_can_return_no_ticket_for_knowledge_question(monkeypatch):
    """
    知识咨询不创建工单
    """
    def fake_search_chroma(query: str, top_k: int, tenant_id: str, category: str | None):
        return [
            make_search_result(
                document_id="doc_leave_policy",
                chunk_id="doc_leave_policy_chunk_1",
                title="leave_policy",
                category="hr",
                content="请假需要在系统中提交申请。",
            )
        ]

    monkeypatch.setattr(
        "services.ticket_agent_service.search_chroma",
        fake_search_chroma,
    )

    response = preview_ticket(
        request=TicketAgentPreviewRequest(
            message="请问请假怎么申请？",
            category="hr",
        ),
        tenant_id="tenant_demo",
    )

    assert response.should_create_ticket is False
    assert response.draft is None
    assert response.sources[0].document_id == "doc_leave_policy"


def test_confirm_ticket_calls_create_ticket_service(monkeypatch):
    """
    confirm 复用 Ticket Service 创建真实工单，并记录 AgentOps 轨迹
    """
    calls = {}

    def fake_update_approval_request(approval_request_id, tenant_id, approval_request_update):
        calls["approval_request_id"] = approval_request_id
        calls["approval_tenant_id"] = tenant_id
        calls["approval_status"] = approval_request_update.status
        calls["approved_by"] = approval_request_update.approved_by
        return SimpleNamespace(
            id=approval_request_id,
            tenant_id=tenant_id,
            status=approval_request_update.status,
            approved_by=approval_request_update.approved_by,
        )

    def fake_create_tool_call(tool_call_create):
        calls["tool_agent_run_id"] = tool_call_create.agent_run_id
        calls["tool_tenant_id"] = tool_call_create.tenant_id
        calls["tool_name"] = tool_call_create.tool_name
        calls["tool_input_json"] = tool_call_create.tool_input_json
        calls["tool_status"] = tool_call_create.status
        return SimpleNamespace(
            id=300,
            agent_run_id=tool_call_create.agent_run_id,
            tenant_id=tool_call_create.tenant_id,
            tool_name=tool_call_create.tool_name,
            status=tool_call_create.status,
        )

    def fake_update_tool_call(tool_call_id, tenant_id, tool_call_update):
        calls["updated_tool_call_id"] = tool_call_id
        calls["updated_tool_tenant_id"] = tenant_id
        calls["updated_tool_status"] = tool_call_update.status
        calls["tool_output_json"] = tool_call_update.tool_output_json
        return SimpleNamespace(
            id=tool_call_id,
            tenant_id=tenant_id,
            status=tool_call_update.status,
            tool_output_json=tool_call_update.tool_output_json,
        )

    def fake_update_agent_run(agent_run_id, tenant_id, agent_run_update):
        calls["updated_agent_run_id"] = agent_run_id
        calls["updated_agent_tenant_id"] = tenant_id
        calls["agent_run_status"] = agent_run_update.status
        calls["agent_result_summary"] = agent_run_update.result_summary
        return SimpleNamespace(
            id=agent_run_id,
            tenant_id=tenant_id,
            status=agent_run_update.status,
            result_summary=agent_run_update.result_summary,
        )

    def fake_create_ticket_service(ticket_create, tenant_id: str, created_by: str):
        calls["title"] = ticket_create.title
        calls["description"] = ticket_create.description
        calls["category"] = ticket_create.category
        calls["priority"] = ticket_create.priority
        calls["tenant_id"] = tenant_id
        calls["created_by"] = created_by

        return SimpleNamespace(
            id=100,
            tenant_id=tenant_id,
            created_by=created_by,
            title=ticket_create.title,
            description=ticket_create.description,
            category=ticket_create.category,
            priority=ticket_create.priority,
            status="open",
            created_at=datetime(2026, 1, 1, 10, 0, 0),
            updated_at=datetime(2026, 1, 1, 10, 0, 0),
        )

    monkeypatch.setattr(
        "services.ticket_agent_service.update_approval_request",
        fake_update_approval_request,
    )
    monkeypatch.setattr(
        "services.ticket_agent_service.create_tool_call",
        fake_create_tool_call,
    )
    monkeypatch.setattr(
        "services.ticket_agent_service.update_tool_call",
        fake_update_tool_call,
    )
    monkeypatch.setattr(
        "services.ticket_agent_service.update_agent_run",
        fake_update_agent_run,
    )
    monkeypatch.setattr(
        "services.ticket_agent_service.create_ticket_service",
        fake_create_ticket_service,
    )

    response = confirm_ticket(
        request=TicketAgentConfirmRequest(
            agent_run_id=1,
            approval_request_id=10,
            draft=TicketDraft(
                title="VPN 连不上",
                description="用户远程办公时 VPN 连不上。",
                category="it",
                priority="high",
            ),
        ),
        tenant_id="tenant_demo",
        created_by="user_demo",
    )

    assert response.agent_run_id == 1
    assert response.approval_request_id == 10
    assert response.tool_call_id == 300
    assert response.ticket.id == 100
    assert response.ticket.tenant_id == "tenant_demo"
    assert response.ticket.created_by == "user_demo"
    assert response.ticket.title == "VPN 连不上"
    assert response.ticket.category == "it"
    assert response.ticket.priority == "high"
    assert response.ticket.status == "open"

    assert calls["approval_request_id"] == 10
    assert calls["approval_status"] == "approved"
    assert calls["approved_by"] == "user_demo"

    assert calls["tool_agent_run_id"] == 1
    assert calls["tool_name"] == "create_ticket"
    assert calls["tool_status"] == "pending"
    assert calls["updated_tool_call_id"] == 300
    assert calls["updated_tool_status"] == "success"

    assert calls["updated_agent_run_id"] == 1
    assert calls["agent_run_status"] == "completed"

    assert calls["title"] == "VPN 连不上"
    assert calls["category"] == "it"
    assert calls["priority"] == "high"
    assert calls["tenant_id"] == "tenant_demo"
    assert calls["created_by"] == "user_demo"