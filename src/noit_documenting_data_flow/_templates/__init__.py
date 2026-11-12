"""Template asset files for the documenting-data-flow package."""

from __future__ import annotations

from importlib.resources import files

_TEMPLATE_ROOT = files("noit_documenting_data_flow._templates")


def _read_template(name: str) -> str:
    return (_TEMPLATE_ROOT / name).read_text(encoding="utf-8")


DIAGRAM_TEMPLATE = _read_template("diagram_template.md")
MANIFEST_TEMPLATE = _read_template("manifest_template.yml")
PAGES_TEMPLATE = _read_template("pages_template.txt")
MERMAID_STYLE = _read_template("mermaid_style.md")
MKDOCS_SNIPPET = _read_template("mkdocs_snippet.yml")
VIEWER_TEMPLATE = _read_template("viewer_template.html")
MERMAID_INTERACTIVE_JS = _read_template("mermaid_interactive.js")
MERMAID_INTERACTIVE_CSS = _read_template("mermaid_interactive.css")
