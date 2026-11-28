#!/usr/bin/env python3
"""
test_stash_unstash.py — Test stashing and unstashing changelists.

Covers:
    git cl stash <n>         — stash a single changelist
    git cl stash --all          — stash all active changelists
    git cl unstash <n>       — restore a stashed changelist
    git cl unstash --all        — restore all stashed changelists
    git cl sh / git cl us       — aliases for stash and unstash

What you'll learn:
    - Stashing saves a changelist's changes and reverts the working directory
    - The changelist is moved from cl.json to cl-stashes.json
    - Unstashing restores both the file changes and the changelist metadata
    - --all operates on every active (stash) or stashed (unstash) changelist
    - Other changelists are not affected when stashing a single one
    - A name ending in '_stashed' is an ordinary changelist name; unstash
      always uses the name exactly as given
    - Unstashing also restores which changes were staged: a file with
      staged and unstaged changes comes back as [MM], an untracked file
      as [??]
    - A stashed changelist cannot be stashed again, and its name cannot
      be used for a new changelist until it is unstashed
    - If unstashing stops with conflicts, the changelist is restored and
      the stash is kept, as with 'git stash pop'
    - A stash is identified by its commit, so another stash with the same
      message, for example from another worktree, is never applied
    - Git records the whole index in every stash, but unstashing brings
      back only the changelist's files: staged files of other changelists
      stay as they are now

Run:
    ./test_stash_unstash.py

Export as shell walkthrough:
    ./test_stash_unstash.py --export > walkthrough_stash_unstash.sh
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: create files and assign to changelists
    # =================================================================

    repo.section("Setup: create files and changelists")

    repo.write_file("alpha.txt", "alpha")
    repo.write_file("beta.txt", "beta")
    repo.write_file("gamma.txt", "gamma")
    repo.run("git add alpha.txt beta.txt gamma.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add files"])

    repo.write_file("alpha.txt", "alpha modified")
    repo.write_file("beta.txt", "beta modified")
    repo.write_file("gamma.txt", "gamma modified")

    repo.run("git cl add list-a alpha.txt")
    repo.run("git cl add list-b beta.txt gamma.txt")

    # =================================================================
    # Test: Stash a single changelist
    # =================================================================

    repo.section("Stash a single changelist")

    output = repo.run("git cl stash list-a")
    repo.assert_exit_code(0, "git cl stash should succeed")

    # list-a should be removed from cl.json
    cl = repo.load_cl_json()
    repo.assert_true("list-a" not in cl,
                      "list-a removed from cl.json")

    # list-a should appear in stash metadata
    stash = repo.load_stash_json()
    repo.assert_true("list-a" in stash,
                      "list-a in stash metadata")

    # alpha.txt should be reverted to original
    content = repo.read_file("alpha.txt")
    repo.assert_equal("alpha", content,
                       "alpha.txt reverted after stash")

    # list-b should be unaffected
    cl = repo.load_cl_json()
    repo.assert_true("list-b" in cl,
                      "list-b still active")

    content = repo.read_file("beta.txt")
    repo.assert_equal("beta modified", content,
                       "beta.txt unchanged (different changelist)")

    # =================================================================
    # Test: Unstash a changelist
    # =================================================================

    repo.section("Unstash a changelist")

    output = repo.run("git cl unstash list-a")
    repo.assert_exit_code(0, "git cl unstash should succeed")

    # list-a should be back in cl.json
    cl = repo.load_cl_json()
    repo.assert_true("list-a" in cl,
                      "list-a restored to cl.json")

    # list-a should be removed from stash
    stash = repo.load_stash_json()
    repo.assert_true("list-a" not in stash,
                      "list-a removed from stash")

    # alpha.txt should have its modifications back
    content = repo.read_file("alpha.txt")
    repo.assert_equal("alpha modified", content,
                       "alpha.txt modifications restored")

    # =================================================================
    # Test: Stash all changelists with --all
    # =================================================================

    repo.section("Stash all changelists with --all")

    output = repo.run("git cl stash --all")
    repo.assert_exit_code(0, "git cl stash --all should succeed")

    # Both changelists should be stashed
    stash = repo.load_stash_json()
    repo.assert_true("list-a" in stash, "list-a stashed")
    repo.assert_true("list-b" in stash, "list-b stashed")

    # No active changelists should remain
    cl = repo.load_cl_json()
    repo.assert_equal({}, cl, "no active changelists remain")

    # All files should be reverted
    content_a = repo.read_file("alpha.txt")
    content_b = repo.read_file("beta.txt")
    content_g = repo.read_file("gamma.txt")
    repo.assert_equal("alpha", content_a, "alpha.txt reverted")
    repo.assert_equal("beta", content_b, "beta.txt reverted")
    repo.assert_equal("gamma", content_g, "gamma.txt reverted")

    # =================================================================
    # Test: Unstash a single changelist after stash --all
    # =================================================================
    # This is a common workflow: stash everything, then selectively
    # restore one changelist to work on.

    repo.section("Unstash one changelist after stash --all")

    output = repo.run("git cl unstash list-b")
    repo.assert_exit_code(0, "unstashing list-b should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("list-b" in cl, "list-b restored")

    stash = repo.load_stash_json()
    repo.assert_true("list-b" not in stash,
                      "list-b removed from stash")
    repo.assert_true("list-a" in stash,
                      "list-a still stashed")

    content_b = repo.read_file("beta.txt")
    repo.assert_equal("beta modified", content_b,
                       "beta.txt restored")

    # alpha.txt should still be clean (list-a is still stashed)
    content_a = repo.read_file("alpha.txt")
    repo.assert_equal("alpha", content_a,
                       "alpha.txt still reverted (list-a stashed)")

    # =================================================================
    # Test: Unstash all with --all
    # =================================================================

    repo.section("Unstash all with --all")

    # First stash list-b again so we have both stashed
    repo.run("git cl stash list-b")

    output = repo.run("git cl unstash --all")
    repo.assert_exit_code(0, "git cl unstash --all should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("list-a" in cl, "list-a restored")
    repo.assert_true("list-b" in cl, "list-b restored")

    stash = repo.load_stash_json()
    repo.assert_equal({}, stash, "stash is empty")

    content_a = repo.read_file("alpha.txt")
    content_b = repo.read_file("beta.txt")
    repo.assert_equal("alpha modified", content_a,
                       "alpha.txt modifications restored")
    repo.assert_equal("beta modified", content_b,
                       "beta.txt modifications restored")

    # =================================================================
    # Test: 'sh' alias for stash
    # =================================================================

    repo.section("'sh' alias for stash")

    output = repo.run("git cl sh list-a")
    repo.assert_exit_code(0, "git cl sh alias should succeed")

    stash = repo.load_stash_json()
    repo.assert_true("list-a" in stash,
                      "list-a stashed via sh alias")

    # =================================================================
    # Test: 'us' alias for unstash
    # =================================================================

    repo.section("'us' alias for unstash")

    output = repo.run("git cl us list-a")
    repo.assert_exit_code(0, "git cl us alias should succeed")

    cl = repo.load_cl_json()
    repo.assert_true("list-a" in cl,
                      "list-a unstashed via us alias")

    # =================================================================
    # Test: Stash a non-existent changelist
    # =================================================================

    repo.section("Stash a non-existent changelist")

    output = repo.run("git cl stash no-such-list")
    repo.assert_in("no-such-list", output,
                    "error message mentions the changelist name")

    # =================================================================
    # Test: Unstash a non-existent changelist
    # =================================================================

    repo.section("Unstash a non-existent changelist")

    output = repo.run("git cl unstash no-such-list")
    repo.assert_in("no-such-list", output,
                    "error message mentions the changelist name")

    # =================================================================
    # Test: A name ending in '_stashed' is an ordinary changelist name
    # =================================================================

    repo.section("A name ending in '_stashed' is an ordinary changelist name")

    repo.write_file("epsilon.txt", "epsilon")
    repo.run("git add epsilon.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add epsilon"])

    repo.write_file("epsilon.txt", "epsilon modified")
    repo.run("git cl add notes_stashed epsilon.txt")

    output = repo.run("git cl st --no-color")
    repo.assert_in("notes_stashed:", output,
                    "changelist ending in '_stashed' is shown in status")
    repo.assert_not_in("No Changelist", output,
                        "its file is not listed under 'No Changelist'")

    repo.run("git cl stash notes_stashed")
    repo.assert_exit_code(0, "stash notes_stashed succeeds")

    repo.run("git cl unstash notes_stashed")
    repo.assert_exit_code(0, "unstash by its own name succeeds")

    cl = repo.load_cl_json()
    repo.assert_true("notes_stashed" in cl,
                      "notes_stashed is active again")
    repo.assert_equal("epsilon modified", repo.read_file("epsilon.txt"),
                       "changes restored")

    # =================================================================
    # Test: The '_stashed' suffix is not an alias for unstash
    # =================================================================

    repo.section("The '_stashed' suffix is not an alias for unstash")

    repo.write_file("zeta.txt", "zeta")
    repo.run("git add zeta.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add zeta"])

    repo.write_file("zeta.txt", "zeta modified")
    repo.run("git cl add plain zeta.txt")
    repo.run("git cl stash plain")

    repo.run("git cl unstash plain_stashed")
    repo.assert_exit_code(1, "unstash plain_stashed fails when only "
                             "'plain' is stashed")

    stashes = repo.load_stash_json()
    repo.assert_true("plain" in stashes,
                      "plain is still stashed")

    # =================================================================
    # Test: Unstash restores which changes were staged
    # =================================================================

    repo.section("Unstash restores which changes were staged")

    repo.write_file("eta.txt", "eta")
    repo.run("git add eta.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add eta"])

    repo.write_file("eta.txt", "eta staged")
    repo.run("git add eta.txt")
    repo.write_file("eta.txt", "eta staged and unstaged")
    repo.write_file("iota.txt", "iota staged")
    repo.run("git add iota.txt")
    repo.write_file("iota.txt", "iota staged and unstaged")
    repo.write_file("kappa.txt", "kappa untracked")
    repo.write_file("lambda.txt", "lambda staged in another changelist")
    repo.run("git add lambda.txt")
    repo.run("git cl add other-staged lambda.txt")

    repo.run("git cl add staging eta.txt iota.txt kappa.txt")
    status_before = repo.run("git status --porcelain")
    staged_before = repo.run("git diff --cached")

    repo.run("git cl stash staging")
    repo.assert_exit_code(0, "stash staging succeeds")
    repo.run("git cl unstash staging")
    repo.assert_exit_code(0, "unstash staging succeeds")

    repo.assert_equal(status_before, repo.run("git status --porcelain"),
                      "[MM], [AM] and [??] files come back as before")
    repo.assert_equal(staged_before, repo.run("git diff --cached"),
                      "staged content is the same as before")

    # =================================================================
    # Test: A stashed changelist cannot be stashed again or reused
    # =================================================================

    repo.section("A stashed changelist cannot be stashed again or reused")

    repo.write_file("mu.txt", "mu")
    repo.run("git add mu.txt", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add mu", "--", "mu.txt"],
             check=True)
    repo.write_file("mu.txt", "mu changed in the changelist")
    repo.run("git cl add parked2 mu.txt")
    repo.run("git cl stash parked2")
    repo.assert_exit_code(0, "stash parked2 succeeds")

    repo.run("git cl stash parked2")
    repo.assert_exit_code(1, "stashing it again fails")
    repo.assert_in("already stashed", repo.last_stderr,
                   "says the changelist is already stashed")

    repo.write_file("nu.txt", "nu untracked")
    repo.run("git cl add parked2 nu.txt")
    repo.assert_exit_code(1, "adding to the stashed name fails")
    repo.assert_in("is stashed", repo.last_stderr,
                   "says the changelist is stashed")
    repo.assert_true("parked2" not in repo.load_cl_json(),
                     "no active changelist with the stashed name")

    # =================================================================
    # Test: Unstash with conflicts restores the changelist
    # =================================================================

    repo.section("Unstash with conflicts restores the changelist")

    repo.write_file("mu.txt", "mu changed in a commit")
    repo.run(["git", "commit", "--quiet", "-m", "Change mu", "--", "mu.txt"],
             check=True)

    repo.run("git cl unstash parked2")
    repo.assert_exit_code(1, "unstash reports the conflict")
    repo.assert_in("stopped with conflicts", repo.last_stderr,
                   "conflict is reported")
    repo.assert_true("parked2" in repo.load_cl_json(),
                     "changelist is restored")
    repo.assert_true("parked2" not in repo.load_stash_json(),
                     "stash record is removed, so it cannot be applied twice")
    repo.assert_in("git-cl-stash:parked2:", repo.run("git stash list"),
                   "the stash itself is kept")

    repo.run("git cl stage parked2")
    repo.assert_exit_code(1, "stage refuses while the conflict is unresolved")
    repo.assert_not_in("git merge --abort", repo.last_stderr,
                       "no merge hint, as no merge is in progress")

    repo.write_file("mu.txt", "mu resolved")
    repo.run("git add mu.txt")
    repo.run("git stash drop --quiet", check=True)

    # =================================================================
    # Test: A stash is told apart from another with the same message
    # =================================================================

    repo.section("A stash is told apart from another with the same message")

    # Worktrees share one stash list. A changelist of the same name
    # stashed in another worktree within the same second gets the same
    # message. A plain git stash with that message stands in for it here.
    repo.write_file("xi.txt", "xi")
    repo.run("git add xi.txt", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add xi", "--", "xi.txt"],
             check=True)
    repo.write_file("xi.txt", "xi changed in the changelist")
    repo.run("git cl add same xi.txt")
    repo.run("git cl stash same")
    repo.assert_exit_code(0, "stash same succeeds")

    message = repo.load_stash_json()["same"]["stash_message"]
    repo.write_file("omicron.txt", "from the other worktree")
    repo.run(["git", "stash", "push", "--quiet", "--include-untracked",
              "-m", message, "--", "omicron.txt"], check=True)

    repo.run("git cl unstash same")
    repo.assert_exit_code(0, "unstash same succeeds")
    repo.assert_equal("xi changed in the changelist",
                      repo.read_file("xi.txt"),
                      "its own changes are restored")
    repo.assert_true(not (repo.repo_dir / "omicron.txt").exists(),
                     "the other stash is not applied")
    repo.assert_in(message, repo.run("git stash list"),
                   "the other stash is left alone")

    # If the changelist's own stash is dropped with plain git, the other
    # stash with the same message must not keep its record alive
    repo.run("git cl stash same")
    message = repo.load_stash_json()["same"]["stash_message"]
    repo.run(["git", "stash", "drop", "--quiet", "stash@{1}"], check=True)
    repo.write_file("omicron.txt", "from the other worktree")
    repo.run(["git", "stash", "push", "--quiet", "--include-untracked",
              "-m", message, "--", "omicron.txt"], check=True)
    repo.run(["git", "stash", "drop", "--quiet", "stash@{1}"], check=True)
    output = repo.run("git cl prune -n")
    repo.assert_in("Would remove stashed changelist 'same'", output,
                   "prune sees the record as orphaned")
    repo.run("git cl prune")
    repo.run("git stash drop --quiet", check=True)

    # Records from git-cl 1.6.4 and earlier have no 'stash_commit';
    # they are still found by their message
    repo.write_file("xi.txt", "xi changed again")
    repo.run("git cl add older xi.txt")
    repo.run("git cl stash older")
    stashes = repo.load_stash_json()
    del stashes["older"]["stash_commit"]
    repo.write_file(".git/cl-stashes.json", json.dumps(stashes))
    repo.run("git cl unstash older")
    repo.assert_exit_code(0, "a record without stash_commit unstashes")
    repo.assert_equal("xi changed again", repo.read_file("xi.txt"),
                      "its changes are restored")

    # =================================================================
    # Test: Staged files of other changelists are not unstashed
    # =================================================================

    repo.section("Unstash leaves staged files of other changelists alone")

    repo.write_file("own.txt", "own")
    repo.run("git add own.txt", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add own.txt"], check=True)
    repo.write_file("own.txt", "own changed")
    repo.write_file("dropped.txt", "dropped")
    repo.write_file("restaged.txt", "first")
    repo.run("git add dropped.txt restaged.txt", check=True)
    repo.run("git cl add mine own.txt")
    repo.run("git cl add theirs dropped.txt restaged.txt")
    repo.run("git cl stash mine")

    # Meanwhile, one staged file of 'theirs' is dropped, the other staged
    # again with other content
    repo.run("git rm --quiet --force dropped.txt", check=True)
    repo.write_file("restaged.txt", "second")
    repo.run("git add restaged.txt", check=True)

    repo.run("git cl unstash mine")
    repo.assert_exit_code(0, "unstash succeeds")
    repo.assert_equal("own changed", repo.read_file("own.txt"),
                      "the changelist's change is restored")
    repo.assert_true(not (repo.repo_dir / "dropped.txt").exists(),
                     "the dropped file does not come back")
    repo.assert_equal("second", repo.read_file("restaged.txt"),
                      "the file staged again keeps its content")
    repo.assert_not_in("dropped.txt", repo.get_staged_files(),
                       "the dropped file is not staged again")

    # =================================================================
    # Test: Suggested commands fit the current directory
    # =================================================================

    repo.section("Unstash suggests commands for the current directory")

    repo.mkdir("notes")
    repo.write_file("notes/my plan.txt", "plan")
    repo.run(["git", "add", "notes/my plan.txt"], check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add plan"], check=True)
    repo.write_file("notes/my plan.txt", "plan in the changelist")
    repo.run(["git", "cl", "add", "plan", "notes/my plan.txt"])
    repo.run("git cl stash plan")
    repo.write_file("notes/my plan.txt", "plan changed meanwhile")

    repo.run_in("notes", "git cl unstash plan")
    repo.assert_exit_code(1, "unstash is refused by the local change")
    repo.assert_in("git restore 'my plan.txt'", repo.last_stderr,
                   "the path is quoted and relative to the current directory")
    repo.assert_in("[ M] my plan.txt", repo.last_stderr,
                   "the file is listed with its status, relative to the "
                   "current directory")
    repo.assert_in("discards your changes", repo.last_stderr,
                   "the discarding command is marked as such")
    repo.assert_not_in("conflict", repo.last_stderr.lower(),
                       "a local change is not called a conflict")
    repo.run_in("notes", "git restore 'my plan.txt'")
    output = repo.run_in("notes", "git cl unstash plan")
    repo.assert_exit_code(0, "unstash succeeds after discarding the change")
    repo.assert_in("Unstashed changelist 'plan' to branch", output,
                   "one summary line")
    repo.assert_not_in("Ready to work", output, "no closing slogan")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_stash_unstash.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: stash and unstash"))
