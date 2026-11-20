#!/usr/bin/env python3
"""
test_corrupt_metadata.py — Test that damaged metadata files are kept.

Covers:
    Truncated cl.json          — commands stop with exit code 1, file unchanged
    Wrongly shaped cl.json     — clear error instead of a Python traceback
    Damaged cl-stashes.json    — stash and unstash stop, file and files unchanged
    Empty cl.json              — treated as no changelists
    Moving the file aside      — git-cl starts afresh

What you'll learn:
    - git-cl keeps its changelists in .git/cl.json and its stash records
      in .git/cl-stashes.json
    - If one of these files is damaged, git-cl stops instead of carrying
      on with empty data, which would overwrite the file and lose its
      content
    - The error message says how to recover: repair the file, or move it
      aside and start without it

Run:
    ./test_corrupt_metadata.py

Export as shell walkthrough:
    ./test_corrupt_metadata.py --export > walkthrough_corrupt_metadata.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: two changelists
    # =================================================================

    repo.section("Setup: two changelists")

    repo.write_file("alpha.txt", "alpha")
    repo.write_file("beta.txt", "beta")
    repo.write_file("gamma.txt", "gamma")
    repo.run("git add alpha.txt beta.txt gamma.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add files"])
    repo.write_file("alpha.txt", "alpha modified")
    repo.write_file("beta.txt", "beta modified")
    repo.write_file("gamma.txt", "gamma modified")

    repo.run("git cl add one alpha.txt")
    repo.run("git cl add two beta.txt")
    intact = repo.read_file(".git/cl.json")

    # =================================================================
    # Test: Truncated cl.json is not overwritten
    # =================================================================

    repo.section("Truncated cl.json")

    truncated = intact[:len(intact) // 2]
    repo.write_file(".git/cl.json", truncated)

    repo.run("git cl add three gamma.txt")
    repo.assert_exit_code(1, "add stops")
    repo.assert_in("not valid JSON", repo.last_stderr, "reason reported")
    repo.assert_in("cl.json.broken", repo.last_stderr,
                   "recovery hint shown")
    repo.assert_not_in("Added to", repo.last_stdout, "no success message")
    repo.assert_equal(truncated, repo.read_file(".git/cl.json"),
                      "cl.json unchanged")

    repo.run("git cl status")
    repo.assert_exit_code(1, "status stops")

    # =================================================================
    # Test: Wrongly shaped cl.json gives an error, not a traceback
    # =================================================================

    repo.section("Wrongly shaped cl.json")

    for content in ('[]', 'null', '{"one": "alpha.txt"}', '{"one": [1]}'):
        repo.write_file(".git/cl.json", content)
        repo.run("git cl status")
        repo.assert_exit_code(1, f"status stops for {content}")
        repo.assert_not_in("Traceback", repo.last_stderr,
                           f"no traceback for {content}")

    # =================================================================
    # Test: Empty cl.json counts as no changelists
    # =================================================================

    repo.section("Empty cl.json")

    repo.write_file(".git/cl.json", "")
    repo.run("git cl status")
    repo.assert_exit_code(0, "status succeeds")

    # =================================================================
    # Test: Damaged cl-stashes.json stops stash and unstash
    # =================================================================

    repo.section("Damaged cl-stashes.json")

    repo.write_file(".git/cl.json", intact)
    repo.run("git cl stash two")
    repo.assert_exit_code(0, "stash two succeeds")

    repo.write_file(".git/cl-stashes.json", '{"two": {"files": "beta.txt"}}')
    status_before = repo.run("git status --porcelain")

    repo.run("git cl stash one")
    repo.assert_exit_code(1, "stash stops")
    repo.assert_in("'git stash list'", repo.last_stderr,
                   "hint says where the stashed changes are")
    repo.run("git cl unstash two")
    repo.assert_exit_code(1, "unstash stops")

    repo.assert_equal(status_before, repo.run("git status --porcelain"),
                      "working directory unchanged")
    repo.assert_equal('{"two": {"files": "beta.txt"}}',
                      repo.read_file(".git/cl-stashes.json"),
                      "cl-stashes.json unchanged")

    # =================================================================
    # Test: Moving the file aside lets git-cl start afresh
    # =================================================================

    repo.section("Move the damaged file aside")

    # Moving a file aside: a copy under the new name, then delete the original
    repo.write_file(".git/cl.json.broken", truncated)
    repo.delete_file(".git/cl.json")
    repo.run("git cl add three gamma.txt")
    repo.assert_exit_code(1, "still stops while cl-stashes.json is damaged")

    repo.write_file(".git/cl-stashes.json.broken",
                    repo.read_file(".git/cl-stashes.json"))
    repo.delete_file(".git/cl-stashes.json")
    repo.run("git cl add three gamma.txt")
    repo.assert_exit_code(0, "add succeeds once both files are moved aside")
    repo.assert_equal({"three": ["gamma.txt"]}, repo.load_cl_json(),
                      "git-cl starts without the old changelists")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_corrupt_metadata.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell(
                "git-cl walkthrough: damaged metadata files"))
