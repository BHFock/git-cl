
![Status: Prototype](https://img.shields.io/badge/status-prototype-blue)

# git-cl

`git-cl` is a command-line tool that introduces changelists to Git, inspired by Subversion’s workflow grouping. It allows users to assign working directory files to named changelists, making it easier to manage partial commits and organise work by intent.

## Features

- Create and manage named changelists
- View changes grouped by changelist
- Stage and commit changelist contents selectively
- Simple JSON-based local tracking (no changes to Git internals)
- Seamless integration via `git cl` subcommand interface

## Installation

To use `git cl` as a [Git subcommand](https://git.github.io/htmldocs/howto/new-command.html), place the executable script named `git-cl` in a directory that’s part of your system’s `$PATH`, such as `~/bin`. For example:

```bash
chmod +x git-cl
mkdir -p ~/bin
mv git-cl ~/bin/
```

Make sure `~/bin` is listed in your `$PATH`. You’ll then be able to run:

```bash
git cl list
```

Git will recognise `git-cl` as the handler for `git cl`, just like its built-in commands.

### Optional: Replace `git status` with changelist view

For a more integrated experience, you can alias `git st` to show the changelist-enhanced status:

```bash
git config alias.st '!git cl st'
```

After setting this alias, `git st` will show your modified files grouped by changelist, making it easier to decide what to stage next. This is particularly useful for former Subversion users who want to maintain a similar workflow.

## Usage

Below are a few common tasks using `git cl`:

```bash
# Create a changelist implicitly by adding files to it
git cl add docs-fix README.md docs/index.md

# List all changelists and their assigned files
git cl list       # or: git cl ls

# View modified files grouped by changelist
git cl status     # or: git cl st

# Stage all files in a changelist and delete it
git cl stage docs-fix

# Commit all changes in a changelist
git cl commit docs-fix -m "Update documentation layout and intro"

# Remove a file from its changelist
git cl remove README.md

# Delete a changelist manually (even if it still contains files)
git cl delete docs-fix
```

Changelists are created on demand when adding files. Every changelist must be named explicitly — there is no default or unnamed group

## Example Workflow

Let’s say you’re working on a feature, making several changes across multiple files. Instead of staging them immediately, you group them by intent:

```bash
# Add files you're happy with to a changelist
git cl add ok src/core.py tests/test_core.py

# Add test-specific or experimental changes to a separate list
git cl add test_only tests/setup_test_env.sh

# Add files you know you don't want to commit yet
git cl add do_not_commit notes/tmp.txt
```

You iterate and clean up your work. To see what you have, check the changelist status:

```bash
git cl st    # or 'git st' if you've set up the alias
```

Once everything in the `ok` changelist is confirmed, you stage those files with:

```bash
git cl stage ok
```

This moves the files to Git’s index and clears the changelist — ready for a focused commit:

```bash
git commit -m "Implement core feature"
```

Meanwhile, other changelists remain untouched and visible in `git cl status` — keeping your workspace organised without hiding files from your main view.
