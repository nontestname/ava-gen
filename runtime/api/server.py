"""
FastAPI application entry point for the AVA-Gen runtime.

Responsibilities:
- create the FastAPI app
- construct shared singletons (SessionStore, ActionPlanStore, IntentValidator, ConversationAgent)
- include session-related routes under /agent
"""

from fastapi import FastAPI

from configs.settings import settings
from core.interpreter.intent_validator import (
    IntentValidator,
    OpenAIIntentMatcherBackend,
)
from runtime.agents.conversation_agent import ConversationAgent
from runtime.store.session_store import SessionStore
from runtime.store.actionplan_store import ActionPlanStore
from . import session_routes


class ConsoleLogStore:
    """Very small log sink used during local development / testing.

    For now this just prints events; it can later be replaced with a
    JSONL-based LogStore that writes to runtime/data/logs.
    """

    def log_event(self, event_type: str, payload: dict) -> None:
        print(f"[LOG] {event_type}: {payload}")


# ---------------------------------------------------------------------------
# Shared singletons
# ---------------------------------------------------------------------------

# Session storage: in-memory with optional file backing under runtime/data.
session_store = SessionStore(data_dir=str(settings.runtime_data_dir))

# ActionPlan storage: reads workspace/<app_id>/actionplan/<app_id>_actionplan.json
actionplan_store = ActionPlanStore(workspace_root=str(settings.workspace_root))

# Simple console logger for now.
log_store = ConsoleLogStore()

# IntentValidator with backend configured with OPENAI.
backend = OpenAIIntentMatcherBackend(
    model=settings.intent_model,
    temperature=0.0,
)
intent_validator = IntentValidator(
    workspace_root=str(settings.workspace_root),
    backend=backend,
)

# Main conversation agent used by the /agent routes.
conversation_agent = ConversationAgent(
    session_store=session_store,
    actionplan_store=actionplan_store,
    log_store=log_store,
    intent_validator=intent_validator,
)

# ---------------------------------------------------------------------------
# FastAPI app + route registration
# ---------------------------------------------------------------------------

app = FastAPI(title="AVA-Gen Runtime")

# Initialize the router module with our shared objects, then include it.
session_routes.init_routes(
    session_store=session_store,
    conversation_agent=conversation_agent,
)
app.include_router(session_routes.router, prefix="/agent")
