"""
Session-related models for AVA-Gen runtime.

These describe:
- a minimal Session object
- Turn entries (user / server)
- SessionStatus enum (OPEN, ACTION_SENT, CLOSED)
"""

from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    OPEN = "OPEN"
    ACTION_SENT = "ACTION_SENT"
    CLOSED = "CLOSED"


class Turn(BaseModel):
    role: str          # "user" or "server"
    message: str       # raw text
    type: Optional[str] = None  # "clarification", "action_plan", etc.
    timestamp: Optional[str] = None  # ISO string, optional for now


class Session(BaseModel):
    session_id: str
    app_id: Optional[str] = None
    status: SessionStatus = SessionStatus.OPEN
    turns: List[Turn] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
