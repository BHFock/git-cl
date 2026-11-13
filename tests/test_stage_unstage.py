#!/usr/bin/env python3
"""
test_stage_unstage.py — Test staging and unstaging changelists.

Covers:
    git cl stage <n>              — stage tracked files (changelist kept)
    git cl stage <n> --delete     — stage and delete the changelist
    git cl unstage <n>            — unstage files (changelist kept)
    git cl unstage <n> --delete   — unstage and delete the changelist
    git cl stage <n1> <n2>        — stage several changelists at once
    git cl unstage <n1> <n2>      — unstage several changelists at once

What you'll learn:
    - Staging a changelist runs 'git add' on its tracked files
    - Untracked files ([??]) in the changelist are NOT staged
    - By default, stage KEEPS the changelist (use --delete to remove it)
    - This is the opposite of commit, which deletes by default
    - Unstaging reverses the staging operation (git reset)
    - Stage and unstage can be round-tripped without losing the changelist
    - Several changelists can be staged or unstaged in one command
    - If any named changelist is missing, nothing is staged or unstaged

Run:
    ./test_stage_unstage.py

Export as shell walkthrough:
    ./test_stage_unstage.py --export > walkthrough_stage_unstage.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: tracked modifications and an untracked file
    # =================================================================

    repo.section("Setup: tracked modifications and an untracked file")

    repo.write_file("alpha.txt", "alpha")
    repo.write_file("beta.txt", "beta")
    repo.run("git add alpha.txt beta.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add alpha and beta"])

    # Modify tracked files
    repo.write_file("alpha.txt", "alpha v2")
    repo.write_file("beta.txt", "beta v2")

    # Create an untracked file
    repo.write_file("untracked.txt", "new file")

    # Add all three to a changelist
    repo.run("git cl add my-list alpha.txt beta.txt untracked.txt")

    # =================================================================
    # Test: Stage a changelist (default — keeps changelist)
    # =================================================================

    repo.section("Stage a changelist (default keeps changelist)")

    output = repo.run("git cl stage my-list")
    repo.assert_exit_code(0, "git cl stage should succeed")

    # Tracked files should now be staged
    staged = repo.get_staged_files()
    repo.assert_in("alpha.txt", staged, "alpha.txt is staged")
    repo.assert_in("beta.txt", staged, "beta.txt is staged")

    # Untracked files should NOT be staged
    repo.assert_true("untracked.txt" not in staged,
                      "untracked file is not staged")

    # The changelist should still exist
    cl = repo.load_cl_json()
    repo.assert_true("my-list" in cl,
                      "changelist kept after staging (default)")

    # =================================================================
    # Test: Unstage a changelist
    # =================================================================

    repo.section("Unstage a changelist")

    output = repo.run("git cl unstage my-list")
    repo.assert_exit_code(0, "git cl unstage should succeed")

    staged = repo.get_staged_files()
    repo.assert_true("alpha.txt" not in staged,
                      "alpha.txt is no longer staged")
    repo.assert_true("beta.txt" not in staged,
                      "beta.txt is no longer staged")

    # Changelist should still exist
    cl = repo.load_cl_json()
    repo.assert_true("my-list" in cl,
                      "changelist preserved after unstage")

    # =================================================================
    # Test: Stage then unstage round-trip
    # =================================================================
    # Verify that staging and then unstaging leaves us back where we
    # started — files modified but unstaged, changelist intact.

    repo.section("Stage then unstage round-trip")

    repo.run("git cl stage my-list")
    staged = repo.get_staged_files()
    repo.assert_in("alpha.txt", staged, "alpha.txt staged in round-trip")

    repo.run("git cl unstage my-list")
    staged = repo.get_staged_files()
    repo.assert_true("alpha.txt" not in staged,
                      "alpha.txt unstaged in round-trip")

    cl = repo.load_cl_json()
    repo.assert_true("my-list" in cl,
                      "changelist survives round-trip")

    # =================================================================
    # Test: Stage with --delete (changelist removed)
    # =================================================================

    repo.section("Stage with --delete flag")

    output = repo.run("git cl stage my-list --delete")
    repo.assert_exit_code(0, "git cl stage --delete should succeed")

    staged = repo.get_staged_files()
    repo.assert_in("alpha.txt", staged, "alpha.txt is staged")

    cl = repo.load_cl_json()
    repo.assert_true("my-list" not in cl,
                      "changelist deleted with --delete")

    # =================================================================
    # Test: Unstage with --delete
    # =================================================================
    # Unstage the files we just staged, and set up a new changelist
    # to test unstage --delete.

    repo.section("Unstage with --delete flag")

    repo.run("git reset --quiet HEAD -- alpha.txt beta.txt")

    repo.run("git cl add keep-list alpha.txt beta.txt")
    repo.run("git cl stage keep-list")

    output = repo.run("git cl unstage keep-list --delete")
    repo.assert_exit_code(0, "git cl unstage --delete should succeed")

    staged = repo.get_staged_files()
    repo.assert_true("alpha.txt" not in staged,
                      "alpha.txt unstaged after --delete")

    cl = repo.load_cl_json()
    repo.assert_true("keep-list" not in cl,
                      "changelist deleted after unstage --delete")

    # =================================================================
    # Test: Stage a non-existent changelist
    # =================================================================

    repo.section("Stage a non-existent changelist")

    output = repo.run("git cl stage no-such-list")
    repo.assert_in("no-such-list", output,
                    "error message mentions the changelist name")

    # =================================================================
    # Test: Unstage a non-existent changelist
    # =================================================================

    repo.section("Unstage a non-existent changelist")

    output = repo.run("git cl unstage no-such-list")
    repo.assert_in("no-such-list", output,
                    "error message mentions the changelist name")


    # =================================================================
    # Test: Stage and unstage multiple changelists
    # =================================================================

    repo.section("Stage and unstage multiple changelists")

    repo.run("git reset --quiet HEAD -- alpha.txt beta.txt")
    repo.run("git cl add list-a alpha.txt")
    repo.run("git cl add list-b beta.txt")

    output = repo.run("git cl stage list-a list-b")
    repo.assert_exit_code(0, "staging multiple changelists should succeed")

    staged = repo.get_staged_files()
    repo.assert_in("alpha.txt", staged, "alpha.txt from list-a is staged")
    repo.assert_in("beta.txt", staged, "beta.txt from list-b is staged")

    cl = repo.load_cl_json()
    repo.assert_true("list-a" in cl and "list-b" in cl,
                      "both changelists kept after staging (default)")

    output = repo.run("git cl unstage list-a list-b")
    repo.assert_exit_code(0, "unstaging multiple changelists should succeed")

    staged = repo.get_staged_files()
    repo.assert_true("alpha.txt" not in staged and "beta.txt" not in staged,
                      "both files are no longer staged")

    # =================================================================
    # Test: Stage and unstage multiple changelists with --delete
    # =================================================================

    repo.section("Stage and unstage multiple changelists with --delete")

    repo.run("git cl stage list-a list-b --delete")
    staged = repo.get_staged_files()
    repo.assert_in("alpha.txt", staged, "alpha.txt staged with --delete")
    repo.assert_in("beta.txt", staged, "beta.txt staged with --delete")

    cl = repo.load_cl_json()
    repo.assert_true("list-a" not in cl and "list-b" not in cl,
                      "both changelists deleted after stage --delete")

    repo.run("git cl add list-a alpha.txt")
    repo.run("git cl add list-b beta.txt")
    repo.run("git cl unstage list-a list-b --delete")

    staged = repo.get_staged_files()
    repo.assert_true("alpha.txt" not in staged and "beta.txt" not in staged,
                      "both files unstaged with --delete")

    cl = repo.load_cl_json()
    repo.assert_true("list-a" not in cl and "list-b" not in cl,
                      "both changelists deleted after unstage --delete")

    # =================================================================
    # Test: A missing changelist aborts staging and unstaging
    # =================================================================

    repo.section("A missing changelist aborts staging and unstaging")

    repo.run("git cl add real alpha.txt")

    output = repo.run("git cl stage real no-such-list")
    repo.assert_in("no-such-list", output,
                    "stage error mentions the missing changelist")
    repo.assert_in("Nothing staged", output,
                    "stage output states that nothing was staged")

    staged = repo.get_staged_files()
    repo.assert_true("alpha.txt" not in staged,
                      "alpha.txt is not staged")

    repo.run("git add alpha.txt")

    output = repo.run("git cl unstage real no-such-list")
    repo.assert_in("Nothing unstaged", output,
                    "unstage output states that nothing was unstaged")

    staged = repo.get_staged_files()
    repo.assert_in("alpha.txt", staged, "alpha.txt remains staged")

    cl = repo.load_cl_json()
    repo.assert_true("real" in cl, "existing changelist is preserved")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_stage_unstage.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: stage and unstage"))
