# Releasing git-cl

This document describes how to cut a new release of git-cl and publish it to
[PyPI](https://pypi.org/project/git-changelists/). It is intended for
maintainers.

git-cl uses manual releases via [`build`](https://pypi.org/project/build/) and
[`twine`](https://pypi.org/project/twine/). Releases are tagged without a `v`
prefix (e.g. `1.1.9`).

> **Note on credentials:** uploading requires a PyPI API token. The token is
> configured separately in `~/.pypirc` (or via the `TWINE_USERNAME` /
> `TWINE_PASSWORD` environment variables) and must **never** be committed to
> this repository. This document references where the token lives; it does not
> contain one.

## 1. Bump the version

The version number is recorded in three places and **all three must match**:

- `setup.cfg`
- `git-cl` (the `__version__` string)
- `CITATION.cff`

In `CITATION.cff`, also update the `date-released:` field to today's date — it
is tied to the version and will otherwise carry the previous release's date.

Update all of these before tagging. Releasing from a tree where the version
strings disagree will ship an inconsistent version string.

## 2. Pre-release checks

Make sure everything is merged and the working tree is clean:

```bash
git checkout main
git pull
git status          # should report a clean tree
```

Run the test suite and confirm it is fully green:

```bash
./tests/run_tests.py
```

## 3. Tag

Create an annotated tag matching the new version (no `v` prefix), then push it:

```bash
git tag -a 1.1.9 -m "Release 1.1.9"
git push origin 1.1.9
```

A tag is recoverable if you spot a mistake before uploading — delete it locally
(`git tag -d 1.1.9`) and on the remote (`git push origin :refs/tags/1.1.9`),
fix the problem, and re-tag. Once step 6 runs, the version is final (see below).

## 4. Build

Remove any stale artefacts so a previous build can't be uploaded by accident,
then build the source distribution and wheel:

```bash
rm -rf dist/ build/ *.egg-info
python3 -m build
```

This writes a `.tar.gz` (sdist) and a `.whl` (wheel) into `dist/`.

## 5. Check

Validate the artefacts before uploading. This catches metadata and README
rendering problems early, before they reach the live PyPI page:

```bash
twine check dist/*
```

### Optional: TestPyPI dry run

To verify the full upload path without touching the real index:

```bash
twine upload -r testpypi dist/*
pip install -i https://test.pypi.org/simple/ git-changelists
```

Worth doing after a long gap between releases; optional once the build is
trusted.

## 6. Upload to PyPI

```bash
twine upload dist/*
```

With an API token configured in `~/.pypirc`, this runs without prompting.

> **Point of no return:** PyPI does not allow a version number to be reused or
> overwritten once uploaded. If a release is wrong after this step, you cannot
> re-push the same number — fix the problem and release the next version
> instead. For this reason, do the tag-and-upload only when you are sure the
> release is final.

## 7. Verify the published package installs

This confirms the uploaded package is installable and starts cleanly. After a
short propagation delay, install it into a throwaway Conda environment:

```bash
conda create -n gitcl-test python=3.12 -y
conda activate gitcl-test
pip install git-changelists
git cl --version          # should print the version you just released
conda deactivate
conda env remove -n gitcl-test -y
```

The environment is isolated, so this tests a clean install rather than your
existing setup. Make sure you install inside the activated `gitcl-test`
environment, not your `base` environment.

## 8. Create the GitHub release

In the web UI: **Releases → Draft a new release →** choose the existing `1.1.9`
tag → **Generate release notes** → publish. No file uploads needed; PyPI is the
download source.

Unlike the PyPI upload, a GitHub release is not final — you can edit or delete
it at any time.

## Quick reference

```bash
# 1. Bump version in setup.cfg, git-cl, CITATION.cff (all must match)
#    Also update date-released: in CITATION.cff
# 2. Pre-release
git checkout main && git pull && git status
./tests/run_tests.py
# 3. Tag
git tag -a 1.1.9 -m "Release 1.1.9"
git push origin 1.1.9
# 4. Build
rm -rf dist/ build/ *.egg-info
python3 -m build
# 5. Check
twine check dist/*
# 6. Upload
twine upload dist/*
# 7. Verify in a throwaway Conda environment
conda create -n gitcl-test python=3.12 -y
conda activate gitcl-test
pip install git-changelists && git cl --version
conda deactivate
conda env remove -n gitcl-test -y
# 8. Create GitHub release in web UI (choose tag, Generate release notes, publish)
```
