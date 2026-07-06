"""
Built-in templates for NOit Documenting Data Flow.
All templates use NOit branding and dark theme.
"""

# STAR Diagram Piece Template
DIAGRAM_TEMPLATE = """# TEMPLATE: Your Function Name

**Copy this file** to create a new diagram piece (e.g., `01-your-function.md`).

One function = one hub = one piece. The function is the STAR center; its inputs, dependencies, and outputs radiate as spokes.

```mermaid
graph LR
    %% ── STAR hub: the ONE function this piece documents ──
    hub["⚙️ FUNCTION_NAME<br/>src/path/to/module.py"]:::hub

    %% ── Spoke: inputs (data the function reads) ──
    subgraph In["📥 Inputs"]
        in1["INPUT_SOURCE_1<br/>where it comes from"]:::input
        in2["INPUT_SOURCE_2"]:::input
    end

    %% ── Spoke: dependencies (services / models it calls) ──
    subgraph Deps["🤖 Dependencies"]
        dep1["LLM / API / Cache"]:::dep
        svc1["EXTERNAL_SERVICE"]:::extSvc
    end

    %% ── Spoke: outputs (data it writes / emits) ──
    subgraph Out["💾 Outputs"]
        out1["OUTPUT_SINK<br/>store / snapshot / preview"]:::output
    end

    %% ── Streaming edges: in → hub → out ──
    in1 -->|"what flows"| hub
    in2 --> hub
    hub <-->|"read / write"| dep1
    hub -->|"query"| svc1
    hub ==>|"result"| out1

    classDef hub      fill:#4A148C,stroke:#CE93D8,color:#F3E5F9,stroke-width:3px
    classDef input    fill:#37474F,stroke:#78909C,color:#CFD8DC,stroke-width:1px
    classDef dep      fill:#0D47A1,stroke:#42A5F5,color:#BBDEFB,stroke-width:1px
    classDef extSvc   fill:#E65100,stroke:#FFB74D,color:#FFF3E0,stroke-width:2px
    classDef output   fill:#1B5E20,stroke:#66BB6A,color:#C8E6C9,stroke-width:2px
```

---

*Rendered natively by MkDocs Material (Mermaid). This piece is the source of truth; the interactive
[Architecture Diagrams](../../architecture_diagrams.html) viewer is generated from it by
`noit-diagram-rollup build`.*
"""


# Manifest Template
MANIFEST_TEMPLATE = """title: "Project Architecture Diagrams"
subtitle: "Interactive viewer generated from per-function STAR pieces — by NOit (noit2.com)"
groups:
  - id: "infra"
    label: "Infrastructure"
    badge: "infra"
  - id: "ops"
    label: "Operations"
    badge: "ops"
  - id: "seq"
    label: "Sequences"
    badge: "seq"

diagrams:
  - file: "00-template.md"
    group: "ops"
  # Add your diagrams here:
  # - file: "01-your-function.md"
  #   group: "ops"
  # - file: "02-another-flow.md"
  #   group: "seq"
"""


# Pages Template (awesome-pages nav order)
PAGES_TEMPLATE = """00-template.md
# Add new diagram files here (one per line) for MkDocs nav order:
# 01-your-function.md
# 02-another-flow.md
"""


# Mermaid Style Reference
MERMAID_STYLE = """# Mermaid Style Reference (NOit Diagrams)

The canonical palette + syntax for every diagram piece under `docs/architecture/diagrams/`.
Use this so a piece renders identically in MkDocs Material **and** in the generated HTML viewport.

## Line breaks: `<br/>`, never `\\n`

Inside a node label use `<br/>` for multi-line text. `\\n` does NOT render in these renderers.

```
good["title_normalized<br/>(lowercase augmented title)"]   ✅
bad["title_normalized\\n(lowercase)"]                        ❌
```

## Node shapes

| Syntax | Shape | Use for |
|---|---|---|
| `id["text"]` | rectangle | functions, operations, keywords, plain nodes |
| `id[("text")]` | cylinder | stores / volumes / caches (`./output/...`, snapshots) |
| `id[/"text"/]` | parallelogram | external services (API, payment, email) |
| `id{{"text"}}` | hexagon | LLM model tiers |
| `id{"text?"}` | diamond | decision points (guard checks, branches) |
| `subgraph Grp["📥 Title"]` | cluster | dimension grouping (inputs / deps / outputs) |

## Edge vocabulary (keep consistent — matches the Legend)

| Edge | Meaning |
|---|---|
| `A -->|"label"| B` | direct call / data flow |
| `A ==>|"label"| B` | pipeline chain |
| `A -.->|"label"| B` | async / optional / suggestion / dry-run branch |
| `A <-->|"read/write"| B` | bidirectional read+write (hub ↔ service) |

## classDef palette (DARK — canonical)

The living pieces and the HTML viewer both render on a dark theme, so `classDef` MUST set an
explicit `color:` (text) or labels vanish on dark backgrounds.

```
classDef hub      fill:#4A148C,stroke:#CE93D8,color:#F3E5F9,stroke-width:3px   %% the STAR center function
classDef input    fill:#37474F,stroke:#78909C,color:#CFD8DC,stroke-width:1px   %% inputs / keywords / grey
classDef dep      fill:#0D47A1,stroke:#42A5F5,color:#BBDEFB,stroke-width:1px   %% LLM / classification / blue
classDef extSvc   fill:#E65100,stroke:#FFB74D,color:#FFF3E0,stroke-width:2px   %% external API / orange
classDef output   fill:#1B5E20,stroke:#66BB6A,color:#C8E6C9,stroke-width:2px   %% outputs / success / green
classDef decision fill:#E65100,stroke:#FFB74D,color:#FFF3E0,stroke-width:2px   %% diamond decisions
classDef danger   fill:#B71C1C,stroke:#EF5350,color:#FFCDD2,stroke-width:2px   %% error / block / red
classDef fix      fill:#4E342E,stroke:#FFB74D,color:#FFE0B2,stroke-width:2px   %% bug-fix annotation
```

Apply with a trailing `:::class` on the node (`hub["..."]:::hub`) or a `class a,b,c input` line.

## Emoji subgraph titles (recurring)

📥 Inputs · ⚙️ Function/Operation · 🤖 Dependencies · 🌐 External Services · 💾 Outputs ·
🛡️ Guard Chain · 📦 Supplier · 🔀 Routing · ⚡ Triggers · 🧠 LLM · 🗺️ Breadcrumb · ✅ Final Output

## Required page skeleton

Every piece is `# H1 Title` → one-line description paragraph → the ```` ```mermaid ```` block →
the standard footer. The generator reads exactly those parts (title, first paragraph, first mermaid
block), so keep that order.
"""


# MkDocs snippet to add
MKDOCS_SNIPPET = """extra_javascript:
  - javascripts/mermaid-interactive.js
extra_css:
  - stylesheets/mermaid-interactive.css

plugins:
  - awesome-pages          # enables .pages nav (install: mkdocs-awesome-pages-plugin)
  - roamlinks              # enables [[wikilinks]] (install: mkdocs-roamlinks-plugin)

markdown_extensions:
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
"""


# Viewer Template (dark theme, pan/zoom, fullscreen)
VIEWER_TEMPLATE = """<!DOCTYPE html>
<!--
  GENERATED by noit-diagram-rollup — DO NOT EDIT BY HAND.
  Source of truth: the per-piece Mermaid files (docs/architecture/diagrams/*.md).
  Edit a piece, then re-run the generator. This template holds only the static shell.
  Built by NOit (https://noit2.com)
-->
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }
        .header { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-bottom: 1px solid #334155; padding: 1.5rem; text-align: center; }
        .header h1 { font-size: 1.6rem; font-weight: 700; background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header p { color: #94a3b8; margin-top: 0.3rem; font-size: 0.85rem; }
        .nav { display: flex; justify-content: center; gap: 0.4rem; padding: 0.8rem; background: #1e293b; border-bottom: 1px solid #334155; position: sticky; top: 0; z-index: 100; flex-wrap: wrap; }
        .nav button { padding: 0.4rem 1rem; border: 1px solid #475569; border-radius: 6px; background: transparent; color: #94a3b8; cursor: pointer; font-size: 0.82rem; transition: all 0.2s; }
        .nav button:hover, .nav button.active { background: #334155; color: #e2e8f0; border-color: #60a5fa; }
        .container { max-width: 100%; margin: 0 auto; padding: 1.5rem; }
        .diagram-section { background: #1e293b; border: 1px solid #334155; border-radius: 12px; margin-bottom: 2rem; overflow: hidden; }
        .diagram-section.hidden { display: none; }
        .section-header { padding: 1.2rem 1.5rem; border-bottom: 1px solid #334155; display: flex; align-items: center; gap: 1rem; }
        .section-header h2 { font-size: 1.2rem; font-weight: 600; color: #f1f5f9; }
        .section-header .badge { padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; }
        .badge-infra { background: #065f46; color: #6ee7b7; }
        .badge-ops { background: #4c1d95; color: #c4b5fd; }
        .badge-seq { background: #7c2d12; color: #fdba74; }
        .section-desc { padding: 0.8rem 1.5rem; color: #b0bec5; font-size: 0.85rem; border-bottom: 1px solid #334155; }
        .diagram-viewport { position: relative; width: 100%; height: 85vh; min-height: 500px; background: #0f172a; border-radius: 0 0 12px 12px; overflow: hidden; cursor: grab; }
        .diagram-viewport:active { cursor: grabbing; }
        .diagram-viewport svg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
        .mermaid-src { display: none; }
        .zoom-controls { position: absolute; bottom: 16px; right: 16px; display: flex; flex-direction: column; gap: 4px; z-index: 50; }
        .zoom-controls button { width: 38px; height: 38px; border: 1px solid #475569; border-radius: 8px; background: rgba(30, 41, 59, 0.9); backdrop-filter: blur(8px); color: #e2e8f0; font-size: 1.2rem; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.15s; line-height: 1; }
        .zoom-controls button:hover { background: #334155; border-color: #60a5fa; }
        .zoom-badge { position: absolute; top: 12px; right: 16px; padding: 4px 10px; background: rgba(30, 41, 59, 0.85); backdrop-filter: blur(8px); border: 1px solid #475569; border-radius: 6px; color: #94a3b8; font-size: 0.75rem; z-index: 50; pointer-events: none; font-variant-numeric: tabular-nums; }
        .zoom-help { position: absolute; top: 12px; left: 16px; padding: 4px 10px; background: rgba(30, 41, 59, 0.85); backdrop-filter: blur(8px); border: 1px solid #334155; border-radius: 6px; color: #64748b; font-size: 0.72rem; z-index: 50; pointer-events: none; transition: opacity 0.5s; }
        .diagram-viewport:fullscreen, .diagram-viewport:-webkit-full-screen { height: 100vh; }
        .footer { text-align: center; padding: 2rem; color: #475569; font-size: 0.8rem; }
        @media (max-width: 768px) { .diagram-viewport { height: 70vh; min-height: 400px; } .container { padding: 1rem; } }
    </style>
</head>
<body>

<div class="header">
    <h1>{{TITLE}}</h1>
    <p>{{SUBTITLE}}</p>
</div>

<div class="nav">
{{NAV_BUTTONS}}
</div>

<div class="container">
{{DIAGRAM_SECTIONS}}
</div>

<div class="footer">
    Generated by noit-diagram-rollup — scroll to zoom, drag to pan, double-click to reset. | Built by <a href="https://noit2.com" style="color:#60a5fa">NOit</a>
</div>

<script>
    mermaid.initialize({
        startOnLoad: false,
        theme: 'dark',
        themeVariables: {
            primaryColor: '#1e293b', primaryTextColor: '#e2e8f0', primaryBorderColor: '#475569',
            lineColor: '#64748b', secondaryColor: '#334155', tertiaryColor: '#0f172a',
            nodeTextColor: '#e2e8f0', nodeBorder: '#475569', clusterBkg: '#1e293b',
            clusterBorder: '#475569', fontFamily: 'Segoe UI, system-ui, sans-serif', fontSize: '14px'
        },
        flowchart: { htmlLabels: true, curve: 'basis', useMaxWidth: false },
        sequence: { useMaxWidth: false, wrap: true }
    });

    const panZoomInstances = {};
    const diagramIds = {{DIAGRAM_IDS_JSON}};

    async function renderDiagrams() {
        for (const id of diagramIds) {
            const srcEl = document.getElementById('src-' + id);
            const viewport = document.getElementById('viewport-' + id);
            if (!srcEl || !viewport) continue;
            try {
                const { svg } = await mermaid.render('mermaid-' + id, srcEl.textContent.trim());
                viewport.insertAdjacentHTML('afterbegin', svg);
                const svgEl = viewport.querySelector('svg#mermaid-' + id);
                if (svgEl) {
                    svgEl.removeAttribute('style');
                    svgEl.setAttribute('width', '100%');
                    svgEl.setAttribute('height', '100%');
                    panZoomInstances[id] = svgPanZoom(svgEl, {
                        zoomEnabled: true, panEnabled: true, controlIconsEnabled: false,
                        dblClickZoomEnabled: false, mouseWheelZoomEnabled: true,
                        preventMouseEventsDefault: true, minZoom: 0.3, maxZoom: 5, fit: true, center: true,
                        beforeZoom: function() { updateZoomBadge(id); }, onZoom: function() { updateZoomBadge(id); }
                    });
                    svgEl.addEventListener('dblclick', function(e) {
                        e.preventDefault();
                        if (panZoomInstances[id]) {
                            panZoomInstances[id].reset();
                            setTimeout(() => { panZoomInstances[id].fit(); panZoomInstances[id].center(); updateZoomBadge(id); }, 50);
                        }
                    });
                    updateZoomBadge(id);
                }
            } catch (err) {
                console.error('Mermaid render error for', id, err);
                viewport.insertAdjacentHTML('afterbegin', '<div style="padding:2rem;color:#f87171;">Diagram render error. Check console.</div>');
            }
        }
        setTimeout(() => { document.querySelectorAll('.zoom-help').forEach(el => el.style.opacity = '0'); }, 5000);
    }

    function updateZoomBadge(id) {
        const inst = panZoomInstances[id]; const badge = document.getElementById('badge-' + id);
        if (inst && badge) { badge.textContent = Math.round(inst.getZoom() * 100) + '%'; }
    }
    function zoomIn(id) { const i = panZoomInstances[id]; if (i) { i.zoomIn(); updateZoomBadge(id); } }
    function zoomOut(id) { const i = panZoomInstances[id]; if (i) { i.zoomOut(); updateZoomBadge(id); } }
    function zoomReset(id) { const i = panZoomInstances[id]; if (i) { i.reset(); setTimeout(() => { i.fit(); i.center(); updateZoomBadge(id); }, 50); } }
    function zoomFit(id) { const i = panZoomInstances[id]; if (i) { i.fit(); i.center(); updateZoomBadge(id); } }

    function toggleFullscreen(viewportId) {
        const el = document.getElementById(viewportId); if (!el) return;
        const id = viewportId.replace('viewport-', '');
        const refit = () => setTimeout(() => { if (panZoomInstances[id]) { panZoomInstances[id].resize(); panZoomInstances[id].fit(); panZoomInstances[id].center(); updateZoomBadge(id); } }, 200);
        if (!document.fullscreenElement) { el.requestFullscreen().then(refit).catch(err => console.log('Fullscreen denied', err)); }
        else { document.exitFullscreen().then(refit); }
    }

    function showSection(group) {
        document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.diagram-section').forEach(el => {
            if (group === 'all' || el.dataset.group === group) el.classList.remove('hidden');
            else el.classList.add('hidden');
        });
        const active = document.querySelector('.nav button[data-group="' + group + '"]');
        if (active) active.classList.add('active');
        setTimeout(() => { diagramIds.forEach(id => { if (panZoomInstances[id]) { try { panZoomInstances[id].resize(); } catch (e) {} } }); }, 100);
    }

    document.addEventListener('DOMContentLoaded', renderDiagrams);
</script>
</body>
</html>
"""


# mermaid-interactive.js - makes ALL mermaid fences interactive on MkDocs site
MERMAID_INTERACTIVE_JS = """/**
 * NOit Mermaid Interactive - Makes ALL Mermaid diagrams on the MkDocs site interactive
 * (pan/zoom/fullscreen). Loaded via extra_javascript in mkdocs.yml.
 * Built by NOit (https://noit2.com)
 */

(function () {
  'use strict';

  function waitForMermaid() {
    return new Promise((resolve) => {
      if (window.mermaid && typeof mermaid.run === 'function') {
        mermaid.run().then(resolve).catch(resolve);
      } else {
        const check = setInterval(() => {
          if (window.mermaid && typeof mermaid.run === 'function') {
            clearInterval(check);
            mermaid.run().then(resolve).catch(resolve);
          }
        }, 100);
        setTimeout(() => { clearInterval(check); resolve(); }, 5000);
      }
    });
  }

  function loadPanZoom() {
    return new Promise((resolve, reject) => {
      if (window.svgPanZoom) {
        resolve(window.svgPanZoom);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js';
      script.onload = () => resolve(window.svgPanZoom);
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  async function initPanZoom(svgEl, container) {
    const svgPanZoom = await loadPanZoom();

    svgEl.removeAttribute('style');
    svgEl.setAttribute('width', '100%');
    svgEl.setAttribute('height', '100%');

    let controls = container.querySelector('.mermaid-zoom-controls');
    if (!controls) {
      controls = document.createElement('div');
      controls.className = 'mermaid-zoom-controls';
      controls.innerHTML = `
        <button class="zoom-in" title="Zoom in">+</button>
        <button class="zoom-out" title="Zoom out">−</button>
        <button class="zoom-reset" title="Reset view">↻</button>
        <button class="zoom-fit" title="Fit to screen">⛶</button>
        <button class="zoom-fullscreen" title="Fullscreen">⛶</button>
      `;
      container.style.position = 'relative';
      container.appendChild(controls);
    }

    let badge = container.querySelector('.mermaid-zoom-badge');
    if (!badge) {
      badge = document.createElement('div');
      badge.className = 'mermaid-zoom-badge';
      badge.textContent = '100%';
      container.appendChild(badge);
    }

    let help = container.querySelector('.mermaid-zoom-help');
    if (!help) {
      help = document.createElement('div');
      help.className = 'mermaid-zoom-help';
      help.textContent = 'Scroll to zoom • Drag to pan • Double-click to reset';
      container.appendChild(help);
    }

    const panZoom = svgPanZoom(svgEl, {
      zoomEnabled: true,
      panEnabled: true,
      controlIconsEnabled: false,
      dblClickZoomEnabled: false,
      mouseWheelZoomEnabled: true,
      preventMouseEventsDefault: true,
      minZoom: 0.3,
      maxZoom: 5,
      fit: true,
      center: true,
      beforeZoom: () => updateBadge(badge, panZoom),
      onZoom: () => updateBadge(badge, panZoom)
    });

    svgEl.addEventListener('dblclick', (e) => {
      e.preventDefault();
      panZoom.reset();
      setTimeout(() => { panZoom.fit(); panZoom.center(); updateBadge(badge, panZoom); }, 50);
    });

    controls.querySelector('.zoom-in').addEventListener('click', () => { panZoom.zoomIn(); updateBadge(badge, panZoom); });
    controls.querySelector('.zoom-out').addEventListener('click', () => { panZoom.zoomOut(); updateBadge(badge, panZoom); });
    controls.querySelector('.zoom-reset').addEventListener('click', () => { panZoom.reset(); setTimeout(() => { panZoom.fit(); panZoom.center(); updateBadge(badge, panZoom); }, 50); });
    controls.querySelector('.zoom-fit').addEventListener('click', () => { panZoom.fit(); panZoom.center(); updateBadge(badge, panZoom); });

    controls.querySelector('.zoom-fullscreen').addEventListener('click', () => toggleFullscreen(container, panZoom, badge));

    setTimeout(() => { help.style.opacity = '0'; }, 5000);

    container._panZoom = panZoom;
  }

  function updateBadge(badge, panZoom) {
    if (badge && panZoom) {
      badge.textContent = Math.round(panZoom.getZoom() * 100) + '%';
    }
  }

  function toggleFullscreen(container, panZoom, badge) {
    const refit = () => setTimeout(() => {
      if (panZoom) {
        panZoom.resize();
        panZoom.fit();
        panZoom.center();
        updateBadge(badge, panZoom);
      }
    }, 200);

    if (!document.fullscreenElement) {
      container.requestFullscreen().then(refit).catch(err => console.log('Fullscreen denied', err));
    } else {
      document.exitFullscreen().then(refit);
    }
  }

  async function initAll() {
    await waitForMermaid();
    const containers = document.querySelectorAll('.mermaid');
    for (const container of containers) {
      const svg = container.querySelector('svg');
      if (svg && !container._panZoom) {
        try {
          await initPanZoom(svg, container);
        } catch (err) {
          console.error('Mermaid interactive init failed:', err);
        }
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  document.addEventListener('pjax:end', initAll);
  document.addEventListener('pjax:complete', initAll);

  window.initMermaidInteractive = initAll;
})();
"""


# mermaid-interactive.css - dark theme for interactive diagrams on MkDocs site
MERMAID_INTERACTIVE_CSS = """/**
 * NOit Mermaid Interactive Styles - Dark theme for pan/zoom/fullscreen
 * Loaded via extra_css in mkdocs.yml
 * Built by NOit (https://noit2.com)
 */

.mermaid {
  position: relative;
  width: 100%;
  min-height: 400px;
  background: var(--md-default-bg-color, #0f172a);
  border-radius: 8px;
  overflow: hidden;
  cursor: grab;
  user-select: none;
}

.mermaid:active {
  cursor: grabbing;
}

.mermaid svg {
  position: absolute !important;
  top: 0;
  left: 0;
  width: 100% !important;
  height: 100% !important;
}

.mermaid-zoom-controls {
  position: absolute;
  bottom: 12px;
  right: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 50;
  pointer-events: auto;
}

.mermaid-zoom-controls button {
  width: 36px;
  height: 36px;
  border: 1px solid var(--md-default-fg-color--lightest, #475569);
  border-radius: 8px;
  background: rgba(30, 41, 59, 0.9);
  backdrop-filter: blur(8px);
  color: var(--md-default-fg-color, #e2e8f0);
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  line-height: 1;
}

.mermaid-zoom-controls button:hover {
  background: var(--md-primary-fg-color--light, #334155);
  border-color: var(--md-primary-fg-color, #60a5fa);
}

.mermaid-zoom-badge {
  position: absolute;
  top: 10px;
  right: 12px;
  padding: 4px 10px;
  background: rgba(30, 41, 59, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid var(--md-default-fg-color--lightest, #475569);
  border-radius: 6px;
  color: var(--md-default-fg-color--light, #94a3b8);
  font-size: 0.75rem;
  z-index: 50;
  pointer-events: none;
  font-variant-numeric: tabular-nums;
  font-family: ui-monospace, SFMono-Regular, 'Fira Code', monospace;
}

.mermaid-zoom-help {
  position: absolute;
  top: 10px;
  left: 12px;
  padding: 4px 10px;
  background: rgba(30, 41, 59, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid var(--md-default-fg-color--lightest, #475569);
  border-radius: 6px;
  color: var(--md-default-fg-color--lighter, #64748b);
  font-size: 0.7rem;
  z-index: 50;
  pointer-events: none;
  transition: opacity 0.5s;
  white-space: nowrap;
}

.mermaid:fullscreen,
.mermaid:-webkit-full-screen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999 !important;
  border-radius: 0 !important;
  min-height: 100vh !important;
}

[data-md-color-scheme="slate"] .mermaid {
  background: #0f172a;
}

[data-md-color-scheme="slate"] .mermaid-zoom-controls button {
  background: rgba(30, 41, 59, 0.9);
  border-color: #475569;
  color: #e2e8f0;
}

[data-md-color-scheme="slate"] .mermaid-zoom-controls button:hover {
  background: #334155;
  border-color: #60a5fa;
}

[data-md-color-scheme="slate"] .mermaid-zoom-badge {
  background: rgba(30, 41, 59, 0.85);
  border-color: #475569;
  color: #94a3b8;
}

[data-md-color-scheme="slate"] .mermaid-zoom-help {
  background: rgba(30, 41, 59, 0.85);
  border-color: #475569;
  color: #64748b;
}

[data-md-color-scheme="default"] .mermaid {
  background: #ffffff;
}

[data-md-color-scheme="default"] .mermaid-zoom-controls button {
  background: rgba(255, 255, 255, 0.95);
  border-color: #d1d5db;
  color: #374151;
}

[data-md-color-scheme="default"] .mermaid-zoom-controls button:hover {
  background: #f3f4f6;
  border-color: #3b82f6;
}

[data-md-color-scheme="default"] .mermaid-zoom-badge {
  background: rgba(255, 255, 255, 0.9);
  border-color: #d1d5db;
  color: #6b7280;
}

[data-md-color-scheme="default"] .mermaid-zoom-help {
  background: rgba(255, 255, 255, 0.9);
  border-color: #d1d5db;
  color: #9ca3af;
}

@media (max-width: 768px) {
  .mermaid { min-height: 300px; }
  .mermaid-zoom-controls { bottom: 8px; right: 8px; }
  .mermaid-zoom-controls button { width: 32px; height: 32px; font-size: 1rem; }
  .mermaid-zoom-badge { top: 8px; right: 8px; padding: 3px 8px; font-size: 0.7rem; }
  .mermaid-zoom-help { top: 8px; left: 8px; padding: 3px 8px; font-size: 0.65rem; }
}

@media print {
  .mermaid-zoom-controls,
  .mermaid-zoom-badge,
  .mermaid-zoom-help { display: none !important; }
  .mermaid {
    position: static !important;
    height: auto !important;
    min-height: 0 !important;
    overflow: visible !important;
  }
  .mermaid svg {
    position: static !important;
    width: 100% !important;
    height: auto !important;
  }
}
"""