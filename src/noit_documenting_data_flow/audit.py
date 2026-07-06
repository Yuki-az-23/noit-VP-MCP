#!/usr/bin/env python3
"""
Drift audit - measures how in-sync diagram pieces are with the code they document.

Inspired by loop-engineering's Loop Ready score: one number (10-100) that a human
CI gate or an agent loop can act on. Report-only by design (L1); enforcement is
the caller's choice via --fail-under (L2) or an agent loop (L3).
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .generator import parse_piece

HUB_LABEL_RE = re.compile(r'"([^"]*)"\]\s*:::hub')

# Points each kind of drift costs. A diagram pointing at deleted code is a lie;
# a missing manifest line is merely unfinished bookkeeping.
DEDUCTIONS = {
    "missing_file": 20,     # manifest lists a piece that is not on disk
    "missing_source": 15,   # hub references a source file that is gone
    "stale": 10,            # source changed after the piece was last touched
    "unregistered": 10,     # piece on disk but absent from the manifest
    "no_source_ref": 5,     # hub label has no <br/>source/path line
}


@dataclass
class Finding:
    kind: str
    piece: str
    detail: str


@dataclass
class AuditReport:
    findings: list[Finding]
    total_pieces: int
    score: int

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "total_pieces": self.total_pieces,
            "findings": [
                {"kind": f.kind, "piece": f.piece, "detail": f.detail} for f in self.findings
            ],
        }


def extract_source_path(mermaid: str) -> str | None:
    """Pull the documented source path out of the hub node label.

    Convention: hub["⚙️ TITLE<br/>src/path/to/file.py"]:::hub — the text after
    the last <br/> is the path. Returns None if absent or not path-like.
    """
    m = HUB_LABEL_RE.search(mermaid)
    if not m or "<br/>" not in m.group(1):
        return None
    candidate = m.group(1).rsplit("<br/>", 1)[1].strip()
    return candidate if "/" in candidate else None


def compute_score(total_pieces: int, findings: list[Finding]) -> int:
    """Docs Sync Score: 100 minus per-finding deductions, clamped to [10, 100]."""
    if total_pieces == 0:
        return 10
    score = 100 - sum(DEDUCTIONS.get(f.kind, 5) for f in findings)
    return max(10, min(100, score))