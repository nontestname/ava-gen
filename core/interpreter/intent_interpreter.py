"""
interpreter/intent_interpreter.py

Intent → method mapping based on skills_description files.

Assumptions about workspace layout
----------------------------------
- All skills description files live under `workspace/`, typically in `workspace/skills_description/`, with names:

    {app_id}_skills_description.json

- Each file describes all VA methods for a single app.

We expect one of the following shapes:

1) Rich per-method skills description (preferred):

    {
      "app_id": "hu.vmiklos.plees_tracker",
      "skills": [
        {
          "method_name": "accessStatistics",
          "description_short": "Navigate to the app's \"Statistics\" section.",
          "description_detail": "Open the navigation menu and select the Statistics option to view graphs."
        },
        ...
      ]
    }

2) Already-aggregated intent list (fallback):

    {
      "app_id": "hu.vmiklos.plees_tracker",
      "intentList": [
        "Navigate to the app's \"Statistics\" section.",
        "Automate UI deletion of all sleep data."
      ]
    }

In case (1), we will build both:
- an `intentList` of strings (short+detail joined)
- an internal mapping from each intent string → method_name

In case (2), we only have intent strings (no method_name mapping).
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class IntentEntry:
    """One intent phrase and the VA method it maps to (if known)."""

    intent: str
    method_name: Optional[str]  # may be None if we don't know the method


@dataclass
class AppIntentIndex:
    """All intents and mappings for a single app."""

    app_id: str
    intents: List[IntentEntry]

    @property
    def intent_list(self) -> List[str]:
        """Return just the list of intent strings (for validators / LLM)."""
        return [entry.intent for entry in self.intents]


class IntentInterpreter:
    """
    Loads {app_id}_skills_description.json files from the workspace and builds:

    - for each app_id:
        * a list of intent strings (`intent_list`)
        * a mapping intent → method_name (when available)

    This can be used by:
    - an intent validator (e.g., OpenAI-based) that needs allowed intents
    - the runtime ConversationAgent to map a chosen intent back to a method
    """

    def __init__(self, workspace_root: str = "workspace") -> None:
        self.workspace_root = Path(workspace_root)
        # app_id -> AppIntentIndex
        self._apps: Dict[str, AppIntentIndex] = {}

        self._load_all_skills_descriptions()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_intents_for_app(self, app_id: str) -> List[str]:
        """
        Return the list of allowed intent strings for a given app_id.

        This matches the shape used by IntentValidator.intentList in your
        backend (and by the example you gave).
        """
        index = self._apps.get(app_id)
        if not index:
            return []
        return index.intent_list

    def get_method_for_intent(self, app_id: str, intent: str) -> Optional[str]:
        """
        Given an app_id and an intent string, return the associated method_name
        if known. This assumes the intent string is exactly one of the entries
        we generated (or you may normalize before calling).
        """
        index = self._apps.get(app_id)
        if not index:
            return None

        for entry in index.intents:
            if entry.intent == intent:
                return entry.method_name
        return None

    def list_apps(self) -> List[str]:
        """Return all app_ids discovered in the workspace."""
        return sorted(self._apps.keys())

    # ------------------------------------------------------------------
    # Internal GPT-backed helpers
    # ------------------------------------------------------------------

    def _summarize_intents(self, app_id: str, intents: List[str]) -> Optional[str]:
        """
        Produce a short (< 20 words) natural-language summary of an app's intents.

        This uses the OpenAI helper (send_request_to_gpt) if available. If the
        OpenAI client is not configured or the call fails, returns None and
        silently skips the summary.
        """
        if not intents:
            return None

        # Lazy import so that environments without OPENAI_API_KEY can still
        # use this module without failing at import time.
        try:
            from core.api.openai_client import send_request_to_gpt
        except Exception:
            return None

        # Build a concise prompt describing the app's intents.
        lines: List[str] = []
        lines.append(
            "You are summarizing what a mobile app's assistant can do."
        )
        lines.append(f"App id: {app_id}")
        lines.append("")
        lines.append("Here are the allowed intents for this app:")
        for idx, intent in enumerate(intents, start=1):
            lines.append(f"{idx}. {intent}")
        lines.append("")
        lines.append(
            "Write ONE sentence (at most 20 words) that summarizes what these "
            "intents allow the assistant to help the user with."
        )
        lines.append(
            "Do not include numbering or lists. Respond with plain text only."
        )

        prompt = "\n".join(lines)

        try:
            summary = send_request_to_gpt(prompt)
        except Exception:
            return None

        summary = (summary or "").strip()
        return summary or None

    # ------------------------------------------------------------------
    def export_full_intent_list(self, output_path: Optional[str] = None) -> Path:
        """
        Aggregate intents from all {app_id}_skills_description.json files and write them
        to workspace/intent/intent_list_full.json (or a custom output_path).

        NEW FORMAT (intent strings only):

            [
              {
                "app_id": "hu.vmiklos.plees_tracker",
                "intents": [
                  "Open sleep statistics view",
                  "Opens the app's statistics screen to view summarized sleep data and averages."
                ]
              },
              ...
            ]

        This file is used by IntentValidator / GPT as the *allowed intent list*.
        Method mapping is stored separately in intent_method_map.json.
        """
        if output_path is None:
            intent_dir = self.workspace_root / "intent"
            output = intent_dir / "intent_list_full.json"
        else:
            output = Path(output_path)
            intent_dir = output.parent

        intent_dir.mkdir(parents=True, exist_ok=True)

        # self._apps maps app_id -> AppIntentIndex, which has .intents
        # where each element is an IntentEntry(intent: str, method_name: Optional[str])
        data = []
        for app_id, index in sorted(self._apps.items()):
            try:
                intent_texts = [entry.intent for entry in index.intents]
            except AttributeError:
                intent_texts = list(getattr(index, "intent_list", []))

            # Optional GPT-backed summary for this app's intents.
            intent_summary = self._summarize_intents(app_id, intent_texts)

            item = {
                "app_id": app_id,
                "intents": intent_texts,
            }
            if intent_summary:
                item["intent_summary"] = intent_summary

            data.append(item)

        with output.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output

    def export_intent_method_map(self, output_path: Optional[str] = None) -> Path:
        """
        Export a deterministic mapping from intent text -> method_name per app.

        Output format (workspace/intent/intent_method_map.json):

            {
              "hu.vmiklos.plees_tracker": {
                "Open sleep statistics view": "accessStatistics",
                "Opens the app's statistics screen to view summarized sleep data and averages.": "accessStatistics"
              },
              "com.pocket_plan.j7_003": {
                "Activate and access the sleep reminder feature.": "activateSleepReminder",
                ...
              }
            }

        This file is used by IntentValidator.get_method_for_intent() on the server.
        GPT never sees this file.
        """
        if output_path is None:
            intent_dir = self.workspace_root / "intent"
            output = intent_dir / "intent_method_map.json"
        else:
            output = Path(output_path)
            intent_dir = output.parent

        intent_dir.mkdir(parents=True, exist_ok=True)

        mapping: Dict[str, Dict[str, str]] = {}

        for app_id, index in self._apps.items():
            try:
                entries = index.intents  # list[IntentEntry]
            except AttributeError:
                entries = getattr(index, "intents", [])

            app_map: Dict[str, str] = {}
            for entry in entries:
                try:
                    text = entry.intent
                    method_name = entry.method_name
                except AttributeError:
                    continue

                if not text or not method_name:
                    continue
                text = str(text).strip()
                method_name = str(method_name).strip()
                if not text or not method_name:
                    continue

                app_map[text] = method_name

            if app_map:
                mapping[app_id] = app_map

        with output.open("w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)

        return output

    # ------------------------------------------------------------------
    # Internal loading helpers
    # ------------------------------------------------------------------

    def _load_all_skills_descriptions(self) -> None:
        """
        Scan the workspace for *skills_description.json files and build indexes.

        Expected pattern:
            workspace/{app_id}_skills_description.json
        """
        pattern = "*_skills_description.json"
        for path in self.workspace_root.rglob(pattern):
            try:
                index = self._load_single_file(path)
            except Exception:
                # For robustness: skip broken files rather than crash.
                continue
            self._apps[index.app_id] = index

    def _load_single_file(self, path: Path) -> AppIntentIndex:
        """Load one {app_id}_skills_description.json and build AppIntentIndex."""
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Derive app_id from JSON if present; else from filename.
        json_app_id = data.get("app_id")
        if json_app_id:
            app_id = json_app_id
        else:
            # Strip the suffix `_skills_description.json`
            stem = path.stem  # e.g. com.pocket_plan.j7_003_skills_description
            suffix = "_skills_description"
            app_id = stem[:-len(suffix)] if stem.endswith(suffix) else stem

        # Case 1: rich skills structure with method_name + descriptions
        if "skills" in data or "methods" in data:
            skills = data.get("skills") or data.get("methods") or []
            intents: List[IntentEntry] = []
            for skill in skills:
                method_name = skill.get("method_name")
                short = skill.get("description_short") or ""
                detail = skill.get("description_detail") or ""
                # Combine short + detail; you can tweak how they are concatenated.
                pieces = [short.strip(), detail.strip()]
                combined = " ".join(p for p in pieces if p)
                if combined:
                    intents.append(IntentEntry(intent=combined, method_name=method_name))
            return AppIntentIndex(app_id=app_id, intents=intents)

        # Case 2: already aggregated intentList without method mappings
        if "intentList" in data:
            intents = [
                IntentEntry(intent=str(text), method_name=None)
                for text in data.get("intentList", [])
            ]
            return AppIntentIndex(app_id=app_id, intents=intents)

        # Case 3: context_methods dict with per-method short/detail descriptions.
        # In this format the method name is the dict key and we treat
        # description-short and description-detail as separate intents that both
        # map to the same method.
        if "context_methods" in data and isinstance(data["context_methods"], dict):
            intents: List[IntentEntry] = []
            for method_name, value in data["context_methods"].items():
                if not isinstance(value, dict):
                    continue
                short = (value.get("description-short") or "").strip()
                detail = (value.get("description-detail") or "").strip()

                # Add short description as its own intent, if present.
                if short:
                    intents.append(
                        IntentEntry(
                            intent=short,
                            method_name=method_name,
                        )
                    )

                # Add detailed description as a second intent, if present.
                if detail:
                    intents.append(
                        IntentEntry(
                            intent=detail,
                            method_name=method_name,
                        )
                    )

            return AppIntentIndex(app_id=app_id, intents=intents)

        # If we reach here, the structure is unknown; treat as no intents.
        return AppIntentIndex(app_id=app_id, intents=[])


# ----------------------------------------------------------------------
# CLI helper
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Use the configured workspace root (if available).
    try:
        from configs.settings import settings

        workspace_root = str(settings.workspace_root)
    except Exception:
        workspace_root = "workspace"

    interpreter = IntentInterpreter(workspace_root=workspace_root)
    list_path = interpreter.export_full_intent_list()
    map_path = interpreter.export_intent_method_map()
    print(f"Wrote full intent list (with optional intent_summary) to: {list_path}")
    print(f"Wrote intent→method map to: {map_path}")
