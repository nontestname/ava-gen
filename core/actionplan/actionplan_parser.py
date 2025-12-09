"""
core.actionplan.actionplan_parser

Parse generated VA Java methods into structured ActionPlans.

Assumes VA methods look like:

public void updateOverviewDisplayEvents() {
    performClick(findNode(withId("overviewFragment"), withContentDescription("Overview")));
    performClick(findNode(withContentDescription("More options")));
    performInput(findNode(withId("note_input")), "school");
    pressBack();
    Thread.sleep(1500);
}

We convert them into an ActionPlan with a list of ActionSteps.
"""

from __future__ import annotations

import os
import re
from typing import List, Dict, Optional


import json

# Reuse the Espresso-side string expression parser so that arguments like
# equalsIgnoreCase("Save") and containsIgnoreCase("EditText") are
# interpreted consistently when we build ActionPlan matchers.
from core.converter.espresso.statement_converter import _parse_string_expr

from pydantic import BaseModel


# ============================================================
# Data models
# ============================================================

class Matcher(BaseModel):
    """A simple matcher extracted from findNode(...).

    Example matcher types:
      - id
      - text
      - contentDescription
      - className

    The Android client expects a `mode` field that describes how to
    compare the string (equalsIgnoreCase, containsIgnoreCase, regex, ...).
    For now we always default to an *exact* match (case-insensitive)
    by emitting `mode="equalsIgnoreCase"`.

    If we can't classify, we can still store the raw expr in the
    ActionStep's `node_query` field.
    """

    # Which field to match on (text, contentDescription, id, className, ...)
    type: str
    # Value to match against
    value: str
    # Optional match mode, used by the Android client to construct a
    # StringMatcher.  We default to "equalsIgnoreCase".
    mode: Optional[str] = "equalsIgnoreCase"


class ActionStep(BaseModel):
    """
    One atomic step in an ActionPlan.

    The 'node_query' field holds the full NodeQuery expression inside findNode(...)
    (including nested constructs like withChild(...), withParent(...), etc.),
    while 'matchers' are just flattened hints extracted from it.
    """
    action: str                           # Supported actions: click, input, swipeLeft, swipeRight, swipeLeftOnNode, swipeRightOnNode, scrollDown, scrollUp, swipeLeft50Percent, swipeRight50Percent, pressBack, closeSoftKeyboard, sleep
    matchers: List[Matcher] = []          # target matchers if any
    text: Optional[str] = None            # for input actions
    millis: Optional[int] = None          # for sleep
    node_query: Optional[str] = None      # full NodeQuery expression inside findNode(...)


class ActionPlan(BaseModel):
    """
    Plan for one VA method.
    """
    method_name: str
    steps: List[ActionStep]


# ============================================================
# Low-level parsing helpers
# ============================================================

_METHOD_NAME_RE = re.compile(r"public\s+void\s+(\w+)\s*\(")


def extract_method_name(va_code: str) -> str:
    """
    Extract method name from a VA Java method.
    """
    m = _METHOD_NAME_RE.search(va_code)
    return m.group(1) if m else "UnknownMethod"


def extract_method_body_lines(va_code: str) -> List[str]:
    """
    Extract just the body lines inside the outermost method braces.

    Assumes exactly one public void method per file.
    """
    lines = va_code.splitlines()
    body_lines: List[str] = []

    in_method = False
    brace_count = 0

    for line in lines:
        if not in_method:
            if "public void" in line:
                in_method = True
                brace_count += line.count("{") - line.count("}")
                continue
        else:
            brace_count += line.count("{") - line.count("}")
            stripped = line.strip()

            if brace_count <= 0:
                break

            if stripped:
                body_lines.append(line)

    return body_lines


def split_args_preserving_parens(arg_str: str) -> List[str]:
    """
    Split a comma-separated argument list into individual arguments,
    but ONLY on commas that are not nested inside parentheses or string
    literals.

    This is required for patterns like:

        performInput(
            findNode(withId("AmountEditText"),
                     withParent(withId("Amount"), hasDescendant(withId("TaType")))),
            "20"
        );

    A naive `split(",")` would incorrectly split inside the withParent(...)
    call. Instead, we track parentheses depth and basic string state and
    only treat a comma as a delimiter when:

        - paren_depth == 0  (we are not inside any (...))
        - we are not currently inside a quoted string literal.

    NOTE: This is a minimal, purpose-built splitter for our generated VA
    code. It assumes double-quoted string literals and does not attempt
    to fully parse arbitrary Java.
    """
    parts: List[str] = []
    buf: List[str] = []
    depth = 0
    in_string = False
    escape = False

    for ch in arg_str:
        if in_string:
            buf.append(ch)
            if escape:
                # Previous char was backslash; current char is escaped.
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            buf.append(ch)
            continue

        if ch == '(':
            depth += 1
            buf.append(ch)
            continue
        if ch == ')':
            depth -= 1
            buf.append(ch)
            continue

        if ch == ',' and depth == 0 and not in_string:
            parts.append("".join(buf).strip())
            buf = []
            continue

        buf.append(ch)

    if buf:
        parts.append("".join(buf).strip())

    return parts


def parse_findnode_matchers(findnode_call: str) -> (List[Matcher], str):
    """
    Parse findNode(...) call into a list of simple Matcher objects and return
    the full NodeQuery expression (inner contents of findNode(...)) as node_query.

    Example input:
        findNode(withId("overviewFragment"), withContentDescription("Overview"))

    We return:
        [Matcher(type="id", value="overviewFragment"),
         Matcher(type="contentDescription", value="Overview")]
    plus the full inside part as node_query string.
    """
    # Strip `findNode(` and trailing `);` or `)`
    inner = findnode_call.strip()
    inner = re.sub(r"^findNode\s*\(", "", inner)
    inner = re.sub(r"\)\s*;?\s*$", "", inner).strip()

    node_query = inner

    # If we detect structural NodeQuery constructs (withParent/withChild/hasDescendant),
    # we should NOT emit flattened matchers. In these cases, the Android client will
    # rely entirely on the full node_query DSL, and matchers are left empty.
    structural_pattern = r"\b(withParent|withChild|hasDescendant)\s*\("
    has_structural = re.search(structural_pattern, inner) is not None

    matchers: List[Matcher] = []

    # Simple patterns for direct matchers. These are only emitted when the expression
    # does NOT contain structural nesting; otherwise we leave matchers empty and let
    # the client use node_query as the single source of truth.
    #
    # We now support both plain literals and nested string helpers in the
    # argument position, for example:
    #
    #   findNode(withId("button1"), withText(equalsIgnoreCase("Save")))
    #   findNode(withClassName(containsStringIgnoringCase("EditText")))
    #
    # The inner argument (e.g., "Save" or equalsIgnoreCase("Save")) is passed
    # through `_parse_string_expr(...)`, which returns a pair:
    #
    #   ("Save", "equalsIgnoreCase")
    #
    # This allows the ActionPlan `matchers` array to carry both the value and
    # the match mode, so the Android client can reconstruct the correct
    # StringMatcher.
    if not has_structural:
        # Break the inner expression into top-level arguments, respecting
        # nested parentheses and string literals. For example:
        #
        #   withId("button1"), withText(equalsIgnoreCase("Save"))
        #
        # becomes:
        #   ["withId(\"button1\")", "withText(equalsIgnoreCase(\"Save\"))"]
        arg_parts = split_args_preserving_parens(inner)

        for part in arg_parts:
            p = part.strip()
            if not p:
                continue

            # withId(...)
            if p.startswith("withId(") and p.endswith(")"):
                inner_arg = p[len("withId("):-1].strip()
                value, mode = _parse_string_expr(inner_arg)
                matchers.append(Matcher(type="id", value=value, mode=mode))
                continue

            # withText(...)
            if p.startswith("withText(") and p.endswith(")"):
                inner_arg = p[len("withText("):-1].strip()
                value, mode = _parse_string_expr(inner_arg)
                matchers.append(Matcher(type="text", value=value, mode=mode))
                continue

            # withContentDescription(...)
            if p.startswith("withContentDescription(") and p.endswith(")"):
                inner_arg = p[len("withContentDescription("):-1].strip()
                value, mode = _parse_string_expr(inner_arg)
                matchers.append(Matcher(type="contentDescription", value=value, mode=mode))
                continue

            # withClassName(...)
            if p.startswith("withClassName(") and p.endswith(")"):
                inner_arg = p[len("withClassName("):-1].strip()
                value, mode = _parse_string_expr(inner_arg)
                matchers.append(Matcher(type="className", value=value, mode=mode))
                continue

            # If the part is not a simple withX(...) matcher (for example, it is
            # a structural construct like withParent(...) or a complex NodeQuery
            # expression), we deliberately ignore it here and rely solely on the
            # `node_query` string for the Android client to interpret.

    return matchers, node_query


# ============================================================
# Line → ActionStep parsing
# ============================================================

def parse_action_line(line: str) -> Optional[ActionStep]:
    """
    Parse one VA line into an ActionStep, if possible.

    Handles patterns like:
      performClick(findNode(...));
      performInput(findNode(...), "text");
      performSwipeLeftOnNode(findNode(...));
      performSwipeRightOnNode(findNode(...));
      performSwipeLeft();
      performSwipeRight();
      pressBack();
      closeSoftKeyboard();
      Thread.sleep(1500);
    """
    stripped = line.strip().rstrip(";").strip()

    # Press back
    if stripped == "pressBack()":
        return ActionStep(action="pressBack")

    # Close keyboard
    if stripped == "closeSoftKeyboard()":
        return ActionStep(action="closeSoftKeyboard")

    # Scroll down
    # We support both the bare helper call:
    #   scrollDown();
    # and the ActionPerformer-style helper:
    #   performScrollDown();
    if stripped in ("scrollDown()", "performScrollDown()"):
        return ActionStep(action="scrollDown")

    # Scroll up
    # Similarly, handle both:
    #   scrollUp();
    #   performScrollUp();
    if stripped in ("scrollUp()", "performScrollUp()"):
        return ActionStep(action="scrollUp")

    # Swipe left 50 percent
    if stripped == "swipeLeft50Percent()":
        return ActionStep(action="swipeLeft50Percent")

    # Swipe right 50 percent
    if stripped == "swipeRight50Percent()":
        return ActionStep(action="swipeRight50Percent")

    # Sleep
    m_sleep = re.match(r"Thread\.sleep\((\d+)\)", stripped)
    if m_sleep:
        millis = int(m_sleep.group(1))
        return ActionStep(action="sleep", millis=millis)

    # performSwipeLeft(); / performSwipeRight();
    if stripped == "performSwipeLeft()":
        return ActionStep(action="swipeLeft")
    if stripped == "performSwipeRight()":
        return ActionStep(action="swipeRight")

    # With findNode target
    # performClick(...)
    m_click = re.match(r"performClick\s*\((.+)\)", stripped)
    if m_click:
        arg = m_click.group(1).strip()
        if arg.startswith("findNode("):
            matchers, node_query = parse_findnode_matchers(arg)
            return ActionStep(action="click", matchers=matchers, node_query=node_query)
        else:
            return ActionStep(action="click")

    # performInput(findNode(...), value)
    m_input = re.match(r"performInput\s*\((.+)\)", stripped)
    if m_input:
        args = m_input.group(1).strip()

        # Use a parenthesis- and string-aware splitter so that nested NodeQuery
        # expressions do not break argument parsing.
        #
        # Example:
        #   performInput(
        #       findNode(withId("AmountEditText"),
        #                withParent(withId("Amount"), hasDescendant(withId("TaType")))),
        #       "20"
        #   );
        #
        # This should yield:
        #   target_expr = 'findNode(withId("AmountEditText"), withParent(...))'
        #   text_expr   = '"20"'
        parts = split_args_preserving_parens(args)

        target_expr = parts[0] if parts else ""
        text_expr = parts[1] if len(parts) > 1 else ""

        text_value = text_expr

        # Strip quotes around text literal if present so that:
        #   text_expr = "\"20\""  →  text_value = "20"
        m_text_lit = re.match(r'"(.*)"', text_expr)
        if m_text_lit:
            text_value = m_text_lit.group(1)

        if target_expr.startswith("findNode("):
            matchers, node_query = parse_findnode_matchers(target_expr)
            return ActionStep(
                action="input",
                matchers=matchers,
                text=text_value,
                node_query=node_query,
            )
        else:
            # Input without a findNode; we still keep the text literal.
            return ActionStep(
                action="input",
                text=text_value,
            )

    # performSwipeLeftOnNode(findNode(...))
    m_swipe_left_node = re.match(r"performSwipeLeftOnNode\s*\((.+)\)", stripped)
    if m_swipe_left_node:
        arg = m_swipe_left_node.group(1).strip()
        if arg.startswith("findNode("):
            matchers, node_query = parse_findnode_matchers(arg)
            return ActionStep(action="swipeLeftOnNode", matchers=matchers, node_query=node_query)
        else:
            return ActionStep(action="swipeLeftOnNode")

    # performSwipeRightOnNode(findNode(...))
    m_swipe_right_node = re.match(r"performSwipeRightOnNode\s*\((.+)\)", stripped)
    if m_swipe_right_node:
        arg = m_swipe_right_node.group(1).strip()
        if arg.startswith("findNode("):
            matchers, node_query = parse_findnode_matchers(arg)
            return ActionStep(action="swipeRightOnNode", matchers=matchers, node_query=node_query)
        else:
            return ActionStep(action="swipeRightOnNode")

    # Unknown line pattern → ignore for now
    return None


# ============================================================
# VA code → ActionPlan
# ============================================================

def parse_va_method_to_action_plan(va_code: str) -> ActionPlan:
    """
    Parse a full VA Java method into an ActionPlan.
    """
    method_name = extract_method_name(va_code)
    body_lines = extract_method_body_lines(va_code)

    steps: List[ActionStep] = []

    for line in body_lines:
        step = parse_action_line(line)
        if step is not None:
            steps.append(step)

    return ActionPlan(method_name=method_name, steps=steps)


# ============================================================
# App-level helper: parse all VA methods for an app
# ============================================================

def generate_action_plans_for_app(
    app_id: str,
    *,
    workspace_root: str = "workspace",
) -> None:
    """
    Parse all VA Java methods under:

        {workspace_root}/{app_id}/va_methods/

    Aggregates the parsed action plans and writes them as JSON to:
        {workspace_root}/actionplan/{app_id}_actionplan.json
    """
    app_root = os.path.join(workspace_root, app_id)
    va_dir = os.path.join(app_root, "va_methods")

    if not os.path.isdir(va_dir):
        raise FileNotFoundError(f"VA methods directory not found: {va_dir}")

    plans: Dict[str, ActionPlan] = {}

    for fname in os.listdir(va_dir):
        if not fname.endswith(".java"):
            continue

        va_path = os.path.join(va_dir, fname)
        if not os.path.isfile(va_path):
            continue

        with open(va_path, "r", encoding="utf-8") as f:
            va_code = f.read()

        plan = parse_va_method_to_action_plan(va_code)
        plans[plan.method_name] = plan

        # Debug/logging: summarize parsed action plan for this method
        print(f"[AVA-Gen] Parsed VA method '{plan.method_name}' with {len(plan.steps)} steps.")
        for idx, step in enumerate(plan.steps):
            print(
                f"  [STEP {idx}] action={step.action} "
                f"text={step.text!r} "
                f"node_query={step.node_query!r} "
                f"matchers={len(step.matchers)}"
            )

    # Prepare output directory
    out_dir = os.path.join(workspace_root, "actionplan")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{app_id}_actionplan.json")

    # Serialize plans as plain dicts
    plans_dict = {method: plan.model_dump() for method, plan in plans.items()}
    output_obj = {
        "app_id": app_id,
        "action_plans": plans_dict,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_obj, f, indent=2, ensure_ascii=False)
    print(f"[AVA-Gen] Action plans written to: {out_path}")


# ============================================================
# Simple demo
# ============================================================

if __name__ == "__main__":
    # Example usage:
    app_id = "hu.vmiklos.plees_tracker"
    generate_action_plans_for_app(app_id, workspace_root="workspace")