# SQLModel Notes

SQLModel 是一个结合 SQLAlchemy 和 Pydantic 的 Python ORM 工具。

在 Todo 项目中，可以用 SQLModel 定义 Todo 表，包括 id、title、completed、due_time 等字段。

保存数据时，通常需要创建数据库 session，然后 add、commit、refresh。