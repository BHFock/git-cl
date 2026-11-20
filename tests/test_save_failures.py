#!/usr/bin/env python3
"""
test_save_failures.py — Test that failed metadata writes are reported.

Covers:
    Stash, metadata not saved — exit code 1, changes restored, changelist kept,
                                 also with new files staged in another changelist
    Add, changelist not saved — exit code 1, no success message

What you'll learn:
    - git-cl keeps its changelists in .git/cl.json and its stash records
      in .git/cl-stashes.json
    - If git-cl cannot write these files, the command fails with exit
      code 1 instead of reporting success
    - A stash whose record cannot be saved is undone: your staged and
      unstaged changes, deletions and untracked files are put back as
      they were, and files in other changelists are left alone

The tests run git-cl through fail_write.py, which makes writing one of
these files fail while reading it still works.

Run:
    ./test_save_failures.py

Export as shell walkthrough:
    ./test_save_failures.py --export > walkthrough_save_failures.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo

FAIL_WRITE = str(Path(__file__).parent / "fail_write.py")


def git_cl_failing_write(repo: TestRepo, filename: str, *args: str) -> str:
    """Run git-cl with writes to the given metadata file failing."""
    return repo.run([sys.executable, FAIL_WRITE, filename, *args])


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: staged and unstaged changes and an untracked file
    # =================================================================

    repo.section("Setup: staged, unstaged, deleted and untracked files")

    repo.write_file("alpha.txt", "alpha")
    repo.write_file("beta.txt", "beta")
    repo.write_file("gamma.txt", "gamma")
    repo.run("git add alpha.txt beta.txt gamma.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add alpha, beta and gamma"])
    repo.write_file("alpha.txt", "alpha staged")
    repo.run("git add alpha.txt")
    repo.write_file("alpha.txt", "alpha staged and unstaged")
    repo.write_file("beta.txt", "beta v2")
    repo.delete_file("gamma.txt")
    repo.write_file("new.txt", "untracked")
    repo.write_file("other.txt", "staged new file in another changelist")
    repo.run("git add other.txt")

    repo.run("git cl add feature alpha.txt gamma.txt new.txt")
    repo.assert_exit_code(0, "add succeeds")
    repo.run("git cl add other other.txt")
    repo.assert_exit_code(0, "add to second changelist succeeds")

    status_before = repo.run("git status --porcelain")

    # =================================================================
    # Test: Stash fails when its record cannot be saved
    # =================================================================

    repo.section("Stash: record cannot be saved")

    git_cl_failing_write(repo, "cl-stashes.json", "stash", "feature")
    repo.assert_exit_code(1, "stash fails")
    repo.assert_in("Could not save the stash", repo.last_stderr,
                   "failure reported on stderr")
    repo.assert_in("Your changes have been restored", repo.last_stderr,
                   "restoration reported")
    repo.assert_not_in("Successfully stashed", repo.last_stdout,
                       "no success message")

    repo.assert_equal(status_before, repo.run("git status --porcelain"),
                      "staged, unstaged, deleted and untracked files as before")
    repo.assert_equal("", repo.run("git stash list"),
                      "no stash left behind")
    repo.assert_equal(["alpha.txt", "gamma.txt", "new.txt"],
                      repo.load_cl_json().get("feature"),
                      "changelist 'feature' still active")

    # =================================================================
    # Test: Add fails when the changelists cannot be saved
    # =================================================================

    repo.section("Add: changelists cannot be saved")

    git_cl_failing_write(repo, "cl.json", "add", "other", "beta.txt")
    repo.assert_exit_code(1, "add fails")
    repo.assert_in("Error saving changelists", repo.last_stderr,
                   "failure reported on stderr")
    repo.assert_not_in("Added to", repo.last_stdout,
                       "no success message")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_save_failures.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell(
                "git-cl walkthrough: failed metadata writes"))
