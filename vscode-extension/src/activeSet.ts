import * as fs from "node:fs/promises";
import * as path from "node:path";

const HEADER = `<!-- Managed by NOit Diagrams extension. Hand-edits are fine. -->
# Active STAR diagrams for this workspace
`;

const BULLET_RE = /^\s*[-*]\s+(.+?)\s*$/;

export async function readActivePaths(absolutePath: string): Promise<string[]> {
  let raw: string;
  try {
    raw = await fs.readFile(absolutePath, "utf8");
  } catch (err: any) {
    if (err.code === "ENOENT") return [];
    throw err;
  }
  return raw
    .split(/\r?\n/)
    .map((line) => {
      const m = line.match(BULLET_RE);
      if (!m) return null;
      return stripAtRef(m[1]);
    })
    .filter((p): p is string => p !== null);
}

export async function writeActivePaths(
  absolutePath: string,
  paths: string[]
): Promise<void> {
  await fs.mkdir(path.dirname(absolutePath), { recursive: true });
  const body = paths.length === 0 ? "" : "\n" + paths.map((p) => `- @${p}`).join("\n") + "\n";
  await fs.writeFile(absolutePath, HEADER + body, "utf8");
}

function stripAtRef(token: string): string {
  let t = token.trim();
  if (t.startsWith("@")) t = t.slice(1);
  return t;
}
