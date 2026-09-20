# artemis-e2e-pipeline

Story → test case → execution pipeline for Android E2E automation, using [google/artemis](https://github.com/google/artemis) to execute against the [ADYA](../ADYA) app (`com.sarangupadhye.adya`).

**Status: working end-to-end.** The "Add a task from the Today screen" story has been generated into test steps and successfully executed against ADYA on a local emulator via ARTEMIS Flash mode + Gemini (`gemini-3.6-flash`) — it opened the app, got past onboarding, avoided the real sign-in flow, added "Buy milk", and verified it appeared in the task list.

## Flow

```
stories/*.json  --(generate_tests.py, via local Ollama)-->  generated_tests/*.json  --(run_tests.py, via ARTEMIS)--> pass/fail + replays
```

1. **Write a story** as JSON in `stories/` (schema below).
2. **Generate test cases** from it using a local Ollama model — no API key needed.
3. **Execute** the generated test cases against a connected device/emulator via ARTEMIS, driven by Gemini (free tier).

## Story schema

See `stories/add_task.json` for an example. Fields:

- `id` — unique story id
- `title`, `description` — the user story
- `app`, `package`, `screen` — which app/screen this targets
- `acceptance_criteria` — plain-English criteria the generated tests must cover
- `known_elements` — map of logical name → how to find it (accessibility label, visible text, or a visual description), since ADYA has no `testID`s

**Important:** ADYA has a real sign-in flow (Google/Apple/email via Firebase). Stories and generated tests must never exercise it — no automation should enter account credentials. Target flows that work signed-out (e.g. adding a task on the Today screen).

## Setup

```bash
# 1. Ollama (test-case generation only, local, no API key)
ollama pull llama3.2

# 2. Gemini API key (ARTEMIS's actual perception/planning model - local
# Ollama vision models were tried first but hit real blockers: llama3.2-vision's
# 'mllama' architecture isn't loadable by current Ollama server builds, and
# moondream lacks tool-calling support that ARTEMIS's planner requires).
# Get a free key at https://aistudio.google.com/apikey and put it in
# ../artemis/.env as GEMINI_API_KEY=...
# Note: newer keys can't use gemini-2.5-flash or older ("no longer available
# to new users") - config/artemis.jsonc is already set to gemini-3.6-flash,
# which works. Free tier is a HARD 20 requests/day/model quota (not
# per-minute) - Flash mode uses far fewer calls per task than Pro mode, so
# prefer Flash while on the free tier.

# 3. ARTEMIS (execution) - already cloned as a sibling repo at ../artemis
cd ../artemis
export UV_HTTP_TIMEOUT=120
uv sync
# If you ever see "ModuleNotFoundError: No module named 'artemis_client'"
# (a uv/Python 3.14 editable-install bug where the workspace member's .pth
# silently fails to register), the durable fix is a real symlink instead of
# relying on .pth processing:
ln -sf "$(pwd)/packages/artemis-client/src/artemis_client" .venv/lib/python3.14/site-packages/artemis_client
./start.sh
# In the console (http://localhost:8000), choose "Custom Configuration"
# under AI Model Setup - it reads ../artemis/config/artemis.jsonc.

# 4. This repo's deps
pip install -r requirements.txt
```

## Usage

```bash
# Generate test cases for a story
python scripts/generate_tests.py stories/add_task.json

# Run them against a device/emulator, installing the bundled APK first
python scripts/run_tests.py generated_tests/US-001.json \
  --device emulator-5554 \
  --mode flash \
  --apk app/ADYA-release.apk
```

Or drive it directly through the ARTEMIS console (what was used for the verified run): open a task with mode "Flash" and a prompt like:

> Open the app com.sarangupadhye.adya. Get past any onboarding screens (tap Skip or Next as needed) and any sign-in screen or modal (do not sign in - dismiss or ignore it) until you reach the main Today screen. On the Today screen, tap the quick-add text input and type 'Buy milk', then tap the 'Add task' button that appears. Verify the input field is empty afterward and 'Buy milk' appears in the task list.

## Contents

- `stories/` — user stories in JSON
- `generated_tests/` — LLM-generated ARTEMIS test cases (git-tracked, so you can diff/review generation quality over time)
- `scripts/generate_tests.py` — story → test cases via local Ollama
- `scripts/run_tests.py` — test cases → execution via ARTEMIS
- `app/ADYA-release.apk` — the target app build (⚠️ 91MB, `app/DetoxAcademy-debug.apk` also present at 126MB — see note below)

## Note on bundled APKs

Both APKs are committed directly. `DetoxAcademy-debug.apk` is ~126MB, which **exceeds GitHub's 100MB per-file limit**. Before pushing this repo to GitHub, move both to Git LFS:

```bash
git lfs install
git lfs track "*.apk"
git add .gitattributes
git add --renormalize app/
git commit -m "Track APKs via Git LFS"
```
