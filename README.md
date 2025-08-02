
# git-cl

> A Git subcommand for managing named changelists — group files into changelists before staging.

[![Tutorial](https://img.shields.io/badge/Tutorial-View-blue)](https://github.com/BHFock/git-cl/blob/main/docs/tutorial.md)

`git-cl` is a command-line tool for Git that introduces Subversion-style changelists. It allows users to assign working directory files to named changelists, helping organise work by intent and manage partial commits more easily.

## Why git-cl?

- Group files logically before staging
- Work on multiple features on a single branch
- Stage/commit changes by intent, not path
- Local-only metadata (`.git/cl.json`)
- Simple CLI: `git cl <command>`

## Quick Start

```
# Install
mkdir -p ~/bin
curl -sLo ~/bin/git-cl https://raw.githubusercontent.com/BHFock/git-cl/main/git-cl
chmod +x ~/bin/git-cl

# Verify Installation
git cl --version
git cl help

# Create & use changelist
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
```

## Example Output

<p align="left">
  <img src="docs/git-cl.png" alt="Screenshot git cl status" width="225"/>
</p>

## Notes

- Requires Python 3.9+, Git, and a Unix-like OS
- Changelists are local and not version-controlled
- See the [tutorial](docs/tutorial.md) for full details
  
## Maintenance Disclaimer

This is a personal tool, built to support my own Git workflow. No active maintenance or collaboration is planned. ´git-cl` is considered feature-complete. It remains available for use, fork, or adaptation under the license terms. Further changes are not planned.

## License

BSD 3-Clause License — see [LICENSE](./LICENSE) for details.

<!--
#git-changelists #git-workflow-tools #svn-style-git #git-cli #partial-commits #git-subcommand
-->

