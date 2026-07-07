from __future__ import annotations

import asyncio
import json
import os
import time

from conftest import make_manifest, make_piece

from noit_documenting_data_flow.mcp_server import _audit, list_tools


def test_audit_tool_is_listed():
    names = [t.name for t in asyncio.run(list_tools())]
    assert "audit_diagrams" in names


def test_audit_tool_returns_json_report(tmp_path, monkeypatch):
    diagrams = tmp_path / "docs" / "architecture" / "diagrams"
    src = tmp_path / "src" / "handler.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(): pass\n")
    t = time.time() - 100
    os.utime(src, (t, t))
    make_piece(diagrams, "01-handler.md", "src/handler.py")
    make_manifest(diagrams, ["01-handler.md"])
    monkeypatch.chdir(tmp_path)

    result = asyncio.run(_audit(diagrams))
    report = json.loads(result.content[0].text)
    assert report["score"] == 100
    assert report["total_pieces"] == 1
    assert report["findings"] == []