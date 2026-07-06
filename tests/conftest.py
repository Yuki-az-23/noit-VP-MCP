"""Shared helpers for building throwaway diagram projects in tmp_path."""
from __future__ import annotations

from pathlib import Path

import yaml

PIECE_TMPL = '''# {title}

STAR piece for {title}.

```mermaid
graph LR
    hub["⚙️ {title}<br/>{src}"]:::hub
    in1["📥 Input"]:::input
    in1 --> hub
```
'''


def make_piece(diagrams_dir: Path, name: str, src: str, title: str = "Handler") -> Path:
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    path = diagrams_dir / name
    path.write_text(PIECE_TMPL.format(title=title, src=src), encoding="utf-8")
    return path


def make_manifest(diagrams_dir: Path, files: list[str]) -> dict:
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "title": "Test Diagrams",
        "groups": [{"id": "ops", "label": "Operations", "badge": "ops"}],
        "diagrams": [{"file": f, "group": "ops"} for f in files],
    }
    (diagrams_dir / "rollup.manifest.yml").write_text(
        yaml.dump(manifest, sort_keys=False), encoding="utf-8"
    )
    return manifest