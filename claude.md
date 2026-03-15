# MCP Bash CLI Demo

## 项目概述

Python CLI 工具（`uno-cli`），通过 bash 命令调用 Uno MCP 网关聚合的 134+ MCP Server。
OAuth 2.1 + PKCE 认证，连接 `https://uno.mcpmarket.cn/mcp`。
PyPI 包名：`uno-cli`，安装：`uv tool install uno-cli`

## 关联工程

| 工程 | 本地路径 | 说明 |
|------|----------|------|
| **Uno MCP（网关）** | `/Users/xiexinfa/uno-mcp` | 网关服务端，定义 5 个 MCP 工具 |
| **MCPMarket** | `/Users/xiexinfa/mcpmarket-quart` | 后端 API，搜索/缓存/评分 |
| 完整列表 | 见 skill `related-projects` | 含部署/SSH/服务器信息 |

## 技术栈

Python 3.12 + uv / click (CLI) / httpx (HTTP) / mcp SDK (MCP 协议) / hatchling (构建)

## 快速命令

```bash
uv sync --dev                   # 安装依赖
uv run uno-cli login --headless # 登录（Device Code Flow）
uv run uno-cli status           # 查看状态
uv run uno-cli --json tools list # 列出工具
uv run pytest tests/ -v         # 运行测试
```

## 两步调用（核心流程）

```bash
# 搜索 → 直接拿到 tools + inputSchema
uv run uno-cli tools call uno_search_servers '{"query": "天气", "mode": "hybrid"}'
# 调用
uv run uno-cli tools call uno_call_tool '{"tool_name": "amap-maps.maps_weather", "arguments": {"city": "北京"}}'
```

## 5 个网关工具

| 工具 | 职责 |
|------|------|
| `uno_search_servers` | **搜索**（主入口）— 返回 tools + inputSchema |
| `uno_discover_servers` | **连接** — 按 server_names 获取 tools / 触发 OAuth |
| `uno_call_tool` | **执行** — 调用 server.tool_name |
| `uno_execute_script` | **沙盒** — 执行 Python/Bash/Node |
| `uno_rate_server` | **评分** — 使用后反馈 |

## 项目结构

```
mcp_cli/
├── cli.py      # CLI 入口（click）
├── oauth.py    # OAuth 2.1 + PKCE + Device Code Flow
├── client.py   # MCP 客户端（StreamableHTTP + Bearer Token）
└── config.py   # Token 持久化（~/.uno/tokens.json）
```

## 注意事项

- mcpmarket.cn CDN 屏蔽默认 httpx UA，需自定义 User-Agent
- `uno_search_servers` 是主入口，返回 tools + schema 后直接 `uno_call_tool`
- OAuth server 冷启动：search 标记 uncached → discover 触发认证 → 自动缓存到 DB
- Token 存储 `~/.uno/tokens.json`，有效期 30 天
