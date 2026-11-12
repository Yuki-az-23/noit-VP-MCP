# TEMPLATE: Your Function Name

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
