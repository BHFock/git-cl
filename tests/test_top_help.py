#!/usr/bin/env python3
"""
test_top_help.py – Top-level help flags show usage instead of an error.

Covers:
    git cl --help / git cl -h   – print the top-level usage and exit 0
    git cl help                 – still prints the same overview (unchanged)

Run:
    ./test_top_help.py

Export as shell walkthrough:
    ./test_top_help.py --export > walkthrough_top_help.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo

GIT_CL = str(Path(__file__).parent.parent / "git-cl")


def run_tests(repo: TestRepo):

    # =================================================================
    # --help and -h print usage and succeed
    # =================================================================

    repo.section("Top-level --help shows usage")

    output = repo.run([sys.executable, GIT_CL, "--help"])
    repo.assert_exit_code(0, "git-cl --help should succeed")
    repo.assert_in("git cl <command>", output,
                  "--help should show the top-level usage")

    repo.section("Top-level -h shows usage")

    output = repo.run([sys.executable, GIT_CL, "-h"])
    repo.assert_exit_code(0, "git-cl -h should succeed")
    repo.assert_in("git cl <command>", output,
                  "-h should show the top-level usage")

    # =================================================================
    # The help subcommand keeps working
    # =================================================================

    repo.section("help subcommand still works")

    output = repo.run([sys.executable, GIT_CL, "help"])
    repo.assert_exit_code(0, "git-cl help should succeed")
    repo.assert_in("git cl <command>", output,
                  "help subcommand should show the overview")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_top_help.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: top-level help"))
