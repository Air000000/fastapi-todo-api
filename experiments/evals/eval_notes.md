# Retrieval Eval Notes

## Baseline: JSON Index

- Total cases: 10
- hit@1: 0.90
- hit@3: 1.00
- top1 miss cases: 1
- failed cases: 0

## Top1 Miss Analysis

### Case

Question: embedding 在 RAG 中有什么作用？

Expected: doc_embedding_notes  
Retrieved top1: doc_rag_notes  
Retrieved top2: doc_embedding_notes

### Analysis

This is not necessarily a retrieval failure. The question contains both "embedding" and "RAG", and `doc_rag_notes` explains how embedding is used inside the RAG pipeline. Therefore, the top1 result is semantically reasonable.

### Possible improvement

Make the eval question more specific, for example:

- embedding 是什么？
- 为什么语义检索要用 embedding？
- embedding 和普通关键词匹配有什么区别？


## JSON vs Chroma Retrieval Comparison

| Retriever | hit@1 | hit@3 | top1 miss cases | failed cases |
|---|---:|---:|---:|---:|
| JSON cosine index | 0.90 | 1.00 | 1 | 0 |
| Chroma | 0.90 | 1.00 | 1 | 0 |

### Observation

Both retrievers return the same top1 miss case: `embedding 在 RAG 中有什么作用？`.

The expected document is `doc_embedding_notes`, but both retrievers rank `doc_rag_notes` first. This is reasonable because the question asks about embedding specifically inside the RAG pipeline, and `doc_rag_notes` also explains how embedding is used in RAG.

This case is better treated as an ambiguous eval case rather than a clear retrieval failure.

## Retrieval eval update - 15 cases

Added 5 additional retrieval eval cases to reduce keyword/title leakage and test more natural user questions.

Current results:

### JSON Index

- Total: 15
- hit@1: 0.93
- hit@3: 1.00
- top1_miss_cases: 1
- failed_cases: 0

### Chroma

- Total: 15
- hit@1: 0.93
- hit@3: 1.00
- top1_miss_cases: 1
- failed_cases: 0

### Observation

The only top1 miss is:

- question: `embedding 在 RAG 中有什么作用？`
- expected: `doc_embedding_notes`
- top1 retrieved: `doc_rag_notes`
- top2 retrieved: `doc_embedding_notes`

This case is ambiguous because the question contains both `embedding` and `RAG`, and the RAG document also describes embedding as part of the retrieval pipeline.  
It is better classified as a top1 ranking issue / ambiguous query rather than a complete retrieval failure.