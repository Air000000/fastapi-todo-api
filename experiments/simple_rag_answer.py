import os
import json
from typing import Any

from dotenv import load_dotenv

from embedding_search import documents, build_index, search, get_client


load_dotenv()


MIN_RETRIEVAL_SCORE = 0.35  # 根据实际情况调整，过高导致无法找到相关文档，过低引入无关文档。
SOURCE_SCORE_THRESHOLD = 0.35   # 只有当单个 source 的相似度超过这个阈值时，才会在最终答案中提及该 source

def format_context(retrieved_docs: list[dict[str, Any]]) -> str:
    """
    把检索到的文档格式化成给 LLM 阅读的上下文。

    retrieved_docs 里面每一项大概长这样：
    {
        "id": "doc_3",
        "title": "SQLModel 基础",
        "text": "...",
        "score": 0.5665
    }
    """
    context_parts = []

    for index, doc in enumerate(retrieved_docs, start=1):   
        context_parts.append(
            f"""[Source {index}]
document_id: {doc["id"]}
title: {doc["title"]}
score: {doc["score"]:.4f}
content: {doc["text"]}
"""
        )

    return "\n".join(context_parts)


def build_rag_prompt(question: str, context: str) -> str:
    """
    构造 RAG prompt。

    重点是：
    1. 要求模型只根据资料回答
    2. 如果资料不足，必须说不知道
    3. 不允许使用资料外的信息编造答案
    """
    return f"""
请你作为一个严谨的 RAG 问答助手回答问题。

规则：
1. 你只能根据下面的【资料】回答问题。
2. 如果【资料】中没有足够信息，请回答：“我在已提供资料中没有找到足够依据。”
3. 不要使用资料之外的通用知识补充答案。
4. 回答要简洁、准确。
5. 回答时可以提到你依据了哪些 Source。

【资料】
{context}

【问题】
{question}
""".strip()


def generate_answer(question: str, retrieved_docs: list[dict[str, Any]]) -> str:
    """
    把检索结果交给 Qwen，让模型基于 context 生成答案。
    """
    client = get_client()
    model = os.getenv("DASHSCOPE_MODEL", "qwen3.5-plus")

    context = format_context(retrieved_docs)
    prompt = build_rag_prompt(question, context)

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful RAG assistant. "
                    "Answer only based on the provided context. "
                    "If the context is insufficient, say you do not have enough evidence."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    return completion.choices[0].message.content


def answer_with_rag(
    question: str,
    index: list[dict[str, Any]],
    top_k: int = 3,
) -> dict[str, Any]:
    """
    完整的最小 RAG 流程：

    1. 检索相关文档
    2. 用最低分数阈值过滤弱相关文档
    3. 如果没有足够资料，直接拒答
    4. 如果有资料，把资料交给 LLM 生成答案
    5. 返回 answer + sources
    """
    retrieved_docs = search(question, index, top_k=top_k)   

    top_score = retrieved_docs[0]["score"] if retrieved_docs else 0.0   # 最高分，后续可以根据这个分数判断是否拒答

    filtered_docs = [
        doc for doc in retrieved_docs
        if doc["score"] >= SOURCE_SCORE_THRESHOLD
    ]   # 只有当单个 source 的相似度超过 SOURCE_SCORE_THRESHOLD 时，才会在最终答案中提及该 source

    sources = [
        {
            "document_id": doc["id"],
            "title": doc["title"],
            "content": doc["text"],
            "score": round(doc["score"], 4),
        }
        for doc in filtered_docs
    ]

    if top_score < MIN_RETRIEVAL_SCORE or not filtered_docs:    # 如果最高分都很低，说明没有找到相关文档，直接拒答。
        return {
            "question": question,
            "answer": "我在已提供资料中没有找到足够依据。",
            "sources": sources,
            "retrieval_status": "low_confidence",
            "top_score": round(top_score, 4),
        }

    answer = generate_answer(question, filtered_docs)   

    if "没有找到足够依据" in answer:
        retrieval_status = "insufficient_context"
    else:
        retrieval_status = "ok"

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "retrieval_status": retrieval_status,
        "top_score": round(top_score, 4),
    }

def run_query(question: str, index: list[dict[str, Any]]) -> None:
    result = answer_with_rag(question, index, top_k=3)

    print("\n" + "=" * 100)
    print(f"问题：{question}")
    print("=" * 100)

    print("\n回答：")
    print(result["answer"])

    print("\n检索状态：")
    print(result["retrieval_status"])

    print("\nTop Score：")
    print(result["top_score"])

    print("\nSources：")
    for source in result["sources"]:
        print("-" * 80)
        print(f"document_id: {source['document_id']}")
        print(f"title: {source['title']}")
        print(f"score: {source['score']}")
        print(f"content: {source['content']}")

    print("\n完整 JSON：")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    print("正在构建 embedding index...")
    index = build_index(documents)
    print("index 构建完成。")

    test_questions = [
        "RAG 是什么？",
        "怎么保存 Todo 到数据库？",
        "把文本变成向量是为了什么？",
        "Kubernetes 是什么？",
    ]

    for question in test_questions:
        run_query(question, index)


if __name__ == "__main__":
    main()