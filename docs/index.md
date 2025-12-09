# AVA-Gen

AVA-Gen is an automated tool including two parts:

1. A pipeline that converts existing Espresso UI tests (Java/Kotlin) into VA methods and using LLM calls (GPT APIs) to generate other code description artifacts.
2. A runtime server and client architecture that support converting user request to the VA tasks.

## Demo video

You can watch a short demo of AVA‑Gen in action here:

https://youtu.be/z4p19QL6ejw

<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%;">
  <iframe
    src="https://www.youtube.com/embed/z4p19QL6ejw"
    title="AVA‑Gen Demo"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowfullscreen
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
  </iframe>
</div>

## Quick start

1. Install the package from the project root:

   ```bash
   pip install .
   ```

   This installs the `ava-gen` CLI and the runtime components.

2. Configure environment and OpenAI:

   - Copy `.env.example` to `.env`, and edit it

   ```bash
   cp .env.example .env
   ```

   - Set `OPENAI_API_KEY` and (optionally) variables such as `AVA_GEN_OPENAI_MODEL`

3. Run your first end-to-end example using the real `workspace/` folder and the bundled app `hu.vmiklos.plees_tracker` by following:

   - `docs/running_example.md`

   This walks you through preparing inputs under `workspace/`, running `ava-gen pipeline hu.vmiklos.plees_tracker`, and inspecting the generated
   artifacts (extracted tests, VA methods, skills, intents, action plans).

4. Explore the CLI and pipelines for your own app (see `docs/cli.md` and `docs/getting-started.md` for details):

   ```bash
   ava-gen --help
   ```

5. Start the runtime server (once workspace artifacts and action plans exist):

   ```bash
   uvicorn runtime.api.server:app --reload
   ```

See the `docs/` directory (used by MkDocs) for:

- `docs/running_example.md` – concrete running example on the real workspace.
- `docs/cli.md` – CLI usage and pipeline overview.
- `docs/runtime_server_client.md` – runtime usage.
