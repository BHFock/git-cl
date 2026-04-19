# git-cl Design Notes

[git-cl](https://github.com/BHFock/git-cl) is a Git subcommand for managing named changelists within a Git working directory. It allows grouping files into changelists before staging or committing. The main design goal is to help review code changes with [git cl status](tutorial.md#22-view-status-by-changelist), but the functionality also supports [stashing](tutorial.md#31-stash-and-unstash-changelists) and [branching](tutorial.md#32-create-a-branch-from-a-changelist) based on changelists.

This document describes the design of `git-cl` to help future maintenance.

## Table of Contents

- [Conceptual Model](#conceptual-model)
- [Technical Architecture](#technical-architecture)
  - [Code and Data Organisation](#code-and-data-organisation)
  - [Runtime Behaviour](#runtime-behaviour)
  - [Security and Safety](#security-and-safety)
- [Core Algorithms](#core-algorithms)
  - [Path Resolution Algorithm](#path-resolution-algorithm)
  - [Git Status Parsing](#git-status-parsing)
  - [Stash Categorisation Rules](#stash-categorisation-rules)
  - [Unstash Conflict Detection](#unstash-conflict-detection)
  - [Branching Workflow](#branching-workflow)
  - [Platform Considerations](#platform-considerations)
  - [Performance Considerations](#performance-considerations)
- [Design Decisions FAQ](#design-decisions-faq)
- [Future Direction](#future-direction)

## Conceptual Model

[git-cl](https://github.com/BHFock/git-cl) adds a layer of changelist metadata alongside Git’s staging and commit mechanisms. While Git’s index reflects staged changes, changelists records logical groupings of files regardless of their Git status. This separation allows changelists to persist across staging, stashing, and branching.

The changelist layer supports intentional workflows: grouping related changes for review, isolating work before staging, and enabling targeted operations without relying on Git’s index or history. By decoupling file organisation from Git’s internal state, [git-cl](https://github.com/BHFock/git-cl) offers a stable and portable way to manage work-in-progress.

git-cl operates at the file level — it groups whole files by intent, not hunks or patches. Patch-level editing is intentionally left to other Git tools.

## Technical Architecture

### Code and Data Organisation

#### File Structure 

Changelists, created with [git cl add](tutorial.md#21-add-files-to-a-changelist), are stored in `.git/cl.json`. The human readable [JSON](https://en.wikipedia.org/wiki/JSON) format allows easy review of how changelists are stored. For example this `git cl st` (executed from the folder `~git-cl_test/folder1`): 

```
list1:
  [  ] ../LICENSE
  [ M] ../README.md
list2:
  [A ] file1.txt
```

is stored in `.git/cl.json` as 

```
{
  "list1": [
    "LICENSE",
    "README.md"
  ],
  "list2": [
    "folder1/file1.txt"
  ]
}
```


Storing `cl.json` in `.git/` allows moving the repository locally while keeping changelists intact, because file paths in `cl.json` are stored relative to the repository root. `git cl st` displays paths relative to the current working directory. The details of how these paths are transformed for display or Git operations are described in the [Path Resolution Algorithm](#path-resolution-algorithm) section.

`.git/cl.json` is not part of the Git history. This keeps changelists as a "pre-staging" layer separate from Git's version control.
  
[Stash](tutorial.md#31-stash-and-unstash-changelists) metadata is stored in `.git/cl-stashes.json`. This keeps the stashes separate from the changelist files and allowed an implementation of the more advanced `git cl stash` and `git cl unstash` without impacting the implementation of the basic functions.

Using `git cl stash list2` in the above example removes `list2` from `.git/cl.json` but adds the following stash metadata to `.git/cl-stashes.json`:

```
{
  "list2": {
    "stash_ref": "stash@{0}",
    "stash_message": "git-cl-stash:list2:20250814_071516",
    "files": [
      "folder1/file1.txt"
    ],
    "timestamp": "2025-08-14T07:15:16.948160",
    "source_branch": "main",
    "file_categories": {
      "unstaged_changes": [],
      "staged_additions": [
        "folder1/file1.txt"
      ],
      "untracked": [],
      "deleted_files": []
    }
  }
}
```

Note that `.git/cl-stashes.json` only contains changelist metadata - the actual file contents are stored in Git's native stash mechanism (accessible via [git stash list](https://git-scm.com/docs/git-stash#Documentation/git-stash.txt-listlog-options)). The `stash_ref` field connects git-cl's metadata to the underlying Git stash entry, enabling coordinated restoration of both file changes and changelist structure.

Both `cl.json` and `cl-stashes.json` are written atomically: the new contents are written to a temporary file in `.git/` and then renamed over the target via `os.replace()`. This ensures that if the process is interrupted mid-write, the original file is left intact rather than truncated, which would otherwise be silently interpreted as an empty metadata store on the next read.

#### Code Structure

The code is organised in a single file for simple installation. Code navigation is facilitated by clear section headers that group related functionality.

##### `# INTERNAL UTILITIES`

Utility functions needed to keep the CLI functions at reasonable length use the name convention `clutil_function_name` and are stored together at the beginning of the script in the `INTERNAL UTILITIES` section.

##### `# BRANCH WORKFLOW UTILITIES`

Utility functions only used by the `cl_branch` function are grouped in this section. These functions break down `cl_branch` into manageable components to maintain code readability and reduce complexity.

##### `# CLI COMMANDS`

This section includes the definition of the main functions callable in git-cl. The functions provide interactions with the changelist metadata and the git repository.

| Changelist Command Function | Tutorial                                                  | Type of Command                  |
|-----------------------------|-----------------------------------------------------------|----------------------------------|
| `cl_add`                    | [cl add](tutorial.md#21-add-files-to-a-changelist)        | Changelist Organisation Commands |
| `cl_remove`                 | [cl rm](tutorial.md#26-remove-files-from-changelists)     |                                  |
| `cl_delete`                 | [cl del](tutorial.md#27-delete-changelists)               |                                  |
| `cl_status`                 | [cl st](tutorial.md#22-view-status-by-changelist)         | Display Commands                 |
| `cl_diff`                   | [cl diff](tutorial.md#23-diff-a-changelist)               |                                  |
| `cl_stage`                  | [cl stage](tutorial.md#stage-a-changelist)                | State Changing Commands          |
| `cl_unstage`                | [cl unstage](tutorial.md#unstage-a-changelist)            |                                  |
| `cl_checkout`               | [cl co](tutorial.md#28-checkout-a-changelist)             |                                  |
| `cl_commit`                 | [cl ci](tutorial.md#25-commit-a-changelist)               |                                  |
| `cl_stash`                  | [cl stash](tutorial.md#stash-a-changelist)                | Advanced Workflow Commands       |
| `cl_unstash`                | [cl unstash](tutorial.md#unstash-a-changelist)            |                                  |
| `cl_branch`                 | [cl br](tutorial.md#32-create-a-branch-from-a-changelist) |                                  |

##### `# MAIN ENTRY POINT`

This section includes the `main` function which serves as the entry point. It uses [argparse](https://docs.python.org/3/library/argparse.html) to define the user interface for subcommands like add, status, commit, branch, etc.

This section also includes the definition of the command line help. Defining the help via `argparse` means that the main help command is available via `git cl help` but not via `git help cl`. Defining the help via `git help cl` would require creating man pages to be installed with git. This has been left out for simplicity.

### Runtime Behaviour

#### Concurrency and Locking

`git-cl` uses platform-specific file locking (fcntl on Unix, msvcrt on Windows) to lock metadata files, preventing race conditions. It is designed for single-user interactive use rather than shared accounts or scripts.

`clutil_file_lock` implements a [context manager](https://book.pythontips.com/en/latest/context_managers.html) that creates temporary `.lock` files (e.g., `cl.json.lock`) with exclusive locks. All metadata read/write operations are wrapped in these locks, with automatic cleanup on exit or exception.

#### Error Handling and Exit Codes

`git-cl` exits with code `0` on success and non-zero codes on errors. Error messages are printed to `stderr`. Some functions terminate execution immediately on fatal errors using [sys.exit()](https://docs.python.org/3/library/sys.html#sys.exit), ensuring no partial metadata changes are written.

#### Command Categories and Git State

`git-cl` commands fall into three categories based on what they touch:

* **Metadata-only** (`add`, `remove`, `delete`) — modify `cl.json` without affecting Git state.
* **Read-only** (`status`, `diff`) — inspect Git state but do not modify it.
* **State-mutating** (`stage`, `unstage`, `commit`, `stash`, `unstash`, `checkout`, `branch`) — call Git commands that change repository state.

This distinction matters during unresolved merges. State-mutating commands detect merge-conflict status codes (`UU`, `AA`, `DD`, `AU`, `UA`, `DU`, `UD`) and refuse cleanly with a message pointing at `git merge --abort` or manual resolution. Without this guard, the underlying Git calls would either fail with cryptic errors or, worse, proceed with partial operations that leave the repository in an unclear state.
Metadata-only commands are deliberately exempt: a user mid-merge may legitimately want to reorganise changelists — for example, to pull a conflicted file out of a changelist so they can resolve it separately. Read-only commands surface conflicts in their output rather than refusing.

### Security and Safety

`git-cl` implements multiple security layers to protect against malicious input and filesystem vulnerabilities whilst maintaining safe operation across different environments.

#### Path Safety and Traversal Protection

All user-provided file paths undergo strict validation through `clutil_sanitize_path()`:

- **Directory traversal prevention** - Rejects `../../../etc/passwd` style attacks through path resolution
- **Repository boundary enforcement** - Ensures paths remain within the Git repository using `Path.relative_to(git_root)`
- **Dangerous character filtering** - Blocks `;`, `|`, `&`, backticks, `$`, newlines, and null bytes
- **Path normalisation** - Converts to absolute paths, then repo-relative for consistent storage

#### Input Validation

Beyond path safety, all user inputs are validated:

- **Changelist names** - `clutil_validate_name()` restricts to alphanumeric characters, hyphens, underscores, and dots
- **Git reserved words** - Prevents conflicts with `HEAD`, `FETCH_HEAD`, `index`, etc.
- **Commit message files** - `clutil_read_commit_message_file()` enforces 64KB size limits
- **Length restrictions** - Changelist names capped at 100 characters

#### Filesystem and Git Safety

Operations use defensive programming patterns:

- **Atomic metadata updates** - `clutil_file_lock()` provides exclusive access with automatic cleanup
- **Rollback capabilities** - Stash operations recover from partial failures by dropping orphaned Git stashes
- **Command injection prevention** - Uses `subprocess.run()` with list arguments, never shell strings
- **Safe argument handling** - All paths passed to Git are pre-validated

#### Security Limitations

`git-cl` targets single-user interactive use with intentional limitations:

- **Single-user file locking** — Uses `fcntl` (Unix) / `msvcrt` (Windows); unsuitable for shared accounts or concurrent automation
- **Local threat model** - Assumes trusted Git repository and filesystem
- **No cryptographic validation** - JSON metadata lacks signatures or checksums

The security model prioritises preventing common accidents and basic attacks whilst maintaining simplicity for typical single-developer workflows.

## Core Algorithms

### Path Resolution Algorithm

File paths in `git-cl` need to work consistently whether you're in a subdirectory or the repository root, and whether the repository is moved between machines. The path resolution system handles this by maintaining three distinct representations throughout the codebase:

- **Repo-root relative** - stored in `.git/cl.json` (e.g., `src/main.py`)
- **CWD relative** - used for Git commands and display (e.g., `../src/main.py`)
- **Absolute** - used for internal validation and checks

#### Key Functions:

- `clutil_sanitize_path()` - validates user input and converts to repo-root relative format for storage
- `clutil_format_file_status()` - converts stored paths to CWD-relative format for display

#### Conversion Pipeline:

**1. Input Validation** - `clutil_sanitize_path()` takes user-provided paths, resolves relative components (like ../), ensures they're within the Git repository, and rejects dangerous characters.

**2. Storage Normalization** - The system converts all validated paths to repo-root relative format using [Path.relative_to](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.relative_to)(git_root).[as_posix()](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.as_posix) before storing in `.git/cl.json`.

**3. Display Conversion** - `clutil_format_file_status()` converts stored repo-root relative paths back to CWD-relative paths using `os.path.relpath()` for user display and Git command compatibility.

This three-stage approach ensures repository portability (paths work regardless of where the repo is moved) while maintaining compatibility with standard Git commands that expect CWD-relative paths

### Git Status Parsing

Git's `status --porcelain` output needs to be transformed into changelist-grouped display. The transformation has four stages: collection, parsing with filtering, changelist grouping, and display formatting.

`clutil_get_git_status` runs `git status --porcelain` with the `--untracked-files=all` flag and returns the raw output lines. `clutil_get_file_status_map` then parses each line, extracting the two-character status code and the file path. Renamed files (which appear as `old -> new`) are normalised to the new path. Paths are converted to repository-root-relative form using `Path.relative_to(git_root).as_posix()` for consistent internal representation, and the result is returned as a `dict[str, str]` mapping paths to status codes.

During parsing, codes are filtered against an allowlist rather than a denylist. The `INTERESTING_CODES` set contains the common working-directory states (`??`, ` M`, `M `, `MM`, `A `, `AM`, ` D`, `D `, `R `, `RM`) together with the seven merge-conflict codes (`UU`, `AA`, `DD`, `AU`, `UA`, `DU`, `UD`). Merge conflicts are included in the default view because they require immediate user action; rare codes like type changes (`T `) and copy renames are filtered unless `--all` is passed. Files with filtered codes are counted and reported with a summary note, so the user knows something was hidden.

`cl_status` iterates through loaded changelists, looks up each file's status in the map, and passes it to `clutil_format_file_status` for display. The formatter converts repo-relative paths back to current-working-directory-relative using `os.path.relpath()`, applies colour, and returns a string with the `[XX]` status prefix.

The colour rules are:

- `??` — blue (untracked)
- Staged-only (`X `) — green (ready to commit)
- Unstaged-only (` X`) — red (working-directory changes)
- Merge conflict (`UU`, `AA`, etc.) — red (blocking state, matches git's own convention)
- Mixed staged+unstaged (`XX`) — magenta (both staged and unstaged changes in the same file)

The merge-conflict branch sits at the top of the colour-selection chain in `clutil_format_file_status`. Without that placement, codes like `AA` would fall through to the `staged == 'A'` branch and render green, which would be actively misleading for a file that actually needs resolving.

If the `colorama` module isn't available, the formatter falls back to plain text via dummy colour objects, so output works uncoloured rather than failing.

### Stash Categorisation Rules

`git cl stash` will only stash files that `git stash push` can actually handle. Categorising files up front, before any Git command runs, means failures are reported against the changelist rather than surfacing as cryptic errors from a half-completed stash.

`clutil_categorize_files_for_stash` checks each file's Git status and sorts it into one of these buckets:

| Git status                                                | Stashable?    |
|----------------------------------------------------------|---------------|
| Unstaged changes (modified/deleted in working directory) | stashable     |
| Staged additions (newly added to index)                  | stashable     |
| Untracked files (if explicitly in changelist)            | stashable     |
| Staged modifications (only staged changes, no unstaged)  | not stashable |
| Clean files (no changes)                                 | not stashable |

Files must have unstaged changes, be newly added to the index, or be untracked (but explicitly included in the changelist) to be stashable. This matches `git stash push` behaviour, which cannot stash files that only have staged modifications without unstaged changes.

### Unstash Conflict Detection

Unstashing a changelist needs to distinguish file states that genuinely block `git stash pop` from states that merely look concerning but are fine. Being too conservative here would make unstash refuse in cases where it would actually succeed; being too permissive would let users hit cryptic Git errors mid-operation.

`clutil_check_unstash_conflicts_optimized` performs this check using a lookup table (`UNSTASH_STATUS_ANALYSIS`) keyed on the two-character status code. Real blocking conflicts are untracked files at the target path (which would be overwritten by the stash restoration) and working-directory modifications or deletions (which would conflict with the stashed changes). Staged changes and clean files are safe — the stash applies on top without collision. Missing files are treated as ideal: the stash will restore them with no conflict at all.

When conflicts are detected, `clutil_suggest_workflow_actions` produces context-specific advice — for example, suggesting `git checkout -- <file>` for working-directory modifications or `git rm` for files deleted in the working directory. The suggestions are tailored to the stash→branch→unstash workflow that `cl_branch` automates, since that's where most unstash operations happen in practice.

### Branching Workflow

`cl_branch` automates the stash→branch→unstash sequence in a single operation, so users can move a changelist to its own branch without manually coordinating the three steps.

Before doing anything destructive, the command performs three safety checks. `clutil_validate_branch_preconditions` ensures the target changelist exists and is active (not already stashed). `clutil_check_branch_exists` refuses if a branch with the target name already exists. `clutil_check_unassigned_changes` detects uncommitted changes that aren't assigned to any changelist and aborts with an error — this prevents accidental data loss, since unassigned changes would otherwise get caught up in the stash-all step with no clear way to identify them afterwards.

Once the checks pass, `clutil_stash_all_changelists` stashes every active changelist (including the target), leaving a clean working directory. `clutil_create_branch` creates and checks out the new branch from the specified base, or from the current HEAD if `--from` wasn't given. `clutil_unstash_changelist` then restores only the target changelist onto the new branch. The other changelists stay stashed and can be restored later with `git cl unstash`.

If branch creation or the final unstash fails, `clutil_handle_branch_creation_failure` attempts to restore all stashed changelists by calling `cl_unstash --all --force`. This isn't a perfect rollback — if the failure happened after the branch checkout, the restoration lands on the new branch rather than the original one — but it avoids leaving changelists stranded in the stash with no obvious recovery path. Partial failures are reported for manual cleanup.

#### Example

Starting on `main` with two changelists:

```
feature-a  (5 files)
bugfix     (3 files)
```

After `git cl branch feature-a`:

```
main:       feature-a and bugfix both stashed
feature-a:  feature-a unstashed, ready for development
```

The other changelists are available via `git cl unstash` whenever needed.

### Platform Considerations

#### Path Handling Differences
`git-cl` normalises all paths to forward slashes (Git standard) via `.as_posix()` for consistent storage across platforms. The [pathlib.Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path) module abstracts away OS-specific path handling differences.

#### Terminal Colour Detection  
Colour output depends on [colorama](https://pypi.org/project/colorama/) for cross-platform compatibility. The implementation gracefully degrades to plain text when colour support is unavailable.

#### File Locking Differences
Uses `fcntl` on Unix and `msvcrt` on Windows for metadata locking. On Unix, `fcntl.flock` blocks indefinitely; on Windows, `msvcrt.locking` retries for approximately ten seconds before raising an error. Both are advisory locks suitable for single-user interactive usage, where race conditions are unlikely.

### Performance Considerations

#### Large Repository Handling
`git-cl` has been tested with repositories containing ~250k lines of code across ~1600 files without performance issues. The design avoids loading entire repository state into memory, instead relying on `git status --porcelain` for file state queries and processing changelists incrementally.

#### Memory Usage Patterns
Memory usage scales with the number of files in active changelists rather than total repository size. Metadata is stored in lightweight JSON files and loaded only when needed. The largest memory consumers are Git subprocess calls and status parsing, which are handled efficiently by the standard library.

#### Git Command Optimisation

Leverages Git's native commands (`git status`, `git stash`, etc.) rather than reimplementing Git functionality. File operations are batched where possible (e.g., `git add` with multiple files) to minimise subprocess overhead. Within commands that iterate over changelist files, the result of `git status --porcelain` is fetched once and reused rather than re-queried per file.

## Design Decisions FAQ

### Why store metadata in .git/ instead of tracked files?
- Keeps changelists separate from version control as a "pre staging area"
- Survives repository moves while staying private to local development

### Why use a single file instead of a Python package?
- Zero-dependency installation and easy deployment
- Self-contained for air-gapped systems

### Why JSON for metadata storage?
- Human readable with native [Python support](https://docs.python.org/3/library/json.html) for read and write operations
  
### Why relative paths in cl.json?
- Repository portability (can move anywhere)
- Works regardless of mount points
- Consistent with Git's internal path handling

### Why fcntl/msvcrt locking instead of Git's index locking?
- Simpler implementation using platform-native advisory locks
- Independent of Git's internal mechanisms
- Sufficient for single-user interactive use case

### Why use argparse instead of a more modern CLI framework?
- Part of Python standard library with automatic help generation
- Sufficient for git-cl's simple command structure

### Do changelists work with Git worktrees?

Each worktree maintains its own independent set of changelists. This follows naturally from how `git rev-parse --git-dir` works: in a linked worktree it returns a worktree-specific path inside `.git/worktrees/<name>/` rather than the main `.git/` directory, so cl.json is stored and read independently per worktree. Changelists created in one worktree are not visible in another, which is consistent with worktrees representing separate working contexts on separate branches.

`git cl` branch correctly detects branch name conflicts arising from worktrees and reports them with a clear error and suggested fix.

## Future direction

The aim is to keep functionality focused while improving code quality. Priority areas include handling edge cases, general refactoring for maintainability, and improving tests. The single-file structure should be preserved for deployment simplicity.
