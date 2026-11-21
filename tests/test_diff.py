#!/usr/bin/env python3
"""
test_diff.py — Test viewing diffs for changelists.

Covers:
    git cl diff <name>               — show diff for one changelist
    git cl diff <name1> <name2>      — show combined diff for multiple changelists
    git cl diff <name> --staged      — show only staged changes in a changelist
    git cl diff <name> --both        — staged and unstaged changes in two sections
    Deleted files                    — shown as deletions, staged and unstaged
    A failing git diff               — reported, exit code 1

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
    # Test: Deleted files are shown as deletions
    # =================================================================

    repo.section("Deleted files are shown as deletions")

    repo.write_file("delta.txt", "delta")
    repo.write_file("epsilon.txt", "epsilon")
    repo.write_file("zeta.txt", "zeta")
    repo.run("git add delta.txt epsilon.txt zeta.txt", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add delta, epsilon, zeta"],
             check=True)
    repo.delete_file("delta.txt")                       # unstaged deletion
    repo.run("git rm --quiet epsilon.txt", check=True)  # staged deletion
    repo.write_file("zeta.txt", "zeta staged")          # staged and unstaged
    repo.run("git add zeta.txt", check=True)
    repo.write_file("zeta.txt", "zeta staged and unstaged")
    repo.run("git cl add removed delta.txt epsilon.txt zeta.txt")

    output = repo.run("git cl diff removed")
    repo.assert_exit_code(0, "diff succeeds")
    repo.assert_in("deleted file", output, "unstaged deletion is shown")
    repo.assert_in("a/delta.txt", output, "delta.txt is in the diff")
    repo.assert_not_in("does not exist", repo.last_stderr,
                       "deleted files are not reported as missing")

    output = repo.run("git cl diff removed --staged")
    repo.assert_exit_code(0, "diff --staged succeeds")
    repo.assert_in("a/epsilon.txt", output, "staged deletion is shown")

    output = repo.run("git cl diff removed --both")
    repo.assert_exit_code(0, "diff --both succeeds")
    unstaged, _, staged = output.partition("=== Staged changes")
    repo.assert_in("+zeta staged and unstaged", unstaged,
                   "the unstaged part of zeta.txt is in the first section")
    repo.assert_in("+zeta staged", staged,
                   "the staged part of zeta.txt is in the second section")
    repo.assert_not_in("zeta staged and unstaged", staged,
                       "the unstaged part is not in the staged section")

    # =================================================================
    # Test: A failing git diff is reported
    # =================================================================

    # A damaged index makes git diff fail. git-cl's own metadata is not
    # affected, so only the diff itself goes wrong.

    repo.section("A failing git diff is reported")

    index = repo.repo_dir / ".git" / "index"
    saved_index = index.read_bytes()
    index.write_bytes(b"not an index")

    repo.run("git cl diff removed")
    repo.assert_exit_code(1, "diff fails")
    repo.assert_in("git diff failed", repo.last_stderr,
                   "the failure is reported")

    repo.run("git cl diff removed --both")
    repo.assert_exit_code(1, "diff --both fails")
    repo.assert_in("git diff failed", repo.last_stderr,
                   "the failing unstaged diff is reported")
    repo.assert_in("git diff --staged failed", repo.last_stderr,
                   "the failing staged diff is reported as well")

    index.write_bytes(saved_index)


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
