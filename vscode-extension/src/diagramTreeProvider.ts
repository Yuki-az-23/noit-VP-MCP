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
    this.pieces = await this.mcp.listPieces().catch((err) => {
      vscode.window.showErrorMessage(`NOit: could not list diagrams — ${err?.message ?? err}`);
      return [];
    });
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
   * Add or remove the piece in the sidecar. Existing order is kept and new
   * entries go to the end; toggling to the current state is a no-op.
   */
  async togglePiece(node: PieceNode, checked: boolean): Promise<void> {
    const target = node.piece.file_path;
    const current = await readActivePaths(this.activeSetAbsolutePath);
    const has = current.includes(target);
    if (checked && !has) {
      await writeActivePaths(this.activeSetAbsolutePath, [...current, target]);
    } else if (!checked && has) {
      await writeActivePaths(
        this.activeSetAbsolutePath,
        current.filter((p) => p !== target)
      );
    }
    await this.refresh();
  }
}
