from __future__ import annotations

import json
from pathlib import Path

from experiments.rag_local.query_index import SearchResult, search
from experiments.evals.eval_core import load_eval_cases
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


def print_report(report: dict, top_k: int = 3) -> None:
    print("=" * 80)
    print("Retrieval Eval Report - JSON Index")
    print("=" * 80)
    print(f"Total: {report['total']}")
    print(f"hit@1: {report['hit@1']:.2f}")
    print(f"hit@{top_k}: {report[f'hit@{top_k}']:.2f}")

    print()
    print(f"top1_miss_cases: {len(report['top1_miss_cases'])}")
    for case in report["top1_miss_cases"]:
        print("-" * 80)
        print(f"question: {case['question']}")
        print(f"expected_document_id: {case['expected_document_id']}")
        print(f"retrieved_document_ids: {case['retrieved_document_ids']}")
        print("top_results:")

        for item in case["top_results"]:
            print(
                f"  - document_id={item['document_id']} | "
                f"chunk_id={item['chunk_id']} | "
                f"score={item['score']:.4f}"
            )
            print(f"    preview={item['preview']}")
            
    print()
    print("Failed cases:")
    failed_cases = report["failed_cases"]

    if not failed_cases:
        print("No failed cases.")
        return

    for case in failed_cases:
        print("-" * 80)
        print(f"question: {case['question']}")
        print(f"expected_document_id: {case['expected_document_id']}")
        print(f"retrieved_document_ids: {case['retrieved_document_ids']}")
        print("top_results:")

        for item in case["top_results"]:
            print(
                f"  - document_id={item['document_id']} | "
                f"chunk_id={item['chunk_id']} | "
                f"score={item['score']:.4f}"
            )
            print(f"    preview={item['preview']}")


def main() -> None:
    top_k = 3
    report = evaluate(top_k=top_k)
    print_report(report, top_k=top_k)


if __name__ == "__main__":
    main()