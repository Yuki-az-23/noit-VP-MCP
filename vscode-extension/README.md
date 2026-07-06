# NOit Diagrams — VS Code Extension

Browse the STAR architecture diagrams in this workspace and toggle which ones are "active" for the current chat. Active diagrams are written to a sidecar file the agent can read directly, so the extension is a UI for context selection — not a gate.

## What it does

- Adds a **NOit Diagrams** activity-bar container with an "Active Pieces" tree view.
- Tree is grouped by `infra` / `ops` / `seq` (from `rollup.manifest.yml`).
- Each piece has a checkbox. Toggling it adds/removes the file path in `.claude/diagrams-active.md`.
- Command: **NOit: Inject Active Diagrams into Chat** — copies the active paths as `@`-references to the clipboard and pastes at the cursor.

## Develop / run

```bash
cd vscode-extension
npm install
npm run watch
# In VS Code: Run > Start Debugging (launches Extension Development Host)
```

The dev host needs `noit-mcp-server` on `PATH` (or override `noit.mcpServerCommand` in settings).

## Sidecar format

`.claude/diagrams-active.md` is hand-editable Markdown. The agent can also read it via `@`-reference or include it in a `CLAUDE.md` reference list. The extension overwrites the file on every toggle but preserves the header comment.

```markdown
<!-- Managed by NOit Diagrams extension. Hand-edits are fine. -->
# Active STAR diagrams for this workspace

- @docs/architecture/diagrams/01-api-gateway.md
- @docs/architecture/diagrams/07-auth-service.md
```

## Configuration

Two settings under `noit.*` in VS Code settings:

| Setting | Default | Purpose |
|---|---|---|
| `noit.mcpServerCommand` | `noit-mcp-server` | Command to spawn the NOit MCP server over stdio. Override if the binary lives somewhere not on `PATH`, or to point at a venv. |
| `noit.activeSetPath` | `.claude/diagrams-active.md` | Path (relative to the workspace root) of the sidecar file. Change if you want the active set stored somewhere else (e.g. `.vscode/diagrams-active.md` for editor-scoped state). |

## Architecture

```
src/
├── extension.ts            # activate(): spawn MCP client, register tree + commands
├── mcpClient.ts            # thin wrapper around @modelcontextprotocol/sdk Client (stdio)
├── activeSet.ts            # readActivePaths() / writeActivePaths() — sidecar I/O
├── diagramTreeProvider.ts  # TreeDataProvider; nodes = groups + pieces
│                           # ← togglePiece() lives here (currently a TODO)
└── injectCommand.ts        # reads sidecar, pastes @-refs at cursor
```

**Data flow on a toggle:**
1. User clicks a checkbox in the tree.
2. `view.onDidChangeCheckboxState` fires in `extension.ts`.
3. It calls `tree.togglePiece(node, checked)`.
4. `togglePiece` reads the sidecar, mutates the list, writes it back.
5. `tree.refresh()` re-fires the tree, and `getTreeItem()` re-reads the sidecar to repaint checkboxes.

**Why the sidecar is the source of truth, not the tree:** the tree is a *view* of the file. The agent, the extension, and humans editing the file by hand all see the same data. If the extension is broken or missing, the agent can still read the sidecar via `@`-reference.

## Status

This is a scaffold. The toggle handler in `src/diagramTreeProvider.ts` is intentionally a `TODO` — see the docstring there for the design decisions to make.

## Contributing

The "missing piece" for a first working version is `togglePiece` in `src/diagramTreeProvider.ts`. The skeleton is in the TODO comment. After that, polish targets in roughly this order:

1. Error states — what if `noit-mcp-server` isn't installed? (Currently: tree is empty, no message.)
2. Tree grouping — currently hardcoded to `infra` / `ops` / `seq`. Should read from `rollup.manifest.yml` if present.
3. Filter / search in the tree view.
