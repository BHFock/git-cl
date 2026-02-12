#!/usr/bin/env python3
"""
test_subdirectory.py — Test that git-cl works correctly from different directories.

Covers:
    Adding files from repo root       — paths stored as-is in cl.json
    Adding files from a subdirectory  — paths normalised to repo-root-relative
    Adding files from a nested subdir — deeper paths normalised correctly
    Status display from different CWDs — paths shown relative to current directory
    Diff from a subdirectory          — works with repo-relative paths
    Stage from a subdirectory         — stages the correct files
    Commit from a subdirectory        — commits the correct files
    Stash from a subdirectory         — stashes and restores correctly
    Remove from a subdirectory        — removes the correct file
    Checkout from a subdirectory      — reverts the correct files
    Cross-directory add               — adding a file from a sibling directory

What you'll learn:
    - cl.json always stores paths relative to the repository root
    - git cl status displays paths relative to the current working directory
    - All commands work correctly regardless of which subdirectory you're in
    - Files in different directories can be grouped in the same changelist

Run:
    ./test_subdirectory.py

Export as shell walkthrough:
    ./test_subdirectory.py --export > walkthrough_subdirectory.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: create a directory structure with files at various depths
    # =================================================================

    repo.section("Setup: create a nested directory structure")

    repo.write_file("root.txt", "root content")
    repo.mkdir("src")
    repo.write_file("src/app.py", "print('app')")
    repo.mkdir("src/lib")
    repo.write_file("src/lib/utils.py", "def helper(): pass")
    repo.mkdir("docs")
    repo.write_file("docs/guide.md", "# Guide")
    repo.mkdir("tests")
    repo.write_file("tests/test_app.py", "assert True")

    repo.run("git add root.txt src/app.py src/lib/utils.py "
             "docs/guide.md tests/test_app.py")
    repo.run(["git", "commit", "--quiet", "-m", "Add directory structure"])

    # Modify all files so they have changes to track
    repo.write_file("root.txt", "root modified")
    repo.write_file("src/app.py", "print('app v2')")
    repo.write_file("src/lib/utils.py", "def helper(): return True")
    repo.write_file("docs/guide.md", "# Guide v2")
    repo.write_file("tests/test_app.py", "assert 1 == 1")

    # =================================================================
    # Test: Add files from repo root — paths stored as repo-relative
    # =================================================================

    repo.section("Add files from repo root")

    output = repo.run("git cl add feature root.txt src/app.py src/lib/utils.py")
    repo.assert_exit_code(0, "adding from root should succeed")

    cl = repo.load_cl_json()
    repo.assert_in("root.txt", cl["feature"],
                    "root.txt stored as 'root.txt'")
    repo.assert_in("src/app.py", cl["feature"],
                    "src/app.py stored with forward slash")
    repo.assert_in("src/lib/utils.py", cl["feature"],
                    "nested path stored correctly")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Add files from a subdirectory
    # =================================================================

    repo.section("Add files from a subdirectory (src/)")

    output = repo.run_in("src", "git cl add feature app.py")
    repo.assert_exit_code(0, "adding from src/ should succeed")

    # Path should be stored relative to repo root, not relative to src/
    cl = repo.load_cl_json()
    repo.assert_in("src/app.py", cl["feature"],
                    "path normalised to repo root: 'src/app.py'")
    repo.assert_not_in("app.py", cl["feature"],
                        "bare 'app.py' not stored (normalised to src/app.py)")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Add files from a nested subdirectory
    # =================================================================

    repo.section("Add files from a nested subdirectory (src/lib/)")

    output = repo.run_in("src/lib", "git cl add utils-fix utils.py")
    repo.assert_exit_code(0, "adding from src/lib/ should succeed")

    cl = repo.load_cl_json()
    repo.assert_in("src/lib/utils.py", cl["utils-fix"],
                    "path normalised to 'src/lib/utils.py'")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Add a file from a sibling directory using relative path
    # =================================================================

    repo.section("Cross-directory add: from src/ add a docs/ file")

    output = repo.run_in("src", "git cl add cross-dir ../docs/guide.md")
    repo.assert_exit_code(0, "cross-directory add should succeed")

    cl = repo.load_cl_json()
    repo.assert_in("docs/guide.md", cl["cross-dir"],
                    "sibling path normalised to 'docs/guide.md'")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Status display from repo root
    # =================================================================

    repo.section("Status display from repo root")

    repo.run("git cl add feature src/app.py src/lib/utils.py")

    output = repo.run("git cl st")
    repo.assert_in("src/app.py", output,
                    "full path shown from root")
    repo.assert_in("src/lib/utils.py", output,
                    "nested path shown from root")

    # =================================================================
    # Test: Status display from a subdirectory
    # =================================================================

    repo.section("Status display from a subdirectory (src/)")

    output = repo.run_in("src", "git cl st")
    repo.assert_exit_code(0, "status from subdirectory should succeed")

    # From src/, paths should be shown relative to src/
    repo.assert_in("app.py", output,
                    "app.py shown relative to src/")
    repo.assert_in("lib/utils.py", output,
                    "lib/utils.py shown relative to src/")

    # =================================================================
    # Test: Status display from a nested subdirectory
    # =================================================================

    repo.section("Status display from a nested subdirectory (src/lib/)")

    output = repo.run_in("src/lib", "git cl st")
    repo.assert_exit_code(0, "status from nested subdir should succeed")

    # From src/lib/, utils.py should be shown without path prefix
    repo.assert_in("utils.py", output,
                    "utils.py shown relative to src/lib/")
    # app.py should be shown with ../ prefix
    repo.assert_in("../app.py", output,
                    "../app.py shown relative to src/lib/")

    # =================================================================
    # Test: Diff from a subdirectory
    # =================================================================

    repo.section("Diff from a subdirectory (src/)")

    output = repo.run_in("src", "git cl diff feature")
    repo.assert_exit_code(0, "diff from subdirectory should succeed")
    repo.assert_in("app.py", output,
                    "diff includes app.py changes")
    repo.assert_in("utils.py", output,
                    "diff includes utils.py changes")

    # =================================================================
    # Test: Stage from a subdirectory
    # =================================================================

    repo.section("Stage from a subdirectory (src/)")

    output = repo.run_in("src", "git cl stage feature")
    repo.assert_exit_code(0, "stage from subdirectory should succeed")

    staged = repo.get_staged_files()
    repo.assert_in("src/app.py", staged,
                    "src/app.py is staged")
    repo.assert_in("src/lib/utils.py", staged,
                    "src/lib/utils.py is staged")

    # Unstage to restore state for further tests
    repo.run("git cl unstage feature")

    # =================================================================
    # Test: Commit from a subdirectory
    # =================================================================

    repo.section("Commit from a subdirectory (docs/)")

    repo.run("git cl add docs-update docs/guide.md")

    output = repo.run_in("docs",
                         ["git", "cl", "commit", "docs-update", "-m",
                          "Update guide from docs dir"])
    repo.assert_exit_code(0, "commit from subdirectory should succeed")

    log = repo.get_git_log_oneline()
    repo.assert_in("Update guide from docs dir", log,
                    "commit message in log")

    status = repo.run("git status --porcelain docs/guide.md")
    repo.assert_equal("", status, "docs/guide.md is clean after commit")

    # =================================================================
    # Test: Remove from a subdirectory
    # =================================================================

    repo.section("Remove a file from a subdirectory (src/)")

    output = repo.run_in("src", "git cl remove feature app.py")
    repo.assert_exit_code(0, "remove from subdirectory should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("src/app.py" not in cl.get("feature", []),
                      "src/app.py removed from changelist")
    # utils.py should still be there
    repo.assert_in("src/lib/utils.py", cl.get("feature", []),
                    "src/lib/utils.py still in changelist")

    # =================================================================
    # Test: Checkout (revert) from a subdirectory
    # =================================================================

    repo.section("Checkout from a subdirectory (src/lib/)")

    # Set up a changelist with a nested file
    repo.run("git cl add revert-test src/lib/utils.py")

    output = repo.run_in("src/lib", "git cl checkout revert-test --force")
    repo.assert_exit_code(0, "checkout from nested subdir should succeed")

    content = repo.read_file("src/lib/utils.py")
    repo.assert_equal("def helper(): pass", content,
                       "utils.py reverted to original")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Stash and unstash from a subdirectory
    # =================================================================

    repo.section("Stash and unstash from a subdirectory (src/)")

    repo.write_file("src/app.py", "print('stash test')")
    repo.run("git cl add stash-test src/app.py")

    output = repo.run_in("src", "git cl stash stash-test")
    repo.assert_exit_code(0, "stash from subdirectory should succeed")

    content = repo.read_file("src/app.py")
    repo.assert_equal("print('app')", content,
                       "app.py reverted after stash")

    stash = repo.load_stash_json()
    repo.assert_true("stash-test" in stash,
                      "stash-test in stash metadata")

    output = repo.run_in("src", "git cl unstash stash-test")
    repo.assert_exit_code(0, "unstash from subdirectory should succeed")

    content = repo.read_file("src/app.py")
    repo.assert_equal("print('stash test')", content,
                       "app.py modifications restored after unstash")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: Mixed-directory changelist (files from different subtrees)
    # =================================================================

    repo.section("Changelist with files from different directories")

    repo.write_file("src/app.py", "print('mixed')")
    repo.write_file("tests/test_app.py", "assert 2 == 2")

    repo.run("git cl add mixed-dirs src/app.py tests/test_app.py root.txt")

    # View status from root — all paths visible
    output = repo.run("git cl st")
    repo.assert_in("src/app.py", output, "src/app.py in mixed changelist")
    repo.assert_in("tests/test_app.py", output,
                    "tests/test_app.py in mixed changelist")
    repo.assert_in("root.txt", output, "root.txt in mixed changelist")

    # Stage the mixed changelist from a subdirectory
    output = repo.run_in("tests", "git cl stage mixed-dirs")
    repo.assert_exit_code(0, "staging mixed changelist from subdir should succeed")

    staged = repo.get_staged_files()
    repo.assert_in("src/app.py", staged, "src/app.py staged from tests/")
    repo.assert_in("tests/test_app.py", staged,
                    "tests/test_app.py staged from tests/")
    repo.assert_in("root.txt", staged, "root.txt staged from tests/")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_subdirectory.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: subdirectory"))
