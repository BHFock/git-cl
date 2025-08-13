# git-cl Design Notes - DRAFT

This document aims to describe the design of [git-cl](https://github.com/BHFock/git-cl) to make future maintenance more easy. Note that links to code examples are pinned to certain version of the code and that the code may have evolved since creating the links.

## Table of Contents
- [Overview](#overview)
- [Technical Architecture](#technical-architecture)
  - [Code and Data Organisation](#code-and-data-organisation)
  - [Runtime Behaviour](#runtime-behaviour)
  - [User Interface](#user-interface)
- [Common Implementation Patterns](#common-implementation-patterns)
- [Data Flow and Operations](#data-flow-and-operations)
- [Implementation Details](#implementation-details)
  - [Key Algorithms](#key-algorithms)
- [Troubleshooting and Edge Cases](#troubleshooting-and-edge-cases)
  - [Common Issues](#common-issues)
  - [Design Decisions FAQ](#design-decisions-faq)
- [Future Direction](#future-direction)

## Overview

### Purpose and Scope

`git-cl` is a Git subcommand for managing named changelists within a Git working directory. It allows grouping files into logical changelists before staging or committing. The main design goal is that this helps to review code changes with `git cl status`, but the functionality also support stashing and branching based on changelists.
  
Repository hosted at: https://github.com/BHFock/git-cl

### Key Features

- Add/remove files to/from changelists. 
- Show status grouped by changelists.
- Stage or commit all files in a changelist.
- Stash changelists and create branches from changelists.

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


Storing `cl.json` in `.git/` allows moving the repository locally while keeping changelists intact, because file paths in `cl.json` are stored relative to the repository root. `git cl st` displays paths relative to the current working directory. The details of how these paths are transformed for display or Git operations are described in the [Path Conversion](#path-conversion) section.

`.git/cl.json`is not part of the git history. That keeps changelists conceptually as a 'pre staging functionality' which is not mixed up with git's version control.
  
Stash metadata is stored in `.git/cl-stashes.json`. This keeps the stashes separate from the changelist files and allowed an implementation of the more advanced `git cl stash` and `git cl unstash` without impacting the implementation of the basic functions. 

#### Code Structure

Code stored in one single file to make installation easy. The disadvantage of more difficult code navigation is mitigated by separation into blocks of different functionality with clear header comments:

##### [# INTERNAL UTILITIES](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L90)

Helper functions needed to keep the [CLI functions](https://github.com/BHFock/git-cl/blob/main/docs/design-notes.md#-cli-commands) at reasonable length use the name convention `clutil_function_name` and are stored together at the begin of the script in the `INTERNAL UTILITIES` section.

##### [# BRANCH WORKFLOW UTILITIES](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2048)

Utility functions only used by the [cl_branch](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2809) function are grouped in this section. In parts these are quite small functions, intended to make `cl_branch` more readable with a complexity which is seen by [pylint](https://www.pylint.org/) as recommended. These functions include:

- [clutil_validate_branch_preconditions](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2051)
- [clutil_check_branch_exists](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2074)
- [clutil_check_unassigned_changes](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2085)
- [clutil_execute_stash_all](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2105C5-L2105C29)
- [clutil_create_branch](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2112C5-L2112C25)
- [clutil_unstash_changelist](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2123C5-L2123C30)
- [clutil_handle_branch_creation_failure](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2132C5-L2132C42)

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

#### Path Conversion

`git-cl` works with three path representations: repo-root relative (storage), CWD relative (Git commands), and absolute (internal checks). Utility functions handle conversions ensuring paths work from any directory

#### Error Handling and Exit Codes

`git-cl` exits with code `0` on success and non-zero codes on errors. Error messages are printed to `stderr`. Some functions terminate execution immediately on fatal errors using [sys.exit()](https://docs.python.org/3/library/sys.html#sys.exit), ensuring no partial metadata changes are written.

#### Colour Output

Output of `git cl st` is coloured by default. This uses [colorama](https://pypi.org/project/colorama/). The output is uncoloured if colorama is not available, if the output is redirected/piped or if coloured output is switched off via flag or environment variable. 

### User Interface 

#### Command Parsing

- Uses argparse to define subcommands like add, remove, stage, commit, stash, unstash, branch, etc.

#### Workflow Support

Supports a branch workflow:
- Stash all changelists.
- Create a new branch.
- Unstash a specific changelist.

#### Validation and Safety

- Validates changelist names against reserved Git terms.
- Sanitises file paths and checks for dangerous characters.
- Handles edge cases like missing files, untracked files, and merge conflicts.

## Common Implementation Patterns

### Utility Function Convention
- All utilities use `clutil_` prefix
- Path sanitization pattern
- Atomic metadata operations

### Error Handling Strategies
- Immediate exit on fatal errors
- Rollback on partial failures
- User-friendly error messages

### Git Integration Patterns
- Status parsing
- Path conversion workflows
- Safe git command execution

## Data Flow and Operations

### File Lifecycle Management
- File addition/removal patterns
- Path normalization workflow

### Metadata Operations
- JSON structure evolution
- Locking strategies
- Backup/recovery approaches

### Git Integration Points
- Status synchronization
- Conflict detection
- Branch state management

### Branching Workflow

- **Validate preconditions** using [`clutil_validate_branch_preconditions`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2051) and [`clutil_check_branch_exists`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2074) to ensure the changelist exists and no conflicting branch is present.  
- **Check for unassigned changes** via [`clutil_check_unassigned_changes`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2085) to avoid unintentionally losing work.  
- **Stash all changelists** with [`clutil_execute_stash_all`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2105) to preserve the current working state.  
- **Create and check out** the new branch using [`clutil_create_branch`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2112).  
- **Unstash the target changelist** onto the new branch via [`clutil_unstash_changelist`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2123).  
- **Handle failures** in branch creation or unstashing with [`clutil_handle_branch_creation_failure`](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2132) to restore the original state.  

## Implementation Details

### Key Algorithms

#### Path Resolution Algorithm

The path conversion system handles three representations: repo-root relative (storage), CWD relative (Git commands), and absolute (internal checks). 

[clutil_sanitize_path()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L358) validates user input, resolves relative components, and ensures paths are within the Git repository while rejecting dangerous characters. All paths in `.git/cl.json` are stored relative to the repository root for portability. [clutil_format_file_status()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L461) converts stored paths to CWD-relative paths for display, making output compatible with standard Git commands.

#### Unstash Conflict Detection

Git's many possible repository states make it difficult to design reliable workflows. `git-cl` uses targeted conflict detection optimized for the "stash→branch→unstash" workflow rather than general-purpose checking.

[clutil_check_unstash_conflicts_optimized](https://github.com/BHFock/git-cl/blob/19576c5a9eed0749aec9a344a0a70614caeb9b50/git-cl#L718) only flags conflicts that would actually prevent [git stash pop](https://git-scm.com/docs/git-stash#Documentation/git-stash.txt-pop--index-q--quietstash) from succeeding. It uses a lookup table ([UNSTASH_STATUS_ANALYSIS](https://github.com/BHFock/git-cl/blob/c64e92b15bc8d85caf5390ca2fc327d4eb04e193/git-cl#L667)) to categorize Git status codes, with missing files treated as ideal for unstashing since they'll be restored without conflict.

The algorithm distinguishes real blocking conflicts (untracked files, working directory modifications) from safe states (staged changes, clean files). [clutil_suggest_workflow_actions()](https://github.com/BHFock/git-cl/blob/c64e92b15bc8d85caf5390ca2fc327d4eb04e193/git-cl#L767) provides actionable suggestions tailored to the git-cl workflow.

##### Stash categorization rules

Similar to the repository state checking for unstashing, a pre-check is done for `git cl stash`. This is handled by [clutil_categorize_files_for_stash](https://github.com/BHFock/git-cl/blob/cb5ca1923e1ee7acf4b942b5f259f3e5ce0db98c/git-cl#L1110C4-L1110C38) which determines if files are "stashable".

The categorization logic groups files into distinct categories based on their Git status:
- **Unstaged changes** (modified/deleted in working directory) - stashable
- **Staged additions** (newly added to index) - stashable  
- **Untracked files** (if explicitly in changelist) - stashable
- **Staged modifications** (only staged changes, no unstaged) - not stashable
- **Clean files** (no changes) - not stashable

Files must have unstaged changes, be newly added to the index, or be untracked (but explicitly included in the changelist) to be stashable. This matches `git stash push` behavior, which cannot stash files that only have staged modifications without unstaged changes.


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


## Troubleshooting and Edge Cases

### Common Issues
- Path-related problems
- Merge conflict scenarios
- Metadata corruption recovery

### Design Decisions FAQ

#### Why store metadata in .git/ instead of tracked files?
- Keeps changelists separate from version control (concept of a "pre staging area")
- Survives repository moves but stays private in push operations
- No merge conflicts in changelist metadata

#### Why use a single file instead of a Python package?
- Zero-dependency installation (just copy the file)
- No package management complexity
- Easy deployment to different environments
- Self-contained for air-gapped systems

#### Why JSON for metadata storage?
- Human readable for debugging
- Easy to parse/modify if needed
- Widely understood format
- Python support for read and write operations
  
#### Why relative paths in cl.json?
- Repository portability (can move anywhere)
- Works regardless of mount points
- Consistent with Git's internal path handling

#### Why fcntl locking instead of Git's index locking?
- Simpler implementation
- Independent of Git's internal mechanisms
- Sufficient for single-user interactive use case

#### Why use argparse instead of a more modern CLI framework?
- Part of Python standard library (no external dependencies)
- Sufficient for git-cl's command structure
- Familiar to most Python developers
- Automatic help generation matches git-cl's simplicity goals

## Future direction

The aim is to avoid expansion of functionality to keep the code size under control and the help/documentation readable. The code may need some extensions to cover more edge cases, platform compatibility, etc. General refactoring may help with maintainability and addition of tests would be beneficial. It would be desirable to keep the single file structure of the script to simplify deployment.
