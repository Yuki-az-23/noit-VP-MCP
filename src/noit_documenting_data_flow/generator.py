#!/usr/bin/env python3
"""
Diagram generator - core logic for building viewer + overview from STAR pieces.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

import yaml

MERMAID_RE = re.compile(r"```mermaid\s*\n(.*?)\n```", re.DOTALL)
FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def derive_id(stem: str) -> str:
    """Filename stem -> a valid HTML/JS id (letters/digits/underscore, never digit-first)."""
    slug = re.sub(r"[^0-9a-zA-Z]+", "_", stem).strip("_").lower()
    return slug if slug[:1].isalpha() else "d" + slug


def _parse_front_matter(text: str) -> dict[str, Any]:
    """Extract YAML front matter from a piece, if present."""
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def parse_piece(path: Path) -> dict[str, Any]:
    """Extract {title, desc, mermaid, source_path, issues, milestone, project} from a diagram piece."""
    text = path.read_text(encoding="utf-8")
    front = _parse_front_matter(text)

    # Find H1 title
    title = path.stem
    for ln in text.splitlines():
        if ln.startswith("# "):
            title = ln[2:].strip()
            break

    # Find first paragraph after H1 (description)
    desc = ""
    seen_h1 = False
    for ln in text.splitlines():
        if ln.startswith("# "):
            seen_h1 = True
            continue
        if seen_h1 and ln.strip() and not ln.startswith(("#", "```", ">", "|")):
            desc = ln.strip()
            break

    # Find first mermaid block
    m = MERMAID_RE.search(text)
    if not m:
        raise ValueError(f"No ```mermaid block found in {path.name}")

    mermaid = m.group(1).strip()
    source_path = front.get("source") or front.get("source_path") or ""
    issues = front.get("issues") or []
    milestone = front.get("milestone") or ""
    project = front.get("project") or ""

    return {
        "title": title,
        "desc": desc,
        "mermaid": mermaid,
        "source_path": source_path,
        "issues": issues,
        "milestone": milestone,
        "project": project,
    }


def render_nav(groups: list[dict[str, Any]]) -> str:
    buttons = [
        '    <button class="active" data-group="all" onclick="showSection(\'all\')">All Diagrams</button>'
    ]
    for g in groups:
        label = html.escape(g["label"])
        buttons.append(
            f'    <button data-group="{g["id"]}" onclick="showSection(\'{g["id"]}\')">{label}</button>'
        )
    return "\n".join(buttons)


def render_section(did: str, group_id: str, badge: str, index: int, piece: dict[str, str]) -> str:
    title = html.escape(f"{index}. {piece['title']}")
    desc = html.escape(piece["desc"] or piece["title"])
    badge_label = html.escape(badge.capitalize())
    # HTML-escape the Mermaid so <br/> / <--> survive as text
    mermaid = html.escape(piece["mermaid"], quote=False)

    issue_bits = []
    for issue in piece.get("issues") or []:
        issue_bits.append(f'<span class="issue-badge">#{issue}</span>')
    issue_html = "\n".join(issue_bits)
    milestone = piece.get("milestone") or ""
    milestone_html = f'<span class="milestone-badge">{html.escape(str(milestone))}</span>' if milestone else ""
    meta_html = "" if not (issue_html or milestone_html) else (
        f'<div class="section-meta">{issue_html}{milestone_html}</div>'
    )

    return f"""    <div class=\"diagram-section\" data-group=\"{group_id}\" id=\"sec-{did}\">
        <div class=\"section-header\">
            <h2>{title}</h2>
            <span class=\"badge badge-{badge}\">{badge_label}</span>
        </div>
        <div class=\"section-desc\">{desc}</div>
        {meta_html}
        <div class=\"diagram-viewport\" id=\"viewport-{did}\">
            <div class=\"zoom-help\" id=\"help-{did}\">Scroll to zoom &bull; Drag to pan &bull; Double-click to reset</div>
            <div class=\"zoom-badge\" id=\"badge-{did}\">100%</div>
            <div class=\"zoom-controls\">
                <button onclick=\"zoomIn('{did}')\" title=\"Zoom in\">+</button>
                <button onclick=\"zoomOut('{did}')\" title=\"Zoom out\">&minus;</button>
                <button onclick=\"zoomReset('{did}')\" title=\"Reset view\" style=\"font-size:0.8rem\">&#8635;</button>
                <button onclick=\"zoomFit('{did}')\" title=\"Fit to screen\" style=\"font-size:0.75rem\">&#8865;</button>
                <button onclick=\"toggleFullscreen('viewport-{did}')\" title=\"Fullscreen\" style=\"font-size:0.85rem\">&#10530;</button>
            </div>
            <div class=\"mermaid-src\" id=\"src-{did}\">
 {mermaid}
            </div>
        </div>
    </div>"""


def build_viewer(manifest: dict[str, Any], diagrams_dir: Path, template: str) -> tuple[str, str]:
    """Build the interactive HTML viewer and overview Markdown from manifest + pieces."""
    groups = manifest["groups"]
    badge_by_group = {g["id"]: g.get("badge", "ops") for g in groups}

    sections, ids, rows, map_nodes, map_clicks = [], [], [], [], []
    groups_seen: dict[str, list[str]] = {g["id"]: [] for g in groups}

    for i, entry in enumerate(manifest["diagrams"], start=1):
        path = diagrams_dir / entry["file"]
        piece = parse_piece(path)
        did = derive_id(path.stem)
        gid = entry["group"]
        ids.append(did)
        sections.append(render_section(did, gid, badge_by_group.get(gid, "ops"), i, piece))
        rows.append(f"| {i} | [{piece['title']}]({entry['file']}) | {piece['desc']} |")
        node_label = piece["title"].replace('"', "'")
        map_nodes.append((gid, did, node_label))
        map_clicks.append(f'    click {did} "{entry["file"]}"')
        groups_seen.setdefault(gid, []).append(did)

    html_out = (
        template.replace("{{TITLE}}", html.escape(manifest.get("title", "Architecture Diagrams")))
        .replace("{{SUBTITLE}}", html.escape(manifest.get("subtitle", "")))
        .replace("{{NAV_BUTTONS}}", render_nav(groups))
        .replace("{{DIAGRAM_SECTIONS}}", "\n".join(sections))
        .replace("{{DIAGRAM_IDS_JSON}}", "[" + ", ".join(f"'{i}'" for i in ids) + "]")
    )

    # Overview index page (Markdown) with clickable system map
    map_lines = ["graph LR"]
    for g in groups:
        members = [n for (gid, did, n) in map_nodes if gid == g["id"]]
        if not members:
            continue
        map_lines.append(f'    subgraph {g["id"]}["{g["label"]}"]')
        for gid, did, label in map_nodes:
            if gid == g["id"]:
                map_lines.append(f'        {did}["{label}"]')
        map_lines.append("    end")
    map_lines.extend(map_clicks)

    overview = (
        f"# {manifest.get('title', 'Architecture Diagrams')} — Overview\n\n"
        "> **Generated** by `noit-diagram-rollup` from `docs/architecture/diagrams/*.md`. "
        "Do not edit by hand — edit a piece and re-run the generator.\n\n"
        "| # | Diagram | Shows |\n|---|---------|-------|\n"
        + "\n".join(rows)
        + "\n\n## System map\n\n```mermaid\n"
        + "\n".join(map_lines)
        + "\n```\n"
    )
    return html_out, overview
