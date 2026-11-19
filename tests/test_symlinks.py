#!/usr/bin/env python3
"""
test_symlinks.py — Test symbolic links in changelists.

Covers:
    git cl add       — a symlink is added as itself, not as its target
    git cl status    — a changed symlink is shown under its own name
    git cl commit    — a retargeted symlink is committed
    git cl prune     — a changed symlink is kept
    git cl stash     — a symlink is stashed and restored

What you'll learn:
    - Git treats a symbolic link as a file of its own: its content is
      the path it points to. git-cl does the same and never follows it
    - A symlink to a directory, to a file outside the repository or to a
      missing file is still a single file in a changelist
    - Paths through a symlinked directory are stored with the real
      directory, because Git does not accept paths beyond a symlink

Run:
    ./test_symlinks.py

Export as shell walkthrough:
    ./test_symlinks.py --export > walkthrough_symlinks.sh

Skipped on Windows, and on systems where symbolic links cannot be
created.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def symlinks_supported() -> bool:
    """
    Whether this system lets us create symbolic links that Git tracks as
    such. On Windows, Git for Windows checks symlinks out as plain files
    unless core.symlinks is enabled, so the test is skipped there.
    """
    if os.name == "nt":
        return False
    with tempfile.TemporaryDirectory() as tmp:
        try:
            os.symlink("target", os.path.join(tmp, "link"))
            return True
        except (OSError, NotImplementedError):
            return False


def link(repo: TestRepo, target: str, name: str) -> None:
    """Create or replace the symlink 'name' pointing to 'target'."""
    path = repo.repo_dir / name
    if os.path.lexists(path):
        path.unlink()
    os.symlink(target, path)


def run_tests(repo: TestRepo):

    # =================================================================
    # Prepare: files and symlinks
    # =================================================================

    repo.section("Setup: create and commit files and symlinks")

    repo.write_file("real.txt", "real")
    repo.write_file("other.txt", "other")
    repo.write_file("dir/inner.txt", "inner")
    link(repo, "real.txt", "link.txt")
    link(repo, "dir", "linkdir")
    link(repo, os.path.abspath(os.sep), "outside")
    repo.run("git add .", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "initial"], check=True)

    # =================================================================
    # Test: A symlink is added as itself
    # =================================================================

    repo.section("A symlink is added as itself")

    repo.run("git cl add feature link.txt")
    cl = repo.load_cl_json()
    repo.assert_equal(["link.txt"], cl.get("feature"),
                      "the symlink is stored, not its target")

    # =================================================================
    # Test: A retargeted symlink is shown and committed under its name
    # =================================================================

    repo.section("A retargeted symlink is shown and committed under its "
                 "name")

    link(repo, "dir/inner.txt", "link.txt")

    output = repo.run("git cl st --no-color")
    repo.assert_in("[ M] link.txt", output,
                   "the symlink is shown as modified")
    repo.assert_not_in("inner.txt", output,
                       "its new target is not shown as modified")

    output = repo.run("git cl prune -n")
    repo.assert_in("Nothing to prune", output,
                   "prune keeps the changed symlink")

    repo.run(["git", "cl", "commit", "feature", "-m", "Retarget link"])
    repo.assert_exit_code(0, "commit succeeds")
    output = repo.run(["git", "show", "--name-status", "--format=", "HEAD"])
    repo.assert_in("link.txt", output, "the symlink is committed")

    # =================================================================
    # Test: Stash and unstash a symlink
    # =================================================================

    repo.section("Stash and unstash a symlink")

    link(repo, "other.txt", "link.txt")
    repo.run("git cl add parked link.txt")

    repo.run("git cl stash parked")
    repo.assert_exit_code(0, "stash succeeds")
    repo.assert_equal("dir/inner.txt", os.readlink(repo.repo_dir /
                                                    "link.txt"),
                      "the symlink is reverted while stashed")

    repo.run("git cl unstash parked")
    repo.assert_exit_code(0, "unstash succeeds")
    repo.assert_equal("other.txt", os.readlink(repo.repo_dir / "link.txt"),
                      "the symlink is restored")

    repo.run(["git", "cl", "commit", "parked", "-m", "Retarget again"])

    # =================================================================
    # Test: Special symlinks are single files
    # =================================================================

    repo.section("Special symlinks are single files")

    repo.run("git cl add special linkdir")
    repo.assert_exit_code(0, "a symlink to a directory is not rejected as "
                             "a directory")

    repo.run("git cl add special outside")
    repo.assert_exit_code(0, "a symlink pointing outside the repository "
                             "is accepted")

    link(repo, "missing.txt", "dangling")
    output = repo.run("git cl add special dangling")
    repo.assert_exit_code(0, "a symlink to a missing file is accepted")
    repo.assert_not_in("does not exist", output,
                       "no 'does not exist' warning for it")

    cl = repo.load_cl_json()
    repo.assert_equal(["linkdir", "outside", "dangling"], cl.get("special"),
                      "all three are stored as given")

    output = repo.run("git cl st --no-color")
    repo.assert_in("[??] dangling", output,
                   "the new dangling symlink is shown as untracked")
    repo.assert_not_in("[XX]", output,
                       "no symlink is reported as missing")

    repo.run("git cl delete special")
    (repo.repo_dir / "dangling").unlink()

    # =================================================================
    # Test: A trailing slash on a symlink to a directory is rejected
    # =================================================================

    repo.section("A trailing slash on a symlink to a directory is rejected")

    repo.write_file("dir/inner.txt", "inner for slash test")

    # Like Git ('beyond a symbolic link'): 'linkdir/' means the contents
    output = repo.run("git cl add slash linkdir/")
    repo.assert_exit_code(1, "adding 'linkdir/' fails")
    repo.assert_in("'linkdir/' is a symlink to a directory", output,
                   "error explains what 'linkdir/' is")
    repo.assert_in("use 'linkdir'", output,
                   "error shows how to add the symlink itself")
    repo.assert_in("git cl add slash dir/inner.txt", output,
                   "error suggests the changed files under the real "
                   "directory")

    cl = repo.load_cl_json()
    repo.assert_true("slash" not in cl, "nothing was added")

    output = repo.run("git cl add slash outside/")
    repo.assert_exit_code(1, "adding 'outside/' fails")
    repo.assert_in("target is outside the repository", output,
                   "error says the target is outside the repository")

    repo.run(["git", "checkout", "--quiet", "--", "dir/inner.txt"],
             check=True)

    # =================================================================
    # Test: An untracked symlink is shown under its own name
    # =================================================================

    repo.section("An untracked symlink is shown under its own name")

    link(repo, "other.txt", "new-link")
    output = repo.run("git cl st --no-color")
    repo.assert_in("[??] new-link", output,
                   "the untracked symlink is shown")
    repo.assert_not_in("[??] other.txt", output,
                       "its target is not shown as untracked")
    (repo.repo_dir / "new-link").unlink()

    # =================================================================
    # Test: A path through a symlinked directory uses the real directory
    # =================================================================

    repo.section("A path through a symlinked directory uses the real "
                 "directory")

    repo.write_file("dir/inner.txt", "inner changed")
    repo.run("git cl add via linkdir/inner.txt")
    cl = repo.load_cl_json()
    repo.assert_equal(["dir/inner.txt"], cl.get("via"),
                      "stored with the real directory, as Git expects")


if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_symlinks.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    if not symlinks_supported():
        print("Skipping test_symlinks.py: symbolic links cannot be created "
              "on this system.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: symbolic links"))
