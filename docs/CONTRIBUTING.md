# Contributing

Work is planned as GitHub issues grouped under one epic per phase; pick an open sub-issue or open
an issue first for anything larger than a small fix, so the approach can be agreed before code.

## Setup

```bash
git clone https://github.com/Yuki-az-23/noit-VP-MCP
cd noit-VP-MCP
pip install -e ".[dev]"
```

For the extension: `cd vscode-extension && npm ci`.

## Before you open a pull request

Run the same checks CI runs, so the pull request goes green on the first try:

```bash
ruff check . && ruff format --check . && mypy src && pytest
cd vscode-extension && npx tsc -p ./ --noEmit
```

Add or update a test for every behaviour change, and reference the issue in the PR (`Fixes #12`)
so it closes on merge. Architecture documentation lives in `docs/`; diagrams are STAR pieces made
with this tool.

## Releasing

Bump `version` in `pyproject.toml`, merge, then push a matching tag (`v1.2.0`). The release
workflow builds the package and the extension, attaches both to a GitHub release, publishes to
PyPI through trusted publishing, and to the VS Code marketplace when the `VSCE_PAT` secret is set.
