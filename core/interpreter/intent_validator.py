# interpreter/intent_validator.py
"""
Intent validation and intent → method mapping for AVA-Gen.

This module now loads a pre-generated, aggregated intent list for all apps,
rather than parsing individual *_skills_description.json files directly.

1. Loads workspace/intent/intent_list_full.json, which contains a list of objects:
       [
           {
               "app_id": "hu.vmiklos.plees_tracker",
               "intents": [
                   { "text": "Open sleep statistics view", "method_name": "accessStatistics" },
                   { "text": "Opens the app's statistics screen...", "method_name": "accessStatistics" }
               ]
           },
           ...
       ]
   Each object has:
     - app_id: the app's identifier
     - intents: a list of objects with "text" and "method_name" (method_name may be null).

2. Exposes an IntentValidator that:
   - provides allowed intents for a given app_id
   - delegates intent matching to a backend (e.g., OpenAI in the future)
   - returns a structured IntentValidationResult used by ConversationAgent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel
from core.api import openai_client
from configs.settings import settings  # ✅ use your existing Settings instance


# ---------------------------------------------------------------------------
# Result + backend interface
# ---------------------------------------------------------------------------


@dataclass
class IntentValidationResult:
    """Structured result of an intent validation / matching call."""

    is_supported: bool
    matched_intent: Optional[str] = None
    method_name: Optional[str] = None
    reason: Optional[str] = None


class IntentMatcherBackend(Protocol):
    """
    Abstract backend interface for intent matching.

    Implementations may use:
    - OpenAI
    - other LLMs
    - simple keyword heuristics

    The backend is intentionally decoupled from the workspace layout and
    from any HTTP/DB details.
    """

    def match_intent(
        self,
        app_id: str,
        message: str,
        intents: List[str],
        history: Optional[List[Any]] = None,
    ) -> IntentValidationResult:
        """
        Given a user message and the allowed intents for an app, decide:

        - whether the message is supported (is_supported)
        - which intent best matches (matched_intent)
        - optionally which method_name it corresponds to
        - an optional human-readable reason

        This method MUST be pure (no side effects) from the perspective
        of the caller; logging / metrics are allowed internally.
        """
        ...


# ---------------------------------------------------------------------------
# IntentValidator
# ---------------------------------------------------------------------------


class IntentValidator:
    """
    Coordinates:
    - reading skills description JSON ({app_id}_skills_description.json)
    - keeping intent → method mapping per app
    - delegating scoring/matching to a backend (e.g., OpenAI)

    This is the object that ConversationAgent expects to work with:

        result = intent_validator.validate(app_id, message, history)
        result.is_supported, result.matched_intent, result.method_name, result.reason

        method_name = intent_validator.get_method_for_intent(app_id, intent)

    It does NOT know about FastAPI, sessions, or network.
    """

    def __init__(
        self,
        workspace_root: str = "workspace",
        backend: Optional[IntentMatcherBackend] = None,
    ) -> None:
        self.workspace_root = Path(workspace_root)
        self.backend = backend

        # app_id -> {
        #   "intents": List[str],
        #   "intent_to_method": Dict[str, str],
        # }
        self._apps: Dict[str, Dict[str, Any]] = {}
        self._intent_list_loaded: bool = False
        self._intent_map_loaded: bool = False

        self._load_intent_list()
        self._load_intent_method_map()

    # ------------------------------------------------------------------
    # Public API used by ConversationAgent
    # ------------------------------------------------------------------

    def get_intents_for_app(self, app_id: str) -> List[str]:
        """Return the list of allowed intent strings for a given app_id."""
        info = self._apps.get(app_id) or {}
        return list(info.get("intents", []))

    def get_method_for_intent(self, app_id: str, intent: str) -> Optional[str]:
        """Return the method_name corresponding to the given intent, if known."""
        info = self._apps.get(app_id) or {}
        mapping: Dict[str, str] = info.get("intent_to_method") or {}
        return mapping.get(intent)

    def get_intent_summary_for_app(self, app_id: str) -> Optional[str]:
        """Return the optional, precomputed intent_summary for an app, if available."""
        info = self._apps.get(app_id) or {}
        summary = info.get("intent_summary")
        if isinstance(summary, str):
            summary = summary.strip()
        return summary or None

    def validate(
        self,
        app_id: str,
        message: str,
        history: Optional[List[Any]] = None,
    ) -> IntentValidationResult:
        """
        Main entry point for intent validation.

        - Looks up the allowed intents for the app_id.
        - If none exist, returns is_supported=False with a reason.
        - If no backend is configured, returns is_supported=False with a reason.
        - Otherwise delegates to backend.match_intent(...).

        The backend MUST NOT expand the scope beyond the provided intents;
        it should only choose among them or reject.
        """
        intents = self.get_intents_for_app(app_id)
        if not intents:
            base_reason = f"No intents defined for app_id={app_id}."
            if not getattr(self, "_intent_list_loaded", False):
                base_reason += (
                    " intent_list_full.json is missing or could not be loaded; "
                    "please run IntentInterpreter.export_full_intent_list() first."
                )
            return IntentValidationResult(
                is_supported=False,
                reason=base_reason,
            )

        if self.backend is None:
            # No real matching logic configured yet.
            return IntentValidationResult(
                is_supported=False,
                reason="Intent backend is not configured.",
            )

        # Delegate actual matching to the backend.
        return self.backend.match_intent(
            app_id=app_id,
            message=message,
            intents=intents,
            history=history,
        )

    # ------------------------------------------------------------------
    # Internal loading helpers
    # ------------------------------------------------------------------

    def _load_intent_list(self) -> None:
        """
        Load the aggregated intent list from workspace/intent/intent_list_full.json.

        Expected format:

            [
              {
                "app_id": "...",
                "intents": [
                  "Open sleep statistics view",
                  "Opens the app's statistics screen..."
                ]
              },
              ...
            ]
        """
        intent_path = self.workspace_root / "intent" / "intent_list_full.json"
        if not intent_path.exists():
            self._intent_list_loaded = False
            return
        try:
            with intent_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # Do not wipe out _apps completely; we may also load a method map
            # into the same structure. Start fresh but allow _load_intent_method_map
            # to update per-app mapping later.
            self._apps = {}
            self._intent_list_loaded = True

            for item in data:
                if not isinstance(item, dict):
                    continue
                app_id = item.get("app_id")
                if not app_id:
                    continue

                intents_data = item.get("intents") or []
                intent_summary = item.get("intent_summary")
                normalized_intents: List[str] = []

                for entry in intents_data:
                    text = str(entry).strip()
                    if not text:
                        continue
                    normalized_intents.append(text)

                self._apps[app_id] = {
                    "intents": normalized_intents,
                    # mapping will be filled by _load_intent_method_map()
                    "intent_to_method": {},
                    "intent_summary": intent_summary,
                }
        except Exception:
            self._intent_list_loaded = False
            self._apps = {}

    def _load_intent_method_map(self) -> None:
        """
        Load the intent → method mapping from workspace/intent/intent_method_map.json.

        Expected format:

            {
              "app_id": {
                "intent text": "method_name",
                ...
              },
              ...
            }

        This augments self._apps[app_id]["intent_to_method"].
        """
        map_path = self.workspace_root / "intent" / "intent_method_map.json"
        if not map_path.exists():
            self._intent_map_loaded = False
            return

        try:
            with map_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                self._intent_map_loaded = False
                return

            for app_id, mapping in data.items():
                if not isinstance(mapping, dict):
                    continue

                info = self._apps.get(app_id)
                if info is None:
                    info = {"intents": [], "intent_to_method": {}}
                    self._apps[app_id] = info

                intent_to_method: Dict[str, str] = info.get("intent_to_method") or {}

                for intent_text, method_name in mapping.items():
                    text = str(intent_text).strip()
                    method = str(method_name).strip()
                    if not text or not method:
                        continue
                    intent_to_method[text] = method

                info["intent_to_method"] = intent_to_method

            self._intent_map_loaded = True
        except Exception:
            self._intent_map_loaded = False


# ---------------------------------------------------------------------------
# OpenAI-based backend (optional)
# ---------------------------------------------------------------------------


class IntentMatchResultModel(BaseModel):
    """Structured result from GPT for intent matching.

    GPT chooses:
    - is_supported: bool
    - matched_intent: the SINGLE best intent string from the provided list, or null
    - reason: a short natural-language explanation (at most ~20 words)
    """

    is_supported: bool
    matched_intent: Optional[str] = None
    reason: Optional[str] = None


class OpenAIIntentMatcherBackend(IntentMatcherBackend):
    """IntentMatcherBackend implementation using the project-local openai_client.

    This backend is intentionally thin: it only knows how to formulate a
    prompt and parse a structured response. It does *not* know anything
    about FastAPI, sessions, or storage.

    It relies on openai_client.send_request_to_gpt, which already manages
    model configuration and basic error handling. Here we only define:
    - the prompt format
    - the structured output schema (IntentMatchResultModel)
    """

    def __init__(self, model: Optional[str] = None, temperature: float = 0.0) -> None:
        # Prefer explicitly provided model; otherwise load from global settings
        self.model = settings.intent_model
        self.temperature = temperature  # currently encoded in the prompt text

    def match_intent(
        self,
        app_id: str,
        message: str,
        intents: List[str],
        history: Optional[List[Any]] = None,
    ) -> IntentValidationResult:
        """Call GPT via openai_client to choose the best intent or reject.

        Responsibilities:
        1. Reject if there are no intents.
        2. Provide GPT with:
           - app_id
           - allowed intents
           - recent history (for pronouns / context)
           - current user message
        3. Ask GPT to output a JSON object matching IntentMatchResultModel.
        """
        if not intents:
            return IntentValidationResult(
                is_supported=False,
                reason="No intents provided to the OpenAI backend.",
            )

        # Prepare a short text history snippet (last few turns).
        history_lines: List[str] = []
        if history:
            for turn in history[-4:]:
                try:
                    role = getattr(turn, "role", "user")
                    text = getattr(turn, "message", "")
                    if not text:
                        continue
                    history_lines.append(f"{role}: {text}")
                except Exception:
                    continue

        history_block = "\n".join(history_lines) if history_lines else "None"

        # Build the prompt. We:
        # - constrain GPT to only choose among the provided intents
        # - allow it to say "unsupported" when nothing fits
        prompt_lines: List[str] = []
        prompt_lines.append(
            "You are an intent classifier for a single mobile app. "
            "Your job is to decide whether the user's request matches one of the "
            "allowed intents for this app."
        )
        prompt_lines.append("")
        prompt_lines.append(f"App id: {app_id}")
        prompt_lines.append("")
        prompt_lines.append("Allowed intents (each line is one intent string):")
        for idx, intent in enumerate(intents, start=1):
            prompt_lines.append(f"{idx}. {intent}")
        prompt_lines.append("")
        prompt_lines.append("Recent conversation history (oldest to newest):")
        prompt_lines.append(history_block)
        prompt_lines.append("")
        prompt_lines.append("Current user request:")
        prompt_lines.append(message)
        prompt_lines.append("")
        prompt_lines.append(
            "Decide the following and respond ONLY with a single valid JSON object.\n"
            "- is_supported: true or false.\n"
            "- matched_intent: if is_supported is true, the SINGLE best intent string, "
            "exactly as it appears in the allowed intents list; otherwise null.\n"
            "- reason: a short natural-language explanation of your decision (at most 20 words)."
        )
        prompt_lines.append("")
        prompt_lines.append(
            "The JSON must:\n"
            "- use double quotes for all keys and string values (standard JSON).\n"
            "- NOT include any markdown, code fences, or backticks.\n"
            "- NOT include any extra commentary before or after the JSON.\n"
            "- NOT escape single quotes inside strings; write \"user's data\" not \"user\\'s data\".\n"
            "The JSON must have exactly these keys: "
            '"is_supported", "matched_intent", "reason".'
        )

        full_prompt = "\n".join(prompt_lines)

        try:
            result_model = openai_client.send_request_to_gpt(
                full_prompt,
                structured_output=IntentMatchResultModel,
                model=self.model,
            )
        except Exception as exc:
            # Any unexpected error from the helper/OpenAI -> treat as unsupported
            # but do NOT crash the whole runtime.
            return IntentValidationResult(
                is_supported=False,
                reason=f"OpenAI backend error: {exc}",
            )

        # Convert the Pydantic model into our dataclass.
        return IntentValidationResult(
            is_supported=result_model.is_supported,
            matched_intent=result_model.matched_intent,
            method_name=None,  # always resolved by server-side map, never by GPT
            reason=result_model.reason,
        )
