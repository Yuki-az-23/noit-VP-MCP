# Mermaid Style Reference (NOit Diagrams)

The canonical palette + syntax for every diagram piece under `docs/architecture/diagrams/`.
Use this so a piece renders identically in MkDocs Material **and** in the generated HTML viewport.

## Line breaks: `<br/>`, never `\n`

Inside a node label use `<br/>` for multi-line text. `\n` does NOT render in these renderers.

```
good["title_normalized<br/>(lowercase augmented title)"]   ✅
bad["title_normalized\n(lowercase)"]                        ❌
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
