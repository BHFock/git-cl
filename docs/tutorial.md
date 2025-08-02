<!--
git-cl: A Git subcommand to manage changelists in Git. Group files by intent, manage partial commits cleanly, and improve your Git workflow.
-->


# git-cl: A Git Subcommand for Changelist Management

[git-cl](https://github.com/BHFock/git-cl?tab=readme-ov-file) is a command-line tool that brings changelists to Git — like sticky notes for your working directory. It lets you group files into named changelists before staging or committing, helping you manage multiple parallel changes and make partial commits with intent and clarity.

<details>
<summary> Table of Contents</summary>

- [What is git-cl](#what-is-git-cl)
- [How changelists fit into Git workflows](#how-changelists-fit-into-git-workflows)
- [1. Installation](#1-installation)
- [2. Basic Commands](#2-basic-commands)
  - [2.1 Add files to a changelist](#21-add-files-to-a-changelist)
  - [2.2 View status by changelist](#22-view-status-by-changelist) 
    - [Filtering by changelist name](#filtering-by-changelist-name)
    - [Showing all Git status codes](#showing-all-git-status-codes)
    - [Git Status codes](#git-status-codes)
    - [Color Key](#color-key)
  - [2.3 Diff a changelist](#23-diff-a-changelist) 
  - [2.4 Stage a changelist](#24-stage-a-changelist)
  - [2.5 Commit a changelist](#25-commit-a-changelist)
  - [2.6 Remove files from changelists](#26-remove-files-from-changelists)
  - [2.7 Delete changelists](#27-delete-changelists)
- [3. Example Workflow: Changelists as Named Staging Areas](#3-example-workflow-changelists-as-named-staging-areas)
- [4. FAQ & Common Pitfalls](#4-faq--common-pitfalls)
- [5. Command Summary](#5-command-summary)

</details>


## What is git-cl?

`git-cl` is a Git subcommand that lets you group related file changes under a named changelist — similar to changelists in Subversion, but tailored for Git workflows.

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

To install `git-cl`, download the script and place it in your `$PATH`.

### Quick Install

```
mkdir -p ~/bin
curl -sLo ~/bin/git-cl https://raw.githubusercontent.com/BHFock/git-cl/main/git-cl
chmod +x ~/bin/git-cl
```

### Manual Install

Download or clone the repository:

```
git clone https://github.com/BHFock/git-cl.git
cd git-cl
```

Make it executable:

```
chmod +x git-cl
```

Move it into a directory in your system PATH:

```
mkdir -p ~/bin
mv git-cl ~/bin
```

### Verify Installation

Make sure `~/bin` is listed in your `$PATH`. Add this to your shell config file (`.bashrc`, `.zshrc`, etc.) if needed:

```
export PATH="$HOME/bin:$PATH"
```

Then confirm it's working:

```
git cl --version
git cl help
```

Git will recognise `git-cl` as the handler for `git cl`, just like its built-in commands.

[↑ Back to top](#git-cl-tutorial)

## 2. Basic Commands

The following commands are the core of `git-cl`. Each helps you manage your changelists as you prepare your working directory for staging or commits.

### 2.1 Add files to a changelist

```
git cl add <changelist-name> <file1> <file2> ...
```

- Groups files under a named changelist.
- A file can only belong to one changelist at a time; it will be moved if already assigned elsewhere.

#### Example

```
git cl add docs README.md docs/index.md
```

### 2.2 View status by changelist

```
git cl status
# or
git cl st
```

- Like `git status --porcelain`, but grouped by changelist.
- Shows Git’s precise two-letter status codes, grouped under each changelist.
- Files not assigned to any changelist appear under No Changelist.

##### Filtering by changelist name

You can pass one or more changelist names to show only those specific groups:

```
git cl status docs tests
```

This limits the output to the specified changelists. By default, unassigned files (those in “No Changelist”) are hidden in this mode.

If you want to include unassigned files alongside named changelists, use the `--include-no-cl` flag:

```
git cl st docs --include-no-cl
```

#### Showing all Git status codes

By default, git cl status shows only the most common status codes (like [M ], [??], [ D], etc.) for clarity.

To include all Git status codes — including merge conflicts and type changes — use the `--all` flag:

```
git cl st --all
```

This reveals additional cases like

| Code  | Description             |
| ----- | ----------------------- |
| \[UU] | Unmerged (conflict)     |
| \[T ] | Type change             |

#### Git Status Codes

| Code   | Status                 | Description                                         |
|--------|------------------------|-----------------------------------------------------|
| `[??]` | Untracked              | New file, not yet tracked by Git                   |
| `[M ]` | Staged                 | Change staged and ready to commit                  |
| `[ M]` | Unstaged               | Change made but not yet staged                     |
| `[MM]` | Mixed                  | Staged change with additional unstaged modification|
| `[A ]` | Added                  | New file added and staged                          |
| `[AM]` | Added + Modified       | File added and then further modified               |
| `[D ]` | Deletion (staged)      | File deletion staged                               |
| `[ D]` | Deletion (unstaged)    | File deleted but not yet staged                    |
| `[R ]` | Renamed                | File renamed and staged                            |
| `[RM]` | Renamed + Modified     | Renamed and then modified before staging           |

See the full list of codes in the [Git documentation](https://git-scm.com/docs/git-status). 

#### Example

```
$ git cl st docs --include-no-cl --all

docs:
  [ M] docs/index.md
  [A ] docs/new_section.md

No Changelist:
  [??] scratch.txt
  [UU] merge_conflict_file.py
```

#### Color Key

By default, `git cl status` uses colors to highlight file states:

| Color   | Meaning                       |
|---------|-------------------------------|
| Green   | Staged changes (`[M ]`, `[A ]`)|
| Red     | Unstaged changes (`[ M]`, `[ D]`)|
| Magenta | Both staged and unstaged (`[MM]`, `[AM]`)|
| Blue    | Untracked (`[??]`)            |

You can disable color with the `--no-color` flag or `NO_COLOR=1` environment variable.

### 2.3 Diff a changelist

```
git cl diff <changelist-name>
git cl diff <changelist1> <changelist2>
git cl diff <changelist-name> --staged
```

- Shows a unified diff (`git diff`) of the files in the changelist.
- When you specify multiple changelists, shows a combined diff of all files from those changelists.
- Uses `git diff --cached` when `--staged` is provided.

#### Example

```bash
git cl diff docs          # Show diff for 'docs' changelist only
git cl diff docs tests    # Show combined diff for both 'docs' and 'tests'
git cl diff docs --staged # Show staged changes for 'docs' changelist
```

### 2.4 Stage a changelist

```
git cl stage <changelist-name>
```

- Stages all tracked files from the changelist.
- Only files already tracked by Git will be staged. Untracked files are ignored unless you add them with `git add` first.
- Changelist is deleted after staging.
  
#### Example

```
git cl stage docs
git commit -m "Refactor docs"
```

Tip: Run `git cl diff` first if you want to review the changes before staging.

### 2.5 Commit a changelist

```
git cl commit <changelist-name> -m "Message"
git cl commit <changelist-name> -F commit.txt
```

- Automatically stages and commits all tracked files in the changelist — no need to `run git cl stage` or `git add` first.
- Untracked files ([??]) are ignored unless you add them first with `git add`.
- The changelist is deleted after commit, unless you use `--keep`.

This allows you to commit grouped changes directly, without touching the Git staging area manually.

#### Example

```
git cl commit tests -m "Add test environment"
# or
git cl commit tests -F message.txt
```

If you want to reuse the changelist (e.g. for further edits), use:


```
git cl commit tests -m "Partial commit" --keep
```

### 2.6 Remove files from changelists

```
git cl remove <file1> <file2> ...
```

- Removes the given files from any changelist.
- Files remain unchanged in your working directory.

### 2.7 Delete changelists

```
git cl delete <changelist1> <changelist2> ...
```

- Deletes one or more named changelists.
- Files remain in the working directory and will appear under “No Changelist” next time you run `git cl st`.

You can also delete all changelists at once with:

```
git cl delete --all
```

- This clears all changelists from your workspace, leaving files untouched.

Only changelist metadata is deleted — no file content or Git history is lost.


[↑ Back to top](#git-cl-tutorial)


## 3. Example Workflow: Changelists as Named Staging Areas

`git-cl` changelists function as named pre-staging areas. Instead of staging files directly, you organise them into changelists — then selectively stage or commit based on those names.

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

Because `git cl` only stages or commits files already tracked by Git.

If a file is untracked (`[??]`), it will show up in `git cl st`, but won’t be included when staging or committing.

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

### Why don’t I see all files in git cl status?

By default, `git cl status` filters out files with uncommon Git status codes (e.g. merge conflicts or type changes) to keep the output clean.

If you want to include everything, use the `--all` flag:

```
git cl status --all
```

This will show all files, including those with status codes like `[UU]` (unmerged) or `[T ]` (type change).

[↑ Back to top](#git-cl-tutorial)

## 5. Command Summary

| Task                                     | Command                              | Alias        | 
| ---------------------------------------- | ------------------------------------ | ------------ |
| Add files to a changelist      | `git cl add <name> <files...>`                 | `git cl a`   |
| View grouped status            | `git cl status` / `git cl st`                  | `git cl st`  | 
| View all statuses, no color    | `git cl status --all --no-color`               |              |
| Show diff for changelist(s)    | `git cl diff <name1> [<name2> ...] [--staged]` |              |
| Stage a changelist             | `git cl stage <name> [--keep]`                 |              |
| Commit with inline message     | `git cl commit <name> -m "Message" [--keep]`   | `git cl ci`  |
| Commit using message from file | `git cl commit <name> -F message.txt [--keep]` |              |
| Remove files from changelists  | `git cl remove <file1> <file2> ...`            | `git cl rm`  |
| Delete changelists             | `git cl delete <name1> <name2> ...`            | `git cl del` | 
| Delete all changelists         | `git cl delete --all`                          |              |
| Show help                      | `git cl help`                                  |              |

[↑ Back to top](#git-cl-tutorial)
