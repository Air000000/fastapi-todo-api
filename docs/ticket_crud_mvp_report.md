# Ticket CRUD MVP 阶段报告

## 1. 阶段目标

本阶段目标是为后续 Ticket Agent 提供可调用的业务工具层。Ticket Agent 未来会通过 service 层调用工单能力。

当前已实现最小工单闭环：

- 创建工单
- 查询工单列表
- 查询单个工单
- 更新工单状态 / 优先级 / 分类 / 内容
- 基于 mock tenant context 进行租户隔离
- API 自动化测试

## 2. 当前 API

| Method | Path | 作用 |
|---|---|---|
| POST | `/tickets` | 创建工单 |
| GET | `/tickets` | 查询工单列表 |
| GET | `/tickets/{ticket_id}` | 查询单个工单 |
| PATCH | `/tickets/{ticket_id}` | 更新工单 |

## 3. 数据模型

Ticket 当前包含：

```text
id
tenant_id
created_by
title
description
category
priority
status
created_at
updated_at
```

枚举约束：
```text
category: it / hr / finance / admin / security / other
priority: low / medium / high / urgent
status: open / in_progress / resolved / closed
```

## 4. 分层设计
```text
routers/tickets.py
↓
services/ticket_service.py
↓
models/ticket.py
↓
SQLite
```