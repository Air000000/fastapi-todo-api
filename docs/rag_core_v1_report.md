# RAG Core v1 评估报告

## 1. 阶段概述

本阶段目标是将项目中的 RAG 能力从早期 learning-doc 实验升级为面向企业内部支持场景的知识库检索与问答底座。

当前版本围绕企业 IT、HR、财务、行政、安全五类支持文档构建本地知识库，支持文档加载、文本切块、embedding、Chroma 向量索引、tenant/category metadata filter、RAG 检索问答接口，以及企业文档检索评估。

当前阶段版本：

```text
RAG Core v1
```

本阶段完成后，项目已经具备以下能力：

```text
企业内部文档
↓
文档加载
↓
文本切块
↓
embedding 批处理
↓
Chroma 向量库
↓
tenant/category 过滤检索
↓
/rag/search
↓
/rag/ask
↓
structured sources
↓
enterprise retrieval eval
```

---

## 2. 当前项目定位

项目当前定位为：

```text
Enterprise Support AI Copilot
```

当前阶段重点是企业知识库 RAG Core。后续将在此基础上接入 Ticket CRUD、Ticket Agent、人工确认、工具调用审计和 AgentOps 能力。

RAG Core 在整体项目中的作用是：

| 层级        | 作用                             |
| --------- | ------------------------------ |
| 企业文档层     | 提供 IT、HR、财务、行政、安全等内部知识来源       |
| 检索层       | 根据用户问题召回相关知识片段                 |
| 过滤层       | 基于 tenant_id 和 category 控制检索范围 |
| 问答层       | 使用检索上下文生成带来源依据的回答              |
| 评估层       | 使用 eval cases 量化检索效果           |
| Agent 基础层 | 为后续 Ticket Agent 提供知识查询工具      |

---

## 3. 企业文档集

当前文档位于：

```text
experiments/docs/
```

当前共 10 份企业内部支持文档，覆盖 5 个业务类别。

| Category   | Documents                                      | 主题                 |
| ---------- | ---------------------------------------------- | ------------------ |
| `it`       | `vpn_guide.md`、`email_login_faq.md`            | VPN、邮箱、登录、MFA、账号问题 |
| `hr`       | `leave_policy.md`、`onboarding_process.md`      | 请假、休假、入职、前 90 天安排  |
| `finance`  | `travel_reimbursement.md`、`invoice_rules.md`   | 差旅报销、发票、供应商付款      |
| `admin`    | `meeting_room.md`、`device_borrowing.md`        | 会议室、设备借用与归还        |
| `security` | `data_access_policy.md`、`outsource_account.md` | 数据访问权限、外包与供应商账号    |

文档 category 由目录推断：

```text
experiments/docs/it/vpn_guide.md
→ category = it

experiments/docs/security/outsource_account.md
→ category = security
```

当前租户使用 mock 值：

```text
tenant_demo
```

后续接入用户系统后，`tenant_id` 将从当前用户身份上下文中获取。

---

## 4. 文档加载与 metadata 设计

文档加载由以下文件负责：

```text
experiments/rag_local/document_loader.py
```

当前 `Document` 数据结构包含：

```text
document_id
title
source_path
text
tenant_id
category
```

其中：

| 字段            | 含义                               |
| ------------- | -------------------------------- |
| `document_id` | 文档唯一标识，例如 `doc_vpn_guide`        |
| `title`       | 文档标题，当前由文件名生成                    |
| `source_path` | 文档路径                             |
| `text`        | 文档正文                             |
| `tenant_id`   | 当前 mock tenant，默认为 `tenant_demo` |
| `category`    | 文档分类，由父目录推断                      |

metadata 的主要作用是支持后续过滤检索、来源展示和评估分析。

---

## 5. 文本切块策略

文本切块由以下文件负责：

```text
experiments/rag_local/text_splitter.py
```

当前 chunk 参数：

```text
chunk_size = 800
chunk_overlap = 120
min_chunk_size = 150
```

当前切块策略：

```text
1. 优先按空行切自然段
2. 尽量将相关段落合并到同一 chunk
3. 长段落使用字符窗口切分
4. 对过短 chunk 做后处理合并
5. 合并标题-only chunk
6. 合并短残句 chunk
```

当前企业文档集切块结果：

```text
Loaded documents: 10
Generated chunks: 40
```

当前 `Chunk` 数据结构包含：

```text
chunk_id
document_id
title
source_path
chunk_index
content
tenant_id
category
```

切块策略调整的原因：

早期学习文档较短，简单切块即可满足验证需求。企业制度类文档更长，存在多级标题、流程说明、FAQ 和边界场景。若 chunk 过短，会出现标题单独入库、残句单独入库、top-k 噪声增加等问题。因此本阶段将 chunk_size 调整到 800，并增加 min_chunk_size 后处理逻辑，提升 chunk 的语义完整性。

---

## 6. Embedding 与 Chroma Index

Embedding 与索引构建主要由以下文件负责：

```text
experiments/rag_local/build_rag_index.py
experiments/rag_local/build_chroma_index.py
```

当前 embedding 已支持分批请求，避免一次性提交过多文本导致 embedding API batch size 超限。

Chroma index 构建命令：

```bash
python -m experiments.rag_local.build_chroma_index
```

当前构建结果：

```text
Loaded documents: 10
Generated chunks: 40
Generated embeddings: 40
Collection count: 40
```

数量链路一致：

```text
documents → chunks → embeddings → Chroma collection
10        → 40     → 40         → 40
```

这说明文档加载、切块、embedding 生成和 Chroma 写入过程没有丢失数据。

当前 Chroma metadata 包含：

```text
chunk_id
document_id
title
source_path
chunk_index
tenant_id
category
```

---

## 7. Metadata Filter 设计

当前检索支持两个 metadata filter：

| Filter      | 作用         |
| ----------- | ---------- |
| `tenant_id` | 限定当前租户数据范围 |
| `category`  | 限定业务文档分类范围 |

底层检索函数：

```text
experiments/rag_local/query_chroma.py::search_chroma()
```

支持参数：

```text
query
top_k
tenant_id
category
```

API 层当前只暴露 `category`，`tenant_id` 暂时由系统内部 mock tenant context 提供：

```text
tenant_demo
```

这样可以避免把租户边界交给用户请求体。后续接入认证系统后，`tenant_id` 应从当前用户身份中获取。

---

## 8. RAG API

当前 RAG API 已接入 FastAPI。

相关文件：

```text
routers/rag.py
schemas/rag.py
services/rag_service.py
```

调用链：

```text
POST /rag/search
→ routers/rag.py::rag_search()
→ services/rag_service.py::search_documents()
→ experiments/rag_local/query_chroma.py::search_chroma()

POST /rag/ask
→ routers/rag.py::rag_ask()
→ services/rag_service.py::answer_question()
→ experiments/rag_local/query_rag_chroma.py::ask_rag()
```

### 8.1 `/rag/search`

功能：执行 Chroma top-k 检索，返回相关 chunk 及来源 metadata。

请求示例：

```json
{
  "query": "VPN 连不上应该先检查什么？",
  "top_k": 3,
  "category": "it"
}
```

响应包含：

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

### 8.2 `/rag/ask`

功能：执行完整 RAG 流程，包括检索、上下文构造、LLM 回答生成和 sources 返回。

请求示例：

```json
{
  "question": "VPN 连不上应该先检查什么？",
  "top_k": 3,
  "max_distance": 0.9,
  "category": "it"
}
```

响应包含：

```text
answer
retrieval_status
top_distance
sources
```

当检索不到足够依据时，系统会返回拒答：

```text
我在已提供资料中没有找到足够依据。
```

---

## 9. 企业 RAG Eval 设计

本阶段新增企业文档检索评估集：

```text
experiments/evals/enterprise_rag_cases.jsonl
```

评估脚本：

```text
experiments/evals/eval_enterprise_chroma_retrieval.py
```

当前 eval case 数量：

```text
30
```

每条 case 格式：

```json
{
  "id": "ent_it_001",
  "question": "VPN 连不上应该先检查什么？",
  "expected_document_id": "doc_vpn_guide",
  "category": "it",
  "tenant_id": "tenant_demo"
}
```

字段说明：

| 字段                     | 含义             |
| ---------------------- | -------------- |
| `id`                   | case 唯一编号      |
| `question`             | 用户问题           |
| `expected_document_id` | 期望命中的文档 ID     |
| `category`             | 检索时使用的业务分类     |
| `tenant_id`            | 当前 mock tenant |

当前 eval 是 document-level retrieval eval。

检索方式仍然是基于 chunk content 的向量检索：

```text
question
↓
query embedding
↓
Chroma search over chunk embeddings
↓
top-k chunks
↓
取每个 chunk 的 document_id
↓
判断 expected_document_id 是否命中
```

评估粒度是 document-level：

```text
只要 top-k 结果中包含 expected_document_id 对应文档下的任意 chunk，即视为文档级命中。
```

后续可以扩展为 chunk-level eval，通过 `expected_chunk_id` 或 `expected_section` 判断是否命中更精确的知识片段。

---

## 10. Eval 指标

当前使用以下 retrieval 指标：

| 指标                | 含义                                             |
| ----------------- | ---------------------------------------------- |
| `hit@1`           | top1 结果的 document_id 是否等于 expected_document_id |
| `hit@3`           | top3 结果中是否包含 expected_document_id              |
| `top1_miss_cases` | top1 未命中，但 top3 命中的 case                       |
| `failed_cases`    | top3 中没有命中 expected_document_id 的 case         |

说明：

```text
top1_miss 不等同于失败。
它说明 retriever 召回了正确文档，但排序不够理想。
```

---

## 11. Eval 结果

运行命令：

```bash
python -m experiments.evals.eval_enterprise_chroma_retrieval
```

当前结果：

```text
Total cases:      30
hit@1:            1.00 (30/30)
hit@3:            1.00 (30/30)
top1_miss_cases:  0
failed_cases:     0
```

按 category 拆分：

| Category   | Cases | hit@1 | hit@3 |
| ---------- | ----: | ----: | ----: |
| `admin`    |     6 |  1.00 |  1.00 |
| `finance`  |     6 |  1.00 |  1.00 |
| `hr`       |     6 |  1.00 |  1.00 |
| `it`       |     6 |  1.00 |  1.00 |
| `security` |     6 |  1.00 |  1.00 |

当前自动化测试结果：

```text
14 passed, 1 warning
```

---

## 12. 结果解释

当前 30 条企业文档检索 case 全部命中，说明：

```text
1. 企业文档加载正常
2. category 推断正常
3. chunk metadata 正常
4. Chroma metadata 写入正常
5. tenant/category filter 生效
6. eval runner 能正确调用 search_chroma()
7. document-level retrieval 链路稳定
```

当前指标适合作为：

```text
Enterprise RAG retrieval v1 baseline
```

该 baseline 表明，在当前 10 份企业文档、5 个业务分类、30 条明确业务问题的条件下，系统可以稳定召回正确文档。

---

## 13. 当前局限

当前 eval 结果需要结合数据集规模和检索边界解释。

### 13.1 文档规模较小

当前只有 10 份企业文档，每个 category 下只有 2 份文档。category filter 会显著缩小搜索空间，因此当前 hit@1 = 1.00 主要说明基础链路稳定。

### 13.2 Case 仍偏明确

当前 30 条 case 主要覆盖流程型、事实型、FAQ 型和边界场景型问题。虽然比 smoke test 更完整，但问题与目标文档之间仍然比较明确。

### 13.3 缺少同类相似文档干扰

真实企业知识库中，同一 category 下可能有多份高度相似文档，例如账号权限、MFA、外包账号、数据访问、安全审计等内容可能互相重叠。当前每类只有 2 份文档，干扰强度有限。

### 13.4 暂未评估 chunk-level precision

当前 eval 只判断是否召回正确文档。它不能判断系统是否命中了最精确的 chunk。后续需要加入 chunk-level eval 或 section-level eval。

### 13.5 暂未评估生成回答质量

当前 eval 只评估 retrieval，没有评估 LLM answer 的准确性、完整性、引用质量和幻觉风险。

### 13.6 暂未覆盖 no-answer case

当前 eval case 都有明确答案来源。后续需要加入知识库无法回答的问题，评估系统是否能拒答。

---

## 14. 后续改进方向

后续 RAG 评估可以从以下方向增强：

| 方向                  | 说明                                         |
| ------------------- | ------------------------------------------ |
| 增加同类文档数量            | 每个 category 从 2 篇扩展到 5–10 篇                |
| 增加 ambiguous cases  | 测试跨文档、跨流程、语义重叠问题                           |
| 增加 no-answer cases  | 验证无依据拒答能力                                  |
| 增加 chunk-level eval | 判断是否命中具体 chunk 或 section                   |
| 增加 answer eval      | 评估回答准确性、引用一致性、幻觉风险                         |
| 引入 rerank           | 在 top-k 初召回后优化排序                           |
| 记录 retrieval logs   | 记录 query、retrieved chunks、distance、latency |
| 统计 latency / token  | 为后续工程化和成本控制提供依据                            |

---

## 15. 阶段结论

本阶段完成了企业 RAG Core 的第一版闭环：

```text
企业文档集
↓
metadata-aware chunking
↓
batch embedding
↓
Chroma vector store
↓
tenant/category filtered retrieval
↓
RAG API
↓
enterprise retrieval eval
```

当前结果：

```text
Documents: 10
Chunks: 40
Eval cases: 30
hit@1: 1.00
hit@3: 1.00
Tests: 14 passed
```

RAG Core v1 已具备作为主项目知识库底座的基本能力。下一阶段将进入工单系统和 Agent 工作流建设：

```text
Ticket CRUD
↓
Ticket Agent preview
↓
Human approval
↓
Tool calls audit
↓
AgentOps metrics
```

RAG Core 将作为 Ticket Agent 的知识查询工具，为后续“知识库问答 → 工单预览 → 人工确认 → 工单创建”的业务闭环提供基础。
