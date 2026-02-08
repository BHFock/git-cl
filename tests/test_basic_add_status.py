#!/usr/bin/env python3
"""
test_basic_add_status.py — Test adding files to changelists and viewing status.

Covers:
    git cl add <name> <files...>    — add files to a changelist
    git cl status / git cl st       — view status grouped by changelist
    git cl st <name>                — filter status by changelist name
    git cl st --include-no-cl       — include unassigned files when filtering

What you'll learn:
    - How to create changelists and assign files
    - How files are automatically reassigned when added to a new changelist
    - How 'git cl status' groups files by changelist
    - How unassigned files appear under "No Changelist"

Run:
    ./test_basic_add_status.py

Export as shell walkthrough:
    ./test_basic_add_status.py --export > walkthrough_add_status.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: create files and an initial commit
    # =================================================================

    repo.section("Setup: create files with an initial commit")

    repo.write_file("file1.txt", "hello")
    repo.write_file("file2.txt", "world")
    repo.mkdir("src")
    repo.write_file("src/main.py", "print('hello')")
    repo.run("git add file1.txt file2.txt src/main.py")
    repo.run(["git", "commit", "--quiet", "-m", "Add initial files"])

    # Modify tracked files — they will show as [ M] (unstaged modification)
    repo.write_file("file1.txt", "hello modified")
    repo.write_file("file2.txt", "world modified")

    # Create an untracked file — will show as [??]
    repo.write_file("file3.txt", "new file")

    # =================================================================
    # Test: Add files to a new changelist
    # =================================================================

    repo.section("Add files to a new changelist")

    output = repo.run("git cl add feature1 file1.txt file2.txt")
    repo.assert_exit_code(0, "git cl add should succeed")
    repo.assert_in("Added to 'feature1'", output, "output confirms addition")

    # Verify internal metadata
    cl = repo.load_cl_json()
    repo.assert_true("feature1" in cl,
                      "changelist 'feature1' exists in cl.json")
    repo.assert_in("file1.txt", cl["feature1"],
                    "file1.txt is in feature1")
    repo.assert_in("file2.txt", cl["feature1"],
                    "file2.txt is in feature1")

    # =================================================================
    # Test: Add files to a second changelist
    # =================================================================

    repo.section("Add files to a second changelist")

    output = repo.run("git cl add feature2 src/main.py")
    repo.assert_exit_code(0, "git cl add for second changelist should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("feature2" in cl,
                      "changelist 'feature2' exists in cl.json")
    repo.assert_in("src/main.py", cl["feature2"],
                    "src/main.py is in feature2")

    # =================================================================
    # Test: View status grouped by changelist
    # =================================================================

    repo.section("View status grouped by changelist")

    output = repo.run("git cl st")
    repo.assert_exit_code(0, "git cl st should succeed")
    repo.assert_in("feature1:", output, "output shows feature1 header")
    repo.assert_in("file1.txt", output, "output lists file1.txt")
    repo.assert_in("file2.txt", output, "output lists file2.txt")
    repo.assert_in("feature2:", output, "output shows feature2 header")
    repo.assert_in("src/main.py", output, "output lists src/main.py")

    # The untracked file3.txt is not in any changelist
    repo.assert_in("No Changelist:", output,
                    "shows 'No Changelist' section")
    repo.assert_in("file3.txt", output,
                    "untracked file3.txt appears under No Changelist")

    # =================================================================
    # Test: Reassign a file to a different changelist
    # =================================================================
    # A file can only belong to one changelist. Adding it to a new one
    # automatically removes it from the old one.

    repo.section("Reassign a file to a different changelist")

    output = repo.run("git cl add feature2 file1.txt")
    repo.assert_exit_code(0, "reassigning file should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("file1.txt" not in cl["feature1"],
                      "file1.txt removed from feature1")
    repo.assert_in("file1.txt", cl["feature2"],
                    "file1.txt now in feature2")

    # =================================================================
    # Test: Add an untracked file to a changelist
    # =================================================================

    repo.section("Add an untracked file to a changelist")

    output = repo.run("git cl add feature1 file3.txt")
    repo.assert_exit_code(0, "adding untracked file should succeed")

    cl = repo.load_cl_json()
    repo.assert_in("file3.txt", cl["feature1"],
                    "untracked file3.txt is in feature1")

    # It should now appear under feature1 in status
    output = repo.run("git cl st")
    repo.assert_in("file3.txt", output, "file3.txt appears in status")

    # =================================================================
    # Test: Filter status by changelist name
    # =================================================================

    repo.section("Filter status by changelist name")

    output = repo.run("git cl st feature1")
    repo.assert_exit_code(0, "filtered status should succeed")
    repo.assert_in("feature1:", output, "output shows feature1")
    repo.assert_not_in("feature2:", output,
                        "output does not show feature2")
    repo.assert_not_in("No Changelist:", output,
                        "No Changelist hidden when filtering")

    # =================================================================
    # Test: Filter with --include-no-cl
    # =================================================================

    repo.section("Filter status with --include-no-cl")

    # Modify src/main.py so feature2 has a visible change
    repo.write_file("src/main.py", "print('modified')")

    output = repo.run("git cl st feature2 --include-no-cl")
    repo.assert_exit_code(0, "filtered with --include-no-cl should succeed")
    repo.assert_in("feature2:", output, "output shows feature2")

    # =================================================================
    # Test: Add file from a subdirectory
    # =================================================================

    repo.section("Add file from a subdirectory")

    repo.mkdir("docs")
    repo.write_file("docs/guide.md", "readme content")
    repo.run("git add docs/guide.md")
    repo.run(["git", "commit", "--quiet", "-m", "Add docs"])
    repo.write_file("docs/guide.md", "updated readme")

    # Run git cl add from the docs/ subdirectory
    output = repo.run_in("docs", "git cl add docs-cl guide.md")
    repo.assert_exit_code(0, "adding from subdirectory should succeed")

    # In cl.json the path should be stored relative to the repo root
    cl = repo.load_cl_json()
    repo.assert_in("docs/guide.md", cl["docs-cl"],
                    "path stored as repo-relative in cl.json")

    # =================================================================
    # Test: 'st' alias produces same output as 'status'
    # =================================================================

    repo.section("'st' alias matches 'status'")

    output_st = repo.run("git cl st")
    output_status = repo.run("git cl status")
    repo.assert_equal(output_st, output_status,
                       "'git cl st' and 'git cl status' produce identical output")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":
    export_mode = "--export" in sys.argv
    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: add and status"))
