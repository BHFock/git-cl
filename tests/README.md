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

### What is NOT tested?

- Interactive terminal behaviour (colour output, terminal width)
- Concurrent access or file locking under load
- Platform-specific behaviour (Windows, network filesystems)


## Architecture

```
tests/
├── README.md              <= this file
├── test_helpers.py        <= TestRepo class and shell export logic
├── run_tests.py           <= test runner (discovers and runs all test scripts)
├── test_basic_add_status.py
├── test_stage_unstage.py
├── test_commit.py
├── test_diff.py
├── test_remove_delete.py
├── test_checkout.py
├── test_stash_unstash.py
├── test_branch.py
├── test_validation.py
└── test_edge_cases.py
```

### test_helpers.py

Provides the `TestRepo` class — a context manager that:

- Creates a fresh temporary Git repository with an initial commit
- Offers helper methods for common operations (`write_file`, `run`, `load_cl_json`, ...)
- Records every operation so the session can be exported as a shell script
- Provides assertion methods that print pass/fail results and log themselves for export
- Cleans up the temporary directory on exit

### Test scripts

Each test script follows the same structure:

```python
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

The exported scripts are for reading and manual line-by-line execution, not for automated testing.


## Test Plan

### Core Commands

| Script                        | Commands under test                    | Key behaviours verified                                    |
|-------------------------------|----------------------------------------|------------------------------------------------------------|
| `test_basic_add_status.py`    | `add`, `status`, `st`                  | Creating changelists, assigning files, reassignment,       |
|                               |                                        | status grouping, filtering, subdirectory paths, aliases    |
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


## Open Questions

> Items to resolve as development progresses.

- **Commit messages with spaces:** `run()` currently splits commands on whitespace. Commands like `git cl commit my-list -m "Fix the bug"` need a way to handle quoted arguments. Options: accept a list of arguments, or use `shlex.split()`.
- **Subdirectory execution:** testing `git cl add` from within a subdirectory requires changing the working directory. A `run_in(subdir, command)` helper could handle this cleanly.
- **Export noise:** when using `--export`, test output (pass/fail lines) is printed to stderr alongside the shell script on stdout. Consider suppressing test output in export mode, or writing it to a separate stream.
- **Test runner:** `run_tests.py` needs to discover test scripts, run each in a subprocess, and summarise results. Keep it simple — no need for pytest-level machinery.
