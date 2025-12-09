"""
HTTP request/response models for the AVA-Gen runtime API.
"""

from pydantic import BaseModel
from typing import Optional, Any


class StartSessionResponse(BaseModel):
    session_id: str


class AgentRequest(BaseModel):
    session_id: str
    app_id: str
    message: str


class AgentResponse(BaseModel):
    """
    High-level response:

    type:
      - "clarification"
      - "action_plan"

    - if clarification:
        message: str
    - if action_plan:
        action_plan: Any (the ActionPlan dict)
        method_name: str
        next_session_id: Optional[str]
    """
    type: str
    message: Optional[str] = None
    method_name: Optional[str] = None
    action_plan: Optional[Any] = None
    next_session_id: Optional[str] = None

