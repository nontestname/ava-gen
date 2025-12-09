"""
core.converter.espresso.va_code_generator

See previous version for detailed docs; this version adds workspace support:

workspace/
  app_id_1/
    input_tests/      # raw Espresso test classes (already exists)
    extracted_tests/  # GENERATED: one @Test method per file (test-only)
    va_methods/       # GENERATED: VA Java methods (one per file)
"""

from __future__ import annotations

import os
import re
from typing import Dict, List

from core.converter.espresso.java_extractor import (
    extract_espresso_calls_from_java_source,
)
from core.converter.espresso.kotlin_extractor import (
    extract_espresso_calls_from_kotlin_source,
)
from core.converter.espresso.statement_converter import (
    convert_espresso_statement,
    validate_non_espresso_statement,
)


# ---------------------------------------------------------------------------
# Utilities: language detection
# ---------------------------------------------------------------------------

def detect_language_from_path(path: str) -> str:
    _, ext = os.path.splitext(path)
    if ext == ".java":
        return "java"
    if ext == ".kt":
        return "kotlin"
    raise ValueError(f"Unsupported file extension for AVA-Gen: {ext}")


# ---------------------------------------------------------------------------
# Step 1: Extract @Test methods from a Java/Kotlin class source
# ---------------------------------------------------------------------------

def split_test_methods_from_java_source(source: str) -> Dict[str, str]:
    lines = source.splitlines()
    methods: Dict[str, str] = {}

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        if line == "@Test":
            header_index = i + 1
            while header_index < n and not lines[header_index].strip():
                header_index += 1
            if header_index >= n:
                break

            header_line = lines[header_index]
            m = re.search(r"public\s+void\s+(\w+)\s*\(", header_line)
            if not m:
                i = header_index + 1
                continue

            method_name = m.group(1)

            if "{" not in header_line:
                body_start_index = header_index + 1
                while body_start_index < n and "{" not in lines[body_start_index]:
                    body_start_index += 1
                if body_start_index >= n:
                    break
            else:
                body_start_index = header_index

            brace_count = 0
            method_end_index = body_start_index
            while method_end_index < n:
                brace_count += lines[method_end_index].count("{")
                brace_count -= lines[method_end_index].count("}")
                if brace_count == 0:
                    break
                method_end_index += 1

            method_lines = lines[i : method_end_index + 1]
            methods[method_name] = "\n".join(method_lines)

            i = method_end_index + 1
        else:
            i += 1

    return methods


def split_test_methods_from_kotlin_source(source: str) -> Dict[str, str]:
    lines = source.splitlines()
    methods: Dict[str, str] = {}

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        if line == "@Test":
            header_index = i + 1
            while header_index < n and not lines[header_index].strip():
                header_index += 1
            if header_index >= n:
                break

            header_line = lines[header_index]
            m = re.search(r"fun\s+(\w+)\s*\(", header_line)
            if not m:
                i = header_index + 1
                continue

            method_name = m.group(1)

            if "{" not in header_line:
                body_start_index = header_index + 1
                while body_start_index < n and "{" not in lines[body_start_index]:
                    body_start_index += 1
                if body_start_index >= n:
                    break
            else:
                body_start_index = header_index

            brace_count = 0
            method_end_index = body_start_index
            while method_end_index < n:
                brace_count += lines[method_end_index].count("{")
                brace_count -= lines[method_end_index].count("}")
                if brace_count == 0:
                    break
                method_end_index += 1

            method_lines = lines[i : method_end_index + 1]
            methods[method_name] = "\n".join(method_lines)

            i = method_end_index + 1
        else:
            i += 1

    return methods


# ---------------------------------------------------------------------------
# Step 2: Convert a single test method to a VA method
# ---------------------------------------------------------------------------

def rename_method_without_test_suffix(header_line: str) -> str:
    def repl(match: re.Match) -> str:
        prefix = match.group(1)
        name = match.group(2)
        suffix = match.group(3)
        if name.endswith("Test"):
            name = name[:-4]
        return f"{prefix}{name}{suffix}"

    # Allow an optional `throws ...` clause between parameter list and `{`
    pattern = r"(public\s+void\s+)(\w+)(\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\s*\{)"
    return re.sub(pattern, repl, header_line)


def generate_va_method_from_test_method(
    method_source: str,
    language: str = "java",
) -> str:
    lines = method_source.splitlines()

    # remove @Test
    cleaned_lines: List[str] = [l for l in lines if not l.strip().startswith("@Test")]

    # locate header
    header_index = None
    for idx, line in enumerate(cleaned_lines):
        if "public void" in line:
            header_index = idx
            break
    if header_index is None:
        for idx, line in enumerate(cleaned_lines):
            if "fun " in line and "(" in line:
                header_index = idx
                break
    if header_index is None:
        raise ValueError("Could not locate method header in test method.")

    header_line = cleaned_lines[header_index]

    if language == "java":
        new_header_line = rename_method_without_test_suffix(header_line)
    else:
        def repl_fun(match: re.Match) -> str:
            prefix = match.group(1)
            name = match.group(2)
            suffix = match.group(3)
            if name.endswith("Test"):
                name = name[:-4]
            return f"{prefix}{name}{suffix}"
        new_header_line = re.sub(r"(fun\s+)(\w+)(\s*\([^)]*\)\s*\{)", repl_fun, header_line)

    cleaned_lines[header_index] = new_header_line
    cleaned_source = "\n".join(cleaned_lines)

    if language == "java":
        espresso_calls = extract_espresso_calls_from_java_source(cleaned_source)
    else:
        espresso_calls = extract_espresso_calls_from_kotlin_source(cleaned_source)

    # build VA method body, preserving original statement order
    header_indent_match = re.match(r"^(\s*)", new_header_line)
    header_indent = header_indent_match.group(1) if header_indent_match else ""
    stmt_indent = header_indent + "    "

    va_lines: List[str] = []
    va_lines.append(new_header_line)

    body_started = "{" in new_header_line
    collecting = False
    buffer: List[str] = []
    paren_balance = 0

    def flush_buffer() -> None:
        nonlocal collecting, buffer, paren_balance
        joined = " ".join(line.strip() for line in buffer)
        try:
            converted = convert_espresso_statement(joined)
        except Exception:
            converted = ""
        if converted and not converted.startswith("Error:"):
            va_lines.append(f"{stmt_indent}{converted}")
        collecting = False
        buffer = []
        paren_balance = 0

    for line in cleaned_lines[header_index + 1 :]:
        stripped = line.strip()

        # Skip until body starts
        if not body_started:
            if "{" in line:
                body_started = True
            continue

        # Stop at closing brace
        if stripped.startswith("}"):
            break

        # Collect multi-line Espresso statements
        if collecting:
            buffer.append(line)
            paren_balance += line.count("(") - line.count(")")
            joined = " ".join(l.strip() for l in buffer)
            if ".perform(" in joined and joined.rstrip().endswith(");") and paren_balance <= 0:
                flush_buffer()
            continue

        if not stripped:
            continue

        # Start collecting an Espresso statement
        if any(entry in stripped for entry in ("onView(", "onData(", "onWebView(")):
            buffer = [line]
            collecting = True
            paren_balance = line.count("(") - line.count(")")
            joined = " ".join(l.strip() for l in buffer)
            if ".perform(" in joined and joined.rstrip().endswith(");") and paren_balance <= 0:
                flush_buffer()
            continue

        # Drop assertions
        if "check(" in stripped or "matches(" in stripped:
            continue

        # Keep allowed non-Espresso helpers
        if validate_non_espresso_statement(stripped):
            va_lines.append(f"{stmt_indent}{stripped}")

    va_lines.append(f"{header_indent}}}")

    return "\n".join(va_lines)


# ---------------------------------------------------------------------------
# Workspace-level API
# ---------------------------------------------------------------------------

def process_app_workspace(app_id: str, workspace_root: str = "workspace") -> None:
    """
    Process one app's AVA-Gen workspace.

    Expected workspace layout:

        workspace/
          <app_id>/
            input/               ← contains raw test class files (*.java / *.kt)
              app_introduction.txt  (optional; used later by interpreter)
              *.java
              *.kt
            extracted_tests/      ← created automatically
            va_methods/           ← created automatically

    Steps:
      1. Read each .java/.kt file in input/
      2. Split into individual @Test methods (remove imports, rules, etc.)
      3. Write each stripped test method into extracted_tests/
      4. Convert each test method into a VA Java method
      5. Save into va_methods/ (method names remove "Test" suffix)

    Note:
      Skill description generation (JSON) is done separately in skill_interpreter.
    """

    # ------------------------------
    # Path setup
    # ------------------------------
    app_root = os.path.join(workspace_root, app_id)
    input_dir = os.path.join(app_root, "input")
    extracted_dir = os.path.join(app_root, "extracted_tests")
    va_dir = os.path.join(app_root, "va_methods")

    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    os.makedirs(extracted_dir, exist_ok=True)
    os.makedirs(va_dir, exist_ok=True)

    # ------------------------------
    # Iterate through input files
    # ------------------------------
    for fname in os.listdir(input_dir):
        fpath = os.path.join(input_dir, fname)
        if not os.path.isfile(fpath):
            continue

        # Skip app introduction file
        if fname == "app_introduction.txt":
            print(f"[AVA-Gen] Found app introduction: {fpath}")
            continue

        # Accept only Java/Kotlin test classes
        if not (fname.endswith(".java") or fname.endswith(".kt")):
            print(f"[AVA-Gen] Skipping non-test file: {fname}")
            continue

        # Determine language
        language = detect_language_from_path(fpath)

        with open(fpath, "r", encoding="utf-8") as f:
            source = f.read()

        # Extract test methods
        if language == "java":
            test_methods = split_test_methods_from_java_source(source)
            ext = ".java"
        else:
            test_methods = split_test_methods_from_kotlin_source(source)
            ext = ".kt"

        if not test_methods:
            print(f"[AVA-Gen] WARNING: No @Test methods found in {fname}")
            continue

        # ------------------------------
        # Process each extracted test method
        # ------------------------------
        for raw_method_name, method_src in test_methods.items():

            # Normalize method name (remove spaces, line breaks)
            method_name = raw_method_name.strip()

            # ------------------------------
            # 1) Save the stripped test method
            # ------------------------------
            extracted_path = os.path.join(extracted_dir, f"{method_name}{ext}")
            with open(extracted_path, "w", encoding="utf-8") as out_f:
                out_f.write(method_src)
                out_f.write("\n")

            # ------------------------------
            # 2) Convert to a VA Java method
            # ------------------------------
            va_java = generate_va_method_from_test_method(method_src, language=language)

            # Remove trailing "Test" suffix if present
            if method_name.endswith("Test"):
                va_method_name = method_name[:-4]
            else:
                va_method_name = method_name

            va_path = os.path.join(va_dir, f"{va_method_name}.java")
            with open(va_path, "w", encoding="utf-8") as out_f:
                out_f.write(va_java)
                out_f.write("\n")

    # ------------------------------
    # Done!
    # ------------------------------
    print(f"\n[AVA-Gen] Finished processing workspace for app_id='{app_id}'")
    print(f"  Input directory:        {input_dir}")
    print(f"  Extracted test methods: {extracted_dir}")
    print(f"  VA methods output:      {va_dir}\n")


# ---------------------------------------------------------------------------
# Demo / manual test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example: process existing workspace/app_id_1
    process_app_workspace(app_id="hu.vmiklos.plees_tracker", workspace_root="workspace")
