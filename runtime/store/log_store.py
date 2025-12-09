"""
LogStore: append-only logging for AVA-Gen runtime events.

This can write JSON lines to:

    runtime/data/logs/actions_YYYY-MM-DD.jsonl

For now, this is a stub.
"""


class LogStore:
    """Simple logging abstraction (placeholder)."""

    def __init__(self, log_dir: str = "runtime/data/logs"):
        self.log_dir = log_dir

    def log_event(self, event_type: str, payload: dict) -> None:
        """
        Append an event to a log file.

        TODO: implement date-based JSONL logging.
        """
        raise NotImplementedError


