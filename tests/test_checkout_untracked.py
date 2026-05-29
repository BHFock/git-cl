#!/usr/bin/env python3
"""
test_checkout_untracked.py — Test that checkout skips untracked files.

Regression test for the bug where a single untracked file in a changelist
caused `git cl checkout` to abort for the ENTIRE changelist.

Background:
    `git checkout HEAD -- <paths>` validates every pathspec before doing
    any work. An untracked file has no committed state, so git rejects the
    whole batch with a non-zero exit — meaning the tracked files that COULD
    have been reverted were left untouched. cl_stage and cl_commit already
    filter untracked files; cl_checkout did not.

Covers:
    git cl checkout <mixed>            — tracked file reverts, untracked skipped
    git cl checkout <all-untracked>    — exits cleanly, nothing reverted
    git cl checkout <mixed> --delete   — changelist removed after a real revert
    git cl checkout <untracked> --delete — changelist kept (nothing happened)

What you'll learn:
    - An untracked file in a changelist no longer blocks checkout of its
      tracked siblings
    - Untracked files are named in a warning rather than silently ignored,
      because "revert this changelist" might be expected to clear them too
    - --delete only fires after a successful revert, so an all-untracked
      changelist is preserved (there was nothing to revert)

Run:
    ./test_checkout_untracked.py

Export as shell walkthrough:
    ./test_checkout_untracked.py --export > walkthrough_checkout_untracked.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Test: Mixed changelist — tracked file reverts, untracked is skipped
    # =================================================================
    # This is the core regression. Before the fix, the untracked file made
    # `git checkout HEAD -- ...` reject the whole pathspec, so tracked.txt
    # was NOT reverted. The key assertion is that tracked.txt IS reverted.

    repo.section("Mixed changelist: tracked reverts, untracked skipped")

    repo.write_file("tracked.txt", "committed content")
    repo.run("git add tracked.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add tracked file"])

    repo.write_file("tracked.txt", "working modification")  # [ M]
    repo.write_file("fresh.txt", "untracked content")       # [??]

    repo.run("git cl add mixed tracked.txt fresh.txt")

    output = repo.run("git cl checkout mixed --force")
    repo.assert_exit_code(
        0, "checkout of a mixed tracked/untracked changelist should succeed")

    # The regression check: the tracked file must be reverted to HEAD even
    # though an untracked file shares the changelist.
    repo.assert_equal(
        "committed content", repo.read_file("tracked.txt"),
        "tracked file reverted to HEAD despite untracked sibling")

    # The untracked file must be left completely alone.
    repo.assert_true(repo.file_exists("fresh.txt"),
                     "untracked file still on disk after checkout")
    repo.assert_equal("untracked content", repo.read_file("fresh.txt"),
                      "untracked file content untouched")

    # The user should be told the untracked file was skipped, by name.
    repo.assert_in("fresh.txt", output,
                   "untracked file named in the warning output")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: All-untracked changelist exits cleanly
    # =================================================================
    # Nothing can be reverted, but the command must not error out the way
    # the raw `git checkout` would. It should exit 0 and name what it skipped.

    repo.section("All-untracked changelist exits cleanly")

    repo.write_file("only1.txt", "alpha")
    repo.write_file("only2.txt", "beta")
    repo.run("git cl add untracked-only only1.txt only2.txt")

    output = repo.run("git cl checkout untracked-only --force")
    repo.assert_exit_code(
        0, "checkout of an all-untracked changelist exits cleanly")

    repo.assert_in("only1.txt", output, "first untracked file named in output")
    repo.assert_in("only2.txt", output, "second untracked file named in output")

    # The files are untracked, so there is nothing to revert — they stay put.
    repo.assert_true(repo.file_exists("only1.txt"),
                     "untracked file 1 untouched")
    repo.assert_true(repo.file_exists("only2.txt"),
                     "untracked file 2 untouched")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: --delete fires after a real revert (mixed changelist)
    # =================================================================
    # When at least one tracked file is actually reverted, the checkout
    # succeeds and --delete should remove the changelist as usual.

    repo.section("Checkout --delete with a mixed changelist removes it")

    repo.write_file("td.txt", "committed")
    repo.run("git add td.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add td"])

    repo.write_file("td.txt", "modified")     # [ M] tracked
    repo.write_file("tu.txt", "untracked")    # [??] untracked

    repo.run("git cl add del-mixed td.txt tu.txt")

    output = repo.run("git cl checkout del-mixed --force --delete")
    repo.assert_exit_code(
        0, "checkout --delete with a mixed changelist should succeed")

    repo.assert_equal("committed", repo.read_file("td.txt"),
                      "tracked file reverted under --delete")

    cl = repo.load_cl_json()
    repo.assert_true("del-mixed" not in cl,
                     "changelist deleted after a successful checkout --delete")

    repo.run("git cl delete --all")

    # =================================================================
    # Test: --delete does NOT fire when nothing was reverted
    # =================================================================
    # An all-untracked changelist hits the early "nothing to checkout" return
    # before the --delete branch, so the changelist is intentionally kept.
    # This pins that behaviour as deliberate rather than incidental.

    repo.section("Checkout --delete keeps an all-untracked changelist")

    repo.write_file("au.txt", "untracked only")
    repo.run("git cl add au-delete au.txt")

    output = repo.run("git cl checkout au-delete --force --delete")
    repo.assert_exit_code(
        0, "checkout --delete on an all-untracked changelist exits cleanly")

    cl = repo.load_cl_json()
    repo.assert_true(
        "au-delete" in cl,
        "changelist kept when nothing was reverted (early return precedes --delete)")

    repo.run("git cl delete --all")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_checkout_untracked.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell(
                "git-cl walkthrough: checkout with untracked files"))
