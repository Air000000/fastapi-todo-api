# FastAPI Notes

FastAPI 是一个 Python Web 框架，常用于构建 API 服务。

在 FastAPI 中，可以使用 Pydantic 模型定义请求体。例如创建 Todo 时，可以定义 TodoCreate schema，然后在接口函数中接收这个 schema。

FastAPI 会自动生成 Swagger 文档，默认地址是 /docs。