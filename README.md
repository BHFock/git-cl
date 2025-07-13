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
