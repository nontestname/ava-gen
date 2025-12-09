"""HTTP routes for interacting with the AVA-Gen runtime.

Exposes endpoints like:

- POST /agent/start_session -> returns a new session_id
- POST /agent/request       -> takes (session_id, app_id, message)
                               and returns either a clarification or an
                               action plan JSON.
"""

import logging

from fastapi import APIRouter, HTTPException
from typing import Optional

from ..models.api_models import (
    StartSessionResponse,
    AgentRequest,
    AgentResponse,
)
from ..store.session_store import SessionStore
# ActionPlanStore and LogStore are not directly used here
from ..agents.conversation_agent import ConversationAgent


logger = logging.getLogger(__name__)

# Router for all agent-related endpoints
router = APIRouter()


# Module-level references, to be initialized by the server.
_SESSION_STORE: Optional[SessionStore] = None
_CONVERSATION_AGENT: Optional[ConversationAgent] = None


def init_routes(session_store: SessionStore, conversation_agent: ConversationAgent) -> None:
    """Initialize module-level references used by the route handlers."""
    global _SESSION_STORE, _CONVERSATION_AGENT
    _SESSION_STORE = session_store
    _CONVERSATION_AGENT = conversation_agent


def _require_session_store() -> SessionStore:
    if _SESSION_STORE is None:
        raise HTTPException(
            status_code=500,
            detail="SessionStore is not configured on the server.",
        )
    return _SESSION_STORE


def _require_conversation_agent() -> ConversationAgent:
    if _CONVERSATION_AGENT is None:
        raise HTTPException(
            status_code=500,
            detail="ConversationAgent is not configured on the server.",
        )
    return _CONVERSATION_AGENT


@router.post("/start_session", response_model=StartSessionResponse)
async def start_session() -> StartSessionResponse:
    """Create a new minimal session and return its ID.

    The SessionStore is responsible for generating a unique session_id
    and initializing any in-memory / on-disk state.
    """
    session_store = _require_session_store()
    session = session_store.create_session()
    return StartSessionResponse(session_id=session.session_id)


@router.post("/request", response_model=AgentResponse)
async def handle_request(request: AgentRequest) -> AgentResponse:
    """Handle a single user message within a session.

    Delegates to ConversationAgent, which uses the SessionStore and
    ActionPlanStore under the hood to decide between clarification and
    returning a concrete ActionPlan.

    This handler now logs key context (app_id, session_id, message)
    whenever an HTTPException is raised, which is especially useful
    for debugging 400- and 404-level errors observed by the client.
    """
    try:
        session_store = _require_session_store()
        agent = _require_conversation_agent()

        session = session_store.get_session(request.session_id)
        if session is None:
            # Session not found for this session_id
            raise HTTPException(status_code=404, detail="Session not found")

        # Attach app_id to the session on first use, and enforce that it
        # does not change across requests for the same session.
        if session.app_id is None:
            session.app_id = request.app_id
            session_store.save_session(session)
        elif session.app_id != request.app_id:
            raise HTTPException(
                status_code=400,
                detail="app_id does not match existing session",
            )

        response = agent.handle_user_message(
            session_id=request.session_id,
            message=request.message,
        )
        return response

    except HTTPException as e:
        # Log structured context for any HTTP error (e.g., 400/404) so
        # that we can correlate client-side failures with server-side
        # reasons.
        logger.warning(
            "[AGENT] HTTP %s for app_id=%s session_id=%s message=%r reason=%r",
            e.status_code,
            request.app_id,
            request.session_id,
            request.message,
            e.detail,
        )
        raise

    except Exception as e:
        # Log unexpected errors with a full traceback for debugging.
        logger.exception(
            "[AGENT] Unexpected error for app_id=%s session_id=%s message=%r",
            request.app_id,
            request.session_id,
            request.message,
        )
        raise

# --------------------------------------------------------
# Endpoint: GET /healthz
# --------------------------------------------------------
@router.get("/healthz")
def health_check():
    """
    Simple health check endpoint for uptime monitoring.
    """
    return {"status": "ok"}
