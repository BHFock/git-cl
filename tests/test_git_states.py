#!/usr/bin/env python3
"""
test_git_states.py — Test that git-cl correctly displays all Git status codes.

Covers:
    [ M]  Unstaged modification    [M ]  Staged modification
    [MM]  Mixed staged/unstaged    [A ]  Newly added
    [AM]  Added then modified      [ D]  Unstaged deletion
    [D ]  Staged deletion          [??]  Untracked

What you'll learn:
    - git cl status shows the two-character Git status code for each file
    - The first character represents the staging area, the second the working tree
    - All common states are displayed correctly when files are in a changelist

Run:
    ./test_git_states.py

Export as shell walkthrough:
    ./test_git_states.py --export > walkthrough_git_states.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: create files in each of the eight common Git states
    # =================================================================

    repo.section("Setup: create files in all common Git states")

    # Files that need an initial commit
    repo.write_file("unstaged-mod.txt", "original")
    repo.write_file("staged-mod.txt", "original")
    repo.write_file("mixed.txt", "original")
    repo.write_file("del-unstaged.txt", "original")
    repo.write_file("del-staged.txt", "original")
    repo.run("git add unstaged-mod.txt staged-mod.txt mixed.txt "
             "del-unstaged.txt del-staged.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add tracked files"])

    # [ M] unstaged modification
    repo.write_file("unstaged-mod.txt", "modified")

    # [M ] staged modification
    repo.write_file("staged-mod.txt", "modified")
    repo.run("git add staged-mod.txt")

    # [MM] staged then modified again
    repo.write_file("mixed.txt", "staged version")
    repo.run("git add mixed.txt")
    repo.write_file("mixed.txt", "working tree version")

    # [A ] newly added
    repo.write_file("newly-added.txt", "new")
    repo.run("git add newly-added.txt")

    # [AM] added then modified
    repo.write_file("add-then-mod.txt", "initial")
    repo.run("git add add-then-mod.txt")
    repo.write_file("add-then-mod.txt", "modified after add")

    # [ D] unstaged deletion
    repo.delete_file("del-unstaged.txt")

    # [D ] staged deletion
    repo.run("git rm --quiet del-staged.txt")

    # [??] untracked
    repo.write_file("untracked.txt", "untracked content")

    # =================================================================
    # Add all files to one changelist so we can inspect them together
    # =================================================================

    repo.section("Add all files to a changelist")

    repo.run(["git", "cl", "add", "all-states",
              "unstaged-mod.txt", "staged-mod.txt", "mixed.txt",
              "newly-added.txt", "add-then-mod.txt",
              "del-unstaged.txt", "del-staged.txt", "untracked.txt"])
    repo.assert_exit_code(0, "adding files in various states should succeed")

    # =================================================================
    # Test: git cl status shows the correct code for each file
    # =================================================================

    repo.section("Verify status codes in git cl st")

    output = repo.run("git cl st")

    repo.assert_in("[ M] unstaged-mod.txt", output,
                    "[ M] unstaged modification shown correctly")
    repo.assert_in("[M ] staged-mod.txt", output,
                    "[M ] staged modification shown correctly")
    repo.assert_in("[MM] mixed.txt", output,
                    "[MM] mixed staged/unstaged shown correctly")
    repo.assert_in("[A ] newly-added.txt", output,
                    "[A ] newly added shown correctly")
    repo.assert_in("[AM] add-then-mod.txt", output,
                    "[AM] added then modified shown correctly")
    repo.assert_in("[ D] del-unstaged.txt", output,
                    "[ D] unstaged deletion shown correctly")
    repo.assert_in("[D ] del-staged.txt", output,
                    "[D ] staged deletion shown correctly")
    repo.assert_in("[??] untracked.txt", output,
                    "[??] untracked shown correctly")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_git_states.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: git states"))
