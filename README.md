# git-cl

`git-cl` is a command-line tool that introduces changelists to Git, inspired by Subversion's workflow grouping. It allows users to assign working directory files to named changelists, making it easier to manage partial commits and organise work by intent.

## Features

- Create and manage named changelists
- View changes grouped by changelist
- Stage and commit changelist contents selectively
- Simple JSON-based local tracking (no changes to Git internals)
- Seamless integration via `git cl` subcommand interface

## Installation

To use `git cl` as a [Git subcommand](https://git.github.io/htmldocs/howto/new-command.html), place the executable script named `git-cl` in a directory that's part of your system’s `$PATH`, such as `~/bin`. For example:

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


## Usage

Below are a few common tasks using `git cl`:

```bash
# Create a changelist implicitly by adding files to it
git cl add docs-fix README.md docs/index.md

# List all changelists and their assigned files
git cl list       # or: git cl ls

# View modified files grouped by changelist
git cl status     # or: git cl st

# Commit all changes in a changelist
git cl commit docs-fix -m "Update documentation layout and intro"

# Remove files from a changelist
git cl remove docs-fix README.md

# Delete a changelist (does not modify files or Git index)
git cl delete docs-fix
```

Changelists are created on demand when adding files. Every changelist must be named explicitly — there is no default or unnamed group




