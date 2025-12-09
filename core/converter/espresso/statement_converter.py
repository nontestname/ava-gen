"""
core.converter.espresso.statement_converter

Language-agnostic Espresso statement utilities.

Pipeline assumption
-------------------
Java/Kotlin test files are first processed by language-specific extractors:

  - core.converter.espresso.java_extractor.extract_espresso_calls_from_java_source(...)
  - core.converter.espresso.kotlin_extractor.extract_espresso_calls_from_kotlin_source(...)

Those extractors return **normalized Espresso calls** as single-line strings in
a Java-style format, e.g.:

    'onView(...).perform(...);'

This module then:

  1. Validates Espresso statements against SUPPORTED_MATCHERS / SUPPORTED_ACTIONS.
  2. Validates non-Espresso statements (e.g., pressBack, closeSoftKeyboard).
  3. Converts Espresso statements into internal VA-style statements, using
     `findNode(...)` plus higher-level helper actions.

Note on `isRoot()`
------------------
`onView(isRoot()).perform(swipeLeft());` and
`onView(isRoot()).perform(swipeRight());` are handled via the **generic**
parsing logic, not as hard-coded string matches. Make sure `"isRoot"` is
included in SUPPORTED_MATCHERS so validation passes.
"""

import re
from typing import List


from core.converter.espresso.supported_espresso_apis import (
    IGNORED_MATCHERS,
    SUPPORTED_MATCHERS,
    SUPPORTED_ACTIONS,
    SUPPORTED_NON_ESPRESSO,
)
from exceptions.exceptions import ( 
    UnsupportedMatcherException, 
    UnsupportedActionException, 
    ConversionFormatException,
)

# ---------------------------------------------------------------------------
# Nested string matcher helpers (Hamcrest-style) used inside view matchers
# ---------------------------------------------------------------------------
#
# Espresso view matchers such as withText(...) and withContentDescription(...)
# can wrap Hamcrest-style string helpers, for example:
#
#     withText(equalsIgnoreCase("Save"))
#     withText(containsStringIgnoringCase("Blueberry"))
#
# Our Android client parses these helper calls on the device side
# (NodeQuery.parseList + StringMatcher), so here we treat them as
# "nested string helpers" rather than top-level view matchers. They
# should therefore NOT cause validate_espresso_statement(...) to fail.
#
# Any names listed here will be ignored by the matcher validation
# step below, even though they still appear in the regex that extracts
# function names from the onView(...) part.
# Mapping from helper function name to the normalized "mode" string
# that we will store in the action plan. This lets us keep the set of
# supported helpers in STRING_HELPER_MATCHERS and centralize any
# normalization (for example, equals(...) -> equalsIgnoreCase).
HELPER_MODE_NORMALIZATION = {
    "equalsIgnoreCase": "equalsIgnoreCase",
    "equals": "equals",  # normalize to case-insensitive equality
    "containsIgnoreCase": "containsIgnoreCase",
    "containsStringIgnoringCase": "containsIgnoreCase",  # same as containsIgnoreCase
    "contains": "contains",
    "startsWithIgnoreCase": "startsWithIgnoreCase",
    "endsWithIgnoreCase": "endsWithIgnoreCase",
}

STRING_HELPER_MATCHERS = {
    "equalsIgnoreCase",
    "equals",
    "containsIgnoreCase",
    "containsStringIgnoringCase",
    "contains",
    "startsWithIgnoreCase",
    "endsWithIgnoreCase",
}

# ---------------------------------------------------------------------------
# String expression helpers for nested matchers like withText(equalsIgnoreCase("Save"))
# ---------------------------------------------------------------------------
#
# These helpers are intended for use by higher-level converters (e.g.,
# the action‑plan builder) that need to interpret the *argument* passed
# into withText(...), withId(...), etc. The goal is to support both:
#
#   withText("Save")
#   withText(equalsIgnoreCase("Save"))
#   withText(containsIgnoreCase("Save"))
#   withText(containsStringIgnoringCase("EditText"))
#
# and normalize them into a (value, mode) pair that can be used to build
# StepMatcher objects and NodeQuery DSL strings consistently.
#
# NOTE: This module currently does not build StepMatcher objects itself;
# the helper is provided here so other modules can import and reuse the
# same parsing logic.
TEXT_CALL_RE = re.compile(r'withText\(\s*(?P<arg>[^)]+)\s*\)')

def _parse_string_expr(expr: str):
    """
    Parse a Java-style string expression used inside withText(...) / withId(...).

    Examples
    --------
    The following inputs are all accepted:

      "Save"                            -> ("Save", "containsIgnoreCase")
      equalsIgnoreCase("Save")         -> ("Save", "equalsIgnoreCase")
      containsIgnoreCase("Save")       -> ("Save", "containsIgnoreCase")
      containsStringIgnoringCase("X")  -> ("X",   "containsIgnoreCase")

    The returned tuple is (value, mode), where `mode` is a textual
    representation that can be stored in the action plan JSON and later
    mapped to a concrete StringMatcher on the Android client.
    """
    if expr is None:
        return None, "containsIgnoreCase"

    expr = expr.strip()

    # Generic helper pattern: helperName("value")
    #
    # This will match things like:
    #   equalsIgnoreCase("Save")
    #   containsIgnoreCase("Save")
    #   containsStringIgnoringCase("EditText")
    #   startsWithIgnoreCase("X")
    #   endsWithIgnoreCase("Y")
    #
    # We then look up helperName in STRING_HELPER_MATCHERS and normalize
    # it via HELPER_MODE_NORMALIZATION.
    m = re.match(r'(\w+)\(\s*"([^"]+)"\s*\)$', expr)
    if m:
        helper_name = m.group(1)
        value = m.group(2)

        if helper_name in STRING_HELPER_MATCHERS:
            mode = HELPER_MODE_NORMALIZATION.get(helper_name, "containsIgnoreCase")
            return value, mode

    # bare literal: "Save"
    m = re.match(r'"([^"]+)"', expr)
    if m:
        # Default mode for plain literals – here we choose containsIgnoreCase
        # so that "Save" will match "save", "SAVE", etc.
        return m.group(1), "containsIgnoreCase"

    # Fallback – return the raw expr as value and a conservative default mode.
    return expr, "containsIgnoreCase"


# ---------------------------------------------------------------------------
# Helpers for allOf(...) flattening and whitespace normalization
# ---------------------------------------------------------------------------

def _flatten_allOf_once(expr: str) -> str:
    """
    Replace a single occurrence of allOf(A, B, ...) with its arguments: A, B, ...

    This version is robust to nested parentheses inside the arguments.
    """
    pattern = "allOf("
    i = 0
    out: List[str] = []

    while i < len(expr):
        j = expr.find(pattern, i)
        if j == -1:
            out.append(expr[i:])
            break

        # text before allOf(
        out.append(expr[i:j])

        # find matching ')' for this allOf(
        k = j + len(pattern)
        depth = 1
        while k < len(expr) and depth > 0:
            ch = expr[k]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            k += 1

        inner = expr[j + len(pattern) : k - 1]  # inside allOf(...)
        out.append(inner)
        i = k  # continue after ')'

    return "".join(out)


def _flatten_allOf(expr: str) -> str:
    """
    Repeatedly flatten allOf(...) until none remain.
    """
    while "allOf(" in expr:
        expr = _flatten_allOf_once(expr)
    return expr


def _normalize_whitespace(expr: str) -> str:
    """
    Normalize whitespace to avoid ugly double spaces or space-before-paren
    issues, while keeping the expression semantics intact.
    """
    # Collapse multi-space sequences
    expr = re.sub(r"\s+", " ", expr)

    # Trim around parentheses and commas
    expr = re.sub(r"\(\s+", "(", expr)
    expr = re.sub(r"\s+\)", ")", expr)
    expr = re.sub(r",\s+", ", ", expr)

    # Remove redundant spaces before semicolons
    expr = re.sub(r"\s+;", ";", expr)

    # Final trim
    return expr.strip()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_espresso_statement(espresso_statement: str) -> bool:
    """
    Validate a single normalized Espresso statement.

    Checks:
      - All matcher function names in the `onView(...)` portion are supported.
      - All action function names in the `.perform(...)` portion are supported.

    Expected input format (after normalization):

        'onView(...).perform(...);'

    Parameters
    ----------
    espresso_statement : str
        Normalized Espresso statement as a string.

    Raises
    ------
    UnsupportedMatcherException
        If one or more matchers are not in SUPPORTED_MATCHERS.
    UnsupportedActionException
        If one or more actions are not in SUPPORTED_ACTIONS.
    ValueError
        If the statement does not match the expected Espresso format.

    Returns
    -------
    bool
        True if the statement is valid; otherwise an exception is raised.
    """
    stmt = espresso_statement.strip()

    # Split into `onView(...)` and `.perform(...)` parts.
    match = re.match(r"(.+?)\.perform\((.+?)\);", stmt)
    if not match:
        raise ValueError(
            f"Invalid Espresso format. Expected 'onView(...).perform(...);' but got: {espresso_statement}"
        )

    on_view_part, perform_part = match.groups()

    # Extract matcher function names from onView(...)
    matchers: List[str] = re.findall(r"(\w+)\(", on_view_part)

    # The regex above will also pick up nested string helper calls used
    # *inside* matchers, e.g.:
    #
    #     onView(allOf(
    #         withId(android.R.id.button1),
    #         withText(equalsIgnoreCase("Save"))
    #     )).perform(click());
    #
    # produces the function-name list:
    #     ["onView", "allOf", "withId", "withText", "equalsIgnoreCase"]
    #
    # The outer view matchers (onView, allOf, withId, withText, ...) are
    # validated against SUPPORTED_MATCHERS. The nested helpers such as
    # equalsIgnoreCase(...) are handled later by the Android-side DSL
    # (NodeQuery + StringMatcher) and must NOT cause validation failure.
    unsupported_matchers = [
        m for m in matchers
        if m not in SUPPORTED_MATCHERS and m not in STRING_HELPER_MATCHERS
    ]
    if unsupported_matchers:
        raise UnsupportedMatcherException(unsupported_matchers)

    # Extract action function names from perform(...)
    actions: List[str] = re.findall(r"(\w+)\(", perform_part)
    unsupported_actions = [a for a in actions if a not in SUPPORTED_ACTIONS]
    if unsupported_actions:
        raise UnsupportedActionException(unsupported_actions)

    return True


def validate_non_espresso_statement(statement: str) -> bool:
    """
    Validate a non-Espresso statement (e.g., navigation / keyboard helpers).

    Intended for statements that do *not* start with onView/onData/etc. but are
    still part of the test flow, for example:

        'pressBack();'
        'closeSoftKeyboard();'
        'Thread.sleep(5000);'

    Logic:
      - Return True if the stripped statement is in SUPPORTED_NON_ESPRESSO.
      - Return True if it matches `Thread.sleep(<integer>);`.
      - Otherwise, return False.

    Parameters
    ----------
    statement : str
        Non-Espresso statement.

    Returns
    -------
    bool
        True if the non-Espresso statement is supported, False otherwise.
    """
    stmt = statement.strip()

    # Direct membership check (variants with/without semicolon can be listed).
    if stmt in SUPPORTED_NON_ESPRESSO:
        return True

    # Allow generic `Thread.sleep(<number>);` calls.
    if re.fullmatch(r"\s*Thread\.sleep\(\d+\);\s*", stmt):
        return True

    return False


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

def convert_espresso_to_findNode(espresso_statement: str) -> str:
    """
    Convert a normalized Espresso UI statement into a VA-style internal statement.

    Assumes input format:

        'onView(...).perform(...);'

    Transformations
    ---------------
    - Special handling for root-level swipes:
        onView(isRoot()).perform(swipeLeft());  ->  performSwipeLeft();
        onView(isRoot()).perform(swipeRight()); ->  performSwipeRight();

    - Removes `isDisplayed()` from matcher chains.
    - Converts view IDs:
        withId(R.id.someId)           -> withId("someId")
        withId(android.R.id.someId)   -> withId("someId")

    - Flattens:
        allOf(A, B)                   -> A, B

    - Rewrites `onView(...)` to `findNode(...)`:
        onView(matchers...)           -> findNode(matchers...)

    - Maps actions:
        .perform(typeText("abc"))     ->
            performInput(findNode(...), "abc");
        .perform(replaceText("abc"))  ->
            performInput(findNode(...), "abc");
        .perform(click())             ->
            performClick(findNode(...));
        .perform(scrollTo())          ->
            performScrollDown();
        .perform(swipeLeft())         ->
            performSwipeLeftOnNode(findNode(...));
        .perform(swipeRight())        ->
            performSwipeRightOnNode(findNode(...));

    Any other patterns fall back to:

        '<converted_on_view>.perform(<original_perform_part>);'

    Parameters
    ----------
    espresso_statement : str
        Normalized Espresso statement string.

    Returns
    -------
    str
        Converted VA-style statement.
    """
    stmt = espresso_statement.strip()

    # Split into matcher part and action part
    match = re.match(r"(.+?)\.perform\((.+?)\);", stmt)
    if not match:
        # Non-fatal: return explicit error string so callers can log/inspect.
        return f"Error: Invalid Espresso input format: {espresso_statement}"

    on_view_part, perform_part = match.groups()

    # Special handling for root-level statements using isRoot()
    is_root_statement = "isRoot()" in on_view_part

    # Remove ignored matcher such as 'isDisplayed()' occurrences from matcher chain
    ignored_regex = "|".join(IGNORED_MATCHERS)
    on_view_part = re.sub(rf",?\s*({ignored_regex})\(\)", "", on_view_part)

    # ------------------------------------------------------------------
    # Remove all `ViewMatchers.` prefixes to produce cleaner VA matchers
    # Example:
    #   ViewMatchers.withId(R.id.foo) → withId("foo")
    #   ViewMatchers.withContentDescription("X") → withContentDescription("X")
    # Espresso allows both withId(...) and ViewMatchers.withId(...).
    # Our VA DSL only wants the raw matcher function.
    # ------------------------------------------------------------------
    on_view_part = on_view_part.replace("ViewMatchers.", "")
    
    # Convert withId(R.id.X) -> withId("X")
    on_view_part = re.sub(r"withId\(R\.id\.(\w+)\)", r'withId("\1")', on_view_part)

    # Convert withId(android.R.id.X) -> withId("X")
    on_view_part = re.sub(r"withId\(android\.R\.id\.(\w+)\)", r'withId("\1")', on_view_part)

    # Flatten allOf(A, B, ...) -> A, B, ...
    on_view_part = _flatten_allOf(on_view_part)

    # Replace outermost onView(...) with findNode(...)
    on_view_part = re.sub(r"onView\((.*?)\)", r"findNode(\1)", on_view_part)

    # Normalize matcher expression whitespace
    on_view_part = _normalize_whitespace(on_view_part)

    # === Action mapping ===

    # Text input (typeText / replaceText)
    text_match = re.search(r"(?:replaceText|typeText)\(([^)]+)\)", perform_part)
    if text_match:
        text_value = text_match.group(1)
        # Do NOT add quotes here; variables / function calls should remain valid.
        converted = f"performInput({on_view_part}, {text_value});"
        return _normalize_whitespace(converted)

    # Scroll actions
    # For now we normalize any onView(...).perform(scrollTo()) to a simple
    # screen-level scroll down, regardless of the specific matcher. In most
    # tests this pattern is just used to bring a widget into view; the real
    # click or input is a separate statement.
    if perform_part.strip() == "scrollTo()":
        converted = "performScrollDown();"
        return _normalize_whitespace(converted)

    # Root-level actions (isRoot())
    if is_root_statement:
        action = perform_part.strip()
        if action == "swipeLeft()":
            return "performSwipeLeft();"
        if action == "swipeRight()":
            return "performSwipeRight();"
        # Fallback for other root-level actions (if any in the future)
        converted = f"performOnRoot({action});"
        return _normalize_whitespace(converted)

    # Node-level click
    if perform_part.strip() == "click()":
        converted = f"performClick({on_view_part});"
        return _normalize_whitespace(converted)

    # Node-level swipes
    if perform_part.strip() == "swipeLeft()":
        converted = f"performSwipeLeftOnNode({on_view_part});"
        return _normalize_whitespace(converted)

    if perform_part.strip() == "swipeRight()":
        converted = f"performSwipeRightOnNode({on_view_part});"
        return _normalize_whitespace(converted)

    # Fallback: keep structure but with converted findNode(...)
    converted = f"{on_view_part}.perform({perform_part});"
    return _normalize_whitespace(converted)



def convert_espresso_statement(espresso_statement: str) -> str:
    """
    Convenience entry point: validate, then convert an Espresso statement.

    Steps:
      1. validate_espresso_statement(...)
      2. convert_espresso_to_findNode(...)

    Parameters
    ----------
    espresso_statement : str
        Normalized Espresso statement string.

    Returns
    -------
    str
        Converted VA-style statement.

    Raises
    ------
    UnsupportedMatcherException
        If one or more matchers are not supported.
    UnsupportedActionException
        If one or more actions are not supported.
    ValueError
        If the statement format is invalid.
    """
    validate_espresso_statement(espresso_statement)
    return convert_espresso_to_findNode(espresso_statement)


if __name__ == "__main__":
    # Full test suite including all user-provided examples.

    test_examples = [
        'onView(withId(R.id.button)).perform(click());',  # Supported
        'onView(allOf(withId(R.id.text), withText(heelo))).perform(swipeLeft());',  # Supported
        'onView(withId(R.id.button)).perform(doubleClick());',  # Unsupported action
        'onView(withRandomMatcher(R.id.button)).perform(click());',  # Unsupported matcher
        'onView(isRoot()).perform(swipeLeft());',  # Supported special case → root-level swipe
        'onView(isRoot()).perform(swipeRight());',  # Supported special case
        'onView(allOf(withText("Press"), unsupportedMatcher())).perform(click());',  # Unsupported matcher
        'onView(allOf(withId(R.id.text_deck_name), withText(containsStringIgnoringCase("Keto Fruit")))).perform(click());',  # containsStringIgnoringCase is allowed
        'onView(allOf(withId(R.id.button_edit), withParent(withParent(hasDescendant(withText(containsStringIgnoringCase("Blueberry"))))))).perform(click());',
        'onView(allOf(withContentDescription("Open drawer"), isDisplayed())).perform(click());',
        'onView(allOf(withId(R.id.category_name), isDisplayed())).perform(replaceText(param3));'
    ]

    print("\n========== Espresso Validation & Conversion Tests ==========\n")

    for ex in test_examples:
        print(f"\n[Input] {ex}")

        try:
            valid = validate_espresso_statement(ex)
            print("  ✔ validate_espresso_statement ->", valid)
        except Exception as e:
            print("  ✘ Validation failed:", repr(e))
            continue

        converted = convert_espresso_to_findNode(ex)
        print("  → convert_espresso_to_findNode ->", converted)

    # Test non-Espresso helpers
    print("\n========== Non-Espresso Tests ==========\n")
    non_espresso_examples = [
        "pressBack();",
        "closeSoftKeyboard();",
        "Thread.sleep(5000);",
        "Thread.sleep(1500);",
        "someUnknownHelper();",
    ]
    for s in non_espresso_examples:
        print(f"[Non-Espresso] '{s}' -> {validate_non_espresso_statement(s)}")
