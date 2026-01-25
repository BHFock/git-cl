<!--
git-cl is a minimal Git subcommand that brings changelist support to Git. Organise modified files into named changelists before staging or committing. Ideal for managing partial commits.
-->
# git-cl

> A Git subcommand for managing named changelists — organise files by purpose before staging.

[![Git Changelist Tutorial](https://img.shields.io/badge/Tutorial-View-blue)](https://github.com/BHFock/git-cl/blob/main/docs/tutorial.md)

`git-cl` is a command-line tool that offers Git changelist support, inspired by Subversion. It allows users to assign working directory files to named changelists, helping organise work by intent, manage partial commits, and create branches directly from a changelist.

Perfect for developers who prefer to organise their work logically from the start, rather than managing complex commit history afterwards.

## Why git-cl?

- Group files logically before staging using Git changelists
- Work on multiple features on a single branch
- Stage and commit changes by intent
- Stash changelists and resume work later
- Create a new branch directly from a changelist
- Local-only metadata (`.git/cl.json`)
- Simple CLI: `git cl <command>`

## Branching from changelists

<p align="left">
  <img src="docs/git-cl.svg" alt="git-cl workflow: changelists in working directory moving to a new branch" width="800"/>
</p>


## Quick Start

```
# Install
mkdir -p ~/bin
wget https://raw.githubusercontent.com/BHFock/git-cl/main/git-cl -O ~/bin/git-cl
chmod +x ~/bin/git-cl

# Verify Installation
git cl --version
git cl help

# Use changelists inside a Git repository
git cl add fixup file1.py
git cl status
git cl commit fixup -m "Fix file1"
```

Make sure `~/bin` is listed in your `$PATH`. 


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

# Temporarily stash a changelist and resume work on a new branch
git cl stash docs-fix
git checkout -b docs-fix-work
git cl unstash docs-fix

# Create and switch to a new branch from a changelist (auto-stash/unstash)
git cl br docs-fix
```

## Example Output

<p align="left">
  <img src="docs/git-cl.png" alt="git-cl status changelist screenshot in terminal" width="220"/>
</p>

## Documentation

📘 [Full Tutorial](docs/tutorial.md): Comprehensive guide with detailed examples

📘 [Design Notes](docs/design-notes.md): Technical architecture and implementation

📘 [Why git-cl?](docs/why-git-cl.md): History and motivation behind the tool

## Getting Help

```
git cl help              # General help
git cl <command> -h      # Command-specific help
```

### Common Issues:
- **Untracked files not staging?** Use `git add` first, then `git cl stage`
- **Changelist deleted after commit?** This is default behaviour. Use `--keep` to preserve it.
- **Command not found?** Check that `~/bin` is in your `$PATH`

See the [FAQ](docs/tutorial.md#5-faq--common-pitfalls) for more troubleshooting.


## Notes

- Requires Python 3.9+, Git, and a Unix-like OS
- Designed for single-user workflows, concurrent operations may conflict
- Always inspect downloaded scripts before executing. See [git-cl](https://github.com/BHFock/git-cl/blob/main/git-cl) for source.
- For security considerations or to report vulnerabilities, see [SECURITY](./SECURITY.md).

## Project status

`git-cl` is now feature complete. All planned functionality has been implemented, including changelist creation, staging, committing, stashing, and branching. Future updates will focus on code refactoring, bug fixes, and usability improvements — no major new features are planned.

See [CONTRIBUTING](CONTRIBUTING.md) for guidelines on bug reports and documentation improvements.

Use, fork, or adapt freely under the BSD license.

## License

BSD 3-Clause License — see [LICENSE](./LICENSE) for details.

<!--
Keywords: git changelist, svn changelist, partial commit, group files, perforce, git extension, organise changes, subversion, named staging area, pre-staging, commit logical units, selective commit
-->
