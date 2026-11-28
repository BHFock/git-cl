#!/usr/bin/env python3
"""
test_exit_codes.py — Test exit codes and the split between stdout and stderr.

Covers:
    Success                  — exit code 0, output on stdout
    Errors in every command  — exit code 1, message on stderr, nothing on stdout
    Partial failure          — valid names are processed, exit code is still 1
    Nothing to do            — exit code 0
    Warnings                 — on stderr, exit code stays 0
    Invalid usage            — exit code 2 (from argparse)

What you'll learn:
    - git-cl can be used in scripts: 'git cl commit docs -m "..." && git push'
      only pushes if the commit really happened
    - Errors, warnings and their hints go to stderr, regular output to stdout
    - A command that has nothing to do (e.g. no tracked files to stage)
      succeeds
    - Commands that take several names or paths still handle the valid
      ones, but report the failure in their exit code
    - Refusing to unstash onto a branch with a dirty working directory is
      an error, not a warning

Run:
    ./test_exit_codes.py

Export as shell walkthrough:
    ./test_exit_codes.py --export > walkthrough_exit_codes.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def assert_error(repo: TestRepo, command, message: str, what: str):
    """Run a command that must fail: exit code 1, message on stderr only."""
    repo.run(command)
    repo.assert_exit_code(1, f"{what}: exit code 1")
    repo.assert_in(message, repo.last_stderr, f"{what}: error on stderr")
    repo.assert_equal("", repo.last_stdout, f"{what}: nothing on stdout")


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: tracked modifications and an untracked file
    # =================================================================

    repo.section("Setup: tracked modifications and an untracked file")

    repo.write_file("alpha.txt", "alpha")
    repo.write_file("beta.txt", "beta")
    repo.run("git add alpha.txt beta.txt")
    repo.run(["git", "commit", "--quiet", "-m", "Add alpha and beta"])
    repo.write_file("alpha.txt", "alpha v2")
    repo.write_file("beta.txt", "beta v2")
    repo.write_file("new.txt", "untracked")

    # =================================================================
    # Test: Success gives exit code 0 and output on stdout
    # =================================================================

    repo.section("Success: exit code 0, output on stdout")

    repo.run("git cl add docs alpha.txt")
    repo.assert_exit_code(0, "add succeeds")
    repo.assert_in("Added to 'docs'", repo.last_stdout,
                   "confirmation on stdout")
    repo.assert_equal("", repo.last_stderr, "nothing on stderr")

    repo.run("git cl status")
    repo.assert_exit_code(0, "status succeeds")

    # =================================================================
    # Test: A missing changelist is an error in every command
    # =================================================================

    repo.section("Error: changelist not found")

    for command in ["stage", "unstage", "diff", "stash", "delete"]:
        assert_error(repo, f"git cl {command} nope",
                     "Changelist 'nope' not found", f"{command} nope")

    assert_error(repo, ["git", "cl", "commit", "nope", "-m", "Message"],
                 "Changelist 'nope' not found", "commit nope")
    assert_error(repo, "git cl checkout nope --force",
                 "nope", "checkout nope")
    assert_error(repo, "git cl unstash nope",
                 "No stashed changelist found for 'nope'", "unstash nope")
    assert_error(repo, "git cl branch nope",
                 "Changelist 'nope' not found", "branch nope")

    # Nothing was committed by the failed commit
    log = repo.get_git_log_oneline()
    repo.assert_in("Add alpha and beta", log, "no commit was made")

    # =================================================================
    # Test: Other invalid input
    # =================================================================

    repo.section("Error: invalid names, paths and option combinations")

    assert_error(repo, ["git", "cl", "add", "my list", "beta.txt"],
                 "Invalid changelist name", "add with invalid name")
    assert_error(repo, "git cl rm new.txt",
                 "'new.txt' was not found in any changelist",
                 "rm of an unassigned file")
    assert_error(repo, "git cl delete docs --all",
                 "Cannot specify changelist names and --all together",
                 "delete with names and --all")

    cl = repo.load_cl_json()
    repo.assert_true("docs" in cl, "docs survived the failed commands")

    # =================================================================
    # Test: Partial failure still handles the valid names
    # =================================================================

    repo.section("Partial failure: valid names are handled, exit code is 1")

    repo.run("git cl add tmp beta.txt")
    repo.run("git cl delete tmp nope")
    repo.assert_exit_code(1, "delete with one missing name fails")
    repo.assert_in("Deleted changelist 'tmp'", repo.last_stdout,
                   "existing changelist deleted (stdout)")
    repo.assert_in("Changelist 'nope' not found", repo.last_stderr,
                   "missing changelist reported (stderr)")
    cl = repo.load_cl_json()
    repo.assert_true("tmp" not in cl, "tmp is gone from cl.json")

    repo.run(["git", "cl", "add", "docs", "beta.txt", "../outside.txt"])
    repo.assert_exit_code(1, "add with an unsafe path fails")
    repo.assert_in("invalid or unsafe path", repo.last_stderr,
                   "unsafe path reported on stderr")
    cl = repo.load_cl_json()
    repo.assert_in("beta.txt", cl.get("docs", []),
                   "the valid file was still added")
    repo.run("git cl rm beta.txt")

    # =================================================================
    # Test: Nothing to do is not an error
    # =================================================================

    repo.section("Nothing to do: exit code 0")

    repo.run("git cl add only-new new.txt")
    repo.run("git cl stage only-new")
    repo.assert_exit_code(0, "staging a changelist without tracked files")
    repo.assert_in("No tracked files with changes to stage",
                   repo.last_stdout, "message on stdout")
    repo.assert_in("git add <file>", repo.last_stdout,
                   "hint on adding untracked files to Git")
    repo.run("git cl delete only-new")

    repo.run("git cl prune --dry-run")
    repo.assert_exit_code(0, "prune with nothing to prune")

    # =================================================================
    # Test: Warnings go to stderr but keep exit code 0
    # =================================================================

    repo.section("Warnings: on stderr, exit code 0")

    repo.run("git cl add maybe missing.txt")
    repo.assert_exit_code(0, "adding a non-existent file only warns")
    repo.assert_in("Warning: File 'missing.txt' does not exist",
                   repo.last_stderr, "warning on stderr")
    repo.assert_in("Added to 'maybe'", repo.last_stdout,
                   "confirmation on stdout")
    repo.run("git cl delete maybe")

    # =================================================================
    # Test: Refusing to unstash onto a dirty branch is an error
    # =================================================================

    repo.section("Error: unstash refused on a dirty branch")

    repo.run("git cl stash docs")
    repo.assert_exit_code(0, "stash succeeds")
    repo.run("git checkout --quiet -b other")
    repo.write_file("beta.txt", "beta v3")

    assert_error(repo, "git cl unstash docs",
                 "Error: Working directory is not clean", "unstash docs")
    stash = repo.load_stash_json()
    repo.assert_true("docs" in stash, "docs is still stashed")

    repo.run("git cl unstash docs --force")
    repo.assert_exit_code(0, "unstash --force succeeds")

    # =================================================================
    # Test: Commit only reports success if it committed
    # =================================================================

    repo.section("Success: commit")

    repo.run(["git", "cl", "commit", "docs", "-m", "Update alpha"])
    repo.assert_exit_code(0, "commit succeeds")
    log = repo.get_git_log_oneline()
    repo.assert_in("Update alpha", log, "commit was made")

    # =================================================================
    # Test: Invalid usage is reported by argparse with exit code 2
    # =================================================================

    repo.section("Invalid usage: exit code 2")

    repo.run("git cl no-such-command")
    repo.assert_exit_code(2, "unknown command gives exit code 2")
    repo.assert_in("invalid choice", repo.last_stderr,
                   "usage error on stderr")

    repo.run("git cl branch")
    repo.assert_exit_code(2, "missing argument gives exit code 2")
    repo.assert_in("usage: git cl branch", repo.last_stderr,
                   "the usage line names the subcommand")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_exit_codes.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: exit codes"))
