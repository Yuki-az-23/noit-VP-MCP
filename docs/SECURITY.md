# Security Policy

## Reporting a vulnerability

Please report security problems privately through GitHub's
[private vulnerability reporting](https://github.com/Yuki-az-23/noit-VP-MCP/security/advisories/new)
rather than in a public issue, so a fix can ship before the problem is known widely. Include the
version, how you ran the tool (CLI, MCP over stdio or HTTP, VS Code extension) and the steps to
reproduce. You will get a first answer within a few working days.

## Supported versions

Fixes go into the latest release only; upgrade to receive them.

## How the tool limits risk

The MCP server only reads and writes `.md` pieces directly inside the configured diagrams folder,
and refuses any file name that points elsewhere. Over stdio it is reachable only by the process
that started it. The HTTP transport refuses to start unless `NOIT_MCP_TOKEN` is set, rejects
requests without that bearer token, and listens on `127.0.0.1` unless you pass `--host`. Expose it
beyond your machine only behind TLS, because the token travels in a header.
