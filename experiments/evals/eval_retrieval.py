from __future__ import annotations

from experiments.rag_local.query_index import SearchResult, search
from experiments.evals import eval_core

def result_to_preview(result: SearchResult) -> dict:
    '''
    将 SearchResult 转换为包含预览信息的字典，方便 eval 报告展示。
    '''
    return {
        "chunk_id": result.chunk_id,    
        "document_id": result.document_id,
        "title": result.title,
        "source_path": result.source_path,
        "chunk_index": result.chunk_index,
        "score": result.score,
        "preview": result.content[:120].replace("\n", " "),
    }

    
def evaluate(top_k: int = 3) -> dict:
    return eval_core.evaluate_retriever(
        retriever=search,
        result_to_preview=result_to_preview,
        top_k=top_k,
    )


def main() -> None:
    top_k = 3
    report = evaluate(top_k=top_k)
    eval_core.print_retrieval_report(report, title="Retrieval Eval Report - JSON Index", top_k=top_k, metric_key = "score")


if __name__ == "__main__":
    main()