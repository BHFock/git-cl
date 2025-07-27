# git-cl Tutorial

**Status:** Draft Tutorial 

Welcome to the `git-cl` tutorial — a lightweight tool to organise your Git working directory changes into **named changelists**. This helps you manage multiple ongoing changes efficiently before staging or committing them.

## What is `git-cl`?

`git-cl` is a Git Subcommand inspired by Subversion changelists. It lets you group related file changes under a named label — ideal for organising and managing uncommitted changes.

Use it when:

- Working on multiple features or fixes simultaneously
- Wanting to break down a messy working directory into manageable parts
- Staging changes logically by intent, not just by file

Changelists are stored locally in `.git/cl.json`, keeping everything isolated and version-neutral.


## How changelists fit into Git workflows

| Concept        | Description                                | Purpose                          |
|----------------|--------------------------------------------|----------------------------------|
| Changelist     | A named group of files in the working tree | Organise uncommitted changes     |
| Staging Area   | Selects what to include in a commit        | Prepare commit content           |
| Branch         | A line of development with history         | Isolate parallel development     |

Changelists are complementary to branches and staging — they help organise **uncommitted** work within a branch.

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


### Remove files from changelists

```
git cl remove <file1> <file2> ...
```

### Delete a changelist

```
git cl delete <changelist-name>
```

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


## 4. Optional: Alias for git st

To use git st for grouped status:

```
git config alias.st '!git cl st'
```

Now you can run:

```
git st
```

To get a changelist-aware status view.

## 5. Notes

- A file can belong to only one changelist at a time.
- Untracked files are shown but are not included in staging or commits.
- Changelists are stored in .git/cl.json and are never versioned or shared.
- You can use changelists inside any branch.

## Summary of Commands

| Task                        | Command                             |
| --------------------------- | ----------------------------------- |
| Add files to a changelist   | `git cl add <name> <files...>`      |
| List changelists            | `git cl list` or `git cl ls`        |
| View grouped status         | `git cl status` or `git cl st`      |
| Stage a changelist          | `git cl stage <name>`               |
| Commit a changelist         | `git cl commit <name> -m "Message"` |
| Remove file from changelist | `git cl remove <file>`              |
| Delete a changelist         | `git cl delete <name>`              |

