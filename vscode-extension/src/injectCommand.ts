import * as vscode from "vscode";
import { readActivePaths } from "./activeSet";

export async function injectActive(activeSetAbsolutePath: string): Promise<void> {
  const paths = await readActivePaths(activeSetAbsolutePath);

  if (paths.length === 0) {
    vscode.window.showInformationMessage(
      "NOit: no active diagrams. Toggle one in the sidebar first."
    );
    return;
  }

  const missing: string[] = [];
  for (const p of paths) {
    try {
      await vscode.workspace.fs.stat(vscode.Uri.file(p));
    } catch {
      missing.push(p);
    }
  }

  const block = paths.map((p) => `@${p}`).join("\n");
  await vscode.env.clipboard.writeText(block);

  await vscode.commands.executeCommand("editor.action.clipboardPasteAction");

  if (missing.length > 0) {
    vscode.window.showWarningMessage(
      `NOit: injected ${paths.length} refs, but ${missing.length} path(s) don't exist on disk: ${missing.join(", ")}`
    );
  }
}
