#!/usr/bin/env python3
"""
test_diff.py — Test viewing diffs for changelists.

Covers:
    git cl diff <name>               — show diff for one changelist
    git cl diff <name1> <name2>      — show combined diff for multiple changelists
    git cl diff <name> --staged      — show only staged changes in a changelist

What you'll learn:
    - git cl diff shows only the changes for files in the named changelist
    - You can diff multiple changelists at once
    - The --staged flag filters to changes that have been staged (git add)
    - Unstaged changes are excluded from --staged output

Run:
    ./test_diff.py

Export as shell walkthrough:
    ./test_diff.py --export > walkthrough_diff.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: create files and modify them
    # =================================================================

    repo.section("Setup: create files with modifications")

    repo.write_file("alpha.txt", "alpha")
    repo.write_file("beta.txt", "beta")
    repo.write_file("gamma.txt", "gamma")
    repo.run("git add alpha.txt beta.txt gamma.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add alpha, beta, gamma"])

    # Modify all three files
    repo.write_file("alpha.txt", "alpha v2")
    repo.write_file("beta.txt", "beta v2")
    repo.write_file("gamma.txt", "gamma v2")

    # Assign to two changelists
    repo.run("git cl add list-a alpha.txt")
    repo.run("git cl add list-b beta.txt gamma.txt")

    # =================================================================
    # Test: Diff a single changelist
    # =================================================================

    repo.section("Diff a single changelist")

    output = repo.run("git cl diff list-a")
    repo.assert_exit_code(0, "git cl diff should succeed")
    repo.assert_in("alpha.txt", output,
                    "diff output includes alpha.txt changes")
    repo.assert_not_in("beta.txt", output,
                        "diff output does not include beta.txt")
    repo.assert_not_in("gamma.txt", output,
                        "diff output does not include gamma.txt")

    # =================================================================
    # Test: Diff multiple changelists
    # =================================================================

    repo.section("Diff multiple changelists")

    output = repo.run("git cl diff list-a list-b")
    repo.assert_exit_code(0, "git cl diff with multiple lists should succeed")
    repo.assert_in("alpha.txt", output,
                    "combined diff includes alpha.txt")
    repo.assert_in("beta.txt", output,
                    "combined diff includes beta.txt")
    repo.assert_in("gamma.txt", output,
                    "combined diff includes gamma.txt")

    # =================================================================
    # Test: Diff with --staged flag
    # =================================================================
    # Stage only list-a. The --staged flag should show the staged changes
    # for list-a but not the unstaged changes for list-b.

    repo.section("Diff with --staged flag")

    repo.run("git cl stage list-a")

    output = repo.run("git cl diff list-a --staged")
    repo.assert_exit_code(0, "git cl diff --staged should succeed")
    repo.assert_in("alpha.txt", output,
                    "staged diff includes alpha.txt")

    # list-b was not staged, so --staged should not show its changes
    output = repo.run("git cl diff list-b --staged")
    repo.assert_not_in("beta.txt", output,
                        "unstaged changes not in --staged diff")

    # =================================================================
    # Test: Diff a changelist with no changes
    # =================================================================
    # After committing list-a, its files are clean — diff should be empty.

    repo.section("Diff a changelist with no changes")

    repo.run(["git", "commit", "--quiet", "-m", "Commit staged alpha"])

    output = repo.run("git cl diff list-a")
    repo.assert_exit_code(0, "diffing clean changelist should succeed")
    repo.assert_not_in("alpha.txt", output,
                        "no diff output for committed file")

    # =================================================================
    # Test: Diff a non-existent changelist
    # =================================================================

    repo.section("Diff a non-existent changelist")

    output = repo.run("git cl diff no-such-list")
    repo.assert_in("no-such-list", output,
                    "error message mentions the changelist name")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_diff.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: diff"))
