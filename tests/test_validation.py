#!/usr/bin/env python3
"""
test_validation.py — Test input validation and error handling.

Covers:
    Invalid changelist names  — special characters, reserved words, dots-only, too long
    Dangerous file paths      — directory traversal, absolute paths
    Missing arguments         — no changelist name, no files
    Non-existent files        — files that don't exist on disk

What you'll learn:
    - git-cl rejects names with spaces, slashes, @, :, ~, ^, *
    - Hyphens, underscores, and dots within names are allowed
    - Names that are only dots (., .., ...) are rejected
    - HEAD is a reserved word and rejected
    - Names longer than ~100 characters are rejected
    - Path traversal (../) and absolute paths are silently skipped
    - Non-existent files get a warning but are still added to the changelist

Run:
    ./test_validation.py

Export as shell walkthrough:
    ./test_validation.py --export > walkthrough_validation.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: a file to use for all validation tests
    # =================================================================

    repo.section("Setup: create a file for testing")

    repo.write_file("file.txt", "content")
    repo.run("git add file.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add file"])
    repo.write_file("file.txt", "modified")

    # =================================================================
    # Test: Rejected special characters
    # =================================================================

    repo.section("Rejected: names with special characters")

    rejected = ["my list", "my/list", "my@list", "my:list",
                 "my~list", "my^list", "my*list"]

    for name in rejected:
        output = repo.run(["git", "cl", "add", name, "file.txt"])
        repo.assert_in("Invalid changelist name", output,
                        f"'{name}' rejected")

    # =================================================================
    # Test: Accepted names with hyphens, underscores, dots
    # =================================================================

    repo.section("Accepted: hyphens, underscores, dots")

    accepted = ["my-list", "my_list", "my.list"]

    for name in accepted:
        output = repo.run(["git", "cl", "add", name, "file.txt"])
        repo.assert_in("Added to", output,
                        f"'{name}' accepted")

    # Clean up for next tests
    repo.run("git cl delete --all")

    # =================================================================
    # Test: Dots-only names are rejected
    # =================================================================

    repo.section("Rejected: dots-only names")

    for name in [".", "..", "..."]:
        output = repo.run(["git", "cl", "add", name, "file.txt"])
        repo.assert_in("Invalid changelist name", output,
                        f"'{name}' rejected")

    # =================================================================
    # Test: .hidden is allowed
    # =================================================================

    repo.section("Accepted: dotfile-style name")

    output = repo.run(["git", "cl", "add", ".hidden", "file.txt"])
    repo.assert_in("Added to", output, "'.hidden' accepted")
    repo.run("git cl delete --all")

    # =================================================================
    # Test: HEAD is a reserved word
    # =================================================================

    repo.section("Rejected: reserved word HEAD")

    output = repo.run(["git", "cl", "add", "HEAD", "file.txt"])
    repo.assert_in("Invalid changelist name", output,
                    "'HEAD' rejected")

    # =================================================================
    # Test: common branch names are NOT reserved
    # =================================================================

    repo.section("Accepted: common branch and command names")

    for name in ["main", "master", "status", "add"]:
        output = repo.run(["git", "cl", "add", name, "file.txt"])
        repo.assert_in("Added to", output,
                        f"'{name}' accepted (not reserved)")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Very long names are rejected
    # =================================================================

    repo.section("Rejected: very long name")

    long_name = "a" * 200
    output = repo.run(["git", "cl", "add", long_name, "file.txt"])
    repo.assert_in("Invalid changelist name", output,
                    "200-char name rejected")

    # =================================================================
    # Test: Moderately long names are accepted
    # =================================================================

    repo.section("Accepted: moderately long name")

    ok_name = "a" * 50
    output = repo.run(["git", "cl", "add", ok_name, "file.txt"])
    repo.assert_in("Added to", output, "50-char name accepted")
    repo.run("git cl delete --all")

    # =================================================================
    # Test: Path traversal is blocked
    # =================================================================

    repo.section("Blocked: path traversal")

    output = repo.run(["git", "cl", "add", "safe", "../../../etc/passwd"])
    repo.assert_in("invalid or unsafe path", output,
                    "directory traversal blocked")

    # =================================================================
    # Test: Absolute paths are blocked
    # =================================================================

    repo.section("Blocked: absolute paths")

    output = repo.run(["git", "cl", "add", "safe", "/etc/passwd"])
    repo.assert_in("invalid or unsafe path", output,
                    "absolute path blocked")

    # =================================================================
    # Test: Non-existent files get a warning but are added
    # =================================================================

    repo.section("Non-existent files: warning but added")

    output = repo.run(["git", "cl", "add", "maybe", "nonexistent.txt"])
    repo.assert_in("does not exist", output,
                    "warning about non-existent file")

    cl = repo.load_cl_json()
    repo.assert_in("nonexistent.txt", cl.get("maybe", []),
                    "file still added to changelist despite warning")

    # =================================================================
    # Test: Missing arguments
    # =================================================================

    repo.section("Missing arguments")

    # No arguments at all
    output = repo.run("git cl add")
    repo.assert_exit_code(2, "no arguments gives exit code 2")

    # Changelist name but no files
    output = repo.run("git cl add mylist")
    repo.assert_exit_code(2, "no files gives exit code 2")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_validation.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: validation"))
