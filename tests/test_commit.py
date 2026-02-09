#!/usr/bin/env python3
"""
test_commit.py — Test committing changelists.

Covers:
    git cl commit <n> -m "msg"     — commit with inline message
    git cl commit <n> -F file      — commit with message from file
    git cl commit <n> -m "msg" --keep  — commit but keep the changelist
    git cl ci                         — alias for commit

What you'll learn:
    - git cl commit stages and commits tracked files in one step
    - Untracked files ([??]) in the changelist are skipped
    - The changelist is DELETED after commit by default (opposite of stage)
    - Use --keep to preserve the changelist after committing
    - The commit message can come from -m or from a file via -F

Run:
    ./test_commit.py

Export as shell walkthrough:
    ./test_commit.py --export > walkthrough_commit.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: create tracked files and an untracked file
    # =================================================================

    repo.section("Setup: create tracked and untracked files")

    repo.write_file("file1.txt", "original 1")
    repo.write_file("file2.txt", "original 2")
    repo.write_file("file3.txt", "original 3")
    repo.run("git add file1.txt file2.txt file3.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add files"])

    # =================================================================
    # Test: Commit with -m (changelist deleted by default)
    # =================================================================

    repo.section("Commit a changelist with -m")

    repo.write_file("file1.txt", "modified 1")
    repo.run("git cl add bugfix file1.txt")

    # Also modify file2.txt but put it in a different changelist
    repo.write_file("file2.txt", "modified 2")
    repo.run("git cl add other file2.txt")

    output = repo.run(["git", "cl", "commit", "bugfix", "-m", "Fix the bug"])
    repo.assert_exit_code(0, "git cl commit should succeed")

    # Verify the commit appeared in the log
    log = repo.get_git_log_oneline()
    repo.assert_in("Fix the bug", log, "commit message appears in git log")

    # file1.txt should be clean now (committed)
    status = repo.run("git status --porcelain file1.txt")
    repo.assert_equal("", status, "file1.txt is clean after commit")

    # The changelist should be deleted (default behaviour)
    cl = repo.load_cl_json()
    repo.assert_true("bugfix" not in cl,
                     "changelist deleted after commit (default)")

    # file2.txt should still be modified (different changelist, not committed)
    status = repo.run("git status --porcelain file2.txt")
    repo.assert_in("M", status,
                   "file2.txt remains modified (not committed)")

    # =================================================================
    # Test: Commit with -F (message from file)
    # =================================================================

    repo.section("Commit a changelist with -F")

    repo.write_file("commit-msg.txt", "Message from file")
    output = repo.run(["git", "cl", "commit", "other", "-F", "commit-msg.txt"])
    repo.assert_exit_code(0, "git cl commit -F should succeed")

    log = repo.get_git_log_oneline()
    repo.assert_in("Message from file", log,
                   "commit message from file appears in git log")

    # =================================================================
    # Test: Commit with --keep flag
    # =================================================================

    repo.section("Commit with --keep flag")

    repo.write_file("file3.txt", "modified 3")
    repo.run("git cl add refactor file3.txt")

    output = repo.run(["git", "cl", "commit", "refactor", "-m",
                       "Refactor work", "--keep"])
    repo.assert_exit_code(0, "git cl commit --keep should succeed")

    log = repo.get_git_log_oneline()
    repo.assert_in("Refactor work", log, "commit appears in log")

    cl = repo.load_cl_json()
    repo.assert_true("refactor" in cl,
                     "changelist preserved with --keep")

    # =================================================================
    # Test: Untracked files are skipped during commit
    # =================================================================

    repo.section("Untracked files are skipped during commit")

    repo.write_file("file1.txt", "changed again")
    repo.write_file("newfile.txt", "brand new")

    repo.run("git cl add mixed file1.txt newfile.txt")

    output = repo.run(["git", "cl", "commit", "mixed", "-m", "Mixed commit"])
    repo.assert_exit_code(0, "commit with mixed tracked/untracked should succeed")

    # newfile.txt should still be untracked
    status = repo.run("git status --porcelain newfile.txt")
    repo.assert_in("??", status,
                   "newfile.txt remains untracked after commit")

    # file1.txt should be committed
    status = repo.run("git status --porcelain file1.txt")
    repo.assert_equal("", status, "file1.txt is clean after commit")

    # =================================================================
    # Test: 'ci' alias works
    # =================================================================

    repo.section("'ci' alias works")

    repo.write_file("file1.txt", "alias modification")
    repo.run("git cl add alias-test file1.txt")

    output = repo.run(["git", "cl", "ci", "alias-test", "-m", "Via ci alias"])
    repo.assert_exit_code(0, "git cl ci should succeed")

    log = repo.get_git_log_oneline()
    repo.assert_in("Via ci alias", log,
                   "commit via 'ci' alias appears in log")

    # =================================================================
    # Test: Commit a non-existent changelist
    # =================================================================

    repo.section("Commit a non-existent changelist")

    output = repo.run(["git", "cl", "commit", "no-such-list",
                       "-m", "Should fail"])
    repo.assert_in("no-such-list", output,
                   "error message mentions the changelist name")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_commit.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: commit"))
