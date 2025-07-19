# git-cl Tutorial

**Version:** 0.1.0  
**Status:** Prototype

## What is `git-cl`?

`git-cl` is a lightweight Git extension that adds changelist-style functionality, inspired by Subversion (SVN). It lets you group related file changes under a named label — ideal for organising changes before staging or committing them.

This is useful when:

- You're working on multiple features or fixes at once
- You want to split up a messy working directory
- You want to stage changes with intent, not just by file

Internally, changelists are stored in `.git/cl.json`, keeping everything local and version-neutral.

## Changelists vs Staging Area vs Branches

Git already has powerful tools. Here’s how changelists fit in:

| Concept        | Description                                | Purpose                          |
|----------------|--------------------------------------------|----------------------------------|
| Changelist     | A named group of files in the working tree | Organise uncommitted changes     |
| Staging Area   | Selects what to include in a commit        | Prepares a commit                |
| Branch         | A line of development with history         | Isolate parallel work streams    |

### When to use a changelist

Use changelists when you want to:

- Group files by topic before staging
- Avoid accidental commits
- Switch between related changes more easily

Changelists are not a replacement for branches — they help manage your **uncommitted** work within a branch.

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

### Add files to a changelist

```bash
git cl add <changelist-name> <file1> <file2> ...
```

Files are moved from any other changelist if needed.

Example:

```bash
git cl add docs README.md docs/index.md
```

### List changelists

```bash
git cl list
# or
git cl ls
```

### Show grouped status

```bash
git cl status
# or
git cl st
```

Example output:

```
docs:
  [M] README.md
  [M] docs/index.md

No Changelist:
  [??] scratch.txt
  [M] main.py
```

### Stage a changelist

```
git cl stage <changelist-name>
```

This will:

- Stage all tracked files
- Skip untracked or unstageable files
- Delete the changelist after staging

Example:

```
git cl stage docs
git commit -m "Improve documentation"
```

### Commit a changelist

```
git cl commit <changelist-name> -m "Commit message"
```

Stages and commits tracked files, then deletes the changelist.

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

