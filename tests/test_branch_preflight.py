#!/usr/bin/env python3
"""
test_branch_preflight.py — Test pre-flight validation of 'git cl branch'.

Covers (issue #51):
    git cl branch with a changelist containing clean files     — fails fast
    git cl branch with staged files in multiple changelists    — fails fast
    git cl branch after cleaning up the changelists            — succeeds
    git cl branch with a single changelist with staged files   — succeeds

What you'll learn:
    - 'git cl branch' must stash EVERY active changelist before creating
      the branch, so every changelist must be fully stashable
    - Clean (unmodified) files in a changelist block the workflow: the
      command aborts before mutating any state instead of leaving the
      repository half-stashed on a new branch
    - Staged files block the workflow when more than one changelist is
      involved: git records the full index in every pathspec stash, so
      staged files would leak into other changelists' stashes and
      reappear when those stashes are applied
    - The error messages explain how to clean up (git cl rm,
      git cl unstage, git cl commit, git cl delete)

Run:
    ./test_branch_preflight.py

Export as shell walkthrough:
    ./test_branch_preflight.py --export > walkthrough_branch_preflight.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Setup: tracked files with an initial commit
    # =================================================================

    repo.section("Setup: create files with an initial commit")

    repo.write_file("mod_a.txt", "a")
    repo.write_file("clean_b.txt", "b")
    repo.write_file("mod_c.txt", "c")
    repo.run("git add mod_a.txt clean_b.txt mod_c.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add files"])

    default_branch = repo.get_current_branch()

    # =================================================================
    # Test: changelist with a clean file blocks the workflow (issue #51)
    # =================================================================
    # Changelist A holds one modified and one clean file. cl_stash
    # refuses changelists containing clean files, so 'git cl branch'
    # must abort BEFORE stashing anything or creating the branch.

    repo.section("Changelist with clean file blocks branch creation")

    repo.write_file("mod_a.txt", "a modified")
    repo.write_file("mod_c.txt", "c modified")
    repo.run("git cl add A mod_a.txt clean_b.txt")
    repo.run("git cl add B mod_c.txt")

    output = repo.run("git cl branch B")
    repo.assert_in("clean_b.txt", output,
                   "error message names the clean file")
    repo.assert_in("clean", output,
                   "error message explains the file has no changes")
    repo.assert_in("git cl rm", output,
                   "error message suggests 'git cl rm' cleanup")

    # Nothing must have changed: no branch, no stashes, both
    # changelists still active, modifications still in place
    branch = repo.get_current_branch()
    repo.assert_equal(default_branch, branch,
                      "still on the original branch")

    stash_list = repo.run("git stash list")
    repo.assert_equal("", stash_list,
                      "no git stashes were created")

    cl = repo.load_cl_json()
    repo.assert_true("A" in cl and "B" in cl,
                     "both changelists still active")

    stash = repo.load_stash_json()
    repo.assert_true("A" not in stash and "B" not in stash,
                     "no changelist was stashed")

    repo.assert_equal("a modified", repo.read_file("mod_a.txt"),
                      "mod_a.txt modifications untouched")
    repo.assert_equal("c modified", repo.read_file("mod_c.txt"),
                      "mod_c.txt modifications untouched")

    # =================================================================
    # Test: after removing the clean file, the workflow succeeds
    # =================================================================

    repo.section("After cleanup the branch workflow succeeds")

    repo.run("git cl rm clean_b.txt")

    output = repo.run("git cl branch B")
    repo.assert_exit_code(0, "git cl branch should succeed after cleanup")

    branch = repo.get_current_branch()
    repo.assert_equal("B", branch, "now on branch 'B'")

    cl = repo.load_cl_json()
    repo.assert_true("B" in cl, "changelist B active on new branch")

    repo.assert_equal("c modified", repo.read_file("mod_c.txt"),
                      "mod_c.txt modifications present on new branch")

    # Changelist A was stashed, so its modification must be gone
    repo.assert_equal("a", repo.read_file("mod_a.txt"),
                      "mod_a.txt reverted (changelist A stashed)")

    stash = repo.load_stash_json()
    repo.assert_true("A" in stash, "changelist A is stashed")

    # =================================================================
    # Test: staged files in multiple changelists block the workflow
    # =================================================================
    # Git builds pathspec-limited stashes from the FULL index, so a
    # staged file leaks into every stash created while it is staged
    # and would reappear when another changelist's stash is applied.

    repo.section("Staged files in multiple changelists block the workflow")

    # Clean up the previous scenario: restore the stashed changelist,
    # revert all modifications and remove the changelists
    repo.run("git cl unstash A --force")
    repo.run("git checkout --quiet " + default_branch)
    repo.run("git reset --quiet --hard HEAD")
    repo.run("git cl delete --all")

    repo.write_file("folder1/file1.txt", "f1")
    repo.write_file("dddd", "d")
    repo.run("git add folder1/file1.txt dddd")
    repo.write_file("mod_a.txt", "a modified again")

    repo.run("git cl add ok folder1/file1.txt")
    repo.run("git cl add xxx dddd mod_a.txt")

    output = repo.run("git cl branch ok")
    repo.assert_in("staged", output,
                   "error message mentions staged files")
    repo.assert_in("git cl unstage", output,
                   "error message suggests 'git cl unstage'")
    repo.assert_in("dddd", output,
                   "error message names the staged file dddd")
    repo.assert_in("folder1/file1.txt", output,
                   "error message names the staged file folder1/file1.txt")

    branch = repo.get_current_branch()
    repo.assert_equal(default_branch, branch,
                      "still on the original branch")

    stash_list = repo.run("git stash list")
    repo.assert_equal("", stash_list,
                      "no git stashes were created")

    staged = repo.get_staged_files()
    repo.assert_in("dddd", staged, "dddd still staged (state untouched)")

    # =================================================================
    # Test: after unstaging, the workflow succeeds without leaks
    # =================================================================
    # This is the leak scenario from issue #51: previously dddd
    # reappeared (staged) on the new branch although it belongs to the
    # stashed changelist xxx.

    repo.section("After unstaging the workflow succeeds without leaks")

    repo.run("git cl unstage ok")
    repo.run("git cl unstage xxx")

    output = repo.run("git cl branch ok")
    repo.assert_exit_code(0, "git cl branch should succeed after unstaging")

    branch = repo.get_current_branch()
    repo.assert_equal("ok", branch, "now on branch 'ok'")

    cl = repo.load_cl_json()
    repo.assert_true("ok" in cl, "changelist ok active on new branch")
    repo.assert_true(repo.file_exists("folder1/file1.txt"),
                     "folder1/file1.txt restored on new branch")

    # The crucial check: files of the stashed changelist xxx must NOT
    # leak onto the new branch
    repo.assert_true(not repo.file_exists("dddd"),
                     "dddd did NOT leak onto the new branch")
    repo.assert_equal("a", repo.read_file("mod_a.txt"),
                      "mod_a.txt reverted (changelist xxx stashed)")

    stash = repo.load_stash_json()
    repo.assert_true("xxx" in stash, "changelist xxx is stashed")

    # =================================================================
    # Test: a single changelist with staged files still works
    # =================================================================
    # With only one changelist there is nothing the staged files could
    # leak into, so the workflow must not be blocked.

    repo.section("Single changelist with staged files still works")

    # Clean up the previous scenario: restore the stashed changelist,
    # revert everything (staged-new files become untracked and are
    # removed by git clean) and delete the changelists
    repo.run("git cl unstash xxx --force")
    repo.run("git checkout --quiet " + default_branch)
    repo.run("git reset --quiet --hard HEAD")
    repo.run("git clean --quiet -fd")
    repo.run("git cl delete --all")

    repo.write_file("solo.txt", "solo")
    repo.run("git add solo.txt")
    repo.run("git cl add solo solo.txt")

    output = repo.run("git cl branch solo")
    repo.assert_exit_code(0,
                          "git cl branch with single staged changelist "
                          "should succeed")

    branch = repo.get_current_branch()
    repo.assert_equal("solo", branch, "now on branch 'solo'")

    staged = repo.get_staged_files()
    repo.assert_in("solo.txt", staged,
                   "solo.txt restored as staged on the new branch")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_branch_preflight.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: branch pre-flight"))
