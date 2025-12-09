# AVA-Gen CLI Guide

This document describes the AVA-Gen command-line interface (CLI) and how it
orchestrates the end-to-end workflow from **raw test classes** to
**runtime-ready artifacts** for the AVA-Gen server.

The CLI lives in `cli/main.py` and is exposed as the `ava-gen` command when
you install the package.

---

## Installation

From the project root:

```bash
pip install .
# or
pipx install .
```

Once installed:

```bash
ava-gen --help
```

---

## Configuration

AVA-Gen reads configuration from environment variables (optionally via a
`.env` file). Copy `.env.example` to `.env` and fill in your values:

- `OPENAI_API_KEY` (required) – your OpenAI key.
- `OPENAI_BASE_URL` (optional) – custom API base URL or proxy.
- `AVA_GEN_OPENAI_MODEL` (optional) – default model (default: `gpt-4.1-mini`).
- `AVA_GEN_INTENT_MODEL` (optional) – model for intent matching (defaults to `AVA_GEN_OPENAI_MODEL`).
- `AVA_GEN_WORKSPACE_ROOT` (optional) – workspace root (default: `workspace`).
- `AVA_GEN_RUNTIME_DATA_DIR` (optional) – runtime data dir (default: `runtime/data`).

The CLI option `--workspace-root` always takes precedence over
`AVA_GEN_WORKSPACE_ROOT`.

---

## Overview

High-level pipeline (per app):

| Step | Command                           | Purpose                                                   | Key outputs                                                                 |
|------|-----------------------------------|-----------------------------------------------------------|-----------------------------------------------------------------------------|
| 1    | `ava-gen prepare <app_id> ...`    | Copy raw test classes / app intro into the workspace.     | `workspace/<app_id>/input/`                                                 |
| 2    | `ava-gen extract <app_id>`        | Parse Espresso tests into per-test Java methods.          | `workspace/<app_id>/extracted_tests/`                                       |
| 3    | `ava-gen generate-va <app_id>`    | Convert extracted tests into VA methods.                  | `workspace/<app_id>/va_methods/`                                            |
| 4    | `ava-gen build-skills <app_id>`   | Build skill/context descriptions from VA methods.         | `workspace/skills_description/<app_id>_skills_description.json`             |
| 5    | `ava-gen build-intents`           | Aggregate intents and intent→method mapping (all apps).   | `workspace/intent/intent_list_full.json`, `workspace/intent/intent_method_map.json` |
| 6    | `ava-gen actionplan <app_id>`     | Build ActionPlans from VA methods for the given app.      | `workspace/actionplan/<app_id>_actionplan.json`                             |
| 7    | `ava-gen pipeline <app_id>`       | Convenience command that runs steps 2–6 for one app.      | All of the above for `<app_id>`                                             |

The VA runtime server is started separately, for example:

```bash
uvicorn runtime.api.server:app --reload
```

All commands accept an optional `--workspace-root` argument (default: `workspace`).

---

## Global options

```bash
ava-gen <command> [options]
ava-gen --workspace-root <PATH> <command> [options]
```

- By default, the workspace root is taken from `AVA_GEN_WORKSPACE_ROOT` or
  `./workspace` if the env var is not set.
- `--workspace-root PATH`  
  Overrides the workspace root for a single command.

!!! important
`--workspace-root` is a **global** option. It must appear
**before** the subcommand name (`prepare`, `extract`, `pipeline`, etc.),
not after the `app_id`.

---

## 1. `prepare` – copy files into workspace input

Prepare the workspace for a specific app by copying a single file into the
app's `input/` folder. You can call this multiple times (for test classes and
an optional app introduction text).

### Usage

```bash
ava-gen prepare <app_id> path/to/file
```

### Behavior

- Creates (if needed):
  - `workspace/<app_id>/input/`
- Copies:
  - `path/to/file` → `workspace/<app_id>/input/<original_name>`

Call this once for your test class, e.g.:

```bash
ava-gen prepare com.example.myapp path/to/MyAppTest.java
```

And optionally once for your app introduction:

```bash
ava-gen prepare com.example.myapp path/to/app_introduction.txt
```

### Example output

```text
[AVA-Gen] Preparing workspace for app_id=hu.vmiklos.plees_tracker
[AVA-Gen] ➕ Copying file: tests/PleesTrackerTests.java → workspace/hu.vmiklos.plees_tracker/input/PleesTrackerTests.java
[AVA-Gen] Workspace input updated
```

---

## 2. `extract` – extract test methods

Run the Espresso test parser and populate `extracted_tests/` for the app.

### Usage

```bash
ava-gen extract <app_id>
```

### Behavior

- Calls `process_app_workspace(app_id, workspace_root)` (converter pipeline).
- Reports how many test methods were extracted.
- Uses:
  - `workspace/<app_id>/extracted_tests/`

### Example output

```text
[AVA-Gen] Parsing test scripts for app_id=hu.vmiklos.plees_tracker...
[AVA-Gen] ✓ 12 test methods extracted → workspace/hu.vmiklos.plees_tracker/extracted_tests/
```

!!! note
Internally, `process_app_workspace` also populates `va_methods/`, but
this command focuses on reporting the extracted tests.

---

## 3. `generate-va` – generate VA methods

Generate VA methods from the extracted tests for a specific app.

### Usage

```bash
ava-gen generate-va <app_id>
```

### Behavior

- Reuses `process_app_workspace(app_id, workspace_root)` to ensure that
  `extracted_tests/` and `va_methods/` are in sync.
- Counts the generated VA method files.
- Uses:
  - `workspace/<app_id>/va_methods/`

### Example output

```text
[AVA-Gen] Generating VA methods for app_id=hu.vmiklos.plees_tracker...
[AVA-Gen] ✓ 5 VA methods created → workspace/hu.vmiklos.plees_tracker/va_methods/
```

---

## 4. `build-skills` – build skills_description JSON

Build skill/context descriptions for a specific app using the skill interpreter.

### Usage

```bash
ava-gen build-skills <app_id>
```

### Behavior

- Calls `core.interpreter.skill_interpreter.interpret(workspace_root, app_id)`.
- Writes a skills/contexts JSON file to:

  ```text
  workspace/skills_description/<app_id>_skills_description.json
  ```

### Example output

```text
[AVA-Gen] Building JSON skill descriptions for app_id=hu.vmiklos.plees_tracker...
[AVA-Gen] ✓ workspace/skills_description/hu.vmiklos.plees_tracker_skills_description.json written
```

---

## 5. `build-intents` – build global intent artifacts

Build the global intent list and intent→method map used by the runtime
intent validator.

### Usage

```bash
ava-gen build-intents
```

### Behavior

- Uses `core.interpreter.intent_interpreter.IntentInterpreter`.
- Aggregates all `*_skills_description.json` files.
- Writes:

  - `workspace/intent/intent_list_full.json`  
    – per-app **intent strings** (and optional `intent_summary` sentence) for GPT
    intent matching and capability summaries.
  - `workspace/intent/intent_method_map.json`  
    – per-app **intent → method_name** mapping.

### Example output

```text
[AVA-Gen] Building global intent list and intent→method map...
[AVA-Gen] ✓ workspace/intent/intent_list_full.json written
[AVA-Gen] ✓ workspace/intent/intent_method_map.json written
```

---

## 6. `actionplan` – build ActionPlans for one app

Build ActionPlans for a specific app based on its generated VA methods.

### Usage

```bash
ava-gen actionplan <app_id>
```

### Behavior

- Uses `core.actionplan.actionplan_parser.generate_action_plans_for_app`.
- Reads:
  - `workspace/<app_id>/va_methods/*.java`
- Writes:
  - `workspace/actionplan/<app_id>_actionplan.json`

### Example output

```text
[AVA-Gen] Building ActionPlans for app_id=hu.vmiklos.plees_tracker...
[AVA-Gen] Action plans written to: workspace/actionplan/hu.vmiklos.plees_tracker_actionplan.json
```

---

## 7. `pipeline` – run the full chain for one app

Run the main pipeline steps (2–6) for a single app in one command.

### Usage

```bash
ava-gen pipeline <app_id> [--skip-intents]
```

- `--skip-intents`  
  If provided, skips the `build-intents` step and only generates
  app-specific artifacts (extracted tests, VA methods, skills_description).

### Behavior

- For the given `app_id`, runs:

  1. `extract` (via `process_app_workspace`)
  2. `generate-va` (counting VA method files)
  3. `build-skills`
  4. `build-intents` (unless `--skip-intents` is set)
  5. `actionplan`

### Example output

```text
[AVA-Gen] Running full pipeline for app_id=hu.vmiklos.plees_tracker
[AVA-Gen] Parsing test scripts...
[AVA-Gen] 12 test methods extracted

[AVA-Gen] Generating VA methods...
[AVA-Gen] 5 VA methods created

[AVA-Gen] Building JSON skill descriptions...
[AVA-Gen] workspace/skills_description/hu.vmiklos.plees_tracker_skills_description.json written

[AVA-Gen] Building global intent artifacts...
[AVA-Gen] workspace/intent/intent_list_full.json written
[AVA-Gen] workspace/intent/intent_method_map.json written

[AVA-Gen] Building ActionPlans...
[AVA-Gen] Action plans written to: workspace/actionplan/hu.vmiklos.plees_tracker_actionplan.json

[AVA-Gen] All artifacts ready for runtime
[AVA-Gen] Next step: start the VA runtime server
[AVA-Gen]     uvicorn runtime.api.server:app --reload
```

If `--skip-intents` is used:

```text
[AVA-Gen] Building global intent artifacts... (skipped)
```

---

## 7. Starting the runtime server

After running the CLI pipeline (either via individual commands or `pipeline`),
the VA-Gen runtime server can be started separately:

```bash
uvicorn runtime.api.server:app --reload
```

The server will then use:

- `workspace/skills_description/` for skills/contexts
- `workspace/intent/intent_list_full.json` and `intent_method_map.json` for
  intent validation
- `workspace/actionplan/<app_id>_actionplan.json` for ActionPlans

You can interact with the server using tools like Postman or your Android
client.
