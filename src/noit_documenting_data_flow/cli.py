#!/usr/bin/env python3
"""
CLI for NOit Documenting Data Flow.

Commands:
  init      Initialize diagram structure in current project
  build     Build viewer + overview (dry-run by default)
  validate  Validate all pieces have valid mermaid + required fields
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

from .generator import build_viewer, parse_piece, derive_id
from .audit import audit_diagrams
from .templates import (
    DIAGRAM_TEMPLATE,
    MANIFEST_TEMPLATE,
    PAGES_TEMPLATE,
    MERMAID_STYLE,
    MKDOCS_SNIPPET,
    VIEWER_TEMPLATE,
    MERMAID_INTERACTIVE_JS,
    MERMAID_INTERACTIVE_CSS,
)


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize diagram structure in current project."""
    cwd = Path.cwd()
    diagrams_dir = cwd / "docs" / "architecture" / "diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)

    # Create directories
    (cwd / "docs" / "architecture").mkdir(parents=True, exist_ok=True)
    (cwd / "docs" / "javascripts").mkdir(parents=True, exist_ok=True)
    (cwd / "docs" / "stylesheets").mkdir(parents=True, exist_ok=True)
    (cwd / "scripts").mkdir(parents=True, exist_ok=True)
    (cwd / ".claude" / "skills" / "documenting-data-flow").mkdir(parents=True, exist_ok=True)

    # Write template files
    files_to_write = [
        (diagrams_dir / "00-template.md", DIAGRAM_TEMPLATE),
        (diagrams_dir / "rollup.manifest.yml", MANIFEST_TEMPLATE),
        (diagrams_dir / ".pages", PAGES_TEMPLATE),
        (diagrams_dir / "mermaid-style.md", MERMAID_STYLE),
        (cwd / "docs" / "javascripts" / "mermaid-interactive.js", MERMAID_INTERACTIVE_JS),
        (cwd / "docs" / "stylesheets" / "mermaid-interactive.css", MERMAID_INTERACTIVE_CSS),
        (cwd / ".claude" / "skills" / "documenting-data-flow" / "SKILL.md", SKILL_TEMPLATE),
    ]

    for path, content in files_to_write:
        if path.exists() and not args.force:
            print(f"  [SKIP]  Skip (exists): {path.relative_to(cwd)}")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"  [OK] Created: {path.relative_to(cwd)}")

    # Show mkdocs snippet
    print("\n[NOTE] Add to your mkdocs.yml:")
    print(MKDOCS_SNIPPET)

    print("\n[OK] Initialized! Next steps:")
    print("  1. Copy 00-template.md to NN-your-function.md")
    print("  2. Edit the piece (STAR pattern: hub = your function)")
    print("  3. Add to .pages and rollup.manifest.yml")
    print("  4. Run: noit-diagram-rollup build --write")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Build the viewer and overview."""
    cwd = Path.cwd()
    diagrams_dir = cwd / args.diagrams_dir
    manifest_path = Path(args.manifest) if args.manifest else diagrams_dir / "rollup.manifest.yml"
    template_path = Path(args.template) if args.template else TEMPLATES_DIR / "viewer_template.html"

    if not manifest_path.exists():
        print(f"[ERROR] Manifest not found: {manifest_path}")
        print("   Run 'noit-diagram-rollup init' first, or specify --manifest")
        return 1

    if not template_path.exists():
        # Use built-in template
        template = VIEWER_TEMPLATE
    else:
        template = template_path.read_text(encoding="utf-8")

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"[ERROR] Invalid manifest YAML: {e}")
        return 1

    try:
        html_out, overview = build_viewer(manifest, diagrams_dir, template)
    except (ValueError, FileNotFoundError) as e:
        print(f"[ERROR] Build failed: {e}")
        return 1

    dry = not args.write
    if dry:
        scratch = Path(tempfile.mkdtemp(prefix="noit_diagram_rollup_"))
        out_html = scratch / Path(args.out_html).name
        out_overview = scratch / Path(args.out_overview).name
    else:
        out_html = cwd / args.out_html
        out_overview = cwd / args.out_overview
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_overview.parent.mkdir(parents=True, exist_ok=True)

    out_html.write_text(html_out, encoding="utf-8")
    out_overview.write_text(overview, encoding="utf-8")

    n = len(manifest["diagrams"])
    print(f"{'DRY-RUN' if dry else 'WROTE'}: {n} pieces -> viewport + overview")
    print(f"  HTML     : {out_html}")
    print(f"  Overview : {out_overview}")

    if dry:
        live_html = cwd / "docs" / "architecture_diagrams.html"
        if live_html.exists():
            print(f"\n[DIFF] Diff vs live viewer:")
            print(f"   git --no-pager diff --no-index {live_html} {out_html}")
        print("\n[TIP] Review, then re-run with --write to emit to real paths.")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate all diagram pieces."""
    cwd = Path.cwd()
    diagrams_dir = cwd / args.diagrams_dir
    manifest_path = Path(args.manifest) if args.manifest else diagrams_dir / "rollup.manifest.yml"

    if not manifest_path.exists():
        print(f"❌ Manifest not found: {manifest_path}")
        return 1

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    errors = []
    warnings = []

    for i, entry in enumerate(manifest["diagrams"], 1):
        path = diagrams_dir / entry["file"]
        if not path.exists():
            errors.append(f"  {i}. {entry['file']}: FILE NOT FOUND")
            continue

        try:
            piece = parse_piece(path)
            # Check required fields
            if not piece["title"] or piece["title"] == path.stem:
                warnings.append(f"  {i}. {entry['file']}: Title defaults to filename")
            if not piece["desc"]:
                warnings.append(f"  {i}. {entry['file']}: No description (first paragraph after H1)")
            if "FUNCTION_NAME" in piece["mermaid"]:
                warnings.append(f"  {i}. {entry['file']}: Contains template placeholder FUNCTION_NAME")
            print(f"  [OK] {i}. {entry['file']}: {piece['title']}")
        except ValueError as e:
            errors.append(f"  {i}. {entry['file']}: {e}")
        except Exception as e:
            errors.append(f"  {i}. {entry['file']}: Unexpected error - {e}")

    if warnings:
        print("\n[WARN] Warnings:")
        for w in warnings:
            print(w)

    if errors:
        print("\n[ERRORS]:")
        for e in errors:
            print(e)
        return 1

    print(f"\n[OK] All {len(manifest['diagrams'])} pieces valid!")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    """Audit pieces for drift against the source code they document."""
    cwd = Path.cwd()
    diagrams_dir = cwd / args.diagrams_dir
    manifest_path = Path(args.manifest) if args.manifest else diagrams_dir / "rollup.manifest.yml"

    if not manifest_path.exists():
        print(f"[ERROR] Manifest not found: {manifest_path}")
        print("   Run 'noit-diagram-rollup init' first, or specify --manifest")
        return 1

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    report = audit_diagrams(manifest, diagrams_dir, cwd)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        if report.score >= 80:
            band = "IN SYNC"
        elif report.score >= 50:
            band = "DRIFTING"
        else:
            band = "OUT OF SYNC"
        print(f"Docs Sync Score: {report.score}/100  [{band}]")
        print(f"Pieces audited: {report.total_pieces}")
        if report.findings:
            print("\n[FINDINGS]")
            for f in report.findings:
                print(f"  [{f.kind.upper()}] {f.piece}: {f.detail}")
        else:
            print("\n[OK] No drift detected - diagrams match the code.")

    if args.fail_under and report.score < args.fail_under:
        print(f"\n[FAIL] Score {report.score} below --fail-under {args.fail_under}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="noit-diagram-rollup",
        description="NOit Documenting Data Flow - STAR diagrams -> interactive viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.1.0")

    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize diagram structure in current project")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing files")
    p_init.set_defaults(func=cmd_init)

    # build
    p_build = sub.add_parser("build", help="Build viewer + overview")
    p_build.add_argument("--diagrams-dir", default="docs/architecture/diagrams", help="Diagrams folder")
    p_build.add_argument("--manifest", help="Manifest file (default: <diagrams-dir>/rollup.manifest.yml)")
    p_build.add_argument("--template", help="Viewer template HTML")
    p_build.add_argument("--out-html", default="docs/architecture_diagrams.generated.html", help="Output HTML path")
    p_build.add_argument("--out-overview", default="docs/architecture/diagrams/OVERVIEW.generated.md", help="Output overview path")
    p_build.add_argument("--write", action="store_true", help="Write to real paths (default: dry-run)")
    p_build.set_defaults(func=cmd_build)

    # validate
    p_val = sub.add_parser("validate", help="Validate all diagram pieces")
    p_val.add_argument("--diagrams-dir", default="docs/architecture/diagrams", help="Diagrams folder")
    p_val.add_argument("--manifest", help="Manifest file")
    p_val.set_defaults(func=cmd_validate)

    # audit
    p_audit = sub.add_parser("audit", help="Audit pieces for drift vs source code (Docs Sync Score)")
    p_audit.add_argument("--diagrams-dir", default="docs/architecture/diagrams", help="Diagrams folder")
    p_audit.add_argument("--manifest", help="Manifest file")
    p_audit.add_argument("--json", action="store_true", help="Emit machine-readable JSON report")
    p_audit.add_argument("--fail-under", type=int, default=0,
                         help="Exit 1 if score is below this value (CI gate; 0 = report-only)")
    p_audit.set_defaults(func=cmd_audit)

    args = parser.parse_args()
    return args.func(args)


# Skill template for .claude/skills/
SKILL_TEMPLATE = """---
name: documenting-data-flow
description: Use when documenting a function or operation's data flow, adding or updating an architecture diagram, or keeping the interactive diagram viewer and overview in sync in this repo
---

# Documenting Data Flow

## Overview

Architecture is documented as **per-function diagram pieces** under `docs/architecture/diagrams/`.
Each piece is the **source of truth** for one function's data flow. The interactive viewer
(`docs/architecture_diagrams.html`) and the overview index are **generated** from the pieces by
`scripts/build_diagram_rollup.py` — you never hand-edit them.

**Inverted source-of-truth:** author the `.md` piece -> run the generator -> the "VP rollup" (HTML
viewport + overview) rebuilds. Do NOT copy Mermaid into the HTML by hand or maintain it twice.

**House convention (every plan + doc, not just architecture):** author diagrams in the STAR
hub-and-spoke layout ([star-template.md](star-template.md)) with the dark palette
([mermaid-style.md](mermaid-style.md)). Every ```` ```mermaid ```` block on the MkDocs site renders
**interactive automatically** — dark pan/zoom/fullscreen viewport, same look as
`architecture_diagrams.html` — via `docs/javascripts/mermaid-interactive.js` +
`docs/stylesheets/mermaid-interactive.css` (wired in `mkdocs.yml`). So just write a `mermaid` fence
anywhere; the viewer treatment is free. No per-page setup.

## Artifact map

| Artifact | Role | You edit it? |
|---|---|---|
| `docs/architecture/diagrams/NN-*.md` | One STAR piece per function — **source** | [OK] yes |
| `docs/architecture/diagrams/rollup.manifest.yml` | nav groups + badge per piece | [OK] yes (add a line) |
| `docs/architecture/diagrams/.pages` | MkDocs nav order (awesome-pages) | [OK] yes (add a line) |
| `docs/architecture_diagrams.html` | interactive pan/zoom viewer | ❌ generated |
| overview index | high-level rollup linking pieces | ❌ generated |

## Authoring a piece (4 steps)

1. **One function = one hub.** Use the STAR hub-and-spoke layout in
   [star-template.md](star-template.md): the function is the center; inputs / dependencies / outputs
   radiate out. Copy the blank skeleton; a filled real-op example is in the same file.
2. **Style it** per [mermaid-style.md](mermaid-style.md): dark `classDef` palette with explicit
   `color:`, `<br/>` (never `\\n`) for line breaks, the shared edge vocabulary (`-->` `==>` `-.->`).
3. **Register nav:** add the file to `.pages` (order) and to `rollup.manifest.yml` (group + badge).
4. **Roll up:** run the generator (below), preview with `mkdocs serve`, validate with
   `mkdocs build --strict`.

## Roll up the VP (viewport + overview)

Three deliberate tiers — the `--write` default is a **safe `.generated.` sibling**, so replacing the
live viewer is always an explicit choice:

```bash
# 1. dry-run (default): writes to a scratch temp dir + prints a diff hint. Nothing in the repo moves.
noit-diagram-rollup build --dry-run

# 2. write the *.generated.* siblings
noit-diagram-rollup build --write

# 3. REPLACE the live viewer (only after reviewing tier 1/2): explicit --out-html at the live file.
noit-diagram-rollup build --write --out-html docs/architecture_diagrams.html
```

The generator derives every HTML id from the filename, builds the nav + `diagramIds` for you,
HTML-escapes the Mermaid (so `<br/>` survives), and preserves the pan/zoom shell.

## The documentation loop

After changing any function that has a STAR piece (or adding a new public function):

1. Run `noit-diagram-rollup audit` (or the `audit_diagrams` MCP tool).
2. For every `stale` finding: re-read the source, update the piece's mermaid, re-run audit.
3. For every `missing_source` finding: the code moved or was deleted — fix the hub path or
   remove the piece (and its `.pages` / manifest lines).
4. For every `unregistered` finding: add the piece to `.pages` and `rollup.manifest.yml`.
5. Re-roll the viewer: `noit-diagram-rollup build --write`.

Do not declare a documentation task done while the Docs Sync Score is below 80.

## Common mistakes

- ❌ Hand-editing `architecture_diagrams.html` — the generator owns all of it. Edit the piece, re-run.
- ❌ Treating the HTML as the source — it's generated; the `.md` piece is the source.
- ❌ A flat `graph LR` with generic Inputs->Op->Outputs — use the STAR hub layout.
- ❌ `\\n` in labels — use `<br/>`.
- ❌ Forgetting the `.pages` / manifest entry — the piece won't appear in nav or the rollup.
"""


if __name__ == "__main__":
    sys.exit(main())