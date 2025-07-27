# git-cl Tutorial


Welcome to the `git-cl` tutorial — a lightweight Git extension for organising your working directory changes into **named changelists**. This helps you manage multiple ongoing changes efficiently before staging or committing them.


<details>
<summary> Table of Contents</summary>

- [What is `git-cl`](#what-is-git-cl)
- [How changelists fit into Git workflows](#how-changelists-fit-into-git-workflows)
- [1. Installation](#1-installation)
- [2. Basic Commands](#2-basic-commands)
  - [2.1 Add files to a changelist](#21-add-files-to-a-changelist)
  - [2.2 List all changelists](#22-list-all-changelists)
  - [2.3 View status by changelist](#23-view-status-by-changelist)
  - [2.4 Stage a changelist](#24-stage-a-changelist)
  - [2.5 Commit a changelist](#25-commit-a-changelist)
  - [2.6 Remove files from changelists](#26-remove-files-from-changelists)
  - [2.7 Delete a changelist](#27-delete-a-changelist)
- [3. Tips, Notes & Troubleshooting](#3-tips-notes--troubleshooting)
- [4. Command Summary](#4-command-summary)

</details>


## What is `git-cl`?

`git-cl` is a Git subcommand inspired by Subversion’s changelists. It lets you group related file changes under a named label — ideal for managing uncommitted edits when juggling multiple tasks.

Use it when:

- Working on several features or fixes in parallel
- Wanting to break down a messy working directory into logical units
- Staging or committing changes by *intent* rather than *file*

Changelists are stored in a local metadata file (`.git/cl.json`) inside your repo. They're not versioned or shared — meaning they’re lightweight and personal, like sticky notes on your working copy.

## How changelists fit into Git workflows

Changelists help you manage changes **before** they’re staged or committed. They complement Git’s existing concepts rather than replacing them:

| Concept          | Description                                 | Role in Workflow                    |
|------------------|---------------------------------------------|-------------------------------------|
| **Changelist**   | A named group of modified files             | Organise uncommitted work           |
| **Staging Area** | Selects what goes into the next commit      | Prepare commit content              |
| **Branch**       | A line of development with commit history   | Isolate long-running or shared work |

Use changelists to track *what you're working on*, even when it's not ready to commit — especially useful when tasks overlap on the same branch.

## 1. Installation

1. Download or copy the `git-cl` script.

2. Make it executable:

   ```bash
   chmod +x git-cl

3. Move it into a directory in your system `PATH`:

   ```bash
   mkdir -p ~/bin
   mv git-cl ~/bin/

4. Add this to your shell config file (`.bashrc`, `.zshrc`, etc.) if needed:

   ```bash
   export PATH="$HOME/bin:$PATH"

5. (Optional) Confirm it's working:

   ```bash
   git cl -h

[↑ Back to top](#git-cl-tutorial)

## 2. Basic Commands

The following commands are the core of `git-cl`. Each helps you manage your changelists as you prepare your working directory for staging or commits.

### 2.1 Add files to a changelist

```
git cl add <changelist-name> <file1> <file2> ...
```

Groups files under a named changelist.

A file can only belong to one changelist at a time; it will be moved if already assigned elsewhere.

#### Example:

```
git cl add docs README.md docs/index.md
```

### 2.2 List all changelists

```
git cl list
# or
git cl ls
```

#### Example Output:

```
docs:
  README.md
  docs/index.md
tests:
  tests/dev_env.sh
```

### 2.3 View status by changelist

```
git cl status
# or
git cl st
```

- Like git status, but grouped by changelist.
- Shows modified ([M]), added ([A]), untracked ([??]) files.

#### Example Output:

```
docs:
  [M] README.md
  [M] docs/index.md

tests:
  [A] tests/dev_env.sh

No Changelist:
  [M] main.py
  [??] scratch.txt
```

### 2.4 Stage a changelist

```
git cl stage <changelist-name>
```

- Stages all tracked files from the changelist.
- Untracked files are skipped.
- Changelist is deleted after staging.

#### Example:

```
git cl stage docs
git commit -m "Refactor docs"
```

### 2.5 Commit a changelist

```
git cl commit <changelist-name> -m "Message"
git cl commit <changelist-name> -F commit.txt
```

- Commits tracked files and deletes the changelist.
- Use `-F <file>` to supply commit message from a file (like regular Git).

#### Example:

```
git cl commit tests -m "Add test environment"
```

### 2.6 Remove files from changelists

```
git cl remove <file1> <file2> ...
```

- Removes the given files from any changelist.
- Files remain in the working directory.

#### Example:

```
git cl remove notes/debug.txt
```

### 2.7 Delete a changelist

```
git cl delete <changelist-name>
```

- Removes the changelist grouping.
- Files remain in the working directory and will appear under “No Changelist” next time you run `git cl st`.

[↑ Back to top](#git-cl-tutorial)

## 3. Tips, Notes & Troubleshooting

### Moving a file between changelists

Each file can be part of only one changelist at a time. You don’t need to manually remove a file from one changelist before adding it to another. Just run:

```
git cl add new-list path/to/file
```

This automatically reassigns the file to the new changelist.

### Preserving changelists after staging/committing

By default, changelists are deleted after staging or committing. To keep them:

```
git cl stage docs --keep
git cl commit tests -m "Add tests" --keep
```

### Untracked files aren’t automatically staged or committed

Untracked files (those marked `[??]` in `git status`) will show up in `git cl st` if they’re part of a changelist — but they won't be staged or committed by `git cl stage` or `git cl commit`.

To include them:

1. Use `git add <file>` manually
2. Then stage or commit the changelist

### Changelists are local

All changelist metadata is stored in `.git/cl.json`. This is local to your repository and never shared via Git, keeping changelist structure flexible and personal.


### Changelists persist across branches

Changelists are just local lists of files stored in `.git/cl.json`. They persist when switching branches. This can be useful — but also confusing — if changelists refer to files that don’t exist in the new branch. In doubt, delete them with `git cl delete <name>`.

[↑ Back to top](#git-cl-tutorial)

## 4. Command Summary

| Task                           | Command                                        |
| ------------------------------ | ---------------------------------------------- |
| Add files to a changelist      | `git cl add <name> <files...>`                 |
| List changelists               | `git cl list` or `git cl ls`                   |
| View grouped status            | `git cl status` or `git cl st`                 |
| Stage a changelist             | `git cl stage <name>` [--keep]                 |
| Commit with inline message     | `git cl commit <name> -m "Message"` [--keep]   |
| Commit using message from file | `git cl commit <name> -F message.txt` [--keep] |
| Remove file from changelist    | `git cl remove <file>`                         |
| Delete a changelist            | `git cl delete <name>`                         |

[↑ Back to top](#git-cl-tutorial)
