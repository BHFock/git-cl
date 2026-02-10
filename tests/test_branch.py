#!/usr/bin/env python3
"""
test_branch.py — Test creating branches from changelists.

Covers:
    git cl branch <n>                        — create branch named after changelist
    git cl branch <n> <branch-name>          — create branch with custom name
    git cl branch <n> <branch> --from <base> — create branch from a base branch
    git cl br                                   — alias for branch

What you'll learn:
    - git cl branch stashes all active changelists, creates a new branch,
      and restores only the target changelist on that branch
    - Other changelists remain stashed and can be restored later
    - The branch name defaults to the changelist name but can be overridden
    - The --from flag lets you base the branch on a different branch
    - This is a one-step workflow for isolating work on a dedicated branch

Run:
    ./test_branch.py

Export as shell walkthrough:
    ./test_branch.py --export > walkthrough_branch.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Test: Create branch from changelist (default name)
    # =================================================================

    repo.section("Create branch from changelist")

    repo.write_file("alpha.txt", "alpha")
    repo.write_file("beta.txt", "beta")
    repo.run("git add alpha.txt beta.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add files"])

    default_branch = repo.get_current_branch()

    repo.write_file("alpha.txt", "alpha modified")
    repo.write_file("beta.txt", "beta modified")
    repo.run("git cl add feature-a alpha.txt")
    repo.run("git cl add feature-b beta.txt")

    output = repo.run("git cl branch feature-a")
    repo.assert_exit_code(0, "git cl branch should succeed")

    # Should now be on a branch named after the changelist
    branch = repo.get_current_branch()
    repo.assert_equal("feature-a", branch,
                       "now on branch 'feature-a'")

    # feature-a changelist should be active on the new branch
    cl = repo.load_cl_json()
    repo.assert_true("feature-a" in cl,
                      "feature-a changelist active on new branch")

    # alpha.txt should have its modifications
    content = repo.read_file("alpha.txt")
    repo.assert_equal("alpha modified", content,
                       "alpha.txt modifications present on new branch")

    # feature-b should NOT be active — it was stashed
    repo.assert_true("feature-b" not in cl,
                      "feature-b not active on new branch")

    stash = repo.load_stash_json()
    repo.assert_true("feature-b" in stash,
                      "feature-b is stashed")

    # beta.txt should be clean (feature-b was stashed)
    content = repo.read_file("beta.txt")
    repo.assert_equal("beta", content,
                       "beta.txt reverted (feature-b stashed)")

    # =================================================================
    # Test: Create branch with custom name
    # =================================================================
    # Start fresh to avoid branch conflicts.

    repo.section("Create branch with custom name")

    repo.run("git checkout --quiet " + default_branch)
    repo.write_file("alpha.txt", "alpha v3")
    repo.run("git cl add feature-c alpha.txt")

    output = repo.run("git cl branch feature-c my-custom-branch")
    repo.assert_exit_code(0, "git cl branch with custom name should succeed")

    branch = repo.get_current_branch()
    repo.assert_equal("my-custom-branch", branch,
                       "now on branch 'my-custom-branch'")

    cl = repo.load_cl_json()
    repo.assert_true("feature-c" in cl,
                      "feature-c active on custom-named branch")

    # =================================================================
    # Test: Create branch with --from base
    # =================================================================

    repo.section("Create branch with --from base")

    repo.run("git checkout --quiet " + default_branch)

    # Create a develop branch with an extra commit
    repo.run("git checkout --quiet -b develop")
    repo.write_file("develop.txt", "develop content")
    repo.run("git add develop.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add develop content"])
    repo.run("git checkout --quiet " + default_branch)

    repo.write_file("alpha.txt", "hotfix content")
    repo.run("git cl add hotfix alpha.txt")

    output = repo.run("git cl branch hotfix hotfix-branch --from develop")
    repo.assert_exit_code(0, "git cl branch --from should succeed")

    branch = repo.get_current_branch()
    repo.assert_equal("hotfix-branch", branch,
                       "now on branch 'hotfix-branch'")

    # The branch should be based on develop, so develop.txt should exist
    repo.assert_true(repo.file_exists("develop.txt"),
                      "develop.txt exists (branched from develop)")

    cl = repo.load_cl_json()
    repo.assert_true("hotfix" in cl,
                      "hotfix changelist active on new branch")

    # =================================================================
    # Test: 'br' alias works
    # =================================================================

    repo.section("'br' alias works")

    repo.run("git checkout --quiet " + default_branch)
    repo.write_file("alpha.txt", "alias modification")
    repo.run("git cl add quick-fix alpha.txt")

    output = repo.run("git cl br quick-fix")
    repo.assert_exit_code(0, "git cl br alias should succeed")

    branch = repo.get_current_branch()
    repo.assert_equal("quick-fix", branch,
                       "'br' alias created the branch")

    # =================================================================
    # Test: Branch with a non-existent changelist
    # =================================================================

    repo.section("Branch with a non-existent changelist")

    repo.run("git checkout --quiet " + default_branch)

    output = repo.run("git cl branch no-such-list")
    repo.assert_in("no-such-list", output,
                    "error message mentions the changelist name")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_branch.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: branch"))
