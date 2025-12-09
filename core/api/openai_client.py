"""
core.api.openai_client

Thin wrapper around the OpenAI Chat Completions API for AVA-Gen.

Used by:
  - core/interpreter/skill_interpreter.py
  - any other GPT-backed modules
"""

from __future__ import annotations

import json
from typing import Any, Optional, Type, Union

from pydantic import BaseModel
from openai import OpenAI, OpenAIError

from configs.settings import settings


# -------------------------------------------------------------------
# Client + config
# -------------------------------------------------------------------

# Create a single shared client using central settings
client = OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

# Default model for AVA-Gen (customizable via AVA_GEN_OPENAI_MODEL)
DEFAULT_MODEL = settings.openai_model


# -------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------


def _extract_json_from_text(text: str) -> str:
    """
    Normalize model text output into a raw JSON string.

    Handles common patterns like Markdown ```json fenced blocks and
    extra prose around the JSON object by extracting the first JSON-like
    block from the text.
    """
    text = text.strip()

    # Strip Markdown code fences if present.
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # Best-effort extraction of the first {...} block.
    if "{" in text and "}" in text:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1].strip()

    return text


# -------------------------------------------------------------------
# Public function
# -------------------------------------------------------------------

def send_request_to_gpt(
    prompt: str,
    *,
    structured_output: Union[bool, Type[BaseModel]] = False,
    model: Optional[str] = None,
) -> Any:
    """
    Send a prompt to the OpenAI API and return the response.

    Parameters
    ----------
    prompt : str
        The user prompt (full instruction text).
    structured_output : bool | Type[BaseModel]
        - False (default): return plain text string.
        - True: expect a JSON object and return raw text (caller parses).
        - Pydantic BaseModel subclass: ask the model to fill that schema and
          return an instance of that model.
    model : str, optional
        Override the default model name.

    Returns
    -------
    Any
        - If structured_output is False or True: returns `str` (model text).
        - If structured_output is a BaseModel subclass: returns a BaseModel instance.

    Raises
    ------
    OpenAIError
        If the API call fails.
    RuntimeError
        If response is missing or malformed.
    """
    model_name = model or DEFAULT_MODEL

    # Basic chat-style call with a single user message
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
    except OpenAIError as e:
        # Re-raise for now; you can log or wrap this later
        raise e

    if not completion.choices:
        raise RuntimeError("Empty response from OpenAI API.")

    text = completion.choices[0].message.content or ""

    # Case 1: caller just wants raw text
    if structured_output is False:
        return text

    # Case 2: caller wants JSON but will handle parsing
    if structured_output is True:
        return text

    # Case 3: caller passed a Pydantic model type for structured output
    if isinstance(structured_output, type) and issubclass(structured_output, BaseModel):
        # We expect the model to output JSON; normalize and try to parse it
        cleaned_text = _extract_json_from_text(text)
        try:
            data = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON from model output: {e}\nRaw text: {text}")

        return structured_output(**data)

    # Fallback: unknown structured_output type
    return text
