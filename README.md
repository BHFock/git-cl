# git-cl

`git-cl` is a command-line tool that introduces changelists to Git, inspired by Subversion's workflow grouping. It allows users to assign working directory files to named changelists, making it easier to manage partial commits and organise work by intent.

## Features

- Create and manage named changelists
- View changes grouped by changelist
- Stage and commit changelist contents selectively
- Simple JSON-based local tracking (no changes to Git internals)
- Seamless integration via `git cl` subcommand interface

## Installation

Make sure `git-cl` is executable and available in your `$PATH`. A common setup uses your home directory:

```bash
chmod +x git-cl
mkdir -p ~/bin
mv git-cl ~/bin/
