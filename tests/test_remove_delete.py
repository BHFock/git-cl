#!/usr/bin/env python3
"""
test_remove_delete.py — Test removing files from changelists and deleting changelists.

Covers:
    git cl remove <name> <files...>  — remove files from a changelist
    git cl rm / git cl r                — aliases for remove
    git cl delete <names...>         — delete one or more changelists
    git cl delete --all              — delete all changelists
    git cl del                       — alias for delete

What you'll learn:
    - Removing a file from a changelist does not affect the file on disk
    - Removed files reappear under "No Changelist" in status
    - Deleting a changelist removes its metadata but leaves files untouched
    - delete --all clears every changelist at once

Run:
    ./test_remove_delete.py

Export as shell walkthrough:
    ./test_remove_delete.py --export > walkthrough_remove_delete.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: create files and assign to changelists
    # =================================================================

    repo.section("Setup: create files and changelists")

    repo.write_file("file1.txt", "one")
    repo.write_file("file2.txt", "two")
    repo.write_file("file3.txt", "three")
    repo.run("git add file1.txt file2.txt file3.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add files"])

    # Modify files so they have changes to track
    repo.write_file("file1.txt", "one modified")
    repo.write_file("file2.txt", "two modified")
    repo.write_file("file3.txt", "three modified")

    repo.run("git cl add list-a file1.txt file2.txt")
    repo.run("git cl add list-b file3.txt")

    # =================================================================
    # Test: Remove a file from a changelist
    # =================================================================

    repo.section("Remove a file from a changelist")

    output = repo.run("git cl remove list-a file1.txt")
    repo.assert_exit_code(0, "git cl remove should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("file1.txt" not in cl.get("list-a", []),
                      "file1.txt removed from list-a")
    repo.assert_in("file2.txt", cl["list-a"],
                    "file2.txt still in list-a")

    # File should still exist on disk
    repo.assert_true(repo.file_exists("file1.txt"),
                      "file1.txt still exists on disk")

    # Removed file should appear under No Changelist
    output = repo.run("git cl st")
    repo.assert_in("No Changelist:", output,
                    "No Changelist section visible")
    repo.assert_in("file1.txt", output,
                    "removed file visible in status")

    # =================================================================
    # Test: 'rm' alias works
    # =================================================================

    repo.section("'rm' alias works")

    # Re-add file1.txt to list-a first
    repo.run("git cl add list-a file1.txt")

    output = repo.run("git cl rm list-a file1.txt")
    repo.assert_exit_code(0, "git cl rm alias should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("file1.txt" not in cl.get("list-a", []),
                      "file1.txt removed via rm alias")

    # =================================================================
    # Test: 'r' alias works
    # =================================================================

    repo.section("'r' alias works")

    repo.run("git cl add list-a file1.txt")

    output = repo.run("git cl r list-a file1.txt")
    repo.assert_exit_code(0, "git cl r alias should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("file1.txt" not in cl.get("list-a", []),
                      "file1.txt removed via r alias")

    # =================================================================
    # Test: Delete a changelist
    # =================================================================

    repo.section("Delete a changelist")

    output = repo.run("git cl delete list-b")
    repo.assert_exit_code(0, "git cl delete should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("list-b" not in cl,
                      "list-b deleted from cl.json")

    # File should still exist on disk
    repo.assert_true(repo.file_exists("file3.txt"),
                      "file3.txt still exists on disk after delete")

    # File should appear under No Changelist
    output = repo.run("git cl st")
    repo.assert_in("file3.txt", output,
                    "file3.txt visible in status after delete")

    # =================================================================
    # Test: Delete multiple changelists by name
    # =================================================================

    repo.section("Delete multiple changelists")

    repo.run("git cl add x file1.txt")
    repo.run("git cl add y file2.txt")

    output = repo.run("git cl delete x y")
    repo.assert_exit_code(0, "deleting multiple changelists should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("x" not in cl, "changelist x deleted")
    repo.assert_true("y" not in cl, "changelist y deleted")

    # =================================================================
    # Test: Delete all changelists with --all
    # =================================================================

    repo.section("Delete all changelists with --all")

    repo.run("git cl add p file1.txt")
    repo.run("git cl add q file2.txt")
    repo.run("git cl add r file3.txt")

    output = repo.run("git cl delete --all")
    repo.assert_exit_code(0, "git cl delete --all should succeed")

    cl = repo.load_cl_json()
    repo.assert_equal({}, cl, "all changelists deleted")

    # =================================================================
    # Test: 'del' alias works
    # =================================================================

    repo.section("'del' alias works")

    repo.run("git cl add temp file1.txt")

    output = repo.run("git cl del temp")
    repo.assert_exit_code(0, "git cl del alias should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("temp" not in cl,
                      "changelist deleted via del alias")

    # =================================================================
    # Test: Remove from a non-existent changelist
    # =================================================================

    repo.section("Remove from a non-existent changelist")

    output = repo.run("git cl remove no-such-list file1.txt")
    repo.assert_in("no-such-list", output,
                    "error message mentions the changelist name")

    # =================================================================
    # Test: Delete a non-existent changelist
    # =================================================================

    repo.section("Delete a non-existent changelist")

    output = repo.run("git cl delete no-such-list")
    repo.assert_in("no-such-list", output,
                    "error message mentions the changelist name")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_remove_delete.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: remove and delete"))
