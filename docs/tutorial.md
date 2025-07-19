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
