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

import os
import shlex
import shutil
import subprocess
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

    def __init__(self):
        self.repo_dir: Path | None = None
        self.last_exit_code: int = 0
        self.log: list[dict] = []

    def __enter__(self):
        self._setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._teardown()
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
