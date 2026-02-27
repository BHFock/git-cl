<!--
git-cl is a minimal Git subcommand that brings changelist support to Git. Organise modified files into named changelists before staging or committing. Ideal for managing partial commits.
-->
# git-cl

> A pre-staging layer for organising changes in Git

[![Tutorial](https://img.shields.io/badge/Tutorial-View-blue)](https://github.com/BHFock/git-cl/blob/main/docs/tutorial.md)
[![Paper](https://img.shields.io/badge/Paper-Read-blue)](https://github.com/BHFock/git-cl/blob/main/docs/paper.md)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.18722077-blue)](https://doi.org/10.5281/zenodo.18722077)
[![PyPI](https://img.shields.io/pypi/v/git-changelists)](https://pypi.org/project/git-changelists/)
[![Tests](https://github.com/BHFock/git-cl/actions/workflows/test.yml/badge.svg)](https://github.com/BHFock/git-cl/actions/workflows/test.yml)
[![GitHub stars](https://img.shields.io/github/stars/BHFock/git-cl?style=social)](https://github.com/BHFock/git-cl/stargazers)

`git-cl` is a command-line tool that brings changelist support to Git, inspired by Subversion. It adds a pre-staging review layer that lets you organise modified files into named groups before staging or committing. Changelists can be stashed selectively and promoted to dedicated branches — enabling a late-binding branching workflow where the branch decision follows the code, not the other way around.

## Why git-cl?

- Pre-staging review: group changed files by intent before staging
- Organise multiple concerns on a single branch
- Stage and commit changes by intent
- Stash changelists and resume work later
- Late-binding branching: promote a changelist to a dedicated branch
- Local-only metadata (`.git/cl.json`)
- Simple CLI: `git cl <command>`

## Demo 

<a href="https://github.com/BHFock/git-cl/blob/main/docs/tutorial.md">
  <img src="https://raw.githubusercontent.com/BHFock/git-cl/refs/heads/main/docs/demo/git-cl-demo.gif" alt="git-cl demo: creating changelists, viewing status, and branching" width="750"/>
</a>

## Quick Start

### Install via pip
```
pip install git-changelists
```

### Install via wget
```
mkdir -p ~/bin
wget https://raw.githubusercontent.com/BHFock/git-cl/main/git-cl -O ~/bin/git-cl
chmod +x ~/bin/git-cl
```
Make sure `~/bin` is listed in your `$PATH`.

### Verify installation
```
git cl --version
git cl help
```

### Use changelists inside a Git repository
```bash
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

# Late-binding branching: create a branch from a changelist (auto-stash/unstash)
git cl br docs-fix
```

## Documentation

📘 [Tutorial](docs/tutorial.md): Guide with examples and FAQ

📘 [Design Notes](docs/design-notes.md): Technical architecture

📘 [Tests](tests/README.md): Test suite and shell walkthroughs

📘 [Why git-cl?](docs/why-git-cl.md): History and motivation

📘 [Paper](docs/paper.md): Design, workflow, and related work


## Notes

- Requires Python 3.9+ and Git
- Local-only; designed for single-user workflows
- Always inspect downloaded scripts before executing, see [source](https://github.com/BHFock/git-cl/blob/main/git-cl)
- For security concerns, see [SECURITY](./SECURITY.md)

## License

BSD 3-Clause — see [LICENSE](./LICENSE) | [CONTRIBUTING](CONTRIBUTING.md)

<!--
Keywords: git changelist, svn changelist, partial commit, group files, perforce, git extension, organise changes, subversion, named staging area, pre-staging, commit logical units, selective commit, late-binding branching
-->
