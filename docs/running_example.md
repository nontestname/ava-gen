# AVA-Gen Running Example for preparing VA-Ready Artifacts

This guide walks through a **concrete, end-to-end example** that generating all the VA-Ready Artifacts that your AVA-Gen sever may need later, using the example tests and application descriptions under `workspace/` folder and the bundled example app:

- `app_id`: `hu.vmiklos.plees_tracker`

We assume you have already:

- Installed AVA‑Gen from this repo (`pip install .` or `pipx install ava-gen`)
- Configured `OPENAI_API_KEY` via environment or `.env`

All commands below are run from the project root (where `pyproject.toml` lives).

---

## 1. Prepare the example in the real workspace

This repo ships an example test and app introduction under:

- `examples/hu.vmiklos.plees_tracker/DeleteAllSleepsTest.java`
- `examples/hu.vmiklos.plees_tracker/app_introduction.txt`

Use the `prepare` command to copy these into the `workspace/` folder:

```bash
ava-gen prepare hu.vmiklos.plees_tracker examples/hu.vmiklos.plees_tracker/DeleteAllSleepsTest.java
ava-gen prepare hu.vmiklos.plees_tracker examples/hu.vmiklos.plees_tracker/app_introduction.txt
```

After this, your real workspace will contain:

```text
workspace/
  hu.vmiklos.plees_tracker/
    input/
      DeleteAllSleepsTest.java
      app_introduction.txt
```

This is exactly the same structure you will use for your own apps, just with a
different `{app_id}`, different tests and app introduction.

---

## 2. Run the pipeline for `hu.vmiklos.plees_tracker`

Now run the full pipeline against the `workspace/`:

```bash
ava-gen pipeline hu.vmiklos.plees_tracker
```

This will automatically:

- Parse the Espresso test class from `workspace/hu.vmiklos.plees_tracker/input/`
- Generate _Code Artifacts_:

  - `workspace/hu.vmiklos.plees_tracker/extracted_tests/` – per-test method Java files
  - `workspace/hu.vmiklos.plees_tracker/va_methods/` – converted VA methods

- Generate _Description Artifacts_:
  - `workspace/skills_description/hu.vmiklos.plees_tracker_skills_description.json`
  - `workspace/intent/intent_list_full.json`
  - `workspace/intent/intent_method_map.json`
  - `workspace/actionplan/hu.vmiklos.plees_tracker_actionplan.json`

After the command completes, your workspace will look roughly like:

```text
workspace/
  actionplan/
    hu.vmiklos.plees_tracker_actionplan.json

  intent/
    intent_list_full.json
    intent_method_map.json

  skills_description/
    hu.vmiklos.plees_tracker_skills_description.json

  hu.vmiklos.plees_tracker/
    input/
      DeleteAllSleepsTest.java
      app_introduction.txt
    extracted_tests/
      deleteAllSleepsTest.java
    va_methods/
      deleteAllSleeps.java
```

**Congratulations!** Now you have succesfully generate all the VA-Ready Artifcats for your app `hu.vmiklos.plees_tracker` with skill extracted from test method `DeleteAllSleepsTest.java`

The AVA-Gen server is ready to use all these artifacts to support the Voice Assistant on deleting all sleeps. Please see this to check details about AVA-Gen runtime server-client architecture.

---

## 3. Adapt the pattern to your own app

To use AVA‑Gen with your own app under the same `workspace/` root:

1. Choose your app id, e.g. `com.example.myapp`.
2. Prepare input files:

   ```bash
   ava-gen prepare com.example.myapp path/to/MyAppTest.java
   ava-gen prepare com.example.myapp path/to/app_introduction.txt   # optional
   ```

3. Run the pipeline:

   ```bash
   ava-gen pipeline com.example.myapp
   ```

You will get the same kinds of outputs as the `hu.vmiklos.plees_tracker` example,
but under `workspace/com.example.myapp/` and shared `workspace/skills_description`,
`workspace/intent`, and `workspace/actionplan`.

---

## 4. (Optional) Start the runtime server

Once your example (and/or your own app) has been processed via the pipeline, you
can start the runtime server from the project root:

```bash
uvicorn runtime.api.server:app --reload
```

Before starting the server, make sure:

- `workspace/hu.vmiklos.plees_tracker/actionplan/hu.vmiklos.plees_tracker_actionplan.json`
  exists (and similarly for your own `{app_id}`)
- `workspace/intent/intent_list_full.json` and
  `workspace/intent/intent_method_map.json` have been generated

Your tools or clients can then talk to the server at:

- `http://127.0.0.1:8000/agent`

using the ActionPlans and skills that were generated in the real `workspace/` folder.
