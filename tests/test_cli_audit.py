from __future__ import annotations

import argparse
import json
import os
import time

from conftest import make_manifest, make_piece

from noit_documenting_data_flow.cli import cmd_audit


def _args(**over):
    base = {
        "diagrams_dir": "docs/architecture/diagrams",
        "manifest": None,
        "json": False,
        "fail_under": 0,
    }
    base.update(over)
    return argparse.Namespace(**base)


def _setup_clean_project(tmp_path, monkeypatch):
    diagrams = tmp_path / "docs" / "architecture" / "diagrams"
    src = tmp_path / "src" / "handler.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f(): pass\n")
    t = time.time() - 100
    os.utime(src, (t, t))  # source older than the piece
    make_piece(diagrams, "01-handler.md", "src/handler.py")
    make_manifest(diagrams, ["01-handler.md"])
    monkeypatch.chdir(tmp_path)


def test_cmd_audit_human_output(tmp_path, monkeypatch, capsys):
    _setup_clean_project(tmp_path, monkeypatch)
    assert cmd_audit(_args()) == 0
    out = capsys.readouterr().out
    assert "Docs Sync Score: 100/100" in out
    assert "IN SYNC" in out


def test_cmd_audit_json_output(tmp_path, monkeypatch, capsys):
    _setup_clean_project(tmp_path, monkeypatch)
    assert cmd_audit(_args(json=True)) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["score"] == 100
    assert report["findings"] == []


def test_cmd_audit_missing_manifest_errors(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cmd_audit(_args()) == 1
    assert "[ERROR]" in capsys.readouterr().out


def test_cmd_audit_fail_under_gates(tmp_path, monkeypatch, capsys):
    diagrams = tmp_path / "docs" / "architecture" / "diagrams"
    make_piece(diagrams, "01-gone.md", "src/deleted.py")  # missing_source → 85
    make_manifest(diagrams, ["01-gone.md"])
    monkeypatch.chdir(tmp_path)
    assert cmd_audit(_args(fail_under=90)) == 1
    out = capsys.readouterr().out
    assert "[MISSING_SOURCE]" in out
    assert "[FAIL]" in out