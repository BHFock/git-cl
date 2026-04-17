#!/usr/bin/env python3
"""
test_merge_conflict.py — Test refusal of state-mutating commands during
unresolved merge conflicts.

Covers:
    git cl stage       — refuses during merge conflict
    git cl unstage     — refuses during merge conflict
    git cl commit      — refuses during merge conflict
    git cl stash       — refuses during merge conflict
    git cl unstash     — refuses during merge conflict
    git cl checkout    — refuses during merge conflict
    git cl add / rm    — still work (metadata only, no git state change)

What you'll learn:
    - git-cl detects unresolved merge conflicts (UU, AA, DD, etc.) and
      refuses to stage, unstage, commit, stash, unstash, or checkout
    - The refusal is clean: the user sees what's conflicted and how to
      resolve it, rather than a cryptic git error
    - Changelist organisation commands (add, remove) still work, so
      users can rearrange changelists mid-merge if they want to
    - After resolving the conflict, all commands work normally again

Run:
    ./test_merge_conflict.py

Export as shell walkthrough:
    ./test_merge_conflict.py --export > walkthrough_merge_conflict.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def create_merge_conflict(repo: TestRepo, file_path: str = "shared.txt"):
    """
    Create an unresolved merge conflict on the given file.

    Sets up two branches that both modify the same file, then attempts
    to merge them. The merge fails, leaving the file in a UU state.

    After this function returns:
    - The repo is on the original branch
    - `file_path` has a merge conflict (status UU)
    - MERGE_HEAD exists — the repo is mid-merge
    """
    original_branch = repo.get_current_branch()

    # Start from a clean baseline with a committed version of the file
    repo.write_file(file_path, "original line")
    repo.run(f"git add {file_path}")
    repo.run(["git", "commit", "--quiet", "-m", "Add shared file"])

    # Create a side branch with its own version
    repo.run("git checkout --quiet -b conflict-branch")
    repo.write_file(file_path, "branch version")
    repo.run(f"git add {file_path}")
    repo.run(["git", "commit", "--quiet", "-m", "Branch change"])

    # Back to the original branch, make a conflicting change
    repo.run(f"git checkout --quiet {original_branch}")
    repo.write_file(file_path, "original change")
    repo.run(f"git add {file_path}")
    repo.run(["git", "commit", "--quiet", "-m", "Original change"])

    # Attempt the merge — this should fail with a conflict
    repo.run("git merge conflict-branch")
    # Not asserting exit code here — merge is expected to fail with
    # conflict, and we're about to check the conflict exists anyway


def run_tests(repo: TestRepo):

    # =================================================================
    # Setup: create an unresolved merge conflict
    # =================================================================

    repo.section("Setup: create an unresolved merge conflict")

    create_merge_conflict(repo, "shared.txt")

    # Verify the conflict is present
    output = repo.run("git status --porcelain")
    repo.assert_in("UU shared.txt", output,
                   "shared.txt is in conflict state (UU)")

    # Create an additional tracked file we can safely add to a changelist
    repo.write_file("safe.txt", "safe content")
    repo.run("git add safe.txt")
    # Don't commit — we want modifications for stage/commit tests, but
    # the merge is mid-progress so we leave safe.txt staged-and-added.
    # Actually: reset it so we can use it as an unstaged modification later.
    repo.run("git reset --quiet HEAD -- safe.txt")

    # =================================================================
    # Test: stage refuses during merge conflict
    # =================================================================

    repo.section("stage refuses during merge conflict")

    repo.run("git cl add my-list safe.txt")

    output = repo.run("git cl stage my-list")
    repo.assert_in("Cannot stage while merge conflicts are unresolved",
                   output, "stage refuses with clear message")
    repo.assert_in("shared.txt", output,
                   "refusal message names the conflicted file")
    repo.assert_in("[UU]", output,
                   "refusal shows the conflict status code")

    # The changelist should be untouched
    cl = repo.load_cl_json()
    repo.assert_true("my-list" in cl,
                     "changelist preserved after refusal")

    # =================================================================
    # Test: unstage refuses during merge conflict
    # =================================================================

    repo.section("unstage refuses during merge conflict")

    output = repo.run("git cl unstage my-list")
    repo.assert_in("Cannot unstage while merge conflicts are unresolved",
                   output, "unstage refuses with clear message")

    # =================================================================
    # Test: commit refuses during merge conflict
    # =================================================================

    repo.section("commit refuses during merge conflict")

    output = repo.run("git cl commit my-list -m 'should not happen'")
    repo.assert_in("Cannot commit while merge conflicts are unresolved",
                   output, "commit refuses with clear message")

    # Changelist must survive a refused commit
    cl = repo.load_cl_json()
    repo.assert_true("my-list" in cl,
                     "changelist preserved after refused commit")

    # =================================================================
    # Test: stash refuses during merge conflict
    # =================================================================

    repo.section("stash refuses during merge conflict")

    output = repo.run("git cl stash my-list")
    repo.assert_in("Cannot stash while merge conflicts are unresolved",
                   output, "stash refuses with clear message")

    cl = repo.load_cl_json()
    repo.assert_true("my-list" in cl,
                     "changelist not moved to stash after refusal")

    stash = repo.load_stash_json()
    repo.assert_true("my-list" not in stash,
                     "no stash entry created")

    # =================================================================
    # Test: checkout refuses during merge conflict
    # =================================================================

    repo.section("checkout refuses during merge conflict")

    output = repo.run("git cl checkout my-list --force")
    repo.assert_in("Cannot checkout while merge conflicts are unresolved",
                   output, "checkout refuses with clear message")

    # The changelist must survive
    cl = repo.load_cl_json()
    repo.assert_true("my-list" in cl,
                     "changelist preserved after refused checkout")

    # =================================================================
    # Test: unstash refuses during merge conflict
    # =================================================================
    # We can't create a real stash during a merge (stash itself refuses),
    # so unstash's protection is checked against the empty stash: the
    # refusal fires before the "no such stash" error would.

    repo.section("unstash refuses during merge conflict")

    output = repo.run("git cl unstash some-name")
    repo.assert_in("Cannot unstash while merge conflicts are unresolved",
                   output, "unstash refuses before checking stash existence")

    # =================================================================
    # Test: add still works during merge conflict
    # =================================================================
    # Organising changelists doesn't touch git state, so it should be
    # allowed mid-merge. A user might want to pull the conflicted file
    # out of a changelist so they can resolve it manually.

    repo.section("add still works during merge conflict")

    output = repo.run("git cl add organised-list safe.txt")
    repo.assert_exit_code(0, "add succeeds during merge conflict")

    cl = repo.load_cl_json()
    repo.assert_in("safe.txt", cl["organised-list"],
                   "file added to changelist during merge")

    # =================================================================
    # Test: remove still works during merge conflict
    # =================================================================

    repo.section("remove still works during merge conflict")

    output = repo.run("git cl rm safe.txt")
    repo.assert_exit_code(0, "remove succeeds during merge conflict")

    # =================================================================
    # Test: status shows conflicts in default view
    # =================================================================
    # Previously, conflicts were hidden behind --all. Now they're
    # shown by default because they're states the user needs to act on.

    repo.section("status shows conflicts in default view")

    output = repo.run("git cl status")
    repo.assert_exit_code(0, "git cl status succeeds during merge")
    repo.assert_in("shared.txt", output,
                   "conflicted file visible in default status view")
    repo.assert_in("[UU]", output,
                   "conflict code shown in status output")
    repo.assert_not_in("uncommon Git status codes", output,
                       "conflicts no longer reported as 'uncommon'")

    # =================================================================
    # Test: status shows advisory when conflicts present
    # =================================================================

    repo.section("status shows advisory when conflicts present")

    output = repo.run("git cl status")
    repo.assert_in("merge conflicts", output,
                   "status mentions merge conflicts")
    repo.assert_in("Resolve before", output,
                   "advisory tells user to resolve")

    # =================================================================
    # Test: status alias 'st' shows same conflict handling
    # =================================================================

    repo.section("'st' alias shows conflicts identically")

    output_full = repo.run("git cl status")
    output_alias = repo.run("git cl st")
    repo.assert_equal(output_full, output_alias,
                       "status and st produce identical output during merge")

    # =================================================================
    # Test: commands work again after resolving the conflict
    # =================================================================

    repo.section("commands work again after resolving the conflict")

    # Resolve the conflict by writing a final version and committing
    repo.write_file("shared.txt", "resolved version")
    repo.run("git add shared.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Resolve merge conflict"])

    # Verify we're no longer in a merge state
    output = repo.run("git status --porcelain")
    repo.assert_not_in("UU", output, "no conflicts remain after resolution")

    # Use a fresh file to avoid inherited state from the mid-merge setup
    repo.write_file("post-merge.txt", "fresh file")
    repo.run("git add post-merge.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add post-merge file"])
    repo.write_file("post-merge.txt", "modified after merge")

    repo.run("git cl add post-merge-list post-merge.txt")

    # Staging should now succeed
    output = repo.run("git cl stage post-merge-list")
    repo.assert_exit_code(0, "stage works again after merge resolution")

    staged = repo.get_staged_files()
    repo.assert_in("post-merge.txt", staged, "post-merge.txt is now staged")

    
# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_merge_conflict.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: merge conflict handling"))
