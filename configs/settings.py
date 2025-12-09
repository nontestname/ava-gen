from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


class Settings:
    """
    Central configuration for AVA-Gen.

    Values are loaded once from environment variables (with sensible defaults)
    and then exposed via typed properties.
    """

    def __init__(self) -> None:
        # OpenAI / model configuration
        self._openai_api_key = os.getenv("OPENAI_API_KEY")
        self._openai_base_url = os.getenv("OPENAI_BASE_URL") or None
        self._openai_model = os.getenv("AVA_GEN_OPENAI_MODEL", "gpt-4.1-mini")

        # Workspace and runtime data paths
        self._workspace_root = Path(
            os.getenv("AVA_GEN_WORKSPACE_ROOT", "workspace")
        )
        self._runtime_data_dir = Path(
            os.getenv("AVA_GEN_RUNTIME_DATA_DIR", "runtime/data")
        )

        # Intent matcher model (defaults to OpenAI model)
        self._intent_model = os.getenv(
            "AVA_GEN_INTENT_MODEL",
            self._openai_model,
        )

    # ------------------------------------------------------------------
    # OpenAI / model settings
    # ------------------------------------------------------------------

    @property
    def openai_api_key(self) -> str:
        if not self._openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Please export it in your environment "
                "or define it in a .env file."
            )
        return self._openai_api_key

    @property
    def openai_base_url(self) -> Optional[str]:
        return self._openai_base_url

    @property
    def openai_model(self) -> str:
        return self._openai_model

    @property
    def intent_model(self) -> str:
        return self._intent_model

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------

    @property
    def workspace_root(self) -> Path:
        return self._workspace_root

    @property
    def runtime_data_dir(self) -> Path:
        return self._runtime_data_dir


settings = Settings()

