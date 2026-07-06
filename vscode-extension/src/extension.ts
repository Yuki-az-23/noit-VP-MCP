import * as vscode from "vscode";
import * as path from "node:path";
import { NoitMcpClient } from "./mcpClient";
import { DiagramTreeProvider } from "./diagramTreeProvider";
import { injectActive } from "./injectCommand";

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders || workspaceFolders.length === 0) {
    return;
  }
  const root = workspaceFolders[0].uri.fsPath;

  const config = vscode.workspace.getConfiguration("noit");
  const mcpCommand = config.get<string>("mcpServerCommand", "noit-mcp-server");
  const activeSetRelative = config.get<string>("activeSetPath", ".claude/diagrams-active.md");
  const activeSetAbsolute = path.join(root, activeSetRelative);

  const mcp = new NoitMcpClient(mcpCommand);
  context.subscriptions.push({ dispose: () => void mcp.dispose() });

  const tree = new DiagramTreeProvider(mcp, root, activeSetAbsolute);
  const view = vscode.window.createTreeView("noit.diagramList", {
    treeDataProvider: tree,
    manageCheckboxStateManually: false,
  });
  context.subscriptions.push(view);

  view.onDidChangeCheckboxState(async (e) => {
    for (const [node, state] of e.items) {
      if (node.kind !== "piece") continue;
      const checked = state === vscode.TreeItemCheckboxState.Checked;
      try {
        await tree.togglePiece(node, checked);
      } catch (err: any) {
        vscode.window.showErrorMessage(`NOit: toggle failed — ${err?.message ?? err}`);
      }
    }
  });

  context.subscriptions.push(
    vscode.commands.registerCommand("noit.injectActive", () => injectActive(activeSetAbsolute))
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("noit.refreshTree", () => tree.refresh())
  );

  await tree.refresh();
}

export function deactivate(): void {}
