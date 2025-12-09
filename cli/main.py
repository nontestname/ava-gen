#!/usr/bin/env python3
"""
AVA-Gen CLI

This CLI orchestrates the end-to-end workflow from raw test classes to
runtime-ready artifacts.

High-level pipeline:

1) prepare
   - Copy raw test classes (and optional app introduction) into:
       workspace/<app_id>/input/

2) extract
   - Run the Espresso test parser to extract test methods into:
       workspace/<app_id>/extracted_tests/

3) generate-va
   - Generate VA methods from extracted tests into:
       workspace/<app_id>/va_methods/

4) build-skills
   - Use the skill interpreter to build skills/contexts into:
       workspace/skills_description/<app_id>_skills_description.json

5) build-intents
   - Use the intent interpreter to build:
       workspace/intent/intent_list_full.json
       workspace/intent/intent_method_map.json

6) actionplan
   - Parse VA methods into ActionPlans in:
       workspace/actionplan/<app_id>_actionplan.json

7) pipeline
   - Convenience command that runs steps 2–6 for a single app_id.

The actual VA runtime server is started separately, e.g.:

    uvicorn runtime.api.server:app --reload
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List

# Ensure project root is on sys.path when running as a script
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from configs.settings import settings
from core.converter.espresso.va_code_generator import process_app_workspace


def _count_files(directory: str, extensions: tuple[str, ...]) -> int:
    """Count files in a directory with given extensions."""
    if not os.path.isdir(directory):
        return 0
    return sum(
        1
        for fname in os.listdir(directory)
        if fname.lower().endswith(extensions)
        and os.path.isfile(os.path.join(directory, fname))
    )


def _write_json(data: Dict, out_path: str) -> None:
    """Write JSON to a file with UTF-8 encoding and pretty formatting."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _copy_file(src: str, dest: str) -> None:
    """Copy a file to dest, creating parent directories if needed."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(src, dest)


# ---------------------------------------------------------------------------
# Step 1: prepare – copy files into workspace input
# ---------------------------------------------------------------------------


def cmd_prepare(app_id: str, src_path: str, workspace_root: str) -> None:
    """
    Copy a single file into:

        {workspace_root}/{app_id}/input/

    The destination filename is the basename of src_path. This is used for
    both test classes (e.g., AccessStatisticsTest.java) and optional
    app_introduction.txt files.
    """
    app_root = os.path.join(workspace_root, app_id)
    input_dir = os.path.join(app_root, "input")
    os.makedirs(input_dir, exist_ok=True)

    if not os.path.isfile(src_path):
        raise FileNotFoundError(f"Source file not found: {src_path}")

    dest_path = os.path.join(input_dir, os.path.basename(src_path))

    print(f"[AVA-Gen] Preparing workspace for app_id={app_id}")
    print(f"[AVA-Gen] ➕ Copying file: {src_path} → {dest_path}")
    _copy_file(src_path, dest_path)
    print("[AVA-Gen] Workspace input updated")


# ---------------------------------------------------------------------------
# Step 2 & 3: extract & generate-va – use process_app_workspace
# ---------------------------------------------------------------------------


def cmd_extract(app_id: str, workspace_root: str) -> None:
    """
    Extract test methods for a given app_id.

    We currently reuse process_app_workspace, which populates both
    extracted_tests/ and va_methods/. Here we focus the output on
    extracted_tests/.
    """
    app_root = os.path.join(workspace_root, app_id)
    extracted_dir = os.path.join(app_root, "extracted_tests")

    print(f"[AVA-Gen] Parsing test scripts for app_id={app_id}...")
    process_app_workspace(app_id=app_id, workspace_root=workspace_root)
    test_count = _count_files(extracted_dir, (".java", ".kt"))
    print(f"[AVA-Gen] ✓ {test_count} test methods extracted → {extracted_dir}")


def cmd_generate_va(app_id: str, workspace_root: str) -> None:
    """
    Generate VA methods for a given app_id.

    We reuse process_app_workspace to ensure extracted_tests/ and
    va_methods/ are in sync, then report VA method count.
    """
    app_root = os.path.join(workspace_root, app_id)
    va_dir = os.path.join(app_root, "va_methods")

    print(f"[AVA-Gen] Generating VA methods for app_id={app_id}...")
    process_app_workspace(app_id=app_id, workspace_root=workspace_root)
    va_count = _count_files(va_dir, (".java",))
    print(f"[AVA-Gen] ✓ {va_count} VA methods created → {va_dir}")


# ---------------------------------------------------------------------------
# Step 4: build-skills – skills_description per app
# ---------------------------------------------------------------------------


def cmd_build_skills(app_id: str, workspace_root: str) -> None:
    """
    Build skills/contexts for a single app and write skills_description JSON.
    """
    print(f"[AVA-Gen] Building JSON skill descriptions for app_id={app_id}...")

    # Lazy import so conversion-only mode works without OPENAI_API_KEY.
    # interpret_all_methods will read all VA methods for the app and write
    # the full skills_description JSON to disk.
    from core.interpreter.skill_interpreter import interpret_all_methods

    interpret_all_methods(app_id=app_id, workspace_root=workspace_root)


# ---------------------------------------------------------------------------
# Step 5: build-intents – global intent artifacts
# ---------------------------------------------------------------------------


def cmd_build_intents(workspace_root: str) -> None:
    """
    Build global intent list and intent→method map for all apps that have
    skills_description files.
    """
    print("[AVA-Gen] Building global intent list and intent→method map...")

    # Lazy import to avoid pulling interpreter code when not needed.
    from core.interpreter.intent_interpreter import IntentInterpreter

    interpreter = IntentInterpreter(workspace_root=workspace_root)
    list_path = interpreter.export_full_intent_list()
    map_path = interpreter.export_intent_method_map()

    print(f"[AVA-Gen] ✓ {list_path} written")
    print(f"[AVA-Gen] ✓ {map_path} written")


# ---------------------------------------------------------------------------
# Step 6: actionplan – per-app ActionPlan JSON
# ---------------------------------------------------------------------------


def cmd_actionplan(app_id: str, workspace_root: str) -> None:
    """
    Build ActionPlans for a single app from its VA methods and write them to:

        {workspace_root}/actionplan/{app_id}_actionplan.json
    """
    print(f"[AVA-Gen] Building ActionPlans for app_id={app_id}...")

    # Lazy import to avoid pulling actionplan code when not needed.
    from core.actionplan.actionplan_parser import generate_action_plans_for_app

    generate_action_plans_for_app(app_id=app_id, workspace_root=workspace_root)


# ---------------------------------------------------------------------------
# Step 7: pipeline – end-to-end for a single app
# ---------------------------------------------------------------------------


def cmd_pipeline(app_id: str, workspace_root: str, skip_intents: bool) -> None:
    """
    Run the full pipeline (extract, generate-va, build-skills, build-intents)
    for a single app_id.
    """
    print(f"[AVA-Gen] Running full pipeline for app_id={app_id}")

    # Extract & VA generation in one go via process_app_workspace
    app_root = os.path.join(workspace_root, app_id)
    extracted_dir = os.path.join(app_root, "extracted_tests")
    va_dir = os.path.join(app_root, "va_methods")

    print("[AVA-Gen] Parsing test scripts...")
    process_app_workspace(app_id=app_id, workspace_root=workspace_root)
    test_count = _count_files(extracted_dir, (".java", ".kt"))
    print(f"[AVA-Gen] ✓ {test_count} test methods extracted")

    print("\n[AVA-Gen] Generating VA methods...")
    va_count = _count_files(va_dir, (".java",))
    print(f"[AVA-Gen] ✓ {va_count} VA methods created")

    print("\n[AVA-Gen] Building JSON skill descriptions...")
    cmd_build_skills(app_id=app_id, workspace_root=workspace_root)

    if skip_intents:
        print("\n[AVA-Gen] Building global intent artifacts... (skipped)")
    else:
        print("\n[AVA-Gen] Building global intent artifacts...")
        cmd_build_intents(workspace_root=workspace_root)

    # Build ActionPlans from VA methods for this app.
    print("\n[AVA-Gen] Building ActionPlans...")
    cmd_actionplan(app_id=app_id, workspace_root=workspace_root)

    print("\n[AVA-Gen] All artifacts ready for runtime")
    print("[AVA-Gen] Next step: start the VA runtime server using command:")
    print("[AVA-Gen]     uvicorn runtime.api.server:app --reload")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AVA-Gen CLI")
    parser.add_argument(
        "--workspace-root",
        default=str(settings.workspace_root),
        help=(
            "Root workspace directory "
            "(default: AVA_GEN_WORKSPACE_ROOT or 'workspace')"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # prepare
    p_prepare = subparsers.add_parser(
        "prepare",
        help="Copy a file into workspace/<app_id>/input/",
    )
    p_prepare.add_argument("app_id", help="App ID (folder name under workspace/)")
    p_prepare.add_argument(
        "path",
        help="Path to the file to copy (e.g., AccessStatisticsTest.java or app_introduction.txt)",
    )

    # extract
    p_extract = subparsers.add_parser(
        "extract", help="Extract test methods for an app"
    )
    p_extract.add_argument("app_id", help="App ID (folder name under workspace/)")

    # generate-va
    p_gen_va = subparsers.add_parser(
        "generate-va", help="Generate VA methods for an app"
    )
    p_gen_va.add_argument("app_id", help="App ID (folder name under workspace/)")

    # build-skills
    p_skills = subparsers.add_parser(
        "build-skills", help="Build skills_description JSON for an app"
    )
    p_skills.add_argument("app_id", help="App ID (folder name under workspace/)")

    # actionplan
    p_actionplan = subparsers.add_parser(
        "actionplan",
        help="Build ActionPlans for an app from its VA methods",
    )
    p_actionplan.add_argument("app_id", help="App ID (folder name under workspace/)")

    # build-intents
    subparsers.add_parser(
        "build-intents",
        help="Build global intent list and intent→method map for all apps",
    )

    # pipeline
    p_pipeline = subparsers.add_parser(
        "pipeline",
        help="Run extract, generate-va, build-skills, and build-intents for an app",
    )
    p_pipeline.add_argument("app_id", help="App ID (folder name under workspace/)")
    p_pipeline.add_argument(
        "--skip-intents",
        action="store_true",
        help="Skip building global intent artifacts",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    workspace_root: str = args.workspace_root
    command: str = args.command

    if command == "prepare":
        cmd_prepare(
            app_id=args.app_id,
            src_path=args.path,
            workspace_root=workspace_root,
        )
    elif command == "actionplan":
        cmd_actionplan(app_id=args.app_id, workspace_root=workspace_root)
    elif command == "extract":
        cmd_extract(app_id=args.app_id, workspace_root=workspace_root)
    elif command == "generate-va":
        cmd_generate_va(app_id=args.app_id, workspace_root=workspace_root)
    elif command == "build-skills":
        cmd_build_skills(app_id=args.app_id, workspace_root=workspace_root)
    elif command == "build-intents":
        cmd_build_intents(workspace_root=workspace_root)
    elif command == "pipeline":
        cmd_pipeline(
            app_id=args.app_id,
            workspace_root=workspace_root,
            skip_intents=args.skip_intents,
        )
    else:
        parser.error(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
