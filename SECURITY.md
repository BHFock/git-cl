# Security

If you notice something that might be a security issue, please report it privately using GitHub’s [security advisory form](../../security/advisories/new).

This allows you to share details confidentially, giving me a chance to review and respond before any public disclosure. While there's no guaranteed response or timeline, thoughtful reports are always appreciated.

## Supported Versions

Fixes are made for the latest release only. Please check that a problem still occurs with it, or with the current state of `main`, before reporting it.

## Notes on Code Safety

This tool includes some basic safeguards by design:

- All file paths are sanitised and resolved to prevent directory traversal or injection issues
- Changelist names are validated against a restricted character set (no shell metacharacters)
- Git commands are executed using safe, argument-based subprocess calls (no shell=True)
- Stored paths are passed to Git as literal file names, so a name such as `*.md` never matches other files
- Control characters in file and changelist names are escaped in all output, as `git status` does, so a name cannot send commands to the terminal
- JSON metadata is stored locally in the Git directory (`.git/cl.json`; in a linked worktree, `.git/worktrees/<name>/cl.json`). On Linux and macOS, only you can read and write it (mode 0600)

`git-cl` is not intended for multi-user or remote use, and is best suited for local developer workflows.

git-cl runs Git, so the hooks and configuration of a repository apply as they do for Git itself. As with Git, only work in repositories whose hooks and configuration you trust.

While it's not security-critical software, care has been taken to avoid common pitfalls and insecure patterns. If something looks off — even if you're not sure — feel free to reach out.

Thanks for helping keep [git-cl](https://github.com/BHFock/git-cl) safe and clean!
