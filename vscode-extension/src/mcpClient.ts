import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

export interface DiagramPiece {
  slug: string;
  title: string;
  function_path: string;
  group: string;
  file_path: string;
}

export class NoitMcpClient {
  private client: Client | null = null;
  private connecting: Promise<void> | null = null;

  constructor(private readonly command: string) {}

  async listPieces(): Promise<DiagramPiece[]> {
    const result = await this.call("list_diagram_pieces", {});
    const content = (result as any).content ?? [];
    const text = content.find((c: any) => c.type === "text")?.text ?? "[]";
    return JSON.parse(text) as DiagramPiece[];
  }

  private async call(tool: string, args: Record<string, unknown>): Promise<unknown> {
    await this.ensureConnected();
    if (!this.client) {
      throw new Error("MCP client not connected");
    }
    return this.client.callTool({ name: tool, arguments: args });
  }

  private async ensureConnected(): Promise<void> {
    if (this.client) return;
    if (!this.connecting) {
      this.connecting = this.connect();
    }
    await this.connecting;
  }

  private async connect(): Promise<void> {
    const transport = new StdioClientTransport({
      command: this.command,
      args: [],
    });
    const client = new Client(
      { name: "noit-diagrams-vscode", version: "0.1.0" },
      { capabilities: {} }
    );
    await client.connect(transport);
    this.client = client;
  }

  async dispose(): Promise<void> {
    if (this.client) {
      await this.client.close();
      this.client = null;
    }
  }
}
