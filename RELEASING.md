# Releasing git-cl

This document describes how to cut a new release of git-cl and publish it to
[PyPI](https://pypi.org/project/git-changelists/). It is intended for
maintainers.

Releases are published by the [release workflow](.github/workflows/release.yml)
with [Trusted Publishing](https://docs.pypi.org/trusted-publishers/): pushing a
tag builds and checks the package, and the upload to PyPI waits until a
maintainer approves it in GitHub. No PyPI token is stored anywhere, and PyPI
shows an attestation that each package was built from this repository.
Releases are tagged without a `v` prefix (e.g. `1.2.0`).

> **Setup:** the workflow relies on two settings outside this repository. On
> PyPI, `git-changelists` lists the workflow `release.yml` of `BHFock/git-cl`
> with the environment `pypi` as a trusted publisher (TestPyPI likewise, with
> the environment `testpypi`). On GitHub, the environment `pypi` requires a
> reviewer and accepts version tags only (`*.*.*`). If either setting is
> changed, the upload fails or no longer waits for approval.

## 1. Bump the version

The version number is recorded in three places and **all three must match**:

- `setup.cfg`
- `git-cl` (the `__version__` string)
- `CITATION.cff`

In `CITATION.cff`, also update the `date-released:` field to today's date — it
is tied to the version and will otherwise carry the previous release's date.

The release workflow checks that all three match the tag and stops before the
upload if they do not.

Commit the version bump and push it to `main` before tagging, so that
`main` and the release tag carry the same version:

```bash
git commit -am "Set version 1.2.0"
git push origin main
```

Pushing only the tag (step 3) leaves `main` on the previous version.

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

### Optional: TestPyPI dry run

To verify the build and upload path without touching the real index, start
the release workflow by hand: **Actions → Release → Run workflow** on `main`.
It builds the package and uploads it to TestPyPI. TestPyPI does not accept a
version twice either, so this only works for a version that is not there yet.

```bash
pip install -i https://test.pypi.org/simple/ git-changelists
```

Worth doing after a long gap between releases or after changes to the
workflow; optional otherwise.

## 3. Tag

Create an annotated tag matching the new version (no `v` prefix), then push it:

```bash
git tag -a 1.2.0 -m "Release 1.2.0"
git push origin 1.2.0
```

The push starts the release workflow. It checks the version numbers, builds
the source distribution and wheel, and runs `twine check` on them. The upload
then waits for approval (step 4).

A tag is recoverable until the upload is approved. If the workflow fails or
you spot a mistake, reject the deployment (or let the workflow fail), delete
the tag locally (`git tag -d 1.2.0`) and on the remote
(`git push origin :refs/tags/1.2.0`), fix the problem, and re-tag.

## 4. Approve the upload to PyPI

Open the run under **[Actions → Release](https://github.com/BHFock/git-cl/actions/workflows/release.yml)**.
When the build has passed, the run shows **Review deployments**. Select `pypi`
and choose **Approve and deploy**. The upload takes about a minute.

> **Point of no return:** PyPI does not allow a version number to be reused or
> overwritten once uploaded. If a release is wrong after this step, you cannot
> re-push the same number — fix the problem and release the next version
> instead. For this reason, approve only when you are sure the release is
> final.

## 5. Verify the published package installs

This confirms the uploaded package is installable and starts cleanly. After a
short propagation delay, install it into a throwaway Conda environment:

```bash
conda create -n gitcl-test python=3.12 -y
conda activate gitcl-test
pip install --no-cache-dir git-changelists==<version>
git cl --version          # should print the version you just released
conda deactivate
conda env remove -n gitcl-test -y
```

The environment is isolated, so this tests a clean install rather than your
existing setup. Make sure you install inside the activated `gitcl-test`
environment, not your `base` environment.

## 6. Create the GitHub release

In the web UI: **[Releases](https://github.com/BHFock/git-cl/releases) → Draft a new release →** choose the existing `1.2.0`
tag → **Generate release notes**, then rewrite them before publishing. No file
uploads needed; PyPI is the download source.

Structure (see [1.4.0](https://github.com/BHFock/git-cl/releases/tag/1.4.0)):

- One sentence on what the release is about
- `### New: …` or `### Fixed`: what changed for users, not the commit title
- `### ⚠️ Behaviour change`: only if users or scripts must react
- `### Other changes`: docs, CI, small output tweaks
- `### Pull requests`: the generated list, with `#NN` instead of full URLs
- `**Full Changelog**` line as generated

Put `<name>` placeholders in backticks, or GitHub hides them as HTML.

Unlike the PyPI upload, a GitHub release is not final — you can edit or delete
it at any time.

## Quick reference

```bash
# 1. Bump version in setup.cfg, git-cl, CITATION.cff (all must match)
#    Also update date-released: in CITATION.cff
git commit -am "Set version 1.2.0" && git push origin main
# 2. Pre-release
git checkout main && git pull && git status
./tests/run_tests.py
# 3. Tag (starts the release workflow)
git tag -a 1.2.0 -m "Release 1.2.0"
git push origin 1.2.0
# 4. Approve the upload: Actions → Release → Review deployments → pypi
# 5. Verify in a throwaway Conda environment
conda create -n gitcl-test python=3.12 -y
conda activate gitcl-test
pip install git-changelists && git cl --version
conda deactivate
conda env remove -n gitcl-test -y
# 6. Create GitHub release in web UI (choose tag, Generate release notes, publish)
```
