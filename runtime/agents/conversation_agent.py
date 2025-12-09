"""ConversationAgent implementation.

Responsible for:
- inspecting the current session (history, app_id)
- taking a new user message
- deciding how to respond

Current behavior:
- always appends the user's message as a Turn
- if an intent_validator is configured, uses it to decide whether the
  request is supported and, if so, which VA method to execute and which
  ActionPlan to return.
- if no intent_validator is available (or it fails), falls back to a
  simple clarification-style response.
- always appends the server's response as another Turn
- persists the updated Session via SessionStore
"""

from datetime import datetime, timezone
from typing import Optional

from ..models.api_models import AgentResponse
from ..models.session_models import Session, Turn, SessionStatus


class ConversationAgent:
    """Conversation + decision logic for AVA-Gen.

    Parameters
    ----------
    session_store:
        Store used to load and persist Session objects.
    actionplan_store:
        Store used to look up ActionPlans for a given app + method.
    log_store:
        Store used to log high-level events (optional).
    intent_validator:
        Optional component responsible for mapping a user message to a
        supported intent and method_name. It is expected to expose:

            validate(app_id, message, history) -> result
                where result has at least:
                    - is_supported: bool
                    - matched_intent: Optional[str]
                    - method_name: Optional[str] (optional)
                    - reason: Optional[str]

            get_method_for_intent(app_id, intent) -> Optional[str]

        If this validator is None, the agent will always return a
        clarification-style response.
    """

    def __init__(self, session_store, actionplan_store, log_store, intent_validator: Optional[object] = None):
        # Initialize the ConversationAgent with the necessary stores and optional intent validator.
        self.session_store = session_store
        self.actionplan_store = actionplan_store
        self.log_store = log_store
        self.intent_validator = intent_validator

    def handle_user_message(self, session_id: str, message: str) -> AgentResponse:
        """Handle a single user message within the given session.

        Flow:
        - load Session from store
        - append user Turn
        - if an intent_validator is configured, attempt to use it to
          decide between clarification vs. action_plan
        - otherwise, or on failure, fall back to a simple clarification
        - append server Turn
        - save Session
        - return AgentResponse
        """
        # Load the current session from the session store.
        session: Session | None = self.session_store.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        now = datetime.now(timezone.utc).isoformat()

        # (1) Append user turn: record the incoming user message as a Turn in the session history.
        user_turn = Turn(
            role="user",
            message=message,
            type="user",
            timestamp=now,
        )
        session.turns.append(user_turn)

        # (2) First, handle meta-requests asking for an intent summary, if possible.
        # This uses GPT to classify whether the user is asking about the app's
        # capabilities and, if so, returns the precomputed intent_summary.
        summary_response: Optional[AgentResponse] = None
        try:
            summary_response = self._maybe_handle_intent_summary(session, message)
        except Exception:
            summary_response = None

        if summary_response is not None:
            # Persist session (with the appended user + server turns) and return.
            self.session_store.save_session(session)
            return summary_response

        # (3) Try to handle with intent_validator if available.
        # This is the main decision point: use the validator to determine if the message corresponds to a supported intent.
        if self.intent_validator is not None:
            try:
                # Attempt to process the message via the intent validator.
                response = self._handle_with_intent_validator(session, message)
            except NotImplementedError:
                # Validator not implemented yet; fall back to clarification response.
                response = self._fallback_clarification(session, message)
            except Exception:
                # Any unexpected error in validation should not break the main flow; fall back to clarification.
                response = self._fallback_clarification(session, message)
        else:
            # (4) No validator configured; always clarify.
            response = self._fallback_clarification(session, message)

        # (5) Persist updated session after appending both user and server turns.
        self.session_store.save_session(session)

        # (6) Logging is done inside helpers; just return the response.
        return response

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _maybe_handle_intent_summary(
        self,
        session: Session,
        message: str,
    ) -> Optional[AgentResponse]:
        """
        Use GPT to decide whether the user is asking for a high-level
        summary of what the app can do (its intents). If so, return an
        AgentResponse with the precomputed intent_summary for this app.

        If GPT classification fails or no summary is available, return None.
        """
        app_id = session.app_id
        if not app_id or self.intent_validator is None:
            return None

        # Get the precomputed summary text for this app, if any.
        summary: Optional[str] = None
        if hasattr(self.intent_validator, "get_intent_summary_for_app"):
            try:
                summary = self.intent_validator.get_intent_summary_for_app(app_id)
            except Exception:
                summary = None

        if not summary:
            return None

        # Lazy-import GPT helper to avoid hard dependency when OpenAI is not configured.
        try:
            from core.api.openai_client import send_request_to_gpt
        except Exception:
            return None

        # Ask GPT to classify whether this message is a capabilities / intents question.
        classification_prompt_lines = [
            "You classify whether a user message is asking about an app's capabilities",
            "(its intents) or asking to perform a specific action.",
            "",
            "Examples that SHOULD be classified as YES (asking for a summary of intents):",
            '- "What can you do?"',
            '- "What can this app do?"',
            '- "What can I do here?"',
            '- "What can I ask?"',
            '- "What are your intents?"',
            '- "What intents are available?"',
            '- "List intents."',
            "",
            "Examples that SHOULD be classified as NO (specific actions, not capability questions):",
            '- "Open sleep statistics screen"',
            '- "Delete all sleep entries"',
            '- "Start tracking my sleep"',
            "",
            "User message:",
            message,
            "",
            "Answer with exactly one word: YES or NO.",
        ]
        classification_prompt = "\n".join(classification_prompt_lines)

        try:
            raw = send_request_to_gpt(classification_prompt)
        except Exception:
            return None

        answer = (raw or "").strip().lower()
        if answer.startswith("yes"):
            is_summary_request = True
        elif answer.startswith("no"):
            is_summary_request = False
        else:
            # Unclear response; do not treat as a summary request.
            return None

        if not is_summary_request:
            return None

        # At this point we have both a summary request and a summary string.
        server_turn = Turn(
            role="server",
            message=summary,
            type="intent_summary",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        session.turns.append(server_turn)
        session.status = SessionStatus.OPEN

        if self.log_store is not None:
            try:
                self.log_store.log_event(
                    event_type="intent_summary",
                    payload={
                        "session_id": session.session_id,
                        "app_id": app_id,
                    },
                )
            except Exception:
                pass

        return AgentResponse(
            type="clarification",
            message=summary,
            method_name=None,
            action_plan=None,
            next_session_id=None,
        )

    def _fallback_clarification(self, session: Session, message: str) -> AgentResponse:
        """Produce a simple clarification-style response.

        This matches the original placeholder behavior and is used
        whenever no intent validator is configured or validation fails.
        """
        # Prepare a generic clarification message indicating the lack of intent processing.
        clarification_text = (
            "(AVA-Gen placeholder) I received your request but intent-to-"
            "ActionPlan logic is not implemented or not available. This is "
            "a dummy clarification response."
        )

        # Append the clarification as a server turn in the session history.
        server_turn = Turn(
            role="server",
            message=clarification_text,
            type="clarification",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        session.turns.append(server_turn)

        # Mark the session status as open, indicating no specific action plan was sent.
        session.status = SessionStatus.OPEN

        # Log event (optional) to record that a clarification was sent due to fallback.
        if self.log_store is not None:
            try:
                self.log_store.log_event(
                    event_type="clarification_sent",
                    payload={
                        "session_id": session.session_id,
                        "app_id": session.app_id,
                        "message": message,
                        "reason": "fallback",
                    },
                )
            except Exception:
                # Logging failures should not affect main flow.
                pass

        # Return an AgentResponse indicating a clarification was sent.
        return AgentResponse(
            type="clarification",
            message=clarification_text,
            method_name=None,
            action_plan=None,
            next_session_id=None,
        )

    def _handle_with_intent_validator(self, session: Session, message: str) -> AgentResponse:
        """Use the configured intent_validator to decide the next action.

        High-level logic:
        - call validator.validate(app_id, message, history=session.turns)
        - if not supported -> clarification
        - if supported -> map intent to method_name, load ActionPlan,
          and return an action_plan response
        """
        app_id = session.app_id

        # Call the validator to check if the message is supported and to identify the intent and method.
        result = self.intent_validator.validate(
            app_id=app_id,
            message=message,
            history=list(session.turns),  # pass a snapshot of turns
        )

        # Extract relevant fields from the validation result.
        is_supported = getattr(result, "is_supported", False)
        matched_intent = getattr(result, "matched_intent", None)
        reason = getattr(result, "reason", None)

        # (2a) If the intent is not supported, generate an unsupported clarification response.
        if not is_supported:
            clarification_text = (
                reason
                or "This request is not supported for the current app. "
                "Please try a different phrasing or another action."
            )

            server_turn = Turn(
                role="server",
                message=clarification_text,
                type="clarification_unsupported",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            session.turns.append(server_turn)
            session.status = SessionStatus.OPEN

            if self.log_store is not None:
                try:
                    self.log_store.log_event(
                        event_type="intent_not_supported",
                        payload={
                            "session_id": session.session_id,
                            "app_id": app_id,
                            "message": message,
                            "reason": reason,
                        },
                    )
                except Exception:
                    pass

            return AgentResponse(
                type="clarification",
                message=clarification_text,
                method_name=None,
                action_plan=None,
                next_session_id=None,
            )

        # (2b) Supported: always resolve method_name from the server-side map using matched_intent.
        method_name: Optional[str] = None
        if matched_intent and hasattr(self.intent_validator, "get_method_for_intent"):
            method_name = self.intent_validator.get_method_for_intent(
                app_id, matched_intent
            )

        # (2c) If method_name cannot be resolved, return an explicit configuration clarification.
        if not method_name:
            clarification_text = (
                "I recognized your intent, but I could not map it to a concrete action. "
                "Please double-check the intent→method configuration."
            )

            server_turn = Turn(
                role="server",
                message=clarification_text,
                type="clarification_ambiguous",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            session.turns.append(server_turn)
            session.status = SessionStatus.OPEN

            if self.log_store is not None:
                try:
                    self.log_store.log_event(
                        event_type="intent_ambiguous",
                        payload={
                            "session_id": session.session_id,
                            "app_id": app_id,
                            "message": message,
                            "matched_intent": matched_intent,
                        },
                    )
                except Exception:
                    pass

            return AgentResponse(
                type="clarification",
                message=clarification_text,
                method_name=None,
                action_plan=None,
                next_session_id=None,
            )

        # (4) We have a method_name; try to load the corresponding ActionPlan.
        try:
            plan = self.actionplan_store.get_actionplan(app_id, method_name)
        except Exception as exc:
            plan = None
            load_error = str(exc)
        else:
            load_error = None

        # If no ActionPlan is found, return a clarification indicating this.
        if not plan:
            clarification_text = (
                "I recognized your intent, but there is no ActionPlan "
                f"defined for method '{method_name}'."
            )
            if load_error:
                clarification_text += f" (Details: {load_error})"

            # Append the clarification as a server turn.
            server_turn = Turn(
                role="server",
                message=clarification_text,
                type="clarification_no_plan",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            session.turns.append(server_turn)
            session.status = SessionStatus.OPEN

            # Log the missing ActionPlan event.
            if self.log_store is not None:
                try:
                    self.log_store.log_event(
                        event_type="actionplan_missing",
                        payload={
                            "session_id": session.session_id,
                            "app_id": app_id,
                            "method_name": method_name,
                            "error": load_error,
                        },
                    )
                except Exception:
                    pass

            # Return a clarification AgentResponse.
            return AgentResponse(
                type="clarification",
                message=clarification_text,
                method_name=None,
                action_plan=None,
                next_session_id=None,
            )

        # (5) At this point, we have a valid plan; mark the session as having sent an ActionPlan.
        # Use the matched intent description (if available) as a short user-facing
        # confirmation of what action will be performed. Fall back to a generic
        # method-based message if we don't have an intent string.
        if matched_intent:
            server_message = matched_intent
        else:
            server_message = f"Executing method '{method_name}' for app '{app_id}'."

        # Append the server turn with the action plan notification.
        server_turn = Turn(
            role="server",
            message=server_message,
            type="action_plan",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        session.turns.append(server_turn)
        session.status = SessionStatus.ACTION_SENT

        # Create a new session for follow-up interactions with the same app.
        next_session = self.session_store.create_session(app_id=app_id)
        next_session_id = next_session.session_id

        # Log the action plan selection event.
        if self.log_store is not None:
            try:
                self.log_store.log_event(
                    event_type="actionplan_selected",
                    payload={
                        "session_id": session.session_id,
                        "app_id": app_id,
                        "method_name": method_name,
                        "next_session_id": next_session_id,
                    },
                )
            except Exception:
                pass

        # Return an AgentResponse with the action plan details.
        return AgentResponse(
            type="action_plan",
            message=server_message,
            method_name=method_name,
            action_plan=plan,
            next_session_id=next_session_id,
        )
