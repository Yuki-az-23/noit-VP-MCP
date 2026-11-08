#!/usr/bin/env python3
"""
MCP Server for NOit Documenting Data Flow.

Provides tools for AI agents to create, update, and manage STAR diagram pieces.
Run with: noit-mcp-server (stdio) or noit-mcp-server --transport http --port 8765
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)

from .config import load_config
from .generator import build_viewer, parse_piece
from .templates import VIEWER_TEMPLATE

SERVER = Server("noit-documenting-data-flow")


def _get_diagrams_dir() -> Path:
    """Get the diagrams directory from noit.yml (or the default) under cwd."""
    return Path.cwd() / load_config(Path.cwd())["diagrams_dir"]


def _get_manifest_path(diagrams_dir: Path) -> Path:
    return diagrams_dir / "rollup.manifest.yml"


def _load_manifest(diagrams_dir: Path) -> dict:
    manifest_path = _get_manifest_path(diagrams_dir)
    if not manifest_path.exists():
        return {"title": "Architecture Diagrams", "subtitle": "", "groups": [], "diagrams": []}
    import yaml

    manifest: dict = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    manifest["diagrams"] = manifest.get("diagrams") or []
    return manifest


def _save_manifest(diagrams_dir: Path, manifest: dict) -> None:
    manifest_path = _get_manifest_path(diagrams_dir)
    import yaml

    manifest_path.write_text(
        yaml.dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


def _update_pages(diagrams_dir: Path, new_file: str) -> None:
    pages_path = diagrams_dir / ".pages"
    lines = []
    if pages_path.exists():
        lines = [
            line.strip()
            for line in pages_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    if new_file not in lines:
        lines.append(new_file)
        pages_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


HUB_PATH_RE = re.compile(r'hub\["[^"]*<br/>([^"]*)"\]')
NODE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _safe_piece_path(diagrams_dir: Path, filename: str) -> Path:
    """Resolve a piece filename, refusing anything outside the diagrams folder."""
    path = (diagrams_dir / filename).resolve()
    if path.parent != diagrams_dir.resolve() or path.suffix != ".md":
        raise ValueError(f"Not a diagram piece in {diagrams_dir.name}/: {filename}")
    return path


def _function_path(mermaid: str) -> str:
    m = HUB_PATH_RE.search(mermaid)
    return m.group(1) if m else ""


def _label(text: str) -> str:
    """Escape text for a quoted Mermaid label."""
    return text.replace('"', "#quot;")


def _build_mermaid(
    title: str, function_path: str, inputs: list, dependencies: list, outputs: list
) -> str:
    for node in [*inputs, *dependencies, *outputs]:
        if not NODE_ID_RE.match(node["id"]):
            raise ValueError(f"Invalid node id {node['id']!r}: use letters, digits and _ only")
        if node in dependencies and node.get("type") not in ("dep", "extSvc"):
            raise ValueError(f"Invalid dependency type {node.get('type')!r}: use 'dep' or 'extSvc'")

    mermaid_lines = ["graph LR", f'    hub["⚙️ {_label(title)}<br/>{_label(function_path)}"]:::hub']

    # Inputs
    if inputs:
        mermaid_lines.append('    subgraph In["📥 Inputs"]')
        for inp in inputs:
            desc = f"<br/>{_label(inp['description'])}" if inp.get("description") else ""
            mermaid_lines.append(f'        {inp["id"]}["{_label(inp["label"])}{desc}"]:::input')
        mermaid_lines.append("    end")

    # Dependencies
    if dependencies:
        mermaid_lines.append('    subgraph Deps["🤖 Dependencies"]')
        for dep in dependencies:
            cls = dep["type"]  # dep or extSvc
            mermaid_lines.append(f'        {dep["id"]}["{_label(dep["label"])}"]:::{cls}')
        mermaid_lines.append("    end")

    # Outputs
    if outputs:
        mermaid_lines.append('    subgraph Out["💾 Outputs"]')
        for out in outputs:
            desc = f"<br/>{_label(out['description'])}" if out.get("description") else ""
            mermaid_lines.append(f'        {out["id"]}["{_label(out["label"])}{desc}"]:::output')
        mermaid_lines.append("    end")

    # Edges
    for inp in inputs:
        mermaid_lines.append(f"    {inp['id']} --> hub")
    for dep in dependencies:
        if dep["type"] == "extSvc":
            mermaid_lines.append(f'    hub -->|"query"| {dep["id"]}')
        else:
            mermaid_lines.append(f'    hub <-->|"read/write"| {dep["id"]}')
    for out in outputs:
        mermaid_lines.append(f'    hub ==>|"result"| {out["id"]}')

    # ClassDefs
    mermaid_lines.extend(
        [
            "",
            "    classDef hub      fill:#4A148C,stroke:#CE93D8,color:#F3E5F9,stroke-width:3px",
            "    classDef input    fill:#37474F,stroke:#78909C,color:#CFD8DC,stroke-width:1px",
            "    classDef dep      fill:#0D47A1,stroke:#42A5F5,color:#BBDEFB,stroke-width:1px",
            "    classDef extSvc   fill:#E65100,stroke:#FFB74D,color:#FFF3E0,stroke-width:2px",
            "    classDef output   fill:#1B5E20,stroke:#66BB6A,color:#C8E6C9,stroke-width:2px",
        ]
    )
    return "\n".join(mermaid_lines)


def _render_piece(title: str, desc: str, mermaid: str) -> str:
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


def _error(text: str) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=f"❌ {text}")], isError=True)


@SERVER.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="create_diagram_piece",
            description="Create a new STAR diagram piece from template",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "Slug for the piece (e.g., 'api-handler')",
                    },
                    "title": {"type": "string", "description": "Human-readable title"},
                    "function_path": {
                        "type": "string",
                        "description": "Source file path (e.g., 'src/api/handler.py')",
                    },
                    "group": {
                        "type": "string",
                        "enum": ["infra", "ops", "seq"],
                        "description": "Group for viewer nav",
                        "default": "ops",
                    },
                    "inputs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "label": {"type": "string"},
                                "description": {"type": "string"},
                            },
                            "required": ["id", "label"],
                        },
                        "description": "Input sources",
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "label": {"type": "string"},
                                "type": {"type": "string", "enum": ["dep", "extSvc"]},
                            },
                            "required": ["id", "label", "type"],
                        },
                        "description": "Dependencies (services, APIs)",
                    },
                    "outputs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "label": {"type": "string"},
                                "description": {"type": "string"},
                            },
                            "required": ["id", "label"],
                        },
                        "description": "Outputs",
                    },
                },
                "required": ["slug", "title", "function_path"],
            },
        ),
        Tool(
            name="update_diagram_piece",
            description=(
                "Update an existing diagram piece. title/function_path/group are changed in place. "
                "If any of inputs/dependencies/outputs is given, the diagram is rebuilt from the "
                "given lists, so pass all spokes the piece should keep."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "description": "Filename (e.g., '01-api-handler.md')",
                    },
                    "title": {"type": "string"},
                    "function_path": {"type": "string"},
                    "group": {"type": "string", "enum": ["infra", "ops", "seq"]},
                    "inputs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "label": {"type": "string"},
                                "description": {"type": "string"},
                            },
                            "required": ["id", "label"],
                        },
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "label": {"type": "string"},
                                "type": {"type": "string", "enum": ["dep", "extSvc"]},
                            },
                            "required": ["id", "label", "type"],
                        },
                    },
                    "outputs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "label": {"type": "string"},
                                "description": {"type": "string"},
                            },
                            "required": ["id", "label"],
                        },
                    },
                },
                "required": ["file"],
            },
        ),
        Tool(
            name="list_diagram_pieces",
            description=(
                "List all diagram pieces as a JSON array of "
                "{file, slug, title, function_path, group, file_path, exists}"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_diagram_piece",
            description="Read a diagram piece's content",
            inputSchema={
                "type": "object",
                "properties": {"file": {"type": "string"}},
                "required": ["file"],
            },
        ),
        Tool(
            name="build_viewer",
            description="Generate the interactive HTML viewer + overview",
            inputSchema={
                "type": "object",
                "properties": {
                    "write": {
                        "type": "boolean",
                        "default": False,
                        "description": "Write the *.generated.* files next to the live ones (default: dry-run to a temp dir)",
                    },
                },
            },
        ),
    ]


@SERVER.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    try:
        diagrams_dir = _get_diagrams_dir()
        diagrams_dir.mkdir(parents=True, exist_ok=True)

        if name == "create_diagram_piece":
            return await _create_piece(diagrams_dir, arguments)

        if name == "update_diagram_piece":
            return await _update_piece(diagrams_dir, arguments)

        if name == "list_diagram_pieces":
            return await _list_pieces(diagrams_dir)

        if name == "get_diagram_piece":
            return await _get_piece(diagrams_dir, arguments["file"])

        if name == "build_viewer":
            return await _build_viewer(diagrams_dir, arguments.get("write", False))
    except ValueError as e:
        return _error(str(e))
    except KeyError as e:
        return _error(f"Missing required field {e}")

    return _error(f"Unknown tool: {name}")


async def _create_piece(diagrams_dir: Path, args: dict) -> CallToolResult:
    slug = args["slug"]
    title = args["title"]
    function_path = args["function_path"]
    group = args.get("group", "ops")
    inputs = args.get("inputs", [])
    dependencies = args.get("dependencies", [])
    outputs = args.get("outputs", [])

    # Determine next numeric prefix
    existing = list(diagrams_dir.glob("[0-9][0-9]-*.md"))
    nums = [int(f.stem[:2]) for f in existing if f.stem[:2].isdigit()]
    next_num = max(nums, default=0) + 1
    filename = f"{next_num:02d}-{slug}.md"

    mermaid = _build_mermaid(title, function_path, inputs, dependencies, outputs)
    content = _render_piece(
        title, f"STAR diagram for {title} — generated by NOit Documenting Data Flow.", mermaid
    )

    # Write piece
    piece_path = diagrams_dir / filename
    piece_path.write_text(content, encoding="utf-8")

    # Update manifest
    manifest = _load_manifest(diagrams_dir)
    manifest["diagrams"].append({"file": filename, "group": group})
    _save_manifest(diagrams_dir, manifest)

    # Update .pages
    _update_pages(diagrams_dir, filename)

    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"✅ Created {filename} in group '{group}'\n   Path: {piece_path}\n   Added to manifest and .pages",
            )
        ]
    )


async def _update_piece(diagrams_dir: Path, args: dict) -> CallToolResult:
    filename = args["file"]
    piece_path = _safe_piece_path(diagrams_dir, filename)

    if not piece_path.exists():
        return _error(f"File not found: {filename}")

    existing = parse_piece(piece_path)
    old_function_path = _function_path(existing["mermaid"])
    title = args.get("title", existing["title"])
    function_path = args.get("function_path", old_function_path)

    text = piece_path.read_text(encoding="utf-8")
    if any(k in args for k in ("inputs", "dependencies", "outputs")):
        mermaid = _build_mermaid(
            title,
            function_path,
            args.get("inputs", []),
            args.get("dependencies", []),
            args.get("outputs", []),
        )
    else:
        mermaid = existing["mermaid"]
        if old_function_path:
            mermaid = HUB_PATH_RE.sub(
                lambda _: f'hub["⚙️ {_label(title)}<br/>{_label(function_path)}"]', mermaid, count=1
            )
    text = text.replace(existing["mermaid"], mermaid, 1)
    text = re.sub(r"^# .*$", lambda _: f"# {title}", text, count=1, flags=re.MULTILINE)
    piece_path.write_text(text, encoding="utf-8")

    changes = ["content"]
    if "group" in args:
        manifest = _load_manifest(diagrams_dir)
        for entry in manifest["diagrams"]:
            if entry["file"] == piece_path.name:
                entry["group"] = args["group"]
                break
        else:
            manifest["diagrams"].append({"file": piece_path.name, "group": args["group"]})
        _save_manifest(diagrams_dir, manifest)
        changes.append(f"group '{args['group']}'")

    return CallToolResult(
        content=[
            TextContent(type="text", text=f"✅ Updated {piece_path.name}: {', '.join(changes)}")
        ]
    )


async def _list_pieces(diagrams_dir: Path) -> CallToolResult:
    manifest = _load_manifest(diagrams_dir)

    pieces = []
    for entry in manifest.get("diagrams") or []:
        path = diagrams_dir / entry["file"]
        exists = path.exists()
        piece = parse_piece(path) if exists else {"title": entry["file"], "mermaid": ""}
        pieces.append(
            {
                "file": entry["file"],
                "slug": re.sub(r"^\d+-", "", path.stem),
                "title": piece["title"],
                "function_path": _function_path(piece["mermaid"]),
                "group": entry["group"],
                "file_path": path.relative_to(Path.cwd()).as_posix(),
                "exists": exists,
            }
        )

    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(pieces, ensure_ascii=False, indent=2))]
    )


async def _get_piece(diagrams_dir: Path, filename: str) -> CallToolResult:
    path = _safe_piece_path(diagrams_dir, filename)
    if not path.exists():
        return _error(f"File not found: {filename}")

    content = path.read_text(encoding="utf-8")
    return CallToolResult(content=[TextContent(type="text", text=content)])


async def _build_viewer(diagrams_dir: Path, write: bool) -> CallToolResult:
    manifest = _load_manifest(diagrams_dir)

    if not manifest.get("diagrams"):
        return CallToolResult(
            content=[
                TextContent(type="text", text="❌ No diagrams in manifest. Add pieces first.")
            ],
            isError=True,
        )

    try:
        html_out, overview = build_viewer(manifest, diagrams_dir, VIEWER_TEMPLATE)
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"❌ Build failed: {e}")], isError=True
        )

    if write:
        config = load_config(Path.cwd())
        out_html = Path.cwd() / config["out_html"]
        out_overview = Path.cwd() / config["out_overview"]
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_overview.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text(html_out, encoding="utf-8")
        out_overview.write_text(overview, encoding="utf-8")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=(
                        f"✅ Built viewer + overview\n   HTML: {out_html}\n   Overview: {out_overview}\n\n"
                        "Review, then replace the live viewer with: "
                        "noit-diagram-rollup build --write --out-html docs/architecture_diagrams.html"
                    ),
                )
            ]
        )
    else:
        import tempfile

        scratch = Path(tempfile.mkdtemp(prefix="noit_diagram_"))
        out_html = scratch / "architecture_diagrams.generated.html"
        out_overview = scratch / "OVERVIEW.generated.md"
        out_html.write_text(html_out, encoding="utf-8")
        out_overview.write_text(overview, encoding="utf-8")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"🔍 DRY-RUN: {len(manifest['diagrams'])} pieces\n   HTML: {out_html}\n   Overview: {out_overview}\n\nRe-run with write=true to emit to real paths.",
                )
            ]
        )


TOKEN_ENV = "NOIT_MCP_TOKEN"


def create_http_app(token: str) -> Any:
    """Streamable HTTP app at /mcp that rejects requests without the bearer token."""
    import contextlib
    import hmac

    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    manager = StreamableHTTPSessionManager(app=SERVER)
    expected = f"Bearer {token}".encode()

    class AuthorizedMcp:
        async def __call__(self, scope, receive, send):
            headers = dict(scope.get("headers") or [])
            if not hmac.compare_digest(headers.get(b"authorization", b""), expected):
                response = JSONResponse({"error": "unauthorized"}, status_code=401)
                await response(scope, receive, send)
                return
            await manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(_app):
        async with manager.run():
            yield

    return Starlette(
        routes=[Route("/mcp", endpoint=AuthorizedMcp(), methods=["GET", "POST", "DELETE"])],
        lifespan=lifespan,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="NOit Documenting Data Flow MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    if args.transport == "stdio":
        import asyncio

        from mcp.server.stdio import stdio_server as stdio_server_cm

        async def run_stdio():
            async with stdio_server_cm() as (read, write):
                await SERVER.run(read, write, SERVER.create_initialization_options())

        asyncio.run(run_stdio())
    else:
        token = os.environ.get(TOKEN_ENV)
        if not token:
            print(
                f"HTTP transport requires a bearer token: set {TOKEN_ENV} and send "
                f"'Authorization: Bearer <token>' from the client.",
                file=sys.stderr,
            )
            return 2
        import uvicorn

        uvicorn.run(create_http_app(token), host=args.host, port=args.port)

    return 0


if __name__ == "__main__":
    sys.exit(main())
