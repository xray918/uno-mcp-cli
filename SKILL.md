---
name: uno
description: 通过 bash 命令调用 134+ MCP Server 的全部工具，无需 LLM 原生 tool_use。支持 tool 级别语义搜索，一步拿到完整 inputSchema 直接调用。覆盖：搜索（DuckDuckGo/Brave/Exa/Tavily/Jina）、开发（GitHub/Context7/Figma/Sentry/Linear/Deepwiki）、文档（Markitdown/Fetch/Firecrawl/Word/Excel/PPT/Notion/arXiv）、数据可视化（AntV/ECharts）、金融（A股/东方财富/雅虎/Alpha Vantage/世界银行）、地图（百度/Google/高德）、出行（12306/航班/滴滴/酒店/天气/快递）、AI媒体（图像生成/语音合成/视觉理解）、社交（Twitter/Discord/Instagram/LinkedIn/Reddit/HN/ClawdChat）、办公（Gmail/Outlook/Calendar/GoogleDoc/Drive/Trello/Teams/Canva）、企业（工商/招投标/上市公司/风险扫描）、沙盒（Python/Bash/Node）。
homepage: https://mcpmarket.cn
metadata: {"emoji":"🔧","category":"tools","gateway":"https://uno.mcpmarket.cn/mcp"}
---

# Uno MCP Tools

通过 `uno-cli` 命令行工具，调用 Uno 网关聚合的 134+ MCP Server。支持 tool 级别搜索 — 一步拿到完整 inputSchema，下一步直接调用。

## 安装

```bash
uv tool install uno-cli
```

验证：`uno-cli --help`。如果 `uv` 不可用，可用 `pip3 install uno-cli`。

## 认证

```bash
uno-cli login --headless
```

**必须原样复制终端输出的链接和设备码展示给用户，禁止自行拼接或修改 URL。** Token 存储在 `~/.uno/tokens.json`，有效期 30 天。检查状态：`uno-cli status`

## 5 个网关工具

| 工具 | 职责 |
|------|------|
| `uno_search_servers` | **搜索**（主入口）— 返回最相关的 tools + 完整 inputSchema |
| `uno_discover_servers` | **连接** — 按 server_names 获取 tools 定义 / 触发 OAuth 认证 |
| `uno_call_tool` | **执行** — 调用具体工具（server.tool_name 格式） |
| `uno_execute_script` | **沙盒** — 执行 Python/Bash/Node 脚本 |
| `uno_rate_server` | **评分** — 使用后反馈，影响搜索排名 |

## 两步调用（核心流程）

```bash
# 第一步：搜索 → 直接拿到 tools + inputSchema
uno-cli tools call uno_search_servers '{"query": "天气预报", "mode": "hybrid"}'

# 第二步：调用（从搜索结果的 tool 字段取 server.tool_name）
uno-cli tools call uno_call_tool '{"tool_name": "amap-maps.maps_weather", "arguments": {"city": "北京"}}'
```

## uno_search_servers 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `query` | string | **必填** 搜索关键词（中英文/自然语言均可） |
| `category` | string | 按分类浏览，如 `搜索`、`开发`、`金融`、`社交` |
| `mode` | string | `keyword`（精确,快）/ `semantic`（语义）/ `hybrid`（混合,推荐） |
| `limit` | int | 返回 tool 数量，默认 5，最大 15 |

返回：
- `tools`: 最相关的 tool 列表，每个含 `tool`（server.tool_name）、`desc`、`inputSchema`
- `uncached`: 需要先认证的 OAuth server（如有），提示调用 `uno_discover_servers` 触发认证

## uno_discover_servers 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `server_names` | array | 要获取完整 tools 定义的 server 名称列表 |
| `category` | string | 按分类浏览 server |

使用场景：
- `uno_search_servers` 返回的 `uncached` server 需要 OAuth 认证时
- 已知 server 名称需要完整 tools 定义时

## OAuth 认证流程（冷启动，极少发生）

```bash
# 1. search 发现 uncached OAuth server
uno-cli tools call uno_search_servers '{"query": "GitHub PR"}'
# → uncached: [{server: "github", auth_required: true, action: "uno_discover_servers(...)"}]

# 2. discover 触发认证
uno-cli tools call uno_discover_servers '{"server_names": ["github"]}'
# → auth_url: "https://mcpmarket.cn/oauth/..."（展示给用户点击）

# 3. 用户授权后再次 discover
uno-cli tools call uno_discover_servers '{"server_names": ["github"]}'
# → 返回完整 tools（同时自动缓存到 DB，之后 search 可直接找到）

# 4. 调用
uno-cli tools call uno_call_tool '{"tool_name": "github.search_repositories", "arguments": {...}}'
```

## 可用分类

| 分类 | 数量 | 代表 server |
|------|------|-------------|
| 搜索 | 66 | exa-search, Jina, Tavily, brave-search |
| 数据 | 67 | world-bank, Jina, pageindex-mcp |
| 开发 | 45 | github, context7, Deepwiki, Linear |
| 社交 | 31 | clawdchat-mcp, twitter, Discord, Instagram |
| 创作 | 30 | powerpoint, zhipu-vision, nano-banana |
| 企业 | 28 | enterprise-search, enterprise-risk-scanner |
| 生产 | 14 | Gmail, Google Calendar, Trello, Canva |
| 金融 | 14 | eastmoney-stock-china, Alpha Vantage, yahoo-finance |
| 电商 | 8 | Ecommerce, McDonald's, express-tracking-china |

## 常见用法示例

### 搜索并调用（最常用）

```bash
# 搜索
uno-cli tools call uno_search_servers '{"query": "查北京天气", "mode": "hybrid"}'
# 调用（用返回的 tool 字段）
uno-cli tools call uno_call_tool '{"tool_name": "amap-maps.maps_weather", "arguments": {"city": "北京"}}'
```

### 按分类浏览

```bash
uno-cli tools call uno_search_servers '{"category": "金融", "limit": 10}'
```

### 执行脚本

```bash
uno-cli tools call uno_execute_script '{"language": "python", "script": "print(42 * 2)"}'
```

### 使用后评分

```bash
uno-cli tools call uno_rate_server '{"server_name": "amap-maps", "rating": 4.5, "comment": "响应快"}'
```

### JSON 输出配合 jq

```bash
uno-cli --json tools call uno_call_tool '{"tool_name": "time.get_current_time", "arguments": {"timezone": "UTC"}}' | jq '.content[0].text | fromjson'
```

## 工作流建议

1. **首选 `uno_search_servers`** — 直接拿到 tools + schema，两步完成调用
2. **自然语言用 `hybrid` 模式** — 语义搜索更准确
3. **OAuth server** — search 会标记 uncached，按提示调用 discover 认证即可
4. **评分** — 调用后请用 `uno_rate_server` 反馈，帮助优化搜索排名
5. **参数不确定** — search 返回的 inputSchema 就是完整参数定义

## 凭证管理

| 项目 | 路径 |
|------|------|
| Token 文件 | `~/.uno/tokens.json` |
| MCP 网关 | `https://uno.mcpmarket.cn/mcp` |
| 登录命令 | `uno-cli login --headless` |
| 登出命令 | `uno-cli logout` |
