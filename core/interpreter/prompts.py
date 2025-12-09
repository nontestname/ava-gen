# Prompt templates used by the VA code interpreter.


PROMPT_EXTRACT_PARAMETERS = """
Please read the following Java method and output a JSON object:

{
  "parameters": ["param1", "param2", ...]
}

containing the names of exactly all the parameters of the OUTERMOST method
in the code below. Do not include local variables, only method parameters.

Code:
{code}
"""


PROMPT_PARAMETER_DESCRIPTION = """
In the following Java method code (used for UI testing of a mobile app),
please analyze the parameter '{param}' and answer the following:

1. Write a simple sentence (<= 10 words) to describe what '{param}' represents
   in the code, such as 'Name of the city', 'Temperature unit'. Use the logic
   and especially the literals in the code.
2. Summarize that description and generate a short name (2-3 words) for this
   parameter, such as 'CityName', 'TemperatureUnit', 'FoodName'.
3. Determine if '{param}' has pre-defined values. If yes, set 'is_pre_defined'
   to true. Otherwise, set it to false.
4. If '{param}' has pre-defined values, set 'possible_values' to a list
   containing all possible pre-defined values. Otherwise, come up with at least
   {n} example values for this parameter in the same format.

Return a JSON object matching the following Pydantic model:

SlotInformation:
  - description: str
  - slot_name: str
  - is_pre_defined: bool
  - possible_values: List[str]

Code:
{code}
"""


PROMPT_INTENT_FOR_VALUES = """
In the following Java method (used in UI testing of a mobile app),
assume that:

{items}

Please describe the overall intent or purpose of this method in LESS than
10 words. Use a single short sentence.

Code:
{code}
"""


PROMPT_INTENT_COMBINE = """
We have multiple example intents for the same Java method, each produced
using different concrete parameter values.

Parameters: {params}

Example intents:
{intents}

Please summarize these into ONE general intent description that does NOT
mention specific example values, but instead generalizes appropriately.
Keep your final answer under 10 words.

Base code:
{code}
"""


PROMPT_INTENT_NAME = """
Read the following Java method (used as a VA skill) and give a concise
2-3 word name that captures its intent. Do NOT include the word 'Test'
or low-level UI implementation details (like 'Button Click').

Only output the name phrase.

Code:
{code}
"""


# PROMPT_DIRECT_INTENT_DETAIL

PROMPT_DIRECT_INTENT_DETAIL = """
You are interpreting a VA Java method for a mobile app.

App introduction:
{app_intro}

Read the following VA Java method and summarize its purpose with details
in fewer than 20 words. Focus on the high-level user intent and ignore
UI-level details such as clicks, swipes, or findNode operations.

Code:
{code}
"""


# PROMPT_DIRECT_INTENT_SHORT

PROMPT_DIRECT_INTENT_SHORT = """
You are interpreting a VA Java method for a mobile app.

App introduction:
{app_intro}

Read the following VA Java method and summarize its purpose in fewer
than 5 words. Focus on the high-level user intent and ignore UI-level
details such as clicks, swipes, or findNode operations.

Code:
{code}
"""