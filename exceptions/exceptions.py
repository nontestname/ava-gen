"""
Custom exceptions for AVA-Gen converters and interpreters.

These exceptions are intentionally simple and descriptive.
They are used across:

  - core/converter/espresso/
  - core/interpreter/
  - runtime/server/

Placing them at the project root (ava-gen/exceptions/) avoids
circular imports and keeps exception types consistent across modules.
"""


class UnsupportedMatcherException(Exception):
    """
    Raised when an Espresso matcher (e.g., withId, withText, allOf, etc.)
    is not found in the SUPPORTED_MATCHERS set.

    The exception contains the list of unsupported matcher names.
    """

    def __init__(self, unsupported_matchers):
        self.unsupported_matchers = unsupported_matchers
        msg = (
            "Unsupported Espresso matcher(s): "
            + ", ".join(str(m) for m in unsupported_matchers)
        )
        super().__init__(msg)


class UnsupportedActionException(Exception):
    """
    Raised when an Espresso action (e.g., click, swipeLeft, typeText)
    is not found in the SUPPORTED_ACTIONS set.

    The exception contains the list of unsupported action names.
    """

    def __init__(self, unsupported_actions):
        self.unsupported_actions = unsupported_actions
        msg = (
            "Unsupported Espresso action(s): "
            + ", ".join(str(a) for a in unsupported_actions)
        )
        super().__init__(msg)


class ConversionFormatException(Exception):
    """
    Raised when an Espresso statement cannot be parsed into an expected format.

    Example:
        'onView(...).perform(...);'  ← expected
        invalid input                ← raises this exception
    """

    def __init__(self, statement, details=None):
        self.statement = statement
        self.details = details or "Invalid Espresso format."
        msg = f"Conversion error for statement: {statement}\nDetails: {self.details}"
        super().__init__(msg)