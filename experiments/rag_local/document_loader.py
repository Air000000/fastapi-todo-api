from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


SUPPORTED_SUFFIXES = {".md", ".txt"}


@dataclass
class Document:
    document_id: str
    title: str
    source_path: str
    text: str


def build_document_id(path: Path) -> str:
    """
    根据文件名生成稳定 document_id。

    例如：
    experiments/docs/fastapi_notes.md
    ->
    doc_fastapi_notes
    """
    safe_name = path.stem.strip().lower().replace(" ", "_")
    return f"doc_{safe_name}"


def read_text_file(path: Path) -> str:
    """
    读取文本文件。

    当前先只处理 utf-8。
    后面遇到编码问题，再加 fallback。
    """
    return path.read_text(encoding="utf-8")


def load_documents(docs_dir: str | Path) -> list[Document]:
    """
    从目录中读取 .md / .txt 文档。

    返回 Document 列表，每个 Document 包含：
    - document_id
    - title
    - source_path
    - text
    """
    docs_path = Path(docs_dir)

    if not docs_path.exists():
        raise FileNotFoundError(f"Docs directory not found: {docs_path}")

    if not docs_path.is_dir():
        raise NotADirectoryError(f"Expected a directory: {docs_path}")

    documents: list[Document] = []

    for file_path in sorted(docs_path.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        text = read_text_file(file_path).strip()

        if not text:
            continue

        document = Document(
            document_id=build_document_id(file_path),
            title=file_path.stem,
            source_path=str(file_path),
            text=text,
        )
        documents.append(document)

    return documents


def print_documents_summary(documents: Iterable[Document]) -> None:
    for doc in documents:
        print("=" * 80)
        print(f"document_id: {doc.document_id}")
        print(f"title:       {doc.title}")
        print(f"source_path: {doc.source_path}")
        print(f"text_len:    {len(doc.text)}")
        print(f"preview:     {doc.text[:80].replace(chr(10), ' ')}...")


def main() -> None:
    docs_dir = Path("experiments/docs")
    documents = load_documents(docs_dir)

    print(f"Loaded documents: {len(documents)}")
    print_documents_summary(documents)

    print("\nFirst document as dict:")
    if documents:
        print(asdict(documents[0]))


if __name__ == "__main__":
    main()