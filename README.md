# artemis-e2e-pipeline

Story → test case → execution pipeline for Android E2E automation, using [google/artemis](https://github.com/google/artemis) to execute against the [ADYA](../ADYA) app (`com.sarangupadhye.adya`).

## Flow

```
stories/*.json  --(generate_tests.py, via local Ollama)-->  generated_tests/*.json  --(run_tests.py, via ARTEMIS)--> pass/fail + replays
```

1. **Write a story** as JSON in `stories/` (schema below).
2. **Generate test cases** from it using a local Ollama model — no API key needed.
3. **Execute** the generated test cases against a connected device/emulator via ARTEMIS.

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
# 1. Ollama (test-case generation + ARTEMIS perception, local, no API key)
ollama pull moondream   # small, broadly-compatible vision model
# (llama3.2-vision was tried first but its 'mllama' architecture isn't
# loadable by current Ollama server builds - see LLMExhaustedError in
# ../artemis/traces/*/stdout.log if you hit this again)

# 2. ARTEMIS (execution) - already cloned as a sibling repo at ../artemis
cd ../artemis
export UV_HTTP_TIMEOUT=120
uv sync
uv pip install -e packages/artemis-client --python .venv/bin/python  # workaround for a stale workspace editable install
./start.sh
# In the console (http://localhost:8000), choose "Custom Configuration"
# under AI Model Setup - it reads ../artemis/config/artemis.jsonc, already
# pointed at ollama/moondream.

# 3. This repo's deps
pip install -r requirements.txt
```

## Usage

```bash
# Generate test cases for a story
python scripts/generate_tests.py stories/add_task.json

# Run them against a device/emulator, installing the bundled APK first
python scripts/run_tests.py generated_tests/US-001.json \
  --device emulator-5554 \
  --mode pro \
  --apk app/ADYA-release.apk
```

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
