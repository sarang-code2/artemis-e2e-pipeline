#!/usr/bin/env python3
"""Turn a user-story JSON file into an ARTEMIS test-case JSON file, using a local Ollama model."""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2"

PROMPT_TEMPLATE = """You are a QA engineer writing mobile E2E test cases for an Android app automation tool (ARTEMIS), which executes natural-language steps against the app's UI.

Given this user story (JSON), produce test cases as a JSON array. Each test case must have:
- "name": short test case name
- "steps": array of plain-English instructions ARTEMIS can execute one at a time (e.g. "tap the element with testID login-username-input and type 'jane'")
- "expected": plain-English assertion of what should be true at the end

Cover the happy path, the error path, and any validation/disabled-state cases implied by the acceptance criteria. Use the known_elements testIDs in your steps where relevant.

Return ONLY a raw JSON array, no prose, no markdown fences.

User story:
{story_json}
"""


def call_ollama(prompt: str, model: str) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read())
    return body["response"]


def extract_json_array(text: str) -> list:
    text = text.strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in model output:\n{text}")
    return json.loads(match.group(0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("story", type=Path, help="Path to a story JSON file, e.g. stories/login.json")
    parser.add_argument("-o", "--out", type=Path, default=None, help="Output path (default: generated_tests/<story-id>.json)")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"Ollama model to use (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    story = json.loads(args.story.read_text())
    prompt = PROMPT_TEMPLATE.format(story_json=json.dumps(story, indent=2))

    print(f"Generating test cases for '{story.get('title', story.get('id'))}' using {args.model}...", file=sys.stderr)
    raw = call_ollama(prompt, args.model)
    try:
        test_cases = extract_json_array(raw)
    except (ValueError, json.JSONDecodeError):
        debug_path = Path("generated_tests") / f"{story['id']}.raw.txt"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(raw)
        print(f"Failed to parse model output as JSON. Raw output saved to {debug_path}", file=sys.stderr)
        raise

    out_path = args.out or Path("generated_tests") / f"{story['id']}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "story_id": story["id"],
        "app": story.get("app"),
        "screen": story.get("screen"),
        "test_cases": test_cases,
    }
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Wrote {len(test_cases)} test case(s) to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
