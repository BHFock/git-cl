# git-cl Test Suite

Automated integration tests for [git-cl](https://github.com/BHFock/git-cl). Each test script creates a temporary Git repository, runs git-cl commands, and verifies the results. Every test can also be exported as a standalone shell walkthrough — a step-by-step terminal session you can follow to learn how git-cl works.


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


## Shell Walkthroughs

Every test script supports `--export` to produce a self-contained shell script. These walkthroughs mirror the test scenarios but are written for reading and manual line-by-line execution. `# Check:` comments tell you what to expect at each step.

Here is a shortened example from `test_basic_add_status.py --export`:

```bash
#!/usr/bin/env bash
# git-cl walkthrough: add and status
#
# Run it line by line to learn how git-cl works.
# Lines starting with '# Check:' tell you what to expect.

set -euo pipefail

# Create a temporary Git repository
cd $(mktemp -d)
git init --quiet
git config user.email "test@git-cl.test"
git config user.name "git-cl test"

# === Setup: create files with an initial commit ===

echo "hello" > file1.txt
echo "world" > file2.txt
git add file1.txt file2.txt
git commit --quiet -m "Add initial files"
echo "hello modified" > file1.txt
echo "world modified" > file2.txt

# === Add files to a new changelist ===

git cl add feature1 file1.txt file2.txt
# Check: output contains 'Added to 'feature1''

# === View status grouped by changelist ===

git cl st
# Check: output contains 'feature1:'
# Check: output contains 'file1.txt'
# Check: output contains 'file2.txt'
```


## What's Tested

### Core Commands

| Script | Commands |
|---|---|
| `test_basic_add_status.py` | `add`, `status` / `st`, filtering, `--include-no-cl` |
| `test_stage_unstage.py` | `stage`, `unstage`, `--delete` flag, round-trip, multiple changelists |
| `test_commit.py` | `commit` / `ci`, `-m`, `-F`, `--keep` flag, multiple changelists |
| `test_diff.py` | `diff`, multiple changelists, `--staged` |
| `test_remove_delete.py` | `remove` / `rm`, `delete` / `del`, `--all` |
| `test_prune.py` | `prune`, `--dry-run` / `-n`, `--quiet` / `-q`, `--exit-code`, post-commit hook |
| `test_deleted_renamed.py` | `add`, `status`, `stage`, `commit` and `prune` with deleted and renamed files |
| `test_directories.py` | `add` rejects directories with a file list; `status` points out old directory entries |
| `test_special_paths.py` | file names with spaces, umlauts and quotes in `status`, `prune`, `stash` and `commit` |
| `test_symlinks.py` | symbolic links in `add`, `status`, `commit`, `prune` and `stash` (skipped on Windows) |
| `test_checkout.py` | `checkout` / `co`, `--delete`, `--force` |

### Advanced Commands

| Script | Commands |
|---|---|
| `test_stash_unstash.py` | `stash` / `sh`, `unstash` / `us`, `--all`, names ending in `_stashed` |
| `test_branch.py` | `branch` / `br`, custom name, `--from` base, untracked files outside changelists |

### States, Paths, and Validation

| Script | Focus |
|---|---|
| `test_git_states.py` | All common Git status codes (`[ M]`, `[M ]`, `[MM]`, `[A ]`, `[AM]`, `[ D]`, `[D ]`, `[??]`) |
| `test_subdirectory.py` | Path normalisation from subdirectories, cross-directory add, relative display |
| `test_validation.py` | Invalid names, reserved words, path traversal, missing arguments |
| `test_edge_cases.py` | Empty states, reassignment, duplicate files, deleted files |
| `test_exit_codes.py` | Exit codes `0`, `1` and `2`, errors and warnings on stderr, partial failure |
| `test_save_failures.py` | Failed writes of `cl.json` and `cl-stashes.json`: exit code `1`, stashed changes restored |
| `test_corrupt_metadata.py` | Damaged or wrongly shaped `cl.json` and `cl-stashes.json`: exit code `1`, files not overwritten, recovery |


## How the Tests Work

The test framework lives in `test_helpers.py` and provides a single class: `TestRepo`. It is used as a context manager that creates a fresh temporary Git repository on entry and cleans it up on exit.

`TestRepo` offers helpers for common operations — `write_file`, `run`, `run_in` (execute from a subdirectory), `load_cl_json`, `get_staged_files`, and a set of assertion methods (`assert_in`, `assert_equal`, `assert_exit_code`, etc.) that print pass/fail results during the test run. After each `run`, the exit code and the two output streams are available as `last_exit_code`, `last_stdout` and `last_stderr`.

Every operation is recorded internally. When a test script is run with `--export`, the recorded operations are replayed as a shell script instead of executing assertions. This is how the same test code serves both as an automated check and as a readable walkthrough. Commands that failed during the test run are exported with `|| true`, so that a deliberately triggered error does not stop the walkthrough at `set -euo pipefail`.

`fail_write.py` is not a test itself. `test_save_failures.py` runs git-cl through it to make writing one metadata file fail while reading it still works, as on a full disk or a read-only file system.

Each `test_*.py` script follows the same pattern: import `TestRepo`, define a `run_tests(repo)` function with sections and assertions, and handle both normal execution and `--export` mode in `__main__`. Test scripts are self-contained and can be run independently. `run_tests.py` discovers and runs all of them, collecting results into a summary.
