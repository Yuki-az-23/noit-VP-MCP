#!/usr/bin/env python3
"""
MCP Server for NOit Documenting Data Flow.

Provides tools for AI agents to create, update, and manage STAR diagram pieces.
Run with: noit-mcp-server (stdio) or noit-mcp-server --transport http --port 8765
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

from .generator import build_viewer, parse_piece, derive_id
from .templates import (
    DIAGRAM_TEMPLATE,
    MANIFEST_TEMPLATE,
    PAGES_TEMPLATE,
    VIEWER_TEMPLATE,
)


SERVER = Server("noit-documenting-data-flow")


def _get_diagrams_dir() -> Path:
    """Get the diagrams directory from cwd."""
    return Path.cwd() / "docs" / "architecture" / "diagrams"


def _get_manifest_path(diagrams_dir: Path) -> Path:
    return diagrams_dir / "rollup.manifest.yml"


def _load_manifest(diagrams_dir: Path) -> dict:
    manifest_path = _get_manifest_path(diagrams_dir)
    if not manifest_path.exists():
        return {"title": "Architecture Diagrams", "subtitle": "", "groups": [], "diagrams": []}
    import yaml
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))


def _save_manifest(diagrams_dir: Path, manifest: dict) -> None:
    manifest_path = _get_manifest_path(diagrams_dir)
    import yaml
    manifest_path.write_text(yaml.dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _update_pages(diagrams_dir: Path, new_file: str) -> None:
    pages_path = diagrams_dir / ".pages"
    lines = []
    if pages_path.exists():
        lines = [l.strip() for l in pages_path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("#")]
    if new_file not in lines:
        lines.append(new_file)
        pages_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@SERVER.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="create_diagram_piece",
            description="Create a new STAR diagram piece from template",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Slug for the piece (e.g., 'api-handler')"},
                    "title": {"type": "string", "description": "Human-readable title"},
                    "function_path": {"type": "string", "description": "Source file path (e.g., 'src/api/handler.py')"},
                    "group": {"type": "string", "enum": ["infra", "ops", "seq"], "description": "Group for viewer nav", "default": "ops"},
                    "inputs": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "label": {"type": "string"}, "description": {"type": "string"}}, "required": ["id", "label"]}, "description": "Input sources"},
                    "dependencies": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "label": {"type": "string"}, "type": {"type": "string", "enum": ["dep", "extSvc"]}}, "required": ["id", "label", "type"]}, "description": "Dependencies (services, APIs)"},
                    "outputs": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "label": {"type": "string"}, "description": {"type": "string"}}, "required": ["id", "label"]}, "description": "Outputs"},
                },
                "required": ["slug", "title", "function_path"],
            },
        ),
        Tool(
            name="update_diagram_piece",
            description="Update an existing diagram piece",
            inputSchema={
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "Filename (e.g., '01-api-handler.md')"},
                    "title": {"type": "string"},
                    "function_path": {"type": "string"},
                    "group": {"type": "string", "enum": ["infra", "ops", "seq"]},
                    "inputs": {"type": "array", "items": {"type": "object"}},
                    "dependencies": {"type": "array", "items": {"type": "object"}},
                    "outputs": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["file"],
            },
        ),
        Tool(
            name="list_diagram_pieces",
            description="List all diagram pieces with metadata",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_diagram_piece",
            description="Read a diagram piece's content",
            inputSchema={"type": "object", "properties": {"file": {"type": "string"}}, "required": ["file"]},
        ),
        Tool(
            name="build_viewer",
            description="Generate the interactive HTML viewer + overview",
            inputSchema={
                "type": "object",
                "properties": {
                    "write": {"type": "boolean", "default": False, "description": "Write to real paths (default: dry-run)"},
                },
            },
        ),
    ]


@SERVER.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
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

    return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")], isError=True)


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

    # Build mermaid from structured data
    mermaid_lines = ['graph LR', f'    hub["⚙️ {title}<br/>{function_path}"]:::hub']

    # Inputs
    if inputs:
        mermaid_lines.append('    subgraph In["📥 Inputs"]')
        for inp in inputs:
            desc = f'<br/>{inp["description"]}' if inp.get("description") else ""
            mermaid_lines.append(f'        {inp["id"]}["{inp["label"]}{desc}"]:::input')
        mermaid_lines.append('    end')

    # Dependencies
    if dependencies:
        mermaid_lines.append('    subgraph Deps["🤖 Dependencies"]')
        for dep in dependencies:
            cls = dep["type"]  # dep or extSvc
            mermaid_lines.append(f'        {dep["id"]}["{dep["label"]}"]:::{cls}')
        mermaid_lines.append('    end')

    # Outputs
    if outputs:
        mermaid_lines.append('    subgraph Out["💾 Outputs"]')
        for out in outputs:
            desc = f'<br/>{out["description"]}' if out.get("description") else ""
            mermaid_lines.append(f'        {out["id"]}["{out["label"]}{desc}"]:::output')
        mermaid_lines.append('    end')

    # Edges
    if inputs:
        for inp in inputs:
            mermaid_lines.append(f'    {inp["id"]} --> hub')
    if dependencies:
        for dep in dependencies:
            if dep["type"] == "extSvc":
                mermaid_lines.append(f'    hub -->|"query"| {dep["id"]}')
            else:
                mermaid_lines.append(f'    hub <-->|"read/write"| {dep["id"]}')
    if outputs:
        for out in outputs:
            mermaid_lines.append(f'    hub ==>|"result"| {out["id"]}')

    # ClassDefs
    mermaid_lines.extend([
        '',
        '    classDef hub      fill:#4A148C,stroke:#CE93D8,color:#F3E5F9,stroke-width:3px',
        '    classDef input    fill:#37474F,stroke:#78909C,color:#CFD8DC,stroke-width:1px',
        '    classDef dep      fill:#0D47A1,stroke:#42A5F5,color:#BBDEFB,stroke-width:1px',
        '    classDef extSvc   fill:#E65100,stroke:#FFB74D,color:#FFF3E0,stroke-width:2px',
        '    classDef output   fill:#1B5E20,stroke:#66BB6A,color:#C8E6C9,stroke-width:2px',
    ])

    mermaid = "\n".join(mermaid_lines)

    # Build piece content
    content = f"""# {title}

STAR diagram for {title} — generated by NOit Documenting Data Flow.

```mermaid
{mermaid}
```

---

*Rendered natively by MkDocs Material (Mermaid). This piece is the source of truth; the interactive
[Architecture Diagrams](../../architecture_diagrams.html) viewer is generated from it by
`noit-diagram-rollup build`.*
"""

    # Write piece
    piece_path = diagrams_dir / filename
    piece_path.write_text(content, encoding="utf-8")

    # Update manifest
    manifest = _load_manifest(diagrams_dir)
    manifest["diagrams"].append({"file": filename, "group": group})
    _save_manifest(diagrams_dir, manifest)

    # Update .pages
    _update_pages(diagrams_dir, filename)

    return CallToolResult(content=[TextContent(type="text", text=f"✅ Created {filename} in group '{group}'\n   Path: {piece_path}\n   Added to manifest and .pages")])


async def _update_piece(diagrams_dir: Path, args: dict) -> CallToolResult:
    filename = args["file"]
    piece_path = diagrams_dir / filename

    if not piece_path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"❌ File not found: {filename}")], isError=True)

    # Read existing to preserve structure
    existing = parse_piece(piece_path)

    # Build new mermaid (simplified - would need full rebuild logic)
    # For now, just return current content
    return CallToolResult(content=[TextContent(type="text", text=f"📄 Current content of {filename}:\n\n{piece_path.read_text(encoding='utf-8')}")])


async def _list_pieces(diagrams_dir: Path) -> CallToolResult:
    manifest = _load_manifest(diagrams_dir)

    if not manifest.get("diagrams"):
        return CallToolResult(content=[TextContent(type="text", text="📭 No diagram pieces found. Create one with create_diagram_piece.")])

    lines = ["📋 Diagram Pieces:\n"]
    for i, entry in enumerate(manifest["diagrams"], 1):
        path = diagrams_dir / entry["file"]
        status = "✅" if path.exists() else "❌ MISSING"
        piece = parse_piece(path) if path.exists() else {"title": entry["file"], "desc": ""}
        lines.append(f"  {i}. {entry['file']} ({entry['group']}) — {piece['title']} {status}")

    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


async def _get_piece(diagrams_dir: Path, filename: str) -> CallToolResult:
    path = diagrams_dir / filename
    if not path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"❌ File not found: {filename}")], isError=True)

    content = path.read_text(encoding="utf-8")
    return CallToolResult(content=[TextContent(type="text", text=content)])


async def _build_viewer(diagrams_dir: Path, write: bool) -> CallToolResult:
    manifest = _load_manifest(diagrams_dir)

    if not manifest.get("diagrams"):
        return CallToolResult(content=[TextContent(type="text", text="❌ No diagrams in manifest. Add pieces first.")], isError=True)

    try:
        html_out, overview = build_viewer(manifest, diagrams_dir, VIEWER_TEMPLATE)
    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"❌ Build failed: {e}")], isError=True)

    if write:
        out_html = Path.cwd() / "docs" / "architecture_diagrams.html"
        out_overview = diagrams_dir / "OVERVIEW.generated.md"
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text(html_out, encoding="utf-8")
        out_overview.write_text(overview, encoding="utf-8")
        return CallToolResult(content=[TextContent(type="text", text=f"✅ Built viewer + overview\n   HTML: {out_html}\n   Overview: {out_overview}")])
    else:
        import tempfile
        scratch = Path(tempfile.mkdtemp(prefix="noit_diagram_"))
        out_html = scratch / "architecture_diagrams.generated.html"
        out_overview = scratch / "OVERVIEW.generated.md"
        out_html.write_text(html_out, encoding="utf-8")
        out_overview.write_text(overview, encoding="utf-8")
        return CallToolResult(content=[TextContent(type="text", text=f"🔍 DRY-RUN: {len(manifest['diagrams'])} pieces\n   HTML: {out_html}\n   Overview: {out_overview}\n\nRe-run with write=true to emit to real paths.")])


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
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as (read, write):
                await SERVER.run(read, write, SERVER.create_initialization_options())

        app = Starlette(routes=[
            Route("/sse", handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ])
        uvicorn.run(app, host=args.host, port=args.port)

    return 0


if __name__ == "__main__":
    sys.exit(main())