#!/usr/bin/env python3
"""
test_checkout.py — Test reverting changes using changelists.

Covers:
    git cl checkout <name>           — revert changes for one changelist
    git cl checkout <name1> <name2>  — revert multiple changelists
    git cl checkout <name> --delete  — revert and then remove the changelist
    git cl checkout <name> --force   — skip the confirmation prompt
    git cl co                        — alias for checkout

What you'll learn:
    - git cl checkout (or git cl co) reverts files to their HEAD state
    - It acts only on the files within the named changelist(s)
    - The --delete flag cleans up the metadata after the revert
    - The --force flag is useful for automation to skip interactive prompts

Run:
    ./test_checkout.py

Export as shell walkthrough:
    ./test_checkout.py --export > walkthrough_checkout.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: create files, commit them, and then modify them
    # =================================================================

    repo.section("Setup: create files and modify them")

    repo.write_file("file1.txt", "original content 1")
    repo.write_file("file2.txt", "original content 2")
    repo.run("git add file1.txt file2.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Initial commit"])

    # Apply modifications
    repo.write_file("file1.txt", "modified content 1")
    repo.write_file("file2.txt", "modified content 2")

    # Assign to changelists
    repo.run("git cl add list-1 file1.txt")
    repo.run("git cl add list-2 file2.txt")

    # =================================================================
    # Test: Basic checkout (revert)
    # =================================================================

    repo.section("Basic checkout: revert changes in list-1")

    # Use --force to skip the interactive confirmation prompt
    repo.run("git cl checkout list-1 --force")
    repo.assert_exit_code(0, "git cl checkout should succeed")

    # Verify file1.txt is reverted, but file2.txt is still modified
    content1 = repo.read_file("file1.txt")
    content2 = repo.read_file("file2.txt")

    repo.assert_equal("original content 1", content1,
                      "file1.txt should be reverted")
    repo.assert_equal("modified content 2", content2,
                      "file2.txt should still be modified")

    # Verify list-1 still exists (default behaviour keeps changelist)
    cl = repo.load_cl_json()
    repo.assert_true("list-1" in cl,
                     "changelist list-1 kept by default")

    # =================================================================
    # Test: Checkout with --delete
    # =================================================================

    repo.section("Checkout with --delete: revert and remove metadata")

    repo.run("git cl checkout list-2 --force --delete")
    repo.assert_exit_code(0, "git cl checkout --delete should succeed")

    content2 = repo.read_file("file2.txt")
    repo.assert_equal("original content 2", content2,
                       "file2.txt should be reverted")

    cl = repo.load_cl_json()
    repo.assert_true("list-2" not in cl,
                     "changelist list-2 deleted after checkout --delete")

    # =================================================================
    # Test: Checkout multiple changelists
    # =================================================================

    repo.section("Checkout multiple changelists")

    # Set up fresh modifications
    repo.write_file("file1.txt", "new mod 1")
    repo.write_file("file2.txt", "new mod 2")
    repo.run("git cl add list-a file1.txt")
    repo.run("git cl add list-b file2.txt")

    # Revert both at once
    repo.run("git cl checkout list-a list-b --force")
    repo.assert_exit_code(0, "multi-changelist checkout should succeed")

    content1 = repo.read_file("file1.txt")
    content2 = repo.read_file("file2.txt")
    repo.assert_equal("original content 1", content1,
                      "file1.txt reverted in multi-checkout")
    repo.assert_equal("original content 2", content2,
                      "file2.txt reverted in multi-checkout")

    # =================================================================
    # Test: 'co' alias works
    # =================================================================

    repo.section("'co' alias works")

    repo.write_file("file1.txt", "another modification")
    repo.run("git cl add alias-test file1.txt")

    repo.run("git cl co alias-test --force")
    repo.assert_exit_code(0, "git cl co alias should succeed")

    content1 = repo.read_file("file1.txt")
    repo.assert_equal("original content 1", content1,
                      "file reverted via 'co' alias")

    # =================================================================
    # Test: Error handling for non-existent changelist
    # =================================================================

    repo.section("Error handling: non-existent changelist")

    output = repo.run("git cl checkout ghost-list --force")
    repo.assert_in("ghost-list", output,
                   "error message mentions missing changelist")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_checkout.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: checkout"))
