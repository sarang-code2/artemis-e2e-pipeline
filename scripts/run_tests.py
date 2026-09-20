#!/usr/bin/env python3
"""Execute a generated test-case JSON file against a running ARTEMIS host.

Requires ARTEMIS's own server to already be running (`./start.sh` in the
artemis repo, serving at http://127.0.0.1:8000 by default) with a device
connected - this script is a client of that host, it does not start ARTEMIS
itself.
"""
import argparse
import asyncio
import json
import os
import subprocess
from pathlib import Path

from artemis_client import ArtemisClient


def install_apk(apk: Path, device: str) -> None:
    subprocess.run(["adb", "-s", device, "install", "-r", str(apk)], check=True)


async def run_file(test_file: Path, device: str, mode: str, apk: Path | None, base_url: str) -> list[dict]:
    data = json.loads(test_file.read_text())

    if apk:
        install_apk(apk, device)

    client = ArtemisClient(base_url, token=os.environ.get("ARTEMIS_TOKEN"))
    results = []
    for case in data["test_cases"]:
        steps_text = "; then ".join(case["steps"])
        instruction = f"{steps_text}. Finally verify: {case['expected']}"
        print(f"Running: {case['name']}")
        result = await client.run(instruction, profile=mode, device_serial=device)
        results.append({"name": case["name"], "success": result.succeeded, "error": result.error})
        print(f"  -> {'PASS' if result.succeeded else 'FAIL'}" + (f" ({result.error})" if result.error else ""))

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("test_file", type=Path, help="Path to a generated_tests/<id>.json file")
    parser.add_argument("--device", default="emulator-5554", help="ADB device serial")
    parser.add_argument("--mode", default="flash", choices=["flash", "pro"], help="ARTEMIS execution profile (flash uses far fewer LLM calls - prefer it on the Gemini free tier)")
    parser.add_argument("--apk", type=Path, default=None, help="APK to install before running (e.g. app/ADYA-release.apk)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Running ARTEMIS host URL")
    args = parser.parse_args()

    results = asyncio.run(run_file(args.test_file, args.device, args.mode, args.apk, args.base_url))
    failed = [r for r in results if not r["success"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
