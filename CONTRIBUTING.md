# Contributing to git-cl

Thanks for your interest in [git-cl](https://github.com/BHFock/git-cl)! This project is **feature complete**. All planned functionality has been implemented. Future development focuses on **maintenance, bug fixes, and usability improvements** rather than new features.

**Best way to help:** Report reproducible bugs or improve documentation.

## Project Status

git-cl is a feature complete, focused tool with a clear scope. While I appreciate feature ideas, I'm **not actively seeking new functionality** — the tool already does what it was designed to do.

## How You Can Help

### Bug Reports — Most valuable contribution!

- **Check** [existing issues](https://github.com/BHFock/git-cl/issues) first
- **Include** your Python version, OS, and git-cl version (`git cl --version`)
- **Provide** clear steps to reproduce
- **Attach** relevant error messages or **describe** unexpected behaviour

### Documentation Improvements

- **Fix** typos, broken links, unclear explanations
- **Add** missing examples for existing features  
- **Suggest** FAQ additions based on real user questions
- **Check** the [tutorial](docs/tutorial.md) for clarity and completeness
- **Evaluate** the [design documentation](docs/design-notes.md) for technical accuracy

### Testing & Compatibility Reports

- **Report** compatibility with different Python/Git versions
- **Test** on different operating systems
- **Share** edge cases you've tried

### External GUI Projects
git-cl is intentionally a focused CLI tool and GUI development is out of scope for this repository. However, GUI integrations (e.g. 
Emacs/Magit, VSCode, JetBrains) are very welcome as **separate, independently maintained projects**.

If you want to build a GUI integration, everything you need is available:
- The changelist data is stored in `.git/git-cl.json` — a stable, documented format that won't change
- Combine it with standard `git status` output for a full picture of the working tree
- Call `git cl add`, `git cl stage`, `git cl commit`, `git cl stash`, `git cl branch` etc. directly for all operations

If you build a GUI integration, open an issue — I'll link to it from the README.

## What I'm Not Looking For

To keep git-cl simple and maintainable, I don’t plan to add:

- New features or commands
- Major architectural changes
- Alternative file formats or storage backends
- GUI or web interfaces as part of this repository

## Before Opening an Issue

**1. Read** the [tutorial](docs/tutorial.md) and [FAQ](docs/tutorial.md#5-faq--common-pitfalls)

**2. Try** the [latest version](https://raw.githubusercontent.com/BHFock/git-cl/main/git-cl) to rule out already-fixed issues

**3. Search** existing [issues](https://github.com/BHFock/git-cl/issues) — your question might already be answered

**4. Use issue templates** to [report a bug](https://github.com/BHFock/git-cl/issues/new?template=bug_report.md) or to [report a documentation issue](https://github.com/BHFock/git-cl/issues/new?template=documentation-issue.md).

## Development Philosophy

[git-cl](https://github.com/BHFock/git-cl) follows the Unix philosophy: **do one thing well**. 

It brings SVN-style changelists to Git, nothing more. This focused scope is intentional and helps keep the tool reliable and understandable.

## Response Expectations

I maintain git-cl in my spare time. I'll do my best to:

- **Respond** to bug reports
- **Fix** genuine bugs as time permits
- **Consider** documentation improvements

I may not respond to feature requests or questions already covered in the documentation.

Thanks for helping keep [git-cl](https://github.com/BHFock/git-cl) stable and useful!
