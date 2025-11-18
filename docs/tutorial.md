<!--
git-cl: A Git subcommand to manage changelists in Git. Group files by intent, manage partial commits cleanly, and improve your Git workflow.
-->


# git-cl: A Git Subcommand for Changelist Management

[git-cl](https://github.com/BHFock/git-cl) is a command-line tool that brings changelists to Git — like sticky notes for your working directory. It lets you group files into named changelists before [staging](https://git-scm.com/about/staging-area) or [committing](https://git-scm.com/docs/git-commit), helping you manage multiple parallel changes and make partial commits with intent and clarity.

<details>
<summary> Table of Contents</summary>

- [Why git-cl](#why-git-cl)
- [How changelists fit into Git workflows](#how-changelists-fit-into-git-workflows)
- [1. Installation](#1-installation)
- [2. Basic Commands](#2-basic-commands)
  - [2.1 Add files to a changelist](#21-add-files-to-a-changelist)
  - [2.2 View status by changelist](#22-view-status-by-changelist) 
  - [2.3 Diff a changelist](#23-diff-a-changelist) 
  - [2.4 Stage and unstage a changelist](#24-stage-and-unstage-a-changelist)
  - [2.5 Commit a changelist](#25-commit-a-changelist)
  - [2.6 Remove files from changelists](#26-remove-files-from-changelists)
  - [2.7 Delete changelists](#27-delete-changelists)
  - [2.8 Checkout a changelist](#28-checkout-a-changelist)
  - [2.9 Getting help from the command line](#29-getting-help-from-the-command-line)
- [3. Advanced Commands](#3-advanced-commands)
  - [3.1 Stash and Unstash changelists](#31-stash-and-unstash-changelists)
  - [3.2 Create a branch from a changelist](#32-create-a-branch-from-a-changelist)
- [4. Example Workflows](#4-example-workflows)
  - [4.1 Changelists as named staging areas](#41-changelists-as-named-staging-areas)
  - [4.2 Branching Mid-Feature with git cl branch](#42-branching-mid-feature-with-git-cl-branch)
- [5. FAQ & Common Pitfalls](#5-faq--common-pitfalls)
- [6. Command Summary](#6-command-summary)
  - [6.1 Command Summary Table](#61-command-summary-table)
  - [6.2 Git Status Code Reference](#62-git-status-code-reference)

</details>


## Why git-cl?

`git-cl` is a Git subcommand that lets you group related file changes under a named changelist — similar to changelists in [Subversion](https://subversion.apache.org/), but tailored for [Git](https://git-scm.com) workflows.

```
Traditional Git Workflow              With git-cl
========================              ===========

 Working Directory                    Working Directory
        ↓                                    ↓
(all mixed together)                 (organised by intent)
        ↓                                    ↓
 git add file1.py                     Changelist: "bugfix"
 git add file2.py                     Changelist: "refactor"  
 git add file3.py                     Changelist: "docs"
        ↓                                    ↓
 Staging Area                         git cl commit bugfix
(still mixed up)                     (clean, focused commit)
```

This helps when:

- Working on several features or fixes in parallel
- Wanting to break down a messy working directory into logical units
- Staging or committing changes by intent rather than file

Changelists are saved locally in `.git/cl.json`. They’re private to your workspace and not shared or committed. Think of them as quick labels on piles of work.

Read more: [Why git-cl exists: A personal history](why-git-cl.md) of changelists from SVN to Git.


## How changelists fit into Git workflows

Changelists act as a layer above Git's [staging area](https://git-scm.com/about/staging-area) — helping you group related edits before deciding what to stage or commit:

```
Working Directory
=================
modified: clean_data.py ───┐
modified: filters.py ──────┼─> Changelist: "preprocessing"
modified: utils/math.py ───┘

modified: plot.py ─────────┐
modified: charts.py ───────┼─> Changelist: "visualisation"  
modified: style.mplstyle ──┘

modified: test_filters.py  ──> Changelist: "tests"

new file: debug_output.csv ──> (No Changelist)

     ↓ git cl stage preprocessing
     
Staging Area                     
============
clean_data.py
filters.py      ─────────────> git commit -m "Apply Gaussian filters to input data"
math.py
```

They work alongside Git's core concepts, not in place of them:


| Concept          | Description                                                                                 | Role in Workflow                    |
|------------------|---------------------------------------------------------------------------------------------|-------------------------------------|
| **Changelist**   | A named group of modified files                                                             | Organise uncommitted work           |
| **Staging Area** | Selects what goes into the next commit ([Git docs](https://git-scm.com/docs/git-add))       | Prepare commit content              |
| **Branch**       | A line of development with commit history ([Git docs](https://git-scm.com/docs/git-branch)) | Isolate long-running or shared work |

Use changelists as your own labelled workspace, keep unrelated edits separate, or manage overlapping work — all without affecting Git history.

## 1. Installation

### Method 1: Download the script

For the latest stable version, download directly from the [git-cl repository](https://github.com/BHFock/git-cl):

```
mkdir -p ~/bin
wget https://raw.githubusercontent.com/BHFock/git-cl/main/git-cl -O ~/bin/git-cl
chmod +x ~/bin/git-cl
```

Make sure `~/bin` is in your `$PATH`. You can add this line to your shell config file if needed:

```
export PATH="$HOME/bin:$PATH"
```

### Method 2: Clone the repository

Clone the complete [git-cl project](https://github.com/BHFock/git-cl) including documentation:

```
git clone https://github.com/BHFock/git-cl.git ~/opt/git-cl
chmod +x ~/opt/git-cl/git-cl
```

Add the cloned directory to your `$PATH`:

```
export PATH="$HOME/opt/git-cl:$PATH"
```

You can add this line to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) to make it permanent.


### Verify Installation

Then confirm it's working:

```
git cl --version
git cl help
```

Git will recognise `git-cl` as a [subcommand]( https://git.github.io/htmldocs/howto/new-command.html): you can now run `git cl` just like `git commit` or `git status`.


[↑ Back to top](#git-cl-a-git-subcommand-for-changelist-management)

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

- Like [git status --porcelain](https://git-scm.com/docs/git-status), but grouped by changelist.
- Shows Git’s precise two-letter status codes, grouped under each changelist.
- Files not assigned to any changelist appear under 'No Changelist'.

##### Filtering by changelist name

You can pass one or more changelist names to show only those specific groups:

```
git cl st docs tests
```

This limits the output to the specified changelists. By default, unassigned files (those in 'No Changelist') are hidden in this mode.

If you want to include unassigned files alongside named changelists, use the `--include-no-cl` flag:

```
git cl st docs --include-no-cl
```

#### Showing all Git status codes

By default, `git cl status` shows only the most [common status codes](#common-status-codes) (like [M ], [??], [ D], etc.) for clarity.

To include all Git status codes — including merge conflicts and type changes — use the `--all` flag:

```
git cl st --all
```

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

### 2.3 Diff a changelist

```
git cl diff <changelist-name>
git cl diff <changelist1> <changelist2>
git cl diff <changelist-name> --staged
```

- Shows a unified diff ([git diff](https://git-scm.com/docs/git-diff)) of the files in the changelist.
- When you specify multiple changelists, shows a combined diff of all files from those changelists.
- Uses `git diff --cached` when `--staged` is provided.

#### Example

```bash
git cl diff docs          # Show diff for 'docs' changelist only
git cl diff docs tests    # Show combined diff for both 'docs' and 'tests'
git cl diff docs --staged # Show staged changes for 'docs' changelist
```

### 2.4 Stage and Unstage a Changelist

#### Stage a changelist

```
git cl stage <changelist-name>
```

- Stages all tracked files in the changelist.
- Untracked files ([??]) are ignored unless added with git add.
- The changelist is deleted after staging, unless `--keep` is used.
  
#### Example

```
git cl stage docs
git commit -m "Refactor docs"
```

Tip: Run [git cl diff](#23-diff-a-changelist) first if you want to review changes.

#### Unstage a changelist

```
git cl unstage <changelist-name>
```

- Unstages files from the changelist (i.e. removes them from the index).
- Only applies to staged files — unchanged or unstaged files are ignored.
- Files remain in the changelist and your working directory.

#### Example

```
git cl unstage docs
```

This is useful when you've staged something too early and want to pull it back without losing the changelist group.

### 2.5 Commit a changelist

```
git cl commit <changelist-name> -m "Message"
git cl commit <changelist-name> -F commit.txt
```

- Automatically stages and commits all tracked files in the changelist — no need to run [git add](https://git-scm.com/docs/git-add) or [git cl stage](#stage-a-changelist) first.
- Untracked files ([see status codes](#common-status-codes)) are ignored unless you add them first with `git add`.
- The changelist is deleted after commit, unless you use `--keep`.

Important: This command automatically stages tracked files before committing them, so you don't need to run `git add` or [git cl stage](24-stage-and-unstage-a-changelist) first. However, untracked files ([??]) in the changelists are safely ignored and will remain untracked.

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
- Files remain in the working directory and will appear under “No Changelist” next time you run [git cl st](#22-view-status-by-changelist).

You can also delete all changelists at once with:

```
git cl delete --all
```

- This clears all changelists from your workspace, leaving files untouched.

Only changelist metadata is deleted — no file content or Git history is lost.

### 2.8 Checkout a Changelist

```
git cl checkout <changelist-name>
# or
git cl co <changelist-name>
```

- Reverts all files in the changelist to their last committed state ([HEAD](https://git-scm.com/book/ms/v2/Git-Tools-Reset-Demystified.html#_the_head)).
- Useful for discarding local changes by intent, not just by filename.
- Prompts for confirmation before proceeding.
- Shows a summary of reverted files.

### 2.9 Getting Help from the Command Line

You can explore all available commands directly from your terminal:

```
git cl help
```

To see help for a specific command — including its available options — add -h after the command name:

```
git cl commit -h
git cl branch -h
```

Note: `git help cl` does not work — because `git-cl` is an external subcommand and not part of Git's built-in help system. Always use `git cl help` instead.

[↑ Back to top](#git-cl-a-git-subcommand-for-changelist-management)


## 3. Advanced Commands

These commands build on the [Basic Commands](#2-basic-commands) - make sure you're familiar with [adding files](#21-add-files-to-a-changelist) and [viewing status](#22-view-status-by-changelist) first.

### 3.1 Stash and Unstash Changelists

Sometimes you’re in the middle of a changelist but need to switch branches or pause your work — without committing it.

Stash saves those changes aside, and unstash brings them back later.

#### Stash a changelist

```
git cl stash <changelist-name>
```

Tip: Run stash commands from your repository root to avoid path issues.

- Saves all unstaged and untracked files from the changelist.
- Staged files are left alone (so you can commit them separately).
- The stash is named after your changelist and timestamped.

#### Unstash a changelist

```
git cl unstash <changelist-name>
```

- Restores the previously stashed changes.
- Warns if files conflict with current working directory.

#### Stash all changelists

```
git cl stash --all
```

- Stashes all active changelists at once

Tip: Your files aren’t deleted — they’re just “put in a box” until you bring them back with unstash.

### 3.2 Create a branch from a changelist

You can turn a changelist into its own branch in one step — great for separating work mid-feature or starting a dedicated branch for a new idea.

```
git cl branch <changelist-name> [<branch-name>] [--from <base-branch>]
```

What happens under the hood:

1. Saves (stashes) all active changelists.
2. Creates and checks out the new branch.
3. Restores only the chosen changelist on that branch — the other changelists remain stashed and can be restored with `git cl unstash` later.

See [Section 4.2](#42-branching-mid-feature-with-git-cl-branch) for a worked example.

[↑ Back to top](#git-cl-a-git-subcommand-for-changelist-management)

## 4. Example Workflows

Perfect for developers who prefer to organise their work logically from the start, rather than managing [complex commit history](https://git-scm.com/docs/git-rebase) afterward.

### 4.1 Changelists as Named Staging Areas

`git-cl` changelists function as named pre-staging areas. Instead of staging files directly, you organise them into changelists — then selectively [stage](#stage-a-changelist) or [commit](#25-commit-a-changelist) based on those names.

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

Once you're satisfied with the files in the changelist `ok`, you stage and commit them:

```
git cl stage ok
git commit -m "Implement core feature"
```

The other changelists remain untouched, keeping your workspace organised and uncommitted changes visible.


### 4.2 Branching Mid-Feature with git cl branch

Sometimes you’re deep in the middle of a changelist — maybe tweaking numerical algorithms or refactoring simulation code — and you realise it would be cleaner to finish the work on a separate branch.
`git cl branch` makes that move painless, without committing incomplete work.

Let’s say you’re improving the performance of a weather simulation in Fortran. You’ve grouped your edits into a changelist:

```
git cl add solver-opt src/solver.f90 src/utils_math.f90
```

You’re not ready to commit, but you decide this optimisation deserves its own branch. Use:

```
git cl branch solver-opt
```

Your workspace will now look like you never left, but you’re on a dedicated branch:

```
$ git cl st
solver-opt:
  [ M] src/solver.f90
  [ M] src/utils_math.f90
```

This preserves your work-in-progress and the changelist grouping — so you can pick up right where you left off. Unlike [git stash](https://git-scm.com/docs/git-stash), [git cl branch](#32-create-a-branch-from-a-changelist) is changelist-aware. You don’t lose file intent or grouping across branches.

If you prefer a custom branch name or base branch, you can specify them:

```
git cl branch solver-opt feature/fortran-speedup --from main
```

This workflow is especially handy when experimental work — like optimising a finite-difference solver or changing file I/O routines — starts to grow beyond the original scope of your current branch.
It keeps unrelated changes isolated and easy to review later.

[↑ Back to top](#git-cl-a-git-subcommand-for-changelist-management)

## 5. FAQ & Common Pitfalls

### How do I move a file from one changelist to another?

Just run [git cl add](#21-add-files-to-a-changelist) with the new changelist name. You don't need to remove it from the old one manually.

```
git cl add new-list path/to/file
```

This automatically reassigns the file to new-list.

### Why are changelists deleted after I commit?

[git cl commit](#25-Commit-a-changelist) always deletes the changelist after committing, unless you explicitly use the `--keep` flag:

```
git cl commit my-list -m "Implement my feature" --keep
```

[git cl stage](#24-stage-and-unstage-a-changelist), [git cl unstage](#unstage-a-changelist), and [git cl checkout](#28-checkout-a-changelist) behave differently — they keep the changelist by default. If you want to remove it in those cases, pass `--delete`:

```
git cl stage my-list
git cl unstage my-list 
git cl checkout my-list --delete
```

This way, you can choose whether the changelist sticks around after staging or reverting.

### Why aren’t untracked files included when I stage or commit a changelist?

`git cl` only stages or commits files already tracked by Git.

If a file is untracked (`[??]`), it will show up in `git cl st`, but won’t be included when staging or committing.

To include it:

```
git add my-file.txt
git cl stage my-changelist
```

### Are changelists shared between team members?

No. Changelists are stored locally in `.git/cl.json` and are not version-controlled or shared via Git. They’re like personal sticky notes on your working directory and visible only to you.

### Do changelists persist when switching branches?

Yes — changelists are local and independent of [branches](https://git-scm.com/docs/git-branch). This means:

- You can keep working on the same files across branches
- But beware: a changelist may reference files that don't exist in the new branch

If things get messy, delete a stale changelist:

```
git cl delete old-list
```

### How do I pause work in progress without committing?

Use `git cl stash <name>`, then switch branches and [git cl unstash](#31-stash-and-unstash-changelists) when ready.

### Why don’t I see all files in git cl status?

By default, [git cl status](#22-view-status-by-changelist) filters out files with uncommon Git status codes (e.g. merge conflicts or type changes) to keep the output clean.

If you want to include everything, use the `--all` flag:

```
git cl status --all
```

This will show all files, including those with status codes like `[UU]` (unmerged) or `[T ]` (type change).

### Can I reuse a changelist name later?

Yes. If the changelist was deleted after a stage or commit, you can create a new one with the same name — it's just a label, not a persistent identity.

[↑ Back to top](#git-cl-a-git-subcommand-for-changelist-management)

## 6. Command Summary

### 6.1 Command Summary Table

| Task                            | Command                                                   | Alias         | 
| ------------------------------- | --------------------------------------------------------- | ------------- |
| Add files to a changelist       | `git cl add <name> <files...>`                            | `git cl a`    |
| View grouped status             | `git cl status [--all] [--no-color] `                     | `git cl st`   | 
| Show diff for changelist(s)     | `git cl diff <name1> [<name2> ...] [--staged]`            |               |
| Stage a changelist              | `git cl stage <name> [--delete]`                          |               |
| Unstage a changelist            | `git cl unstage <name> [--delete]`                        |               |
| Commit with inline message      | `git cl commit <name> -m "Message" [--keep]`              | `git cl ci`   |
| Commit using message from file  | `git cl commit <name> -F message.txt [--keep]`            |               |
| Revert changelist to HEAD	      | `git cl checkout <name>`                                  | `git cl co`   |
| Remove files from changelists   | `git cl remove <file1> <file2> ...`                       | `git cl rm`   |
| Delete changelists              | `git cl delete <name1> <name2> ...`                       | `git cl del`  | 
| Stash a changelist              | `git cl stash <name>`                                     |               |
| Unstash a changelist            | `git cl unstash <name> [--force]`                         |               |
| Create branch from changelist   | `git cl branch <name> [<branch>] [--from <base>]`         | `git cl br`   |
| Show help                       | `git cl help`                                             |               |

### 6.2 Git Status Code Reference

`git cl status` uses standard Git status codes — shown as two-character prefixes (e.g. `[M ]`, `[??]`).

#### Common Status Codes

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

To show all codes, including rare ones like `[UU]` (conflicts), use:

```
git cl status --all
```

#### Additional Codes

| Code  | Description             |
| ----- | ----------------------- |
| `[UU]` | Unmerged (conflict)     |
| `[T ]` | Type change             |

#### Color Key

| Color   | Meaning                       |
|---------|-------------------------------|
| Green   | Staged changes (`[M ]`, `[A ]`)|
| Red     | Unstaged changes (`[ M]`, `[ D]`)|
| Magenta | Both staged and unstaged (`[MM]`, `[AM]`)|
| Blue    | Untracked (`[??]`)            |

You can disable color output with:

```
git cl status --no-color
```

or set `NO_COLOR=1` in your environment.

See also: [Git status documentation](https://git-scm.com/docs/git-status)


[↑ Back to top](#git-cl-a-git-subcommand-for-changelist-management)
