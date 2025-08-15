# git-cl Design Notes

[git-cl](https://github.com/BHFock/git-cl) is a Git subcommand for managing named changelists within a Git working directory. It allows grouping files into changelists before staging or committing. The main design goal is to help review code changes with [git cl status](tutorial.md#22-view-status-by-changelist), but the functionality also supports [stashing](tutorial.md#31-stash-and-unstash-changelists) and [branching](tutorial.md#32-create-a-branch-from-a-changelist) based on changelists.

This document describes the design of `git-cl` to help future maintenance. Note that links to code examples are pinned to certain versions of the code which may have evolved since creating the links.

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

The changelist layer supports intentional workflows: grouping related changes for review, isolating work before staging, and enabling targeted operations without relying on Git’s index or history. By decoupling file organisation from Git’s internal state, [git-cl](https://github.com/BHFock/git-cl) offers a stable and portable way to manage work-in-progress

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

Using `git cl stash list2` in the above example removes `list2` from `.git/cl.json` but adds the follwing stash metadata to `.git/cl-stashes.json`:

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

#### Code Structure

The code is organised in a single file for simple installation. Code navigation is facilitated by clear section headers that group related functionality.

##### [# INTERNAL UTILITIES](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L90)

Utility functions needed to keep the [CLI functions](https://github.com/BHFock/git-cl/blob/main/docs/design-notes.md#-cli-commands) at reasonable length use the name convention `clutil_function_name` and are stored together at the beginning of the script in the `INTERNAL UTILITIES` section.

##### [# BRANCH WORKFLOW UTILITIES](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2048)

Utility functions only used by the [cl_branch](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2809) function are grouped in this section. These functions break down `cl_branch` into manageable components to maintain code readability and reduce complexity.

##### [# CLI COMMANDS](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2146)

This section includes the definition of the main functions callable in git-cl. The functions provide interactions with the changelist metadata and the git repository.

| Changelist Command Function                                             | Tutorial                                                  | Type of Command                  |
|-------------------------------------------------------------------------|-----------------------------------------------------------|----------------------------------|
| [cl_add](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2150)      | [cl add](tutorial.md#21-add-files-to-a-changelist)        | Changelist Organisation Commands |
| [cl_remove](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2526)   | [cl rm](tutorial.md#26-remove-files-from-changelists)     |                                  |
| [cl_delete](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2559)   | [cl del](tutorial.md#27-delete-changelists)               |                                  |
| [cl_status](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2318)   | [cl st](tutorial.md#22-view-status-by-changelist)         | Display Commands                 |
| [cl_diff](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2356)     | [cl diff](tutorial.md#23-diff-a-changelist)               |                                  |
| [cl_stage](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2206)    | [cl stage](tutorial.md#stage-a-changelist)                | State Changing Commands          |
|  [cl_unstage](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2258) | [cl unstage](tutorial.md#unstage-a-changelist)            |                                  |
| [cl_checkout](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2408) | [cl co](tutorial.md#28-checkout-a-changelist)             |                                  |
| [cl_commit](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2596)   | [cl ci](tutorial.md#25-commit-a-changelist)               |                                  |
| [cl_stash](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2655)    | [cl stash](tutorial.md#stash-a-changelist)                | Advanced Workflow Commands       |
| [cl_unstash](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2753)  | [cl unstash](tutorial.md#unstash-a-changelist)            |                                  |
| [cl_branch](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2809)   | [cl br](tutorial.md#32-create-a-branch-from-a-changelist) |                                  |

##### [# MAIN ENTRY POINT](https://github.com/BHFock/git-cl/blob/e0bd57f450762f752e13483c1d2ae383f5ba79e3/git-cl#L2921)

This section includes the [main function](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2916) which serves as the entry point. It uses [argparse](https://docs.python.org/3/library/argparse.html) to define the user interface for subcommands like [add](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2950), [status](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2992), [commit](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L3093), [branch](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L3162), etc. 

This section also includes the definition of the command line help. Defining the help via `argparse` means that the main help command is available via `git cl help` but not via `git help cl`. Defining the help via `git help cl` would require creating man pages to be installed with git. This has been left out for simplicity.

### Runtime Behaviour

#### Concurrency and Locking

`git-cl` uses [fcntl](https://docs.python.org/3/library/fcntl.html) to lock metadata files preventing race conditions. It is designed for single-user interactive use rather than shared accounts or scripts.

[`clutil_file_lock`](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L99) implements a [context manager](https://book.pythontips.com/en/latest/context_managers.html) that creates temporary `.lock` files (e.g., `cl.json.lock`) with exclusive locks. All metadata read/write operations are wrapped in these locks, with automatic cleanup on exit or exception.

#### Error Handling and Exit Codes

`git-cl` exits with code `0` on success and non-zero codes on errors. Error messages are printed to `stderr`. Some functions terminate execution immediately on fatal errors using [sys.exit()](https://docs.python.org/3/library/sys.html#sys.exit), ensuring no partial metadata changes are written.

### Security and Safety

`git-cl` implements multiple security layers to protect against malicious input and filesystem vulnerabilities whilst maintaining safe operation across different environments.

#### Path Safety and Traversal Protection

All user-provided file paths undergo strict validation through [clutil_sanitize_path()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L358):

- **Directory traversal prevention** - Rejects `../../../etc/passwd` style attacks through path resolution
- **Repository boundary enforcement** - Ensures paths remain within the Git repository using `Path.relative_to(git_root)`
- **Dangerous character filtering** - Blocks `;`, `|`, `&`, backticks, `$`, newlines, and null bytes
- **Path normalisation** - Converts to absolute paths, then repo-relative for consistent storage

#### Input Validation

Beyond path safety, all user inputs are validated:

- **Changelist names** - [clutil_validate_name()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L265) restricts to alphanumeric characters, hyphens, underscores, and dots
- **Git reserved words** - Prevents conflicts with `HEAD`, `FETCH_HEAD`, `index`, etc.
- **Commit message files** - [clutil_read_commit_message_file()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L529) enforces 64KB size limits
- **Length restrictions** - Changelist names capped at 100 characters

#### Filesystem and Git Safety

Operations use defensive programming patterns:

- **Atomic metadata updates** - [clutil_file_lock()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L99) provides exclusive access with automatic cleanup
- **Rollback capabilities** - Stash operations recover from partial failures by dropping orphaned Git stashes
- **Command injection prevention** - Uses `subprocess.run()` with list arguments, never shell strings
- **Safe argument handling** - All paths passed to Git are pre-validated

#### Security Limitations

`git-cl` targets single-user interactive use with intentional limitations:

- **Unix-only file locking** - Uses `fcntl`, unsuitable for shared accounts or Windows
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

- [clutil_sanitize_path()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L358) - validates user input and converts to repo-root relative format for storage
- [clutil_format_file_status()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L461) - converts stored paths to CWD-relative format for display

#### Conversion Pipeline:

**1. Input Validation** - [clutil_sanitize_path()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L358) takes user-provided paths, resolves relative components (like ../), ensures they're within the Git repository, and rejects dangerous characters.

**2. Storage Normalization** - The system converts all validated paths to repo-root relative format using [Path.relative_to](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.relative_to)(git_root).[as_posix()](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.as_posix) before storing in `.git/cl.json`.

**3. Display Conversion** - [clutil_format_file_status()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L461) converts stored repo-root relative paths back to CWD-relative paths using `os.path.relpath()` for user display and Git command compatibility.

This three-stage approach ensures repository portability (paths work regardless of where the repo is moved) while maintaining compatibility with standard Git commands that expect CWD-relative paths


#### Git Status Parsing

Git's `status --porcelain` output needs to be transformed into changelist-grouped display. This happens in several stages:

**Overview:** Raw Git status → Filtered status codes → Grouped by changelist → Formatted for display

**Detailed Pipeline:**
1. Status Collection - [clutil_get_git_status]...


### Git Status Parsing

The status display system transforms Git's repository state into changelist-grouped output through a multi-stage pipeline implemented across several utility functions.

#### Detailed Pipeline:

**1. Status Collection** - [clutil_get_git_status](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L307) runs `git status --porcelain` with optional `--untracked-files=all` flag. Returns raw output lines as list.

**2. Parsing and Filtering** - [clutil_get_file_status_map](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L387) processes each line:

- Extracts 2-character Git status codes (`M `, `??`, `A `) and file paths from each line
- Handles renamed files by parsing old -> new syntax
- Filters against [INTERESTING_CODES](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L399) allowlist (`??`, ` M`, `M `, `MM`, `A `, `AM`, ` D`, `D `, `R `, `RM`)
- Counts and reports skipped files unless --all specified
- Returns `dict[str, str]` mapping file paths to status codes

**3. Path Normalization** - Converts all paths to repository-root relative format using `Path.relative_to(git_root).as_posix()` for consistent internal representation.

**4. Changelist Grouping** -  [cl_status](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2318) iterates through loaded changelists, checking file membership and calling display formatting for each group.

**5. Display Formatting** - [clutil_format_file_status](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L461) handles final presentation:

- Converts repo-relative paths back to CWD-relative using os.path.relpath
- Applies color coding via clutil_should_use_color and colorama constants
- Returns formatted string with [XX] status prefix

**Color Logic:** Status codes are [mapped](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L464) to colors in `clutil_format_file_status`:

- `??` → Blue (untracked)
- Staged-only (`X `) → Green
- Unstaged-only (` X`) → Red
- Mixed staged+unstaged (`XX`) → Magenta
- Fallback → No color

The system gracefully degrades when colorama is unavailable through [dummy color objects](https://github.com/BHFock/git-cl/blob/6ad06dc168da7548dfd759b224830f797df644d5/git-cl#L70).


### Stash categorisation rules


### Stash Categorisation Rules

> **Why this matters:** Stashing the wrong files can cause Git errors or lose work. This categorisation prevents those problems by matching Git's own stash behavior.

The stash system needs to determine which files can safely be stashed. Git has many possible file states, but only some work with `git stash push`. Here's how git-cl categorizes files: `git cl stash` uses pre-validation to ensure only compatible files are included. This is handled by [clutil_categorize_files_for_stash](https://github.com/BHFock/git-cl/blob/cb5ca1923e1ee7acf4b942b5f259f3e5ce0db98c/git-cl#L1110C4-L1110C38) which determines if files are "stashable".

Files are grouped into categories based on what Git thinks of them:

|Git status                                                | Stashable?    |
|----------------------------------------------------------|---------------|
| Unstaged changes (modified/deleted in working directory) | stashable     |
| Staged additions (newly added to index)                  | stashable     |
| Untracked files (if explicitly in changelist)            | stashable     |
| Staged modifications (only staged changes, no unstaged)  | not stashable |
| Clean files (no changes)                                 | not stashable |

Files must have unstaged changes, be newly added to the index, or be untracked (but explicitly included in the changelist) to be stashable. This matches `git stash push` behaviour, which cannot stash files that only have staged modifications without unstaged changes.

### Unstash Conflict Detection

**The Problem:** When you unstash a changelist, some file states will cause Git conflicts or failures.

**The Solution:** Check file states before unstashing and provide specific guidance for resolving issues.

**How it works:** Similar to stash categorisation, unstash operations require conflict detection optimised for the 'stash→branch→unstash' workflow.

[clutil_check_unstash_conflicts_optimized](https://github.com/BHFock/git-cl/blob/19576c5a9eed0749aec9a344a0a70614caeb9b50/git-cl#L718) flags conflicts that would actually prevent [git stash pop](https://git-scm.com/docs/git-stash#Documentation/git-stash.txt-pop--index-q--quietstash) from succeeding. It uses a lookup table ([UNSTASH_STATUS_ANALYSIS](https://github.com/BHFock/git-cl/blob/c64e92b15bc8d85caf5390ca2fc327d4eb04e193/git-cl#L667)) to categorise Git status codes, with missing files treated as ideal for unstashing since they'll be restored without conflict.

The algorithm distinguishes real blocking conflicts (untracked files, working directory modifications) from safe states (staged changes, clean files). [clutil_suggest_workflow_actions()](https://github.com/BHFock/git-cl/blob/c64e92b15bc8d85caf5390ca2fc327d4eb04e193/git-cl#L767) provides actionable suggestions tailored to the git-cl workflow.

### Branching Workflow

The cl_branch command automates the common "stash→branch→unstash" workflow in a single operation. This allows users to move a changelist to its own dedicated branch without losing work or changelist organization.

#### Workflow Steps:

**Safety Checks:**

1. Precondition Validation - [clutil_validate_branch_preconditions](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2051) ensures the target changelist exists and is active (not stashed). [clutil_check_branch_exists](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2074) prevents conflicts with existing branch names.

2. Workspace Safety Check - [clutil_check_unassigned_changes](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2085) detects uncommitted changes not assigned to any changelist. The operation aborts if unassigned changes exist, preventing accidental data loss.

**Execution:**

3. Workspace Cleanup - [clutil_execute_stash_all](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2105) stashes all active changelists (including the target changelist), creating a clean working directory. Each changelist is stashed individually with metadata tracking.

4. Branch Creation - [clutil_create_branch](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2112) creates and checks out the new branch from the specified base (or current HEAD). The branch is created only after successful stashing.

5. Selective Restore - [clutil_unstash_changelist](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2123) restores only the target changelist to the new branch. Other changelists remain stashed and can be restored later with git cl unstash.

**Error Handling:**

6. Failure Recovery - [clutil_handle_branch_creation_failure](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2132) attempts to restore all stashed changelists if branch creation or unstashing fails, preventing partial state corruption.

#### Example Flow:

```
Before: Working on main branch with two changelists
├── feature-a (5 files)
└── bugfix (3 files) 
git cl branch feature-a my-feature-branch
After: Clean separation
├── main branch: feature-a and bugfix stashed, available for unstash
└── * my-feature-branch: feature-a unstashed, ready for development
```

This atomic operation eliminates the manual coordination required for branching workflows while preserving changelist metadata and ensuring workspace

### Platform Considerations

#### Path Handling Differences
`git-cl` normalises all paths to forward slashes (Git standard) via `.as_posix()` for consistent storage across platforms. The [pathlib.Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path) module abstracts away OS-specific path handling differences.

#### Terminal Colour Detection  
Colour output depends on [colorama](https://pypi.org/project/colorama/) for cross-platform compatibility. The implementation gracefully degrades to plain text when colour support is unavailable.

#### File Locking Differences
Uses Unix-specific [fcntl](https://docs.python.org/3/library/fcntl.html) module for metadata locking. Alternative implementations would be needed for Windows compatibility, though single-user interactive usage makes race conditions unlikely.

### Performance Considerations

#### Large Repository Handling
`git-cl` has been tested with repositories containing ~250k lines of code across ~1600 files without performance issues. The design avoids loading entire repository state into memory, instead relying on `git status --porcelain` for file state queries and processing changelists incrementally.

#### Memory Usage Patterns
Memory usage scales with the number of files in active changelists rather than total repository size. Metadata is stored in lightweight JSON files and loaded only when needed. The largest memory consumers are Git subprocess calls and status parsing, which are handled efficiently by the standard library.

#### Git Command Optimisation
Leverages Git's native commands (`git status`, `git stash`, etc.) rather than reimplementing Git functionality. File operations are batched where possible (e.g., `git add` with multiple files) to minimise subprocess overhead. Path conversion caching could be added for very large changelists if needed.



## Design Decisions FAQ

### Why store metadata in .git/ instead of tracked files?
- Keeps changelists separate from version control as a "pre staging area"
- Survives repository moves while staying private to local development

### Why use a single file instead of a Python package?
- Zero-dependency installation and easy deployment
- Self-contained for air-gapped systems

### Why JSON for metadata storage?
- Human readable with native Python support for [read](https://github.com/BHFock/git-cl/blob/4e75779b6c06365adaa148eb92ab7062fbdd68ba/git-cl#L219) and [write](https://github.com/BHFock/git-cl/blob/4e75779b6c06365adaa148eb92ab7062fbdd68ba/git-cl#L239) operations

  
### Why relative paths in cl.json?
- Repository portability (can move anywhere)
- Works regardless of mount points
- Consistent with Git's internal path handling

### Why fcntl locking instead of Git's index locking?
- Simpler implementation
- Independent of Git's internal mechanisms
- Sufficient for single-user interactive use case

### Why use argparse instead of a more modern CLI framework?
- Part of Python standard library with automatic help generation
- Sufficient for git-cl's simple command structure

## Future direction

The aim is to keep functionality focused while improving code quality. Priority areas include handling edge cases, platform compatibility improvements, general refactoring for maintainability, and adding tests. The single-file structure should be preserved for deployment simplicity.
