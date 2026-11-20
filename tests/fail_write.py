#!/usr/bin/env python3
"""
fail_write.py — Run git-cl with writes to one metadata file failing.

Used by test_save_failures.py. Reading the file works as usual; only
replacing it with new content fails, as on a full disk or a read-only
file system.

Usage:
    python3 fail_write.py <cl.json|cl-stashes.json> <git-cl arguments>

Example:
    python3 fail_write.py cl-stashes.json stash feature
"""

import errno
import os
import runpy
import sys
from pathlib import Path


def find_git_cl() -> str:
    """Return the path of the git-cl script on PATH."""
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / "git-cl"
        if candidate.is_file():
            return str(candidate)
    sys.exit("fail_write.py: git-cl not found on PATH")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)

    target = sys.argv[1]
    real_replace = os.replace

    def failing_replace(src, dst, *args, **kwargs):
        if Path(dst).name == target:
            raise OSError(errno.EACCES, "Simulated write failure", str(dst))
        return real_replace(src, dst, *args, **kwargs)

    os.replace = failing_replace
    script = find_git_cl()
    sys.argv = [script] + sys.argv[2:]
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
