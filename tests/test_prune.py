#!/usr/bin/env python3
"""
test_prune.py — Test pruning stale entries from changelists.

Covers:
    git cl prune             — remove stale entries from all changelists
    git cl prune --dry-run   — show what would be removed, change nothing
    git cl prune -n          — short form of --dry-run
    git cl prune --quiet     — prune without output
    git cl prune -q          — short form of --quiet

What you'll learn:
    - Committing with plain 'git commit' leaves clean files behind in
      changelists; 'git cl prune' removes them
    - Files that were deleted and committed ([XX]) are pruned as well
    - Files with any Git status (modified, staged, deleted, untracked)
      are kept
    - Changelists left empty are deleted
    - Stashed changelists are not touched
    - Pruning unblocks 'git cl stash', which refuses clean files
    - Running 'git cl prune -q' from a post-commit hook keeps
      changelists up to date automatically

Run:
    ./test_prune.py

Export as shell walkthrough:
    ./test_prune.py --export > walkthrough_prune.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TestRepo


def run_tests(repo: TestRepo):

    # =================================================================
    # Test: Nothing to prune when there are no changelists
    # =================================================================

    repo.section("Nothing to prune without changelists")

    output = repo.run("git cl prune")
    repo.assert_exit_code(0, "prune without changelists should succeed")
    repo.assert_in("Nothing to prune", output,
                   "reports that there is nothing to prune")

    # =================================================================
    # Prepare: committed files, then modify them
    # =================================================================

    repo.section("Setup: create files and changelists")

    repo.write_file("app.py", "print('app')")
    repo.write_file("util.py", "print('util')")
    repo.write_file("README.md", "readme")
    repo.run("git add app.py util.py README.md", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add files"], check=True)

    repo.write_file("app.py", "print('app v2')")
    repo.write_file("util.py", "print('util v2')")
    repo.write_file("README.md", "readme v2")

    repo.run("git cl add feature app.py util.py")
    repo.run("git cl add docs README.md")

    # =================================================================
    # Test: Nothing to prune while all files have changes
    # =================================================================

    repo.section("Nothing to prune while all files have changes")

    output = repo.run("git cl prune")
    repo.assert_exit_code(0, "prune should succeed")
    repo.assert_in("Nothing to prune", output,
                   "reports that there is nothing to prune")

    cl = repo.load_cl_json()
    repo.assert_equal(["app.py", "util.py"], cl.get("feature"),
                      "feature changelist unchanged")
    repo.assert_equal(["README.md"], cl.get("docs"),
                      "docs changelist unchanged")

    # =================================================================
    # Test: Prune a file committed with plain 'git commit'
    # =================================================================

    repo.section("Prune a file committed with plain git commit")

    repo.run("git add app.py", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Update app"], check=True)

    output = repo.run("git cl st")
    repo.assert_in("[  ] app.py", output,
                   "committed file is shown as clean in its changelist")

    output = repo.run("git cl prune")
    repo.assert_exit_code(0, "prune should succeed")
    repo.assert_in("Removed 'app.py' from changelist 'feature'", output,
                   "reports the removed entry")
    repo.assert_in("Pruned 1 stale entry", output,
                   "reports the number of pruned entries")

    cl = repo.load_cl_json()
    repo.assert_equal(["util.py"], cl.get("feature"),
                      "only the modified file remains in feature")
    repo.assert_equal(["README.md"], cl.get("docs"),
                      "other changelists are unaffected")
    repo.assert_equal("print('app v2')", repo.read_file("app.py"),
                      "file contents are untouched")

    # =================================================================
    # Test: A changelist left empty is deleted
    # =================================================================

    repo.section("A changelist left empty is deleted")

    repo.run("git add README.md", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Update readme"], check=True)

    output = repo.run("git cl prune")
    repo.assert_in("Deleted empty changelist 'docs'", output,
                   "reports that docs was deleted")

    cl = repo.load_cl_json()
    repo.assert_true("docs" not in cl, "docs changelist deleted")
    repo.assert_true("feature" in cl, "feature changelist still exists")

    # =================================================================
    # Test: Prune a file that was deleted and committed ([XX])
    # =================================================================

    repo.section("Prune a deleted and committed file")

    repo.write_file("old.py", "print('old')")
    repo.run("git add old.py", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add old.py"], check=True)
    repo.write_file("old.py", "print('old v2')")
    repo.run("git cl add cleanup old.py")

    repo.run("git rm --quiet -f old.py", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Remove old.py"], check=True)

    output = repo.run("git cl st")
    repo.assert_in("[XX] old.py", output,
                   "deleted file is shown as [XX] in status")

    output = repo.run("git cl prune")
    repo.assert_in("Removed 'old.py' from changelist 'cleanup'", output,
                   "deleted file is pruned")

    cl = repo.load_cl_json()
    repo.assert_true("cleanup" not in cl,
                     "changelist with only the deleted file is gone")

    # =================================================================
    # Test: Files with any Git status are kept
    # =================================================================

    repo.section("Files with any Git status are kept")

    repo.write_file("staged.py", "print('staged')")
    repo.write_file("gone.py", "print('gone')")
    repo.run("git add staged.py gone.py", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add more files"], check=True)

    repo.write_file("staged.py", "print('staged v2')")
    repo.run("git add staged.py", check=True)                  # [M ] staged change
    repo.delete_file("gone.py")                    # [ D] unstaged deletion
    repo.write_file("new.py", "print('new')")
    repo.run("git add new.py", check=True)                     # [A ] staged addition
    repo.write_file("scratch.txt", "notes")        # [??] untracked

    repo.run("git cl add mixed staged.py gone.py new.py scratch.txt")

    output = repo.run("git cl prune")
    repo.assert_in("Nothing to prune", output,
                   "no entry with a Git status is pruned")

    cl = repo.load_cl_json()
    repo.assert_equal(["staged.py", "gone.py", "new.py", "scratch.txt"],
                      cl.get("mixed"),
                      "all entries with a Git status are kept")

    # Tidy up so the following tests start from a known state
    repo.run(["git", "commit", "--quiet", "-m", "Commit mixed changes",
              "--", "staged.py", "gone.py", "new.py"], check=True)
    repo.delete_file("scratch.txt")
    repo.run("git cl delete mixed")

    # =================================================================
    # Test: --dry-run shows what would be removed but changes nothing
    # =================================================================

    repo.section("Dry run changes nothing")

    repo.run("git add util.py", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Update util"], check=True)

    output = repo.run("git cl prune --dry-run")
    repo.assert_exit_code(0, "dry run should succeed")
    repo.assert_in("Would remove 'util.py' from changelist 'feature'",
                   output, "dry run reports what would be removed")
    repo.assert_in("Changelist 'feature' would become empty", output,
                   "dry run reports which changelist would be deleted")
    repo.assert_in("nothing changed", output,
                   "dry run says that nothing changed")

    cl = repo.load_cl_json()
    repo.assert_equal(["util.py"], cl.get("feature"),
                      "changelist unchanged after dry run")

    output = repo.run("git cl prune -n")
    repo.assert_in("Would remove 'util.py'", output,
                   "-n is the short form of --dry-run")

    # =================================================================
    # Test: --quiet prunes without output
    # =================================================================

    repo.section("Quiet mode prunes without output")

    output = repo.run("git cl prune --quiet")
    repo.assert_exit_code(0, "quiet prune should succeed")
    repo.assert_equal("", output, "quiet prune prints nothing")

    cl = repo.load_cl_json()
    repo.assert_true("feature" not in cl,
                     "stale entry pruned in quiet mode")

    output = repo.run("git cl prune -q")
    repo.assert_equal("", output,
                      "quiet mode prints nothing when nothing is pruned")

    # =================================================================
    # Test: Paths are shown relative to the current directory
    # =================================================================

    repo.section("Prune from a subdirectory")

    repo.mkdir("src")
    repo.write_file("src/core.py", "print('core')")
    repo.run("git add src/core.py", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add core"], check=True)
    repo.write_file("src/core.py", "print('core v2')")
    repo.run("git cl add core src/core.py")
    repo.run("git add src/core.py", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Update core"], check=True)

    output = repo.run_in("src", "git cl prune")
    repo.assert_exit_code(0, "prune from a subdirectory should succeed")
    repo.assert_in("Removed 'core.py' from changelist 'core'", output,
                   "path is shown relative to the subdirectory")

    cl = repo.load_cl_json()
    repo.assert_true("core" not in cl,
                     "entry pruned when run from a subdirectory")

    # =================================================================
    # Test: Directory entries are kept while they contain changes
    # =================================================================

    repo.section("Directory entries")

    repo.mkdir("lib")
    repo.write_file("lib/a.py", "print('a')")
    repo.write_file("lib/b.py", "print('b')")
    repo.run("git add lib", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Add lib"], check=True)
    repo.write_file("lib/a.py", "print('a v2')")
    repo.run("git cl add libs lib")

    output = repo.run("git cl prune")
    repo.assert_in("Nothing to prune", output,
                   "directory with a modified file is kept")

    repo.run("git add lib", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Update lib"], check=True)

    output = repo.run("git cl prune")
    repo.assert_in("Removed 'lib' from changelist 'libs'", output,
                   "directory without changes is pruned")

    # =================================================================
    # Test: Stashed changelists are not touched
    # =================================================================

    repo.section("Stashed changelists are not touched")

    repo.write_file("app.py", "print('app v3')")
    repo.run("git cl add parked app.py")
    repo.run("git cl stash parked")

    output = repo.run("git cl prune")
    repo.assert_in("Nothing to prune", output,
                   "stashed changelists are ignored by prune")

    stashes = repo.load_stash_json()
    repo.assert_true("parked" in stashes,
                     "stashed changelist still exists")

    repo.run("git cl unstash parked --force")
    repo.run("git cl checkout parked --force --delete")

    # =================================================================
    # Test: Pruning unblocks git cl stash
    # =================================================================

    repo.section("Pruning unblocks git cl stash")

    repo.write_file("util.py", "print('util v3')")
    repo.write_file("README.md", "readme v3")
    repo.run("git cl add wip util.py README.md")
    repo.run("git add README.md", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Update readme again"], check=True)

    output = repo.run("git cl stash wip")
    repo.assert_in("Clean files (no changes)", output,
                   "stash refuses a changelist with a clean file")

    repo.run("git cl prune")

    output = repo.run("git cl stash wip")
    repo.assert_in("Successfully stashed changelist 'wip'", output,
                   "stash succeeds after pruning")

    repo.run("git cl unstash wip --force")
    repo.run("git cl checkout wip --force --delete")

    # =================================================================
    # Test: Prune automatically from a post-commit hook
    # =================================================================

    repo.section("Prune automatically from a post-commit hook")

    repo.write_file(".git/hooks/post-commit",
                    "#!/bin/sh\ngit cl prune --quiet")
    if sys.platform != "win32":
        # Git for Windows does not check the executable bit
        repo.run("chmod +x .git/hooks/post-commit")

    repo.write_file("util.py", "print('util v4')")
    repo.write_file("app.py", "print('app v4')")
    repo.run("git cl add hooked util.py app.py")

    repo.run("git add util.py", check=True)
    repo.run(["git", "commit", "--quiet", "-m", "Commit util via git"], check=True)

    cl = repo.load_cl_json()
    repo.assert_equal(["app.py"], cl.get("hooked"),
                      "hook pruned the committed file automatically")


# =================================================================
# Entry point
# =================================================================

if __name__ == "__main__":

    if "--help" in sys.argv:
        print("Usage: ./test_prune.py [--export]\n")
        print("Options:")
        print("  --export   Print a shell walkthrough instead of test output.")
        print("  --help     Show this message.")
        sys.exit(0)

    export_mode = "--export" in sys.argv

    with TestRepo(quiet=export_mode) as repo:
        run_tests(repo)
        if export_mode:
            print(repo.export_shell("git-cl walkthrough: prune"))
