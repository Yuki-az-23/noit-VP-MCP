import * as vscode from "vscode";
import { DiagramPiece, NoitMcpClient } from "./mcpClient";
import { readActivePaths, writeActivePaths } from "./activeSet";

type GroupNode = { kind: "group"; id: string; label: string };
type PieceNode = { kind: "piece"; piece: DiagramPiece; group: string };
type DiagramNode = GroupNode | PieceNode;

const GROUPS: { id: string; label: string }[] = [
  { id: "infra", label: "Infrastructure" },
  { id: "ops", label: "Operations" },
  { id: "seq", label: "Sequences" },
];

export class DiagramTreeProvider implements vscode.TreeDataProvider<DiagramNode> {
  private readonly _onDidChange = new vscode.EventEmitter<DiagramNode | void>();
  readonly onDidChangeTreeData = this._onDidChange.event;

  private pieces: DiagramPiece[] = [];
  private activePaths: Set<string> = new Set();

  constructor(
    private readonly mcp: NoitMcpClient,
    private readonly workspaceRoot: string,
    private readonly activeSetAbsolutePath: string
  ) {}

  async refresh(): Promise<void> {
    this.pieces = await this.mcp.listPieces().catch(() => []);
    this.activePaths = new Set(await readActivePaths(this.activeSetAbsolutePath));
    this._onDidChange.fire();
  }

  getTreeItem(node: DiagramNode): vscode.TreeItem {
    if (node.kind === "group") {
      const item = new vscode.TreeItem(node.label, vscode.TreeItemCollapsibleState.Expanded);
      item.contextValue = "group";
      return item;
    }
    const isActive = this.activePaths.has(node.piece.file_path);
    const item = new vscode.TreeItem(
      node.piece.title,
      vscode.TreeItemCollapsibleState.None
    );
    item.description = node.piece.function_path;
    item.tooltip = `${node.piece.file_path}\n${node.piece.function_path}`;
    item.checkboxState = isActive
      ? vscode.TreeItemCheckboxState.Checked
      : vscode.TreeItemCheckboxState.Unchecked;
    item.contextValue = "piece";
    return item;
  }

  getChildren(node?: DiagramNode): DiagramNode[] {
    if (!node) {
      return GROUPS.map((g) => ({ kind: "group", id: g.id, label: g.label }));
    }
    if (node.kind === "group") {
      return this.pieces
        .filter((p) => p.group === node.id)
        .map((p) => ({ kind: "piece", piece: p, group: node.id }));
    }
    return [];
  }

  /**
   * Called by VS Code when the user toggles a piece's checkbox.
   *
   * Your job: read the current sidecar, add or remove `node.piece.file_path`
   * (preserving order — see guidance below), and write it back. Then call
   * this.refresh() so the UI re-resolves checkbox state.
   *
   * Guidance / trade-offs to think through:
   *   - Preserve the file's header comment? (activeSet.ts writes it on every
   *     write, so you just need to call writeActivePaths — it'll re-emit.)
   *   - Preserve order? Recommended: keep existing order, append new entries
   *     to the end. That way the sidecar stays stable across toggles and
   *     matches the user's mental model of "things I added in this order."
   *   - What if the path is already in the list (toggle on, no-op) or not
   *     in the list (toggle off, no-op)? Be idempotent — don't error.
   *   - Should this surface errors (e.g. sidecar is read-only)? Use
   *     vscode.window.showErrorMessage so the user knows the toggle didn't
   *     stick, rather than silently failing.
   */
  async togglePiece(node: PieceNode, checked: boolean): Promise<void> {
    // TODO: implement the toggle handler here.
    //
    // Skeleton:
    //   1. const current = await readActivePaths(this.activeSetAbsolutePath);
    //   2. const next = apply your add-or-remove logic with `checked` and
    //      `node.piece.file_path`
    //   3. await writeActivePaths(this.activeSetAbsolutePath, next)
    //   4. await this.refresh()
    //
    // Wrap steps 1–3 in try/catch and call
    // vscode.window.showErrorMessage(...) on failure.
    throw new Error("togglePiece not implemented");
  }
}
