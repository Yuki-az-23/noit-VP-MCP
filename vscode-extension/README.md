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

## Status

This is a scaffold. The toggle handler in `src/diagramTreeProvider.ts` is intentionally a `TODO` — see the docstring there for the design decisions to make.
