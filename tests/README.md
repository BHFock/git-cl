# git-cl Test Suite

## Purpose

This test suite provides automated integration tests for [git-cl](https://github.com/BHFock/git-cl). It serves two goals:

1. **Regression testing** — verify that git-cl behaves correctly across Python versions, Git versions, and operating systems.
2. **Worked examples** — each test script can be exported as a standalone shell walkthrough for user training.

git-cl is feature complete. These tests document and protect existing behaviour rather than driving new features.


## Design Decisions

### Why Python tests with shell export?

The test framework is written in Python, but each test can be exported as a self-contained shell script. This gives us:

- **Clean test logic** — assertions, JSON inspection, and temporary repo management are natural in Python.
- **Readable training material** — the exported shell scripts read as step-by-step terminal sessions a user can follow.
- **No external dependencies** — the framework uses only the Python standard library.

### What is tested?

Each test script creates a temporary Git repository, runs git-cl commands against it, and verifies the results by checking:

- **Command output** — does `git cl add` print the expected confirmation?
- **Exit codes** — does the command succeed or fail as expected?
- **Internal metadata** — does `.git/cl.json` contain the right changelist entries?
- **Git state** — are the correct files staged, committed, or reverted?
- **Git status codes** — are files in the expected state (`[ M]`, `[A ]`, `[??]`, etc.)?
- **Working directory context** — do commands behave correctly from subdirectories?

### What is NOT tested?

- Interactive terminal behaviour (colour output, terminal width)
- Concurrent access or file locking under load
- Platform-specific behaviour (Windows, network filesystems)


## Architecture

```
tests/
├── README.md                  ← this file
├── test_helpers.py            ← TestRepo class and shell export logic
├── run_tests.py               ← test runner (discovers and runs all test scripts)
├── test_basic_add_status.py
├── test_stage_unstage.py
├── test_commit.py
├── test_diff.py
├── test_remove_delete.py
├── test_checkout.py
├── test_stash_unstash.py
├── test_branch.py
├── test_validation.py
├── test_git_states.py
├── test_subdirectory.py
└── test_edge_cases.py
```

### test_helpers.py

Provides the `TestRepo` class — a context manager that:

- Creates a fresh temporary Git repository with an initial commit
- Offers helper methods for common operations (`write_file`, `run`, `load_cl_json`, ...)
- Records every operation so the session can be exported as a shell script
- Provides assertion methods that print pass/fail results and log themselves for export
- Cleans up the temporary directory on exit

#### run() — command execution

`run()` accepts commands as a string or as a list of arguments:

```python
# Simple commands — string is fine, parsed with shlex.split()
repo.run("git cl add docs file.txt")

# Arguments containing spaces — use a list for precise control
repo.run(["git", "cl", "commit", "docs", "-m", "Fix the bug"])
```

When a string is passed, it is split using `shlex.split()`, which handles quoted
arguments correctly (e.g. `'git cl commit docs -m "Fix the bug"'` works as expected).

When a list is passed, it is used directly as the argument vector.

For shell export, list-form commands are reconstructed with proper quoting.

#### run_in() — subdirectory execution

`run_in(subdir, command)` runs a command from within a subdirectory of the
repository, without changing the test process's working directory:

```python
# Test that adding a file from a subdirectory normalises the path
repo.run_in("src", "git cl add my-list main.py")
```

This passes `cwd=repo_dir/subdir` to `subprocess.run`. In the shell export, it
becomes a subshell: `(cd src && git cl add my-list main.py)`.

### Test scripts

Each test script is executable and follows the same structure:

```python
#!/usr/bin/env python3
from test_helpers import TestRepo

def run_tests(repo: TestRepo):
    repo.section("Setup")
    # ... prepare repository ...

    repo.section("Test scenario name")
    output = repo.run("git cl add my-list file.txt")
    repo.assert_in("Added to", output, "confirms addition")

    cl = repo.load_cl_json()
    repo.assert_true("my-list" in cl, "changelist exists")

if __name__ == "__main__":
    # Handles both test execution and --export
    ...
```

### Shell export

Every test script supports `--export` to produce a shell walkthrough:

```
./test_basic_add_status.py --export > walkthrough_add_status.sh
```

The exported script contains:
- The same git-cl commands as the Python test
- `# Check:` comments where assertions were, describing expected outcomes
- Section headers matching the test structure

In export mode, assertion output (pass/fail lines) is suppressed. Only the
shell script is written to stdout.

The exported scripts are for reading and manual line-by-line execution, not
for automated testing.


## Test Plan

### Core Commands

| Script                        | Commands under test                    | Key behaviours verified                                    |
|-------------------------------|----------------------------------------|------------------------------------------------------------|
| `test_basic_add_status.py`    | `add`, `status`, `st`                  | Creating changelists, assigning files, reassignment,       |
|                               |                                        | status grouping, filtering, `--include-no-cl`, aliases     |
| `test_stage_unstage.py`       | `stage`, `unstage`                     | Staging tracked files, skipping untracked files,           |
|                               |                                        | `--delete` flag, round-trip stage/unstage, changelist      |
|                               |                                        | preserved by default                                       |
| `test_commit.py`              | `commit`, `ci`                         | Commit with `-m` and `-F`, `--keep` flag, changelist       |
|                               |                                        | deleted by default, untracked files skipped, alias         |
| `test_diff.py`                | `diff`                                 | Single changelist diff, multiple changelist diff,          |
|                               |                                        | `--staged` flag                                            |
| `test_remove_delete.py`       | `remove`, `rm`, `delete`, `del`        | Removing files from changelists, deleting changelists,     |
|                               |                                        | `--all` flag, files untouched on disk, aliases             |
| `test_checkout.py`            | `checkout`, `co`                       | Reverting files to HEAD, only affects named changelist,    |
|                               |                                        | changelist kept by default, `--delete` flag, alias         |

### Advanced Commands

| Script                        | Commands under test                    | Key behaviours verified                                    |
|-------------------------------|----------------------------------------|------------------------------------------------------------|
| `test_stash_unstash.py`       | `stash`, `unstash`                     | Stash single changelist, unstash restores files and        |
|                               |                                        | metadata, `--all` flag, selective unstash after stash all  |
| `test_branch.py`              | `branch`, `br`                         | Branch from changelist, custom branch name, `--from` base, |
|                               |                                        | other changelists stashed, alias                           |

### Git States and Working Directory

| Script                        | Focus area                             | Key behaviours verified                                    |
|-------------------------------|----------------------------------------|------------------------------------------------------------|
| `test_git_states.py`          | Git status codes                       | Changelists with files in each common state:               |
|                               |                                        | `[ M]` unstaged modification, `[M ]` staged modification, |
|                               |                                        | `[MM]` mixed staged/unstaged, `[A ]` newly added,         |
|                               |                                        | `[AM]` added then modified, `[ D]` unstaged deletion,     |
|                               |                                        | `[D ]` staged deletion, `[??]` untracked.                 |
|                               |                                        | Correct display in `git cl st`, correct behaviour with     |
|                               |                                        | `--all` flag for uncommon codes.                           |
| `test_subdirectory.py`        | Path resolution                        | Running git-cl commands from the repo root, a subdirectory,|
|                               |                                        | and a nested subdirectory. Verifying that paths are stored |
|                               |                                        | as repo-root-relative in `cl.json` and displayed correctly |
|                               |                                        | relative to the current working directory.                 |

### Validation and Edge Cases

| Script                        | Focus area                             | Key behaviours verified                                    |
|-------------------------------|----------------------------------------|------------------------------------------------------------|
| `test_validation.py`          | Input validation                       | Invalid changelist names (special chars, reserved words,   |
|                               |                                        | dots-only, too long), dangerous paths, directory traversal,|
|                               |                                        | non-existent files, non-existent changelists               |
| `test_edge_cases.py`          | Boundary conditions                    | Empty working directory, no changelists, nested            |
|                               |                                        | subdirectories, deleted files, file reassignment,          |
|                               |                                        | already-staged files, rapid add/remove cycles              |


## Requirements

- Python 3.9+
- Git
- A Unix-like OS (Linux, macOS)
- `git-cl` available in `$PATH`


## Usage

Run all tests:

```
./run_tests.py
```

Run a single test:

```
./test_basic_add_status.py
```

Export a test as a shell walkthrough:

```
./test_basic_add_status.py --export > walkthrough_add_status.sh
```


## Resolved Design Decisions

> Decisions made during development of the test framework.

### Commit messages with spaces

`run()` uses `shlex.split()` when given a string, which correctly handles quoted
arguments. For full control, a list of arguments can be passed instead. Shell export
reconstructs the command with proper quoting from the list form.

### Subdirectory execution

`run_in(subdir, command)` sets the `cwd` for the subprocess without affecting the
test process. Exported as `(cd subdir && command)` in shell scripts.

### Export noise

In `--export` mode, all assertion output is suppressed. Only the shell script is
written to stdout. This means `./test_basic_add_status.py --export > walkthrough.sh`
produces a clean file with no test noise mixed in.

### Test runner

`run_tests.py` discovers `test_*.py` files in its directory, runs each as a subprocess,
collects exit codes, and prints a summary. Each test script is self-contained and can
be run independently.
