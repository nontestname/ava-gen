# Using the AVA‑Gen Runtime (Server & Client)

This guide explains how to:

- Start the AVA‑Gen runtime server.
- Call the `/agent` HTTP endpoints from a client.
- Connect an Android emulator or a real phone to the server.
- Note the small differences for macOS vs. Windows hosts.

It assumes you have already:

- Installed AVA‑Gen (`pip install .` or `pipx install ava-gen`).
- Configured `OPENAI_API_KEY` and run the pipeline so that:
  - `workspace/skills_description/*.json`
  - `workspace/intent/intent_list_full.json`
  - `workspace/intent/intent_method_map.json`
  - `workspace/actionplan/<app_id>_actionplan.json`
    exist for at least one app (e.g. `hu.vmiklos.plees_tracker`).

---

## 1. Start the runtime server

From the project root:

```bash
uvicorn runtime.api.server:app --reload
```

This will:

- Load configuration from your environment / `.env` (see `configs/settings.py`).
- Initialize the intent validator, action plan store, and session store.
- Expose the FastAPI app on `http://127.0.0.1:8000` by default.

If the `uvicorn` command is not found, use the Python module form instead:

- **macOS / Linux**

  ```bash
  python -m uvicorn runtime.api.server:app --reload
  ```

- **Windows (PowerShell / Command Prompt)**

  ```bash
  py -m uvicorn runtime.api.server:app --reload
  ```

> Tip: To allow access from other devices on your local network, bind to
> all interfaces:
>
> ```bash
> uvicorn runtime.api.server:app --host 0.0.0.0 --port 8000 --reload
> ```

You can verify the server is up by opening:

- `http://127.0.0.1:8000/agent/healthz`

You should see:

```json
{ "status": "ok" }
```

---

## 2. Using an Android emulator

To run the example app (or your own APK) in an Android emulator and connect it
to the AVA‑Gen runtime server, you will typically:

1. Start the emulator.
2. Install the AVA‑Gen client APK (`ava-gen-client.apk`).
3. Install your example/app-under-test APK.
4. Configure the client app to talk to the host machine (`10.0.2.2:8000`).

### 2.1 Start an emulator

Use Android Studio’s AVD Manager or the command line:

- Open Android Studio → Device Manager → create / start a virtual device.
- Or run:

  ```bash
  emulator -avd <your_avd_name>
  ```

### 2.2 Install the AVA‑Gen client APK

Once the emulator is running, install the provided AVA‑Gen client APK:

```bash
adb install client/ava-gen-client_v1.apk
```

On first launch, make sure:

- The app has **Microphone** permission (Search Permissions → Microphone and enable it).
- If your test device/emulator groups these permissions under Accessibility, ensure the microphone permission is enabled there as well.

### 2.3 Install your example/app-under-test APK

Once the emulator is running, install your example APK via `adb`:

```bash
adb install path/to/your_app.apk
```

If you rebuilt the APK, you may need:

```bash
adb install -r path/to/your_app.apk
```

For the running example of `hu.vmiklos.plees_tracker`, please:

```bash
adb install examples/plees-tracker-24.8.1.apk
```

You should see AVA-Gen app in the Accessibility Tool List after the installation.

### 2.4 Configure the client app to talk to the server

Inside an Android emulator:

- `10.0.2.2` is a special alias that points to **your host’s** `127.0.0.1`.

So as long as you run the server and the emulator (with client) on the same computer (MacOS or Windows), you should see everything connect together automatically.

---

## 3. Using a real Android device (phone)

You can also connect a physical phone to the AVA‑Gen runtime running on your
Mac or Windows machine. There are two common patterns:

1. Use `adb reverse` (USB cable, no Wi‑Fi configuration).
2. Put both phone and host on the same Wi‑Fi network (Not tested)

### 3.1 Using `adb reverse` (recommended for development)

This works on Android 5.0+ and does not require exposing your server on the LAN.

1. Enable **USB debugging** on your phone (Developer options).
2. Connect the phone via USB.
3. Verify the device is recognized:

   ```bash
   adb devices
   ```

4. Start the AVA‑Gen server on your host:

   ```bash
   uvicorn runtime.api.server:app --reload
   ```

5. Run `adb reverse` so the device can reach the host’s port 8000 via its own
   `localhost`:

   ```bash
   adb reverse tcp:8000 tcp:8000
   ```

When the app calls, traffic is forwarded over USB to the AVA‑Gen server running on your Mac or Windows machine.

> On some cases, firewalls can block incoming connections. If the app cannot reach the server, check your firewall settings on macOS (System Settings → Network/Firewall) or Windows (Windows Defender Firewall).

---

## 4. Test the HTTP API from your desktop (curl / Postman)

Once the server is running, you can exercise the `/agent` API directly from your Mac or Windows machine. This is useful for debugging before wiring up the Android client.

The runtime exposes three key endpoints, all under the `/agent` prefix:

- `GET /agent/healthz`  
  Simple health check.

- `POST /agent/start_session`  
  Returns a new `session_id` you use for subsequent requests.

- `POST /agent/request`  
  Main interaction endpoint; takes user messages plus `session_id` and
  `app_id`, and returns an `AgentResponse` (clarifying questions or an
  ActionPlan).

### 4.1 Start a session (curl)

```bash
curl -X POST http://127.0.0.1:8000/agent/start_session
```

Example response:

```json
{ "session_id": "abc123-session-id" }
```

### 4.2 Send a request (curl)

Use the `session_id` above and the app id you have processed (for example
`hu.vmiklos.plees_tracker`):

```bash
curl -X POST http://127.0.0.1:8000/agent/request \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123-session-id",
    "app_id": "hu.vmiklos.plees_tracker",
    "message": "Delete all existing sleep records"
  }'
```

The response shape is defined in `runtime/models/api_models.py` and normally
includes a high-level status and, when applicable, an ActionPlan derived from
your `workspace/actionplan/<app_id>_actionplan.json`.

### 4.3 Use Postman (or similar)

If you prefer a GUI client like Postman or Insomnia:

1. Create a new **POST** request to `http://127.0.0.1:8000/agent/start_session`.
2. Send the request and copy the `session_id` from the JSON response.
3. Create another **POST** request to `http://127.0.0.1:8000/agent/request`.
4. Set the body type to **raw JSON** and provide:

   ```json
   {
     "session_id": "abc123-session-id",
     "app_id": "hu.vmiklos.plees_tracker",
     "message": "Delete all existing sleep records"
   }
   ```

5. Send the request and inspect the JSON response (clarifications, selected
   ActionPlan, etc.).
