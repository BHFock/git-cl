#!/usr/bin/env python3
"""
test_directories.py — Test that changelists contain files, not directories.

Covers:
    git cl add       — a directory is rejected with a list of the changed
                       files under it and a ready-to-copy command
    git cl status    — a directory entry left by an older version is
                       pointed out with the same list

What you'll learn:
    - Changelists contain files only
    - 'git cl add <name> <directory>' shows the changed files under the
      directory, with their status, and the command to add them by name
    - Untracked files are listed in the same way as other changes
    - More than 10 changed files are summarised instead of listed
    - Other paths in the same command are still added, but the command
      exits with 1

Run:
    ./test_directories.py

Export as shell walkthrough:
    ./test_directories.py --export > walkthrough_directories.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: a directory with a modified and an untracked file
    # =================================================================

    repo.section("Setup: create and commit files")

    repo.write_file("lib/old.txt", "one")
    repo.write_file("lib/sub/keep.txt", "keep")
    repo.write_file("readme.txt", "readme")
    repo.run("git add .", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "initial"], check=True)

    repo.write_file("lib/old.txt", "two")
    repo.write_file("lib/sub/new.txt", "new")
    repo.write_file("readme.txt", "readme changed")

    # =================================================================
    # Test: Adding a directory is rejected with a list of its files
    # =================================================================

    repo.section("Adding a directory is rejected with a list of its files")

    output = repo.run("git cl add feature lib")
    repo.assert_exit_code(1, "adding a directory fails")
    repo.assert_in("'lib' is a directory", output,
                   "error names the directory")
    repo.assert_in("[ M] lib/old.txt", output,
                   "modified file listed with its status")
    repo.assert_in("[??] lib/sub/new.txt", output,
                   "untracked file listed the same way")
    repo.assert_not_in("keep.txt", output,
                       "unchanged file is not listed")
    repo.assert_in("git cl add feature lib/old.txt lib/sub/new.txt",
                   output, "ready-to-copy command for the files")

    cl = repo.load_cl_json()
    repo.assert_true("feature" not in cl,
                     "nothing was added to the changelist")

    # =================================================================
    # Test: Other paths in the same command are still added
    # =================================================================

    repo.section("Other paths in the same command are still added")

    repo.run("git cl add feature readme.txt lib")
    repo.assert_exit_code(1, "exit code 1 because the directory was "
                             "rejected")

    cl = repo.load_cl_json()
    repo.assert_equal(["readme.txt"], cl.get("feature"),
                      "the file was added, the directory was not")

    # =================================================================
    # Test: The suggested command works
    # =================================================================

    repo.section("The suggested command works")

    repo.run("git cl add feature lib/old.txt lib/sub/new.txt")
    repo.assert_exit_code(0, "adding the files by name succeeds")

    cl = repo.load_cl_json()
    repo.assert_equal(["readme.txt", "lib/old.txt", "lib/sub/new.txt"],
                      cl.get("feature"), "all three files are in the "
                                         "changelist")

    # =================================================================
    # Test: '.' from a subdirectory is a directory too
    # =================================================================

    repo.section("'.' from a subdirectory is a directory too")

    output = repo.run_in("lib/sub", "git cl add other .")
    repo.assert_exit_code(1, "adding '.' fails")
    repo.assert_in("git cl add other new.txt", output,
                   "suggested paths are relative to the current directory")

    # =================================================================
    # Test: A directory without changes
    # =================================================================

    repo.section("A directory without changes")

    repo.write_file("docs/guide.txt", "guide")
    repo.run("git add docs", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add docs"], check=True)

    output = repo.run("git cl add other docs")
    repo.assert_exit_code(1, "adding a directory without changes fails")
    repo.assert_in("No changed files under 'docs'", output,
                   "says there is nothing to add")

    # =================================================================
    # Test: More than 10 changed files are summarised
    # =================================================================

    repo.section("More than 10 changed files are summarised")

    for i in range(11):
        repo.write_file(f"many/file{i:02d}.txt", str(i))

    output = repo.run("git cl add other many")
    repo.assert_exit_code(1, "adding a large directory fails")
    repo.assert_in("11 changed files under 'many'", output,
                   "shows the number of files")
    repo.assert_not_in("file00.txt", output,
                       "does not list the files")

    for i in range(10, 11):
        repo.delete_file(f"many/file{i:02d}.txt")

    output = repo.run("git cl add other many")
    repo.assert_in("many/file09.txt", output,
                   "10 changed files are still listed")

    # =================================================================
    # Test: status points out a directory entry from an older version
    # =================================================================

    repo.section("status points out a directory entry from an older "
                 "version")

    # Older versions stored a directory as given
    repo.write_file(".git/cl.json", '{"legacy": ["lib"]}')

    output = repo.run("git cl st --no-color")
    repo.assert_exit_code(0, "status still succeeds")
    repo.assert_in("'lib' in changelist 'legacy' is a directory", output,
                   "status names the directory entry")
    repo.assert_in("git cl rm lib", output,
                   "status suggests removing the entry")
    repo.assert_in("git cl add legacy lib/old.txt lib/sub/new.txt", output,
                   "status suggests adding the files")

    repo.run("git cl rm lib")
    output = repo.run("git cl st --no-color")
    repo.assert_not_in("is a directory", output,
                       "note disappears once the entry is removed")


if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_directories.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: changelists "
                                    "contain files, not directories"))
