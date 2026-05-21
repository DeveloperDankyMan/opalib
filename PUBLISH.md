Publishing opalib to PyPI

Overview

Don't store PyPI API tokens in the repository. Use GitHub Actions secrets or local environment variables when uploading.

1) Revoke exposed token on PyPI (important)
- Go to https://pypi.org -> Account -> API tokens
- Revoke the previously exposed token (the one that starts with `pypi-...`) immediately.
- Create a new token (scoped to the project or global) and copy its value.

2) Add token to GitHub Secrets (recommended)
- UI: Repository -> Settings -> Secrets and variables -> Actions -> New repository secret
  - Name: `PYPI_API_TOKEN`
  - Value: the `pypi-...` token value

- Or using `gh` CLI (run locally):

  gh auth login
  gh secret set PYPI_API_TOKEN --body 'pypi-...'

3) Trigger the publish workflow
- Create and push a tag (the workflow triggers on tags matching `v*`):

  git tag v0.4.0
  git push origin v0.4.0

- Or run the workflow manually in GitHub Actions: Actions -> Publish Python package -> Run workflow

4) Local publish (alternative)
- Build and upload locally without committing credentials:

  python -m pip install --upgrade build twine
  python -m build
  TWINE_USERNAME=__token__ TWINE_PASSWORD='pypi-...' python -m twine upload dist/*

5) If the token was committed to git history
- Revoke it immediately on PyPI (step 1).
- If you must scrub history, use `git filter-repo` or BFG — but revoking the token is the critical action.

6) Clean-up and best practices
- Remove `.pypirc` from the repo (already done).
- Never paste tokens into issues/PRs or public chat.
- Prefer repository-scoped API tokens for least privilege.

If you want, I can:
- Add a GitHub Actions `release` workflow that creates a tag and runs the publish job (requires `repo` write access).
- Provide a small script to build and perform a local `twine` upload (keeps token out of git).
