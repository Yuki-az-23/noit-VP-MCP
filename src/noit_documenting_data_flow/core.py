"""Shared core for building and rendering diagram pieces."""

from __future__ import annotations

import re
from typing import Any

HUB_PATH_RE = re.compile(r'hub\["[^"]*<br/>([^"]*)"\]')
NODE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _label(text: str) -> str:
    """Escape text for a quoted Mermaid label."""
    return str(text).replace('"', "#quot;")


def validate_node(node: dict[str, Any], *, kind: str) -> None:
    """Validate a node dict against the expected diagram schema."""
    if not isinstance(node, dict):
        raise ValueError(f"Invalid {kind} node: expected mapping, got {type(node).__name__}")
    node_id = node.get("id")
    if not isinstance(node_id, str) or not NODE_ID_RE.match(node_id):
        raise ValueError(f"Invalid node id {node_id!r}: use letters, digits and _ only")
    if kind == "dependency" and node.get("type") not in ("dep", "extSvc"):
        raise ValueError(f"Invalid dependency type {node.get('type')!r}: use 'dep' or 'extSvc'")


def build_mermaid(
    title: str,
    function_path: str,
    inputs: list[dict[str, Any]] | None = None,
    dependencies: list[dict[str, Any]] | None = None,
    outputs: list[dict[str, Any]] | None = None,
) -> str:
    """Build the Mermaid graph for a STAR diagram piece."""
    inputs = inputs or []
    dependencies = dependencies or []
    outputs = outputs or []

    for node in inputs:
        validate_node(node, kind="input")
    for node in dependencies:
        validate_node(node, kind="dependency")
    for node in outputs:
        validate_node(node, kind="output")

    lines = ["graph LR", f'    hub["⚙️ {_label(title)}<br/>{_label(function_path)}"]:::hub']

    if inputs:
        lines.append('    subgraph In["📥 Inputs"]')
        for node in inputs:
            desc = f"<br/>{_label(node.get('description', ''))}" if node.get("description") else ""
            lines.append(f'        {node["id"]}["{_label(node["label"])}{desc}"]:::input')
        lines.append("    end")

    if dependencies:
        lines.append('    subgraph Deps["🤖 Dependencies"]')
        for node in dependencies:
            lines.append(f'        {node["id"]}["{_label(node["label"])}"]:::{node["type"]}')
        lines.append("    end")

    if outputs:
        lines.append('    subgraph Out["💾 Outputs"]')
        for node in outputs:
            desc = f"<br/>{_label(node.get('description', ''))}" if node.get("description") else ""
            lines.append(f'        {node["id"]}["{_label(node["label"])}{desc}"]:::output')
        lines.append("    end")

    for node in inputs:
        lines.append(f"    {node['id']} --> hub")
    for node in dependencies:
        if node["type"] == "extSvc":
            lines.append(f'    hub -->|"query"| {node["id"]}')
        else:
            lines.append(f'    hub <-->|"read/write"| {node["id"]}')
    for node in outputs:
        lines.append(f'    hub ==>|"result"| {node["id"]}')

    lines.extend(
        [
            "",
            "    classDef hub      fill:#4A148C,stroke:#CE93D8,color:#F3E5F9,stroke-width:3px",
            "    classDef input    fill:#37474F,stroke:#78909C,color:#CFD8DC,stroke-width:1px",
            "    classDef dep      fill:#0D47A1,stroke:#42A5F5,color:#BBDEFB,stroke-width:1px",
            "    classDef extSvc   fill:#E65100,stroke:#FFB74D,color:#FFF3E0,stroke-width:2px",
            "    classDef output   fill:#1B5E20,stroke:#66BB6A,color:#C8E6C9,stroke-width:2px",
        ]
    )
    return "\n".join(lines)


def render_piece(title: str, desc: str, mermaid: str) -> str:
    """Render a standard Markdown piece."""
    return f"""# {title}

{desc}

```mermaid
{mermaid}
```

---

*Rendered natively by MkDocs Material (Mermaid). This piece is the source of truth; the interactive
[Architecture Diagrams](../../architecture_diagrams.html) viewer is generated from it by
`noit-diagram-rollup build`.*
"""


def function_path_from_mermaid(mermaid: str) -> str:
    """Extract the source path encoded in the hub label."""
    match = HUB_PATH_RE.search(mermaid)
    return match.group(1) if match else ""
