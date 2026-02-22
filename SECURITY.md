# Security

If you notice something that might be a security issue, please report it privately using GitHub’s [security advisory form](../../security/advisories/new).

This allows you to share details confidentially, giving me a chance to review and respond before any public disclosure. While there's no guaranteed response or timeline, thoughtful reports are always appreciated.

## Notes on Code Safety

This tool includes some basic safeguards by design:

- All file paths are sanitised and resolved to prevent directory traversal or injection issues
- Changelist names are validated against a restricted character set (no shell metacharacters)
- Git commands are executed using safe, argument-based subprocess calls (no shell=True)
- JSON metadata is stored locally (`.git/cl.json`) using standard file permissions

`git-cl` is not intended for multi-user or remote use, and is best suited for local developer workflows.

While it's not security-critical software, care has been taken to avoid common pitfalls and insecure patterns. If something looks off — even if you're not sure — feel free to reach out.

Thanks for helping keep [git-cl](https://github.com/BHFock/git-cl) safe and clean!
