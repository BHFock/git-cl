# Security

If you notice something that might be a security issue, you can report it privately using GitHub’s [security advisory form](../../security/advisories/new).

This lets you share details without opening a public issue, and gives me a chance to take a look before anything is disclosed. There’s no guaranteed response or timeline, but thoughtful reports are always appreciated.

## Notes on Code Safety

This tool is designed with some basic precautions in mind:

- File paths are sanitised and resolved to prevent traversal or injection issues
- Changelist names are validated against a safe character set
- Git commands are run using explicit argument lists — never via shell
- JSON data is stored locally in the Git directory with standard file permissions

While this project isn’t security-critical, care has been taken to avoid common risky patterns. If you see something that looks off — even if you're not sure — feel free to report it.

Thanks for helping keep things safe and clean!
