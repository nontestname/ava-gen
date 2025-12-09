"""Minimal session storage for AVA-Gen.

For now, this is primarily an in-memory dict of session_id -> Session,
with optional JSON persistence under a data directory.

The design is intentionally simple:
- In-memory access is the primary source of truth during a run.
- If a data_dir is configured, sessions are also written to
  `data_dir/sessions/<session_id>.json` so that they can be reloaded
  on restart for debugging or replay.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from uuid import uuid4

from ..models.session_models import Session


class SessionStore:
    """In-memory + optional file-backed session store.

    Parameters
    ----------
    data_dir:
        Base directory for storing session JSON files. If provided,
        sessions will be written to and read from
        `data_dir/sessions/<session_id>.json`.

        If not provided, a default directory `runtime/data/sessions`
        relative to the current working directory will be used when
        persistence is needed.
    """

    def __init__(self, data_dir: Optional[str] = None) -> None:
        # In-memory cache of sessions for fast access.
        self._sessions: Dict[str, Session] = {}

        # Optional base directory for persistence.
        self._data_dir: Optional[Path] = Path(data_dir) if data_dir else None

        # Ensure the sessions directory exists if a data_dir is configured.
        if self._data_dir is not None:
            self._sessions_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _sessions_dir(self) -> Path:
        """Return the directory used to store session JSON files.

        If `data_dir` was provided, use `<data_dir>/sessions`.
        Otherwise, default to `runtime/data/sessions`.
        """
        if self._data_dir is None:
            base = Path("runtime/data")
        else:
            base = self._data_dir
        return base / "sessions"

    def create_session(self, app_id: Optional[str] = None) -> Session:
        """Create a new session and return it.

        If `app_id` is provided, the session will be bound to that app
        immediately. Otherwise, the app_id can be set later (e.g., on
        the first /agent/request call).

        A newly created session starts with:
        - a random UUID as `session_id`
        - the provided `app_id` (or None)
        - empty turns
        - status OPEN (set by the Session model default)
        """
        session_id = str(uuid4())
        session = Session(session_id=session_id, app_id=app_id)

        # Store in memory and persist to disk if configured.
        self._sessions[session_id] = session
        self._persist_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve an existing session by ID.

        Lookup order:
        1. Check the in-memory cache.
        2. If not found and a data_dir is configured, attempt to
           load the session from disk.
        3. If still not found, return None.
        """
        # 1) Check in-memory cache first.
        if session_id in self._sessions:
            return self._sessions[session_id]

        # 2) Attempt to load from disk if persistence is configured.
        if self._data_dir is not None:
            path = self._sessions_dir / f"{session_id}.json"
            if path.is_file():
                try:
                    with path.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    session = Session(**data)
                except Exception:
                    # If loading fails for any reason, treat as not found.
                    return None

                # Cache in memory for subsequent access.
                self._sessions[session_id] = session
                return session

        # 3) Not found anywhere.
        return None

    def save_session(self, session: Session) -> None:
        """Persist the given session in memory and to disk (if enabled).

        This should be called whenever the session is updated (e.g.,
        when new turns are appended or the status changes).
        """
        self._sessions[session.session_id] = session
        self._persist_session(session)

    def _persist_session(self, session: Session) -> None:
        """Write the session to disk if a data_dir is configured.

        If no data_dir was provided, this is a no-op.
        """
        if self._data_dir is None:
            # No file-based persistence configured.
            return

        sessions_dir = self._sessions_dir
        sessions_dir.mkdir(parents=True, exist_ok=True)
        path = sessions_dir / f"{session.session_id}.json"

        with path.open("w", encoding="utf-8") as f:
            json.dump(session.dict(), f, ensure_ascii=False, indent=2)
