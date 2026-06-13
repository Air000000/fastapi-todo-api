# RAG v0.1 Baseline Report

## 1. Scope

This report records the current RAG v0.1 baseline before moving into the next project phase.

Current project branch:

```text
learn-rag
```

Current RAG components:

```text
/rag/search
/rag/ask
JSON index retrieval
Chroma retrieval
RAG service layer
RAG API tests
RAG service tests
Retrieval eval scripts
Enterprise support documents with metadata
```

The purpose of this report is to freeze the current baseline, record the known evaluation results, and document the root cause of the previous invalid Chroma evaluation result.

---

## 2. Eval Dataset Separation

The eval datasets are now separated by corpus:

| Eval Script                                         | Eval Dataset                      | Target Index | Corpus Type             |
| --------------------------------------------------- | --------------------------------- | ------------ | ----------------------- |
| `python -m experiments.evals.eval_retrieval`        | `eval_learning_questions.jsonl`   | JSON index   | Learning docs           |
| `python -m experiments.evals.eval_chroma_retrieval` | `eval_enterprise_questions.jsonl` | Chroma index | Enterprise support docs |

This separation avoids evaluating a retriever against a corpus that does not contain the expected documents.

The core rule is:

```text
Learning questions should be evaluated against the learning document index.
Enterprise support questions should be evaluated against the enterprise support document index.
```

---

## 3. JSON Index Baseline

Command:

```powershell
python -m experiments.evals.eval_retrieval
```

Result:

| Metric      | Value |
| ----------- | ----: |
| Total cases |    15 |
| hit@1       |  0.93 |
| hit@3       |  1.00 |

Main top1 miss:

```text
Question: embedding 在 RAG 中有什么作用？
Expected document: doc_embedding_notes
Top1 document: doc_rag_notes
Top2 document: doc_embedding_notes
```

Analysis:

```text
This is an understandable semantic overlap.

The RAG notes document also mentions embeddings as part of the RAG pipeline, while the embedding notes document focuses on embedding itself. Since the expected document appears in top3, this is a top1 miss rather than a retrieval failure.
```

Current conclusion:

```text
The JSON index learning baseline is healthy.
```

---

## 4. Chroma Enterprise Baseline

Command:

```powershell
python -m experiments.evals.eval_chroma_retrieval
```

Result:

| Metric      | Value |
| ----------- | ----: |
| Total cases |    10 |
| hit@1       |  0.90 |
| hit@3       |  1.00 |

Main top1 miss:

```text
Question: 发票报销有哪些要求？
Expected document: doc_invoice_rules
Top1 document: doc_travel_reimbursement
Top2 document: doc_invoice_rules
```

Analysis:

```text
This miss is acceptable for the current baseline because travel reimbursement and invoice rules are semantically close.

The top1 result discusses reimbursement materials and invoice-related reimbursement requirements. The expected invoice rules document appears in top3, so the retriever still provides usable context.
```

Current conclusion:

```text
The Chroma enterprise support baseline is healthy.
```

---

## 5. Root Cause of the Previous Chroma 0.00 Result

Earlier Chroma evaluation showed:

```text
hit@1 = 0.00
hit@3 = 0.00
```

This was not caused by a Chroma retriever failure.

Root cause:

```text
The Chroma collection contained only enterprise support documents, while the eval script was still using learning-doc questions.

Therefore, the expected documents such as doc_fastapi_notes, doc_docker_notes, doc_rag_notes, doc_embedding_notes, and doc_sqlmodel_notes were not present in the Chroma collection.
```

Observed Chroma collection documents:

```text
doc_data_access_policy
doc_device_borrowing
doc_email_login_faq
doc_invoice_rules
doc_leave_policy
doc_meeting_room
doc_onboarding_process
doc_outsource_account
doc_travel_reimbursement
doc_vpn_guide
```

Missing learning documents in Chroma:

```text
doc_fastapi_notes
doc_docker_notes
doc_rag_notes
doc_embedding_notes
doc_sqlmodel_notes
```

Final diagnosis:

```text
The previous Chroma 0.00 result reflected a corpus-eval mismatch, not a retriever failure.
```

---

## 6. Fix Applied

The eval setup was adjusted as follows:

```text
eval_learning_questions.jsonl
- Used by JSON index eval
- Covers FastAPI, Docker, RAG, Embedding, SQLModel learning documents

eval_enterprise_questions.jsonl
- Used by Chroma eval
- Covers enterprise support documents such as VPN, email, leave policy, reimbursement, invoice rules, meeting rooms, device borrowing, data access, and outsource accounts
```

The eval scripts now follow this mapping:

| Script                     | Eval File                        |
| -------------------------- | -------------------------------- |
| `eval_retrieval.py`        | `eval_core.LEARNING_EVAL_FILE`   |
| `eval_chroma_retrieval.py` | `eval_core.ENTERPRISE_EVAL_FILE` |

This makes the evaluation target explicit and avoids silently reusing the wrong dataset.

---

## 7. Current Baseline Summary

| Retriever  | Corpus                  | Total Cases | hit@1 | hit@3 | Status  |
| ---------- | ----------------------- | ----------: | ----: | ----: | ------- |
| JSON index | Learning docs           |          15 |  0.93 |  1.00 | Healthy |
| Chroma     | Enterprise support docs |          10 |  0.90 |  1.00 | Healthy |

The current RAG baseline is valid.

---

## 8. Current Limitations

The current baseline is intentionally minimal.

Known limitations:

```text
1. The enterprise eval set currently has only 10 cases.
2. The Chroma enterprise corpus currently has 10 enterprise support documents.
3. The current eval mainly measures document-level retrieval hit rate.
4. MRR and latency metrics are not yet included in the report output.
5. The invoice-related top1 miss shows that semantically close finance documents can still compete with each other.
```

These are acceptable at the current stage because the goal of this step is baseline validation, not final RAG optimization.

---

## 9. Next Step

The project can now move from baseline validation into the next phase:

```text
Enterprise RAG v1 cleanup
```

Recommended next tasks:

```text
1. Verify tenant_id and category metadata consistency.
2. Confirm /rag/search supports category filtering.
3. Confirm /rag/ask returns sources with tenant_id and category metadata.
4. Add or update tests for metadata filter behavior.
5. Expand enterprise eval cases from 10 to 30.
6. Write the next-stage RAG report after enterprise eval v1.
```

After this cleanup, the project should move into:

```text
Ticket CRUD
Ticket Agent preview / confirm
AgentOps audit records
```

---

## 10. Final Conclusion

The RAG v0.1 baseline is now stable.

The key engineering lesson from this phase is:

```text
Evaluation results are only meaningful when the eval dataset, expected documents, and target index corpus are aligned.
```

This baseline can be used as the starting point for the next project stage.
