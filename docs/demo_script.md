# Demo Script

Enterprise Support AI Copilot 演示脚本。

本脚本用于展示当前 `learn-rag` 分支的核心能力：

```text
Enterprise RAG Core
Ticket CRUD
Ticket Agent preview / confirm
Human approval
AgentOps tool_calls audit
AgentOps metrics summary
```

---

## 1. Demo Goal

本次 demo 展示一条完整企业支持流程：

```text
员工提出内部支持问题
↓
系统基于企业知识库检索相关资料
↓
Ticket Agent 判断是否需要创建工单
↓
生成 ticket preview
↓
用户人工确认
↓
系统创建真实 ticket
↓
AgentOps 记录 agent_run / tool_calls / approval_request
↓
通过 metrics summary 查看整体运行状态
```

重点展示：

```text
1. RAG 返回 answer + sources
2. Ticket Agent 不直接创建工单，而是先生成 preview
3. create_ticket 必须经过 approval_request 确认
4. search_kb / classify_ticket / create_ticket 均有 tool_call 审计记录
5. /agent-ops/metrics/summary 能汇总 AgentOps 状态
```

---

## 2. Prerequisites

确保已安装依赖：

```bash
pip install -r requirements.txt
```

确保 `.env` 已配置：

```env
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen3.5-plus
```

如果本地 SQLite 表结构较旧，可以在开发环境中删除本地数据库后重新启动服务。

PowerShell 示例：

```powershell
dir *.db -Recurse
dir *.sqlite -Recurse
```

找到本地开发数据库后删除，例如：

```powershell
Remove-Item .\app.db
```

实际文件名以本地项目为准。

---

## 3. Start API Server

启动 FastAPI 服务：

```bash
uvicorn main:app --reload
```

打开 Swagger UI：

```text
http://127.0.0.1:8000/docs
```

先检查健康接口：

```http
GET /health
```

预期结果：

```json
{
  "status": "ok"
}
```

---

## 4. Run RAG Eval

运行 Enterprise RAG eval：

```bash
python -m experiments.evals.eval_enterprise_chroma_retrieval
```

预期关注指标：

```text
hit@1
hit@3
mrr@3
avg latency
category breakdown
failed cases
```

当前企业文档集预期结果接近：

```text
Total: 30
hit@1: 0.97
hit@3: 1.00
mrr@3: 0.98
```

讲解点：

```text
RAG 不只提供接口，还配套了 retrieval eval，用于验证检索效果。
当前 eval 覆盖 IT、HR、finance、admin、security 等企业内部支持分类。
```

---

## 5. RAG Search Demo

Swagger 中打开：

```http
POST /rag/search
```

请求体：

```json
{
  "query": "VPN 连不上应该先检查什么？",
  "top_k": 3,
  "category": "it"
}
```

预期返回字段：

```text
document_id
chunk_id
title
source_path
chunk_index
distance
preview
tenant_id
category
```

预期讲解：

```text
/rag/search 展示底层检索结果。
它支持 category filter，同时 tenant_id 由 mock tenant context 提供。
返回结果中包含 source_path、document_id、chunk_id 和 distance。
```

截图建议：

```text
截取 /rag/search response 中的 sources / document_id / distance。
```

---

## 6. RAG Ask Demo

Swagger 中打开：

```http
POST /rag/ask
```

请求体：

```json
{
  "question": "VPN 连不上应该先检查什么？",
  "top_k": 3,
  "max_distance": 0.9,
  "category": "it"
}
```

预期返回字段：

```text
answer
retrieval_status
top_distance
sources
```

预期讲解：

```text
/rag/ask 执行完整 RAG 流程：
先检索企业知识库，再基于检索上下文生成回答，并返回 sources。
如果检索不到足够依据，系统会返回拒答。
```

截图建议：

```text
截取 answer + sources。
```

---

## 7. Ticket CRUD Demo

### 7.1 Create Ticket

Swagger 中打开：

```http
POST /tickets
```

请求体：

```json
{
  "title": "VPN 无法连接",
  "description": "用户反馈 VPN 客户端无法连接，重启后仍失败。",
  "category": "it",
  "priority": "high"
}
```

预期结果：

```text
返回新建 ticket
status 默认为 open
包含 ticket_id / created_at / updated_at
```

---

### 7.2 List Tickets

Swagger 中打开：

```http
GET /tickets
```

预期结果：

```text
可以看到刚才创建的 ticket
```

---

### 7.3 Get Ticket

Swagger 中打开：

```http
GET /tickets/{ticket_id}
```

填入刚才创建的 ticket id。

预期结果：

```text
返回指定 ticket 详情
```

---

### 7.4 Update Ticket

Swagger 中打开：

```http
PATCH /tickets/{ticket_id}
```

请求体示例：

```json
{
  "status": "in_progress"
}
```

预期结果：

```text
ticket status 更新为 in_progress
```

讲解点：

```text
Ticket CRUD 是后续 Agent 工具 create_ticket 的业务落地点。
Agent 最终不是只返回文字，而是可以接入后端业务对象。
```

---

## 8. Ticket Agent Preview Demo

Swagger 中打开：

```http
POST /agent/ticket/preview
```

请求体：

```json
{
  "message": "VPN 连不上，重启客户端也没用",
  "category": "it"
}
```

预期返回字段：

```text
agent_run_id
approval_request_id
should_create_ticket
reason
draft
sources
```

预期结果：

```text
should_create_ticket = true
approval_request_id 不为空
draft 包含 title / description / category / priority
sources 包含 RAG 检索来源
```

记录以下值：

```text
agent_run_id = <PREVIEW_AGENT_RUN_ID>
approval_request_id = <PREVIEW_APPROVAL_REQUEST_ID>
draft = <PREVIEW_DRAFT>
```

讲解点：

```text
preview 阶段不会创建真实 ticket。
它只创建 agent_run、tool_calls、ticket draft 和 approval_request。
真实 ticket 必须等 confirm 阶段才会创建。
```

截图建议：

```text
截取 preview response 中的 agent_run_id、approval_request_id、draft、sources。
```

---

## 9. Inspect Preview Tool Calls

Swagger 中打开：

```http
GET /agent-ops/runs/{agent_run_id}/tool-calls
```

填入 preview 返回的：

```text
agent_run_id
```

预期看到两条 tool_call：

```text
search_kb
classify_ticket
```

预期状态：

```text
search_kb.status = success
classify_ticket.status = success
```

检查字段：

```text
tool_name
tool_input_json
tool_output_json
status
error_message
latency_ms
```

讲解点：

```text
search_kb 记录知识库检索动作。
classify_ticket 记录工单判断和分类动作。
preview 阶段的中间决策不是只存在内存里，而是进入 tool_calls 审计记录。
```

截图建议：

```text
截取 search_kb 和 classify_ticket 两条 tool_call。
```

---

## 10. Approval Reject Demo

本节用于展示 rejected flow。

注意：不要使用后续要 confirm 的 approval_request 做 reject。为了保留 confirm 演示，建议重新发起一次 preview。

### 10.1 Create another preview

Swagger 中再次打开：

```http
POST /agent/ticket/preview
```

请求体：

```json
{
  "message": "我需要申请外包账号访问测试环境",
  "category": "security"
}
```

记录返回：

```text
reject_demo_agent_run_id
reject_demo_approval_request_id
```

---

### 10.2 Reject approval request

Swagger 中打开：

```http
POST /agent-ops/approval-requests/{approval_request_id}/reject
```

填入：

```text
reject_demo_approval_request_id
```

预期结果：

```text
approval_request.status = rejected
```

---

### 10.3 Inspect rejected approval

Swagger 中打开：

```http
GET /agent-ops/runs/{agent_run_id}/approval-requests
```

填入：

```text
reject_demo_agent_run_id
```

预期结果：

```text
status = rejected
```

讲解点：

```text
Agent 建议执行动作后，用户可以拒绝审批。
rejected approval_request 不应再被 confirm 执行。
```

截图建议：

```text
截取 rejected approval_request。
```

---

## 11. Ticket Agent Confirm Demo

回到第 8 节的 preview 结果，使用未被 reject 的：

```text
PREVIEW_AGENT_RUN_ID
PREVIEW_APPROVAL_REQUEST_ID
PREVIEW_DRAFT
```

Swagger 中打开：

```http
POST /agent/ticket/confirm
```

请求体必须使用 preview 返回的 draft，不要修改 draft 内容。

示例：

```json
{
  "agent_run_id": 1,
  "approval_request_id": 10,
  "draft": {
    "title": "VPN 连不上，重启客户端也没用",
    "description": "这里必须复制 preview 返回的 description",
    "category": "it",
    "priority": "high"
  }
}
```

预期结果：

```text
返回创建后的 ticket
approval_request 更新为 approved
新增 create_ticket tool_call
agent_run 状态为 completed
```

讲解点：

```text
confirm 阶段会做三类校验：
1. approval_request 必须属于当前 agent_run
2. approval_request.status 必须是 pending
3. confirm draft 必须与服务端保存的 approval_request.draft_json 一致

校验通过后，系统使用服务端保存的 draft 创建真实 ticket。
```

截图建议：

```text
截取 confirm response 中的 ticket_id / status / category / priority。
```

---

## 12. Inspect Full Tool Calls

Swagger 中打开：

```http
GET /agent-ops/runs/{agent_run_id}/tool-calls
```

填入第 8 节 preview 返回的：

```text
PREVIEW_AGENT_RUN_ID
```

confirm 成功后，预期看到三条 tool_call：

```text
search_kb
classify_ticket
create_ticket
```

预期状态：

```text
search_kb.status = success
classify_ticket.status = success
create_ticket.status = success
```

讲解点：

```text
一次完整 Ticket Agent 流程包含三个可审计工具调用：
search_kb 解释查了什么知识库；
classify_ticket 解释为什么建议创建工单；
create_ticket 记录用户确认后真正执行的业务动作。
```

截图建议：

```text
截取完整三条 tool_call。
```

---

## 13. Inspect Approval Requests

Swagger 中打开：

```http
GET /agent-ops/runs/{agent_run_id}/approval-requests
```

填入第 8 节 preview 返回的：

```text
PREVIEW_AGENT_RUN_ID
```

confirm 成功后，预期结果：

```text
approval_request.status = approved
```

讲解点：

```text
approval_requests 记录高风险动作的人工确认状态。
create_ticket 不会在 preview 阶段直接执行，而是在 approval_request approved 后执行。
```

截图建议：

```text
截取 approved approval_request。
```

---

## 14. Inspect AgentOps Metrics

Swagger 中打开：

```http
GET /agent-ops/metrics/summary
```

如果只跑了一条完整 confirm flow，预期接近：

```json
{
  "total_agent_runs": 1,
  "running_agent_runs": 0,
  "completed_agent_runs": 1,
  "failed_agent_runs": 0,
  "cancelled_agent_runs": 0,
  "total_tool_calls": 3,
  "pending_tool_calls": 0,
  "successful_tool_calls": 3,
  "failed_tool_calls": 0,
  "total_approval_requests": 1,
  "pending_approval_requests": 0,
  "approved_approval_requests": 1,
  "rejected_approval_requests": 0,
  "cancelled_approval_requests": 0
}
```

如果同时跑了 rejected demo，预期数字会更多，例如：

```text
total_agent_runs >= 2
total_tool_calls >= 5
total_approval_requests >= 2
approved_approval_requests >= 1
rejected_approval_requests >= 1
```

讲解点：

```text
metrics summary 用于展示 AgentOps 的整体运行状态。
它可以快速回答：
当前有多少 agent_runs？
有多少 tool_calls？
多少成功、失败、pending？
有多少 approval_requests 被 approved / rejected / cancelled？
```

截图建议：

```text
截取 /agent-ops/metrics/summary response。
```

---

## 15. Optional: Confirm Draft Tampering Demo

本节用于展示 confirm 阶段的 payload consistency check。

先创建一个新的 preview：

```http
POST /agent/ticket/preview
```

请求体：

```json
{
  "message": "生产系统无法访问，客户现场已经阻塞",
  "category": "it"
}
```

记录返回：

```text
agent_run_id
approval_request_id
draft
```

然后调用 confirm，但故意修改 draft，例如把 priority 改成：

```json
"priority": "low"
```

预期结果：

```text
confirm 被拒绝
不会创建真实 ticket
不会执行 create_ticket
```

预期错误信息：

```text
Confirm draft does not match approval draft
```

讲解点：

```text
confirm 阶段不会信任客户端临时提交的 draft。
系统会和服务端保存的 approval_request.draft_json 做一致性校验。
```

---

## 16. Optional: Repeated Confirm Demo

本节用于展示 pending approval validation。

对同一个已经 confirm 成功的 approval_request，再次调用：

```http
POST /agent/ticket/confirm
```

预期结果：

```text
confirm 被拒绝
不会重复创建 ticket
```

预期错误信息：

```text
Approval request is not pending
```

讲解点：

```text
approval_request 只能从 pending 被确认一次。
已经 approved / rejected / cancelled 的请求不能重复执行。
```

---

## 17. Expected Demo Summary

完成 demo 后，系统应展示以下能力：

```text
1. RAG 可以基于企业内部文档进行检索和问答
2. RAG response 返回结构化 sources
3. Ticket CRUD 可以创建、查询、更新工单
4. Ticket Agent preview 生成 draft 和 approval_request
5. preview 阶段记录 search_kb 和 classify_ticket tool_call
6. reject / cancel API 可以改变 approval_request 状态
7. confirm 阶段经过审批校验后创建真实 ticket
8. confirm 阶段记录 create_ticket tool_call
9. AgentOps API 可以查看 agent_runs、tool_calls、approval_requests
10. metrics summary 可以汇总 AgentOps 状态
```

建议最终展示顺序：

```text
RAG ask
↓
Ticket Agent preview
↓
Tool calls: search_kb + classify_ticket
↓
Approval request pending
↓
Confirm
↓
Tool calls: search_kb + classify_ticket + create_ticket
↓
Metrics summary
```

---

## 18. Demo Talking Points

简短讲解版本：

```text
这个项目是一个企业内部支持 AI Copilot 后端系统。系统首先通过 RAG 检索企业内部知识库，并返回带 sources 的回答。当用户问题更适合进入支持流程时，Ticket Agent 会生成工单 preview，而不是直接创建工单。只有用户确认后，后端才会创建真实 ticket。整个过程中，search_kb、classify_ticket、create_ticket 都会记录到 tool_calls，审批状态记录到 approval_requests，整体运行状态可以通过 metrics summary 查看。
```

技术讲解版本：

```text
后端采用 FastAPI + SQLModel + Chroma。RAG 层负责知识库检索和 sources 返回；Ticket Agent 层负责 preview / confirm 两阶段工单流程；AgentOps 层负责 agent_runs、tool_calls、approval_requests 和 metrics summary。create_ticket 属于状态变更动作，因此必须经过 approval_request，并在 confirm 阶段校验 ownership、pending 状态和 draft payload 一致性。
```

---

## 19. Optional: Run Smoke Script

如果不想手动通过 Swagger 点击完整流程，可以运行 smoke script：

```bash
python scripts/smoke_agentops_flow.py
```

该脚本会自动验证：

preview
search_kb tool_call
classify_ticket tool_call
pending approval_request
confirm
create_ticket tool_call
approved approval_request
metrics summary