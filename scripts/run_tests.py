#!/usr/bin/env python3
"""Execute a generated test-case JSON file against a connected Android device/emulator using ARTEMIS."""
import argparse
import json
from pathlib import Path

from artemis import Agent  # provided by the artemis package once installed


def run_file(test_file: Path, device: str, mode: str, apk: Path | None):
    data = json.loads(test_file.read_text())
    agent = Agent(device=device, mode=mode)

    if apk:
        agent.install(str(apk))

    results = []
    for case in data["test_cases"]:
        steps_text = "; then ".join(case["steps"])
        instruction = f"{steps_text}. Finally verify: {case['expected']}"
        print(f"Running: {case['name']}")
        result = agent.run(instruction)
        results.append({"name": case["name"], "success": result.success, "details": getattr(result, "details", None)})
        print(f"  -> {'PASS' if result.success else 'FAIL'}")

    agent.close()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("test_file", type=Path, help="Path to a generated_tests/<id>.json file")
    parser.add_argument("--device", default="emulator-5554", help="ADB device serial")
    parser.add_argument("--mode", default="pro", choices=["flash", "pro"], help="ARTEMIS execution mode")
    parser.add_argument("--apk", type=Path, default=None, help="APK to install before running (e.g. app/DetoxAcademy-debug.apk)")
    args = parser.parse_args()

    results = run_file(args.test_file, args.device, args.mode, args.apk)
    failed = [r for r in results if not r["success"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
