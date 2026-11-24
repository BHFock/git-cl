#!/usr/bin/env python3
"""
test_ignorecase.py — Test paths typed in another case when Git ignores case.

Covers:
    git cl add <path in other case>      — stored in the spelling Git knows
    git cl add <new file in other case>  — stored in the spelling on disk
    git cl remove <path in other case>   — finds the stored entry
    core.ignorecase false                — paths are stored as typed
                                           (case-sensitive file systems only)

What you'll learn:
    - On macOS and Windows, file systems usually ignore case, and Git
      sets core.ignorecase to true. 'readme.md' then opens README.md.
    - Git still compares paths case-sensitively in status, diff and
      pathspecs. git cl therefore stores the spelling Git knows, so the
      file shows up in its changelist and can be staged and committed.
    - With core.ignorecase false, git cl does not look for another
      spelling.

The test sets core.ignorecase itself, so it runs on case-sensitive file
systems as well.

Run:
    ./test_ignorecase.py

Export as shell walkthrough:
    ./test_ignorecase.py --export > walkthrough_ignorecase.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: tracked files with upper-case letters
    # =================================================================

    repo.section("Setup: tracked files with upper-case letters")

    repo.mkdir("Docs")
    repo.write_file("README.md", "readme")
    repo.write_file("Docs/Guide.md", "guide")
    repo.run("git add README.md Docs/Guide.md", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add docs"], check=True)
    repo.write_file("README.md", "readme changed")
    repo.write_file("Docs/Guide.md", "guide changed")
    repo.write_file("New.txt", "new")
    repo.run("git config core.ignorecase true", check=True)

    # =================================================================
    # Add and remove with paths in another case
    # =================================================================

    repo.section("Add paths typed in lower case")

    repo.run("git cl add docs readme.md docs/guide.md new.txt")
    repo.assert_exit_code(0, "add succeeds")
    repo.assert_equal(["README.md", "Docs/Guide.md", "New.txt"],
                      repo.load_cl_json().get("docs"),
                      "entries use the spelling Git and the disk use")

    repo.run("git cl stage docs")
    repo.assert_in("README.md", repo.get_staged_files(),
                   "staging the changelist stages README.md")

    repo.section("Remove a path typed in upper case")

    repo.run("git cl remove DOCS/GUIDE.MD")
    repo.assert_exit_code(0, "remove succeeds")
    repo.assert_true("Docs/Guide.md" not in repo.load_cl_json()["docs"],
                     "Docs/Guide.md is no longer in the changelist")

    # =================================================================
    # Without core.ignorecase, paths are stored as typed
    # =================================================================

    # On a case-insensitive file system (Windows, usually macOS), Python
    # itself may already return the spelling on disk when resolving the
    # path, so this check only runs where the file system is case-sensitive
    if (repo.repo_dir / "readme.md").exists():
        return

    repo.section("core.ignorecase false: paths stored as typed")

    repo.run("git config core.ignorecase false", check=True)
    repo.run("git cl add other docs/guide.md")
    repo.assert_equal(["docs/guide.md"], repo.load_cl_json().get("other"),
                      "the path is stored as typed")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_ignorecase.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: ignorecase"))
