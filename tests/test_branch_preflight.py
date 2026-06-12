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
    # Changelist 'docs' holds one modified and one clean file. cl_stash
    # refuses changelists containing clean files, so 'git cl branch'
    # must abort BEFORE stashing anything or creating the branch.

    repo.section("Changelist with clean file blocks branch creation")

    repo.write_file("mod_a.txt", "a modified")
    repo.write_file("mod_c.txt", "c modified")
    repo.run("git cl add docs mod_a.txt clean_b.txt")
    repo.run("git cl add feature mod_c.txt")

    output = repo.run("git cl branch feature")
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
    repo.assert_true("docs" in cl and "feature" in cl,
                     "both changelists still active")

    stash = repo.load_stash_json()
    repo.assert_true("docs" not in stash and "feature" not in stash,
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

    output = repo.run("git cl branch feature")
    repo.assert_exit_code(0, "git cl branch should succeed after cleanup")

    branch = repo.get_current_branch()
    repo.assert_equal("feature", branch, "now on branch 'feature'")

    cl = repo.load_cl_json()
    repo.assert_true("feature" in cl,
                     "changelist 'feature' active on new branch")

    repo.assert_equal("c modified", repo.read_file("mod_c.txt"),
                      "mod_c.txt modifications present on new branch")

    # Changelist 'docs' was stashed, so its modification must be gone
    repo.assert_equal("a", repo.read_file("mod_a.txt"),
                      "mod_a.txt reverted (changelist 'docs' stashed)")

    stash = repo.load_stash_json()
    repo.assert_true("docs" in stash, "changelist 'docs' is stashed")

    # =================================================================
    # Test: staged files in multiple changelists block the workflow
    # =================================================================
    # Git builds pathspec-limited stashes from the FULL index, so a
    # staged file leaks into every stash created while it is staged
    # and would reappear when another changelist's stash is applied.

    repo.section("Staged files in multiple changelists block the workflow")

    # Clean up the previous scenario: restore the stashed changelist,
    # revert all modifications and remove the changelists
    repo.run("git cl unstash docs --force")
    repo.run("git checkout --quiet " + default_branch)
    repo.run("git reset --quiet --hard HEAD")
    repo.run("git cl delete --all")

    repo.write_file("src/new_a.txt", "new file a")
    repo.write_file("new_b.txt", "new file b")
    repo.run("git add src/new_a.txt new_b.txt")
    repo.write_file("mod_a.txt", "a modified again")

    repo.run("git cl add feature-a src/new_a.txt")
    repo.run("git cl add feature-b new_b.txt mod_a.txt")

    output = repo.run("git cl branch feature-a")
    repo.assert_in("staged", output,
                   "error message mentions staged files")
    repo.assert_in("git cl unstage", output,
                   "error message suggests 'git cl unstage'")
    repo.assert_in("new_b.txt", output,
                   "error message names the staged file new_b.txt")
    repo.assert_in("src/new_a.txt", output,
                   "error message names the staged file src/new_a.txt")

    branch = repo.get_current_branch()
    repo.assert_equal(default_branch, branch,
                      "still on the original branch")

    stash_list = repo.run("git stash list")
    repo.assert_equal("", stash_list,
                      "no git stashes were created")

    staged = repo.get_staged_files()
    repo.assert_in("new_b.txt", staged,
                   "new_b.txt still staged (state untouched)")

    # =================================================================
    # Test: after unstaging, the workflow succeeds without leaks
    # =================================================================
    # This is the leak scenario from issue #51: previously new_b.txt
    # reappeared (staged) on the new branch although it belongs to the
    # stashed changelist 'feature-b'.

    repo.section("After unstaging the workflow succeeds without leaks")

    repo.run("git cl unstage feature-a")
    repo.run("git cl unstage feature-b")

    output = repo.run("git cl branch feature-a")
    repo.assert_exit_code(0, "git cl branch should succeed after unstaging")

    branch = repo.get_current_branch()
    repo.assert_equal("feature-a", branch, "now on branch 'feature-a'")

    cl = repo.load_cl_json()
    repo.assert_true("feature-a" in cl,
                     "changelist 'feature-a' active on new branch")
    repo.assert_true(repo.file_exists("src/new_a.txt"),
                     "src/new_a.txt restored on new branch")

    # The crucial check: files of the stashed changelist 'feature-b'
    # must NOT leak onto the new branch
    repo.assert_true(not repo.file_exists("new_b.txt"),
                     "new_b.txt did NOT leak onto the new branch")
    repo.assert_equal("a", repo.read_file("mod_a.txt"),
                      "mod_a.txt reverted (changelist 'feature-b' stashed)")

    stash = repo.load_stash_json()
    repo.assert_true("feature-b" in stash,
                     "changelist 'feature-b' is stashed")

    # =================================================================
    # Test: a single changelist with staged files still works
    # =================================================================
    # With only one changelist there is nothing the staged files could
    # leak into, so the workflow must not be blocked.

    repo.section("Single changelist with staged files still works")

    # Clean up the previous scenario: restore the stashed changelist,
    # revert everything (staged-new files become untracked and are
    # removed by git clean) and delete the changelists
    repo.run("git cl unstash feature-b --force")
    repo.run("git checkout --quiet " + default_branch)
    repo.run("git reset --quiet --hard HEAD")
    repo.run("git clean --quiet -fd")
    repo.run("git cl delete --all")

    repo.write_file("standalone.txt", "standalone")
    repo.run("git add standalone.txt")
    repo.run("git cl add standalone standalone.txt")

    output = repo.run("git cl branch standalone")
    repo.assert_exit_code(0,
                          "git cl branch with single staged changelist "
                          "should succeed")

    branch = repo.get_current_branch()
    repo.assert_equal("standalone", branch, "now on branch 'standalone'")

    staged = repo.get_staged_files()
    repo.assert_in("standalone.txt", staged,
                   "standalone.txt restored as staged on the new branch")


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
