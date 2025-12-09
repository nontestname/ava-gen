"""ActionPlanStore: loads generated ActionPlan JSON files from workspace.

Expected layout (by convention):

    workspace/actionplan/<app_id>_actionplan.json

The JSON structure is assumed to look like:

    {
      "app_id": "hu.vmiklos.plees_tracker",
      "action_plans": {
        "accessStatistics": { ... },
        "startTracking": { ... }
      }
    }

This store provides a simple API:

    get_actionplan(app_id, method_name) -> dict | None

and hides the details of locating and parsing the per-app JSON files.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class ActionPlanStore:
    """Read-only access to per-app actionplan JSON files.

    Parameters
    ----------
    workspace_root:
        Root directory that contains a shared actionplan directory. For a given
        app_id, the store looks for:

            <workspace_root>/actionplan/<app_id>_actionplan.json

        By default this is "workspace" (relative to the current working
        directory), matching the AVA-Gen convention.
    """

    def __init__(self, workspace_root: str = "workspace") -> None:
        self.workspace_root = Path(workspace_root)
        # In-memory cache: app_id -> { method_name -> action_plan_dict }
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _actionplan_path(self, app_id: str) -> Path:
        """Return the expected JSON path for the given app_id."""
        return (
            self.workspace_root
            / "actionplan"
            / f"{app_id}_actionplan.json"
        )

    def _load_app_plans(self, app_id: str) -> Dict[str, Any]:
        """Load and cache the action_plans dict for a given app_id.

        Returns a mapping of method_name -> action_plan_dict.

        Raises
        ------
        FileNotFoundError
            If the expected JSON file does not exist.
        ValueError
            If the JSON structure is missing required keys.
        """
        if app_id in self._cache:
            return self._cache[app_id]

        path = self._actionplan_path(app_id)
        if not path.is_file():
            raise FileNotFoundError(
                f"ActionPlan JSON not found for app_id={app_id}: {path}"
            )

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(
                f"Invalid actionplan file format for app_id={app_id}: expected object"
            )

        # Optional sanity check on app_id in JSON, if present.
        json_app_id = data.get("app_id")
        if json_app_id is not None and json_app_id != app_id:
            raise ValueError(
                f"App ID mismatch in actionplan file: requested app_id={app_id}, "
                f"file app_id={json_app_id}"
            )

        action_plans = data.get("action_plans")
        if action_plans is None:
            raise ValueError(
                f"Missing 'action_plans' key in actionplan file for app_id={app_id}"
            )
        if not isinstance(action_plans, dict):
            raise ValueError(
                f"Invalid 'action_plans' format for app_id={app_id}: expected object"
            )

        # Cache and return
        self._cache[app_id] = action_plans
        return action_plans

    def get_actionplan(self, app_id: str, method_name: str) -> Optional[Dict[str, Any]]:
        """Return the action plan dict for the given app + method.

        Parameters
        ----------
        app_id:
            The application ID, e.g. "hu.vmiklos.plees_tracker".
        method_name:
            The VA method name, e.g. "accessStatistics".

        Returns
        -------
        dict | None
            The action plan dictionary for the given method, or None if
            the method is not defined for this app.

        Raises
        ------
        FileNotFoundError
            If the corresponding app's actionplan JSON file does not exist.
        ValueError
            If the JSON structure is malformed.
        """
        action_plans = self._load_app_plans(app_id)
        plan = action_plans.get(method_name)
        if plan is None:
            # The app is known (file exists), but the requested method
            # does not have an action plan defined.
            return None
        if not isinstance(plan, dict):
            raise ValueError(
                f"Invalid action plan entry for app_id={app_id}, method={method_name}: "
                f"expected object, got {type(plan)!r}"
            )
        return plan

    def get_methods_for_app(self, app_id: str) -> Dict[str, Any]:
        """Return the full mapping of method_name -> action_plan for an app.

        This can be useful for debugging or for listing supported methods.
        """
        return self._load_app_plans(app_id)
