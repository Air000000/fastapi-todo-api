# Ticket Agent MVP 阶段报告

## 1. 阶段目标

本阶段目标是在 RAG Core 和 Ticket CRUD 的基础上，实现一个受控 Ticket Agent MVP。

Agent 不直接自动创建工单，而是采用 preview / confirm 两阶段流程：

```text
用户问题
↓
RAG 检索企业知识库
↓
生成 ticket preview
↓
用户确认
↓
创建真实 ticket
```

## 2. 当前实现范围
当前已实现：

POST /agent/ticket/preview
POST /agent/ticket/confirm
工单草稿 TicketDraft
知识来源 TicketAgentSource
preview 阶段不写数据库
confirm 阶段调用 ticket_service.create_ticket()
mock tenant/user context
API 层测试
Service 层测试

## 3. 核心 API
Method	Path	作用
POST	/agent/ticket/preview	根据用户问题生成工单草稿
POST	/agent/ticket/confirm	用户确认后创建真实工单

## 4. Preview 流程
```text
TicketAgentPreviewRequest
↓
preview_ticket()
↓
normalize_rag_category()
↓
search_chroma()
↓
TicketAgentSource
↓
should_create_ticket()
↓
TicketDraft
↓
TicketAgentPreviewResponse
```

Preview 阶段只返回建议，不写数据库。

## 5. Confirm 流程
```text
TicketAgentConfirmRequest
↓
confirm_ticket()
↓
TicketCreate
↓
ticket_service.create_ticket()
↓
TicketResponse
↓
TicketAgentConfirmResponse
```

## 6. 规则型 Agent 设计
当前第一版使用规则判断：

故障、异常、失败、无法连接等问题：建议创建工单
普通知识咨询：暂不建议创建工单
生产系统、大面积、数据泄露、安全事件等问题：优先级为 urgent
普通故障类问题：优先级为 high
咨询类问题：优先级为 low

## 7. 已发现并修复的问题
子串误判问题

原始规则中，客户 会误命中 客户端：

```text
"客户" in "客户端" == True
```

这会导致普通 VPN 客户端问题被误判为 urgent。

修复方式：

删除过于宽泛的 urgent 关键词
使用更具体的短语，如 客户现场、客户阻塞
增加 service 测试防止回归
咨询问题误判问题

请问请假怎么申请？ 原先会因为包含 申请 被判定为需要创建工单。

修复方式：

从支持类关键词中移除过宽的 申请
保留更明确的故障、异常、权限、开通类信号
增加知识咨询测试用例

## 8. 测试覆盖
当前测试覆盖：

文件	覆盖内容
tests/test_agent_ticket_api.py	Agent API 层 request / response / validation
tests/test_ticket_agent_service.py	Agent service 规则、priority、category、confirm 调用
tests/test_tickets.py	Ticket CRUD
tests/test_rag_api.py	RAG API
tests/test_rag_service.py	RAG service
tests/test_todos.py	Todo CRUD

当前全量测试：

pytest passed

## 9. 当前局限
当前 Ticket Agent MVP 仍是规则型 workflow，暂未引入复杂 LLM planner。

当前局限：

工单标题和描述仍基于规则生成
没有 tool_calls 审计表
没有 approval_requests 表
没有 agent_runs 运行记录
没有记录 token、latency、retrieval distance 统计
没有复杂多轮确认
没有权限系统，只使用 mock tenant/user
