from __future__ import annotations

from noit_documenting_data_flow.audit import (
    AuditReport,
    Finding,
    compute_score,
    extract_source_path,
)

HUB_MERMAID = '''graph LR
    hub["⚙️ handle_request()<br/>src/api/handler.py"]:::hub
    in1["📥 HTTP Request"]:::input
    in1 --> hub
'''


def test_extract_source_path_from_hub_label():
    assert extract_source_path(HUB_MERMAID) == "src/api/handler.py"


def test_extract_source_path_returns_none_without_br():
    assert extract_source_path('graph LR\n    hub["⚙️ my_func()"]:::hub') is None


def test_extract_source_path_returns_none_when_not_a_path():
    # Second line exists but has no slash — it's a subtitle, not a path
    assert extract_source_path('graph LR\n    hub["⚙️ my_func()<br/>the main entry"]:::hub') is None


def test_compute_score_perfect():
    assert compute_score(5, []) == 100


def test_compute_score_deducts_per_finding():
    findings = [Finding("stale", "01-a.md", ""), Finding("missing_source", "02-b.md", "")]
    assert compute_score(5, findings) == 75  # 100 - 10 - 15


def test_compute_score_empty_project_floor():
    assert compute_score(0, []) == 10


def test_compute_score_clamps_at_floor():
    many = [Finding("missing_file", f"{i:02d}-x.md", "") for i in range(10)]
    assert compute_score(10, many) == 10


def test_report_to_dict():
    r = AuditReport(findings=[Finding("stale", "01-a.md", "d")], total_pieces=3, score=90)
    d = r.to_dict()
    assert d["score"] == 90
    assert d["total_pieces"] == 3
    assert d["findings"][0] == {"kind": "stale", "piece": "01-a.md", "detail": "d"}