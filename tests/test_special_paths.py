#!/usr/bin/env python3
"""
test_special_paths.py — Test file names with spaces, umlauts and quotes.

Covers:
    git cl status    — such files are matched to their changelist
    git cl prune     — changed files with such names are kept
    git cl commit    — a rename between such names is committed as one
    git cl stash     — such files are stashed and restored

What you'll learn:
    - git-cl handles any file name Git does, including spaces and
      non-ASCII characters such as umlauts
    - Git quotes such names in 'git status --porcelain'; git-cl reads the
      unquoted form ('-z'), so the names match the stored paths

Run:
    ./test_special_paths.py

Export as shell walkthrough:
    ./test_special_paths.py --export > walkthrough_special_paths.sh
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo

SPACES = "Meeting Notes.md"
UMLAUT = "Übersicht.md"
NEW_UMLAUT = "neu ä.txt"
RENAMED = "Grüße an alle.txt"
# Windows does not allow double quotes in file names
QUOTES = 'say "hi".txt' if os.name != "nt" else "say hi.txt"


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: commit files with special names
    # =================================================================

    repo.section("Setup: create and commit files with special names")

    for name in [SPACES, UMLAUT, QUOTES, "plain.md"]:
        repo.write_file(name, name)
    repo.run("git add .", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "initial"], check=True)

    repo.write_file(SPACES, "changed")
    repo.write_file(UMLAUT, "changed")
    repo.write_file(NEW_UMLAUT, "new")

    # =================================================================
    # Test: status matches files with spaces and umlauts
    # =================================================================

    repo.section("status matches files with spaces and umlauts")

    repo.run(["git", "cl", "add", "docs", SPACES, UMLAUT])

    output = repo.run("git cl st --no-color")
    repo.assert_in(f"[ M] {SPACES}", output,
                   "file with spaces shown as modified in its changelist")
    repo.assert_in(f"[ M] {UMLAUT}", output,
                   "file with an umlaut shown as modified in its changelist")
    repo.assert_in(f"[??] {NEW_UMLAUT}", output,
                   "untracked file with an umlaut shown readably")
    repo.assert_not_in('"', output.replace(QUOTES, ""),
                       "no quoted paths in the output")
    # Earlier versions showed 'Ü' as the octal escape '\303\234', with
    # the backslashes turned into slashes ('/303/234')
    repo.assert_not_in("303", output, "no octal escapes in the output")

    no_cl = output.split("No Changelist:")[1]
    repo.assert_not_in(SPACES, no_cl,
                       "file with spaces is not listed twice")
    repo.assert_not_in(UMLAUT, no_cl,
                       "file with an umlaut is not listed twice")

    # =================================================================
    # Test: prune keeps changed files with special names
    # =================================================================

    repo.section("prune keeps changed files with special names")

    output = repo.run("git cl prune -n")
    repo.assert_in("Nothing to prune", output,
                   "changed files with special names are not stale")

    # =================================================================
    # Test: stash and unstash files with special names
    # =================================================================

    repo.section("stash and unstash files with special names")

    repo.run("git cl stash docs")
    repo.assert_exit_code(0, "stash succeeds")
    repo.assert_equal(SPACES, repo.read_file(SPACES),
                      "file with spaces reverted while stashed")

    repo.run("git cl unstash docs")
    repo.assert_exit_code(0, "unstash succeeds")
    repo.assert_equal("changed", repo.read_file(UMLAUT),
                      "file with an umlaut restored")

    repo.run(["git", "cl", "commit", "docs", "-m", "Update docs"])

    # =================================================================
    # Test: rename between special names is committed as one rename
    # =================================================================

    repo.section("rename between special names is committed as one rename")

    repo.run(["git", "mv", QUOTES, RENAMED], check=True)
    repo.run(["git", "cl", "add", "rename", QUOTES, RENAMED])

    output = repo.run("git cl st --no-color")
    repo.assert_in(f"[D ] {QUOTES}", output,
                   "old name shown as a staged deletion")
    repo.assert_in(f"[R ] {RENAMED}", output,
                   "new name shown as renamed")
    repo.assert_not_in("Note:", output,
                       "no split-rename note, both sides are found")

    repo.run(["git", "cl", "commit", "rename", "-m", "Rename"])
    output = repo.run(["git", "show", "--name-status", "--format=", "HEAD"])
    repo.assert_in("R100", output, "commit records a rename")


if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_special_paths.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: file names with "
                                    "spaces, umlauts and quotes"))
