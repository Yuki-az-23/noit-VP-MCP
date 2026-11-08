"""Project settings, read from an optional noit.yml at the project root."""

from __future__ import annotations

from pathlib import Path

import yaml

CONFIG_FILE = "noit.yml"

DEFAULTS = {
    "diagrams_dir": "docs/architecture/diagrams",
    "out_html": "docs/architecture_diagrams.generated.html",
    "out_overview": "docs/architecture/diagrams/OVERVIEW.generated.md",
}


def load_config(root: Path) -> dict[str, str]:
    """Return the defaults, overridden by any keys set in <root>/noit.yml."""
    path = root / CONFIG_FILE
    if not path.exists():
        return dict(DEFAULTS)

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"{CONFIG_FILE} is not valid YAML: {e}") from e
    if not isinstance(data, dict):
        raise ValueError(f"{CONFIG_FILE} must be a mapping of settings")  # noqa: TRY004 — callers report ValueError as a config error

    unknown = sorted(set(data) - set(DEFAULTS))
    if unknown:
        raise ValueError(
            f"{CONFIG_FILE}: unknown setting(s) {', '.join(unknown)}; "
            f"allowed: {', '.join(DEFAULTS)}"
        )
    for key, value in data.items():
        if not isinstance(value, str) or not value:
            raise ValueError(f"{CONFIG_FILE}: '{key}' must be a non-empty path string")

    return {**DEFAULTS, **data}
