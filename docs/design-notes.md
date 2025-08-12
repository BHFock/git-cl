# git-cl Design Notes - DRAFT

This document aims to describe the design of git-cl to make future maintenance more easy. Note that links to code examples are pinned to certain version of the code and that the code may have evolved since creating the links.

## Core Architecture Components

### Purpose and Scope

`git-cl` is a Git subcommand for managing named changelists within a Git working directory. It allows grouping files into logical changelists before staging or committing. The main design goal is that this helps to review code changes with `git cl status`, but the functionality also support stashing and branching based on changelists.
  
Repository hosted at: https://github.com/BHFock/git-cl

### Key Features

- Add/remove files to/from changelists.
- Stage or commit all files in a changelist.
- Show status grouped by changelists.
- Delete changelists when done.

## Technical Architecture

### File Structure

#### Metadata Structure

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

Storing `cl.json` in `.git/` allows to move the repository around locally while keeping the changelists intact. This is helped by the fact that file paths are stored relative to the repository root in `cl.json`. While the paths shown in `cl.json` are relative to the git root directory, the paths shown by the `git cl st` output are relative to the current working directory which is expected for executing normal Git commands like `git add ../README.md`. `git cl` converts paths depending on the context in paths relative to the git root, relative to the current working directory and in absolute paths. All three representations are needed.

`.git/cl.json`is not part of the git history. That keeps changelists conceptually as a 'pre staging functionality' which is not mixed up with git's version control.
  
Stash metadata is stored in `.git/cl-stashes.json`. This keeps the stashes separate from the changelist files and allowed an implementation of the more advanced `git cl stash` and `git cl unstash` without impacting the implementation of the basic functions. 

#### Code Structure

Code stored in one single file to make installation easy. The disadvantage of more difficult code navigation is mitigated by separation into blocks of different functionality with clear header comments:

##### [# INTERNAL UTILITIES](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L90)

Helper functions needed to keep the [CLI functions](https://github.com/BHFock/git-cl/blob/main/docs/design-notes.md#-cli-commands) at reasonable length use the name convention `clutil_function_name` and are stored together at the begin of the script in the `INTERNAL UTILITIES` section.

##### [# BRANCH WORKFLOW UTILITIES](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2048)

Utility functions only used by the [cl_branch](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2809) function are grouped in this section.  

##### [# CLI COMMANDS](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2146)

This section includes the definition of the main functions callable in git-cl. The functions provides interactions with the changelist metadata and the git repository.

| Changelist Command Function                                             | Tutorial                                                  | Type of Command                  |
|-------------------------------------------------------------------------|-----------------------------------------------------------|----------------------------------|
| [cl_add](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2150)      | [cl add](tutorial.md#21-add-files-to-a-changelist)        | Changelist Organistaion Commands |
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

This section includes the [main function](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2916) which serves as entry point. It uses [argparse](https://docs.python.org/3/library/argparse.html) to define the user interface for the subcommands like [add](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L2950), [status](https://github.com/BHFock/git-cl/blob/0.3.4/git-cl#L2992), [commit](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L3093), [branch](https://github.com/BHFock/git-cl/blob/29f16c54698048a6dbaf42d2e878654cc91a6ba6/git-cl#L3162), etc. This section includes the definition of the command line help. Define the help via `argparse` means that the main help command id availble via `git cl help` but not via  `git help cl`. Defining the help via `git help cl` would need creation of man pages to be installed with git. This has been left out for simplicity. 

### Concurrency and Locking

- Uses fcntl to lock files during read/write operations to prevent race conditions but tool intended for single user interactive mode.

### Colour Output

- Optional coloured CLI output via colorama, with fallbacks if unavailable.

### Command Parsing

- Uses argparse to define subcommands like add, remove, stage, commit, stash, unstash, branch, etc.

### Workflow Support

Supports a branch workflow:
- Stash all changelists.
- Create a new branch.
- Unstash a specific changelist.

### Validation and Safety

- Validates changelist names against reserved Git terms.
- Sanitises file paths and checks for dangerous characters.
- Handles edge cases like missing files, untracked files, and merge conflicts.

## Data Flow and Operations

### Changelist Lifecycle

- Creation → Modification → Staging → Committing → Deletion.

### Stashing Workflow

- Files are categorised (e.g., unstaged changes, staged additions, untracked).
- Only stashable files are processed.
- Metadata is saved atomically to prevent corruption.

### Unstashing Workflow

- Validates environment and branch state.
- Detects and reports conflicts.
- Applies stash and updates metadata.

## Extensibility and Modularity

- Modular design with utility functions (clutil_*) for:
  - File locking
  - Git status parsing
  - Path sanitisation
  - Conflict detection
  - Metadata handling
- CLI commands are mapped to functions for easy extension.

## Future direction

- Avoid expansion of functionality to keep code size under control and to keep the help/documentation readable
