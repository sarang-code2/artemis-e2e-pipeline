# artemis-e2e-pipeline

Story → test case → execution pipeline for Android E2E automation, using [google/artemis](https://github.com/google/artemis) to execute against the [DetoxAcademy](../DetoxAcademy) app.

## Flow

```
stories/*.json  --(generate_tests.py, via local Ollama)-->  generated_tests/*.json  --(run_tests.py, via ARTEMIS)--> pass/fail + replays
```

1. **Write a story** as JSON in `stories/` (schema below).
2. **Generate test cases** from it using a local Ollama model — no API key needed.
3. **Execute** the generated test cases against a connected device/emulator via ARTEMIS.

## Story schema

See `stories/login.json` for an example. Fields:

- `id` — unique story id
- `title`, `description` — the user story
- `app`, `screen` — which app/screen this targets
- `acceptance_criteria` — plain-English criteria the generated tests must cover
- `known_elements` — map of logical name → testID, so generated steps can reference real UI elements

## Setup

```bash
# 1. Ollama (test-case generation, local, no API key)
ollama pull llama3.2

# 2. ARTEMIS (execution)
git clone https://github.com/google/artemis.git ../artemis
cd ../artemis && ./start.sh
# then install its Python package into this repo's environment, e.g.:
pip install -e ../artemis   # exact install method TBD — see ARTEMIS README

# 3. This repo's deps
pip install -r requirements.txt
```

## Usage

```bash
# Generate test cases for a story
python scripts/generate_tests.py stories/login.json

# Run them against a device/emulator, installing the bundled APK first
python scripts/run_tests.py generated_tests/US-001.json \
  --device emulator-5554 \
  --mode pro \
  --apk app/DetoxAcademy-debug.apk
```

## Contents

- `stories/` — user stories in JSON
- `generated_tests/` — LLM-generated ARTEMIS test cases (git-tracked, so you can diff/review generation quality over time)
- `scripts/generate_tests.py` — story → test cases via local Ollama
- `scripts/run_tests.py` — test cases → execution via ARTEMIS
- `app/DetoxAcademy-debug.apk` — the target app build (⚠️ 126MB — see note below)

## Note on the bundled APK

`app/DetoxAcademy-debug.apk` is committed directly and is ~126MB, which **exceeds GitHub's 100MB per-file limit**. Before pushing this repo to GitHub, move it to Git LFS:

```bash
git lfs install
git lfs track "*.apk"
git add .gitattributes
git add --renormalize app/DetoxAcademy-debug.apk
git commit -m "Track APK via Git LFS"
```
