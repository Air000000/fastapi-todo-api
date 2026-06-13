# AGENTS.md

## Project Context

This repository is being upgraded from a FastAPI Todo + RAG learning project into Enterprise Support AI Copilot.

## Current Focus

The current focus is Ticket CRUD MVP and preparing for Ticket Agent.

## Development Rules

- Keep changes small and reviewable.
- Run tests before committing.
- Do not add Agent logic before Ticket CRUD is stable.
- Prefer service / schema / router separation.
- Keep tenant isolation in mind for all ticket and RAG features.

## Important Commands

```bash
pytest tests/test_todos.py
pytest tests/test_rag_api.py
pytest tests/test_rag_service.py
pytest tests/test_tickets_api.py