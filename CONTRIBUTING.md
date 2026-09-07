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

> Security issues: please do **not** open a public issue — see [SECURITY.md](SECURITY.md).

### Documentation Improvements

- **Fix** typos, broken links, unclear explanations
- **Add** missing examples for existing features  
- **Suggest** FAQ additions based on real user questions
- **Check** the [tutorial](docs/tutorial.md) for clarity and completeness
- **Evaluate** the [design documentation](docs/design-notes.md) for technical accuracy

### Testing & Compatibility Reports

- **Report** compatibility with different Python/Git versions
- **Run** the [test suite](https://github.com/BHFock/git-cl/blob/main/tests/README.md) on different operating systems
- **Share** edge cases you've tried

### External Integrations

git-cl is intentionally a focused CLI tool and GUI development is out of scope for this repository. However, editor and GUI integrations (e.g. Emacs/Magit, VSCode, JetBrains) are very welcome as **separate, independently maintained projects**.

If you want to build a GUI integration, everything you need is available:
- The changelist data is stored in `.git/cl.json`; stashed changelists move to `.git/cl-stashes.json` until they are unstashed — read both for a complete picture
- Combine it with standard `git status` output for a full picture of the working tree
- Call `git cl add`, `git cl stage`, `git cl commit`, `git cl stash`, `git cl branch` etc. directly for all operations

If you build a GUI integration, open an issue — I'll link to it from the README's Ecosystem section.

### Packaging

git-cl is published on [PyPI](https://pypi.org/project/git-changelists/) and can also be installed by downloading the single script. I don't plan to maintain distribution packages myself.

Packaging for Homebrew, AUR, nixpkgs, conda-forge or a Linux distribution is welcome as an **independently maintained** effort — no coordination with me is needed. Each release is tagged in Git and published to PyPI, so the source is stable to build from.

Please note in the package that it is community maintained, and point bug reports here only for issues reproducible with a pip or direct-script install — see [Before Opening an Issue](#before-opening-an-issue). I can't support packaging problems in downstream builds.

### Pull Requests

Please **open an issue before writing code**. For a feature complete project, an unsolicited pull request is likely to be declined — not because the work is bad, but because it may not fit the intended scope. Typo and documentation fixes are the exception: send those directly. Contributions are accepted under the BSD 3-Clause License.

## What I'm Not Looking For

To keep git-cl simple and maintainable, I don't plan to add:

- New features or commands
- Major architectural changes
- Alternative file formats or storage backends
- GUI or web interfaces as part of this repository
- Distribution packaging (Homebrew, AUR, distro packages) as part of this repository

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
