from typing import List, Dict
from pydantic import BaseModel


class SlotInformation(BaseModel):
    """
    Information about a single parameter (slot) inferred from the VA code.
    This is used internally to help GPT reason about the function intent.
    """
    description: str
    slot_name: str
    is_pre_defined: bool
    possible_values: List[str]


class SkillSchema(BaseModel):
    """
    Final skill schema exposed to the VA runtime.

    We keep two descriptions:
      - description_short: short label (<=5 words)
      - description_detail: detailed description (<=20 words)
    """
    description_short: str
    description_detail: str

    def to_dict(self) -> dict:
        return {
            "description-short": self.description_short,
            "description-detail": self.description_detail,
        }
