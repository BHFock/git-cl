#!/usr/bin/env python3
"""
test_helpers.py — Test framework for git-cl.

Provides the TestRepo class: a context manager that creates a temporary
Git repository for testing git-cl commands.

Usage:

    from test_helpers import TestRepo

    with TestRepo() as repo:
        # repo.repo_dir is a fresh Git repository
        # with an initial commit already made
        pass
    # temporary directory is cleaned up here
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class TestRepo:
    """
    A temporary Git repository for testing git-cl.

    Creates a fresh repository on entry, removes it on exit.

    Attributes:
        repo_dir:  Path to the temporary repository root.
    """

    def __init__(self):
        self.repo_dir: Path | None = None

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
