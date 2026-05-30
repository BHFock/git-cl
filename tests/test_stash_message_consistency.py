#!/usr/bin/env python3
"""
test_stash_message_consistency.py — Test that the stash message stored in
cl-stashes.json matches the message git actually recorded.

Regression guard for the bug where clutil_create_unique_stash_message was
called twice for a single stash — once for `git stash push -m` and once when
building the metadata — each call producing its own timestamp. If the two
calls straddled a one-second boundary, the `stash_message` persisted in
cl-stashes.json would not match the message stored in git's stash list.

The fix generates the message once in cl_stash and threads it through both
paths, so the two can never diverge.

Note on determinism:
    Because the divergence only occurs across a second boundary, this
    integration test cannot *reliably* reproduce the original bug — both
    timestamps almost always land in the same second, so even the buggy code
    usually produced matching strings. The test's value is as an INVARIANT
    GUARD: after the fix, the stored message is guaranteed to equal git's, and
    this test pins that. It will catch any future regression that reintroduces
    a second, independently generated message, or that lets the message format
    drift between the two call sites. Deterministic reproduction of the timing
    bug itself would require injecting a clock, which the subprocess-based test
    framework does not support.

Covers:
    git cl stash <name>   — stored stash_message matches git's actual stash
    git cl stash --all    — every stored message matches git's actual stash

Run:
    ./test_stash_message_consistency.py

Export as shell walkthrough:
    ./test_stash_message_consistency.py --export > walkthrough_stash_message.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Setup: a tracked modification assigned to a changelist
    # =================================================================

    repo.section("Setup: a tracked modification in a changelist")

    repo.write_file("file1.txt", "original")
    repo.run("git add file1.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add file1"])
    repo.write_file("file1.txt", "modified")
    repo.run("git cl add list-a file1.txt")

    # =================================================================
    # Test: single stash — stored message matches git's stash message
    # =================================================================

    repo.section("Single stash: stored message matches git's stash")

    output = repo.run("git cl stash list-a")
    repo.assert_exit_code(0, "git cl stash should succeed")

    stash = repo.load_stash_json()
    repo.assert_true("list-a" in stash,
                     "list-a recorded in stash metadata")

    stored_msg = stash["list-a"].get("stash_message", "")
    repo.assert_true(
        stored_msg.startswith("git-cl-stash:list-a:"),
        "stored message carries the expected git-cl-stash prefix")

    # The invariant: the message persisted in cl-stashes.json must be the
    # exact message git recorded for the stash. `git stash list` shows the
    # custom -m message, so the stored string must appear verbatim within it.
    git_stash_list = repo.run("git stash list")
    repo.assert_in(
        stored_msg, git_stash_list,
        "stored stash_message matches git's actual stash list entry")

    # =================================================================
    # Test: stash --all — every stored message matches git's
    # =================================================================
    # Exercises the loop path (clutil_stash_all_changelists -> cl_stash per
    # changelist), confirming each metadata message lines up with git.

    repo.section("stash --all: every stored message matches git")

    # Restore the first changelist so we have a clean slate.
    repo.run("git cl unstash list-a")

    repo.write_file("file2.txt", "original2")
    repo.run("git add file2.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add file2"])

    repo.write_file("file1.txt", "mod1")
    repo.write_file("file2.txt", "mod2")
    repo.run("git cl add list-a file1.txt")
    repo.run("git cl add list-b file2.txt")

    output = repo.run("git cl stash --all")
    repo.assert_exit_code(0, "git cl stash --all should succeed")

    stash = repo.load_stash_json()
    git_stash_list = repo.run("git stash list")

    for name in ("list-a", "list-b"):
        repo.assert_true(name in stash, f"{name} recorded in stash metadata")
        msg = stash[name].get("stash_message", "")
        repo.assert_true(
            msg.startswith(f"git-cl-stash:{name}:"),
            f"{name}: stored message carries the expected prefix")
        repo.assert_in(
            msg, git_stash_list,
            f"{name}: stored stash_message matches git's actual stash entry")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_stash_message_consistency.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell(
                "git-cl walkthrough: stash message consistency"))
