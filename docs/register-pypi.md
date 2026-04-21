# Publishing meshcore-py-node to PyPI

---

## Prerequisites

```bash
pip install build twine
```

Accounts needed:
- **https://pypi.org** — production registry
- **https://test.pypi.org** — optional, for test uploads

---

## Before you publish

### 1. Fix the package discovery config in `pyproject.toml`

The current `where` setting points inside the package folder rather than the project root. Update it:

```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["meshcore_py_node*"]
```

### 2. Update the project URLs

Replace the placeholder `YOUR_GITHUB` values in `pyproject.toml`:

```toml
[project.urls]
Homepage = "https://github.com/Lebovitz-Net/meshcore_py_node"
Documentation = "https://github.com/Lebovitz-Net/meshcore_py_node/blob/main/README.md"
Source = "https://github.com/Lebovitz-Net/meshcore_py_node"
Issues = "https://github.com/Lebovitz-Net/meshcore_py_node/issues"
```

### 3. Bump the version

Edit `version` in `pyproject.toml` before each release:

```toml
[project]
version = "0.1.0"
```

---

## Build the distribution

```bash
python -m build
```

This produces two artifacts in `dist/`:
- `meshcore_py_node-0.1.0.tar.gz` — source distribution
- `meshcore_py_node-0.1.0-py3-none-any.whl` — wheel

---

## Test on TestPyPI (recommended before first release)

```bash
twine upload --repository testpypi dist/*
```

Install and verify from TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ meshcore-py-node
```

---

## Upload to PyPI (production)

```bash
twine upload dist/*
```

Twine will prompt for credentials. Use an API token (recommended over password):

- Username: `__token__`
- Password: your API token from https://pypi.org/manage/account/token/

---

## Automate credentials with `.pypirc`

Create `~/.pypirc` to avoid entering credentials on every upload:

```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

Keep this file out of version control — it contains secrets.

---

## After publishing

Users can install with:

```bash
# Core library only
pip install meshcore-py-node

# With SX1262 hardware support
pip install meshcore-py-node[sx1262]
```

---

## Release checklist

- [ ] Update `version` in `pyproject.toml`
- [ ] Update `CHANGELOG.md` — move `[Unreleased]` to the new version + date
- [ ] Commit and tag: `git tag v0.1.0 && git push --tags`
- [ ] `python -m build`
- [ ] `twine upload dist/*`
