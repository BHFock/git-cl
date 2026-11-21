#!/usr/bin/env python3
"""
test_submodules.py — Test how git-cl treats submodules.

Covers:
    git cl add <submodule>               — refused, like a directory
    git cl add <submodule>/<file>        — refused, the file is in another repository
    git cl br, changes inside submodule  — not blocked, they belong to the submodule
    git cl br, new submodule commit      — blocked, with a hint to commit or reset it

What you'll learn:
    - A submodule is a separate repository. This repository only records
      which commit of it is checked out.
    - Changelists contain files only, so a submodule cannot be added,
      just like a directory. To group files inside a submodule, run
      git cl in the submodule.
    - Uncommitted changes inside a submodule do not stop git cl branch.
      A new commit in the submodule does, because the changed pointer
      would otherwise move to the new branch unnoticed.

The submodule here is a nested repository added with 'git add', which
records it the same way as 'git submodule add' (a gitlink), without
needing a second repository to clone from.

Run:
    ./test_submodules.py

Export as shell walkthrough:
    ./test_submodules.py --export > walkthrough_submodules.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: a repository with a submodule
    # =================================================================

    repo.section("Setup: repository with a submodule")

    repo.write_file("main.txt", "main")
    repo.run("git add main.txt", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add main"], check=True)

    repo.mkdir("sub")
    repo.run("git -C sub init --quiet", check=True)
    repo.run("git -C sub config user.email test@example.com", check=True)
    repo.run("git -C sub config user.name Test", check=True)
    repo.write_file("sub/inner.txt", "inner")
    repo.run("git -C sub add inner.txt", check=True)
    repo.run(["git", "-C", "sub", "commit", "--quiet", "-m", "Add inner"],
             check=True)
    repo.run("git add sub", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add submodule"], check=True)

    # =================================================================
    # Test: A submodule cannot be added to a changelist
    # =================================================================

    repo.section("A submodule cannot be added to a changelist")

    repo.run("git cl add feature sub")
    repo.assert_exit_code(1, "adding the submodule fails")
    repo.assert_in("is a submodule", repo.last_stderr,
                   "the submodule is named as such")

    repo.run("git cl add feature sub/inner.txt")
    repo.assert_exit_code(1, "adding a file inside the submodule fails")
    repo.assert_in("inside the submodule", repo.last_stderr,
                   "the file is named as inside the submodule")
    repo.assert_true("feature" not in repo.load_cl_json(),
                     "no changelist was created")

    # =================================================================
    # Test: Changes inside a submodule do not block git cl branch
    # =================================================================

    repo.section("Changes inside a submodule do not block git cl branch")

    repo.write_file("main.txt", "main changed")
    repo.run("git cl add feature main.txt")
    repo.write_file("sub/inner.txt", "inner changed, not committed")

    repo.run("git cl branch feature feature-branch")
    repo.assert_exit_code(0, "branch succeeds")
    repo.assert_equal("feature-branch", repo.get_current_branch(),
                      "on the new branch")
    repo.assert_true("feature" in repo.load_cl_json(),
                     "the changelist is restored on the new branch")

    # =================================================================
    # Test: A new submodule commit blocks git cl branch
    # =================================================================

    repo.section("A new submodule commit blocks git cl branch")

    repo.run(["git", "-C", "sub", "commit", "--quiet", "-am", "Change inner"],
             check=True)

    repo.run("git cl branch feature second-branch")
    repo.assert_exit_code(1, "branch fails")
    repo.assert_in("Submodules point to a new commit", repo.last_stderr,
                   "the submodule commit is explained")
    repo.assert_in("git add sub", repo.last_stderr,
                   "the hint shows how to record it")
    repo.assert_equal("feature-branch", repo.get_current_branch(),
                      "still on the previous branch")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_submodules.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: submodules"))
