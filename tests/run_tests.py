#!/usr/bin/env python3
"""
run_tests.py — Discover and run all git-cl test scripts.

Finds every test_*.py file in the same directory, runs each as a
subprocess, and prints a summary of results.

Usage:
    ./run_tests.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    test_dir = Path(__file__).parent
    scripts = sorted(
        s for s in test_dir.glob("test_*.py")
        if s.name != "test_helpers.py"
    )

    if not scripts:
        print("No test scripts found.")
        sys.exit(1)

    # Print environment info
    print("git-cl Test Suite")
    print("=" * 45)
    for cmd, label in [
        ("git cl --version", "git-cl version"),
        ("python3 --version", "Python version"),
        ("git --version", "Git version"),
    ]:
        result = subprocess.run(
            cmd.split(), capture_output=True, text=True
        )
        output = result.stdout.strip() or result.stderr.strip()
        print(f"{label:>16}: {output}")
    print("=" * 45)

    passed = []
    failed = []

    for script in scripts:
        name = script.stem
        print(f"\n{'=' * 3} Running: {name} {'=' * 3}")

        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=test_dir,
        )

        if result.returncode == 0:
            passed.append(name)
            print(f">>> {name}: PASSED")
        else:
            failed.append(name)
            print(f">>> {name}: FAILED")

    # Summary
    print(f"\n{'=' * 45}")
    print(f"Final Summary")
    print(f"{'=' * 45}")
    print(f"Scripts run:  {len(passed) + len(failed)}")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")

    if failed:
        print(f"\nFailed scripts:")
        for name in failed:
            print(f"  - {name}")

    print(f"{'=' * 45}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
