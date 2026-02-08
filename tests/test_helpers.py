#!/usr/bin/env python3
"""
test_helpers.py — Test framework for git-cl.

Provides the TestRepo class: a context manager that creates a temporary
Git repository for testing git-cl commands. Records every operation so
the session can later be exported as a shell script.

Usage:

    from test_helpers import TestRepo

    with TestRepo() as repo:
        repo.write_file("file.txt", "hello")
        repo.run("git add file.txt")
        repo.run("git commit -m 'Add file'")

        repo.write_file("file.txt", "modified")
        output = repo.run("git cl add my-list file.txt")
        # output contains the command's stdout + stderr
    # temporary directory is cleaned up here
"""

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class TestRepo:
    """
    A temporary Git repository for testing git-cl.

    Creates a fresh repository on entry, removes it on exit.
    Records every operation for later shell export.

    Attributes:
        repo_dir:       Path to the temporary repository root.
        last_exit_code: Exit code of the most recent run() call.
        log:            Recorded operations for shell export.
    """

    def __init__(self, quiet: bool = False):
        self.repo_dir: Path | None = None
        self.last_exit_code: int = 0
        self.log: list[dict] = []
        self.quiet: bool = quiet  # suppress output (used during --export)

        # Assertion counters
        self.tests_run: int = 0
        self.tests_passed: int = 0
        self.tests_failed: int = 0

    def __enter__(self):
        self._setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._print_summary()
        self._teardown()
        # Exit with non-zero code if any assertions failed,
        # but only if no other exception is already propagating
        if exc_type is None and self.tests_failed > 0:
            sys.exit(1)
        return False  # do not suppress exceptions

    def _setup(self):
        """Create a temporary Git repository with an initial commit."""

        # Create a temporary directory with a recognisable prefix
        self.repo_dir = Path(tempfile.mkdtemp(prefix="git-cl-test."))

        # Initialise a Git repository
        self._git("init", "--quiet")

        # Configure user identity (Git requires this for commits)
        self._git("config", "user.email", "test@git-cl.test")
        self._git("config", "user.name", "git-cl test")

        # Create an initial commit so HEAD exists
        gitkeep = self.repo_dir / ".gitkeep"
        gitkeep.write_text("initial\n")
        self._git("add", ".gitkeep")
        self._git("commit", "--quiet", "-m", "Initial commit")

        # Record setup for shell export
        self._record("setup", shell_lines=[
            "# Create a temporary Git repository",
            "cd $(mktemp -d)",
            "git init --quiet",
            'git config user.email "test@git-cl.test"',
            'git config user.name "git-cl test"',
            'echo "initial" > .gitkeep',
            "git add .gitkeep",
            'git commit --quiet -m "Initial commit"',
        ])

    def _teardown(self):
        """Remove the temporary repository."""
        if self.repo_dir and self.repo_dir.exists():
            shutil.rmtree(self.repo_dir)

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        """Run a git command in the repository directory."""
        return subprocess.run(
            ["git"] + list(args),
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )

    # ---- Recording (for shell export) ----

    def _record(self, kind: str, **kwargs):
        """Append an operation to the log for shell export."""
        entry = {"kind": kind}
        entry.update(kwargs)
        self.log.append(entry)

    # ---- Sections ----

    def section(self, title: str):
        """
        Start a named section — printed during test run and in export.

        Use this to group related test steps:

            repo.section("Add files to a changelist")
        """
        if not self.quiet:
            print(f"\n--- {title} ---")
        self._record("section", title=title)

    # ---- File operations ----

    def write_file(self, path: str, content: str):
        """
        Create or overwrite a file in the repo.

        Parent directories are created automatically.

            repo.write_file("src/main.py", "print('hello')")
        """
        filepath = self.repo_dir / path
        filepath.parent.mkdir(parents=True, exist_ok=True)
        if not content.endswith("\n"):
            content += "\n"
        filepath.write_text(content)

        self._record("write_file", path=path, content=content.rstrip("\n"),
                      shell_lines=[f'echo "{content.rstrip(chr(10))}" > {path}'])

    def mkdir(self, path: str):
        """Create a directory (and parents) in the repo."""
        (self.repo_dir / path).mkdir(parents=True, exist_ok=True)
        self._record("mkdir", path=path,
                      shell_lines=[f"mkdir -p {path}"])

    def delete_file(self, path: str):
        """Delete a file from the working directory."""
        (self.repo_dir / path).unlink()
        self._record("delete_file", path=path,
                      shell_lines=[f"rm {path}"])

    def read_file(self, path: str) -> str:
        """Read and return a file's contents (stripped of trailing newline)."""
        return (self.repo_dir / path).read_text().strip()

    def file_exists(self, path: str) -> bool:
        """Check whether a file exists in the repo."""
        return (self.repo_dir / path).exists()

    # ---- Command execution ----

    def run(self, command, check: bool = False) -> str:
        """
        Run a command in the repo directory and return its output.

        Args:
            command:  A string (parsed with shlex.split) or a list of
                      arguments. Examples:

                      repo.run("git cl add docs file.txt")
                      repo.run(["git", "cl", "commit", "docs", "-m", "Fix bug"])

            check:    If True, raise on non-zero exit codes. Default is
                      False because many tests deliberately trigger errors.

        Returns:
            Combined stdout and stderr as a stripped string.
        """
        if isinstance(command, str):
            args = shlex.split(command)
            shell_line = command
        else:
            args = list(command)
            # Reconstruct a shell-safe command string for export
            shell_line = " ".join(shlex.quote(a) for a in args)

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=self.repo_dir,
            env={**os.environ, "NO_COLOR": "1"},
        )

        self.last_exit_code = result.returncode
        output = (result.stdout + result.stderr).strip()

        self._record("run", command=shell_line,
                      shell_lines=[shell_line])

        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, args, result.stdout, result.stderr
            )

        return output

    def run_in(self, subdir: str, command, check: bool = False) -> str:
        """
        Run a command from within a subdirectory of the repo.

        Same as run(), but sets the working directory to repo_dir/subdir.
        In shell export, this becomes: (cd subdir && command)

            repo.run_in("src", "git cl add my-list main.py")
        """
        if isinstance(command, str):
            args = shlex.split(command)
            shell_line = command
        else:
            args = list(command)
            shell_line = " ".join(shlex.quote(a) for a in args)

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=self.repo_dir / subdir,
            env={**os.environ, "NO_COLOR": "1"},
        )

        self.last_exit_code = result.returncode
        output = (result.stdout + result.stderr).strip()

        self._record("run_in", subdir=subdir, command=shell_line,
                      shell_lines=[f"(cd {subdir} && {shell_line})"])

        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, args, result.stdout, result.stderr
            )

        return output

    # ---- git-cl helpers ----

    def load_cl_json(self) -> dict:
        """Load and return the contents of .git/cl.json."""
        cl_path = self.repo_dir / ".git" / "cl.json"
        if not cl_path.exists():
            return {}
        with open(cl_path) as f:
            return json.load(f)

    def load_stash_json(self) -> dict:
        """Load and return the contents of .git/cl-stashes.json."""
        stash_path = self.repo_dir / ".git" / "cl-stashes.json"
        if not stash_path.exists():
            return {}
        with open(stash_path) as f:
            return json.load(f)

    def get_current_branch(self) -> str:
        """Return the current Git branch name."""
        return self.run("git branch --show-current")

    def get_staged_files(self) -> list[str]:
        """Return list of currently staged file paths."""
        output = self.run("git diff --cached --name-only")
        return [f for f in output.splitlines() if f.strip()]

    def get_git_log_oneline(self, n: int = 1) -> str:
        """Return the last n commits as one-line summaries."""
        return self.run(f"git log --oneline -{n}")

    # ---- Assertions ----

    def _assertion_result(self, passed: bool, msg: str, detail: str = ""):
        """Record and print an assertion result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            if not self.quiet:
                print(f"  \u2713 PASS: {msg}")
        else:
            self.tests_failed += 1
            if not self.quiet:
                detail_str = f"\n         Got: {detail}" if detail else ""
                print(f"  \u2717 FAIL: {msg}{detail_str}")

    def assert_in(self, needle: str, haystack, msg: str):
        """
        Assert that needle is found in haystack.

        haystack can be a string (checks substring) or a list (checks membership).

            repo.assert_in("feature1:", output, "shows feature1 header")
            repo.assert_in("file.txt", cl["docs"], "file in changelist")
        """
        passed = needle in haystack
        self._assertion_result(passed, msg,
                               f"'{needle}' not found" if not passed else "")
        self._record("assert", check="contains", needle=needle, msg=msg,
                      shell_lines=[f"# Check: output contains '{needle}'"])

    def assert_not_in(self, needle: str, haystack, msg: str):
        """
        Assert that needle is NOT found in haystack.

            repo.assert_not_in("feature2:", output, "does not show feature2")
        """
        passed = needle not in haystack
        self._assertion_result(passed, msg,
                               f"'{needle}' unexpectedly found" if not passed else "")
        self._record("assert", check="not_contains", needle=needle, msg=msg,
                      shell_lines=[f"# Check: output does NOT contain '{needle}'"])

    def assert_equal(self, expected, actual, msg: str):
        """
        Assert that two values are equal.

            repo.assert_equal(0, repo.last_exit_code, "command succeeded")
        """
        passed = expected == actual
        self._assertion_result(passed, msg,
                               f"expected {expected!r}, got {actual!r}" if not passed else "")
        self._record("assert", check="equal", expected=repr(expected), msg=msg,
                      shell_lines=[f"# Check: {msg}"])

    def assert_true(self, value: bool, msg: str):
        """
        Assert that a value is truthy.

            repo.assert_true("docs" in cl, "changelist exists")
        """
        self._assertion_result(bool(value), msg,
                               "value is falsy" if not value else "")
        self._record("assert", check="true", msg=msg,
                      shell_lines=[f"# Check: {msg}"])

    def assert_exit_code(self, expected: int, msg: str):
        """
        Assert that the last run() call had the expected exit code.

            repo.run("git cl add docs file.txt")
            repo.assert_exit_code(0, "git cl add should succeed")
        """
        actual = self.last_exit_code
        passed = actual == expected
        self._assertion_result(passed, msg,
                               f"exit code {actual} (expected {expected})" if not passed else "")
        self._record("assert", check="exit_code", expected=expected, msg=msg,
                      shell_lines=[f"# Check: exit code is {expected}"])

    # ---- Summary ----

    def _print_summary(self):
        """Print test results summary."""
        if self.quiet:
            return
        print(f"\n{'=' * 45}")
        print(f"Results: {self.tests_run} assertions")
        print(f"  Passed: {self.tests_passed}")
        print(f"  Failed: {self.tests_failed}")
        print(f"{'=' * 45}")

    # ---- Shell export ----

    def export_shell(self, title: str = "git-cl test") -> str:
        """
        Convert the recorded operations into a standalone shell script.

        The exported script is for reading and manual line-by-line
        execution. Assertions become comments that tell the reader
        what to look for.

            script = repo.export_shell("walkthrough: add and status")
            print(script)
        """
        lines = [
            "#!/usr/bin/env bash",
            f"# {title}",
            "#",
            "# This script was exported from a git-cl test.",
            "# Run it line by line to learn how git-cl works.",
            "# Lines starting with '# Check:' tell you what to expect.",
            "#",
            "set -euo pipefail",
            "",
        ]

        for entry in self.log:
            kind = entry["kind"]

            if kind == "section":
                lines.append("")
                lines.append(f"# === {entry['title']} ===")
                lines.append("")

            elif kind in ("setup", "run", "run_in", "write_file",
                          "mkdir", "delete_file", "assert"):
                for shell_line in entry.get("shell_lines", []):
                    lines.append(shell_line)

        lines.append("")
        lines.append('echo "All steps completed."')
        lines.append("")

        return "\n".join(lines)
