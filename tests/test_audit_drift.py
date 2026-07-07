from __future__ import annotations

import os
import subprocess
import time

from conftest import make_manifest, make_piece

from noit_documenting_data_flow.audit import audit_diagrams, last_change_ts


def _make_src(tmp_path, rel="src/handler.py", age_seconds=100):
    src = tmp_path / rel
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("def f(): pass\n")
    t = time.time() - age_seconds
    os.utime(src, (t, t))
    return src


def test_last_change_ts_falls_back_to_mtime(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("x = 1")
    os.utime(f, (1000000, 1000000))
    assert last_change_ts(f, tmp_path) == 1000000


def test_last_change_ts_missing_file_is_none(tmp_path):
    assert last_change_ts(tmp_path / "ghost.py", tmp_path) is None


def test_last_change_ts_uses_git_commit_time(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    f = tmp_path / "a.py"
    f.write_text("x = 1")
    subprocess.run(["git", "add", "a.py"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "add"],
        cwd=tmp_path, check=True,
    )
    os.utime(f, (1000000, 1000000))  # mtime lies; git commit time should win
    ts = last_change_ts(f, tmp_path)
    assert ts is not None and ts > 1000000


def test_audit_clean_project_scores_100(tmp_path):
    diagrams = tmp_path / "docs" / "architecture" / "diagrams"
    _make_src(tmp_path)  # source older than the piece we write now
    make_piece(diagrams, "01-handler.md", "src/handler.py")
    manifest = make_manifest(diagrams, ["01-handler.md"])
    report = audit_diagrams(manifest, diagrams, tmp_path)
    assert report.findings == []
    assert report.total_pieces == 1
    assert report.score == 100


def test_audit_flags_missing_source(tmp_path):
    diagrams = tmp_path / "docs" / "architecture" / "diagrams"
    make_piece(diagrams, "01-gone.md", "src/deleted.py")
    manifest = make_manifest(diagrams, ["01-gone.md"])
    report = audit_diagrams(manifest, diagrams, tmp_path)
    assert [f.kind for f in report.findings] == ["missing_source"]
    assert report.score == 85


def test_audit_flags_stale_piece(tmp_path):
    diagrams = tmp_path / "docs" / "architecture" / "diagrams"
    src = _make_src(tmp_path, age_seconds=0)          # source touched "now"
    piece = make_piece(diagrams, "01-handler.md", "src/handler.py")
    t = time.time() - 1000
    os.utime(piece, (t, t))                            # piece is older
    manifest = make_manifest(diagrams, ["01-handler.md"])
    report = audit_diagrams(manifest, diagrams, tmp_path)
    assert [f.kind for f in report.findings] == ["stale"]
    assert "src/handler.py" in report.findings[0].detail


def test_audit_flags_manifest_entry_without_file(tmp_path):
    diagrams = tmp_path / "docs" / "architecture" / "diagrams"
    manifest = make_manifest(diagrams, ["01-phantom.md"])
    report = audit_diagrams(manifest, diagrams, tmp_path)
    assert [f.kind for f in report.findings] == ["missing_file"]


def test_audit_flags_unregistered_piece_but_ignores_template(tmp_path):
    diagrams = tmp_path / "docs" / "architecture" / "diagrams"
    _make_src(tmp_path)
    make_piece(diagrams, "01-handler.md", "src/handler.py")
    make_piece(diagrams, "02-orphan.md", "src/handler.py")
    make_piece(diagrams, "00-template.md", "src/handler.py")  # never flagged
    manifest = make_manifest(diagrams, ["01-handler.md"])
    report = audit_diagrams(manifest, diagrams, tmp_path)
    assert [f.kind for f in report.findings] == ["unregistered"]
    assert report.findings[0].piece == "02-orphan.md"


def test_audit_flags_piece_without_source_ref(tmp_path):
    diagrams = tmp_path / "docs" / "architecture" / "diagrams"
    diagrams.mkdir(parents=True)
    (diagrams / "01-vague.md").write_text(
        '# Vague\n\nNo path here.\n\n```mermaid\ngraph LR\n    hub["⚙️ f()"]:::hub\n```\n',
        encoding="utf-8",
    )
    manifest = make_manifest(diagrams, ["01-vague.md"])
    report = audit_diagrams(manifest, diagrams, tmp_path)
    assert [f.kind for f in report.findings] == ["no_source_ref"]