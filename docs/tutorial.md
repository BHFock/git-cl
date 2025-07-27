# git-cl Tutorial

**Status:** Draft Tutorial 

Welcome to the `git-cl` tutorial — a lightweight Git extension for organising your working directory changes into **named changelists**. This helps you manage multiple ongoing changes efficiently before staging or committing them.

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

4. Ensure `~/bin` is in your `PATH`, e.g. in `.bashrc` or `.zshrc`:

   ```bash
   export PATH="$HOME/bin:$PATH"

## 2. Basic Commands

### Adding files to a changelist

When you have related changes in multiple files, you can group them together under a meaningful changelist name. This helps keep your work organised before staging or committing.

To add files to a changelist, use:


```bash
git cl add <changelist-name> <file1> <file2> ...
```

This command moves the specified files into the named changelist, removing them from any other changelist if necessary.

#### Example

Say you're working on documentation updates in README.md and docs/index.md. Group these files into a docs changelist:


```bash
git cl add docs README.md docs/index.md
```

Now these files are grouped and can be handled together in later commands.

### Listing all changelists

To see what changelists you have and which files belong to each, run:

```bash
git cl list
```

or the shortcut:

```bash
git cl ls
```

#### Example output

```bash
docs:
  README.md
  docs/index.md
tests:
  tests/dev_env.sh
```

### Viewing the status of your working directory by changelist

When you're juggling several changes at once, it's helpful to see which files belong to which changelist. That’s what `git cl st` does.

```bash
git cl status
# or
git cl st
```

This command shows your working directory `git status` grouped by changelist. Modified files that aren't part of any changelist will appear under a separate No Changelist section.


#### Example output

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

This makes it easy to keep track of your intent: documentation changes are in one group, test setup in another, and ungrouped edits are still visible but clearly separated

### Staging changes from a changelist

Once you’re ready to commit a group of changes, you can stage them all at once by changelist name.

```
git cl stage <changelist-name>
```

This will:

- Add all tracked files in that changelist to the Git staging area
- Skip untracked files (like new files not yet added via git add)
- Delete the changelist after staging

#### Example

```
git cl stage docs
git commit -m "Improve documentation"
```

Now the documentation files are committed, and the docs changelist is gone — because it served its purpose

### Committing directly from a changelist

Prefer to skip the separate `git commit` step? You can do both at once:

```
git cl commit <changelist-name> -m "Your commit message"
```

This will:

- Commit all tracked files with the given message
- Delete the changelist


#### Example

```
git cl commit tests -m "Set up test environment"
```

This is handy for small focused changes where you’re ready to commit immediately. Alternatively to writing the commit message on the command line you can also read in the commit message from a file:

```
git cl commit <changelist-name> -F commit_message.txt
```

### Removing files from changelists

If you no longer want a file to be grouped under a specific changelist, you can remove it using

```
git cl remove <file1> <file2> ...
```

This removes the listed files from whichever changelist they currently belong to. The files will still exist in your working directory — they're just no longer grouped.

#### Example

```
git cl remove notes/debug.txt
```

The file `notes/debug.txt` will now appear under the `No Changelist` section in `git cl st`.

### Deleting a changelist

Once a changelist has served its purpose you may want to remove the group itself

```
git cl delete <changelist-name>
```

This deletes the changelist entry, but does not affect the files in your working directory. Files that were part of the deleted changelist will appear under No Changelist if they’re still modified or untracked.

## 3. Example Workflow

Suppose you're working on both documentation and a test setup.

```
git cl add docs README.md docs/index.md
git cl add tests tests/dev_env.sh
git cl add temp notes/debug.txt
```

You can check the changelists:

```
git cl st
```

Once the documentation changes are ready:

```
git cl stage docs
git commit -m "Refactor documentation"
```

The other changelists remain untouched, so you can continue working on them separately.

## 4. Tips, Notes & Troubleshooting

### Files belong to only one changelist

Each file can be part of only one changelist at a time. Adding it to a new changelist will automatically remove it from any previous one.

### Moving a file between changelists

You don’t need to manually remove a file from one changelist before adding it to another. Just run:

```
git cl add new-list path/to/file
```

This automatically reassigns the file to the new changelist.

### Untracked files aren’t automatically staged or committed

Untracked files (those marked `[??]` in `git status`) will show up in `git cl st` if they’re part of a changelist — but they won't be staged or committed by `git cl stage` or `git cl commit`.

To include them:

1. Use `git add <file>` manually
2. Then stage or commit the changelist

### Changelists are local

All changelist metadata is stored in `.git/cl.json`. This is local to your repository and never shared via Git, keeping changelist structure flexible and personal.

### Works with any branch

Changelists are independent of branches because they are just lists of files stored in `.git/cl.json`. They will continue to exist even if you change branches. This can be helpful — or potentially confusing. When in doubt, delete your changelists before switching branches

## 5. Command Summary

| Task                           | Command                               |
| ------------------------------ | ------------------------------------- |
| Add files to a changelist      | `git cl add <name> <files...>`        |
| List changelists               | `git cl list` or `git cl ls`          |
| View grouped status            | `git cl status` or `git cl st`        |
| Stage a changelist             | `git cl stage <name>`                 |
| Commit with inline message     | `git cl commit <name> -m "Message"`   |
| Commit using message from file | `git cl commit <name> -F message.txt` |
| Remove file from changelist    | `git cl remove <file>`                |
| Delete a changelist            | `git cl delete <name>`                |
