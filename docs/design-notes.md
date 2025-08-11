# git-cl Design Notes

This documnets aims to describe the design of git-cl to make future maintance more easy.

## Core Architecture Components

### Purpose and Scope

- git-cl is a Git subcommand for managing named changelists within a Git working directory.
- It allows grouping files into logical changelists before staging or committing.

### Repository and Maintenance

- Hosted at: https://github.com/BHFock/git-cl

### Key Features

- Add/remove files to/from changelists.
- Stage or commit all files in a changelist.
- Show status grouped by changelists.
- Delete changelists when done.

## Technical Architecture

### File Structure

- Changelists are stored in .git/cl.json.
- Stash metadata is stored in .git/cl-stashes.json.
- Code stored in one single file to make installation easy.

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
  
