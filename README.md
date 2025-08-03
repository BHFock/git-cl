<!--
git-cl is a minimal Git subcommand that brings changelist support to Git. Organise modified files into named changelists before staging or committing. Ideal for managing partial commits.
-->
# git-cl

> A Git subcommand for managing named changelists — group files into changelists before staging.

[![Git Changelist Tutorial](https://img.shields.io/badge/Tutorial-View-blue)](https://github.com/BHFock/git-cl/blob/main/docs/tutorial.md)


`git-cl` is a command-line tool that offers Git changelist support, inspired by Subversion. It allows users to assign working directory files to named changelists, helping organise work by intent and manage partial commits more easily.

Perfect for developers who prefer to organise their work logically from the start, rather than managing complex commit history afterward.

## Why git-cl?

- Group files logically before staging using Git changelists
- Work on multiple features on a single branch
- Stage and commit changes by intent
- Local-only metadata (`.git/cl.json`)
- Simple CLI: `git cl <command>`

## Quick Start

### Install

```
mkdir -p ~/bin
wget https://raw.githubusercontent.com/BHFock/git-cl/main/git-cl -O ~/bin/git-cl
chmod +x ~/bin/git-cl
```

Make sure `~/bin` is listed in your `$PATH`. 

### Verify Installation

```
git cl --version
git cl help
```

### Create & use changelists inside a Git repository

```
git cl add fixup file1.py
git cl status
git cl commit fixup -m "Fix file1"
```

## Common Commands

```bash
# Add files to a changelist
git cl add docs-fix README.md docs/index.md

# See changes grouped by changelist
git cl status

# Stage or commit changelists
git cl stage docs-fix
git cl commit docs-fix -m "Update documentation layout and intro"

# Keep the changelist after committing
git cl commit docs-fix -m "Fix bug" --keep

# Remove a file from its changelist
git cl remove README.md

# Delete a changelist
git cl delete docs-fix
```

## Example Output

<p align="left">
  <img src="docs/git-cl.png" alt="git-cl status changelist screenshot in terminal" width="220"/>
</p>

## Notes

- Requires Python 3.9+, Git, and a Unix-like OS
- Changelists are local and not version-controlled
- See the [tutorial](docs/tutorial.md) for full details
  
## Project status

`git-cl` is feature-complete and stable, with core functionality tested locally. While it's not yet been used extensively in real-world, long-term workflows, it’s ready for practical use.

Further development is not planned. The project is shared as-is for anyone who finds it useful, or wishes to fork or adapt it under the license terms.

## License

BSD 3-Clause License — see [LICENSE](./LICENSE) for details.

<!--
Keywords: git changelist, svn changelist, partial commit, group files, perforce, git extension, organize changes, subversion
-->

