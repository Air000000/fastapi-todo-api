import os
import math
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


documents = [
    {
        "id": "doc_1",
        "title": "FastAPI 基础",
        "text": "FastAPI 是一个用于构建 API 的现代 Python Web 框架，支持类型提示和自动生成接口文档。",
    },
    {
        "id": "doc_2",
        "title": "Pydantic 基础",
        "text": "Pydantic 用于数据校验和序列化，可以定义请求体和响应模型。",
    },
    {
        "id": "doc_3",
        "title": "SQLModel 基础",
        "text": "SQLModel 结合了 SQLAlchemy 和 Pydantic，可以用于定义数据库表，并将 Todo 持久化保存到 SQLite 数据库。",
    },
    {
        "id": "doc_4",
        "title": "RAG 基础",
        "text": "RAG 是检索增强生成，系统会先检索相关资料，再让大模型基于资料生成答案。",
    },
    {
        "id": "doc_5",
        "title": "Embedding 基础",
        "text": "Embedding 会把文本转换成向量，让系统可以根据语义相似度检索相关内容。",
    },
]


def get_client() -> OpenAI:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    base_url = os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    if not api_key:
        raise RuntimeError("Missing DASHSCOPE_API_KEY. Please set it in .env")

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
    )   


def embed_texts(texts: list[str]) -> list[list[float]]: 
    """
    把多段文本转换成 embedding 向量。
    """
    client = get_client()   
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")

    response = client.embeddings.create(
        model=model,
        input=texts,
        encoding_format="float",
    )

    return [item.embedding for item in response.data]

# cosine_similarity(A, B) = (A · B) / (||A|| * ||B||)
def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    计算两个向量的 cosine similarity。
    """
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def build_index(documents: list[dict[str, str]]) -> list[dict[str, Any]]:
    """
    给每篇文档生成 embedding，形成一个最小内存索引。
    """
    texts = [
        f"{doc['title']}\n{doc['text']}"
        for doc in documents
    ]

    embeddings = embed_texts(texts) 

    index = []

    for doc, embedding in zip(documents, embeddings):
        index.append(
            {
                "id": doc["id"],
                "title": doc["title"],
                "text": doc["text"],
                "embedding": embedding,
            }
        )

    return index


def search(
    question: str,
    index: list[dict[str, Any]],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    对用户问题做 embedding，然后和所有文档 embedding 算相似度。
    """
    question_embedding = embed_texts([question])[0] # 获取问题的 embedding 向量。

    results = []    

    for item in index: 
        score = cosine_similarity(question_embedding, item["embedding"])    # 计算问题和文档的相似度得分。

        results.append(
            {
                "id": item["id"],
                "title": item["title"],
                "text": item["text"],
                "score": score,
            }
        )   # 把文档信息和相似度得分一起保存到结果列表中。

    results.sort(key=lambda item: item["score"], reverse=True)  # 根据相似度得分从高到低排序结果列表。

    return results[:top_k]  # 返回相似度最高的 top_k 个文档。


def run_query(question: str, index: list[dict[str, Any]]) -> None:
    print("\n" + "=" * 80) 
    print(f"问题：{question}")
    print("=" * 80)

    results = search(question, index, top_k=3)

    for rank, result in enumerate(results, start=1):
        print(f"Top {rank}")
        print(f"文档 ID: {result['id']}")
        print(f"标题: {result['title']}")
        print(f"相似度: {result['score']:.4f}")
        print(f"内容: {result['text']}")
        print("-" * 80)


def main() -> None:
    # 离线阶段：构建 embedding 索引。
    print("正在构建 embedding index...")
    index = build_index(documents)  
    print("index 构建完成。")

    # 在线阶段：对用户问题进行 embedding 搜索。
    test_questions = [
        "RAG 是什么？",
        "怎么保存 Todo 到数据库？",
        "把文本变成向量是为了什么？",
        "怎么定义接口的请求体？",
    ]

    for question in test_questions:
        run_query(question, index)


if __name__ == "__main__":
    main()