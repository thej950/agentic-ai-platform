from __future__ import annotations

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """Request payload for the agent-orchestrated chat endpoint."""

    question: str = Field(..., description="User question to route to the appropriate enterprise agent.", min_length=1)
