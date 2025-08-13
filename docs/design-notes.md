# git-cl Design Notes - DRAFT

[git-cl](https://github.com/BHFock/git-cl) is a Git subcommand for managing named changelists within a Git working directory. It allows grouping files into logical changelists before staging or committing. The main design goal is to help review code changes with [git cl status](tutorial.md#22-view-status-by-changelist), but the functionality also supports [stashing](tutorial.md#31-stash-and-unstash-changelists) and [branching](tutorial.md#32-create-a-branch-from-a-changelist) based on changelists.

This document describes the design of `git-cl` to help future maintenance. Note that links to code examples are pinned to certain versions of the code and may have evolved since creating the links.

## Table of Contents
- [Overview](#overview)
- [Technical Architecture](#technical-architecture)
- [Implementation Details](#implementation-details)
- [Design Decisions FAQ](#design-decisions-faq)
- [Future Direction](#future-direction)


## Technical Architecture

### Code and Data Organisation

#### File Structure 

Changelists are stored in `.git/cl.json`. The human readable [JSON](https://en.wikipedia.org/wiki/JSON) format allows easy review on how changelist are stored. For example this `git cl st` (executed from the folder `~git-cl_test/folder1`): 

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

`.git/cl.json`is not part of the Git history. This keeps changelists as a "pre-staging" layer separate from Git's version control.
  
Stash metadata is stored in `.git/cl-stashes.json`. This keeps the stashes separate from the changelist files and allowed an implementation of the more advanced `git cl stash` and `git cl unstash` without impacting the implementation of the basic functions. 

#### Code Structure

Code is organized in a single file for simple installation. Code navigation is facilitated by clear section headers that group related functionality

##### [# INTERNAL UTILITIES](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L90)

Utility functions needed to keep the [CLI functions](https://github.com/BHFock/git-cl/blob/main/docs/design-notes.md#-cli-commands) at reasonable length use the name convention `clutil_function_name` and are stored together at the begin of the script in the `INTERNAL UTILITIES` section.

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

This section includes the [main function](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2916) which serves as entry point. It uses [argparse](https://docs.python.org/3/library/argparse.html) to define the user interface for the subcommands like [add](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2950), [status](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2992), [commit](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L3093), [branch](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L3162), etc. This section includes the definition of the command line help. Define the help via `argparse` means that the main help command is available via `git cl help` but not via  `git help cl`. Defining the help via `git help cl` would need creation of man pages to be installed with git. This has been left out for simplicity. 

### Runtime Behaviour

#### Concurrency and Locking

`git-cl` uses [fcntl](https://docs.python.org/3/library/fcntl.html) to lock metadata files preventing race conditions. It is designed for single-user interactive use rather than shared accounts or scripts.

[`clutil_file_lock`](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L99) implements a [context manager](https://book.pythontips.com/en/latest/context_managers.html) that creates temporary `.lock` files (e.g., `cl.json.lock`) with exclusive locks. All metadata read/write operations are wrapped in these locks, with automatic cleanup on exit or exception.

#### Error Handling and Exit Codes

`git-cl` exits with code `0` on success and non-zero codes on errors. Error messages are printed to `stderr`. Some functions terminate execution immediately on fatal errors using [sys.exit()](https://docs.python.org/3/library/sys.html#sys.exit), ensuring no partial metadata changes are written.

## Implementation Details

### Git Status Parsing

`git-cl` transforms Git's repository state into structured, colorized output for changelist-based workflows. This is the foundation for all display and conflict detection operations.

The process follows a multi-stage pipeline:

1. **Status Collection** – [`clutil_get_git_status`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L335) executes `git status --porcelain` with optional `--untracked-files=all` for comprehensive file state detection.

2. **Parsing and Filtering** – [`clutil_get_file_status_map`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L387) processes each status line, extracting 2-character Git status codes and file paths. Known status codes from `INTERESTING_CODES` are separated from uncommon ones, with warnings for filtered files unless `--all` is specified.

3. **Path Normalization** – File paths are converted to repo-root relative format for consistent internal representation, handling renamed files by extracting the target path from `old -> new` syntax.

4. **Display Formatting** – [`clutil_format_file_status`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L461) converts repo-relative paths back to CWD-relative for user display, applying color coding via [`clutil_should_use_color`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L142).

5. **Color Classification** – Status codes are [mapped](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L464) to colors: untracked files (blue), staged-only changes (green), unstaged-only changes (red), mixed staged+unstaged (magenta), with graceful degradation when colorama is unavailable.

This pipeline ensures consistent Git state interpretation across all commands while providing user-friendly, colorized output that matches Git conventions.

### Path Resolution Algorithm

The path conversion system handles three representations: repo-root relative (storage), CWD relative (Git commands), and absolute (internal checks). 

[clutil_sanitize_path()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L358) validates user input, resolves relative components, and ensures paths are within the Git repository while rejecting dangerous characters. All paths in `.git/cl.json` are stored relative to the repository root for portability. [clutil_format_file_status()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L461) converts stored paths to CWD-relative paths for display, making output compatible with standard Git commands.

### Unstash Conflict Detection

Git's many possible repository states make it difficult to design reliable workflows. `git-cl` uses targeted conflict detection optimized for the "stash→branch→unstash" workflow rather than general-purpose checking.

[clutil_check_unstash_conflicts_optimized](https://github.com/BHFock/git-cl/blob/19576c5a9eed0749aec9a344a0a70614caeb9b50/git-cl#L718) only flags conflicts that would actually prevent [git stash pop](https://git-scm.com/docs/git-stash#Documentation/git-stash.txt-pop--index-q--quietstash) from succeeding. It uses a lookup table ([UNSTASH_STATUS_ANALYSIS](https://github.com/BHFock/git-cl/blob/c64e92b15bc8d85caf5390ca2fc327d4eb04e193/git-cl#L667)) to categorize Git status codes, with missing files treated as ideal for unstashing since they'll be restored without conflict.

The algorithm distinguishes real blocking conflicts (untracked files, working directory modifications) from safe states (staged changes, clean files). [clutil_suggest_workflow_actions()](https://github.com/BHFock/git-cl/blob/c64e92b15bc8d85caf5390ca2fc327d4eb04e193/git-cl#L767) provides actionable suggestions tailored to the git-cl workflow.

### Stash categorization rules

Similar to the repository state checking for unstashing, a pre-check is done for `git cl stash`. This is handled by [clutil_categorize_files_for_stash](https://github.com/BHFock/git-cl/blob/cb5ca1923e1ee7acf4b942b5f259f3e5ce0db98c/git-cl#L1110C4-L1110C38) which determines if files are "stashable".

The categorization logic groups files into distinct categories based on their Git status:
- **Unstaged changes** (modified/deleted in working directory) - stashable
- **Staged additions** (newly added to index) - stashable  
- **Untracked files** (if explicitly in changelist) - stashable
- **Staged modifications** (only staged changes, no unstaged) - not stashable
- **Clean files** (no changes) - not stashable

Files must have unstaged changes, be newly added to the index, or be untracked (but explicitly included in the changelist) to be stashable. This matches `git stash push` behavior, which cannot stash files that only have staged modifications without unstaged changes.


### Branching Workflow

- **Validate preconditions** using [`clutil_validate_branch_preconditions`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2051) and [`clutil_check_branch_exists`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2074) to ensure the changelist exists and no conflicting branch is present.  
- **Check for unassigned changes** via [`clutil_check_unassigned_changes`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2085) to avoid unintentionally losing work.  
- **Stash all changelists** with [`clutil_execute_stash_all`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2105) to preserve the current working state.  
- **Create and check out** the new branch using [`clutil_create_branch`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2112).  
- **Unstash the target changelist** onto the new branch via [`clutil_unstash_changelist`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2123).  
- **Handle failures** in branch creation or unstashing with [`clutil_handle_branch_creation_failure`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2132) to restore the original state.  


### Platform Considerations

#### Path Handling Differences
`git-cl` normalizes all paths to forward slashes (Git standard) via `.as_posix()` for consistent storage across platforms. The [pathlib.Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path) module abstracts away OS-specific path handling differences.

#### Terminal Color Detection  
Color output depends on [colorama](https://pypi.org/project/colorama/) for cross-platform compatibility. The implementation gracefully degrades to plain text when color support is unavailable.

#### File Locking Differences
Uses Unix-specific [fcntl](https://docs.python.org/3/library/fcntl.html) module for metadata locking. Alternative implementations would be needed for Windows compatibility, though single-user interactive usage makes race conditions unlikely.

### Performance Considerations

#### Large Repository Handling
`git-cl` has been tested with repositories containing ~250k lines of code across ~1600 files without performance issues. The design avoids loading entire repository state into memory, instead relying on `git status --porcelain` for file state queries and processing changelists incrementally.

#### Memory Usage Patterns
Memory usage scales with the number of files in active changelists rather than total repository size. Metadata is stored in lightweight JSON files and loaded only when needed. The largest memory consumers are Git subprocess calls and status parsing, which are handled efficiently by the standard library.

#### Git Command Optimization
Leverages Git's native commands (`git status`, `git stash`, etc.) rather than reimplementing Git functionality. File operations are batched where possible (e.g., `git add` with multiple files) to minimize subprocess overhead. Path conversion caching could be added for very large changelists if needed.



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
