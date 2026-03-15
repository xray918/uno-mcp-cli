# Changelog

## v2.0.0 — curl direct (current)

**Architecture:** Replaced `pip install uno-cli` + uno-mcp gateway with pure `curl` against MCPMarket REST API.

- **Zero install** — No pip/uv required; eliminates supply-chain risk
- **No middleware** — Bypasses uno-mcp gateway, curl hits MCPMarket directly
- **Transparent auth** — OAuth 2.1 Device Code via plain curl, token at `~/.uno/token` (0600)
- **2 APIs instead of 5** — search-tools + call-tool replaces search/discover/call/script/rate
- **New `POST /api/uno/call-tool`** — MCP protocol handled server-side, client sends JSON only
- **Seamless downstream OAuth** — Returns `auth_url` on first call, retry after authorize, no discover step

## v1.0.0 — uno-cli install

- CLI via `pip install uno-cli`, 5 gateway tools, OAuth cold-start requires discover round-trips
