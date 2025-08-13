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

`git-cl` uses [fcntl](https://docs.python.org/3/library/fcntl.html) to lock metadata files during read/write operations to prevent race conditions caused by simultaneous use of git-cl by multiple processes. This is intended to prevent unexpected changes of changelists. However, it should be noticed that `git-cl` is designed for single user interactive use and not for shared accounts or integration into scripts.

#### Path Conversion

`git-cl` works with three path representations:

- **Repo-root relative** — used for storage in `.git/cl.json`
- **CWD relative** — used for Git CLI commands (`git add ../README.md`)
- **Absolute** — used internally for file existence checks and normalisation

Utility functions handle conversions between these forms, ensuring that paths are always correct regardless of the user’s current working directory. This is essential for features like showing `git cl status` from a subfolder while still storing metadata in `.git/cl.json` relative to the repository root.

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

### Stashing Workflow

- Files are categorised (e.g., unstaged changes, staged additions, untracked).
- Only stashable files are processed.
- Metadata is saved atomically to prevent corruption.

### Unstashing Workflow

- Validates environment and branch state.
- Detects and reports conflicts.
- Applies stash and updates metadata.

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

The path conversion system handles three representations:

1. **Input sanitization** via [clutil_sanitize_path()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L358) - Takes user-provided file paths, resolves relative components and symlinks, ensures paths are within the Git repository, and rejects dangerous characters that could cause security issues. Returns paths normalized to repo-root relative format or None if invalid.
2. **Storage normalization** to repo-root relative paths - All paths in .git/cl.json are stored relative to the repository root, enabling repository portability and providing a canonical representation regardless of where commands are run. This ensures changelists survive rep
3. **Display conversion** to CWD-relative for user commands via [clutil_format_file_status()](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L461) - Converts stored repo-relative paths to current-working-directory relative paths for display, making output compatible with standard Git commands. Shows paths as users expect to see them so they can copy-paste into git add commands.
  
##### Conflict detection logic

##### Stash categorization rules

### Platform Considerations
- Windows vs Unix path handling
- Terminal color detection
- File locking differences

### Performance Considerations
- Large repository handling
- Memory usage patterns
- Git command optimization

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
