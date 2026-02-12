#!/usr/bin/env python3
"""
test_edge_cases.py — Test boundary conditions and unusual states.

Covers:
    Empty states      — no changelists, clean files in changelists
    Reassignment      — rapid add/remove cycles, file moves between changelists
    Duplicate files   — adding the same file twice in one command
    Deleted files     — adding a deleted file to a changelist
    Commit edge cases — committing a changelist with only untracked files

What you'll learn:
    - git cl status produces no output when there are no changelists
    - Clean (unchanged) files show as [  ] in status
    - A file can only belong to one changelist — reassignment is automatic
    - Adding the same file twice in one command deduplicates
    - Committing a changelist with only untracked files does nothing harmful

Run:
    ./test_edge_cases.py

Export as shell walkthrough:
    ./test_edge_cases.py --export > walkthrough_edge_cases.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Test: Status with no changelists
    # =================================================================

    repo.section("Status with no changelists")

    repo.write_file("file.txt", "content")
    repo.run("git add file.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add file"])
    repo.write_file("file.txt", "modified")

    output = repo.run("git cl st")
    repo.assert_exit_code(0, "status with no changelists should succeed")

    # With no changelists, modified files appear under No Changelist
    repo.assert_in("No Changelist:", output,
                    "unassigned files shown under No Changelist")

    # =================================================================
    # Test: Clean (unchanged) file in a changelist
    # =================================================================

    repo.section("Clean file in a changelist shows [  ]")

    # Reset the file to clean state
    repo.run("git checkout -- file.txt")

    repo.run("git cl add my-list file.txt")
    output = repo.run("git cl st")
    repo.assert_in("[  ] file.txt", output,
                    "clean file shows as [  ]")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Rapid reassignment between changelists
    # =================================================================

    repo.section("Rapid reassignment between changelists")

    repo.write_file("file.txt", "modified")

    repo.run("git cl add list-a file.txt")
    repo.run("git cl add list-b file.txt")
    repo.run("git cl add list-a file.txt")

    cl = repo.load_cl_json()
    repo.assert_in("file.txt", cl.get("list-a", []),
                    "file ends up in list-a after reassignment")
    repo.assert_true("file.txt" not in cl.get("list-b", []),
                      "file removed from list-b")

    # list-b should be empty (or absent) after the file was moved away
    repo.assert_true(len(cl.get("list-b", [])) == 0,
                      "list-b is empty after reassignment")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Adding the same file twice deduplicates
    # =================================================================

    repo.section("Duplicate file in one command is deduplicated")

    repo.run(["git", "cl", "add", "dupe-test", "file.txt", "file.txt"])

    cl = repo.load_cl_json()
    count = cl["dupe-test"].count("file.txt")
    repo.assert_equal(1, count,
                       "file.txt appears exactly once despite being added twice")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Deleted file in a changelist shows [ D]
    # =================================================================

    repo.section("Deleted file shows [ D] in status")

    repo.write_file("to-delete.txt", "temporary")
    repo.run("git add to-delete.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add file to delete"])

    repo.delete_file("to-delete.txt")
    repo.run("git cl add cleanup to-delete.txt")

    output = repo.run("git cl st")
    repo.assert_in("[ D] to-delete.txt", output,
                    "deleted file shows [ D]")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Commit with only untracked files does nothing harmful
    # =================================================================

    repo.section("Commit with only untracked files")

    repo.write_file("brand-new.txt", "not tracked")
    repo.run("git cl add new-only brand-new.txt")

    output = repo.run(["git", "cl", "commit", "new-only", "-m", "No tracked files"])
    repo.assert_exit_code(0, "commit exits cleanly")
    repo.assert_in("No tracked files", output,
                    "message indicates no tracked files to commit")

    # The untracked file should still be untracked
    status = repo.run("git status --porcelain brand-new.txt")
    repo.assert_in("??", status,
                    "file remains untracked after failed commit")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Status after delete --all is empty
    # =================================================================

    repo.section("Status after delete --all")

    repo.write_file("file.txt", "changed again")
    repo.run("git cl add temp file.txt")
    repo.run("git cl delete --all")

    cl = repo.load_cl_json()
    repo.assert_equal({}, cl, "cl.json is empty after delete --all")

    # Status should still work — unassigned files go to No Changelist
    output = repo.run("git cl st")
    repo.assert_exit_code(0, "status works after delete --all")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_edge_cases.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: edge cases"))
