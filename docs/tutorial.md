# git-cl Tutorial

`git-cl` lets you group files into named changelists before staging or committing — like sticky notes for your working directory. This helps you manage multiple ongoing changes efficiently before staging or committing them.

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
- [3. Example Workflow: Changelists as Named Staging Areas](#3-example-workflow-changelists-as-named-staging-areas)
- [4. FAQ & Common Pitfalls](#4-faq--common-pitfalls)
- [5. Command Summary](#5-command-summary)

</details>


## What is `git-cl`?

`git-cl` is a Git subcommand inspired by Subversion’s changelists. It lets you group related file changes under a named label.

Use it when:

- Working on several features or fixes in parallel
- Wanting to break down a messy working directory into logical units
- Staging or committing changes by intent rather than file

Changelists are stored in a local metadata file (`.git/cl.json`) inside your repo. They're not versioned or shared.

## How changelists fit into Git workflows

Changelists help you manage changes before they’re staged or committed. They complement Git’s existing concepts rather than replacing them:

| Concept          | Description                                 | Role in Workflow                    |
|------------------|---------------------------------------------|-------------------------------------|
| **Changelist**   | A named group of modified files             | Organise uncommitted work           |
| **Staging Area** | Selects what goes into the next commit      | Prepare commit content              |
| **Branch**       | A line of development with commit history   | Isolate long-running or shared work |

Use changelists to track what you're working on, even when it's not ready to commit — especially useful when tasks overlap on the same branch.

## 1. Installation

1. Download or copy the `git-cl` script.

2. Make it executable:

   ```
   chmod +x git-cl
   ```
   
3. Move it into a directory in your system `PATH`:

   ```
   mkdir -p ~/bin
   mv git-cl ~/bin/
   ```
   
4. Add this to your shell config file (`.bashrc`, `.zshrc`, etc.) if needed:

   ```
   export PATH="$HOME/bin:$PATH"
   ```

5. (Optional) Confirm it's working:

   ```
   git cl -h
   ```

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
- Files remain unchanged in your working directory.

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


## 3. Example Workflow: Changelists as Named Staging Areas

`git-cl` changelists act like named pre-staging areas. Instead of staging files directly, you organise them into changelists — then selectively stage or commit based on those names.

Let’s say you're working on a feature that involves several types of changes. You can group your work like this:

```
git cl add ok src/core.py tests/test_core.py
git cl add test_only tests/setup_test_env.sh
git cl add do_not_commit notes/tmp.txt
```

This separates clean changes from experimental ones. You can check your progress with:

```
git cl status
```

Once you're satisfied with the files in `ok`, you stage and commit them:

```
git cl stage ok
git commit -m "Implement core feature"
```

The other changelists remain untouched, keeping your workspace organised and uncommitted changes visible.

[↑ Back to top](#git-cl-tutorial)

## 4. FAQ & Common Pitfalls

### How do I move a file from one changelist to another?

Just run `git cl add` with the new changelist name. You don't need to remove it from the old one manually.

```
git cl add new-list path/to/file
```

This automatically reassigns the file to new-list.

### Why are changelists deleted after I stage or commit?

This is the default behaviour — `git cl stage` and git `cl commit` clean up after themselves.

If you want to keep the changelist after the operation, use the `--keep` flag:

```
git cl stage my-list --keep
git cl commit my-list -m "WIP" --keep
```

### Why aren’t untracked files included when I stage or commit a changelist?

Because git cl only stages or commits files already tracked by Git.

If a file is untracked (`[??]`), it will show up in git cl st, but won’t be included when staging or committing.

To include it:

```
git add my-file.txt
git cl stage my-changelist
```

### Are changelists shared between team members?

No. Changelists are stored locally in `.git/cl.json` and are not version-controlled or shared via Git. They're like personal to-do lists for your working directory.

### Do changelists persist when switching branches?

Yes — changelists are local and independent of branches. This means:

- You can keep working on the same files across branches
- But beware: a changelist may reference files that don't exist in the new branch

If things get messy, delete a stale changelist:

```
git cl delete old-list
```

[↑ Back to top](#git-cl-tutorial)

## 5. Command Summary

| Task                           | Command                                        |
| ------------------------------ | ---------------------------------------------- |
| Add files to a changelist      | `git cl add <name> <files...>`                 |
| List changelists               | `git cl list` or `git cl ls`                   |
| View grouped status            | `git cl status` or `git cl st`                 |
| Stage a changelist             | `git cl stage <name> [--keep]`                 |
| Commit with inline message     | `git cl commit <name> -m "Message" [--keep]`   |
| Commit using message from file | `git cl commit <name> -F message.txt [--keep]` |
| Remove files from changelists  | `git cl remove <file1> <file2> ...`            |
| Delete a changelist            | `git cl delete <name>`                         |

[↑ Back to top](#git-cl-tutorial)
