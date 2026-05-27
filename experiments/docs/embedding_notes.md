# Embedding Notes

Embedding 是把文本转换成向量的技术。

语义相近的文本在向量空间中距离更近。检索时，可以把用户问题也转换成 embedding，然后用 cosine similarity 找到最相似的文档 chunk。

Embedding 不等于大模型回答，它主要用于语义检索。