#!/usr/bin/env python3
"""
test_deleted_renamed.py — Test deleted and renamed files in changelists.

Covers:
    git cl add       — adding deleted or renamed files
    git cl status    — status of deleted files and both sides of a rename
    git cl commit    — committing deletions and renames
    git cl stage     — staging deletions
    git cl prune     — keeping deletions that are not yet committed

What you'll learn:
    - A deleted tracked file is a change like any other: it can be added
      to a changelist, staged and committed
    - A rename has two sides: the old path is deleted and the new path is
      added. Put both in the changelist to commit them as one rename
    - If only one side of a rename is in a changelist, 'git cl status'
      and 'git cl commit' point out the other side

Run:
    ./test_deleted_renamed.py

Export as shell walkthrough:
    ./test_deleted_renamed.py --export > walkthrough_deleted_renamed.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def last_commit_name_status(repo: TestRepo) -> str:
    """Return 'git show --name-status' output for HEAD."""
    return repo.run(["git", "show", "--name-status", "--format=", "HEAD"])


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: committed files
    # =================================================================

    repo.section("Setup: create and commit files")

    for name in ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]:
        repo.write_file(name, name)
    repo.run("git add .", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "initial"], check=True)

    # =================================================================
    # Test: Commit a rename with both paths in the changelist
    # =================================================================

    repo.section("Commit a rename with both paths in the changelist")

    repo.run("git mv a.txt renamed.txt", check=True)

    output = repo.run("git cl add rename a.txt renamed.txt")
    repo.assert_not_in("does not exist", output,
                       "no 'does not exist' warning for the renamed file")

    output = repo.run("git cl st --no-color")
    repo.assert_in("[D ] a.txt", output,
                   "old path is shown as a staged deletion")
    repo.assert_in("[R ] renamed.txt", output,
                   "new path is shown as renamed")
    repo.assert_not_in("[XX]", output,
                       "old path is not reported as missing")
    repo.assert_not_in("Note:", output,
                       "no note when both sides are in the changelist")

    repo.run(["git", "cl", "commit", "rename", "-m", "Rename a"])
    repo.assert_exit_code(0, "commit succeeds")

    output = last_commit_name_status(repo)
    repo.assert_in("R100", output, "commit records a rename")

    output = repo.run("git status --porcelain")
    repo.assert_not_in("a.txt", output,
                       "no deletion of a.txt left behind")

    # =================================================================
    # Test: Commit a deletion made in the working tree
    # =================================================================

    repo.section("Commit a deletion made in the working tree")

    repo.delete_file("b.txt")

    output = repo.run("git cl add del-unstaged b.txt")
    repo.assert_not_in("does not exist", output,
                       "no 'does not exist' warning for a deleted file")

    output = repo.run(["git", "cl", "commit", "del-unstaged",
                       "-m", "Delete b"])
    repo.assert_not_in("No tracked files", output,
                       "the deletion counts as a tracked change")

    output = last_commit_name_status(repo)
    repo.assert_in("D\tb.txt", output, "commit deletes b.txt")

    # =================================================================
    # Test: Commit a staged deletion
    # =================================================================

    repo.section("Commit a staged deletion")

    repo.run("git rm --quiet c.txt", check=True)
    repo.run("git cl add del-staged c.txt")

    output = repo.run(["git", "cl", "commit", "del-staged",
                       "-m", "Delete c"])
    repo.assert_not_in("No tracked files", output,
                       "the staged deletion counts as a tracked change")

    output = last_commit_name_status(repo)
    repo.assert_in("D\tc.txt", output, "commit deletes c.txt")

    output = repo.run("git status --porcelain")
    repo.assert_equal("", output.strip(), "working tree is clean")

    # =================================================================
    # Test: Stage deletions
    # =================================================================

    repo.section("Stage deletions")

    repo.delete_file("d.txt")
    repo.run("git rm --quiet e.txt", check=True)
    repo.run("git cl add deletions d.txt e.txt")

    repo.run("git cl stage deletions")
    repo.assert_exit_code(0, "staging an unstaged and a staged deletion "
                             "succeeds")

    staged = repo.get_staged_files()
    repo.assert_true("d.txt" in staged, "d.txt deletion is staged")
    repo.assert_true("e.txt" in staged, "e.txt deletion is still staged")

    repo.run(["git", "cl", "commit", "deletions", "-m", "Delete d and e"])

    # =================================================================
    # Test: Only the new path of a rename is in the changelist
    # =================================================================

    repo.section("Only the new path of a rename is in the changelist")

    repo.write_file("f.txt", "f")
    repo.run("git add f.txt", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add f"], check=True)

    repo.run("git mv f.txt f-new.txt", check=True)
    repo.run("git cl add new-only f-new.txt")

    output = repo.run("git cl st --no-color")
    repo.assert_in("No Changelist", output,
                   "old path is listed under 'No Changelist'")
    repo.assert_in("[D ] f.txt", output,
                   "old path is shown as a staged deletion")
    repo.assert_in("'f-new.txt' was renamed from 'f.txt'", output,
                   "status points out the other side of the rename")
    repo.assert_in("git cl add new-only f.txt", output,
                   "status suggests adding the old path")

    output = repo.run(["git", "cl", "commit", "new-only", "--keep",
                       "-m", "Add f-new"])
    repo.assert_in("'f-new.txt' was renamed from 'f.txt'", output,
                   "commit points out the other side of the rename")

    # Clean up: commit the left-over deletion
    repo.run(["git", "commit", "--quiet", "-m", "Delete f"], check=True)
    repo.run("git cl delete new-only")

    # =================================================================
    # Test: Only the old path of a rename is in the changelist
    # =================================================================

    repo.section("Only the old path of a rename is in the changelist")

    repo.write_file("g.txt", "g")
    repo.run("git add g.txt", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add g"], check=True)

    # Typical flow: the file is already in a changelist, then renamed
    repo.run("git cl add old-only g.txt")
    repo.run("git mv g.txt g-new.txt", check=True)

    output = repo.run("git cl st --no-color")
    repo.assert_not_in("[XX]", output,
                       "old path is not reported as missing")
    repo.assert_in("'g.txt' was renamed to 'g-new.txt'", output,
                   "status points out the new path")

    output = repo.run("git cl prune --dry-run")
    repo.assert_not_in("g.txt", output,
                       "prune keeps the old path, a deletion still to "
                       "commit")

    repo.run("git cl add old-only g-new.txt")
    output = repo.run("git cl st --no-color")
    repo.assert_not_in("Note:", output,
                       "note disappears once both sides are added")

    repo.run(["git", "cl", "commit", "old-only", "-m", "Rename g"])
    output = last_commit_name_status(repo)
    repo.assert_in("R100", output, "commit records the rename")

    output = repo.run("git status --porcelain")
    repo.assert_equal("", output.strip(), "working tree is clean")

    # =================================================================
    # Test: Missing files without a Git status still warn
    # =================================================================

    repo.section("Missing files without a Git status still warn")

    output = repo.run("git cl add ghost no-such-file.txt")
    repo.assert_in("does not exist", output,
                   "warns about a file Git does not know")
    repo.run("git cl delete ghost")


if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_deleted_renamed.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: deleted and "
                                    "renamed files"))
