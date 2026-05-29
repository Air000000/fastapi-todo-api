# RAG Learning Lab

本目录用于学习和验证一个最小可运行的 local-doc RAG pipeline。

当前目标是：基于本地 Markdown 文档，实现文档加载、文本切块、embedding、检索、RAG 问答，以及 retrieval eval。项目同时支持两种检索后端：

1. JSON index：用于理解 embedding 检索的最小实现。
2. Chroma vector store：用于学习持久化向量库和更工程化的检索方式。

当前阶段重点不是追求复杂功能，而是把 RAG 的核心链路跑通、测评清楚、能解释失败案例。

---

## 1. 当前目录结构

```text
experiments/
  docs/
    docker_notes.md
    embedding_notes.md
    fastapi_notes.md
    rag_notes.md
    sqlmodel_notes.md

  index/
    rag_index.json

  rag_local/
    document_loader.py
    text_splitter.py
    build_rag_index.py
    query_index.py
    build_chroma_index.py
    query_chroma.py
    query_rag_chroma.py

  evals/
    eval_core.py
    eval_questions.jsonl
    eval_retrieval.py
    eval_chroma_retrieval.py
    eval_notes.md
```

---

## 2. RAG Pipeline

当前实现的核心流程如下：

```text
本地 Markdown 文档
↓
document_loader
↓
text_splitter
↓
embedding
↓
JSON index / Chroma vector store
↓
top-k retrieval
↓
RAG answer with sources
↓
retrieval eval
```

---

## 3. JSON Index 版本

JSON index 是一个最小向量索引实现，用于理解 RAG 检索的基本原理。

它会把每个 chunk 的文本、metadata 和 embedding 保存到：

```text
experiments/index/rag_index.json
```

### 构建 JSON index

```bash
python -m experiments.rag_local.build_rag_index
```

### 查询 JSON index

```bash
python -m experiments.rag_local.query_index "RAG 为什么需要 chunk？"
```

JSON 检索结果使用 `score` 表示相关性，当前实现中 `score` 越大表示越相关。

---

## 4. Chroma 版本

Chroma 版本用于学习持久化向量库。

相比 JSON index，Chroma 更适合后续扩展到更大的文档集合，也更接近真实 RAG 工程中的 vector store 使用方式。

### 构建 Chroma index

```bash
python -m experiments.rag_local.build_chroma_index
```

### 查询 Chroma index

```bash
python -m experiments.rag_local.query_chroma "RAG 为什么需要 chunk？"
```

Chroma 检索结果使用 `distance` 表示距离，通常 `distance` 越小表示越接近。

---

## 5. Retrieval Eval

当前使用 `eval_questions.jsonl` 作为最小评测集。

每条 eval case 包含：

```json
{"question": "...", "expected_document_id": "..."}
```

评测指标包括：

| 指标              | 含义                   |
| --------------- | -------------------- |
| hit@1           | 正确文档是否排在 top1        |
| hit@3           | 正确文档是否出现在 top3       |
| top1_miss_cases | 正确文档不在 top1，但仍在 top3 |
| failed_cases    | 正确文档没有出现在 top3       |

### 运行 JSON index eval

```bash
python -m experiments.evals.eval_retrieval
```

### 运行 Chroma eval

```bash
python -m experiments.evals.eval_chroma_retrieval
```

---

## 6. 当前 Eval 结果

| Retriever         | hit@1 | hit@3 | top1 miss cases | failed cases |
| ----------------- | ----: | ----: | --------------: | -----------: |
| JSON cosine index |  0.90 |  1.00 |               1 |            0 |
| Chroma            |  0.90 |  1.00 |               1 |            0 |

当前 JSON index 和 Chroma 的 retrieval eval 结果一致。

唯一的 top1 miss case 是：

```text
Question: embedding 在 RAG 中有什么作用？
Expected: doc_embedding_notes
Top1: doc_rag_notes
Top2: doc_embedding_notes
```

这个 case 不一定是明确的检索失败。问题同时包含 `embedding` 和 `RAG` 两个主题，而 `doc_rag_notes` 中也解释了 embedding 在 RAG pipeline 中的作用。因此，这更像是一个 query / label 歧义案例，而不是明显的 retrieval failure。

---

## 7. 当前结论

当前 local-doc RAG v0.1 已完成以下能力：

* 读取本地 Markdown 文档
* 切分 chunk
* 生成 embedding
* 构建 JSON index
* 使用 cosine similarity 做 top-k 检索
* 构建 Chroma vector store
* 使用 Chroma 做 top-k 检索
* 基于同一批 eval cases 对比 JSON 和 Chroma
* 输出 hit@1、hit@3、top1 miss cases 和 failed cases
* 对歧义 case 进行分析

当前结果说明：在这个小规模测试集上，JSON index 和 Chroma 的检索效果一致，整体检索表现可接受。

---

## 8. 下一步计划

短期下一步：

1. 增加更多 eval cases，从 10 条扩展到 20 条。
2. 增加更容易混淆的问题，用于观察 retrieval failure。
3. 继续完善 RAG answer，确保回答包含 sources。
4. 之后再考虑接入 FastAPI API。

暂时不做：

* PDF 解析
* rerank
* query rewrite
* 复杂 LLM judge
* Agent
* 前端页面

当前阶段优先保证：能运行、能评测、能讲清楚。
