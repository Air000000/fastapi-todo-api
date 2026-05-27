# RAG Notes

RAG 是 Retrieval-Augmented Generation，即检索增强生成。

RAG 的核心流程是：先把文档切成 chunks，然后对每个 chunk 生成 embedding，用户提问时先检索相关 chunk，再把相关内容放入 prompt 让大模型回答。

RAG 需要 chunk 是因为整篇文档通常太长，直接 embedding 整篇文档会导致语义过粗，也会让检索不够精确。