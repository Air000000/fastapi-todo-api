from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.ticket import TicketCategory, TicketPriority, TicketResponse


class TicketAgentPreviewRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    category: TicketCategory | None = None


class TicketDraft(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    category: TicketCategory
    priority: TicketPriority = "medium"


class TicketAgentSource(BaseModel):
    document_id: str
    chunk_id: str
    title: str
    source_path: str
    distance: float
    preview: str
    category: str | None = None


class TicketAgentPreviewResponse(BaseModel):
    should_create_ticket: bool
    reason: str
    draft: TicketDraft | None = None
    sources: list[TicketAgentSource] = Field(default_factory=list)


class TicketAgentConfirmRequest(BaseModel):
    draft: TicketDraft


class TicketAgentConfirmResponse(BaseModel):
    ticket: TicketResponse