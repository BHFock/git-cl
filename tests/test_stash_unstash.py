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

Run:
    ./test_stash_unstash.py

Export as shell walkthrough:
    ./test_stash_unstash.py --export > walkthrough_stash_unstash.sh
"""

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
